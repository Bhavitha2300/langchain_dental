# g_retrieve_filtered_guidelines.py

import pprint
from dynamic_filtering.b_vector_store import get_vector_store
from dynamic_filtering.f_assess_patient_context import assess_patient_context

SUPPORTED_MEDICATION_CLASSES = [
    "doac",
    "vitamin_k_antagonist",
    "low_molecular_weight_heparin",
    "unfractionated_heparin",
    "antiplatelet"
]


def normalize_value(value):
    return (value.strip().lower().replace("-", "_").replace(" ", "_"))

def find_patient_safety_reasons(assessed_context: dict):

    safety_reasons = []
    clinical_assessment = assessed_context.get("clinical_assessment",{})
    patient_safety = clinical_assessment.get("patient_safety",{})

    # without answering these questions the program will not recommend answer because it is not advisable to proceed without knowing answers to these questions
    required_yes_no_questions = [
        "prosthetic_metal_heart_valve",
        "coronary_stent",
        "dvt_or_pe_within_3_months",
        "anticoagulation_for_cardioversion",
        "initial_high_dose_doac",
        "renal_disease_affecting_bleeding",
        "liver_disease_affecting_bleeding",
        "bone_marrow_disorder",
        "other_bleeding_risk_condition",
        "bleeding_history_concern"
    ]

    # Make sure every required question was answered.
    for question_name in required_yes_no_questions:
        answer = patient_safety.get(question_name,"")
        answer = answer.strip().lower()

        if answer not in ["yes", "no"]:
            safety_reasons.append({
                "reason": "missing_safety_information",
                "missing_information": [question_name]})


    protected_contexts = []
    protected_context_names = [
        "prosthetic_metal_heart_valve",
        "coronary_stent",
        "dvt_or_pe_within_3_months",
        "anticoagulation_for_cardioversion"
    ]

    for context_name in protected_context_names:
        answer = patient_safety.get(context_name,"")

        if answer.strip().lower() == "yes":
            protected_contexts.append(context_name)

    if protected_contexts:
        safety_reasons.append({
            "reason": ("do_not_interrupt_therapy_without_specialist_instruction"),
            "clinical_contexts": protected_contexts,
            "message": ("Anticoagulant or antiplatelet therapy must not be interrupted without the required specialist instruction.")
        })

    # Initial high-dose apixaban or rivaroxaban.
    initial_high_dose = patient_safety.get("initial_high_dose_doac","")

    if initial_high_dose.strip().lower() == "yes":
        safety_reasons.append({
            "reason": "initial_high_dose_doac",
            "message": ("A non-urgent procedure likely to cause bleeding should be delayed where possible until the patient is taking the standard dose.")
        })

    # Conditions that may increase bleeding risk.
    bleeding_risk_conditions = []

    bleeding_condition_names = [
        "renal_disease_affecting_bleeding",
        "liver_disease_affecting_bleeding",
        "bone_marrow_disorder",
        "other_bleeding_risk_condition"
    ]

    for condition_name in bleeding_condition_names:
        answer = patient_safety.get( condition_name,"")
        if answer.strip().lower() == "yes":
            bleeding_risk_conditions.append(condition_name)

    if bleeding_risk_conditions:
        safety_reasons.append({
            "reason": ("additional_bleeding_risk_requires_clinician_review"),
            "clinical_contexts": (bleeding_risk_conditions),
            "message": ("Additional medical conditions may increase the patient's bleeding risk.")
        })

    # Previous bleeding problems.
    bleeding_history = patient_safety.get("bleeding_history_concern","")

    if bleeding_history.strip().lower() == "yes":
        safety_reasons.append({
            "reason": "bleeding_history_requires_review",
            "message": ("The patient reported a relevant history of prolonged or excessive bleeding.")
        })

    # missing treatment duration.
    treatment_duration = patient_safety.get("antithrombotic_treatment_duration","")
    treatment_duration = (treatment_duration.strip().lower())

    if treatment_duration not in [
        "long_term",
        "time_limited"
    ]:
        safety_reasons.append({
            "reason": "missing_safety_information",
            "missing_information": ["antithrombotic_treatment_duration"]
        })

    elif treatment_duration == "time_limited":
        safety_reasons.append({
            "reason": ("time_limited_antithrombotic_treatment"),
            "message": ("Consider delaying non-urgent invasive treatment until the time-limited medication course has finished.")
        })

    # Check for NSAIDs in the medication list.
    medications = assessed_context.get(
        "medications",
        []
    )

    nsaid_medications = []

    for medication in medications:
        medication_class = medication.get("medication_class","")

        if medication_class == "nsaid":
            nsaid_medications.append(
                medication.get("ingredient_name",medication.get( "medication_name",""))
            )

    if nsaid_medications:
        safety_reasons.append({
            "reason": ("additional_bleeding_risk_medication"),
            "medications": nsaid_medications,
            "message": ("The patient is taking an NSAID that may increase bleeding risk.")
        })

    return safety_reasons


