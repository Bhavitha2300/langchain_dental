# g_retrieve_filtered_guidelines.py

import pprint
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.f_assess_patient_context import (assess_patient_context)


def build_metadata_filter(assessed_context: dict):
    clinical_assessment = assessed_context.get(
        "clinical_assessment",
        {}
    )

    procedure_assessments = clinical_assessment.get(
        "procedure_assessments",
        []
    )

    medications = assessed_context.get("medications", [])

    filter_list = []
    added_combinations = []

    for medication in medications:
        medication_class = medication.get(
            "medication_class",
            ""
        )

        ingredient_name = medication.get(
            "ingredient_name",
            ""
        )

        if not medication_class or not ingredient_name:
            continue

        ingredient_name = (
            ingredient_name.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        for procedure in procedure_assessments:
            classification_status = procedure.get(
                "classification_status",
                ""
            )

            bleeding_risk = procedure.get(
                "postoperative_bleeding_risk",
                ""
            )

            if classification_status != "classified":
                continue

            if not bleeding_risk:
                continue

            combination = (
                medication_class,
                ingredient_name,
                bleeding_risk
            )

            if combination in added_combinations:
                continue

            added_combinations.append(combination)

            filter_list.append({
                "$and": [
                    {
                        "medication_classes": {
                            "$ilike": f'%"{medication_class}"%'
                        }
                    },
                    {
                        "medications": {
                            "$ilike": f'%"{ingredient_name}"%'
                        }
                    },
                    {
                        "postoperative_bleeding_risk": {
                            "$eq": bleeding_risk
                        }
                    }
                ]
            })

    if not filter_list:
        return None

    if len(filter_list) == 1:
        return filter_list[0]

    return {
        "$or": filter_list
    }


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