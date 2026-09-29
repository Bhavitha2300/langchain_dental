# e_assess_patient_and_procedure_context.py
# - it identifies each planned dental procedure and applies the SDCEP rules to determine its postoperative bleeding risk.

from pathlib import Path
import pprint
import yaml
import requests
from dynamic_filtering.d_medication_terminology import enrich_patient_context


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VALUE_SETS_FILE = DATA_DIR / "sdcep_value_sets.yaml"
GUIDELINES_FILE = DATA_DIR / "guidelines.yaml"
HERMES_BASE_URL = "http://localhost:8081"
SNOMED_SYSTEM = "http://snomed.info/sct"


def load_value_sets():
    with open(VALUE_SETS_FILE, "r", encoding="utf-8") as file:
        value_sets = yaml.safe_load(file)

    return value_sets

def load_guidelines():
    with open(GUIDELINES_FILE, "r", encoding="utf-8") as file:
        guidelines = yaml.safe_load(file)

    return guidelines

def classify_inr(inr_value):
    inr_text = str(inr_value).strip()
    if not inr_text:
        return ""
    try:
        inr_number = float(inr_text)
    except (ValueError, TypeError):
        return "invalid"
    if inr_number <= 0:
        return "invalid"
    if inr_number < 4:
        return "below_4"
    return "4_or_above"

def assess_patient_context(
    patient_id: str,
    extraction_complexity: str = "",
    wound_size: str = "",
    usual_dose_time: str = "",
    inr_value="",
    inr_test_hours_ago="",
    inr_is_stable: str = "",
    lmwh_dose_category: str = "",
    heparin_during_kidney_dialysis: str = "",
    safety_context=None
):
    if safety_context is None:
        safety_context = {}

    patient_context = enrich_patient_context(patient_id)
    value_sets = load_value_sets()
    guidelines = load_guidelines()

    procedure_assessments = []
    planned_procedures = patient_context.get("planned_procedures",[])
    for procedure in planned_procedures:
        procedure_code = procedure.get("code", "")
        procedure_code_system = procedure.get("code_system","")
        do_not_perform = procedure.get("do_not_perform",False)
        if do_not_perform:
            procedure_assessment = {
                "procedure_type": "",
                "classification_status": "procedure_marked_do_not_perform",
                "missing_information": [],
                "procedure_category": "",
                "postoperative_bleeding_risk": ""
            }
        elif not procedure_code:
            procedure_assessment = {
                "procedure_type": "",
                "classification_status": "procedure_code_missing",
                "missing_information": ["procedure_code"],
                "procedure_category": "",
                "postoperative_bleeding_risk": ""
            }
        elif procedure_code_system != SNOMED_SYSTEM:
            procedure_assessment = {
                "procedure_type": "",
                "classification_status": "unsupported_procedure_code_system",
                "missing_information": [],
                "procedure_category": "",
                "postoperative_bleeding_risk": ""
            }
        else:
            try:
                procedure_type = find_procedure_type(procedure_code,value_sets)
            except requests.RequestException as error:
                print("Hermes error:")
                print(error)
                procedure_assessment = {
                    "procedure_type": "",
                    "classification_status":"terminology_service_unavailable",
                    "missing_information": [],
                    "procedure_category": "",
                    "postoperative_bleeding_risk": ""
                }
            else:
                if procedure_type == "tooth_extraction":
                    procedure_assessment = assess_extraction(
                        procedure,
                        extraction_complexity,
                        wound_size,
                        guidelines
                    )
                elif procedure_type:
                    procedure_assessment = (
                        assess_other_procedure(
                            procedure_type,
                            guidelines
                        )
                    )
                else:
                    procedure_assessment = {
                        "procedure_type": "",
                        "classification_status": "procedure_not_mapped",
                        "missing_information": [],
                        "procedure_category": "",
                        "postoperative_bleeding_risk": ""
                    }

        procedure_assessment["procedure_name"] = procedure.get("procedure_name", "")
        procedure_assessment["procedure_code"] = procedure_code
        procedure_assessment["quantity"] = procedure.get("quantity", "")
        procedure_assessments.append(procedure_assessment)

    inr_category = classify_inr(inr_value)
    patient_context["clinical_assessment"] = {
        "procedure_assessments": procedure_assessments,
        "medication_context": {
            "usual_dose_time": str(usual_dose_time).strip().lower(),
            "inr_value": str(inr_value).strip(),
            "inr_category": inr_category,
            "inr_test_hours_ago":str(inr_test_hours_ago).strip(),
            "inr_is_stable": str(inr_is_stable).strip().lower(),
            "lmwh_dose_category": str(lmwh_dose_category).strip().lower(),
            "heparin_during_kidney_dialysis": str(heparin_during_kidney_dialysis).strip().lower()
        },
        "patient_safety": safety_context
    }
    return patient_context

