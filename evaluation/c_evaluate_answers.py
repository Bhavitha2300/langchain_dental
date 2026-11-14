import csv
import json
from pathlib import Path

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas import EvaluationDataset, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, FactualCorrectness, ResponseRelevancy

from config import load_config

EVALUATION_DIR = Path(__file__).resolve().parent
INPUT_FILE = EVALUATION_DIR / "results" / "ragas_answer_results.csv"
OUTPUT_FILE = EVALUATION_DIR / "results" / "ragas_saved_answer_scores.csv"


def evaluate_answers():
    load_config()

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    samples = []

    for row in rows:
        if not row["generated_answer"].strip():
            raise ValueError(f"Test {row['test_number']} has no generated answer.")

        samples.append({"user_input": row["clinician_question"],
                        "response": row["generated_answer"],
                        "retrieved_contexts": json.loads(row["evidence_contexts"]),
                        "reference": row["reference_answer"]})

    dataset = EvaluationDataset.from_list(samples)

    judge = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o", temperature=0))
    embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))

    results = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            FactualCorrectness(mode="f1"),
            ResponseRelevancy()
        ],
        llm=judge,
        embeddings=embeddings,
        raise_exceptions=True
    )

    scores = results.to_pandas()

    scores.insert(
        0,
        "test_number",
        [row["test_number"] for row in rows]
    )

    scores.insert(
        1,
        "fhir_patient_id",
        [row["fhir_patient_id"] for row in rows]
    )

    scores.to_csv(OUTPUT_FILE, index=False)

    print(results)
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    evaluate_answers()