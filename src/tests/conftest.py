"""Shared test fixtures."""
import pytest
from src.state import ICSRState


@pytest.fixture
def sample_case_state() -> dict:
    """A realistic ICSR case state for testing."""
    return {
        "case_id": "ICSR-TEST-001",
        "source": "email",
        "received_at": "2025-01-15T10:30:00Z",
        "raw_text": (
            "Patient is a 54-year-old female with history of hypertension. "
            "Started taking DrugX 50mg daily on 2025-01-01. On 2025-01-10, "
            "patient experienced severe abdominal pain with nausea and vomiting. "
            "Patient was hospitalized for 3 days and recovered. "
            "Concomitant medications: Lisinopril 10mg, Metformin 500mg. "
            "Reported by Dr. Smith (Physician) on 2025-01-14."
        ),
        "raw_metadata": {"original_id": "EMAIL-78451"},
        "patient_age": 54,
        "patient_sex": "F",
        "patient_weight_kg": None,
        "reporter_name": "Dr. Smith",
        "reporter_role": "Physician",
        "drug_name": "DrugX",
        "drug_dose": "50mg",
        "drug_start_date": "2025-01-01",
        "drug_stop_date": None,
        "concomitant_drugs": ["Lisinopril 10mg", "Metformin 500mg"],
        "adverse_event_text": "Severe abdominal pain with nausea and vomiting",
        "adverse_event_start_date": "2025-01-10",
        "adverse_event_outcome": "recovered",
        "medical_history": "Hypertension",
        "severity": "serious",
        "is_serious": True,
        "is_expected": False,
        "is_causally_related": True,
        "reporting_deadline_days": 15,
        "triage_confidence": 0.92,
        "meddra_term": "Abdominal pain upper",
        "meddra_code": "10000673",
        "meddra_hierarchy_path": "Gastrointestinal disorders > Abdominal pain upper",
        "meddra_confidence": 0.91,
        "who_drug_code": "INN-12345",
        "coding_review_required": False,
        "is_duplicate": False,
        "duplicate_case_id": None,
        "dedup_similarity_score": 0.34,
        "causality_assessment": "probable",
        "medical_narrative": "54F with HTN developed abdominal pain 9 days after starting DrugX...",
        "compliance_status": "passed",
        "compliance_checks": {},
        "compliance_failures": [],
        "compliance_iteration": 1,
        "e2b_xml": None,
        "report_narrative": None,
        "submission_status": None,
        "submission_ack_id": None,
        "submitted_at": None,
        "iteration_count": 0,
        "error": None,
        "total_tokens_input": 0,
        "total_tokens_output": 0,
        "total_cost_usd": 0.0,
    }


@pytest.fixture
def golden_case() -> dict:
    """A golden set entry for regression testing."""
    return {
        "case_id": "GOLDEN-001",
        "input_state": {
            "case_id": "GOLDEN-001",
            "source": "pdf",
            "received_at": "2025-01-01T00:00:00Z",
            "raw_text": "62-year-old male... started Atorvastatin 40mg... myalgia...",
            "raw_metadata": {},
            "patient_age": None,
            "patient_sex": None,
            "drug_name": None,
            "adverse_event_text": None,
            "concomitant_drugs": [],
            "is_serious": False,
            "is_expected": False,
            "is_causally_related": False,
            "reporting_deadline_days": 90,
            "triage_confidence": 0.0,
            "meddra_term": None,
            "meddra_code": None,
            "med   