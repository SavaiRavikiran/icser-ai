"""Prometheus metrics definitions."""
from prometheus_client import Counter, Histogram, Gauge, Info

# Case processing
CASES_PROCESSED = Counter(
    "icser_cases_processed_total",
    "Total ICSR cases processed",
    ["severity", "source", "status"],
)

CASE_DURATION = Histogram(
    "icser_case_duration_seconds",
    "End-to-end case processing duration",
    ["stage"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

# MedDRA coding
MEDDRA_CONFIDENCE = Histogram(
    "icser_meddra_confidence",
    "MedDRA coding confidence distribution",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0],
)

MEDDRA_REVIEW_REQUIRED = Counter(
    "icser_meddra_review_required_total",
    "Cases requiring manual MedDRA review",
)

# LLM costs
LLM_TOKENS = Counter(
    "icser_llm_tokens_total",
    "Total LLM tokens consumed",
    ["model", "direction"],
)

LLM_COST = Counter(
    "icser_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model", "agent"],
)

# Evaluation
EVAL_SCORE = Gauge(
    "icser_eval_score",
    "Evaluation scores",
    ["dimension"],
)

# Compliance
COMPLIANCE_FAILURES = Counter(
    "icser_compliance_failure_total",
    "Compliance check failures",
    ["check"],
)

# Deduplication
DUPLICATES_DETECTED = Counter(
    "icser_duplicates_detected_total",
    "Duplicate cases detected",
)

# Submission
SUBMISSION_ACK_LATENCY = Histogram(
    "icser_submission_ack_latency_seconds",
    "Time from submission to regulator acknowledgement",
    ["regulator"],
    buckets=[60, 300, 900, 3600, 86400],
)

# Queue
QUEUE_DEPTH = Gauge(
    "icser_eventhubs_queue_depth",
    "Current Event Hubs consumer lag",
)

# Info
APP_INFO = Info(
    "icser_app",
    "Application info",
)   