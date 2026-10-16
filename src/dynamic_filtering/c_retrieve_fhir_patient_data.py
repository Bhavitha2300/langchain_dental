# c_retrieve_fhir_patient_data.py

import pprint
import requests

FHIR_BASE_URL = "http://localhost:8080/fhir"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SNOMED_SYSTEM = "http://snomed.info/sct"

def get_patient(patient_id):
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def get_conditions(patient_id):
    url = f"{FHIR_BASE_URL}/Condition"
    response = requests.get(url, params={"patient": patient_id})
    response.raise_for_status()
    return response.json()

def get_medications(patient_id):
    url = f"{FHIR_BASE_URL}/MedicationRequest"
    response = requests.get(url, params={"patient": patient_id})
    response.raise_for_status()
    return response.json()

def get_service_requests(patient_id):
    url = f"{FHIR_BASE_URL}/ServiceRequest"
    response = requests.get(url, params={"patient": patient_id})
    response.raise_for_status()
    return response.json()

def find_coding(code_object, required_system):
    for coding in code_object.get("coding", []):
        if coding.get("system", "") == required_system:
            return coding
    return {}

def get_fhir_patient_data(patient_id):
    patient = get_patient(patient_id)
    conditions = get_conditions(patient_id)
    medications = get_medications(patient_id)
    planned_procedures = get_service_requests(patient_id)

    # patient name
    name = patient.get("name", [{}])[0]
    first_name = name.get("given", [""])[0]
    last_name = name.get("family", "")
    full_name = f"{first_name} {last_name}"

    full_fhir_patient_details = {
        "name": full_name,
        "gender": patient.get("gender", ""),
        "birth_date": patient.get("birthDate", ""),
        "conditions": [],
        "medications": [],
        "planned_procedures": []
    }

    # Conditions
    condition_entries = conditions.get("entry", [])
    for each_entry in condition_entries:
        condition_resource = each_entry.get("resource", {})
        condition_code_object = condition_resource.get("code", {})
        condition_coding = find_coding(condition_code_object, SNOMED_SYSTEM)
        condition_code = condition_coding.get("code", "")
        condition_code_system = condition_coding.get("system", "")
        condition_status = condition_resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", "")
        condition_name = condition_coding.get("display", "") or condition_code_object.get("text", "")
        body_site = condition_resource.get("bodySite", [{}])[0].get("text", "")
        notes = []
        for note in condition_resource.get("note", []):
            notes.append(note.get("text", ""))

        full_fhir_patient_details["conditions"].append({
            "condition_name": condition_name,
            "body_site": body_site,
            "code_system": condition_code_system,
            "status": condition_status,
            "code": condition_code,
            "notes": notes
        })

    # Medications
    medication_entries = medications.get("entry", [])
    for each_entry in medication_entries:
        medication_resource = each_entry.get("resource", {})
        medication_status = medication_resource.get("status", "")
        if medication_status != "active":
            continue
        if medication_resource.get("doNotPerform", False):
            continue
        medication_code_object = medication_resource.get("medicationCodeableConcept", {})
        medication_coding = find_coding(medication_code_object, RXNORM_SYSTEM)
        medication_name = medication_code_object.get("text", "") or medication_coding.get("display", "")
        dosage = medication_resource.get("dosageInstruction", [{}])[0]
        timing = dosage.get("timing", {}).get("repeat", {})
        dose_and_rate = dosage.get("doseAndRate", [{}])[0]
        dose_quantity = dose_and_rate.get("doseQuantity", {})
        reason_reference = medication_resource.get("reasonReference", [{}])[0]

        full_fhir_patient_details["medications"].append({
            "medication_name": medication_name,
            "rxnorm_system": medication_coding.get("system", ""),
            "rxnorm_code": medication_coding.get("code", ""),
            "status": medication_status,
            "reason": reason_reference.get("display", ""),
            "dose_value": dose_quantity.get("value", ""),
            "dose_unit": dose_quantity.get("unit", ""),
            "frequency": timing.get("frequency", ""),
            "period": timing.get("period", ""),
            "period_unit": timing.get("periodUnit", ""),
            "route": dosage.get("route", {}).get("text", "")
        })

    # Planned procedures
    procedure_entries = planned_procedures.get("entry", [])
    for each_entry in procedure_entries:
        procedure_resource = each_entry.get("resource", {})
        procedure_status = procedure_resource.get("status", "")
        if procedure_status != "active":
            continue
        if procedure_resource.get("doNotPerform", False):
            continue
        procedure_code_object = procedure_resource.get("code", {})
        procedure_coding = find_coding(procedure_code_object, SNOMED_SYSTEM)
        procedure_name = procedure_code_object.get("text", "") or procedure_coding.get("display", "")
        quantity = procedure_resource.get("quantityQuantity", {})
        body_site = procedure_resource.get("bodySite", [{}])[0].get("text", "")
        reason_reference = procedure_resource.get("reasonReference", [{}])[0]

        full_fhir_patient_details["planned_procedures"].append({
            "procedure_name": procedure_name,
            "code_system": procedure_coding.get("system", ""),
            "code": procedure_coding.get("code", ""),
            "status": procedure_status,
            "quantity": quantity.get("value", ""),
            "quantity_unit": quantity.get("unit", ""),
            "body_site": body_site,
            "reason": reason_reference.get("display", ""),
            "do_not_perform": procedure_resource.get("doNotPerform", False)
        })

    return full_fhir_patient_details

def preview_patient_data():
    patient_id = "1301"
    fhir_patient_data = get_fhir_patient_data(patient_id)
    pprint.pprint(fhir_patient_data)


if __name__ == "__main__":
    preview_patient_data()

# Patient IDs: 1000, 1151, 1155, 1256, 1301, 1306