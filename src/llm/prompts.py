"""All LLM prompts in one place for versioning and regression testing."""

INTAKE_EXTRACTION_PROMPT = """You are a pharmacovigilance data extraction specialist.
Extract the following fields from this adverse event report. Return ONLY valid JSON.

Report:
{raw_text}

Extract:
{{
  "patient_age": <int or null>,
  "patient_sex": "M" | "F" | "U",
  "patient_weight_kg": <float or null>,
  "reporter_name": "<string or null>",
  "reporter_role": "<string or null>",
  "drug_name": "<string or null>",
  "drug_dose": "<string or null>",
  "drug_start_date": "<YYYY-MM-DD or null>",
  "drug_stop_date": "<YYYY-MM-DD or null>",
  "concomitant_drugs": [<string>],
  "adverse_event_text": "<string or null>",
  "adverse_event_start_date": "<YYYY-MM-DD or null>",
  "adverse_event_outcome": "recovered" | "recovering" | "not_recovered" | "fatal" | "unknown",
  "medical_history": "<string or null>"
}}

Rules:
- If a field is not mentioned, use null (not "unknown" or "N/A")
- Dates must be YYYY-MM-DD format
- Drug names: use generic name if available
- Concomitant drugs: list ALL mentioned, not just the suspect drug
"""

TRIAGE_PROMPT = """You are a pharmacovigilance triage specialist. Assess this adverse event report.

Adverse Event: {adverse_event}
Outcome: {outcome}
Drug: {drug}
Medical History: {medical_history}

Assess:
1. Severity: "non_serious" | "serious" | "fatal" | "life_threatening"
   - Serious = death, life-threatening, hospitalization, disability, congenital anomaly, or important medical event
2. Expectedness: Is this a known adverse effect of {drug}? (true/false)
3. Causality: Is there a temporal relationship and biological plausibility? (true/false)
4. Confidence: 0.0-1.0

Return JSON:
{{
  "severity": "<severity>",
  "is_serious": <bool>,
  "is_expected": <bool>,
  "is_causally_related": <bool>,
  "confidence": <float>,
  "reasoning": "<one sentence>"
}}
"""

MEDDRA_CODING_PROMPT = """You are a MedDRA coding specialist. Select the most appropriate MedDRA Preferred Term (PT) for this adverse event.

Adverse Event Description: {ae_text}

Candidate Terms (reranked by relevance):
{candidates}

Select the BEST matching term. Consider:
- Semantic match (not just keyword overlap)
- Specificity (prefer more specific PT over broader SOC)
- Clinical context

Return JSON:
{{
  "term": "<Preferred Term name>",
  "code": "<MedDRA PT code>",
  "hierarchy_path": "<SOC > HLTT > HLTC > PT>",
  "confidence": <0.0-1.0>,
  "reasoning": "<one sentence>"
}}
"""

MEDICAL_REVIEW_PROMPT = """You are a clinical pharmacovigilance medical reviewer. Write a causality assessment and clinical narrative.

Drug: {drug} ({dose})
Adverse Event: {ae_text}
Outcome: {ae_outcome}
Medical History: {medical_history}
Concomitant Drugs: {concomitant_drugs}
MedDRA Code: {meddra_term}

Tasks:
1. Assess causality using WHO-UMC criteria:
   - certain, probable, possible, unlikely, conditional, unassessable
2. Write a 3-5 sentence clinical narrative suitable for a regulatory submission.

Return JSON:
{{
  "causality": "<assessment>",
  "narrative": "<clinical narrative>",
  "key_factors": ["<factor 1>", "<factor 2>"]
}}
"""

COMPLIANCE_CHECK_PROMPT = """You are a GxP compliance validator. Check this ICSR case against the ICH E2B(R3) requirements.

Case Data:
{context}

Checklist:
{checklist}

For each check, respond true (pass) or false (fail).
Also check: does the narrative contain any patient-identifiable information (name, address, phone, ID number)?

Return JSON:
{{
  "checks": {{
    "patient_age_present": <bool>,
    "patient_sex_present": <bool>,
    "drug_name_present": <bool>,
    "adverse_event_present": <bool>,
    "ae_start_date_present": <bool>,
    "ae_outcome_present": <bool>,
    "reporter_identified": <bool>,
    "seriousness_assessed": <bool>,
    "causality_assessed": <bool>,
    "meddra_coded": <bool>,
    "no_pii_in_narrative": <bool>,
    "e2b_structure_valid": <bool>
  }},
  "failures": ["<list of failed check names>"]
}}
"""

FINAL_NARRATIVE_PROMPT = """Write the final clinical narrative for this ICSR regulatory submission.

Drug: {drug}
Adverse Event: {ae}
Outcome: {outcome}
Causality: {causality}
MedDRA: {meddra}

Requirements:
- 3-5 sentences, formal clinical language
- Include temporal relationship
- Include dechallenge/rechallenge if relevant
- No patient-identifiable information
- Suitable for FDA/EMA submission
"""   