# h_final_response.py

import json
from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dynamic_filtering.g_retrieve_filtered_guidelines import retrieve_filtered_guidelines

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
            f"{metadata.get('medication_action', '')}\n"
        )

        guideline_context += (
            f"{source_information}\n"
            f"Guideline content:\n"
            f"{document.page_content}\n\n"
            f"{'--' * 40}\n"
        )

    return guideline_context


def final_response(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = ""
):
    retrieval_result = retrieve_filtered_guidelines(
        patient_id=patient_id,
        question=question,
        extraction_complexity=extraction_complexity,
        wound_size=wound_size
    )

    if retrieval_result["status"] != "retrieved":
        return (
            "A guideline recommendation cannot be generated "
            "because the procedure requires additional clinician "
            "confirmation."
        )

    documents = retrieval_result["documents"]

    if not documents:
        return (
            "No guideline recommendation matching the patient's "
            "medication class and procedure bleeding risk was found."
        )

    patient_context = retrieval_result["patient_context"]

    # Include only information needed for this clinical question.
    relevant_patient_context = {
        "conditions": patient_context.get("conditions", []),
        "medications": patient_context.get("medications", []),
        "planned_procedures": patient_context.get(
            "planned_procedures",
            []
        ),
        "clinical_assessment": patient_context.get(
            "clinical_assessment",
            {}
        )
    }

    patient_context_json = json.dumps(
        relevant_patient_context,
        indent=2
    )

    guideline_context = format_guideline_documents(
        documents
    )

    chat_model = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are a dental clinical decision support system.

Answer the clinical question using only:

1. The structured patient context.
2. The deterministic clinical assessment.
3. The retrieved SDCEP guideline content.

Rules:

- Do not add medical information that is not provided.
- Do not create or guess medication, diagnosis or procedure codes.
- Do not change the procedure bleeding-risk classification.
- Do not create a medication recommendation that is not stated
  in the retrieved guideline.
- Do not state that the recommendation ensures or guarantees
  safety, effectiveness or prevention of bleeding.
- Explain that the result is decision support and requires
  clinician judgement.
- Clearly state the patient's relevant medication, medication
  class and planned procedure.
- Clearly state the assessed postoperative bleeding risk.
- Explain the guideline-supported medication action.
- Include the practical management considerations found in the
  retrieved guideline.
- Mention the guideline name and section.
- Mention the recommendation strength and evidence certainty
  when they are available.
- If the supplied information is insufficient, say so clearly.
- Present the answer in concise Markdown.
"""
        ),
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

    response = chain.invoke({
        "patient_context": patient_context_json,
        "guideline_context": guideline_context,
        "question": question
    })

    return response.content


def run():
    patient_id = "1000"

    question = (
        "How should this patient's apixaban be managed "
        "for the planned dental extraction?"
    )

    answer = final_response(
        patient_id=patient_id,
        question=question,
        extraction_complexity="simple",
        wound_size="restricted"
    )

    print(answer)


if __name__ == "__main__":
    run()