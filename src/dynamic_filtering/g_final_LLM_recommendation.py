# g_final_LLM_recommendation.py

import json
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dynamic_filtering.f_retrieve_filtered_guidelines import retrieve_filtered_guidelines
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_config()

def format_guideline_documents(documents):
    guideline_context = ""

    for document in documents:
        metadata = document.metadata
        source_information = (
            f"Guideline: {metadata.get('document_title', '')}\n"
            f"Organization: {metadata.get('source_organization', '')}\n"
            f"Edition: {metadata.get('source_edition', '')}\n"
            f"Section: {metadata.get('source_section', '')}\n"
            f"Subsection: {metadata.get('subsection_title', '')}\n"
            f"Recommendation strength: "
            f"{metadata.get('recommendation_strength', '')}\n"
            f"Evidence certainty: "
            f"{metadata.get('evidence_certainty', '')}\n"
            f"Medication action: "
            f"{metadata.get('medication_action', '')}\n")

        guideline_context += (
            f"{source_information}\n"
            f"Guideline content:\n"
            f"{document.page_content}\n\n"
            f"{'--' * 40}\n")

    return guideline_context


def final_response(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = "",
    usual_dose_time: str = "",
    inr_value="",
    inr_test_hours_ago="",
    inr_is_stable: str = "",
    lmwh_dose_category: str = "",
    heparin_during_kidney_dialysis: str = "",
    safety_context=None,
    chat_history=None
):
    if safety_context is None:
        safety_context = {}

    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()

    retrieval_result = retrieve_filtered_guidelines(
        patient_id=patient_id,
        question=question,
        extraction_complexity=extraction_complexity,
        wound_size=wound_size,
        usual_dose_time=usual_dose_time,
        inr_value=inr_value,
        inr_test_hours_ago=inr_test_hours_ago,
        inr_is_stable=inr_is_stable,
        lmwh_dose_category=lmwh_dose_category,
        heparin_during_kidney_dialysis=(heparin_during_kidney_dialysis),
        safety_context=safety_context
    )

    if retrieval_result["status"] != "retrieved":
        blocking_reasons = retrieval_result.get("blocking_reasons", [])
        message_lines = ["A guideline recommendation cannot be generated."]
        for blocking_reason in blocking_reasons:
            reason = blocking_reason.get("reason","unknown_reason")
            message_lines.append(f"Reason: {reason}")
            missing_information = blocking_reason.get("missing_information",[])
            if missing_information:
                missing_text = ", ".join(missing_information)
                message_lines.append(f"Missing information: {missing_text}")
            detailed_message = blocking_reason.get("message","")
            if detailed_message:
                message_lines.append(detailed_message)
        return "\n".join(message_lines)

    documents = retrieval_result["documents"]
    if not documents:
        return ("No guideline recommendation matching the patient's medication class and procedure bleeding risk was found.")

    patient_context = retrieval_result["patient_context"]

    relevant_patient_context = {
        "conditions": patient_context.get("conditions", []),
        "medications": patient_context.get("medications", []),
        "planned_procedures": patient_context.get("planned_procedures",[]),
        "clinical_assessment": patient_context.get("clinical_assessment",{})
    }

    patient_context_json = json.dumps(relevant_patient_context,indent=2)
    guideline_context = format_guideline_documents(documents)
    chat_model = ChatOpenAI(model="gpt-4o-mini",temperature=0)
    prompt = ChatPromptTemplate.from_messages([(
            "system", """
                    You are a dental clinical decision support system.
                    Answer the clinical question using only:
                    1. The structured patient context.
                    2. The deterministic clinical assessment.
                    3. The retrieved SDCEP guideline content.

                    Rules:
                    - Do not add medical information that is not provided.
                    - Do not create or guess medication, diagnosis or procedure codes.
                    - Do not change the procedure bleeding-risk classification.
                    - Do not create a medication recommendation that is not stated in the retrieved guideline.
                    - Use the chat history only to understand follow-up questions.
                    - Always base clinical recommendations on the current patient context, clinical assessment and retrieved guideline content.
                    - Do not state that the recommendation ensures or guarantees safety, effectiveness or prevention of bleeding.
                    - Explain that the result is decision support and requires clinician judgement.
                    - Clearly state the patient's relevant medication, medication class and planned procedure.
                    - Clearly state the assessed postoperative bleeding risk.
                    - Explain the guideline-supported medication action.
                    - Include the practical management considerations found in the retrieved guideline.
                    - Mention the guideline name and section.
                    - Mention the recommendation strength and evidence certainty when they are available.
                    - If the supplied information is insufficient, say so clearly.
                        """),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", """Patient context: {patient_context}
                     Retrieved guideline context: {guideline_context}
                     Clinical question: {question}""")
    ])

    chain = prompt | chat_model

    chain_with_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: chat_history,
        input_messages_key="question",
        history_messages_key="chat_history"
    )
    response = chain_with_history.invoke({
        "patient_context": patient_context_json,
        "guideline_context": guideline_context,
        "question": question
    },
    config={"configurable": {"session_id": patient_id}}
    )

    return response.content


def run():
    safety_context = {
        "prosthetic_metal_heart_valve": "no",
        "coronary_stent": "no",
        "dvt_or_pe_within_3_months": "no",
        "anticoagulation_for_cardioversion": "no",
        "initial_high_dose_doac": "no",
        "renal_disease_affecting_bleeding": "no",
        "liver_disease_affecting_bleeding": "no",
        "bone_marrow_disorder": "no",
        "other_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "antithrombotic_treatment_duration": "long_term"
    }
    patient_id = "1256"

    question = "should we carryout the planned procedure?"
    answer = final_response(
        patient_id=patient_id,
        question=question,
        extraction_complexity="simple",
        wound_size="restricted",
        usual_dose_time = "evening",
        safety_context=safety_context
    )

    print(answer)


if __name__ == "__main__":
    run()