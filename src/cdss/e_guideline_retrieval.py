from cdss.d_get_patient_summary import get_patient_summary
from cdss.b_vector_store import get_vector_store


def formatting_guideline_docs(documents):
    all_guideline_context = ""
    for document in documents:
        h1 = document.metadata.get("h1", "")
        h2 = document.metadata.get("h2", "")
        h3 = document.metadata.get("h3", "")
        h4 = document.metadata.get("h4", "")
        content = document.page_content
        one_guideline_context = f"""
                    H1:{h1}
                    H2:{h2}
                    H3:{h3}
                    H4:{h4}
                    
                    {content}
                    """
        all_guideline_context = all_guideline_context +"\n"+ one_guideline_context
    return all_guideline_context


def retrieve_guidelines(patient_id: str, question: str):
    patient_summary = get_patient_summary(patient_id)
    template = f"""
            Patient Context: 
            {patient_summary}
            
            Clinical question: 
            {question}
            """

    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_kwargs = {
            "k": 10
        }
    )
    raw_documents = retriever.invoke(template)
    guideline_context = formatting_guideline_docs(raw_documents)
    return patient_summary, guideline_context

# def preview_guidelines():
#     patient_id = "1000"
#     question = "What are the guideline-based antithrombotic management considerations for this patient's planned dental procedure?"
#
#     patient_summary, guideline_context = retrieve_guidelines(patient_id, question)
#     print(patient_summary)
#
#     print(guideline_context)


if __name__ == "__main__":
    retrieve_guidelines()
