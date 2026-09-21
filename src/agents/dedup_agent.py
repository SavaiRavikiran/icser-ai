"""Agent 4: Deduplication — check if case already exists in database."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.rag.dedup_index import search_similar_cases
from src.config import settings


logger = structlog.get_logger()


class DedupAgent(BaseAgent):
    name = "dedup_agent"

    async def _execute(self, state: dict) -> dict:
        # Build search text from key fields
        search_text = " ".join(filter(None, [
            state.get("patient_age") and f"age {state['patient_age']}",
            state.get("patient_sex"),
            state.get("drug_name"),
            state.get("adverse_event_text"),
            state.get("adverse_event_start_date"),
        ]))

        @observe(name="dedup_vector_search", as_type="span")
        async def search():
            return await search_similar_cases(
                text=search_text,
                top_k=5,
                threshold=settings.dedup_similarity_threshold,
            )

        matches = await search()

        if not matches:
            return {
                "is_duplicate": False,
                "duplicate_case_id": None,
                "dedup_similarity_score": 0.0,
            }

        # LLM judgment on top match
        top_match = matches[0]
        llm = get_llm(model="gpt-4o-mini")

        @observe(name="dedup_llm_judgment", as_type="generation")
        async def judge():
            prompt = (
                f"Are these two adverse event reports about the SAME patient and event?\n\n"
                f"New case: {search_text}\n"
                f"Existing case {top_match['case_id']}: {top_match['summary']}\n\n"
                f"Respond JSON: {{"is_duplicate": true/false, "reason": "..."}}"
            )
            response = await llm.ainvoke(prompt)
            return response

        result = await judge()
        import json
        judgment = json.loads(result.content)

        return {
            "is_duplicate": judgment.get("is_duplicate", False),
            "duplicate_case_id": top_match["case_id"] if judgment.get("is_duplicate") else None,
            "dedup_similarity_score": top_match["similarity"],
        }


dedup_agent = DedupAgent()   