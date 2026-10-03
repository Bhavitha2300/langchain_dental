# f_patient_safety_checks.py
# - this file check if there is enough information to get a recommendation

from dynamic_filtering.a_load_split_guidelines import normalize_value

MEDICATION_CLASSES_PRESENT_IN_GUIDELINES = [
    "doac",
    "vitamin_k_antagonist",
    "low_molecular_weight_heparin",
    "unfractionated_heparin",
    "antiplatelet"
]

# This function checks safety answers from the clinician
def find_patient_safety_reasons(assessed_context: dict):
    safety_reasons = []
    clinical_assessment = assessed_context.get("clinical_assessment", {})
    patient_safety = clinical_assessment.get("patient_safety", {})
    # These are the safety questions that must have yes/no answers
    required_questions = [
        "medical_history_and_medicines_reviewed",
        "high_risk_reason_for_anticoagulant",
        "additional_bleeding_risk_condition",
        "bleeding_history_concern"
    ]
    for question in required_questions:
        answer = patient_safety.get(question, "")
        if answer not in ["yes", "no"]:
            safety_reasons.append({"reason": "missing_safety_information",
                                   "missing_information": [question]})

    if patient_safety.get("medical_history_and_medicines_reviewed", "") == "no":
        safety_reasons.append({"reason": "clinical_information_not_reviewed",
                               "message": "Review the patient's medical history and medicines before continuing."})
    if patient_safety.get("medication_list_reviewed", "") == "no":
        safety_reasons.append({"reason": "medication_list_not_reviewed",
                               "message": "Review medication list before continuing."})
    if patient_safety.get("high_risk_reason_for_anticoagulant", "") == "yes":
        safety_reasons.append({"reason": "high_risk_reason_for_anticoagulant",
                               "message": "The patient has a high-risk reason for taking anticoagulant or antiplatelet medicine. Clinician review is required before changing medication."})
    if patient_safety.get("additional_bleeding_risk_condition", "") == "yes":
        safety_reasons.append({"reason": "additional_bleeding_risk_requires_review",
                               "message": "A medical condition may increase the patient's bleeding risk. Clinician review is required."})
    if patient_safety.get("bleeding_history_concern", "") == "yes":
        safety_reasons.append({"reason": "bleeding_history_requires_review",
                               "message": "The patient has a relevant history of prolonged or excessive bleeding."})
    if patient_safety.get("initial_high_dose_doac", "") == "yes":
        safety_reasons.append({"reason": "initial_high_dose_doac",
                               "message": "A procedure likely to cause bleeding should be delayed where possible until the patient is taking the standard dose."})

    treatment_duration = patient_safety.get("antithrombotic_treatment_duration", "")
    treatment_duration = treatment_duration.strip().lower().replace(" ", "_")
    if treatment_duration not in ["long_term", "time_limited"]:
        safety_reasons.append({"reason": "missing_safety_information",
                               "missing_information": ["antithrombotic_treatment_duration"]})
    elif treatment_duration == "time_limited":
        safety_reasons.append({"reason": "time_limited_treatment_requires_review",
                               "message": "The treatment is time-limited. Clinician review is required before deciding whether dental treatment should be delayed."})

    return safety_reasons

def find_nsaid_safety_warnings(assessed_context):
    safety_warnings = []
    medications = assessed_context.get("medications", [])
    for medication in medications:
        medication_class = medication.get("medication_class", "")
        if medication_class == "nsaid":
            medication_name = medication.get("medication_name", "")
            safety_warnings.append({"reason": "nsaid_may_increase_bleeding_risk",
                                    "message": f"{medication_name} may increase bleeding risk."})

    return safety_warnings

def find_safety_warnings(assessed_context):
    safety_warnings = []
    safety_warnings.extend(find_nsaid_safety_warnings(assessed_context))

    return safety_warnings

def find_blocking_reasons(assessed_context):
    blocking_reasons = []
    blocking_reasons.extend(find_patient_safety_reasons(assessed_context))

    planned_procedures = assessed_context.get("planned_procedures", [])
    medications = assessed_context.get("medications", [])
    clinical_assessment = assessed_context.get("clinical_assessment", {})
    procedure_assessments = clinical_assessment.get("procedure_assessments", [])

    if not planned_procedures:
        blocking_reasons.append({"reason": "no_planned_procedure",
                                 "message": "No planned dental procedure was found."})
    for procedure_assessment in procedure_assessments:
        classification_status = procedure_assessment.get("classification_status", "")
        if classification_status != "classified":
            blocking_reasons.append({"reason": classification_status,
                                     "message": "The planned procedure could not be safely classified."})

    mapped_antithrombotic_medications = []
    for medication in medications:
        terminology_status = medication.get("terminology_status", "")
        medication_class = medication.get("medication_class", "")
        ingredient_name = medication.get("ingredient_name", "")

        if terminology_status != "mapped":
            blocking_reasons.append({"reason": terminology_status,
                                     "message": "Medication terminology could not be mapped."})
        elif medication_class in MEDICATION_CLASSES_PRESENT_IN_GUIDELINES:
            mapped_antithrombotic_medications.append(medication)
    if not mapped_antithrombotic_medications:
        blocking_reasons.append({"reason": "antithrombotic_not_mapped",
                                 "message": "No supported anticoagulant or antiplatelet medication was mapped."})
    anticoagulants = []
    antiplatelets = []

    for medication in mapped_antithrombotic_medications:
        medication_class = medication.get("medication_class", "")
        ingredient_name = normalize_value(medication.get("ingredient_name", ""))
        if medication_class in [
            "doac",
            "vitamin_k_antagonist",
            "low_molecular_weight_heparin",
            "unfractionated_heparin"
        ]:
            if ingredient_name not in anticoagulants:
                anticoagulants.append(ingredient_name)
        if medication_class == "antiplatelet":
            if ingredient_name not in antiplatelets:
                antiplatelets.append(ingredient_name)
    if anticoagulants and antiplatelets:
        blocking_reasons.append({ "reason": "anticoagulant_and_antiplatelet_combination",
                                  "message": "Anticoagulant and antiplatelet combination therapy needs clinician review."})
    if len(anticoagulants) > 1:
        blocking_reasons.append({
            "reason": "multiple_anticoagulants",
            "message": "Multiple anticoagulants need clinician review."
        })
    return blocking_reasons

def preview_patient_safety_checks():
    import pprint
    from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context

    patient_id = "1256"
    assessed_context = assess_patient_context(patient_id)
    assessed_context["clinical_assessment"]["patient_safety"] = {
        "medical_history_and_medicines_reviewed": "yes",
        "high_risk_reason_for_anticoagulant": "no",
        "additional_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "initial_high_dose_doac": "no",
        "antithrombotic_treatment_duration": "time_limited"
    }
    print("Safety warnings:")
    pprint.pprint(find_safety_warnings(assessed_context))
    print()
    print("Blocking reasons:")
    pprint.pprint(find_blocking_reasons(assessed_context))

if __name__ == "__main__":
    preview_patient_safety_checks()