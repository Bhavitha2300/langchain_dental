# f_patient_safety_checks.py
# - this file check if there is enough information to get a recommendation

from dynamic_filtering.a_load_split_guidelines import normalize_value

MEDICATION_CLASSES_PRESENT_IN_GUIDELINES = [
    "doac",
    "vitamin_k_antagonist",
    "low_molecular_weight_heparin",
    "unfractionated_heparin",
    "antiplatelet"]

# This function checks safety answers from the clinician
def find_patient_safety_reasons(assessed_context: dict):
    safety_reasons = []
    clinical_assessment = assessed_context.get("clinical_assessment", {})
    patient_safety = clinical_assessment.get("patient_safety", {})
    # These are the safety questions that must have yes/no answers
    required_questions = [
        "medical_history_and_medicines_reviewed",
        "therapy_must_not_be_interrupted",
        "additional_bleeding_risk_condition",
        "bleeding_history_concern"]
    for question in required_questions:
        answer = patient_safety.get(question, "")
        if answer not in ["yes", "no"]:
            safety_reasons.append({"reason": "missing_safety_information",
                                   "missing_information": [question]})
    if patient_safety.get("medical_history_and_medicines_reviewed", "") == "no":
        safety_reasons.append({"reason": "clinical_information_not_reviewed",
                               "message": "Review the patient's medical history and medicines before continuing."})
    has_anticoagulant = False
    has_antiplatelet = False
    for medication in assessed_context.get("medications", []):
        medication_class = medication.get("medication_class", "")
        if medication_class in ["doac", "vitamin_k_antagonist", "low_molecular_weight_heparin", "unfractionated_heparin"]:
            has_anticoagulant = True
        if medication_class == "antiplatelet":
            has_antiplatelet = True
    if has_anticoagulant and has_antiplatelet:
        return safety_reasons
    doac_ingredients = []
    for medication in assessed_context.get("medications", []):
        if medication.get("medication_class", "") == "doac":
            ingredient_name = normalize_value(medication.get("ingredient_name", ""))
            doac_ingredients.append(ingredient_name)
    if doac_ingredients:
        urgent_dental_procedure = patient_safety.get("urgent_dental_procedure", "")
        if urgent_dental_procedure not in ["yes", "no"]:
            safety_reasons.append({"reason": "procedure_urgency_missing",
                                   "message": "Confirm whether the dental procedure is urgent."})
        elif urgent_dental_procedure == "yes":
            morning_dose_taken = patient_safety.get("morning_doac_dose_already_taken","")
            if morning_dose_taken not in ["yes", "no"]:
                safety_reasons.append({"reason": "morning_doac_dose_information_missing",
                                       "message": "Confirm whether the patient has already taken the morning DOAC dose."})
    if "apixaban" in doac_ingredients or "rivaroxaban" in doac_ingredients:
        initial_high_dose = patient_safety.get("initial_high_dose_doac","")
        if initial_high_dose not in ["yes", "no"]:
            safety_reasons.append({"reason": "initial_high_dose_information_missing",
                                   "message": "Confirm whether the patient is taking initial high-dose apixaban or rivaroxaban."})
    higher_risk_procedure = False
    for procedure in clinical_assessment.get("procedure_assessments",[]):
        bleeding_risk = procedure.get("postoperative_bleeding_risk","")
        if bleeding_risk == "higher":
            higher_risk_procedure = True
    urgent_after_morning_dose = (patient_safety.get("urgent_dental_procedure", "") == "yes" and patient_safety.get("morning_doac_dose_already_taken","") == "yes")
    therapy_must_not_be_interrupted = patient_safety.get("therapy_must_not_be_interrupted","" )
    if higher_risk_procedure:
        if ("rivaroxaban" in doac_ingredients or "edoxaban" in doac_ingredients):
            if (not urgent_after_morning_dose and therapy_must_not_be_interrupted != "yes"):
                usual_dose_time = patient_safety.get("usual_dose_time","")
                if usual_dose_time not in ["morning", "evening"]:
                    safety_reasons.append({"reason": "usual_dose_time_missing",
                                           "message": "Confirm whether the patient normally takes the medication in the morning or evening."})
    has_low_molecular_weight_heparin = False
    has_unfractionated_heparin = False
    for medication in assessed_context.get("medications", []):
        medication_class = medication.get("medication_class", "")
        if medication_class == "low_molecular_weight_heparin":
            has_low_molecular_weight_heparin = True
        elif medication_class == "unfractionated_heparin":
            has_unfractionated_heparin = True
    if has_low_molecular_weight_heparin:
        lmwh_dose_category = patient_safety.get("lmwh_dose_category","")
        if lmwh_dose_category not in ["prophylactic_low", "treatment_higher", "uncertain"]:
            safety_reasons.append({"reason": "lmwh_dose_category_missing",
                                   "message": "Confirm whether the LMWH dose is prophylactic, treatment, or uncertain."})
    if (has_low_molecular_weight_heparin or has_unfractionated_heparin):
        dialysis_heparin = patient_safety.get("heparin_during_kidney_dialysis","")
        if dialysis_heparin not in ["yes", "no"]:
            safety_reasons.append({ "reason": "kidney_dialysis_heparin_information_missing",
                                    "message": "Confirm whether the patient receives heparin or LMWH during kidney dialysis."})
    has_vitamin_k_antagonist = False
    for medication in assessed_context.get("medications", []):
        medication_class = medication.get("medication_class", "")
        if medication_class == "vitamin_k_antagonist":
            has_vitamin_k_antagonist = True
    if has_vitamin_k_antagonist:
        inr_value = patient_safety.get("inr_value", "")
        inr_test_time = patient_safety.get("inr_test_time", "")
        if inr_value is None or inr_value == "":
            safety_reasons.append({"reason": "inr_value_missing",
                                   "message": "The patient's latest INR value is required."})
        else:
            try:
                inr_value = float(str(inr_value))
            except ValueError:
                inr_value = 0.0
            if not (0 < inr_value < float("inf")):
                safety_reasons.append({"reason": "invalid_inr_value",
                                       "message": "Enter a valid INR value greater than zero."})
        if not inr_test_time:
            safety_reasons.append({"reason": "inr_test_time_missing",
                                   "message": "The time of the latest INR test is required."})
        elif inr_test_time == "more_than_72_hours":
            safety_reasons.append({"reason": "inr_test_is_too_old",
                                   "message": "The INR must be checked again before treatment."})
        elif inr_test_time == "more_than_24_up_to_72_hours":
            inr_is_stable = patient_safety.get("inr_is_stable", "")
            if inr_is_stable != "yes":
                safety_reasons.append({"reason": "inr_requires_recent_test",
                                       "message": "The INR must be checked no more than 24 hours before treatment."})
    treatment_duration = patient_safety.get("antithrombotic_treatment_duration", "")
    treatment_duration = treatment_duration.strip().lower().replace(" ", "_")
    if treatment_duration not in ["long_term", "time_limited"]:
        safety_reasons.append({"reason": "missing_safety_information",
                               "missing_information": ["antithrombotic_treatment_duration"]})
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
    elif not procedure_assessments:
        blocking_reasons.append({"reason": "procedure_assessment_missing",
                                 "message": "The planned dental procedure has not been assessed."})
    for procedure_assessment in procedure_assessments:
        classification_status = procedure_assessment.get("classification_status", "")
        if classification_status != "classified":
            blocking_reasons.append({"reason": classification_status,
                                     "missing_information": procedure_assessment.get("missing_information", []),
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
            "unfractionated_heparin"]:
            if ingredient_name not in anticoagulants:
                anticoagulants.append(ingredient_name)
        if medication_class == "antiplatelet":
            if ingredient_name not in antiplatelets:
                antiplatelets.append(ingredient_name)
    if len(anticoagulants) > 1:
        blocking_reasons.append({"reason": "multiple_anticoagulants",
                                 "message": "Multiple anticoagulants need clinician review."})
    return blocking_reasons

def preview_patient_safety_checks():
    import pprint
    from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
    patient_id = "1256"
    assessed_context = assess_patient_context(patient_id)
    assessed_context["clinical_assessment"]["patient_safety"] = {
        "medical_history_and_medicines_reviewed": "yes",
        "therapy_must_not_be_interrupted": "no",
        "additional_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "urgent_dental_procedure": "no",
        "morning_doac_dose_already_taken": "no",
        "initial_high_dose_doac": "no",
        "usual_dose_time": "morning",
        "antithrombotic_treatment_duration": "long_term"
    }
    print("Safety warnings:")
    pprint.pprint(find_safety_warnings(assessed_context))
    print("Blocking reasons:")
    pprint.pprint(find_blocking_reasons(assessed_context))

if __name__ == "__main__":
    preview_patient_safety_checks()