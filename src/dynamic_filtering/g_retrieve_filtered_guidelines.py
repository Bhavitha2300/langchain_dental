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

    medications = assessed_context.get(
        "medications",
        []
    )

    initial_high_dose_relevant = False

    for medication in medications:
        medication_class = medication.get(
            "medication_class",
            ""
        )

        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        if (
                medication_class == "doac"
                and ingredient_name in [
            "apixaban",
            "rivaroxaban"
        ]
        ):
            initial_high_dose_relevant = True

    # without answering these questions the program will not recommend answer because it is not advisable to proceed without knowing answers to these questions
    required_yes_no_questions = [
        "prosthetic_metal_heart_valve",
        "coronary_stent",
        "dvt_or_pe_within_3_months",
        "anticoagulation_for_cardioversion",
        "renal_disease_affecting_bleeding",
        "liver_disease_affecting_bleeding",
        "bone_marrow_disorder",
        "other_bleeding_risk_condition",
        "bleeding_history_concern"
    ]

    if initial_high_dose_relevant:
        required_yes_no_questions.append("initial_high_dose_doac")

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
    if initial_high_dose_relevant:
        initial_high_dose = patient_safety.get("initial_high_dose_doac","")

        if initial_high_dose.strip().lower() == "yes":
            safety_reasons.append({
                "reason": "initial_high_dose_doac",
                "message": (
                    "A non-urgent procedure likely to cause bleeding should be delayed where possible until the patient is taking the standard dose."
                )
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
        "ingredient_not_in_sdcep_value_sets",
        "multiple_ingredients_require_review"
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

    # Two or more anticoagulants.
    if len(anticoagulant_medications) > 1:
        blocking_reasons.append({
            "reason": "multiple_anticoagulants",
            "message": (
                "Multiple anticoagulant medications "
                "require clinician review."
            )
        })

    # Get the medication-specific information collected
    # during patient assessment.
    medication_context = clinical_assessment.get(
        "medication_context",
        {}
    )

    mapped_medication_classes = []

    for medication in mapped_antithrombotics:
        medication_class = medication.get(
            "medication_class",
            ""
        )

        if (
                medication_class
                and medication_class
                not in mapped_medication_classes
        ):
            mapped_medication_classes.append(
                medication_class
            )

    # Check whether there is a higher-risk procedure.
    has_higher_risk_procedure = False

    for procedure in procedure_assessments:
        if (
                procedure.get("classification_status")
                == "classified"
                and procedure.get(
            "postoperative_bleeding_risk"
        ) == "higher"
        ):
            has_higher_risk_procedure = True

    # Vitamin K antagonist information.
    if "vitamin_k_antagonist" in mapped_medication_classes:
        inr_value = medication_context.get(
            "inr_value",
            ""
        )

        inr_category = medication_context.get(
            "inr_category",
            ""
        )

        inr_test_hours_ago = medication_context.get(
            "inr_test_hours_ago",
            ""
        )

        inr_is_stable = medication_context.get(
            "inr_is_stable",
            ""
        )

        if not inr_value:
            blocking_reasons.append({
                "reason": "missing_medication_information",
                "missing_information": ["inr_value"]
            })

        elif inr_category == "invalid":
            blocking_reasons.append({
                "reason": "invalid_inr_value",
                "message": (
                    "The INR value must be a valid "
                    "number greater than zero."
                )
            })

        if not inr_is_stable:
            blocking_reasons.append({
                "reason": "missing_medication_information",
                "missing_information": ["inr_is_stable"]
            })

        elif inr_is_stable not in ["yes", "no"]:
            blocking_reasons.append({
                "reason": "invalid_inr_stability",
                "message": (
                    "INR stability must be recorded "
                    "as yes or no."
                )
            })

        if not inr_test_hours_ago:
            blocking_reasons.append({
                "reason": "missing_medication_information",
                "missing_information": [
                    "inr_test_hours_ago"
                ]
            })

        else:
            try:
                inr_hours = float(
                    inr_test_hours_ago
                )

            except (ValueError, TypeError):
                blocking_reasons.append({
                    "reason": "invalid_inr_test_time",
                    "message": (
                        "The INR test time must be "
                        "recorded as a number of hours."
                    )
                })

            else:
                if inr_hours < 0:
                    blocking_reasons.append({
                        "reason": "invalid_inr_test_time"
                    })

                elif (
                        inr_is_stable == "yes"
                        and inr_hours > 72
                ):
                    blocking_reasons.append({
                        "reason": "inr_test_too_old",
                        "message": (
                            "A stable INR should have been "
                            "checked no more than 72 hours "
                            "before treatment."
                        )
                    })

                elif (
                        inr_is_stable == "no"
                        and inr_hours > 24
                ):
                    blocking_reasons.append({
                        "reason": "inr_test_too_old",
                        "message": (
                            "The INR should have been checked "
                            "no more than 24 hours before "
                            "treatment."
                        )
                    })

    # LMWH information.
    if (
            "low_molecular_weight_heparin"
            in mapped_medication_classes
    ):
        lmwh_dose_category = medication_context.get(
            "lmwh_dose_category",
            ""
        )

        allowed_lmwh_categories = [
            "prophylactic_low",
            "treatment_higher_or_uncertain"
        ]

        if not lmwh_dose_category:
            blocking_reasons.append({
                "reason": "missing_medication_information",
                "missing_information": [
                    "lmwh_dose_category"
                ]
            })

        elif (
                lmwh_dose_category
                not in allowed_lmwh_categories
        ):
            blocking_reasons.append({
                "reason": "invalid_lmwh_dose_category",
                "message": (
                    "LMWH dose category must be "
                    "prophylactic_low or "
                    "treatment_higher_or_uncertain."
                )
            })

    # Unfractionated heparin information.
    if (
            "unfractionated_heparin"
            in mapped_medication_classes
    ):
        dialysis_heparin = medication_context.get(
            "heparin_during_kidney_dialysis",
            ""
        )

        if not dialysis_heparin:
            blocking_reasons.append({
                "reason": "missing_medication_information",
                "missing_information": [
                    "heparin_during_kidney_dialysis"
                ]
            })

        elif dialysis_heparin not in ["yes", "no"]:
            blocking_reasons.append({
                "reason": "invalid_dialysis_heparin_value",
                "message": (
                    "Kidney dialysis information must "
                    "be recorded as yes or no."
                )
            })

        elif dialysis_heparin == "no":
            blocking_reasons.append({
                "reason": (
                    "unfractionated_heparin_"
                    "requires_clinician_review"
                ),
                "message": (
                    "The current guideline data only has "
                    "a specific unfractionated heparin "
                    "pathway for kidney dialysis."
                )
            })

    # DOAC dose-time information.
    usual_dose_time = medication_context.get(
        "usual_dose_time",
        ""
    )

    for medication in mapped_antithrombotics:
        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        if (
                ingredient_name in [
            "rivaroxaban",
            "edoxaban"
        ]
                and has_higher_risk_procedure
        ):
            if not usual_dose_time:
                blocking_reasons.append({
                    "reason": "usual_dose_time_required",
                    "message": (
                        "The usual medication dose time "
                        "is required for this DOAC."
                    )
                })

            elif usual_dose_time not in [
                "morning",
                "evening"
            ]:
                blocking_reasons.append({
                    "reason": "invalid_usual_dose_time",
                    "message": (
                        "The usual dose time must be "
                        "morning or evening."
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

def get_recommendation_subaspects(
    assessed_context: dict
):
    medications = assessed_context.get(
        "medications",
        []
    )

    clinical_assessment = assessed_context.get(
        "clinical_assessment",
        {}
    )

    procedure_assessments = clinical_assessment.get(
        "procedure_assessments",
        []
    )

    medication_context = clinical_assessment.get(
        "medication_context",
        {}
    )

    bleeding_risks = []

    for procedure in procedure_assessments:
        bleeding_risk = procedure.get(
            "postoperative_bleeding_risk",
            ""
        )

        if (
            bleeding_risk
            and bleeding_risk not in bleeding_risks
        ):
            bleeding_risks.append(
                bleeding_risk
            )

    selected_subaspects = []
    antiplatelet_medications = []
    treatment_can_proceed = False

    for medication in medications:
        if (
            medication.get("terminology_status")
            != "mapped"
        ):
            continue

        medication_class = medication.get(
            "medication_class",
            ""
        )

        ingredient_name = normalize_value(
            medication.get("ingredient_name", "")
        )

        if medication_class == "doac":
            for bleeding_risk in bleeding_risks:
                if bleeding_risk == "low":
                    subaspect = (
                        "doac_low_risk_procedure"
                    )

                    if (
                        subaspect
                        not in selected_subaspects
                    ):
                        selected_subaspects.append(
                            subaspect
                        )

                    treatment_can_proceed = True

                elif bleeding_risk == "higher":
                    if ingredient_name in [
                        "apixaban",
                        "dabigatran"
                    ]:
                        subaspect = (
                            "doac_higher_risk_"
                            "apixaban_dabigatran"
                        )

                        restart_subaspect = (
                            "restart_apixaban_"
                            "or_dabigatran"
                        )

                    elif ingredient_name in [
                        "rivaroxaban",
                        "edoxaban"
                    ]:
                        subaspect = (
                            "doac_higher_risk_"
                            "rivaroxaban_edoxaban"
                        )

                        restart_subaspect = (
                            "restart_rivaroxaban_"
                            "or_edoxaban"
                        )

                    else:
                        continue

                    if (
                        subaspect
                        not in selected_subaspects
                    ):
                        selected_subaspects.append(
                            subaspect
                        )

                    if (
                        restart_subaspect
                        not in selected_subaspects
                    ):
                        selected_subaspects.append(
                            restart_subaspect
                        )

                    if (
                        "bleeding_around_doac_restart"
                        not in selected_subaspects
                    ):
                        selected_subaspects.append(
                            "bleeding_around_doac_restart"
                        )

                    treatment_can_proceed = True

        elif (
            medication_class
            == "vitamin_k_antagonist"
        ):
            if (
                "inr_testing_before_dental_treatment"
                not in selected_subaspects
            ):
                selected_subaspects.append(
                    "inr_testing_before_dental_treatment"
                )

            inr_category = medication_context.get(
                "inr_category",
                ""
            )

            if inr_category == "below_4":
                selected_subaspects.append(
                    "inr_below_4"
                )

                treatment_can_proceed = True

            elif inr_category == "4_or_above":
                selected_subaspects.append(
                    "inr_4_or_above"
                )

        elif (
            medication_class
            == "low_molecular_weight_heparin"
        ):
            lmwh_dose_category = (
                medication_context.get(
                    "lmwh_dose_category",
                    ""
                )
            )

            if (
                lmwh_dose_category
                == "prophylactic_low"
            ):
                selected_subaspects.append(
                    "lmwh_prophylactic_dose"
                )

                treatment_can_proceed = True

            elif (
                lmwh_dose_category
                == "treatment_higher_or_uncertain"
            ):
                selected_subaspects.append(
                    "lmwh_treatment_dose_or_uncertain_dose"
                )

        elif (
            medication_class
            == "unfractionated_heparin"
        ):
            dialysis_heparin = (
                medication_context.get(
                    "heparin_during_kidney_dialysis",
                    ""
                )
            )

            if dialysis_heparin == "yes":
                selected_subaspects.append(
                    "kidney_dialysis_and_heparin"
                )

        elif medication_class == "antiplatelet":
            if (
                ingredient_name
                not in antiplatelet_medications
            ):
                antiplatelet_medications.append(
                    ingredient_name
                )

    if antiplatelet_medications:
        selected_subaspects.append(
            "single_or_dual_antiplatelet_therapy"
        )

        if (
            len(antiplatelet_medications) == 1
            and antiplatelet_medications[0]
            == "aspirin"
        ):
            selected_subaspects.append(
                "aspirin_alone"
            )

        else:
            selected_subaspects.append(
                "other_single_or_dual_antiplatelet_therapy"
            )

        treatment_can_proceed = True

    if treatment_can_proceed:
        supporting_subaspects = [
            "schedule_treatment",
            "atraumatic_treatment",
            "local_haemostatic_measures",
            "post_treatment_advice"
        ]

        for subaspect in supporting_subaspects:
            if (
                subaspect
                not in selected_subaspects
            ):
                selected_subaspects.append(
                    subaspect
                )

    return selected_subaspects

def build_metadata_filters(
    assessed_context: dict
):
    selected_subaspects = (
        get_recommendation_subaspects(
            assessed_context
        )
    )

    metadata_filters = []

    for subaspect in selected_subaspects:
        metadata_filter = {
            "$and": [
                {
                    "record_type": {
                        "$eq": "clinical_recommendation"
                    }
                },
                {
                    "subaspect": {
                        "$eq": subaspect
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

def document_matches_patient_context(
    document,
    assessed_context: dict
):
    metadata = document.metadata

    if (
        metadata.get("record_type")
        != "clinical_recommendation"
    ):
        return False

    selected_subaspects = (
        get_recommendation_subaspects(
            assessed_context
        )
    )

    document_subaspect = metadata.get(
        "subaspect",
        ""
    )

    if document_subaspect in selected_subaspects:
        return True

    return False


def retrieve_filtered_guidelines(
    patient_id: str,
    question: str,
    extraction_complexity: str = "",
    wound_size: str = "",
    usual_dose_time: str = "",
    inr_value="",
    inr_test_hours_ago="",
    inr_is_stable: str = "",
    lmwh_dose_category: str = "",
    heparin_during_kidney_dialysis: str = "",
    safety_context=None
):
    if safety_context is None:
        safety_context = {}

    assessed_context = assess_patient_context(
        patient_id=patient_id,
        extraction_complexity=extraction_complexity,
        wound_size=wound_size,
        usual_dose_time=usual_dose_time,
        inr_value=inr_value,
        inr_test_hours_ago=inr_test_hours_ago,
        inr_is_stable=inr_is_stable,
        lmwh_dose_category=lmwh_dose_category,
        heparin_during_kidney_dialysis=(
            heparin_during_kidney_dialysis
        ),
        safety_context=safety_context
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
            k=10,
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
                    "No guideline recommendation matched the medication-specific assessment."
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
    safety_context = {
        "prosthetic_metal_heart_valve": "no",
        "coronary_stent": "no",
        "dvt_or_pe_within_3_months": "no",
        "anticoagulation_for_cardioversion": "no",
        "initial_high_dose_doac": "no",
        "renal_disease_affecting_bleeding": "no",
        "liver_disease_affecting_bleeding": "no",
        "bone_marrow_disorder": "no",
        "other_bleeding_risk_condition": "no",
        "bleeding_history_concern": "no",
        "antithrombotic_treatment_duration": "long_term"
    }

    question = "How should this patient's rivaroxaban be managed for the planned periodontal surgery?"

    result = retrieve_filtered_guidelines(
        patient_id=patient_id,
        question=question,
        usual_dose_time="morning",
        safety_context=safety_context
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