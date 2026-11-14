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
                instructions=(
                    "Classify the clinician's question into exactly one category. "
                    "Questions about what to do for a specific patient must use "
                    "the appropriate patient-specific category, even if they "
                    "mention guidelines. Use guideline_information for general "
                    "questions about what SDCEP says."
                ),
                criteria={
                    "treatment_recommendation": ("The clinician is asking whether to proceed with or modify the "
                                                 "planned dental procedure, including management of the patient's "
                                                 "existing anticoagulant or antiplatelet medication."),
                    "guideline_explanation": ("The clinician is asking why, when, or how a guideline "
                                              "recommendation applies to this patient."),
                    "guideline_information": ("General questions about the SDCEP guideline's source, scope, "
                                              "recommendations or explanations. Includes general questions "
                                              "about haemostasis, staged treatment, postoperative advice "
                                              "and drug interactions. The question does not request a "
                                              "decision for a specific patient."),
                    "drug_interaction": ("The clinician asks about prescribing or giving another "
                                         "medicine to a specific patient, or interactions with "
                                         "that patient's medicines. Includes 'Can I prescribe "
                                         "amoxicillin?' General questions about what SDCEP says "
                                         "about interactions belong to guideline_information."),
                    "patient_information": ("The clinician is asking for existing information about the "
                                            "patient's condition, current medication, planned procedure, "
                                            "or procedure bleeding risk."),
                    "other": ("The question is outside both the patient's dental "
                              "antithrombotic management and the stored SDCEP guidance."),
                })})
    question_type = response.answers["question_type"].choice
    return question_type

def preview_question_type():
    question = "should i proceed with the dental treatment?"
    question_type = classify_clinician_question(question)
    print(question_type)

if __name__ == "__main__":
    preview_question_type()