# i_final_LLM_recommendation.py

import json
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines, retrieve_guideline_information
from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
from dynamic_filtering.m_drug_interaction_retrieval import retrieve_drug_interactions

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


def final_response(patient_id,question,visit_procedures=None,safety_context=None,chat_history=None,question_type="treatment_recommendation"):
    if visit_procedures is None:
        visit_procedures = []
    if safety_context is None:
        safety_context = {}
    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()
    if question_type == "other":
        return "Please ask a question about this patient's dental treatment."
    if question_type == "treatment_recommendation":
        response_instructions = "Give the full clinical decision-support response. Include the relevant medication, medication class, planned procedure, procedure bleeding risk, guideline action, practical management advice, guideline section, recommendation strength and evidence certainty. Include the action from every retrieved guideline section. Include medication restart instructions and staged treatment advice only when they are present in the retrieved guideline."
    elif question_type == "guideline_information":
        response_instructions = ("Explain the guideline's name, source, purpose and scope using only the retrieved guideline content. "
                                 "Do not give a patient-specific treatment recommendation.")
    elif question_type == "guideline_explanation":
        response_instructions = " Answer the clinician's specific question using the retrieved guideline. Give a short and direct explanation. Do not repeat the complete clinical recommendation, patient context or clinical assesment or guideline content. "
    elif question_type == "drug_interaction":
        response_instructions = ("Answer only the drug-interaction question. State only interactions present in the retrieved guideline. If the medicine is not mentioned, say it was not identified in the stored SDCEP interaction information and advise checking the current BNF or medicine SPC. Never say that no interaction exists.")
    elif question_type == "patient_information":
        response_instructions = "Answer only the question about the patient. Use only the structured patient context. Do not provide a treatment recommendation. Do not mention the retrieved guideline. Do not add management advice or a conclusion."
    else:
        response_instructions = """Answer the question using the patient context and retrieved guideline."""
    if question_type == "guideline_information":
        retrieval_result = retrieve_guideline_information(question)
        if retrieval_result["missing_sections"]:
            return "The guideline information could not be retrieved completely."
        patient_context = {}
        documents = retrieval_result["documents"]
        safety_warnings = []
    elif question_type == "drug_interaction":
        retrieval_result = retrieve_drug_interactions( patient_id=patient_id,question=question, safety_context=safety_context)
        if retrieval_result["status"] != "retrieved":
            return retrieval_result.get("message", "")
        patient_context = retrieval_result["patient_context"]
        documents = retrieval_result["documents"]
        safety_warnings = []
    elif question_type == "patient_information":
        patient_context = assess_patient_context(patient_id,visit_procedures=visit_procedures)
        patient_context["clinical_assessment"]["patient_safety"] = safety_context
        documents = []
        safety_warnings = []
    else:
        retrieval_result = retrieve_filtered_guidelines(patient_id=patient_id,question=question,visit_procedures=visit_procedures,safety_context=safety_context)
        if retrieval_result["status"] != "retrieved":
            return retrieval_result.get("blocking_message", "")
        patient_context = retrieval_result["patient_context"]
        documents = retrieval_result.get("documents", [])
        safety_warnings = retrieval_result.get("safety_warnings", [])
    relevant_patient_context = {
        "conditions": patient_context.get("conditions", []),
        "medications": patient_context.get("medications", []),
        "planned_procedures": patient_context.get("planned_procedures", []),
        "clinical_assessment": patient_context.get("clinical_assessment", {}),
        "safety_warnings": safety_warnings
    }
    patient_context_json = json.dumps(relevant_patient_context)
    guideline_context = format_guideline_documents(documents)
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
            - Give one medication plan for the selected treatment-visit procedures and state which procedures it applies to.
            - Explain that the result requires clinician judgement when giving a clinical recommendation.
            - If the guideline says to consult the prescribing clinician, do not say that the treatment can be continued.
            - Do not add practical advice unless it is present in the retrieved guideline.
            - Use every retrieved guideline section that applies to the patient.
            - If a retrieved guideline section advises delaying the procedure, do not say to proceed without clearly stating that delay.
            - Use the postoperative bleeding-risk classification provided in the clinical assessment.
            - Preserve important conditions from the guideline, such as "unless contraindicated", "where possible", and medication timing requirements.
            - Do not add headings or sections for information that is not present or not applicable.
            - Clearly distinguish between delaying a medication dose and delaying the dental procedure. Do not say to delay the procedure when the guideline only says to delay the medication dose.
            - Do not decide by yourself whether the dental procedure should be delayed or can proceed. State only the procedure action and medication action present in the retrieved guideline.
            - When the retrieved action says "treat according to standard procedures", use those words. Do not change this to "the procedure can proceed", do not say medicines can be continued, and do not mention restart or staged treatment unless those actions are explicitly present in the retrieved guideline.
            - Preserve important qualifiers from the guideline, such as 'regular use', and do not make the interaction sound broader than the retrieved content.
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