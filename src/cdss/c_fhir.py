import requests


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

    fhir_patient_data = {
        "patient": patient,
        "medication_requests": medications,
        "conditions": conditions,
        "service_requests": service_requests
    }

    return fhir_patient_data

def preview_patient_summary():
    patient_id = "1155"
    fhir_patient_data = get_fhir_patient_data(patient_id)
    print(fhir_patient_data)


if __name__ == "__main__":
    preview_patient_summary()


# ids = 1000, 1151, 1155,