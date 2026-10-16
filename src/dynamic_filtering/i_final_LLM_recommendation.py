# i_final_LLM_recommendation.py

import json
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines

load_config()

def format_guideline_documents(documents):
    guideline_parts = []

    for document in documents:
        metadata = document.metadata
        guideline_text = f"""
        Guideline: {metadata.get("document_title", "")}
        Organization: {metadata.get("source_organization", "")}
        Edition: {metadata.get("source_edition", "")}
        Section: {metadata.get("source_section", "")}
        Subsection: {metadata.get("subsection_title", "")}
        Recommendation strength: {metadata.get("recommendation_strength", "")}
        Evidence certainty: {metadata.get("evidence_certainty", "")}
        Medication action: {metadata.get("medication_action", "")}
                             
        Guideline content: {document.page_content}"""
        guideline_parts.append(guideline_text)

    guideline_context = ""
    for guideline_part in guideline_parts:
        guideline_context = guideline_context + guideline_part

    return guideline_context


def final_response(patient_id,question,extraction_complexity="",wound_size="",safety_context=None,chat_history=None,question_type="treatment_recommendation"):
    if safety_context is None:
        safety_context = {}
    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()
    if question_type == "other":
        return "Please ask a question about this patient's dental treatment."
    if question_type == "treatment_recommendation":
        response_instructions = "Give the full clinical decision-support response. Include the relevant medication, medication class, planned procedure, procedure bleeding risk, guideline action, practical management advice, guideline section, recommendation strength and evidence certainty. Include the action from every retrieved guideline section. Do not leave out an instruction to delay treatment. Include medication restart instructions and staged treatment advice only when they are present in the retrieved guideline."
    elif question_type == "guideline_explanation":
        response_instructions = " Answer the clinician's specific question using the retrieved guideline. Give a short and direct explanation. Do not repeat the complete clinical recommendation, patient context or clinical assesment or guideline content. "
    elif question_type == "patient_information":
        response_instructions = "Answer only the question about the patient. Use only the structured patient context. Do not provide a treatment recommendation. Do not mention the retrieved guideline. Do not add management advice or a conclusion."
    else:
        response_instructions = """Answer the question using the patient context and retrieved guideline."""

    retrieval_result = retrieve_filtered_guidelines(patient_id=patient_id,question=question,extraction_complexity=extraction_complexity,wound_size=wound_size,safety_context=safety_context,question_type=question_type)

    if retrieval_result["status"] != "retrieved":
        return retrieval_result.get("blocking_message", "")
    documents = retrieval_result.get("documents", [])
    patient_context = retrieval_result["patient_context"]
    relevant_patient_context = {
        "conditions": patient_context.get("conditions", []),
        "medications": patient_context.get("medications", []),
        "planned_procedures": patient_context.get("planned_procedures", []),
        "clinical_assessment": patient_context.get("clinical_assessment", {}),
        "safety_warnings": retrieval_result.get("safety_warnings", [])
    }
    patient_context_json = json.dumps(relevant_patient_context)
    guideline_context = format_guideline_documents(documents)
    if question_type == "patient_information":
        guideline_context = ""
    chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
            You are a dental clinical decision support system.
            Answer using only:
            1. The structured patient context.
            2. The deterministic clinical assessment.
            3. The retrieved SDCEP guideline content.
            Rules:
            - Do not add medical information that is not provided.
            - Do not create or guess medication, diagnosis or procedure codes.
            - Do not change the procedure bleeding-risk classification.
            - The bleeding-risk classification belongs to the planned dental procedure. Do not say that the medication caused this classification.
            - Include medication restart timing and staged treatment advice when they are present in the retrieved guideline.
            - Do not create a medication recommendation that is not stated in the retrieved guideline.
            - If the clinician confirms that therapy must not be interrupted, do not guess which medical condition caused that answer.
            - Use the clinician role stated in the retrieved guideline. Do not replace cardiologist with prescribing clinician.
            - Use the chat history only to understand follow-up questions.
            - Explain that the result requires clinician judgement when giving a clinical recommendation.
            - If the guideline says to consult the prescribing clinician, do not say that the treatment can be continued.
            - Do not add practical advice unless it is present in the retrieved guideline.
            - Use every retrieved guideline section that applies to the patient.
            - If a retrieved guideline section advises delaying the procedure, do not say to proceed without clearly stating that delay.
            - Describe the procedure as having a higher postoperative bleeding risk. Do not say that the medication caused the procedure classification.
            - Preserve important conditions from the guideline, such as "unless contraindicated", "where possible", and medication timing requirements.
            - Do not add headings or sections for information that is not present or not applicable.
            - Clearly distinguish between delaying a medication dose and delaying the dental procedure. Do not say to delay the procedure when the guideline only says to delay the medication dose.
            - Do not decide by yourself whether the dental procedure should be delayed or can proceed. State only the procedure action and medication action present in the retrieved guideline.
            Response instructions: {response_instructions}
            """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human","""
                Patient context:{patient_context}
                Retrieved guideline context: {guideline_context}
                Clinical question:{question}
                """)
    ])

    chain = prompt | chat_model
    def get_chat_history(session_id):
        return chat_history
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_chat_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    response = chain_with_history.invoke({
        "patient_context": patient_context_json,
        "guideline_context": guideline_context,
        "question": question,
        "response_instructions": response_instructions},
        config={"configurable": {"session_id": patient_id}})

    return response.content

def preview_final_response():
    patient_id = "1256"
    safety_context = {
        "medical_history_and_medicines_reviewed": "yes",
        "therapy_must_not_be_interrupted": "no",
        "additional_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "urgent_dental_procedure": "no",
        "morning_doac_dose_already_taken": "no",
        "initial_high_dose_doac": "no",
        "usual_dose_time": "morning",
        "antithrombotic_treatment_duration": "long_term"
    }
    question = "Can this patient proceed with the planned dental procedure?"
    answer = final_response(patient_id=patient_id,question=question,safety_context=safety_context)
    print(answer)


if __name__ == "__main__":
    preview_final_response()