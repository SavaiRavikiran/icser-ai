"""Agent 6: Compliance Validation — GxP / ICH E2B(R3) checklist."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.llm.prompts import COMPLIANCE_CHECK_PROMPT
from src.state import ComplianceStatus
from src.config import settings


logger = structlog.get_logger()

COMPLIANCE_CHECKLIST = [
    "patient_age_present",
    "patient_sex_present",
    "drug_name_present",
    "adverse_event_present",
    "ae_start_date_present",
    "ae_outcome_present",
    "reporter_identified",
    "seriousness_assessed",
    "causality_assessed",
    "meddra_coded",
    "no_pii_in_narrative",
    "e2b_structure_valid",
]


class ComplianceAgent(BaseAgent):
    name = "compliance_agent"

    async def _execute(self, state: dict) -> dict:
        llm = get_llm(model="gpt-4o-mini")

        # Build context for compliance check
        context = {
            "patient_age": state.get("patient_age"),
            "patient_sex": state.get("patient_sex"),
            "drug_name": state.get("drug_name"),
            "adverse_event_text": state.get("adverse_event_text"),
            "ae_start_date": state.get("adverse_event_start_date"),
            "ae_outcome": state.get("adverse_event_outcome"),
            "reporter_name": state.get("reporter_name"),
            "severity": state.get("severity"),
            "causality": state.get("causality_assessment"),
            "meddra_term": state.get("meddra_term"),
            "medical_narrative": state.get("medical_narrative", "")[:500],
        }

        @observe(name="compliance_validation", as_type="generation")
        async def validate():
            prompt = COMPLIANCE_CHECK_PROMPT.format(
                context=str(context),
                checklist=", ".join(COMPLIANCE_CHECKLIST),
            )
            response = await llm.ainvoke(prompt)
            return response

        result = await validate()

        import json
        compliance_result = json.loads(result.content)

        checks = compliance_result.get("checks", {})
        failures = [k for k, v in checks.items() if not v]
        passed = len(failures) == 0

        # Increment iteration counter
        current_iteration = state.get("compliance_iteration", 0) + 1

        return {
            "compliance_status": ComplianceStatus.PASSED.value if passed else ComplianceStatus.FAILED.value,
            "compliance_checks": checks,
            "compliance_failures": failures,
            "compliance_iteration": current_iteration,
        }


compliance_agent = ComplianceAgent()   