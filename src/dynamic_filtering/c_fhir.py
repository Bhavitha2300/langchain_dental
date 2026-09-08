# c_fhir.py

import requests
import pprint


FHIR_BASE_URL = "http://localhost:8080/fhir"


def get_patient(patient_id: str):
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_medications(patient_id: str):
    url = f"{FHIR_BASE_URL}/MedicationRequest"
    response = requests.get(url,params={"patient": patient_id})
    response.raise_for_status()
    return response.json()


def get_conditions(patient_id: str):
    url = f"{FHIR_BASE_URL}/Condition"
    response = requests.get(url,params={"patient": patient_id})
    response.raise_for_status()
    return response.json()


def get_service_requests(patient_id: str):
    url = f"{FHIR_BASE_URL}/ServiceRequest"
    response = requests.get(url,params={"patient": patient_id})
    response.raise_for_status()
    return response.json()


def get_fhir_patient_data(patient_id: str):
    patient = get_patient(patient_id)
    medications = get_medications(patient_id)
    conditions = get_conditions(patient_id)
    service_requests = get_service_requests(patient_id)

    name_data = patient.get("name", [{}])[0]
    first_name = name_data.get("given", [""])[0]
    last_name = name_data.get("family", "")
    full_name = f"{first_name} {last_name}".strip() or "Unknown"


    fhir_patient_data = {
        "name": full_name,
        "gender": patient.get("gender", ""),
        "birth_date": patient.get("birthDate", ""),
        "conditions": [],
        "medications": [],
        "planned_procedures": []
    }

    for entry in conditions.get("entry", []):
        condition = entry["resource"]
        fhir_patient_data["conditions"].append({
            "condition": condition["code"].get("text", ""),
            "status": condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
        })

    for entry in medications.get("entry", []):
        medication = entry["resource"]
        fhir_patient_data["medications"].append({
            "medication": medication.get("medicationCodeableConcept", {}).get("text", ""),
            "status": medication.get("status", "")
        })

    for entry in service_requests.get("entry", []):
        service_request = entry["resource"]
        fhir_patient_data["planned_procedures"].append({
            "procedure": service_request.get("code", {}).get("text", ""),
            "status": service_request.get("status", "")
        })

    return fhir_patient_data

def preview_patient_data():
    patient_id = "1000"
    fhir_patient_data = get_fhir_patient_data(patient_id)
    return fhir_patient_data


if __name__ == "__main__":
    # preview_patient_data()
    pprint.pprint(preview_patient_data())


# ids = 1000, 1151, 1155,