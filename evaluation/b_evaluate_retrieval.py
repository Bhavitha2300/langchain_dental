import csv
import json
from pathlib import Path
from ragas import EvaluationDataset, evaluate
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR / "datasets" / "rag_evaluation_dataset.csv"
RESULT_FILE = EVALUATION_DIR / "results" / "ragas_retrieval_results.csv"


def evaluate_retrieval():
    with open(DATASET_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        raise ValueError("The dataset is empty.")

    samples = []
    details = []
    for row in rows:
        procedures = json.loads(row["planned_procedure"])
        answers = json.loads(row["clinician_answers"])
        expected = sorted(set(json.loads(row["expected_guideline_section_ids"])))
        if not expected:
            raise ValueError(f"Patient {row['fhir_patient_id']} has no expected sections.")

        response = retrieve_filtered_guidelines(
            patient_id=row["fhir_patient_id"],
            question=row["clinician_question"],
            visit_procedures=procedures,
            safety_context=answers)

        actual = sorted({
            document.metadata["subaspect"]
            for document in response["documents"]
        })

        samples.append({
            "user_input": row["clinician_question"],
            "retrieved_context_ids": actual,
            "reference_context_ids": expected
        })

        success = (
            response["status"] == "retrieved"
            and actual == expected
        )

        details.append({
            "fhir_patient_id": row["fhir_patient_id"],
            "status": response["status"],
            "result": "pass" if success else "fail",
            "missing_sections": json.dumps(sorted(set(expected) - set(actual))),
            "unexpected_sections": json.dumps(sorted(set(actual) - set(expected))),
            "error": response.get("blocking_message", "")
        })

    dataset = EvaluationDataset.from_list(samples)

    results = evaluate(
        dataset=dataset,
        metrics=[IDBasedContextPrecision(),
                 IDBasedContextRecall()],
        raise_exceptions=True
    )

    scores = results.to_pandas()
    scores.insert(0, "test_number", range(1, len(rows) + 1))

    for column in details[0]:
        scores[column] = [item[column] for item in details]

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(RESULT_FILE, index=False)

    print(results)
    print(f"Results saved to: {RESULT_FILE}")


if __name__ == "__main__":
    evaluate_retrieval()