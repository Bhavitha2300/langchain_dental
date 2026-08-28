from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from cdss.c_fhir import get_fhir_patient_data
import json

load_config()

def get_patient_summary(patient_id: str):
    fhir_patient_data = get_fhir_patient_data(patient_id)
    fhir_json = json.dumps(fhir_patient_data, indent=2)
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system",
         """
            You are processing FHIR patient data for a dental clinical decision support system. 
            
            Create a concise structured summary using only the information present in the provided FHIR patient data. 

            Include:
            - patient demographics - Relevant demographic information available in the Patient resource.
            - active medical conditions - Active conditions found in the retrieved Condition resources.
            - active medications - Active medications found in the retrieved MedicationRequest resources.
            - planned dental procedures - Active planned dental procedures found in the retrieved ServiceRequest resources.

            Rules:
            - Do not provide treatment recommendations.
            - Do not add or infer clinical information that is not present in the FHIR data.
            - Do not use outside medical knowledge.
            - If a section has no information in the provided FHIR data, state "Not available in retrieved FHIR data."
            - Present the output in Markdown.
        """
        ),
        ("human", "FHIR patient data:\n{fhir_data}")
    ])

    chain = template | chat_model
    response = chain.invoke({ "fhir_data": fhir_json})
    return response.content

if __name__ == "__main__":
    patient_summary = get_patient_summary("1000")
    print(patient_summary)