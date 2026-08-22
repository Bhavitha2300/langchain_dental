import requests


FHIR_BASE_URL = "http://localhost:8080/fhir"


def get_patient(patient_id: str):
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_medications(patient_id: str):
    url = f"{FHIR_BASE_URL}/MedicationRequest?patient={patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_conditions(patient_id: str):
    url = f"{FHIR_BASE_URL}/Condition?patient={patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_service_requests(patient_id: str):
    url = f"{FHIR_BASE_URL}/ServiceRequest?patient={patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def main():
    patient_id = "1000"

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

    print(fhir_patient_data)


if __name__ == "__main__":
    main()