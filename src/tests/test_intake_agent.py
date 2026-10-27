"""Intake agent: free text -> structured fields (simulated LLM)."""
from src.agents.intake_agent import intake_agent
from src.ingestion.normalizer import normalize_case


async def test_intake_extracts_core_fields(sample_case_state):
    state = normalize_case({"source": "email", "text": sample_case_state["raw_text"]})
    result = await intake_agent(state)

    assert result["error"] is None
    assert result["patient_age"] == 54
    assert result["patient_sex"] == "F"
    assert result["drug_name"] == "DrugX"
    assert result["adverse_event_start_date"] == "2025-01-10"
    assert result["adverse_event_outcome"] == "recovered"
    assert result["concomitant_drugs"] == ["Lisinopril 10mg", "Metformin 500mg"]
    assert result["reporter_role"] == "Physician"


async def test_intake_golden_case(golden_case):
    result = await intake_agent(dict(golden_case["input_state"]))
    for field, expected in golden_case["expected"].items():
        if field in result and not field.startswith("meddra"):
            assert result[field] == expected
