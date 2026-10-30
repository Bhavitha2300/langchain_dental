# l_langgraph_retrieval.py

from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.a_load_split_guidelines import load_documents

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
    all_guideline_chunks_created_from_yaml = load_documents()
    chunks_returned_by_vector_search = []
    for one_metadata_filter in state["metadata_filters"]:
        searched_results = vector_store.similarity_search(
            query=state["question"],
            k=10,
            filter=one_metadata_filter
        )
        for retrieved_chunk in searched_results:
            if retrieved_chunk not in chunks_returned_by_vector_search:
                chunks_returned_by_vector_search.append(retrieved_chunk)

    found_subaspect_names = []
    missing_subaspect_names = []
    all_verified_chunks = []
    for required_subaspect_name in state["required_sections"]:
        expected_chunks_for_this_subaspect = []
        for guideline_chunk in all_guideline_chunks_created_from_yaml:
            guideline_chunk_subaspect = guideline_chunk.metadata.get("subaspect","")
            if guideline_chunk_subaspect == required_subaspect_name:
                expected_chunks_for_this_subaspect.append(guideline_chunk)
        verified_chunks_for_this_subaspect = []
        for expected_chunk in expected_chunks_for_this_subaspect:
            for retrieved_chunk in chunks_returned_by_vector_search:
                if retrieved_chunk.page_content != expected_chunk.page_content:
                    continue
                all_metadata_matches = True
                for metadata_key, expected_metadata_value in expected_chunk.metadata.items():
                    retrieved_metadata_value = (retrieved_chunk.metadata.get(metadata_key))
                    if retrieved_metadata_value != expected_metadata_value:
                        all_metadata_matches = False
                        break
                if all_metadata_matches:
                    verified_chunks_for_this_subaspect.append(retrieved_chunk)
                    break
        expected_chunk_count = len(expected_chunks_for_this_subaspect)
        verified_chunk_count = len(verified_chunks_for_this_subaspect)
        if expected_chunk_count > 0 and verified_chunk_count == expected_chunk_count:
            found_subaspect_names.append(required_subaspect_name)
            all_verified_chunks.extend(verified_chunks_for_this_subaspect)
        else:
            missing_subaspect_names.append( required_subaspect_name)
    if missing_subaspect_names:
        all_verified_chunks = []
    return {
        "documents": all_verified_chunks,
        "found_sections": found_subaspect_names,
        "missing_sections": missing_subaspect_names,
        "search_method": "metadata_filtered_similarity"
    }

def stop_search(state):
    required_subaspect_names = state["required_sections"]
    return {
        "documents": [],
        "found_sections": [],
        "missing_sections": required_subaspect_names,
        "search_method": "not_searched"
    }

def choose_search(state):
    available_metadata_filters = state["metadata_filters"]
    if available_metadata_filters is None:
        return "stop_search"
    if len(available_metadata_filters) == 0:
        return "stop_search"
    return "metadata_search"


workflow = StateGraph(RetrievalState)
workflow.add_node("metadata_search", metadata_search)
workflow.add_node( "stop_search", stop_search)
workflow.add_conditional_edges(START,choose_search,{
        "metadata_search": "metadata_search",
        "stop_search": "stop_search"})
workflow.add_edge( "metadata_search",END)
workflow.add_edge("stop_search",END)
retrieval_graph = workflow.compile()

def retrieve_documents(
    question,
    metadata_filters,
    required_sections
):
    retrieval_starting_state = {
        "question": question,
        "metadata_filters": metadata_filters,
        "required_sections": required_sections,
        "documents": [],
        "found_sections": [],
        "missing_sections": [],
        "search_method": ""
    }
    graph_result = retrieval_graph.invoke(retrieval_starting_state)
    retrieval_report = {
        "documents": graph_result["documents"],
        "requested_sections": required_sections,
        "found_sections": graph_result["found_sections"],
        "missing_sections": graph_result["missing_sections"],
        "search_method": graph_result["search_method"]
    }
    return retrieval_report