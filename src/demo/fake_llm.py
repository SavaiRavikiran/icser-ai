"""Rule-based stand-in for the Foundry LLM used when DEMO_MODE=true.

It inspects the prompt, works out which agent is calling and returns JSON in the
same shape the real model is asked to produce, so the whole pipeline can run
offline.
"""
import json
import re
from dataclasses import dataclass


@dataclass
class FakeResponse:
    content: str


_SERIOUS_WORDS = ("hospital", "life-threatening", "life threatening", "disab", "anaphyla", "died", "death", "fatal")
_DATE = r"(\d{4}-\d{2}-\d{2})"


def _find(pattern: str, text: str, flags: int = re.IGNORECASE):
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else None


def _extract(prompt: str) -> dict:
    text = prompt.split("Report:", 1)[-1].split("Extract:", 1)[0]
    age = _find(r"(\d{1,3})[- ]year[- ]old", text)
    sex = "F" if re.search(r"\b(female|woman)\b", text, re.I) else "M" if re.search(r"\b(male|man)\b", text, re.I) else "U"
    drug_m = re.search(r"(?i:started|taking|took|prescribed|received)\s+([A-Z][A-Za-z0-9-]+)\s*(\d+\s?(?:mg|mcg|g|ml))?", text)
    dates = re.findall(_DATE, text)
    ae = _find(r"(?:experienced|developed|complained of|reported)\s+(.+?)(?:\.|\bPatient\b|$)", text) or "unspecified event"
    if re.search(r"\bfatal|died|death\b", text, re.I):
        outcome = "fatal"
    elif re.search(r"not recovered|ongoing", text, re.I):
        outcome = "not_recovered"
    elif re.search(r"recovering", text, re.I):
        outcome = "recovering"
    elif re.search(r"recovered|resolved", text, re.I):
        outcome = "recovered"
    else:
        outcome = "unknown"
    conc = _find(r"[Cc]oncomitant (?:medications?|drugs?):\s*(.+?)\.", text)
    reporter = re.search(r"[Rr]eported by\s+((?:Dr\.|Nurse|Pharmacist)?\s?[A-Z][a-z]+)\s*\(([^)]+)\)", text)
    history = _find(r"history of\s+(.+?)(?:\.|,? and |$)", text)
    return {
        "patient_age": int(age) if age else None,
        "patient_sex": sex,
        "patient_weight_kg": None,
        "reporter_name": reporter.group(1).strip() if reporter else None,
        "reporter_role": reporter.group(2).strip() if reporter else None,
        "drug_name": drug_m.group(1) if drug_m else None,
        "drug_dose": drug_m.group(2) if drug_m and drug_m.group(2) else None,
        "drug_start_date": dates[0] if dates else None,
        "drug_stop_date": None,
        "concomitant_drugs": [d.strip() for d in re.split(r",| and ", conc)] if conc else [],
        "adverse_event_text": ae,
        "adverse_event_start_date": dates[1] if len(dates) > 1 else None,
        "adverse_event_outcome": outcome,
        "medical_history": history,
    }


def _triage(prompt: str) -> dict:
    ae = (_find(r"Adverse Event:\s*(.*)", prompt) or "").lower()
    outcome = (_find(r"Outcome:\s*(.*)", prompt) or "").lower()
    blob = f"{ae} {outcome}"
    if "fatal" in blob or "died" in blob or "death" in blob:
        sev, serious = "fatal", True
    elif "life" in blob or "anaphyla" in blob:
        sev, serious = "life_threatening", True
    elif any(w in blob for w in _SERIOUS_WORDS) or "severe" in blob:
        sev, serious = "serious", True
    else:
        sev, serious = "non_serious", False
    expected = not serious and any(w in ae for w in ("nausea", "headache", "rash", "myalgia", "dizziness", "muscle"))
    return {
        "severity": sev, "is_serious": serious, "is_expected": expected,
        "is_causally_related": True, "confidence": 0.9,
        "reasoning": "Simulated triage based on keywords.",
    }


