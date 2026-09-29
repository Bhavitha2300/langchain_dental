# d_normalize_patient_context.py

import pprint

from dynamic_filtering.c_retrieve_fhir_patient_data import get_fhir_patient_data


def normalize_text(value: str):
    normalized_value = (value.strip().lower().replace("-", "_").replace(" ", "_"))

    return normalized_value


def normalize_patient_context(patient_id: str):
    fhir_patient_data = get_fhir_patient_data(patient_id)

    normalized_context = {
        "name": fhir_patient_data.get("name", ""),
        "gender": fhir_patient_data.get("gender", ""),
        "birth_date": fhir_patient_data.get("birth_date", ""),
        "conditions": [],
        "medications": [],
        "planned_procedures": []
    }

    # Normalize conditions
    for condition in fhir_patient_data.get("conditions", []):
        condition_name = (condition.get("display") or condition.get("condition", ""))

        normalized_context["conditions"].append({
            "condition_name": condition_name,
            "condition_key": normalize_text(condition_name),
            "code_system": condition.get("code_system", ""),
            "code": condition.get("code", ""),
            "status": condition.get("status", ""),
            "verification_status": condition.get("verification_status",""),
            "body_site": condition.get("body_site", ""),
            "notes": condition.get("notes", [])
        })

    # Normalize medications
    for medication in fhir_patient_data.get("medications", []):
        medication_name = medication.get("medication", "")

        normalized_context["medications"].append({
            "medication_name": medication_name,
            "medication_key": normalize_text(medication_name),
            "rxnorm_system": medication.get("rxnorm_system", ""),
            "rxnorm_code": medication.get("rxnorm_code", ""),
            "status": medication.get("status", ""),
            "reason": medication.get("reason", ""),
            "dose_value": medication.get("dose_value", ""),
            "dose_unit": medication.get("dose_unit", ""),
            "frequency": medication.get("frequency", ""),
            "period": medication.get("period", ""),
            "period_unit": medication.get("period_unit", ""),
            "route": medication.get("route", "")
        })

    # Normalize planned procedures
    for procedure in fhir_patient_data.get("planned_procedures",[]):
        procedure_name = procedure.get("procedure", "")

        normalized_context["planned_procedures"].append({
            "procedure_name": procedure_name,
            "procedure_key": normalize_text(procedure_name),
            "code_system": procedure.get("code_system", ""),
            "code": procedure.get("code", ""),
            "status": procedure.get("status", ""),
            "quantity": procedure.get("quantity", ""),
            "quantity_unit": procedure.get("quantity_unit",""),
            "body_site": procedure.get("body_site", ""),
            "reason": procedure.get("reason", "")
        })

    return normalized_context


def preview_patient_data():
    patient_id = "1000"
    normalized_context = normalize_patient_context(patient_id)
    pprint.pprint(normalized_context)


if __name__ == "__main__":
    preview_patient_data()