"""Normalize raw intake data to ICSRState-compatible dict."""
import uuid
from datetime import datetime, timezone


def normalize_case(raw_data: dict) -> dict:
    """Convert raw event data to the state dict expected by LangGraph."""
    source = raw_data.get("source", "unknown")
    case_id = raw_data.get("case_id") or f"ICSR-{uuid.uuid4().hex[:12]}"

    return {
        "case_id": case_id,
        "source": source,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "raw_text": raw_data.get("text", "") or raw_data.get("body", ""),
        "raw_metadata": {
            "file_path": raw_data.get("file_path"),
            "email_data": raw_data.get("email_data"),
            "original_id": raw_data.get("original_id"),
            "received_via": source,
        },
        # All other fields start as None/empty
        "patient_age": None,
        "patient_sex": None,
        "patient_weight_kg": None,
        "reporter_name": None,
        "reporter_role": None,
        "drug_name": None,
        "drug_dose": None,
        "drug_start_date": None,
        "drug_stop_date": None,
        "concomitant_drugs": [],
        "adverse_event_text": None,
        "adverse_event_start_date": None,
        "adverse_event_outcome": None,
        "medical_history": None,
        "severity": None,
        "is_serious": False,
        "is_expected": False,
        "is_causally_related": False,
        "reporting_deadline_days": 90,
        "triage_confidence": 0.0,
        "meddra_term": None,
        "meddra_code": None,
        "meddra_hierarchy_path": None,
        "meddra_confidence": 0.0,
        "who_drug_code": None,
        "coding_review_required": False,
        "is_duplicate": False,
        "duplicate_case_id": None,
        "dedup_similarity_score": 0.0,
        "causality_assessment": None,
        "medical_narrative": None,
        "compliance_status": "pending",
        "compliance_checks": {},
        "compliance_failures": [],
        "compliance_iteration": 0,
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