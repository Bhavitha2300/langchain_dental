import asyncio
import csv
import json
import math
from pathlib import Path

from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall
from dynamic_filtering.h_retrieve_filtered_guidelines import retrieve_filtered_guidelines

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR / "datasets" / "rag_evaluation_dataset.csv"
RESULT_FILE = EVALUATION_DIR / "results" / "ragas_retrieval_results.csv"

async def evaluate_retrieval():
    precision_metric = IDBasedContextPrecision()
    recall_metric = IDBasedContextRecall()

    total = 0
    passed = 0
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with (
        open(DATASET_FILE, newline="", encoding="utf-8-sig") as dataset_file,
        open(RESULT_FILE, "w", newline="", encoding="utf-8") as result_file
    ):
        dataset = csv.DictReader(dataset_file)

        writer = csv.DictWriter(
            result_file,
            fieldnames=[
                "test_number",
                "fhir_patient_id",
                "clinician_question",
                "status",
                "expected_sections",
                "actual_sections",
                "missing_sections",
                "unexpected_sections",
                "ragas_precision",
                "ragas_recall",
                "result",
                "error"
            ]
        )
        writer.writeheader()

        for test_number, row in enumerate(dataset, start=1):
            total += 1

            output = {
                "test_number": test_number,
                "fhir_patient_id": row["fhir_patient_id"],
                "clinician_question": row["clinician_question"]
            }

            try:
                procedures = json.loads(row["planned_procedure"])
                answers = json.loads(row["clinician_answers"])

                expected = sorted(set(
                    json.loads(row["expected_guideline_section_ids"])
                ))

                if not expected:
                    raise ValueError("Expected guideline sections are empty.")

                response = retrieve_filtered_guidelines(
                    patient_id=row["fhir_patient_id"],
                    question=row["clinician_question"],
                    visit_procedures=procedures,
                    safety_context=answers
                )

                actual = sorted({
                    document.metadata["subaspect"]
                    for document in response["documents"]
                })

                sample = SingleTurnSample(
                    user_input=row["clinician_question"],
                    retrieved_context_ids=actual,
                    reference_context_ids=expected
                )

                precision = await precision_metric.single_turn_ascore(sample)
                recall = await recall_metric.single_turn_ascore(sample)

                missing = sorted(set(expected) - set(actual))
                unexpected = sorted(set(actual) - set(expected))

                success = (
                    response["status"] == "retrieved"
                    and actual == expected
                )

                if success:
                    passed += 1

                output.update({
                    "status": response["status"],
                    "expected_sections": json.dumps(expected),
                    "actual_sections": json.dumps(actual),
                    "missing_sections": json.dumps(missing),
                    "unexpected_sections": json.dumps(unexpected),
                    "ragas_precision": (
                        "NA" if math.isnan(precision)
                        else round(precision, 3)
                    ),
                    "ragas_recall": round(recall, 3),
                    "result": "pass" if success else "fail",
                    "error": response.get("blocking_message", "")
                })

            except Exception as error:
                output.update({
                    "status": "error",
                    "result": "error",
                    "error": str(error)
                })

            writer.writerow(output)
            print(f"Test {test_number}: {output['result']}")

    print(f"\nPassed: {passed}/{total}")

    if total:
        print(f"Exact-match pass rate: {passed / total * 100:.1f}%")

    print(f"Results saved to: {RESULT_FILE}")


if __name__ == "__main__":
    asyncio.run(evaluate_retrieval())