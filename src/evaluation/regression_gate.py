"""CI/CD regression gate: run 500 golden cases, block release if regression detected."""
import json
import asyncio
import structlog

from src.evaluation.golden_set import load_golden_set
from src.graph.builder import build_icser_graph


logger = structlog.get_logger()

# Regression thresholds
EXTRACTION_ACCURACY_DROP_THRESHOLD = 0.02  # 2%
CODING_ACCURACY_DROP_THRESHOLD = 0.03      # 3%


async def run_regression_gate() -> dict:
    """
    Run all 500 golden cases through the current pipeline.
    Compare against baseline. Return pass/fail with details.
    """
    logger.info("regression_gate_start")

    golden_cases = load_golden_set()
    if not golden_cases:
        return {"passed": False, "reason": "Golden set not found"}

    graph = build_icser_graph()
    results = []

    for case_input in golden_cases:
        try:
            # Run through pipeline (staging models)
            result = await graph.ainvoke(case_input["input_state"])

            # Compare against expected
            expected = case_input["expected"]
            comparison = _compare(result, expected)
            results.append({
                "case_id": case_input["case_id"],
                "comparison": comparison,
            })
        except Exception as e:
            results.append({
                "case_id": case_input["case_id"],
                "comparison": {"error": str(e)},
            })

    # Aggregate
    total = len(results)
    extraction_pass = sum(1 for r in results if r["comparison"].get("extraction_match", False))
    coding_pass = sum(1 for r in results if r["comparison"].get("coding_match", False))

    extraction_accuracy = extraction_pass / total if total else 0
    coding_accuracy = coding_pass / total if total else 0

    # Load baseline
    baseline = _load_baseline()
    baseline_extraction = baseline.get("extraction_accuracy", 0.95)
    baseline_coding = baseline.get("coding_accuracy", 0.92)

    extraction_drop = baseline_extraction - extraction_accuracy
    coding_drop = baseline_coding - coding_accuracy

    passed = (
        extraction_drop <= EXTRACTION_ACCURACY_DROP_THRESHOLD
        and coding_drop <= CODING_ACCURACY_DROP_THRESHOLD
    )

    result = {
        "passed": passed,
        "extraction_accuracy": round(extraction_accuracy, 4),
        "coding_accuracy": round(coding_accuracy, 4),
        "baseline_extraction": baseline_extraction,
        "baseline_coding": baseline_coding,
        "extraction_drop": round(extraction_drop, 4),
        "coding_drop": round(coding_drop, 4),
        "total_cases": total,
        "failures": [r for r in results if not r["comparison"].get("extraction_match", True)],
    }

    logger.info(
        "regression_gate_complete",
        passed=passed,
        extraction_accuracy=round(extraction_accuracy, 4),
        coding_accuracy=round(coding_accuracy, 4),
    )

    return result


def _compare(result: dict, expected: dict) -> dict:
    """Compare pipeline output against expected golden values."""
    return {
        "extraction_match": (
            result.get("drug_name") == expected.get("drug_name")
            and result.get("adverse_event_text") is not None
            and result.get("patient_sex") == expected.get("patient_sex")
        ),
        "coding_match": (
            result.get("meddra_term") == expected.get("meddra_term")
        ),
        "narrative_present": bool(result.get("medical_narrative")),
    }


def _load_baseline() -> dict:
    """Load the last known-good baseline scores."""
    baseline_path = Path("/data/eval/baseline.json")
    if baseline_path.exists():
        with open(baseline_path) as f:
            return json.load(f)
    return {"extraction_accuracy": 0.95, "coding_accuracy": 0.92}   