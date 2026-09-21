"""LangGraph state definition for ICSR case processing."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class CaseSeverity(str, Enum):
    NON_SERIOUS = "non_serious"
    SERIOUS = "serious"
    FATAL = "fatal"
    LIFE_THREATENING = "life_threatening"


class ComplianceStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class ICSRState(BaseModel):
    """State object passed through the LangGraph pipeline."""

    # Identity
    case_id: str = ""
    source: str = ""  # email, pdf, web_form, hl7, social_media, edc_api
    received_at: str = ""  # ISO timestamp

    # Raw data
    raw_text: str = ""
    raw_metadata: dict = Field(default_factory=dict)

    # Extracted fields (filled by intake_agent)
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None  # M, F, U
    patient_weight_kg: Optional[float] = None
    reporter_name: Optional[str] = None
    reporter_role: Optional[str] = None
    drug_name: Optional[str] = None
    drug_dose: Optional[str] = None
    drug_start_date: Optional[str] = None
    drug_stop_date: Optional[str] = None
    concomitant_drugs: list[str] = Field(default_factory=list)
    adverse_event_text: Optional[str] = None
    adverse_event_start_date: Optional[str] = None
    adverse_event_outcome: Optional[str] = None
    medical_history: Optional[str] = None

    # Triage (filled by triage_agent)
    severity: Optional[CaseSeverity] = None
    is_serious: bool = False
    is_expected: bool = False
    is_causally_related: bool = False
    reporting_deadline_days: int = 90
    triage_confidence: float = 0.0

    # MedDRA coding (filled by meddra_coding_agent)
    meddra_term: Optional[str] = None
    meddra_code: Optional[str] = None
    meddra_hierarchy_path: Optional[str] = None
    meddra_confidence: float = 0.0
    who_drug_code: Optional[str] = None
    coding_review_required: bool = False

    # Deduplication (filled by dedup_agent)
    is_duplicate: bool = False
    duplicate_case_id: Optional[str] = None
    dedup_similarity_score: float = 0.0

    # Medical review (filled by medical_review_agent)
    causality_assessment: Optional[str] = None  # certain, probable, possible, unlikely, conditional, unassessable
    medical_narrative: Optional[str] = None

    # Compliance (filled by compliance_agent)
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    compliance_checks: dict = Field(default_factory=dict)
    compliance_failures: list[str] = Field(default_factory=list)
    compliance_iteration: int = 0

    # Drafting (filled by drafting_agent)
    e2b_xml: Optional[str] = None
    report_narrative: Optional[str] = None

    # Submission (filled by submission_agent)
    submission_status: Optional[str] = None  # pending, submitted, acknowledged, rejected
    submission_ack_id: Optional[str] = None
    submitted_at: Optional[str] = None

    # Meta
    iteration_count: int = 0
    error: Optional[str] = None
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_usd: float = 0.0   