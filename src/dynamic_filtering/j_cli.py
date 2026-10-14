# j_cli.py

import typer
from langchain_core.chat_history import InMemoryChatMessageHistory
from dynamic_filtering.d_medication_terminology import add_medication_class_to_fhir_patient_data
from dynamic_filtering.i_final_LLM_recommendation import final_response
from dynamic_filtering.k_jev import classify_clinician_question

# ask yes or no questions
def ask_yes_no(question):
    while True:
        answer = typer.prompt(f"{question} (yes/no)")
        answer = answer.strip().lower()
        if answer in ["yes","y"]:
            return "yes"
        if answer in ["no","n"]:
            return "no"
        print("Please enter yes or no.")

def ask_choice(question, allowed_values):
    print(question)
    option_number = 1
    for value in allowed_values:
        display_value = value.replace("_", " ")
        print(f"{option_number}. {display_value}")
        option_number = option_number + 1
    while True:
        answer = typer.prompt("Enter option number")
        if answer.isdigit():
            selected_number = int(answer)
            if 1 <= selected_number <= len(allowed_values):
                return allowed_values[selected_number - 1]
            print(f"Please enter a number from 1 to {len(allowed_values)}.")

def get_medication_classes(patient_context):
    medication_classes = []
    medications = patient_context.get("medications", [])
    for medication in medications:
        medication_class = medication.get("medication_class", "")
        # if medication class exists and we have not already added it
        if medication_class and medication_class not in medication_classes:
            medication_classes.append(medication_class)
    return medication_classes

def show_patient_summary(patient_id, patient_context):
    print()
    print("Selected patient:")
    print()
    print(f"Patient ID: {patient_id}")
    print(f"Name: {patient_context.get('name', '')}")
    print(f"Gender: {patient_context.get('gender', '')}")
    print(f"Birth date: {patient_context.get('birth_date', '')}")
    print()
    print("Patient clinical information:")
    print()
    print("Conditions:")
    for condition in patient_context.get("conditions", []):
        print(condition.get("condition_name", ""))
    print()
    print("Medications:")
    for medication in patient_context.get("medications", []):
        print(medication.get("medication_name", ""))
        print(f"  Medication class: {medication.get('medication_class', '')}")
    print()
    print("Planned procedures:")
    for procedure in patient_context.get("planned_procedures", []):
        print(procedure.get("procedure_name", ""))

def confirm_patient(patient_id):
    while True:
        patient_context = add_medication_class_to_fhir_patient_data(patient_id)
        show_patient_summary(patient_id, patient_context)
        correct_patient = typer.confirm("Is this the correct patient?")
        if correct_patient:
            print("Patient confirmed.")
            return patient_id, patient_context
        print("Please check the patient ID.")
        patient_id = typer.prompt("Enter the correct patient ID")

