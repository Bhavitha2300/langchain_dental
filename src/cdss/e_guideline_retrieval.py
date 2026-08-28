from cdss.d_get_patient_summary import get_patient_summary
from cdss.b_vector_store import get_vector_store


def retrieve_guidelines(patient_id: str):
    patient_summary = get_patient_summary(patient_id)
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 5
        }
    )

    documents = retriever.invoke(patient_summary)

    print("PATIENT SUMMARY")
    print(patient_summary)
    print()
    print("-" * 60)

    print("RETRIEVED GUIDELINE DOCUMENTS")

    for document in documents:
        print()
        print("METADATA:")
        print(document.metadata)
        print()
        print("CONTENT:")
        print(document.page_content)
        print()
        print("-" * 60)

    return documents


if __name__ == "__main__":
    retrieve_guidelines("1000")