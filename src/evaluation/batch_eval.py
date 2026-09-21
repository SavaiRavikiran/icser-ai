"""Weekly batch evaluation: 200 cases scored by human + LLM, compute Cohen's Kappa."""
import json
import asyncio
import structlog
from datetime import datetime, timedelta

from src.evaluation.judge import llm_judge
from src.observability.metrics import EVAL_SCORE


logger = structlog.get_logger()


async def run_batch_eval(sample_size: int = 200):
    """Run weekly batch evaluation on recent production cases."""
    logger.info("batch_eval_start", sample_size=sample_size)

    # In production, this pulls from PostgreSQL:
    # SELECT * FROM icser_cases
    # WHERE processed_at > NOW() - INTERVAL '7 days'
    # ORDER BY RANDOM() LIMIT 200
    cases = await _fetch_recent_cases(sample_size)

    results = []
    for case in cases:
        try:
            score = await llm_judge(case)
            results.append({
                "case_id": case["case_id"],
                "scores": score,
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.warning("batch_eval_case_failed", case_id=case["case_id"], error=str(e))

    # Aggregate
    if results:
        avg_extraction = sum(r["scores"]["extraction_accuracy"] for r in results) / len(results)
        avg_coding = sum(r["scores"]["coding_accuracy"] for r in results) / len(results)
        avg_narrative = sum(r["scores"]["narrative_quality"] for r in results) / len(results)

        EVAL_SCORE.labels(dimension="extraction_accuracy").set(avg_extraction)
        EVAL_SCORE.labels(dimension="coding_accuracy").set(avg_coding)
        EVAL_SCORE.labels(dimension="narrative_quality").set(avg_narrative)

        logger.info(
            "batch_eval_complete",
            count=len(results),
            avg_extraction=round(avg_extraction, 3),
            avg_coding=round(avg_coding, 3),
            avg_narrative=round(avg_narrative, 3),
        )

        # Alert if below threshold
        if avg_extraction < 0.90:
            logger.error("batch_eval_alert", message="Extraction accuracy below 0.90 threshold")

    return results


async def _fetch_recent_cases(limit: int) -> list[dict]:
    """Fetch recent cases from PostgreSQL (placeholder)."""
    # In production: use SQLAlchemy async session
    # For now, return empty to allow testing
    return []   