def collect_safety_context(patient_context):
    safety_context = {}
    print()
    print("Patient safety questions:")
    safety_context["medical_history_and_medicines_reviewed"] = ask_yes_no("Have the patient's medical history and medicines been reviewed?")
    safety_context["therapy_must_not_be_interrupted"] = ask_yes_no( "Does the patient have a prosthetic metal heart valve, coronary stent, DVT or PE within the last 3 months, or anticoagulation for cardioversion?")
    extra_risk_present = ask_yes_no("Does the patient have any extra condition that may increase bleeding risk?")
    if extra_risk_present == "yes":
        safety_context["additional_bleeding_risk_condition"] = ask_yes_no("Does the patient have renal disease, liver disease, bone marrow disorder, or another condition increasing bleeding risk?")
        safety_context["bleeding_history_concern"] = ask_yes_no("Does the patient have a history of prolonged or excessive bleeding?")
    else:
        safety_context["additional_bleeding_risk_condition"] = "no"
        safety_context["bleeding_history_concern"] = "no"
    medication_classes = get_medication_classes(patient_context)
    has_anticoagulant = ("doac" in medication_classes or "vitamin_k_antagonist" in medication_classes or "low_molecular_weight_heparin" in medication_classes or "unfractionated_heparin" in medication_classes)
    has_antiplatelet = "antiplatelet" in medication_classes
    if has_anticoagulant and has_antiplatelet:
        print("The patient is taking an anticoagulant and antiplatelet combination.")
        return safety_context
    # medication class: vitamin_k_antagonists
    if "vitamin_k_antagonist" in medication_classes:
        safety_context["inr_value"] = typer.prompt("Enter the patient's latest INR value", type=float)
        safety_context["inr_test_time"] = ask_choice("When was the INR checked?", ["within_24_hours", "more_than_24_up_to_72_hours", "more_than_72_hours"])
        if safety_context["inr_test_time"] == "more_than_24_up_to_72_hours":
            print()
            print("An INR checked more than 24 hours ago can only be used if:")
            print("- The patient does not require weekly INR monitoring. The patient has had no INR measurements above 4 during the previous two months. There is no reason to believe the result no longer reflects the patient's current INR.")
            print()
            safety_context["inr_is_stable"] = ask_yes_no("Does the patient meet all these conditions?")
    # medication class: low molecular weight heparin
    if "low_molecular_weight_heparin" in medication_classes:
        print()
        print("If the LMWH dose category cannot be confirmed, choose uncertain.")
        safety_context["lmwh_dose_category"] = ask_choice("What type of LMWH dose is the patient taking?",["prophylactic_low","treatment_higher","uncertain"])
    if ("low_molecular_weight_heparin" in medication_classes or "unfractionated_heparin" in medication_classes):
        safety_context["heparin_during_kidney_dialysis"] = ask_yes_no("Is the patient receiving heparin or LMWH during kidney dialysis?")
    # medication class: DOAC
    doac_ingredients = []
    for medication in patient_context.get("medications", []):
        if medication.get("medication_class", "") == "doac":
            ingredient_name = medication.get("ingredient_name", "").strip().lower()
            doac_ingredients.append(ingredient_name)
    if doac_ingredients:
        safety_context["urgent_dental_procedure"] = ask_yes_no("Does the planned dental procedure need to be performed urgently?")
        if safety_context["urgent_dental_procedure"] == "yes":
            safety_context["morning_doac_dose_already_taken"] = ask_yes_no("Has the patient already taken today's morning DOAC dose?")
        else:
            safety_context["morning_doac_dose_already_taken"] = "no"
    else:
        safety_context["urgent_dental_procedure"] = "no"
        safety_context["morning_doac_dose_already_taken"] = "no"
    if "apixaban" in doac_ingredients or "rivaroxaban" in doac_ingredients:
        safety_context["initial_high_dose_doac"] = ask_yes_no("Is the patient taking initial high-dose apixaban or rivaroxaban for acute DVT or pulmonary embolism during the first 1 to 3 weeks of treatment?")
    else:
        safety_context["initial_high_dose_doac"] = "no"
    urgent_after_morning_dose = (safety_context["urgent_dental_procedure"] == "yes" and safety_context["morning_doac_dose_already_taken"] == "yes")
    dose_time_is_needed = (("rivaroxaban" in doac_ingredients or "edoxaban" in doac_ingredients)
            and not urgent_after_morning_dose and safety_context["therapy_must_not_be_interrupted"] != "yes")
    if dose_time_is_needed:
        safety_context["usual_dose_time"] = ask_choice("When does the patient normally take this medication?",["morning", "evening"])
    safety_context["antithrombotic_treatment_duration"] = ask_choice("Enter treatment duration: long_term or time_limited",["long_term", "time_limited"])

    return safety_context

def get_extraction_information(patient_context):
    for procedure in patient_context.get("planned_procedures", []):
        procedure_name = procedure.get("procedure_name", "").lower()
        if "extraction" in procedure_name:
            extraction_complexity = ask_choice("Enter extraction complexity: simple, complex, or surgical",["simple", "complex", "surgical"])
            wound_size = ask_choice("Enter wound size: restricted or large", ["restricted", "large"])
            return extraction_complexity, wound_size

    return "", ""

def main(patient_id: str):
    patient_id, patient_context = confirm_patient(patient_id)
    safety_context = collect_safety_context(patient_context)
    extraction_complexity, wound_size = get_extraction_information(patient_context)
    chat_history = InMemoryChatMessageHistory()
    print()
    print("You can now ask clinical questions.")
    print("Type exit to end the conversation.")
    while True:
        print()
        question = typer.prompt("Enter your clinical question")
        if question.strip().lower() == "exit":
            print("Conversation ended.")
            break
        question_type = classify_clinician_question(question)
        answer = final_response(
            patient_id=patient_id,
            question=question,
            extraction_complexity=extraction_complexity,
            wound_size=wound_size,
            safety_context=safety_context,
            chat_history=chat_history,
            question_type = question_type)
        print()
        print(answer)


if __name__ == "__main__":
    typer.run(main)