from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from cdss.c_fhir import get_fhir_patient_data

load_config()


def get_patient_summary(patient_id: str):
    fhir_patient_data = get_fhir_patient_data(patient_id)
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system",
         """
            You are processing FHIR patient data for a dental clinical decision support system.

            Summarize only the clinically relevant information contained in the provided FHIR data.

            Include:
            - patient demographics
            - active medical conditions
            - active medications
            - planned dental procedures

            Do not provide treatment recommendations.
            Do not add information that is not present in the FHIR data.
            Present the summary in clear Markdown.
            """
        ),
        ("human", "FHIR patient data:\n{fhir_data}")
    ])

    chain = template | chat_model
    response = chain.invoke({ "fhir_data": fhir_patient_data})
    return response.content

if __name__ == "__main__":
    patient_summary = get_patient_summary("1000")
    print(patient_summary)