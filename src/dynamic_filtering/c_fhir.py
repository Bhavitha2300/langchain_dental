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

    # Conditions
    for entry in conditions.get("entry", []):
        condition = entry["resource"]
        condition_code = condition.get("code", {})
        condition_coding = (condition_code.get("coding", [{}])[0])
        body_site = (condition.get("bodySite", [{}])[0].get("text", ""))
        notes = [note.get("text", "")
            for note in condition.get("note", [])]

        fhir_patient_data["conditions"].append({
            "condition": condition_code.get("text", ""),
            "code_system": condition_coding.get("system", ""),
            "code": condition_coding.get("code", ""),
            "display": condition_coding.get("display", ""),
            "status": (condition.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")),
            "verification_status": (condition.get("verificationStatus", {}).get("coding", [{}])[0].get("code", "")),
            "body_site": body_site,
            "notes": notes
        })

    # Medications
    for entry in medications.get("entry", []):
        medication = entry["resource"]
        medication_concept = medication.get("medicationCodeableConcept",{})
        medication_coding = (medication_concept.get("coding", [{}])[0])
        dosage = (medication.get("dosageInstruction", [{}])[0])
        timing = (dosage.get("timing", {}).get("repeat", {}))
        route = dosage.get("route", {})
        route_coding = (route.get("coding", [{}])[0])
        dose_and_rate = (dosage.get("doseAndRate", [{}])[0])
        dose_quantity = dose_and_rate.get("doseQuantity",{})
        medication_reason = (medication.get("reasonReference", [{}])[0])

        fhir_patient_data["medications"].append({
            "medication": medication_concept.get("text", ""),
            "rxnorm_system": medication_coding.get("system", ""),
            "rxnorm_code": medication_coding.get("code", ""),
            "rxnorm_display": medication_coding.get("display",""),
            "status": medication.get("status", ""),
            "reason": medication_reason.get("display", ""),
            "reason_reference": medication_reason.get("reference",""),
            "dosage_text": dosage.get("text", ""),
            "dose_value": dose_quantity.get("value", ""),
            "dose_unit": dose_quantity.get("unit", ""),
            "frequency": timing.get("frequency", ""),
            "period": timing.get("period", ""),
            "period_unit": timing.get("periodUnit", ""),
            "route": route.get("text", ""),
            "route_code_system": route_coding.get("system",""),
            "route_code": route_coding.get("code", "")
        })

    # Planned procedures
    for entry in service_requests.get("entry", []):
        service_request = entry["resource"]
        procedure_concept = service_request.get("code",{})
        procedure_coding = (procedure_concept.get("coding", [{}])[0])
        quantity = service_request.get("quantityQuantity",{})
        body_site = (service_request.get("bodySite", [{}])[0].get("text", ""))
        procedure_reason = (service_request.get("reasonReference", [{}])[0])

        fhir_patient_data["planned_procedures"].append({
            "procedure": procedure_concept.get("text", ""),
            "code_system": procedure_coding.get("system", ""),
            "code": procedure_coding.get("code", ""),
            "display": procedure_coding.get("display", ""),
            "status": service_request.get("status", ""),
            "quantity": quantity.get("value", ""),
            "quantity_unit": quantity.get("unit", ""),
            "body_site": body_site,
            "reason": procedure_reason.get("display", ""),
            "reason_reference": procedure_reason.get("reference","")
        })

    return fhir_patient_data


def preview_patient_data():
    patient_id = "1000"
    fhir_patient_data = get_fhir_patient_data(patient_id)
    return fhir_patient_data


if __name__ == "__main__":
    pprint.pprint(preview_patient_data())


# Patient IDs: 1000, 1151, 1155