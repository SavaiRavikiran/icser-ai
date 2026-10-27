"""Compliance agent and graph routing."""
from src.agents.compliance_agent import compliance_agent
from src.graph.edges import route_after_coding, route_after_compliance, route_after_dedup, route_after_triage


async def test_complete_case_passes(sample_case_state):
    result = await compliance_agent(dict(sample_case_state))
    assert result["compliance_status"] == "passed"
    assert result["compliance_failures"] == []
    assert result["compliance_iteration"] == 2


async def test_missing_fields_fail(sample_case_state):
    state = dict(sample_case_state, reporter_name=None, adverse_event_start_date=None, medical_narrative=None)
    result = await compliance_agent(state)
    assert result["compliance_status"] == "failed"
    assert set(result["compliance_failures"]) == {"ae_start_date_present", "reporter_identified"}


def test_routing():
    assert route_after_triage({"is_duplicate": True}) == "end"
    assert route_after_triage({"is_serious": True}) == "coding"
    assert route_after_coding({"meddra_confidence": 0.97}) == "compliance"
    assert route_after_coding({"meddra_confidence": 0.9}) == "dedup"
    assert route_after_dedup({"is_duplicate": True}) == "end"
    assert route_after_dedup({"is_duplicate": False}) == "medical_review"
    assert route_after_compliance({"compliance_status": "passed"}) == "drafting"
    assert route_after_compliance({"compliance_status": "failed", "compliance_iteration": 1}) == "coding"
    assert route_after_compliance({"compliance_status": "failed", "compliance_iteration": 3}) == "end"
