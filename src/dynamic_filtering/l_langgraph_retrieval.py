# l_langgraph_retrieval.py

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dynamic_filtering.b_vector_store import get_vector_store

class RetrievalState(TypedDict):
    question: str
    question_type: str
    metadata_filters: list | None
    documents: list

def metadata_search(state):
    vector_store = get_vector_store()
    documents = []
    for metadata_filter in state["metadata_filters"]:
        matching_documents = vector_store.similarity_search(
            query=state["question"],
            k=10,
            filter=metadata_filter)
        for document in matching_documents:
            if document not in documents:
                documents.append(document)
    return {"documents": documents}

def similarity_search(state):
    vector_store = get_vector_store()
    documents = vector_store.similarity_search(
        query=state["question"],
        k=10
    )
    return {"documents": documents}

def choose_search(state):
    if not state["metadata_filters"]:
        return "similarity_search"
    return "metadata_search"

def check_metadata_search(state):
    if state["documents"]:
        return "documents_found"
    return "no_documents_found"

workflow = StateGraph(RetrievalState)
workflow.add_node("metadata_search", metadata_search)
workflow.add_node("similarity_search", similarity_search)
workflow.add_conditional_edges(START,choose_search,
    {"metadata_search": "metadata_search",
              "similarity_search": "similarity_search"})
workflow.add_conditional_edges("metadata_search",check_metadata_search,
                               {"documents_found": END,
                                "no_documents_found": "similarity_search"})
workflow.add_edge("similarity_search", END)
retrieval_graph = workflow.compile()

def retrieve_documents(question, question_type, metadata_filters):
    result = retrieval_graph.invoke({
        "question": question,
        "question_type": question_type,
        "metadata_filters": metadata_filters,
        "documents": []})

    return result["documents"]