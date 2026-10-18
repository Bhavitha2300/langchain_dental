# l_langgraph_retrieval.py

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dynamic_filtering.b_vector_store import get_vector_store

class RetrievalState(TypedDict):
    question: str
    metadata_filters: list | None
    required_sections: list
    documents: list
    found_sections: list
    missing_sections: list
    search_method: str

def metadata_search(state):
    vector_store = get_vector_store()
    retrieved_documents = []
    for metadata_filter in state["metadata_filters"]:
        matching_documents = vector_store.similarity_search(
            query=state["question"],
            k=10,
            filter=metadata_filter)
        for document in matching_documents:
            if document not in retrieved_documents:
                retrieved_documents.append(document)
    found_sections = []
    missing_sections = []
    for required_section in state["required_sections"]:
        section_documents = []
        for document in retrieved_documents:
            document_section = document.metadata.get("subaspect", "")
            if document_section == required_section:
                section_documents.append(document)
        number_of_chunks_found = len(section_documents)
        if number_of_chunks_found == 0:
            missing_sections.append(required_section)
            continue
        expected_chunk_count = section_documents[0].metadata.get("subsection_chunk_count",0)
        if number_of_chunks_found == expected_chunk_count:
            found_sections.append(required_section)
        else:
            missing_sections.append(required_section)
    return {
        "documents": retrieved_documents,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
        "search_method": "metadata_filtered_similarity"
    }

def stop_search(state):
    required_sections = state["required_sections"]
    return {
        "documents": [],
        "found_sections": [],
        "missing_sections": required_sections,
        "search_method": "not_searched"
    }


def choose_search(state):
    metadata_filters = state["metadata_filters"]
    if metadata_filters is None:
        return "stop_search"
    if len(metadata_filters) == 0:
        return "stop_search"
    return "metadata_search"

workflow = StateGraph(RetrievalState)
workflow.add_node("metadata_search",metadata_search)
workflow.add_node("stop_search",stop_search)
workflow.add_conditional_edges(START,choose_search,
    {"metadata_search": "metadata_search",
     "stop_search": "stop_search"})
workflow.add_edge("metadata_search", END)
workflow.add_edge("stop_search", END)
retrieval_graph = workflow.compile()

def retrieve_documents(question,metadata_filters,required_sections):
    starting_state = {"question": question,
                      "metadata_filters": metadata_filters,
                      "required_sections": required_sections,
                      "documents": [],
                      "found_sections": [],
                      "missing_sections": [],
                      "search_method": ""}
    result = retrieval_graph.invoke(starting_state)
    retrieval_report = {"documents": result["documents"],
                        "requested_sections": required_sections,
                        "found_sections": result["found_sections"],
                        "missing_sections": result["missing_sections"],
                        "search_method": result["search_method"]}
    return retrieval_report
