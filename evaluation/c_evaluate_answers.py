import csv
import json
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, FactualCorrectness, ResponseRelevancy
from config import load_config
from dynamic_filtering.k_jev import classify_clinician_question
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines, retrieve_guideline_information
from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
from dynamic_filtering.m_drug_interaction_retrieval import retrieve_drug_interactions
from dynamic_filtering.i_final_LLM_recommendation import final_response, format_guideline_documents

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR / "datasets" / "rag_evaluation_dataset.csv"
OUTPUT_FILE = EVALUATION_DIR / "results" / "ragas_answer_scores.csv"
ANSWERS_FILE = EVALUATION_DIR / "results" / "generated_answers.csv"


def evaluate_answers():
    load_config()
    with open(DATASET_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    fields = [
        "test_number",
        "fhir_patient_id",
        "clinician_question",
        "expected_question_type",
        "actual_question_type",
        "classification_result",
        "expected_status",
        "actual_status",
        "status_result",
        "expected_blocking_reason",
        "actual_blocking_reasons",
        "blocking_reason_result",
        "answer_source",
        "generated_answer",
        "evidence_contexts",
        "reference_answer"
    ]

    with open(ANSWERS_FILE, "w", newline="", encoding="utf-8") as file:
        csv.DictWriter(file, fieldnames=fields).writeheader()

    samples = []
    scored_cases = []

    for test_number, row in enumerate(rows, start=1):
        reference = row["reference_answer"].strip()
        if not reference:
            raise ValueError(f"Test {test_number} has no reference answer.")

        procedures = json.loads(row["planned_procedure"])
        answers = json.loads(row["clinician_answers"])
        expected_type = row["expected_question_type"].strip()
        expected_status = row["expected_status"].strip()
        expected_reason = row["expected_blocking_reason"].strip()

        actual_type = classify_clinician_question(row["clinician_question"])
        classification_ok = actual_type == expected_type

        if actual_type == "guideline_information":
            response = retrieve_guideline_information(row["clinician_question"])
            response["patient_context"] = {}
            if response["documents"] and not response["missing_sections"]:
                response["status"] = "retrieved"
            else:
                response["status"] = "no_matching_recommendation"

        elif actual_type == "other":
            message = final_response(
                patient_id=row["fhir_patient_id"],
                question=row["clinician_question"],
                question_type="other")
            response = {
                "status": "out_of_scope",
                "message": message,
                "documents": [],
                "patient_context": {}}

        elif not row["fhir_patient_id"].strip():
            response = {
                "status": "missing_patient_context",
                "message": "The selected route requires a patient ID.",
                "documents": [],
                "patient_context": {}}

        elif actual_type == "patient_information":
            patient = assess_patient_context(
                patient_id=row["fhir_patient_id"],
                visit_procedures=procedures)
            patient["clinical_assessment"]["patient_safety"] = answers

            response = {
                "status": "retrieved",
                "patient_context": patient,
                "documents": [],
                "found_sections": []}

        elif actual_type == "drug_interaction":
            response = retrieve_drug_interactions(
                patient_id=row["fhir_patient_id"],
                question=row["clinician_question"],
                safety_context=answers)

        elif actual_type in [
            "treatment_recommendation",
            "guideline_explanation"]:
            response = retrieve_filtered_guidelines(
                patient_id=row["fhir_patient_id"],
                question=row["clinician_question"],
                visit_procedures=procedures,
                safety_context=answers)

        else:
            response = {
                "status": "unsupported_evaluation_route",
                "message": f"Unexpected question type: {actual_type}",
                "documents": [],
                "patient_context": {}}
        retrieval = response
        status_ok = retrieval["status"] == expected_status
        actual_reasons = [
            reason.get("reason", "")
            for reason in retrieval.get("blocking_reasons", [])]

        reason_result = "NA"

        if expected_status == "needs_clinician_confirmation":
            if not expected_reason:
                raise ValueError( f"Test {test_number} needs a blocking reason.")

            reason_ok = (
                set(actual_reasons) == {expected_reason}
                and not retrieval.get("documents")
                and not retrieval.get("found_sections"))

            reason_result = "pass" if reason_ok else "fail"

        elif expected_status not in ["retrieved", "out_of_scope"]:
            raise ValueError(f"Test {test_number} has an invalid expected status.")

        patient = retrieval.get("patient_context", {})
        documents = retrieval.get("documents", [])

        patient_evidence = {
            "conditions": patient.get("conditions", []),
            "medications": patient.get("medications", []),
            "observations": patient.get("observations", []),
            "planned_procedures": patient.get("planned_procedures", []),
            "clinical_assessment": patient.get("clinical_assessment", {}),
            "safety_warnings": retrieval.get("safety_warnings", [])}

        patient_text = "Patient context: " + json.dumps(patient_evidence)
        guideline_text = format_guideline_documents(documents)
        clinician_text = "Clinician-provided question and scenario: " + row["clinician_question"]
        contexts = [clinician_text, patient_text, guideline_text]
        should_generate = (
            expected_status == "retrieved"
            and retrieval["status"] == "retrieved")

        if should_generate:
            answer = final_response(
                patient_id=row["fhir_patient_id"],
                question=row["clinician_question"],
                visit_procedures=procedures,
                safety_context=answers,
                question_type=actual_type,
                retrieval_result=retrieval)

            answer_source = "llm"
            samples.append({
                "user_input": row["clinician_question"],
                "response": answer,
                "retrieved_contexts": contexts,
                "reference": reference})

            scored_cases.append({
                "test_number": test_number,
                "fhir_patient_id": row["fhir_patient_id"],
                "expected_question_type": expected_type,
                "actual_question_type": actual_type,
                "classification_result": ("pass" if classification_ok else "fail")})

        else:
            answer = retrieval.get("blocking_message", retrieval.get("message", ""))
            answer_source = "system_message"

            if not answer:
                answer = ( "No LLM answer generated because the actual status "
                           "did not match the expected workflow.")

        with open(ANSWERS_FILE, "a", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writerow({
                "test_number": test_number,
                "fhir_patient_id": row["fhir_patient_id"],
                "clinician_question": row["clinician_question"],
                "expected_question_type": expected_type,
                "actual_question_type": actual_type,
                "classification_result": ("pass" if classification_ok else "fail"),
                "expected_status": expected_status,
                "actual_status": retrieval["status"],
                "status_result": "pass" if status_ok else "fail",
                "expected_blocking_reason": expected_reason,
                "actual_blocking_reasons": json.dumps(actual_reasons),
                "blocking_reason_result": reason_result,
                "answer_source": answer_source,
                "generated_answer": answer,
                "evidence_contexts": json.dumps(contexts),
                "reference_answer": reference
            })

        print(f"Test {test_number}: {retrieval['status']}, "
              f"classification {'pass' if classification_ok else 'fail'}")

    if not samples:
        print(f"No new LLM scores written. Check: {ANSWERS_FILE}")
        return

    results = evaluate(
        dataset=EvaluationDataset.from_list(samples),
        metrics=[Faithfulness(),
                 FactualCorrectness(mode="f1"),
                 ResponseRelevancy()],
        llm=LangchainLLMWrapper(ChatOpenAI(model="gpt-4o", temperature=0)),
        embeddings=LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small")),
        raise_exceptions=True)

    scores = results.to_pandas()
    columns = [
        "test_number",
        "fhir_patient_id",
        "expected_question_type",
        "actual_question_type",
        "classification_result"]

    for position, column in enumerate(columns):
        scores.insert(position,
                      column,
                      [case[column] for case in scored_cases])

    scores.to_csv(OUTPUT_FILE, index=False)

    print(results)
    print(f"LLM answers scored: {len(samples)}/{len(rows)}")
    print(f"All case outcomes saved to: {ANSWERS_FILE}")
    print(f"Ragas scores saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    evaluate_answers()