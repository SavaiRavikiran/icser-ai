"""Agent 7: Drafting — generate ICH E2B(R3) XML + final narrative."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.submission.e2b_generator import generate_e2b_xml
from src.llm.router import get_llm
from src.llm.prompts import FINAL_NARRATIVE_PROMPT


logger = structlog.get_logger()


class DraftingAgent(BaseAgent):
    name = "drafting_agent"

    async def _execute(self, state: dict) -> dict:
        # Generate E2B(R3) XML
        @observe(name="e2b_generation", as_type="span")
        async def gen_xml():
            return await generate_e2b_xml(state)

        e2b_xml = await gen_xml()

        # Generate final clinical narrative
        llm = get_llm(model="gpt-4o")

        @observe(name="final_narrative", as_type="generation")
        async def gen_narrative():
            prompt = FINAL_NARRATIVE_PROMPT.format(
                drug=state.get("drug_name", ""),
                ae=state.get("adverse_event_text", ""),
                outcome=state.get("adverse_event_outcome", ""),
                causality=state.get("causality_assessment", ""),
                meddra=state.get("meddra_term", ""),
            )
            response = await llm.ainvoke(prompt)
            return response.content

        narrative = await gen_narrative()

        return {
            "e2b_xml": e2b_xml,
            "report_narrative": narrative,
        }


drafting_agent = DraftingAgent()   