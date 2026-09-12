# g_retrieve_filtered_guidelines.py

import pprint
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.f_assess_patient_context import (assess_patient_context)


def build_metadata_filter(assessed_context: dict):
    clinical_assessment = assessed_context.get("clinical_assessment",{})
    medication_classes = clinical_assessment.get("medication_classes",[])
    procedure_assessments = clinical_assessment.get("procedure_assessments",[])
    medications = assessed_context.get("medications",[])

    if not medication_classes:
        return None

    medication_class = medication_classes[0]

    ingredient_name = ""

    for medication in medications:
        if (
            medication.get("medication_class")
            == medication_class
        ):
            ingredient_name = medication.get("ingredient_name","")
            break

    if not ingredient_name:
        return None

    bleeding_risk = ""

    for procedure in procedure_assessments:
        if (
            procedure.get("classification_status")
            == "classified"
        ):
            bleeding_risk = procedure.get("postoperative_bleeding_risk","")
            break

    if not bleeding_risk:
        return None

    metadata_filter = {
        "$and": [
            {
                "medication_classes": {
                    "$ilike": (
                        f'%"{medication_class}"%'
                    )
                }
            },
            {
                "medications": {
                    "$ilike": (
                        f'%"{ingredient_name}"%'
                    )
                }
            },
            {
                "postoperative_bleeding_risk": {
                    "$eq": bleeding_risk
                }
            }
        ]
    }

    return metadata_filter


def retrieve_filtered_guidelines(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = ""
):
    assessed_context = assess_patient_context(patient_id, extraction_complexity, wound_size)

    metadata_filter = build_metadata_filter(assessed_context)

    if metadata_filter is None:
        return {
            "status": "needs_clinician_confirmation",
            "patient_context": assessed_context,
            "metadata_filter": None,
            "documents": []
        }

    vector_store = get_vector_store()

    documents = vector_store.similarity_search(
        query=question,
        k=5,
        filter=metadata_filter
    )

    return {
        "status": "retrieved",
        "patient_context": assessed_context,
        "metadata_filter": metadata_filter,
        "documents": documents
    }


def preview_retrieval():
    patient_id = "1000"

    question = (
        "How should this patient's apixaban be managed "
        "for the planned dental extraction?"
    )

    result = retrieve_filtered_guidelines(
        patient_id=patient_id,
        question=question,
        extraction_complexity="simple",
        wound_size="restricted"
    )

    print("Status:")
    print(result["status"])
    print()

    print("Metadata filter:")
    pprint.pprint(result["metadata_filter"])
    print()

    print("Retrieved guideline documents:")
    print()

    for document in result["documents"]:
        print("Metadata:")
        pprint.pprint(document.metadata)
        print()

        print("Content:")
        print(document.page_content)
        print()

        print("--" * 40)


if __name__ == "__main__":
    preview_retrieval()