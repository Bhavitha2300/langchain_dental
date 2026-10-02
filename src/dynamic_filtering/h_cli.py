import typer
from langchain_core.chat_history import InMemoryChatMessageHistory
from dynamic_filtering.c_retrieve_fhir_patient_data import get_fhir_patient_data
from dynamic_filtering.g_final_LLM_recommendation import final_response


def ask_yes_no(question):
    while True:
        answer = typer.prompt(question)
        answer = answer.strip().lower()

        if answer in ["yes","y"]:
            return "yes"

        if answer in ["no","n"]:
            return "no"

        print("Please enter yes or no.")

def main(patient_id: str):
    while True:
        patient_context = get_fhir_patient_data(patient_id)
        name = patient_context.get("name","")
        gender = patient_context.get("gender","")
        birth_date = patient_context.get("birth_date","")
        conditions = patient_context.get("conditions",[])
        medications = patient_context.get("medications",[])
        planned_procedures = patient_context.get("planned_procedures",[])

        print("Selected patient:")
        print()
        print(f"Patient ID: {patient_id}")
        print(f"Name: {name}")
        print(f"Gender: {gender}")
        print(f"Birth date: {birth_date}")

        # check_correct_patient_or_not
        correct_patient = typer.confirm("Is this the correct patient?")
        if correct_patient:
            print("Patient confirmed.")
            break
        print("These are the patient details associated with the entered patient ID, Check if the patient ID is correct.")
        patient_id = typer.prompt("Please enter the correct patient ID")

    # display confirmed patient information
    print()
    print("Patient clinical information:")
    print()
    print("Conditions:")
    for condition in conditions:
        condition_name = condition.get("condition_name","")
        print(f"{condition_name}")
    print()
    print("Medications:")
    for medication in medications:
        medication_name = medication.get("medication_name","")
        dose_value = medication.get("dose_value","")
        dose_unit = medication.get("dose_unit","")
        route = medication.get("route","")
        print(f" {medication_name}")
        print(f"  Dose: {dose_value} {dose_unit}")
        print(f"  Route: {route}")
    print()
    print("Planned procedures:")
    for procedure in planned_procedures:
        procedure_name = procedure.get("procedure_name","")
        print(f"{procedure_name}")
    print()
    print()
    print("Patient safety questions:")
    print("Please answer yes or no.")
    medical_history_reviewed = ask_yes_no("Has the patient's medical history been reviewed?")
    medication_list_reviewed = ask_yes_no("Have the patient's prescribed and non-prescribed medicines been reviewed?")
    prosthetic_metal_heart_valve = ask_yes_no("Does the patient have a prosthetic metal heart valve?")
    coronary_stent = ask_yes_no("Does the patient have a coronary stent?")
    dvt_or_pe_within_3_months = ask_yes_no("Has the patient had DVT or PE within the last 3 months?")
    anticoagulation_for_cardioversion = ask_yes_no("Is the patient receiving anticoagulation for cardioversion?")
    protected_antithrombotic_context = "no"
    if (
            prosthetic_metal_heart_valve == "yes"
            or coronary_stent == "yes"
            or dvt_or_pe_within_3_months == "yes"
            or anticoagulation_for_cardioversion == "yes"
    ):
        protected_antithrombotic_context = "yes"
    renal_disease_affecting_bleeding = ask_yes_no("Does the patient have renal disease affecting bleeding?")
    liver_disease_affecting_bleeding = ask_yes_no("Does the patient have liver disease affecting bleeding?")
    bone_marrow_disorder = ask_yes_no("Does the patient have a bone marrow disorder?")
    other_bleeding_risk_condition = ask_yes_no("Does the patient have another condition affecting bleeding?")
    additional_bleeding_risk_condition = "no"

    if (
            renal_disease_affecting_bleeding == "yes"
            or liver_disease_affecting_bleeding == "yes"
            or bone_marrow_disorder == "yes"
            or other_bleeding_risk_condition == "yes"
    ):
        additional_bleeding_risk_condition = "yes"
    bleeding_history_concern = ask_yes_no("Does the patient have a history of prolonged or excessive bleeding?")
    initial_high_dose_doac = ask_yes_no("Is the patient taking an initial high dose of the DOAC?")
    antithrombotic_treatment_duration = typer.prompt("Enter treatment duration: long_term or time_limited")
    antithrombotic_treatment_duration = antithrombotic_treatment_duration.strip().lower()
    usual_dose_time = typer.prompt("Enter usual dose time: morning or evening")
    usual_dose_time = usual_dose_time.strip().lower()

    safety_context = {
        "medical_history_reviewed": medical_history_reviewed,
        "medication_list_reviewed": medication_list_reviewed,
        "protected_antithrombotic_context": (
            protected_antithrombotic_context
        ),
        "additional_bleeding_risk_condition": (
            additional_bleeding_risk_condition
        ),
        "bleeding_history_concern": (
            bleeding_history_concern
        ),
        "initial_high_dose_doac": (
            initial_high_dose_doac
        ),
        "antithrombotic_treatment_duration": (
            antithrombotic_treatment_duration
        )
    }

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

        answer = final_response(
            patient_id=patient_id,
            question=question,
            usual_dose_time=usual_dose_time,
            safety_context=safety_context,
            chat_history=chat_history
        )

        print()
        print(answer)

if __name__ == "__main__":

    typer.run(main)