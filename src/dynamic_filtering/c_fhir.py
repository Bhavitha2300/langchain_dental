# c_fhir.py

import requests
import pprint


FHIR_BASE_URL = "http://localhost:8080/fhir"
FHIR_TIMEOUT = 10
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED_SYSTEM = "http://snomed.info/sct"

INACTIVE_MEDICATION_STATUSES = {
    "cancelled",
    "completed",
    "entered-in-error",
    "stopped"
}

INACTIVE_SERVICE_REQUEST_STATUSES = {
    "revoked",
    "completed",
    "entered-in-error"
}


def get_patient(patient_id: str):
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url, timeout=FHIR_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_medications(patient_id: str):
    url = f"{FHIR_BASE_URL}/MedicationRequest"
    response = requests.get(url,params={"patient": patient_id}, timeout=FHIR_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_conditions(patient_id: str):
    url = f"{FHIR_BASE_URL}/Condition"
    response = requests.get(url,params={"patient": patient_id}, timeout=FHIR_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_service_requests(patient_id: str):
    url = f"{FHIR_BASE_URL}/ServiceRequest"
    response = requests.get(url,params={"patient": patient_id}, timeout=FHIR_TIMEOUT)
    response.raise_for_status()
    return response.json()


def get_fhir_patient_data(patient_id: str):
    patient = get_patient(patient_id)
    medications = get_medications(patient_id)
    conditions = get_conditions(patient_id)
    service_requests = get_service_requests(patient_id)

    # name
    name_data = patient.get("name", [{}])[0]
    first_name = name_data.get("given", [""])[0]
    last_name = name_data.get("family", "")
    full_name = f"{first_name} {last_name}".strip() or "Unknown"

    normalized_fhir_patient_data = {
        "name": full_name,
        "gender": patient.get("gender", ""),
        "birth_date": patient.get("birthDate", ""),
        "conditions": [],
        "medications": [],
        "planned_procedures": []
    }

    # Conditions
    for entry in conditions.get("entry", []):
        condition = entry["resource"]
        condition_code = condition.get("code", {})
        condition_coding = (condition_code.get("coding", [{}])[0])
        condition_name = (condition_coding.get("display") or condition_code.get("text", ""))
        body_site = (condition.get("bodySite", [{}])[0].get("text", ""))
        notes = [note.get("text", "")
            for note in condition.get("note", [])]

        normalized_fhir_patient_data["conditions"].append({
            "condition_name": condition_name,
            "code_system": condition_coding.get("system", ""),
            "code": condition_coding.get("code", ""),
            "status": (condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")),
            "verification_status": (condition.get("verificationStatus", {}).get("coding", [{}])[0].get("code", "")),
            "body_site": body_site,
            "notes": notes
        })

    # Medications
    for entry in medications.get("entry", []):
        medication = entry["resource"]
        medication_status = medication.get("status", "")
        if medication_status != "active":
            continue
        medication_concept = medication.get("medicationCodeableConcept",{})
        medication_coding = (medication_concept.get("coding", [{}])[0])
        if medication_coding.get("system", "") != RXNORM_SYSTEM:
            medication_coding = {}
        medication_name = medication_concept.get("text") or medication_coding.get("display", "")
        dosage = (medication.get("dosageInstruction", [{}])[0])
        timing = (dosage.get("timing", {}).get("repeat", {}))
        route = dosage.get("route", {})
        dose_and_rate = (dosage.get("doseAndRate", [{}])[0])
        dose_quantity = dose_and_rate.get("doseQuantity",{})
        medication_reason = (medication.get("reasonReference", [{}])[0])

        normalized_fhir_patient_data["medications"].append({
            "medication_name": medication_name,
            "rxnorm_system": medication_coding.get("system", ""),
            "rxnorm_code": medication_coding.get("code", ""),
            "status": medication_status,
            "reason": medication_reason.get("display", ""),
            "dose_value": dose_quantity.get("value", ""),
            "dose_unit": dose_quantity.get("unit", ""),
            "frequency": timing.get("frequency", ""),
            "period": timing.get("period", ""),
            "period_unit": timing.get("periodUnit", ""),
            "route": route.get("text", ""),
            "resource_id": medication.get("id", ""),
            "intent": medication.get("intent", "")
        })

    # Planned procedures
    for entry in service_requests.get("entry", []):
        service_request = entry["resource"]
        request_status = service_request.get("status", "")
        if request_status != "active":
            continue
        procedure_concept = service_request.get("code",{})
        procedure_coding = (procedure_concept.get("coding", [{}])[0])
        if procedure_coding.get("system", "") != SNOMED_SYSTEM:
            procedure_coding = {}
        procedure_name = procedure_concept.get("text") or procedure_coding.get("display", "")
        quantity = service_request.get("quantityQuantity",{})
        body_site = (service_request.get("bodySite", [{}])[0].get("text", ""))
        procedure_reason = (service_request.get("reasonReference", [{}])[0])

        normalized_fhir_patient_data["planned_procedures"].append({
            "procedure_name": procedure_name,
            "code_system": procedure_coding.get("system", ""),
            "code": procedure_coding.get("code", ""),
            "status": request_status,
            "quantity": quantity.get("value", ""),
            "quantity_unit": quantity.get("unit", ""),
            "body_site": body_site,
            "reason": procedure_reason.get("display", ""),
            "resource_id": service_request.get("id", ""),
            "intent": service_request.get("intent", ""),
            "do_not_perform": service_request.get(
                "doNotPerform",
                False)
        })

    return normalized_fhir_patient_data


def preview_patient_data():
    patient_id = "1256"
    fhir_patient_data = get_fhir_patient_data(patient_id)
    return fhir_patient_data


if __name__ == "__main__":
    pprint.pprint(preview_patient_data())


# Patient IDs: 1000, 1151, 1155, 1256