# h_retrieve_filtered_guidelines.py

import pprint
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
from dynamic_filtering.f_patient_safety_checks import find_safety_warnings, find_blocking_reasons
from dynamic_filtering.g_guideline_metadata_filter import build_metadata_filters

def create_blocking_message(blocking_reasons):
    message_lines = ["A guideline recommendation cannot be generated."]
    for blocking_reason in blocking_reasons:
        reason = blocking_reason.get("reason", "")
        missing_information = blocking_reason.get("missing_information", [])
        message = blocking_reason.get("message", "")
        if reason:
            message_lines.append(f"Reason: {reason}")
        if missing_information:
            missing_text = ", ".join(missing_information)
            message_lines.append(f"Missing information: {missing_text}")
        if message:
            message_lines.append(message)

    return "\n".join(message_lines)

def retrieve_filtered_guidelines(patient_id, question, extraction_complexity="", wound_size="", safety_context=None):
    if safety_context is None:
        safety_context = {}
    assessed_context = assess_patient_context(patient_id, extraction_complexity=extraction_complexity, wound_size=wound_size)
    assessed_context["clinical_assessment"]["patient_safety"] = safety_context
    safety_warnings = find_safety_warnings(assessed_context)
    blocking_reasons = find_blocking_reasons(assessed_context)
    # if any of the blocking reasons are present return this
    if blocking_reasons:
        blocking_message = create_blocking_message(blocking_reasons)
        return {
            "status": "needs_clinician_confirmation",
            "patient_context": assessed_context,
            "blocking_reasons": blocking_reasons,
            "blocking_message": blocking_message,
            "safety_warnings": safety_warnings,
            "metadata_filters": None,
            "documents": []
        }
    metadata_filters = build_metadata_filters(assessed_context)
    # if no metadata filters are built then return this
    if not metadata_filters:
        blocking_reasons = [{"reason": "metadata_filter_not_created",
                             "message": "A guideline filter could not be created."}]
        blocking_message = create_blocking_message(blocking_reasons)
        return {
            "status": "no_metadata_filters",
            "patient_context": assessed_context,
            "blocking_reasons": blocking_reasons,
            "blocking_message": blocking_message,
            "safety_warnings": safety_warnings,
            "metadata_filters": None,
            "documents": []
        }
    vector_store = get_vector_store()
    documents = []
    added_chunk_ids = []
    for metadata_filter in metadata_filters:
        retrieved_documents = vector_store.similarity_search(
            query=question,
            k=10,
            filter=metadata_filter
        )
        for document in retrieved_documents:
            chunk_id = document.metadata.get("chunk_id", "")
            if chunk_id in added_chunk_ids:
                continue
            added_chunk_ids.append(chunk_id)
            documents.append(document)
    # it no documents match then return this
    if not documents:
        blocking_reasons = [{"reason": "no_matching_recommendation",
                             "message": "No matching guideline recommendation was found."}]
        blocking_message = create_blocking_message(blocking_reasons)
        return {
            "status": "no_matching_recommendation",
            "patient_context": assessed_context,
            "blocking_reasons": blocking_reasons,
            "blocking_message": blocking_message,
            "safety_warnings": safety_warnings,
            "metadata_filters": metadata_filters,
            "documents": []
        }
    return {
        "status": "retrieved",
        "patient_context": assessed_context,
        "blocking_reasons": [],
        "blocking_message": "",
        "safety_warnings": safety_warnings,
        "metadata_filters": metadata_filters,
        "documents": documents
    }

def preview_retrieval():
    patient_id = "1256"
    safety_context = {
        "medical_history_and_medicines_reviewed": "yes",
        "high_risk_reason_for_anticoagulant": "no",
        "additional_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "initial_high_dose_doac": "no",
        "antithrombotic_treatment_duration": "long_term"
    }

    question = "Can this patient proceed with the planned dental procedure?"
    result = retrieve_filtered_guidelines(patient_id=patient_id,question=question,safety_context=safety_context)
    print("Status:")
    print(result["status"])
    print()
    print("Blocking reasons:")
    pprint.pprint(result["blocking_reasons"])
    print()
    print("Safety warnings:")
    pprint.pprint(result["safety_warnings"])
    print()
    print("Metadata filters:")
    pprint.pprint(result["metadata_filters"])
    print()
    print("Retrieved documents:")
    for document in result["documents"]:
        print()
        print("Metadata:")
        pprint.pprint(document.metadata)
        print()
        print("Content:")
        print(document.page_content)
        print("--"*30)


if __name__ == "__main__":
    preview_retrieval()