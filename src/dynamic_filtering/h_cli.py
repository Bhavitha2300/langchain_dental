import typer

def main(patient_id: str):
    print (f"Patient_id: {patient_id} ")

if __name__ == "__main__":

    typer.run(main)