def find_blocking_reasons(assessed_context: dict):
    blocking_reasons = []

    blocking_reasons.extend(find_patient_safety_reasons(assessed_context))
    planned_procedures = assessed_context.get("planned_procedures",[])
    clinical_assessment = assessed_context.get("clinical_assessment",{})
    procedure_assessments = clinical_assessment.get("procedure_assessments",[])
    medications = assessed_context.get("medications",[])

    # when planned procedure is not there stop
    if not planned_procedures:
        blocking_reasons.append({
            "reason": "no_planned_procedure",
            "message": "No planned dental procedure was found."
        })

    # stop when a procedure was not assessed.
    if (
        planned_procedures
        and len(planned_procedures) != len(procedure_assessments)
    ):
        blocking_reasons.append({
            "reason": "procedure_assessment_incomplete",
            "message": "Not all planned procedures were assessed."
        })

    # check every procedure assessment.
    for procedure in procedure_assessments:
        classification_status = procedure.get("classification_status","")
        bleeding_risk = procedure.get("postoperative_bleeding_risk","")

        if classification_status != "classified":
            blocking_reasons.append({
                "reason": classification_status or "procedure_not_classified",
                "procedure_name": procedure.get("procedure_name",""),
                "procedure_code": procedure.get("procedure_code",""),
                "missing_information": procedure.get("missing_information",[])
            })
            continue

        if not bleeding_risk:
            blocking_reasons.append({
                "reason": "unresolved_bleeding_risk",
                "procedure_name": procedure.get("procedure_name",""),
                "procedure_code": procedure.get("procedure_code","")
            })

    mapped_antithrombotics = []

    terminology_problem_statuses = [
        "rxnorm_code_missing_in_patient_data",
        "rxnorm_service_unavailable",
        "ingredient_not_found",
        "multiple_ingredients_require_review",
        "ingredient_not_in_sdcep_value_sets",
    ]

    # Check medication terminology results.
    for medication in medications:
        terminology_status = medication.get("terminology_status","")
        medication_class = medication.get("medication_class","")
        ingredient_name = medication.get("ingredient_name","")

        if terminology_status in terminology_problem_statuses:
            blocking_reasons.append({
                "reason": terminology_status,
                "medication_name": medication.get("medication_name","")
            })

        if (
            terminology_status == "mapped"
            and medication_class in SUPPORTED_MEDICATION_CLASSES
            and ingredient_name
        ):
            mapped_antithrombotics.append(medication)

    # stop when no anticoagulant or antiplatelet was mapped.
    if not mapped_antithrombotics:
        blocking_reasons.append({
            "reason": "antithrombotic_not_mapped",
            "message": (
                "No supported anticoagulant or antiplatelet "
                "medication was mapped."
            )
        })

    anticoagulant_medications = []
    antiplatelet_medications = []

    anticoagulant_classes = [
        "doac",
        "vitamin_k_antagonist",
        "low_molecular_weight_heparin",
        "unfractionated_heparin"
    ]

    for medication in mapped_antithrombotics:
        medication_class = medication.get(
            "medication_class",
            ""
        )

        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        if medication_class in anticoagulant_classes:
            if (
                    ingredient_name
                    not in anticoagulant_medications
            ):
                anticoagulant_medications.append(
                    ingredient_name
                )

        if medication_class == "antiplatelet":
            if (
                    ingredient_name
                    not in antiplatelet_medications
            ):
                antiplatelet_medications.append(
                    ingredient_name
                )

    # Anticoagulant plus antiplatelet.
    if (
            anticoagulant_medications
            and antiplatelet_medications
    ):
        blocking_reasons.append({
            "reason": (
                "anticoagulant_antiplatelet_"
                "combination"
            ),
            "message": (
                "Anticoagulant and antiplatelet "
                "combination therapy requires review "
                "with the prescribing clinician."
            )
        })

    # Two or more antiplatelet medications.
    if len(antiplatelet_medications) > 1:
        blocking_reasons.append({
            "reason": "dual_antiplatelet_therapy",
            "message": (
                "The specific dual-antiplatelet workflow "
                "must be used before treatment advice "
                "is generated."
            )
        })

    # Two or more anticoagulants.
    if len(anticoagulant_medications) > 1:
        blocking_reasons.append({
            "reason": "multiple_anticoagulants",
            "message": (
                "Multiple anticoagulant medications "
                "require clinician review."
            )
        })

    # For now, only allow the completed DOAC workflow.
    for medication in mapped_antithrombotics:
        medication_class = medication.get(
            "medication_class",
            ""
        )

        if medication_class != "doac":
            blocking_reasons.append({
                "reason": "therapy_workflow_not_implemented",
                "medication_class": medication_class,
                "message": (
                    "The exact workflow for this medication "
                    "class has not been implemented."
                )
            })

    # Rivaroxaban and edoxaban need dose-time information
    # for higher-risk procedures.
    medication_context = clinical_assessment.get(
        "medication_context",
        {}
    )

    usual_dose_time = medication_context.get(
        "usual_dose_time",
        ""
    )

    has_higher_risk_procedure = False

    for procedure in procedure_assessments:
        if (
            procedure.get("classification_status") == "classified"
            and procedure.get(
                "postoperative_bleeding_risk"
            ) == "higher"
        ):
            has_higher_risk_procedure = True

    for medication in mapped_antithrombotics:
        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        if (
            ingredient_name in ["rivaroxaban", "edoxaban"]
            and has_higher_risk_procedure
        ):
            if not usual_dose_time:
                blocking_reasons.append({
                    "reason": "usual_dose_time_required",
                    "message": (
                        "The usual medication dose time is "
                        "required for this DOAC."
                    )
                })

            elif usual_dose_time != "morning":
                blocking_reasons.append({
                    "reason": "evening_dose_workflow_not_implemented",
                    "message": (
                        "The evening-dose workflow must be "
                        "implemented before generating a recommendation."
                    )
                })

    for medication in medications:
        status = medication.get("status", "")

        if status != "active":
            blocking_reasons.append({
                "reason": "medication_status_requires_review",
                "medication_name": medication.get(
                    "medication_name",
                    ""
                ),
                "status": status,
                "message": (
                    "The medication is not recorded as active."
                )
            })

    for procedure in planned_procedures:
        status = procedure.get("status", "")

        if status != "active":
            blocking_reasons.append({
                "reason": "procedure_status_requires_review",
                "procedure_name": procedure.get(
                    "procedure_name",
                    ""
                ),
                "status": status,
                "message": (
                    "The planned procedure is not recorded as active."
                )
            })

    return blocking_reasons

