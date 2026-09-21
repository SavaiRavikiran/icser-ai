"""Golden set management: 500 curated cases for regression testing."""
import json
import structlog
from pathlib import Path


logger = structlog.get_logger()

GOLDEN_SET_PATH = Path("/data/eval/golden_set.json")


def load_golden_set() -> list[dict]:
    """Load the 500-case golden set."""
    if not GOLDEN_SET_PATH.exists():
        logger.error("golden_set_not_found", path=str(GOLDEN_SET_PATH))
        return []

    with open(GOLDEN_SET_PATH) as f:
        return json.load(f)


def get_golden_case(case_id: str) -> dict | None:
    """Get a single golden case by ID."""
    for case in load_golden_set():
        if case["case_id"] == case_id:
            return case
    return None   