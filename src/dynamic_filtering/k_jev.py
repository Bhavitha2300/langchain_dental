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
                instructions="Classify the clinician's question into exactly one category.",
                criteria={
                    "treatment_recommendation": ("The clinician is asking whether to proceed with or modify the "
                                                 "planned dental procedure, including management of the patient's "
                                                 "existing anticoagulant or antiplatelet medication."),
                    "guideline_explanation": ("The clinician is asking why, when, or how a guideline "
                                              "recommendation applies to this patient."),
                    "guideline_information": ("The clinician is asking about the guideline's name, source, "
                                              "purpose, scope, edition, or intended patient group."),
                    "drug_interaction": ("The clinician is asking whether they can prescribe, administer, "
                                         "or recommend another medicine for this patient. This includes "
                                         "questions such as 'Can I prescribe amoxicillin?' and questions "
                                         "about interactions with the patient's anticoagulant or "
                                         "antiplatelet medication."),
                    "patient_information": ("The clinician is asking for existing information about the "
                                            "patient's condition, current medication, planned procedure, "
                                            "or procedure bleeding risk."),
                    "other": ("The question is unrelated to this patient's dental treatment "
                              "or medicines.")
                })})
    question_type = response.answers["question_type"].choice
    return question_type

def preview_question_type():
    question = "should i proceed with the dental treatment?"
    question_type = classify_clinician_question(question)
    print(question_type)

if __name__ == "__main__":
    preview_question_type()