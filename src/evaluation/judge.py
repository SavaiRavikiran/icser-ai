"""LLM-as-judge: score individual cases for quality."""
import json
import structlog
from langfuse import observe

from src.llm.router import get_llm
from src.config import settings


logger = structlog.get_logger()

JUDGE_PROMPT = """You are a pharmacovigilance quality reviewer. Score the following ICSR case processing output.

Original Report (excerpt):
{raw_text}

Extracted Fields:
{extracted_fields}

MedDRA Code Assigned: {meddra_term} ({meddra_code})
Confidence: {meddra_confidence}

Clinical Narrative:
{narrative}

Score each dimension from 0.0 to 1.0:
1. extraction_accuracy: Did we correctly extract all fields? Any missing or wrong values?
2. coding_accuracy: Is the MedDRA term the best match for the adverse event?
3. narrative_quality: Is the clinical narrative coherent, complete, and appropriate for regulatory submission?

Return JSON:
{{
  "extraction_accuracy": <float>,
  "coding_accuracy": <float>,
  "narrative_quality": <float>,
  "overall": <float>,
  "issues": ["<list of specific issues found>"]
}}
"""


@observe(name="llm_judge_scoring", as_type="generation")
async def llm_judge(state: dict) -> dict:
    """Score a single case using LLM-as-judge."""
    llm = get_llm(model="gpt-4o")

    prompt = JUDGE_PROMPT.format(
        raw_text=state.get("raw_text", "")[:2000],
        extracted_fields=json.dumps({
            "patient_age": state.get("patient_age"),
            "patient_sex": state.get("patient_sex"),
            "drug_name": state.get("drug_name"),
            "adverse_event_text": state.get("adverse_event_text"),
            "ae_outcome": state.get("adverse_event_outcome"),
        }, indent=2),
        meddra_term=state.get("meddra_term", "N/A"),
        meddra_code=state.get("meddra_code", "N/A"),
        meddra_confidence=state.get("meddra_confidence", 0),
        narrative=state.get("medical_narrative", "N/A"),
    )

    response = await llm.ainvoke(prompt)
    result = json.loads(response.content)

    # Write scores back to Langfuse
    try:
        from src.observability.langfuse_client import get_langfuse
        lf = get_langfuse()
        trace_id = state.get("_langfuse_trace_id")
        if trace_id:
            for dim in ("extraction_accuracy", "coding_accuracy", "narrative_quality"):
                lf.score(
                    trace_id=trace_id,
                    name=dim,
                    value=result.get(dim, 0.0),
                    comment=result.get("issues", [""])[0] if result.get("issues") else "",
                )
    except Exception as e:
        logger.warning("langfuse_score_write_failed", error=str(e))

    return result   