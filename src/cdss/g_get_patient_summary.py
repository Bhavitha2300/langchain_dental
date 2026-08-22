import requests

FHIR_BASE_URL = "http://localhost:8080/fhir"

def build_patient_context(patient, medications, conditions):
    first_name = patient["name"][0]["given"][0]
    last_name = patient["name"][0]["family"]

    medication_list = []

    for entry in medications.get("entry", []):
        medication = entry["resource"]["medicationCodeableConcept"]["text"]
        medication_list.append(medication)

    condition_list = []

    for entry in conditions.get("entry", []):
        condition = entry["resource"]["code"]["text"]
        condition_list.append(condition)

    patient_context = {
        "patient_id": patient["id"],
        "name": f"{first_name} {last_name}",
        "birth_date": patient["birthDate"],
        "gender": patient["gender"],
        "medications": medication_list,
        "conditions": condition_list
    }

    return patient_context