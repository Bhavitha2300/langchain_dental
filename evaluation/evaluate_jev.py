# evaluate.jev.py

from pathlib import Path
import csv
from dynamic_filtering.k_jev import classify_clinician_question

EVALUATION_DIR = Path(__file__).resolve().parent
DATASET_FILE = EVALUATION_DIR/ "datasets"/ "jev_question_classification.csv"
RESULT_FILE = EVALUATION_DIR / "results" / "jev_question_classification_results.csv"

def evaluate_jev_questions():
    correct_answers = 0
    total_questions = 0

    with open(DATASET_FILE, "r", encoding="utf-8") as file:
        data_dict = csv.DictReader(file)
        with open(RESULT_FILE,"w", encoding="utf-8", newline="") as result_file:
            result_writer = csv.writer(result_file)
            result_writer.writerow([
                "question",
                "expected_question_type",
                "actual_question_type",
                "result"
            ])
            for question_details in data_dict:
                question = question_details["question"]
                expected_question_type = question_details["expected_question_type"]
                actual_question_type = (classify_clinician_question(question))
                total_questions = total_questions + 1
                if actual_question_type == expected_question_type:
                    result = "pass"
                    correct_answers = correct_answers + 1
                else:
                    result = "fail"
                result_writer.writerow([
                    question,
                    expected_question_type,
                    actual_question_type,
                    result
                ])
    accuracy = correct_answers / total_questions * 100
    print()
    print("Correct answers:", correct_answers)
    print("Total questions:", total_questions)
    print("Accuracy:", round(accuracy, 2), "%")
    print("Results saved in:", RESULT_FILE)


if __name__ == "__main__":
    evaluate_jev_questions()




