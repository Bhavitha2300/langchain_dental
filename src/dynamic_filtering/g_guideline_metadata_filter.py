# g_guideline_metadata_filter.py

from dynamic_filtering.a_load_split_guidelines import normalize_value

def add_subaspect(selected_subaspects, subaspect):
    if subaspect not in selected_subaspects:
        selected_subaspects.append(subaspect)

def get_bleeding_risks(assessed_context):
    bleeding_risks = []
    clinical_assessment = assessed_context.get("clinical_assessment", {})
    procedure_assessments = clinical_assessment.get("procedure_assessments", [])
    for procedure_assessment in procedure_assessments:
        bleeding_risk = procedure_assessment.get("postoperative_bleeding_risk", "")
        if bleeding_risk and bleeding_risk not in bleeding_risks:
            bleeding_risks.append(bleeding_risk)

    return bleeding_risks


def get_recommendation_subaspects(assessed_context):
    selected_subaspects = []
    bleeding_risks = get_bleeding_risks(assessed_context)
    medications = assessed_context.get("medications", [])
    for medication in medications:
        if medication.get("terminology_status", "") != "mapped":
            continue
        medication_class = medication.get("medication_class", "")
        ingredient_name = normalize_value(medication.get("ingredient_name", ""))
        for bleeding_risk in bleeding_risks:
            if medication_class == "doac":
                if bleeding_risk == "low":
                    add_subaspect(selected_subaspects, "doac_low_risk_procedure")
                elif bleeding_risk == "higher":
                    if ingredient_name in ["apixaban", "dabigatran"]:
                        add_subaspect(selected_subaspects, "doac_higher_risk_apixaban_dabigatran")
                        add_subaspect(selected_subaspects, "restart_apixaban_or_dabigatran")
                        add_subaspect(selected_subaspects, "bleeding_around_doac_restart")
                    elif ingredient_name in ["rivaroxaban", "edoxaban"]:
                        add_subaspect(selected_subaspects, "doac_higher_risk_rivaroxaban_edoxaban_morning")
                        add_subaspect(selected_subaspects, "restart_rivaroxaban_or_edoxaban")
                        add_subaspect(selected_subaspects, "bleeding_around_doac_restart")
            elif medication_class == "vitamin_k_antagonist":
                add_subaspect(selected_subaspects, "inr_testing_before_dental_treatment")
            elif medication_class == "low_molecular_weight_heparin":
                add_subaspect(selected_subaspects, "lmwh_prophylactic_dose")
            elif medication_class == "unfractionated_heparin":
                add_subaspect(selected_subaspects, "kidney_dialysis_and_heparin")
            elif medication_class == "antiplatelet":
                add_subaspect(selected_subaspects, "single_or_dual_antiplatelet_therapy")

    if selected_subaspects:
        add_subaspect(selected_subaspects, "schedule_treatment")
        add_subaspect(selected_subaspects, "atraumatic_treatment")
        add_subaspect(selected_subaspects, "local_haemostatic_measures")
        add_subaspect(selected_subaspects, "analgesic_advice")
        add_subaspect(selected_subaspects, "post_treatment_advice")

    return selected_subaspects


def build_metadata_filters(assessed_context):
    selected_subaspects = get_recommendation_subaspects(assessed_context)
    metadata_filters = []
    for subaspect in selected_subaspects:
        metadata_filters.append({
            "$and": [
                {"record_type": {"$eq": "clinical_recommendation"}},
                {"subaspect": {"$eq": subaspect}}
            ]
        })

    if not metadata_filters:
        return None

    return metadata_filters

def preview_guideline_filters():
    import pprint
    from dynamic_filtering.e_assess_patient_and_procedure_context import assess_patient_context
    patient_id = "1256"
    assessed_context = assess_patient_context(patient_id)
    print("Selected subaspects:")
    pprint.pprint(get_recommendation_subaspects(assessed_context))
    print()
    print("Metadata filters:")
    pprint.pprint(build_metadata_filters(assessed_context))

if __name__ == "__main__":
    preview_guideline_filters()