# g_retrieve_filtered_guidelines.py

import pprint
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.f_assess_patient_context import assess_patient_context


def build_metadata_filters(assessed_context: dict):
    clinical_assessment = assessed_context.get(
        "clinical_assessment",
        {}
    )

    procedure_assessments = clinical_assessment.get(
        "procedure_assessments",
        []
    )

    medications = assessed_context.get("medications", [])

    metadata_filters = []

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
            ingredient_name
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        medication_class_filter = {
            "medication_classes": {
                "$ilike": f'%"{medication_class}"%'
            }
        }

        medication_ingredient_filter = {
            "medications": {
                "$ilike": f'%"{ingredient_name}"%'
            }
        }

        broad_filter = {
            "$or": [
                medication_class_filter,
                medication_ingredient_filter
            ]
        }

        metadata_filters.append(broad_filter)

        # More specific procedure-risk search.
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

            specific_filter = {
                "$and": [
                    medication_class_filter,
                    medication_ingredient_filter,
                    {
                        "postoperative_bleeding_risk": {
                            "$eq": bleeding_risk
                        }
                    }
                ]
            }

            metadata_filters.append(specific_filter)

    if not metadata_filters:
        return None

    return metadata_filters


def retrieve_filtered_guidelines(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = ""
):
    assessed_context = assess_patient_context(patient_id, extraction_complexity, wound_size)
    metadata_filters = build_metadata_filters(assessed_context)

    if metadata_filters is None:
        return {
            "status": "needs_clinician_confirmation",
            "patient_context": assessed_context,
            "metadata_filters": None,
            "documents": []
        }

    vector_store = get_vector_store()

    documents = []
    added_chunk_ids = []

    for metadata_filter in metadata_filters:
        retrieved_documents = vector_store.similarity_search(
            query=question,
            k=5,
            filter=metadata_filter
        )

        for document in retrieved_documents:
            chunk_id = document.metadata.get("chunk_id", "")

            if chunk_id in added_chunk_ids:
                continue

            added_chunk_ids.append(chunk_id)
            documents.append(document)

    return {
        "status": "retrieved",
        "patient_context": assessed_context,
        "metadata_filters": metadata_filters,
        "documents": documents
    }


def preview_retrieval():
    patient_id = "1256"

    question = "How should this patient's apixaban be managed for the planned dental extraction?"

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
    pprint.pprint(result["metadata_filters"])
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