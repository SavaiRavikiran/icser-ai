"""Content safety: PII detection and blocking."""
import re
from dataclasses import dataclass


@dataclass
class SafetyResult:
    is_safe: bool
    violations: list[str]


PII_PATTERNS = {
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
    "email": r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b",
    "date_of_birth": r"\b(0?[1-9]|1[0-2])/(0?[1-9]|1[0-2])/(\d{4})\b",
    "address": r"\b\d+\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)\b",
}


def check_pii(text: str) -> SafetyResult:
    """Check text for PII violations."""
    violations = []
    for name, pattern in PII_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            violations.append(name)

    return SafetyResult(
        is_safe=len(violations) == 0,
        violations=violations,
    )   