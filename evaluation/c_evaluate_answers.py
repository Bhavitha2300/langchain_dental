import csv
import json
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, FactualCorrectness, ResponseRelevancy
from config import load_config
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines
from dynamic_filtering.i_final_LLM_recommendation import final_response, format_guideline_documents

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR / "datasets" / "rag_evaluation_dataset.csv"
OUTPUT_FILE = EVALUATION_DIR / "results" / "ragas_answer_scores.csv"


def evaluate_answers():
    load_config()
    with open(DATASET_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("The dataset is empty.")
    samples = []
    for test_number, row in enumerate(rows, start=1):
        reference = row["reference_answer"].strip()
        if not reference:
            raise ValueError(f"Test {test_number} has no reference answer.")

        procedures = json.loads(row["planned_procedure"])
        safety_answers = json.loads(row["clinician_answers"])

        # Retrieve the patient information and guideline evidence.
        retrieval = retrieve_filtered_guidelines(
            patient_id=row["fhir_patient_id"],
            question=row["clinician_question"],
            visit_procedures=procedures,
            safety_context=safety_answers)

        if retrieval["status"] != "retrieved":
            raise ValueError(f"Test {test_number}: {retrieval['blocking_message']}")

        # Generate an answer using this exact retrieval result.
        answer = final_response(
            patient_id=row["fhir_patient_id"],
            question=row["clinician_question"],
            visit_procedures=procedures,
            safety_context=safety_answers,
            question_type="treatment_recommendation",
            retrieval_result=retrieval)

        # Give Ragas the same evidence supplied to the answer generator.
        patient = retrieval["patient_context"]
        patient_evidence = {
            "conditions": patient.get("conditions", []),
            "medications": patient.get("medications", []),
            "observations": patient.get("observations", []),
            "planned_procedures": patient.get("planned_procedures", []),
            "clinical_assessment": patient.get("clinical_assessment", {}),
            "safety_warnings": retrieval.get("safety_warnings", [])}

        contexts = ["Patient context: " + json.dumps(patient_evidence),
                    format_guideline_documents(retrieval["documents"])]
        samples.append({
            "user_input": row["clinician_question"],
            "response": answer,
            "retrieved_contexts": contexts,
            "reference": reference})

    dataset = EvaluationDataset.from_list(samples)
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o", temperature=0))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))
    results = evaluate(
        dataset=dataset,
        metrics=[Faithfulness(),
                 FactualCorrectness(mode="f1"),
                 ResponseRelevancy()],
        llm=evaluator_llm,
        embeddings=embeddings,
        raise_exceptions=True)

    scores = results.to_pandas()
    scores.insert(0, "test_number", range(1, len(rows) + 1))
    scores.insert(1,"fhir_patient_id",[row["fhir_patient_id"] for row in rows])
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(OUTPUT_FILE, index=False)
    print(results)
    print(f"Results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    evaluate_answers()