"""Agent 2: Triage — assess seriousness, expectedness, causality, deadline."""
import structlog
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.llm.router import get_llm
from src.llm.prompts import TRIAGE_PROMPT
from src.state import CaseSeverity


logger = structlog.get_logger()


class TriageAgent(BaseAgent):
    name = "triage_agent"

    async def _execute(self, state: dict) -> dict:
        llm = get_llm(model="gpt-4o-mini")  # Cheaper model for triage

        context = {
            "adverse_event": state.get("adverse_event_text", ""),
            "outcome": state.get("adverse_event_outcome", ""),
            "drug": state.get("drug_name", ""),
            "medical_history": state.get("medical_history", ""),
        }

        @observe(name="triage_assessment", as_type="generation")
        async def triage():
            response = await llm.ainvoke(
                TRIAGE_PROMPT.format(
                    adverse_event=context["adverse_event"],
                    outcome=context["outcome"],
                    drug=context["drug"],
                    medical_history=context["medical_history"],
                )
            )
            return response

        result = await triage()

        import json
        triage_result = json.loads(result.content)

        severity = CaseSeverity(triage_result.get("severity", "non_serious"))
        is_serious = triage_result.get("is_serious", False)
        is_expected = triage_result.get("is_expected", False)

        # Determine deadline based on ICH guidelines
        if severity in (CaseSeverity.FATAL, CaseSeverity.LIFE_THREATENING):
            deadline = 7
        elif is_serious and not is_expected:
            deadline = 15
        else:
            deadline = 90

        return {
            "severity": severity.value,
            "is_serious": is_serious,
            "is_expected": is_expected,
            "is_causally_related": triage_result.get("is_causally_related", False),
            "reporting_deadline_days": deadline,
            "triage_confidence": triage_result.get("confidence", 0.0),
        }


triage_agent = TriageAgent()   