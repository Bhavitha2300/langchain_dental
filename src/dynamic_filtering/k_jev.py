# k_jev.py

from config import load_config
from typesafe_sdk import Choice, TypeSafeClient

load_config()

def classify_clinician_question(question):
    client = TypeSafeClient()
    response = client.system_one(
        state=question,
        questions={
            "question_type": Choice(
                instructions= "What type of information is the clinician asking for?",
                criteria={
                    "treatment_recommendation": "The clinician is asking what to do for the planned dental treatment.",
                    "guideline_explanation": "The clinician is asking why, when, or how the guideline recommendation applies to this patient.",
                    "guideline_information": ("The clinician is asking which guideline is used, who produced it, its purpose, scope, edition, or intended patient group."),
                    "drug_interaction": ("The clinician is asking whether a medicine they are considering prescribing may interact with this patient's anticoagulant or antiplatelet medication."),
                    "patient_information": "The clinician is asking about this patient's condition, medicine, planned procedure, or bleeding risk.",
                    "other": "The question is not about this patient's dental treatment or medicines."})})
    question_type = response.answers["question_type"].choice

    return question_type

def preview_question_type():
    question = "should i proceed with the dental treatment?"
    question_type = classify_clinician_question(question)
    print(question_type)

if __name__ == "__main__":
    preview_question_type()