# e_assess_patient_and_procedure_context.py

from pathlib import Path
import pprint
import requests
import yaml
from dynamic_filtering.d_medication_terminology import add_medication_class_to_fhir_patient_data, load_value_sets

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GUIDELINES_FILE = DATA_DIR / "guidelines.yaml"

HERMES_BASE_URL = "http://localhost:8081"
SNOMED_SYSTEM = "http://snomed.info/sct"

def load_guidelines():
    with open(GUIDELINES_FILE, "r", encoding="utf-8") as file:
        guidelines = yaml.safe_load(file)

    return guidelines

# find the procedure category. if fhir patient data has procedure code that is directly present in guidelines, use that. if not, use ecl and hermes to identify the procedure type from the guideline
def find_procedure_type(procedure_code, value_sets):
    if not procedure_code:
        return ""
    procedure_value_sets = value_sets.get("procedure_value_sets", {})
    # first check the codes in value sets
    for procedure_type, procedure_details in procedure_value_sets.items():
        root_code = procedure_details.get("root_code", "")
        if procedure_code == root_code:
            return procedure_type
    # if no code matches then check using Hermes.
    url = f"{HERMES_BASE_URL}/v1/snomed/expand"
    for procedure_type, procedure_details in procedure_value_sets.items():
        root_code = procedure_details.get("root_code", "")
        ecl = procedure_details.get("ecl", f"<< {root_code}")
        ecl_query = f"({ecl}) AND {procedure_code}"
        response = requests.get(url, params={"ecl": ecl_query}, timeout=10)
        response.raise_for_status()
        if response.json():
            return procedure_type
    return ""

def assess_extraction(procedure, extraction_complexity, wound_size, guidelines):
    quantity = procedure.get("quantity", "")
    extraction_complexity = extraction_complexity.strip().lower()
    wound_size = wound_size.strip().lower()
    extraction_rules = guidelines.get("procedure_assessment_rules", {}).get("tooth_extraction", {})
    missing_information = []
    if quantity is None or quantity == "":
        missing_information.append("number_of_teeth")
    if not extraction_complexity:
        missing_information.append("extraction_complexity")
    if not wound_size:
        missing_information.append("wound_size")
    if missing_information:
        result = extraction_rules.get("missing_information_result", {}).copy()
        result["missing_information"] = missing_information
        return result
    try:
        quantity = float(str(quantity))
    except ValueError:
        quantity = 0.0
    if quantity <= 0 or not quantity.is_integer():
        result = extraction_rules.get("no_matching_rule_result", {}).copy()
        result["classification_status"] = "invalid_number_of_teeth"
        result["missing_information"] = ["number_of_teeth"]
        return result
    quantity = int(quantity)
    rules = extraction_rules.get("rules", [])
    for rule in rules:
        allowed_complexities = rule.get("extraction_complexity", [])
        allowed_wound_sizes = rule.get("wound_size", [])
        minimum_teeth = rule.get("minimum_teeth")
        maximum_teeth = rule.get("maximum_teeth")
        if allowed_complexities and extraction_complexity not in allowed_complexities:
            continue
        if allowed_wound_sizes and wound_size not in allowed_wound_sizes:
            continue
        if minimum_teeth is not None and quantity < minimum_teeth:
            continue
        if maximum_teeth is not None and quantity > maximum_teeth:
            continue
        result = rule.get("result", {}).copy()
        if "missing_information" not in result:
            result["missing_information"] = []
        return result

    return extraction_rules.get("no_matching_rule_result", {}).copy()

def assess_other_procedure(procedure_type, guidelines):
    procedure_rules = guidelines.get("procedure_assessment_rules", {}).get(procedure_type, {})
    result = procedure_rules.get("result", {}).copy()
    if result:
        return result
    return {
        "procedure_type": procedure_type,
        "classification_status": "procedure_not_mapped",
        "missing_information": [],
        "procedure_category": "",
        "postoperative_bleeding_risk": ""
    }

def assess_patient_context(patient_id, extraction_complexity="", wound_size=""):
    patient_context = add_medication_class_to_fhir_patient_data(patient_id)
    value_sets = load_value_sets()
    guidelines = load_guidelines()
    procedure_assessments = []
    for procedure in patient_context.get("planned_procedures", []):
        procedure_code = procedure.get("code", "")
        if not procedure_code:
            procedure_assessment = {
                "procedure_type": "",
                "classification_status": "procedure_code_missing",
                "missing_information": ["procedure_code"],
                "procedure_category": "",
                "postoperative_bleeding_risk": ""}
        else:
            try:
                procedure_type = find_procedure_type(procedure_code, value_sets)
                if procedure_type == "tooth_extraction":
                    procedure_assessment = assess_extraction(procedure,extraction_complexity,wound_size, guidelines)
                elif procedure_type:
                    procedure_assessment = assess_other_procedure(procedure_type,guidelines)
                else:
                    procedure_assessment = {
                        "procedure_type": "",
                        "classification_status": "procedure_not_identified_in_sdcep_guidelines",
                        "missing_information": [],
                        "procedure_category": "",
                        "postoperative_bleeding_risk": ""}
            except requests.RequestException:
                procedure_assessment = {
                    "procedure_type": "",
                    "classification_status": "terminology_service_unavailable",
                    "missing_information": [],
                    "procedure_category": "",
                    "postoperative_bleeding_risk": ""}
        procedure_assessment["procedure_name"] = procedure.get("procedure_name", "")
        procedure_assessment["procedure_code"] = procedure_code
        procedure_assessment["quantity"] = procedure.get("quantity", "")
        procedure_assessments.append(procedure_assessment)
    patient_context["clinical_assessment"] = {"procedure_assessments": procedure_assessments}

    return patient_context

def preview_patient_assessment():
    patient_id = "1256"
    assessed_context = assess_patient_context(patient_id)
    pprint.pprint(assessed_context)

if __name__ == "__main__":
    preview_patient_assessment()