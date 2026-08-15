import requests

patient_id = "1000"

patient_url = f"http://localhost:8080/fhir/Patient/{patient_id}"
medication_url = f"http://localhost:8080/fhir/MedicationRequest?patient={patient_id}"

patient_response = requests.get(patient_url)
medication_response = requests.get(medication_url)

patient = patient_response.json()
medication_data = medication_response.json()
name = patient["name"][0]["given"][0]
birth_date = patient["birthDate"]
medication = medication_data["entry"][0]["resource"]["medicationCodeableConcept"]["text"]

print(name)
print(birth_date)
print(medication)