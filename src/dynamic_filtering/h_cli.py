import typer
from dynamic_filtering.c_retrieve_fhir_patient_data import get_fhir_patient_data

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


if __name__ == "__main__":

    typer.run(main)