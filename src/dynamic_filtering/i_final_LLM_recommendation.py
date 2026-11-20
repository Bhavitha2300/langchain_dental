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

def final_response(patient_id,question,visit_procedures=None,safety_context=None,chat_history=None,question_type="treatment_recommendation", retrieval_result=None):
    if visit_procedures is None:
        visit_procedures = []
    if safety_context is None:
        safety_context = {}
    if chat_history is None:
        chat_history = InMemoryChatMessageHistory()
    if question_type == "other":
        return "Please ask a question about this patient's dental treatment."
    if question_type == "treatment_recommendation":
        response_instructions = (
            "Answer the clinician's specific treatment question directly. "
            "When a complete treatment plan is requested, include the relevant "
            "medication, procedure, assessed procedure bleeding risk, medication "
            "action and practical management advice. "
            "For a focused question, avoid repeating the complete treatment plan. "
            "Include essential safety conditions even in a short answer. "
            "Include supporting guideline sections when available. "
            "State recommendation strength and evidence certainty only when "
            "provided for the relevant recommendation."
        )

    elif question_type == "guideline_information":
        response_instructions = (
            "Answer the general question using only the retrieved guideline "
            "content and source metadata. "
            "Do not apply the answer to the selected patient. "
            "Preserve medication, procedure and timing conditions. "
            "Do not combine advice for alternative clinical situations. "
            "Include supporting guideline sections when available. "
            "If the evidence is insufficient, explain what it does not establish. "
            "If a patient-specific decision is requested, explain that patient "
            "assessment is required."
        )

    elif question_type == "guideline_explanation":
        response_instructions = (
            "Give a short explanation answering the clinician's specific question. "
            "Use the retrieved guideline and relevant patient context to explain "
            "the applicable recommendation. "
            "Do not repeat the complete patient summary or treatment plan. "
            "Include important conditions or exceptions needed to understand "
            "the answer and supporting guideline sections when available."
        )

    elif question_type == "drug_interaction":
        response_instructions = (
            "Answer only the drug-interaction question. "
            "For a specific drug pair, explain that interaction, its possible "
            "effect and any action supported by the retrieved guideline. "
            "List multiple interactions only when an overview is requested. "
            "Preserve all relevant conditions, including regular-use qualifiers. "
            "If the specific interaction is not identified in the retrieved "
            "information, say so and advise checking the current BNF or relevant "
            "medicine product information. "
            "Do not interpret missing information as evidence that no interaction "
            "exists. "
            "Pass on advice to consult prescribing references when the retrieved "
            "guideline recommends it. "
            "Do not invent an alternative medicine or dose."
        )

    elif question_type == "patient_information":
        response_instructions = (
            "Answer only the question about the patient using the structured "
            "patient context. "
            "If the requested information is absent, say it is not recorded "
            "in the supplied context. "
            "Do not infer that an unrecorded condition or medicine is absent. "
            "Do not provide treatment recommendations, guideline advice "
            "or an unrelated patient summary."
        )

    else:
        response_instructions = (
            "Answer the specific question using the supplied information. "
            "If the available information does not support an answer, say so. "
            "Do not add an unrelated treatment plan."
        )

    if question_type == "guideline_information":
        retrieval_result = retrieve_guideline_information(question)
        if not retrieval_result["documents"] or retrieval_result["missing_sections"]:
            return "The guideline information could not be retrieved completely."
        patient_context = {}
        documents = retrieval_result["documents"]
        safety_warnings = []
        chat_history = InMemoryChatMessageHistory()
    elif question_type == "drug_interaction":
        retrieval_result = retrieve_drug_interactions( patient_id=patient_id,question=question, safety_context=safety_context)
        if retrieval_result["status"] != "retrieved":
            return retrieval_result.get("message", "")
        patient_context = retrieval_result["patient_context"]
        documents = retrieval_result["documents"]
        safety_warnings = []
    elif question_type == "patient_information":
        patient_context = assess_patient_context(patient_id, visit_procedures=visit_procedures)
        patient_context["clinical_assessment"]["patient_safety"] = safety_context
        documents = []
        safety_warnings = []
    else:
        if retrieval_result is None:
            retrieval_result = retrieve_filtered_guidelines(
                patient_id=patient_id,
                question=question,
                visit_procedures=visit_procedures,
                safety_context=safety_context)
        if retrieval_result["status"] != "retrieved":
            return retrieval_result.get("blocking_message", "")
        patient_context = retrieval_result["patient_context"]
        documents = retrieval_result.get("documents", [])
        safety_warnings = retrieval_result.get("safety_warnings", [])
    relevant_patient_context = {
        "conditions": patient_context.get("conditions", []),
        "medications": patient_context.get("medications", []),
        "observations": patient_context.get("observations", []),
        "planned_procedures": patient_context.get("planned_procedures", []),
        "clinical_assessment": patient_context.get("clinical_assessment", {}),
        "safety_warnings": safety_warnings
    }
    patient_context_json = json.dumps(relevant_patient_context)
    guideline_context = format_guideline_documents(documents)
    chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are a dental clinical decision support assistant.

            Use only:
            - The structured patient context.
            - The deterministic clinical assessment and safety information.
            - Explicit clinical details provided by the clinician.
            - The retrieved SDCEP guideline content and source metadata.

            Follow the response instructions for the question type.
            They determine whether to provide treatment advice, an explanation,
            general guideline information, an interaction answer or patient facts.

            Patient information:
            - Do not invent diagnoses, medicines, doses, test results,
              procedure details or terminology codes.
            - Distinguish historical records from explicitly confirmed updates.
            - Do not silently override the current structured assessment or
              safety decision with a conflicting statement in the question.
              Identify a material conflict and request clarification.
            - If information needed for the requested decision is missing,
              explain what is needed instead of assuming a reassuring answer.
            - Use chat history to understand follow-up questions.
              Do not treat previous assistant answers as independent clinical
              evidence.

            Guideline interpretation:
            - Use only retrieved guidance applicable to the actual medication,
              regimen, procedure, urgency and timing.
            - Do not combine instructions for alternative clinical situations
              into one management plan.
            - Preserve conditions such as "where possible",
              "unless contraindicated" and "if further information is required".
            - Apply a relevant specific exception rather than presenting
              conflicting general and specific advice as simultaneous instructions.
            - Preserve the clinician or specialist role specified by the source.
            - If consultation is required before determining management,
              do not give unconditional clearance to proceed.
            - If consultation is conditional, preserve that condition.
            - Do not invent guidance when the retrieved evidence is insufficient.

            Treatment answers:
            - Use the procedure bleeding-risk classification supplied in the
              clinical assessment. Do not change it.
            - Distinguish procedural bleeding risk from additional patient
              bleeding-risk factors. Do not say the medicine caused the
              procedure classification.
            - Clearly distinguish delaying a medicine dose from delaying
              the dental procedure.
            - Include medication changes, restart timing, staging and practical
              precautions only when relevant and supported by applicable
              retrieved guidance.
            - If applicable guidance advises postponement, consultation or
              referral, state that action clearly.
            - For combination therapy, use applicable combination-therapy
              guidance. Do not automatically apply single-drug dose instructions.
            - Do not invent a medication restart schedule or waiting period.
            - If the clinician confirms that therapy must not be interrupted,
              preserve that restriction without guessing its medical cause.
            - Explain standard-procedure advice accurately without adding
              unsupported medication changes or invasive-treatment precautions.
            - Make clear that patient-specific recommendations require
              clinician judgement.

            Response:
            - Start with the direct answer.
            - Use clear, concise language and avoid repeating the same advice.
            - Include essential safety qualifications relevant to the question.
            - Do not repeat the complete patient record unless requested.
            - Explain guideline advice in plain language without requiring
              verbatim wording.
            - Cite supporting guideline sections when available.
            - Report recommendation strength and evidence certainty only when
              supplied for the specific recommendation. Do not apply one
              section's evidence rating to the entire answer.
            - Do not add empty headings or sections for irrelevant information.

            Response instructions:
            {response_instructions}
            """
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        (
            "human",
            """
            Patient context:
            {patient_context}

            Retrieved guideline context:
            {guideline_context}

            Clinical question:
            {question}
            """
        )
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
    visit_procedures = [
        {
            "procedure_id": "test-restoration",
            "procedure_name": "Direct restoration",
            "code_system": "http://snomed.info/sct",
            "code": "173307000",
            "margin_location": "unknown"
        }
    ]

    assessed_context = assess_patient_context(
        patient_id=patient_id,
        visit_procedures=visit_procedures
    )

    print("Procedure assessment:")
    print(assessed_context["clinical_assessment"])
    safety_context = {
        "medical_history_and_medicines_reviewed": "yes",
        "therapy_must_not_be_interrupted": "no",
        "additional_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "urgent_dental_procedure": "no",
        "morning_doac_dose_already_taken": "no",
        "recorded_conditions_reconciled": "yes",
        "initial_high_dose_doac": "no",
        "usual_dose_time": "morning",
        "antithrombotic_treatment_duration": "long_term"
    }
    print("Recorded conditions:")
    for condition in assessed_context.get("conditions", []):
        print(condition)

    print("FHIR planned procedures:")
    for procedure in assessed_context.get("planned_procedures", []):
        print(procedure)
    question = "Can this patient proceed with the planned dental procedure?"
    answer = final_response(
        patient_id=patient_id,
        question=question,
        visit_procedures=visit_procedures,
        safety_context=safety_context
    )
    print(answer)


if __name__ == "__main__":
    preview_final_response()