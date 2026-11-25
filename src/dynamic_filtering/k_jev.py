# k_jev.py

from config import load_config
from typesafe_sdk import Choice, TypeSafeClient

load_config()

def classify_clinician_question(question, usage=None):
    client = TypeSafeClient()
    response = client.system_one(
        state=question,
        questions={
            "question_type": Choice(
                instructions=(
                    "Classify the clinician's main request, not just its medical topic. "
                    "Use guideline_explanation when the clinician asks for the reason "
                    "behind advice or an assessment for a specific patient. "
                    "Mentioning medicines, procedures or conditions does not turn "
                    "an explanation request into a treatment decision, interaction "
                    "check or request for recorded facts. "
                    "Use treatment_recommendation for a new management decision. "
                    "Use guideline_information for general SDCEP guidance "
                    "not applied to a specific patient."
                ),
                criteria={
                    "treatment_recommendation": ("The clinician is asking whether to proceed with or modify the "
                                                 "planned dental procedure, including management of the patient's "
                                                 "existing anticoagulant or antiplatelet medication."),
                    "guideline_explanation": (
                        "The clinician asks for the reason or rationale behind "
                        "guideline-based advice, a previous management decision "
                        "or a bleeding-risk assessment for a specific patient. "
                        "They want to understand the advice or assessment, "
                        "rather than request a new treatment plan."
                    ),
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

    if usage is not None:
        usage["model"] = response.model
        usage["input_tokens"] = response.usage.input_tokens
        usage["output_tokens"] = response.usage.output_tokens

    return question_type

def preview_question_type():
    question = "should i proceed with the dental treatment?"
    question_type = classify_clinician_question(question)
    print(question_type)

if __name__ == "__main__":
    preview_question_type()