"""Agent 1: Intake & Extraction — unstructured report → structured fields."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.llm.prompts import INTAKE_EXTRACTION_PROMPT
from src.ingestion.pdf_parser import parse_pdf
from src.ingestion.email_parser import parse_email
from src.config import settings


logger = structlog.get_logger()


class IntakeAgent(BaseAgent):
    name = "intake_agent"

    async def _execute(self, state: dict) -> dict:
        source = state.get("source", "unknown")
        raw_text = state.get("raw_text", "")

        # If source is PDF and raw_text is empty, parse it
        if source == "pdf" and not raw_text:
            raw_text = await parse_pdf(state.get("raw_metadata", {}).get("file_path", ""))
        elif source == "email" and not raw_text:
            raw_text = await parse_email(state.get("raw_metadata", {}).get("email_data", ""))

        # Call LLM for structured extraction
        llm = get_llm(model="gpt-4o")  # Use full model for complex extraction

        @observe(name="intake_extraction", as_type="generation")
        async def extract():
            response = await llm.ainvoke(
                INTAKE_EXTRACTION_PROMPT.format(raw_text=raw_text)
            )
            return response

        result = await extract()

        # Parse JSON response
        import json
        extracted = json.loads(result.content)

        return {
            "patient_age": extracted.get("patient_age"),
            "patient_sex": extracted.get("patient_sex"),
            "patient_weight_kg": extracted.get("patient_weight_kg"),
            "reporter_name": extracted.get("reporter_name"),
            "reporter_role": extracted.get("reporter_role"),
            "drug_name": extracted.get("drug_name"),
            "drug_dose": extracted.get("drug_dose"),
            "drug_start_date": extracted.get("drug_start_date"),
            "drug_stop_date": extracted.get("drug_stop_date"),
            "concomitant_drugs": extracted.get("concomitant_drugs", []),
            "adverse_event_text": extracted.get("adverse_event_text"),
            "adverse_event_start_date": extracted.get("adverse_event_start_date"),
            "adverse_event_outcome": extracted.get("adverse_event_outcome"),
            "medical_history": extracted.get("medical_history"),
        }


intake_agent = IntakeAgent()   