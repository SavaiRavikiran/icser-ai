"""Agent 5: Medical Review — causality assessment + narrative drafting."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.llm.prompts import MEDICAL_REVIEW_PROMPT


logger = structlog.get_logger()


class MedicalReviewAgent(BaseAgent):
    name = "medical_review_agent"

    async def _execute(self, state: dict) -> dict:
        llm = get_llm(model="gpt-4o")  # Full model for clinical writing

        @observe(name="medical_review", as_type="generation")
        async def review():
            prompt = MEDICAL_REVIEW_PROMPT.format(
                drug=state.get("drug_name", "Unknown"),
                dose=state.get("drug_dose", "Unknown"),
                ae_text=state.get("adverse_event_text", ""),
                ae_outcome=state.get("adverse_event_outcome", "Unknown"),
                medical_history=state.get("medical_history", "None reported"),
                concomitant_drugs=", ".join(state.get("concomitant_drugs", [])) or "None",
                meddra_term=state.get("meddra_term", "Uncoded"),
            )
            response = await llm.ainvoke(prompt)
            return response

        result = await review()

        import json
        review_result = json.loads(result.content)

        return {
            "causality_assessment": review_result.get("causality"),
            "medical_narrative": review_result.get("narrative"),
        }


medical_review_agent = MedicalReviewAgent()   