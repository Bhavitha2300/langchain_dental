import csv
import json
from pathlib import Path
from ragas import EvaluationDataset, evaluate
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall

from dynamic_filtering.k_jev import classify_clinician_question
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines, retrieve_guideline_information
from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
from dynamic_filtering.m_drug_interaction_retrieval import retrieve_drug_interactions
from dynamic_filtering.i_final_LLM_recommendation import final_response

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR / "datasets" / "rag_evaluation_dataset.csv"
RESULT_FILE = EVALUATION_DIR / "results_3" / "ragas_retrieval_results.csv"


def evaluate_retrieval():
    with open(DATASET_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("The dataset is empty.")

    samples = []
    details = []
    scored_details = []

    for test_number, row in enumerate(rows, start=1):
        procedures = json.loads(row["planned_procedure"])
        answers = json.loads(row["clinician_answers"])
        expected_sections = sorted(set(json.loads(row["expected_guideline_section_ids"])))

        expected_type = row["expected_question_type"].strip()
        expected_status = row["expected_status"].strip()
        expected_reason = row["expected_blocking_reason"].strip()

        jev_usage = {}
        actual_type = classify_clinician_question(
            row["clinician_question"], usage=jev_usage)

        jev_cost_usd = ""
        if jev_usage["input_tokens"] is not None:
            jev_cost_usd = round(
                jev_usage["input_tokens"] * 0.042 / 1_000_000, 10)
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
            patient = assess_patient_context(patient_id=row["fhir_patient_id"], visit_procedures=procedures)
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

        actual_sections = response.get("found_sections")
        if actual_sections is None:
            actual_sections = [
                document.metadata["subaspect"]
                for document in response.get("documents", [])
            ]

        actual_sections = sorted(set(actual_sections))
        status_ok = response["status"] == expected_status
        actual_reasons = [
            reason.get("reason", "")
            for reason in response.get("blocking_reasons", [])
        ]

        reason_result = "NA"
        section_result = "NA"
        score_guidelines = (
            expected_status == "retrieved"
            and expected_type not in ["patient_information", "other"])

        if score_guidelines:
            if not expected_sections:
                raise ValueError(f"Test {test_number} needs expected guideline sections.")

            sections_ok = actual_sections == expected_sections
            section_result = "pass" if sections_ok else "fail"

            success = classification_ok and status_ok and sections_ok

            samples.append({
                "user_input": row["clinician_question"],
                "retrieved_context_ids": actual_sections,
                "reference_context_ids": expected_sections})

        elif expected_type == "patient_information" and expected_status == "retrieved":
            success = (
                classification_ok and status_ok
                and bool(response.get("patient_context"))
                and not expected_sections and not actual_sections
                and not response.get("documents"))

        elif expected_type == "other" and expected_status == "out_of_scope":
            success = (
                classification_ok and status_ok
                and bool(response.get("message"))
                and not expected_sections and not actual_sections
                and not response.get("documents"))

        elif expected_status == "needs_clinician_confirmation":
            if expected_sections or not expected_reason:
                raise ValueError(f"Test {test_number} needs [] and a blocking reason.")

            reason_ok = (
                set(actual_reasons) == {expected_reason}
                and not response.get("documents")
                and not actual_sections
            )

            reason_result = "pass" if reason_ok else "fail"
            success = classification_ok and status_ok and reason_ok

        else:
            raise ValueError(f"Test {test_number} has an invalid expected status.")

        detail = {
            "test_number": test_number,
            "fhir_patient_id": row["fhir_patient_id"],
            "clinician_question": row["clinician_question"],
            "expected_question_type": expected_type,
            "actual_question_type": actual_type,
            "jev_model": jev_usage["model"],
            "jev_input_tokens": jev_usage["input_tokens"],
            "jev_output_tokens": jev_usage["output_tokens"],
            "jev_cost_usd": jev_cost_usd,
            "classification_result": "pass" if classification_ok else "fail",
            "expected_status": expected_status,
            "actual_status": response["status"],
            "status_result": "pass" if status_ok else "fail",
            "expected_blocking_reason": expected_reason,
            "actual_blocking_reasons": json.dumps(actual_reasons),
            "blocking_reason_result": reason_result,
            "expected_sections": json.dumps(expected_sections),
            "actual_sections": json.dumps(actual_sections),
            "section_result": section_result,
            "missing_sections": json.dumps(sorted(set(expected_sections) - set(actual_sections))),
            "unexpected_sections": json.dumps(sorted(set(actual_sections) - set(expected_sections))),
            "requested_sections": json.dumps(response.get("requested_sections", [])),
            "retrieval_missing_sections": json.dumps(response.get("missing_sections", [])),
            "ragas_precision": "NA",
            "ragas_recall": "NA",
            "result": "pass" if success else "fail",
            "message": response.get("blocking_message", response.get("message", ""))
        }

        details.append(detail)

        if score_guidelines:
            scored_details.append(detail)

        print(f"Test {test_number}: {detail['result']}")

    if samples:
        results = evaluate(
            dataset=EvaluationDataset.from_list(samples),
            metrics=[IDBasedContextPrecision(),
                     IDBasedContextRecall()],
            raise_exceptions=True)

        scores = results.to_pandas().to_dict("records")

        for detail, score in zip(scored_details, scores):
            detail["ragas_precision"] = score["id_based_context_precision"]
            detail["ragas_recall"] = score["id_based_context_recall"]

    with open(RESULT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(details[0]))
        writer.writeheader()
        writer.writerows(details)

    passed = sum(detail["result"] == "pass" for detail in details)

    print(f"Passed: {passed}/{len(details)}")
    print(f"Results saved to: {RESULT_FILE}")


if __name__ == "__main__":
    evaluate_retrieval()