def build_metadata_filters(assessed_context: dict):
    clinical_assessment = assessed_context.get("clinical_assessment",{})
    procedure_assessments = clinical_assessment.get("procedure_assessments",[])
    medications = assessed_context.get("medications",[])

    metadata_filters = []
    added_combinations = []

    for medication in medications:
        medication_class = medication.get("medication_class","")
        ingredient_name = medication.get("ingredient_name","")
        terminology_status = medication.get("terminology_status","")

        if terminology_status != "mapped":
            continue

        if not medication_class or not ingredient_name:
            continue

        ingredient_name = normalize_value(ingredient_name)

        for procedure in procedure_assessments:
            bleeding_risk = procedure.get("postoperative_bleeding_risk","")

            combination = (
                medication_class,
                ingredient_name,
                bleeding_risk
            )

            if combination in added_combinations:
                continue

            added_combinations.append(combination)

            metadata_filter = {
                "$and": [
                    {
                        "record_type": {
                            "$eq": "clinical_recommendation"
                        }
                    },
                    {
                        "medication_classes": {
                            "$ilike": f'%"{medication_class}"%'
                        }
                    },
                    {
                        "medications": {
                            "$ilike": f'%"{ingredient_name}"%'
                        }
                    },
                    {
                        "postoperative_bleeding_risk": {
                            "$eq": bleeding_risk
                        }
                    }
                ]
            }

            metadata_filters.append(
                metadata_filter
            )

    if not metadata_filters:
        return None

    return metadata_filters

