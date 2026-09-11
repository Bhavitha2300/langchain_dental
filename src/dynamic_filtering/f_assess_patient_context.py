# f_assess_patient_context.py

from pathlib import Path
import pprint
import yaml
from dynamic_filtering.e_terminology import enrich_patient_context


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VALUE_SETS_FILE = DATA_DIR / "sdcep_value_sets.yaml"


def load_value_sets():
    with open(VALUE_SETS_FILE, "r", encoding="utf-8") as file:
        value_sets = yaml.safe_load(file)

    return value_sets


def find_procedure_type(procedure_code: str, value_sets: dict):
    procedure_value_sets = value_sets.get("procedure_value_sets",{})

    for procedure_type, procedure_details in procedure_value_sets.items():
        root_code = procedure_details.get("root_code", "")

        if procedure_code == root_code:
            return procedure_type

    return ""


def assess_extraction(procedure: dict,extraction_complexity: str = "",wound_size: str = ""):
    quantity = procedure.get("quantity", "")
    missing_information = []

    if quantity == "":
        missing_information.append("number_of_teeth")

    if not extraction_complexity:
        missing_information.append("extraction_complexity")

    if not wound_size:
        missing_information.append("wound_size")

    if missing_information:
        return {
            "procedure_type": "tooth_extraction",
            "classification_status": ("needs_clinician_confirmation"),
            "missing_information": missing_information,
            "procedure_category": "",
            "postoperative_bleeding_risk": ""
        }

    extraction_complexity = extraction_complexity.strip().lower()
    wound_size = wound_size.strip().lower()

    # Low-risk extraction
    if (
        extraction_complexity == "simple"
        and 1 <= quantity <= 3
        and wound_size == "restricted"
    ):
        return {
            "procedure_type": "tooth_extraction",
            "classification_status": "classified",
            "missing_information": [],
            "procedure_category": (
                "simple_extraction_1_to_3_teeth_"
                "with_restricted_wound_size"
            ),
            "postoperative_bleeding_risk": "low"
        }

    # Clear higher-risk extraction features
    if (
            extraction_complexity in ["complex", "surgical"]
            or quantity > 3
    ):
        return {
            "procedure_type": "tooth_extraction",
            "classification_status": "classified",
            "missing_information": [],
            "procedure_category": "higher_risk_extraction",
            "postoperative_bleeding_risk": "higher"
        }

    if wound_size == "large":
        return {
            "procedure_type": "tooth_extraction",
            "classification_status": "requires_clinician_review",
            "missing_information": [
                "whether_extractions_are_adjacent"
            ],
            "procedure_category": "",
            "postoperative_bleeding_risk": ""
        }

    return {
        "procedure_type": "tooth_extraction",
        "classification_status": "requires_clinician_review",
        "missing_information": [],
        "procedure_category": "",
        "postoperative_bleeding_risk": ""
    }


def assess_patient_context(
    patient_id: str,
    extraction_complexity: str = "",
    wound_size: str = ""
):
    patient_context = enrich_patient_context(patient_id)
    value_sets = load_value_sets()

    medication_classes = []

    for medication in patient_context.get("medications", []):
        medication_class = medication.get(
            "medication_class",
            ""
        )

        if (
            medication_class
            and medication_class not in medication_classes
        ):
            medication_classes.append(medication_class)

    procedure_assessments = []

    for procedure in patient_context.get(
        "planned_procedures",
        []
    ):
        procedure_code = procedure.get("code", "")

        procedure_type = find_procedure_type(
            procedure_code,
            value_sets
        )

        if procedure_type == "tooth_extraction":
            procedure_assessment = assess_extraction(
                procedure,
                extraction_complexity,
                wound_size
            )
        else:
            procedure_assessment = {
                "procedure_type": procedure_type,
                "classification_status": "procedure_not_mapped",
                "missing_information": [],
                "procedure_category": "",
                "postoperative_bleeding_risk": ""
            }

        procedure_assessment["procedure_name"] = procedure.get(
            "procedure_name",
            ""
        )

        procedure_assessment["procedure_code"] = procedure_code
        procedure_assessment["quantity"] = procedure.get(
            "quantity",
            ""
        )

        procedure_assessments.append(procedure_assessment)

    patient_context["clinical_assessment"] = {
        "medication_classes": medication_classes,
        "procedure_assessments": procedure_assessments
    }

    return patient_context


def preview_patient_assessment():
    patient_id = "1000"

    assessed_context = assess_patient_context(
        patient_id,
        extraction_complexity="simple",
        wound_size="restricted"
    )

    pprint.pprint(assessed_context)


if __name__ == "__main__":
    preview_patient_assessment()