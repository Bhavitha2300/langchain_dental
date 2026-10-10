# l_guideline_retrieval_graph.py

from langgraph.graph import StateGraph, START, END
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines

# First try the exact metadata retrieval from h
def run_metadata_retrieval(state):
    retrieval_result = retrieve_filtered_guidelines(
        patient_id=state["patient_id"],
        question=state["question"],
        extraction_complexity=state["extraction_complexity"],
        wound_size=state["wound_size"],
        safety_context=state["safety_context"])

    retrieval_result["retrieval_method"] = "metadata"
    state["retrieval_result"] = retrieval_result
    return state

# Decide whether similarity search is needed
def choose_retrieval_path(state):
    retrieval_result = state["retrieval_result"]
    status = retrieval_result.get("status", "")
    if status in ["no_metadata_filters", "no_matching_recommendation"]:
        return "similarity_search"
    return "finish"


# Use similarity search only when metadata retrieval found nothing
def run_similarity_search(state):
    vector_store = get_vector_store()
    documents = vector_store.similarity_search(
        query=state["question"],
        k=5,
        filter={"record_type": {"$eq": "clinical_recommendation"}}
    )
    retrieval_result = state["retrieval_result"]
    retrieval_result["retrieval_method"] = "similarity"

    if documents:
        retrieval_result["status"] = "similarity_result"
        retrieval_result["documents"] = documents
        retrieval_result["blocking_reasons"] = []
        retrieval_result["blocking_message"] = ""
    state["retrieval_result"] = retrieval_result

    return state


# Create the graph
workflow = StateGraph(dict)

workflow.add_node(
    "metadata_retrieval",
    run_metadata_retrieval
)

workflow.add_node(
    "similarity_search",
    run_similarity_search
)

workflow.add_edge(
    START,
    "metadata_retrieval"
)

workflow.add_conditional_edges(
    "metadata_retrieval",
    choose_retrieval_path,
    {
        "similarity_search": "similarity_search",
        "finish": END
    }
)

workflow.add_edge(
    "similarity_search",
    END
)

guideline_retrieval_graph = workflow.compile()


# This function starts the graph
def retrieve_guidelines_with_graph(
    patient_id,
    question,
    extraction_complexity="",
    wound_size="",
    safety_context=None
):
    if safety_context is None:
        safety_context = {}

    starting_state = {
        "patient_id": patient_id,
        "question": question,
        "extraction_complexity": extraction_complexity,
        "wound_size": wound_size,
        "safety_context": safety_context,
        "retrieval_result": {}
    }

    final_state = guideline_retrieval_graph.invoke(starting_state)

    return final_state["retrieval_result"]