def document_matches_patient_context(document,assessed_context: dict):
    metadata = document.metadata

    if metadata.get("record_type") != "clinical_recommendation":
        return False

    document_medication_classes = metadata.get("medication_classes",[])
    document_medications = metadata.get("medications",[])
    document_bleeding_risk = metadata.get("postoperative_bleeding_risk","")

    if isinstance(document_medication_classes, str):
        document_medication_classes = [document_medication_classes]

    if isinstance(document_medications, str):
        document_medications = [document_medications]

    normalized_document_classes = []

    for medication_class in document_medication_classes:
        normalized_document_classes.append(
            normalize_value(medication_class)
        )

    normalized_document_medications = []

    for medication_name in document_medications:
        normalized_document_medications.append(
            normalize_value(medication_name)
        )

    medications = assessed_context.get("medications",[])

    procedure_assessments = (
        assessed_context
        .get("clinical_assessment", {})
        .get("procedure_assessments", [])
    )

    for medication in medications:
        if medication.get("terminology_status") != "mapped":
            continue

        medication_class = normalize_value(
            medication.get("medication_class", "")
        )

        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        for procedure in procedure_assessments:
            bleeding_risk = procedure.get(
                "postoperative_bleeding_risk",
                ""
            )

            if (
                medication_class in normalized_document_classes
                and ingredient_name in normalized_document_medications
                and bleeding_risk == document_bleeding_risk
            ):
                return True

    return False


def retrieve_filtered_guidelines(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = "",
    usual_dose_time: str = "",
    safety_context=None
):
    if safety_context is None:
        safety_context = {}

    assessed_context = assess_patient_context(
        patient_id=patient_id,
        extraction_complexity=extraction_complexity,
        wound_size=wound_size,
        usual_dose_time=usual_dose_time,
        safety_context = safety_context
    )

    blocking_reasons = find_blocking_reasons(
        assessed_context
    )

    # Stop before accessing the vector store.
    if blocking_reasons:
        return {
            "status": "needs_clinician_confirmation",
            "patient_context": assessed_context,
            "blocking_reasons": blocking_reasons,
            "metadata_filters": None,
            "documents": []
        }

    metadata_filters = build_metadata_filters(
        assessed_context
    )

    if metadata_filters is None:
        return {
            "status": "needs_clinician_confirmation",
            "patient_context": assessed_context,
            "blocking_reasons": [{
                "reason": "metadata_filter_not_created",
                "message": (
                    "A safe guideline filter could not be created."
                )
            }],
            "metadata_filters": None,
            "documents": []
        }

    vector_store = get_vector_store()

    documents = []
    added_chunk_ids = []

    for metadata_filter in metadata_filters:
        retrieved_documents = vector_store.similarity_search(
            query=question,
            k=5,
            filter=metadata_filter
        )

        for document in retrieved_documents:
            if not document_matches_patient_context(
                document,
                assessed_context
            ):
                continue

            chunk_id = document.metadata.get(
                "chunk_id",
                ""
            )

            if chunk_id in added_chunk_ids:
                continue

            added_chunk_ids.append(chunk_id)
            documents.append(document)

    if not documents:
        return {
            "status": "no_matching_recommendation",
            "patient_context": assessed_context,
            "blocking_reasons": [{
                "reason": "no_matching_recommendation",
                "message": (
                    "No exact guideline recommendation matched "
                    "the medication and procedure bleeding risk."
                )
            }],
            "metadata_filters": metadata_filters,
            "documents": []
        }

    return {
        "status": "retrieved",
        "patient_context": assessed_context,
        "blocking_reasons": [],
        "metadata_filters": metadata_filters,
        "documents": documents
    }


def preview_retrieval():
    patient_id = "1256"

    question = "How should this patient's rivaroxaban be managed for the planned periodontal surgery?"

    result = retrieve_filtered_guidelines(
        patient_id=patient_id,
        question=question,
        usual_dose_time="morning"
    )

    print("Status:")
    print(result["status"])
    print()

    print("Blocking reasons:")
    pprint.pprint(
        result.get("blocking_reasons", [])
    )
    print()

    print("Metadata filter:")
    pprint.pprint(result["metadata_filters"])
    print()

    print("Retrieved guideline documents:")
    print()

    for document in result["documents"]:
        print("Metadata:")
        pprint.pprint(document.metadata)
        print()

        print("Content:")
        print(document.page_content)
        print()

        print("--" * 40)


if __name__ == "__main__":
    preview_retrieval()