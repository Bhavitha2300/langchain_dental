# j_cli.py

import typer
from langchain_core.chat_history import InMemoryChatMessageHistory
from dynamic_filtering.d_medication_terminology import add_medication_class_to_fhir_patient_data
from dynamic_filtering.i_final_LLM_recommendation import final_response

# ask yes or no questions
def ask_yes_no(question):
    while True:
        answer = typer.prompt(question)
        answer = answer.strip().lower()
        if answer in ["yes","y"]:
            return "yes"
        if answer in ["no","n"]:
            return "no"
        print("Please enter yes or no.")

def ask_choice(question, allowed_values):
    while True:
        answer = typer.prompt(question)
        answer = answer.strip().lower().replace(" ", "_")
        if answer in allowed_values:
            return answer
        print(f"Please enter one of: {'or'.join(allowed_values)}")


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
    extra_risk_present = ask_yes_no("Does the patient have any extra condition that may increase bleeding risk or make anticoagulant management more complicated?")
    if extra_risk_present == "yes":
        safety_context["high_risk_reason_for_anticoagulant"] = ask_yes_no("Does the patient have a high-risk reason for taking anticoagulant or antiplatelet medicine, such as prosthetic metal heart valve, coronary stent, recent DVT/PE, or cardioversion?")
        safety_context["additional_bleeding_risk_condition"] = ask_yes_no("Does the patient have renal disease, liver disease, bone marrow disorder, or another condition increasing bleeding risk?")
        safety_context["bleeding_history_concern"] = ask_yes_no("Does the patient have a history of prolonged or excessive bleeding?")
    else:
        safety_context["high_risk_reason_for_anticoagulant"] = "no"
        safety_context["additional_bleeding_risk_condition"] = "no"
        safety_context["bleeding_history_concern"] = "no"
    medication_classes = get_medication_classes(patient_context)
    if "doac" in medication_classes:
        safety_context["initial_high_dose_doac"] = ask_yes_no("Is the patient taking an initial high dose of a DOAC?")
    else:
        safety_context["initial_high_dose_doac"] = "no"
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
    while True:
        print()
        question = typer.prompt("Enter your clinical question")
        if question.strip().lower() == "exit":
            print("Conversation ended.")
            break
        answer = final_response(
            patient_id=patient_id,
            question=question,
            extraction_complexity=extraction_complexity,
            wound_size=wound_size,
            safety_context=safety_context,
            chat_history=chat_history
        )
        print()
        print(answer)


if __name__ == "__main__":
    typer.run(main)