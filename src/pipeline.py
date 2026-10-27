"""Run a case through the LangGraph pipeline, recording per-step results and metrics."""
import time
from functools import lru_cache

from src.graph.builder import build_icser_graph
from src.ingestion.normalizer import normalize_case
from src.observability.metrics import CASE_DURATION, CASES_PROCESSED, COMPLIANCE_FAILURES, DUPLICATES_DETECTED

_NODE_KEYS = {"error"}  # keys always reported in a step diff


@lru_cache(maxsize=1)
def get_graph():
    return build_icser_graph()


def _diff(before: dict, after: dict) -> dict:
    return {k: v for k, v in after.items() if before.get(k) != v or k in _NODE_KEYS and v}


async def run_case(raw_data: dict) -> dict:
    """Process one raw report. Returns {"state": final_state, "steps": [...], "duration_ms": n}."""
    # Already-normalized states (e.g. from the Event Hubs consumer) pass straight through
    state = raw_data if "compliance_iteration" in raw_data else normalize_case(raw_data)
    steps: list[dict] = []
    started = time.time()
    step_start = started

    async for update in get_graph().astream(state, stream_mode="updates"):
        for node, new_state in update.items():
            now = time.time()
            steps.append({
                "agent": node,
                "duration_ms": round((now - step_start) * 1000, 1),
                "changes": _diff(state, new_state),
                "error": new_state.get("error"),
            })
            step_start = now
            CASE_DURATION.labels(stage=node).observe(now - started)
            state = new_state

    if state.get("compliance_status") == "failed" and not state.get("error"):
        state["error"] = "Compliance failed after max iterations; flagged for manual review"
    if state.get("is_duplicate"):
        DUPLICATES_DETECTED.inc()
    for check in state.get("compliance_failures") or []:
        COMPLIANCE_FAILURES.labels(check=check).inc()

    if state.get("submission_status") == "submitted":
        status = "submitted"
    elif state.get("is_duplicate"):
        status = "duplicate"
    elif state.get("error"):
        status = "error"
    else:
        status = "not_submitted"
    CASES_PROCESSED.labels(
        severity=state.get("severity") or "unknown", source=state.get("source", "unknown"), status=status
    ).inc()

    return {
        "state": state,
        "steps": steps,
        "status": status,
        "duration_ms": round((time.time() - started) * 1000, 1),
    }