# Hermes terminology ECL matching
def procedure_matches_ecl(
    procedure_code: str,
    ecl: str
):
    if not procedure_code or not ecl:
        return False
    url = f"{HERMES_BASE_URL}/v1/snomed/expand"
    membership_ecl = (f"({ecl}) AND {procedure_code}")
    response = requests.get(
        url,
        params={"ecl": membership_ecl}
    )
    response.raise_for_status()
    matching_codes = response.json()
    if matching_codes:
        return True
    return False

# Mapping the procedure type present in patient fhir to the value sets dictionaries
def find_procedure_type(procedure_code: str, value_sets: dict):
    procedure_value_sets = value_sets.get("procedure_value_sets",{})

    for procedure_type, procedure_details in procedure_value_sets.items():
        root_code = procedure_details.get("root_code", "")
        ecl = procedure_details.get("ecl", "")

        if procedure_code == root_code:
            return procedure_type

        if procedure_matches_ecl(procedure_code, ecl):
            return procedure_type

    return ""

def assess_other_procedure(procedure_type: str, guidelines: dict):
    procedure_assessment_rules = guidelines.get("procedure_assessment_rules",{})
    procedure_rules = procedure_assessment_rules.get(procedure_type,{})
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

def assess_extraction(
    procedure: dict,
    extraction_complexity: str,
    wound_size: str,
    guidelines: dict
):
    quantity = procedure.get("quantity", "")
    extraction_complexity = extraction_complexity.strip().lower()
    wound_size = wound_size.strip().lower()
    procedure_assessment_rules = guidelines.get("procedure_assessment_rules",{})
    extraction_rules = procedure_assessment_rules.get("tooth_extraction",{})

    missing_information = []
    if quantity == "":
        missing_information.append("number_of_teeth")
    if not extraction_complexity:
        missing_information.append("extraction_complexity")
    if not wound_size:
        missing_information.append("wound_size")
    if missing_information:
        result = extraction_rules.get("missing_information_result",{}).copy()
        result["missing_information"] = missing_information
        return result
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        result = extraction_rules.get("missing_information_result",{}).copy()
        result["missing_information"] = ["valid_number_of_teeth"]
        return result
    rules = extraction_rules.get("rules", [])
    for rule in rules:
        allowed_complexities = rule.get("extraction_complexity",[])
        if (
            allowed_complexities
            and extraction_complexity not in allowed_complexities
        ):
            continue
        allowed_wound_sizes = rule.get("wound_size", [])
        if (
            allowed_wound_sizes
            and wound_size not in allowed_wound_sizes
        ):
            continue
        minimum_teeth = rule.get("minimum_teeth")
        if (
            minimum_teeth is not None
            and quantity < minimum_teeth
        ):
            continue
        maximum_teeth = rule.get("maximum_teeth")
        if (
            maximum_teeth is not None
            and quantity > maximum_teeth
        ):
            continue

        result = rule.get("result", {}).copy()

        if "missing_information" not in result:
            result["missing_information"] = []

        return result

    result = extraction_rules.get("no_matching_rule_result",{}).copy()
    return result


def preview_patient_assessment():
    patient_id = "1256"

    assessed_context = assess_patient_context(
        patient_id,
        extraction_complexity="simple",
        wound_size="restricted"
    )

    pprint.pprint(assessed_context)


if __name__ == "__main__":
    preview_patient_assessment()