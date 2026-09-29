import typer
from dynamic_filtering.c_retrieve_fhir_patient_data import get_fhir_patient_data

def main(patient_id: str):
    patient_context = get_fhir_patient_data(patient_id)
    name = patient_context.get("name","")
    gender = patient_context.get("gender","")
    birth_date = patient_context.get("birth_date","")
    conditions = patient_context.get("conditions",[])
    medications = patient_context.get("medications",[])
    planned_procedures = patient_context.get("planned_procedures",[])


    print(f"Patient ID: {patient_id}")
    print(f"Name: {name}")
    print(f"Gender: {gender}")
    print(f"Birth date: {birth_date}")
    print(f"Conditions: {conditions}")
    print(f"Medications: {medications}")
    print(f"Planned procedures: {planned_procedures}")

if __name__ == "__main__":

    typer.run(main)