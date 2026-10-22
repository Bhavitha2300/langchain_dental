# m_drug_interaction_retrieval.py

from dynamic_filtering.a_load_split_guidelines import normalize_value
from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
from dynamic_filtering.l_langgraph_retrieval import retrieve_documents

def get_interaction_sections(patient_context):
    selected_sections = ["interaction_scope"]
    medication_sections = {
        "apixaban": "apixaban_interactions",
        "dabigatran": "dabigatran_interactions",
        "rivaroxaban": "rivaroxaban_interactions",
        "edoxaban": "edoxaban_interactions",
        "warfarin": "vitamin_k_antagonist_interactions",
        "phenindione": "vitamin_k_antagonist_interactions",
        "acenocoumarol": "vitamin_k_antagonist_interactions",
        "dalteparin": "lmwh_nsaid_interactions",
        "enoxaparin": "lmwh_nsaid_interactions",
        "tinzaparin": "lmwh_nsaid_interactions",
        "aspirin": "aspirin_interactions",
        "clopidogrel": "clopidogrel_interactions",
        "dipyridamole": "dipyridamole_interactions",
        "prasugrel": "prasugrel_interactions",
        "ticagrelor": "ticagrelor_interactions"}

    for medication in patient_context.get("medications", []):
        if medication.get("terminology_status", "") != "mapped":
            continue
        ingredient_name = normalize_value(medication.get("ingredient_name", ""))
        medication_class = medication.get("medication_class","")
        section = medication_sections.get(ingredient_name,"")
        if section and section not in selected_sections:
            selected_sections.append(section)
        if medication_class == "doac":
            if "macrolides_and_doacs" not in selected_sections:
                selected_sections.append("macrolides_and_doacs")
        if ingredient_name in ["apixaban", "dabigatran", "rivaroxaban", "edoxaban", "ticagrelor"]:
            section = ("carbamazepine_with_selected_antithrombotic_drugs")
            if section not in selected_sections:
                selected_sections.append(section)
        if medication_class == "vitamin_k_antagonist":
            if "antibiotics_and_inr" not in selected_sections:
                selected_sections.append("antibiotics_and_inr")
            section = "antibiotics_in_patients_taking_vka"
            if section not in selected_sections:
                selected_sections.append(section)
        if ingredient_name in ["warfarin", "acenocoumarol"]:
            section = ("miconazole_with_warfarin_or_acenocoumarol")
            if section not in selected_sections:
                selected_sections.append(section)
    return selected_sections

def retrieve_drug_interactions(patient_id,question,safety_context=None):
    if safety_context is None:
        safety_context = {}
    patient_context = assess_patient_context(patient_id)
    patient_context["clinical_assessment"]["patient_safety"] = safety_context
    medication_reviewed = safety_context.get("medical_history_and_medicines_reviewed", "")
    if medication_reviewed != "yes":
        return {"status": "needs_clinician_confirmation",
                "message": ("Complete or correct the patient's medication list before checking drug interactions."),
                "patient_context": patient_context,
                "documents": []}
    required_sections = get_interaction_sections(patient_context)
    if required_sections == ["interaction_scope"]:
        return {"status": "no_matching_interaction",
                "message": ("No supported anticoagulant or antiplatelet medication was mapped for interaction checking."),
                "patient_context": patient_context,
                "documents": []}
    metadata_filters = []
    for section in required_sections:
        record_type = "drug_interaction"
        if section == "interaction_scope":
            record_type = "background_information"
        metadata_filters.append({
            "$and": [
                {"record_type": {"$eq": record_type}},
                {"subaspect": {"$eq": section}}
            ]
        })
    retrieval_result = retrieve_documents(
        question=question,
        metadata_filters=metadata_filters,
        required_sections=required_sections
    )
    if retrieval_result["missing_sections"]:
        return {"status": "no_matching_interaction",
                "message": ("The required drug-interaction information could not be retrieved completely."),
                "patient_context": patient_context,
                "documents": []}
    return {
        "status": "retrieved",
        "message": "",
        "patient_context": patient_context,
        "documents": retrieval_result["documents"]
    }