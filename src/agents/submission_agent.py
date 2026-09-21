"""Agent 8: Submission — submit to FAERS/EudraVigilance, track acknowledgement."""
import structlog
from datetime import datetime, timezone
from langfuse import observe

from src.agents.base_agent import BaseAgent
from src.submission.faers_client import FAERSClient


logger = structlog.get_logger()


class SubmissionAgent(BaseAgent):
    name = "submission_agent"

    async def _execute(self, state: dict) -> dict:
        e2b_xml = state.get("e2b_xml", "")
        if not e2b_xml:
            return {"submission_status": "failed", "error": "No E2B XML to submit"}

        client = FAERSClient()

        @observe(name="faers_submission", as_type="span")
        async def submit():
            return await client.submit(e2b_xml)

        result = await submit()

        return {
            "submission_status": "submitted" if result.get("success") else "failed",
            "submission_ack_id": result.get("ack_id"),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }


submission_agent = SubmissionAgent()   