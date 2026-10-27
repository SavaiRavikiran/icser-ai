"""Small in-memory MedDRA subset, prior cases and sample reports for DEMO_MODE and the UI."""

MEDDRA_TERMS = [
    {"term": "Abdominal pain", "code": "10000081", "definition": "Pain in the abdomen", "hierarchy_path": "Gastrointestinal disorders > Gastrointestinal signs and symptoms > Abdominal pain"},
    {"term": "Nausea", "code": "10028813", "definition": "Feeling of sickness with urge to vomit", "hierarchy_path": "Gastrointestinal disorders > Gastrointestinal signs and symptoms > Nausea"},
    {"term": "Vomiting", "code": "10047700", "definition": "Forceful expulsion of stomach contents", "hierarchy_path": "Gastrointestinal disorders > Gastrointestinal signs and symptoms > Vomiting"},
    {"term": "Myalgia", "code": "10028411", "definition": "Muscle pain", "hierarchy_path": "Musculoskeletal and connective tissue disorders > Muscle disorders > Myalgia"},
    {"term": "Rhabdomyolysis", "code": "10039020", "definition": "Breakdown of muscle tissue with severe muscle pain and weakness", "hierarchy_path": "Musculoskeletal and connective tissue disorders > Muscle disorders > Rhabdomyolysis"},
    {"term": "Headache", "code": "10019211", "definition": "Pain in the head", "hierarchy_path": "Nervous system disorders > Headaches > Headache"},
    {"term": "Dizziness", "code": "10013573", "definition": "Sensation of unsteadiness or light-headedness", "hierarchy_path": "Nervous system disorders > Neurological signs and symptoms > Dizziness"},
    {"term": "Rash", "code": "10037844", "definition": "Skin eruption", "hierarchy_path": "Skin and subcutaneous tissue disorders > Rashes, eruptions and exanthems > Rash"},
    {"term": "Anaphylactic reaction", "code": "10002198", "definition": "Severe life-threatening allergic reaction with swelling, hives and breathing difficulty", "hierarchy_path": "Immune system disorders > Allergic conditions > Anaphylactic reaction"},
    {"term": "Dyspnoea", "code": "10013968", "definition": "Shortness of breath, difficulty breathing", "hierarchy_path": "Respiratory, thoracic and mediastinal disorders > Breathing abnormalities > Dyspnoea"},
    {"term": "Hepatotoxicity", "code": "10019851", "definition": "Liver damage with raised liver enzymes", "hierarchy_path": "Hepatobiliary disorders > Hepatic disorders > Hepatotoxicity"},
    {"term": "Palpitations", "code": "10033557", "definition": "Awareness of heartbeat, rapid or irregular", "hierarchy_path": "Cardiac disorders > Cardiac signs and symptoms > Palpitations"},
]

PRIOR_CASES = [
    {"case_id": "ICSR-PRIOR-0042", "summary": "age 54 F DrugX severe abdominal pain with nausea and vomiting 2025-01-10"},
]

SAMPLE_REPORTS = [
    {
        "id": "gi",
        "title": "Serious: abdominal pain, hospitalised",
        "source": "email",
        "text": (
            "Patient is a 61-year-old female with a history of hypertension. "
            "Started taking DrugX 50mg daily on 2025-02-01. On 2025-02-09 she experienced severe abdominal pain with nausea. "
            "Patient was hospitalized for 3 days and recovered. "
            "Concomitant medications: Lisinopril 10mg, Metformin 500mg. "
            "Reported by Dr. Smith (Physician) on 2025-02-14."
        ),
    },
    {
        "id": "myalgia",
        "title": "Non-serious: muscle pain on statin",
        "source": "pdf",
        "text": (
            "A 62-year-old male with a history of high cholesterol. "
            "Started Atorvastatin 40mg on 2025-01-01. On 2025-01-20 he experienced mild muscle pain in both legs. "
            "Patient recovered after dose reduction. "
            "Reported by Nurse Patel (Nurse) on 2025-01-25."
        ),
    },
    {
        "id": "duplicate",
        "title": "Duplicate of an existing case",
        "source": "email",
        "text": (
            "A 54-year-old female with history of hypertension. "
            "Started DrugX 50mg on 2025-01-01. On 2025-01-10 she experienced severe abdominal pain with nausea and vomiting. "
            "Patient was hospitalized and recovered. "
            "Reported by Dr. Jones (Physician) on 2025-01-16."
        ),
    },
    {
        "id": "incomplete",
        "title": "Incomplete: missing reporter & dates (compliance loop)",
        "source": "web_form",
        "text": "A 45-year-old male took ZetaCure 20mg and experienced dizziness. Patient recovered.",
    },
    {
        "id": "fatal",
        "title": "Fatal: anaphylaxis",
        "source": "hl7",
        "text": (
            "A 38-year-old female with a history of asthma. "
            "Started Biovex 10mg on 2025-03-01. On 2025-03-02 she experienced anaphylactic reaction with difficulty breathing. "
            "Patient died on 2025-03-02. "
            "Reported by Dr. Lee (Physician) on 2025-03-03."
        ),
    },
]
