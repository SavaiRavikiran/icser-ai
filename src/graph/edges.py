"""Conditional routing logic for the LangGraph."""
from src.state import ComplianceStatus
from src.config import settings


def route_after_triage(state: dict) -> str:
    """After triage: route to coding, dedup, or end."""
    if state.get("is_duplicate"):
        return "end"

    if not state.get("is_serious") and not state.get("is_expected"):
        # Non-serious, expected → still process but lower priority
        return "coding"

    return "coding"


def route_after_coding(state: dict) -> str:
    """After coding: route to dedup or directly to compliance."""
    if state.get("meddra_confidence", 0) >= 0.95:
        # High confidence → skip dedup (fast path)
        return "compliance"
    return "dedup"


def route_after_compliance(state: dict) -> str:
    """After compliance: route to drafting, back to coding, or end."""
    status = state.get("compliance_status", "pending")
    iteration = state.get("compliance_iteration", 0)

    if status == "passed":
        return "drafting"

    if status == "failed":
        if iteration >= settings.max_compliance_iterations:
            # Max iterations reached → flag for manual review
            state["error"] = "Compliance failed after max iterations"
            return "end"
        return "coding"  # Loop back

    return "drafting"   