"""Agent 3: MedDRA Coding — map adverse events to MedDRA terms via RAG."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.llm.prompts import MEDDRA_CODING_PROMPT
from src.rag.vector_store import vector_search
from src.rag.reranker import cross_encoder_rerank
from src.utils.redis_cache import get_cache, set_cache
from src.config import settings


logger = structlog.get_logger()


class MedDRACodingAgent(BaseAgent):
    name = "meddra_coding_agent"

    async def _execute(self, state: dict) -> dict:
        ae_text = state.get("adverse_event_text", "")
        drug_name = state.get("drug_name", "")

        if not ae_text:
            return {"coding_review_required": True, "meddra_confidence": 0.0}

        # Check Redis cache first (identical drug/AE pairs)
        cache_key = f"meddra:{ae_text.strip().lower()[:100]}"
        cached = await get_cache(cache_key)
        if cached:
            logger.info("meddra_cache_hit", case_id=state.get("case_id"))
            return cached

        # Stage 1: Vector search for candidate MedDRA terms
        @observe(name="meddra_vector_search", as_type="span")
        async def retrieve():
            candidates = await vector_search(
                text=ae_text,
                index="meddra_terms",
                top_k=20,
            )
            return candidates

        candidates = await retrieve()

        # Stage 2: Cross-encoder reranking
        @observe(name="meddra_reranking", as_type="span")
        async def rerank():
            return await cross_encoder_rerank(
                query=ae_text,
                documents=candidates,
                top_k=5,
            )

        reranked = await rerank()

        # Stage 3: LLM selection
        llm = get_llm(model="gpt-4o-mini")

        @observe(name="meddra_llm_selection", as_type="generation")
        async def select():
            prompt = MEDDRA_CODING_PROMPT.format(
                ae_text=ae_text,
                candidates=self._format_candidates(reranked),
            )
            response = await llm.ainvoke(prompt)
            return response

        result = await select()

        import json
        coding_result = json.loads(result.content)

        confidence = coding_result.get("confidence", 0.0)
        needs_review = confidence < settings.meddra_confidence_threshold

        # Cache the result
        cache_value = {
            "meddra_term": coding_result.get("term"),
            "meddra_code": coding_result.get("code"),
            "meddra_hierarchy_path": coding_result.get("hierarchy_path"),
            "meddra_confidence": confidence,
            "coding_review_required": needs_review,
        }
        await set_cache(cache_key, cache_value, ttl=86400 * 30)  # 30 days

        # Also code the drug
        who_drug_code = await self._code_drug(drug_name)

        cache_value["who_drug_code"] = who_drug_code
        return cache_value

    def _format_candidates(self, candidates: list[dict]) -> str:
        lines = []
        for i, c in enumerate(candidates, 1):
            lines.append(
                f"{i}. {c['term']} (PT: {c['code']}) — {c.get('definition', '')}\n"
                f"   Hierarchy: {c.get('hierarchy_path', '')}"
            )
        return "\n".join(lines)

    async def _code_drug(self, drug_name: str) -> str | None:
        """Code drug using WHO Drug dictionary (simplified)."""
        if not drug_name:
            return None

        cache_key = f"who_drug:{drug_name.strip().lower()}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        llm = get_llm(model="gpt-4o-mini")
        response = await llm.ainvoke(
            f"What is the WHO Drug (INN) code for: {drug_name}? "
            f"Respond with JSON: {{"code": "...", "name": "..."}}"
        )
        import json
        result = json.loads(response.content)
        code = result.get("code")
        if code:
            await set_cache(cache_key, code, ttl=86400 * 365)
        return code


meddra_coding_agent = MedDRACodingAgent()   