def _meddra(prompt: str) -> dict:
    first = re.search(r"1\.\s+(.+?) \(PT: (\d+)\).*?\n\s+Hierarchy: (.*)", prompt)
    if not first:
        return {"term": None, "code": None, "hierarchy_path": None, "confidence": 0.0, "reasoning": "no candidates"}
    return {
        "term": first.group(1), "code": first.group(2), "hierarchy_path": first.group(3),
        "confidence": 0.9, "reasoning": "Top reranked candidate selected.",
    }


def _review(prompt: str) -> dict:
    drug = _find(r"Drug:\s*(.*?)\s*\(", prompt) or "the suspect drug"
    ae = _find(r"Adverse Event:\s*(.*)", prompt) or "the event"
    outcome = _find(r"Outcome:\s*(.*)", prompt) or "unknown"
    return {
        "causality": "probable",
        "narrative": (
            f"A patient treated with {drug} experienced {ae}. The event began after drug "
            f"initiation with a plausible temporal relationship and no clearly better alternative "
            f"explanation. Outcome: {outcome}. Causality is assessed as probable (WHO-UMC)."
        ),
        "key_factors": ["temporal relationship", "no alternative aetiology"],
    }


def _compliance(prompt: str) -> dict:
    ctx = _find(r"Case Data:\s*(\{[^{}]*\})", prompt, re.S) or ""
    def has(key):
        m = re.search(rf"'{key}': (None|''|\[\])", ctx)
        return not m
    checks = {
        "patient_age_present": has("patient_age"),
        "patient_sex_present": has("patient_sex"),
        "drug_name_present": has("drug_name"),
        "adverse_event_present": has("adverse_event_text"),
        "ae_start_date_present": has("ae_start_date"),
        "ae_outcome_present": has("ae_outcome"),
        "reporter_identified": has("reporter_name"),
        "seriousness_assessed": has("severity"),
        "causality_assessed": has("causality"),
        "meddra_coded": has("meddra_term"),
        "no_pii_in_narrative": not re.search(r"\b\d{3}-\d{2}-\d{4}\b|@", ctx),
        "e2b_structure_valid": True,
    }
    return {"checks": checks, "failures": [k for k, v in checks.items() if not v]}


def _dedup(prompt: str) -> dict:
    return {"is_duplicate": True, "reason": "Same patient, drug and event."}


def _judge(prompt: str) -> dict:
    return {"extraction_accuracy": 0.95, "coding_accuracy": 0.9, "narrative_quality": 0.92, "overall": 0.92, "issues": []}


class FakeLLM:
    """Mimics the subset of the chat-model interface used by the agents."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model

    async def ainvoke(self, prompt: str) -> FakeResponse:
        p = prompt if isinstance(prompt, str) else str(prompt)
        if "data extraction specialist" in p:
            out = _extract(p)
        elif "triage specialist" in p:
            out = _triage(p)
        elif "MedDRA coding specialist" in p:
            out = _meddra(p)
        elif "medical reviewer" in p:
            out = _review(p)
        elif "compliance validator" in p:
            out = _compliance(p)
        elif "SAME patient and event" in p:
            out = _dedup(p)
        elif "quality reviewer" in p:
            out = _judge(p)
        elif "final clinical narrative" in p:
            drug = _find(r"Drug:\s*(.*)", p) or "the drug"
            ae = _find(r"Adverse Event:\s*(.*)", p) or "an adverse event"
            causality = _find(r"Causality:\s*(.*)", p) or "possible"
            return FakeResponse(
                f"Following administration of {drug}, the patient developed {ae}. "
                f"A plausible temporal relationship was identified and the event was assessed as "
                f"{causality}ly related to treatment. Follow-up information will be provided if available."
            )
        elif "WHO Drug" in p:
            out = {"code": "INN-" + str(abs(hash(p)) % 90000 + 10000), "name": "demo"}
        else:
            out = {}
        return FakeResponse(json.dumps(out))
