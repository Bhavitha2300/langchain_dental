# d_normalize_patient_context.py

from dynamic_filtering.c_fhir import get_fhir_patient_data


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

    for condition in fhir_patient_data.get("conditions", []):
        condition_name = condition.get("condition", "")
        normalized_context["conditions"].append({
            "condition": normalize_text(condition_name),
            "status": condition.get("status", "")
        })

    for medication in fhir_patient_data.get("medications", []):
        medication_name = medication.get("medication", "")
        normalized_context["medications"].append({
            "medication": normalize_text(medication_name),
            "status": medication.get("status", "")
        })

    for procedure in fhir_patient_data.get("planned_procedures", []):

        procedure_name = procedure.get("procedure", "")
        normalized_context["planned_procedures"].append({
            "procedure": normalize_text(procedure_name),
            "status": procedure.get("status", "")
        })

    return normalized_context


def preview_patient_data():
    patient_id = "1000"
    normalized_context = normalize_patient_context(patient_id)
    print(normalized_context)


if __name__ == "__main__":
    preview_patient_data()