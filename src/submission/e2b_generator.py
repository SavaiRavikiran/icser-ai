"""Generate ICH E2B(R3) XML from ICSR state."""
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


async def generate_e2b_xml(state: dict) -> str:
    """Build ICH E2B(R3) compliant XML document."""
    # Root: ICH.E2B.R3
    root = Element("ICH.E2B.R3")
    root.set("Version", "21")

    # Shipment info
    shipment = SubElement(root, "Shipment")
    SubElement(shipment, "ShipmentID").text = state.get("case_id", "")
    SubElement(shipment, "ShipmentDate").text = state.get("received_at", "")[:10]

    # Case info
    case = SubElement(root, "Case")
    SubElement(case, "CaseID").text = state.get("case_id", "")

    # Patient
    patient = SubElement(case, "Patient")
    if state.get("patient_age"):
        SubElement(patient, "PatientAge").text = str(state["patient_age"])
    if state.get("patient_sex"):
        SubElement(patient, "PatientSex").text = state["patient_sex"]
    if state.get("patient_weight_kg"):
        SubElement(patient, "PatientWeight").text = str(state["patient_weight_kg"])

    # Suspect drug
    suspect = SubElement(case, "SuspectDrug")
    if state.get("drug_name"):
        SubElement(suspect, "DrugName").text = state["drug_name"]
    if state.get("drug_dose"):
        SubElement(suspect, "DrugDose").text = state["drug_dose"]
    if state.get("drug_start_date"):
        SubElement(suspect, "DrugStartDate").text = state["drug_start_date"]
    if state.get("drug_stop_date"):
        SubElement(suspect, "DrugStopDate").text = state["drug_stop_date"]

    # Adverse event
    ae = SubElement(case, "AdverseEvent")
    if state.get("adverse_event_text"):
        SubElement(ae, "AEDescription").text = state["adverse_event_text"]
    if state.get("adverse_event_start_date"):
        SubElement(ae, "AEStartDate").text = state["adverse_event_start_date"]
    if state.get("adverse_event_outcome"):
        SubElement(ae, "AEOutcome").text = state["adverse_event_outcome"]

    # MedDRA coding
    if state.get("meddra_term"):
        coding = SubElement(ae, "MedDRACoding")
        SubElement(coding, "PreferredTerm").text = state["meddra_term"]
        SubElement(coding, "PTCode").text = state.get("meddra_code", "")
        SubElement(coding, "HierarchyPath").text = state.get("meddra_hierarchy_path", "")

    # Reporter
    reporter = SubElement(case, "Reporter")
    if state.get("reporter_name"):
        SubElement(reporter, "ReporterName").text = state["reporter_name"]
    if state.get("reporter_role"):
        SubElement(reporter, "ReporterRole").text = state["reporter_role"]

    # Narrative
    if state.get("report_narrative"):
        narrative = SubElement(case, "Narrative")
        narrative.text = state["report_narrative"]

    # Serialize
    rough_string = tostring(root, encoding="unicode")
    pretty_xml = parseString(rough_string).toprettyxml(indent="  ")
    return pretty_xml   