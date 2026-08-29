from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from cdss.e_guideline_retrieval import retrieve_guidelines

load_config()

def final_response(patient_id: str, question: str):
    patient_summary, guideline_context = retrieve_guidelines(patient_id, question)
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", """
            You are a dental clinical decision support system.

            Answer the clinical question using only the patient summary and retrieved guideline context provided.

            Do not add information that is not present in the patient summary or guideline context.

            If the question cannot be answered from the provided information, say that the available information is insufficient.
        """),
        ("human", "Patient Summary:{patient_summary}"),
        ("human", "Guideline Context:{guideline_context}"),
        ("human", "Question:{question}")
    ])
    chain = template | chat_model
    response = chain.invoke({
        "patient_summary": patient_summary,
        "guideline_context": guideline_context,
        "question": question
    })
    return response.content

def run():
    patient_id = "1000"
    question = "What are the guideline-based antithrombotic management considerations for this patient's planned dental procedure?"
    final_recommendation = final_response(patient_id, question)
    print(final_recommendation)

if __name__ == "__main__":
    run()



