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
    antiplatelet_ingredients = []
    has_anticoagulant = False
    has_antiplatelet = False
    for medication in medications:
        if medication.get("terminology_status", "") != "mapped":
            continue
        medication_class = medication.get("medication_class", "")
        ingredient_name = normalize_value(medication.get("ingredient_name", ""))
        if medication_class in ["doac", "vitamin_k_antagonist", "low_molecular_weight_heparin", "unfractionated_heparin"]:
            has_anticoagulant = True
        if medication_class == "antiplatelet":
            has_antiplatelet = True
            if ingredient_name not in antiplatelet_ingredients:
                antiplatelet_ingredients.append(ingredient_name)
    clinical_assessment = assessed_context.get("clinical_assessment", {})
    patient_safety = clinical_assessment.get("patient_safety", {})
    if patient_safety.get("additional_bleeding_risk_condition", "") == "yes":
        add_subaspect(selected_subaspects, "assess_medical_conditions")
        add_subaspect(selected_subaspects, "additional_medical_or_medication_risk")
    if patient_safety.get("bleeding_history_concern", "") == "yes":
        add_subaspect(selected_subaspects, "assess_bleeding_history")
    if patient_safety.get("therapy_must_not_be_interrupted", "") == "yes":
        add_subaspect(selected_subaspects,"therapy_that_should_not_be_interrupted")
    if has_anticoagulant and has_antiplatelet:
        add_subaspect( selected_subaspects,"dental_treatment_with_combination_therapy")
        return selected_subaspects
    inr_value = patient_safety.get("inr_value", "")
    usual_dose_time = patient_safety.get("usual_dose_time", "")
    therapy_must_not_be_interrupted = patient_safety.get("therapy_must_not_be_interrupted","")
    initial_high_dose_doac = patient_safety.get("initial_high_dose_doac", "")
    if initial_high_dose_doac == "yes":
        add_subaspect(selected_subaspects, "acute_dvt_or_pe_high_dose_doac")
    urgent_dental_procedure = patient_safety.get("urgent_dental_procedure","")
    morning_doac_dose_already_taken = patient_safety.get("morning_doac_dose_already_taken","")
    treatment_duration = patient_safety.get("antithrombotic_treatment_duration","")
    if (treatment_duration == "time_limited" and urgent_dental_procedure != "yes"):
        add_subaspect(selected_subaspects,"time_limited_antithrombotic_treatment")
    lmwh_dose_category = patient_safety.get("lmwh_dose_category", "")
    heparin_during_kidney_dialysis = patient_safety.get("heparin_during_kidney_dialysis","")
    for medication in medications:
        if medication.get("terminology_status", "") != "mapped":
            continue
        medication_class = medication.get("medication_class", "")
        ingredient_name = normalize_value(medication.get("ingredient_name", ""))
        for bleeding_risk in bleeding_risks:
            if medication_class == "doac":
                if initial_high_dose_doac == "yes":
                    continue
                if bleeding_risk == "low":
                    add_subaspect(selected_subaspects,"doac_low_risk_procedure")
                elif bleeding_risk == "higher":
                    if (urgent_dental_procedure == "yes" and morning_doac_dose_already_taken == "yes"):
                        add_subaspect(selected_subaspects,"urgent_higher_risk_procedure_after_morning_doac")
                    elif therapy_must_not_be_interrupted != "yes":
                        if ingredient_name in ["apixaban", "dabigatran"]:
                            add_subaspect(selected_subaspects,"doac_higher_risk_apixaban_dabigatran")
                            add_subaspect(selected_subaspects,"restart_apixaban_or_dabigatran")
                            add_subaspect(selected_subaspects,"bleeding_around_doac_restart")
                        elif ingredient_name in ["rivaroxaban", "edoxaban"]:
                            if usual_dose_time == "morning":
                                add_subaspect(selected_subaspects, "doac_higher_risk_rivaroxaban_edoxaban_morning")
                            elif usual_dose_time == "evening":
                                add_subaspect(selected_subaspects,"doac_higher_risk_rivaroxaban_edoxaban_evening")
                            add_subaspect(selected_subaspects,"restart_rivaroxaban_or_edoxaban")
                            add_subaspect(selected_subaspects,"bleeding_around_doac_restart")
            elif medication_class == "vitamin_k_antagonist":
                add_subaspect(selected_subaspects, "inr_testing_before_dental_treatment")
                if inr_value != "":
                    if float(inr_value) < 4:
                        add_subaspect(selected_subaspects, "inr_below_4")
                    else:
                        add_subaspect(selected_subaspects, "inr_4_or_above")
            elif medication_class == "low_molecular_weight_heparin":
                if lmwh_dose_category == "prophylactic_low":
                    add_subaspect(selected_subaspects,"lmwh_prophylactic_dose")
                elif lmwh_dose_category in ["treatment_higher", "uncertain"]:
                    add_subaspect(selected_subaspects,"lmwh_treatment_dose_or_uncertain_dose")
                if treatment_duration == "time_limited":
                    add_subaspect( selected_subaspects,"short_term_lmwh")
                if heparin_during_kidney_dialysis == "yes":
                    add_subaspect(selected_subaspects,"kidney_dialysis_and_heparin")
            elif medication_class == "unfractionated_heparin":
                if heparin_during_kidney_dialysis == "yes":
                    add_subaspect(selected_subaspects,"kidney_dialysis_and_heparin")
            elif medication_class == "antiplatelet":
                add_subaspect(selected_subaspects, "single_or_dual_antiplatelet_therapy")
                if (len(antiplatelet_ingredients) == 1 and ingredient_name == "aspirin"):
                    add_subaspect(selected_subaspects,"aspirin_alone")
                else:
                    add_subaspect(selected_subaspects,"other_single_or_dual_antiplatelet_therapy")
    principal_outcomes = [
        "therapy_that_should_not_be_interrupted",
        "dental_treatment_with_combination_therapy",
        "time_limited_antithrombotic_treatment",
        "acute_dvt_or_pe_high_dose_doac",
        "doac_low_risk_procedure",
        "doac_higher_risk_apixaban_dabigatran",
        "doac_higher_risk_rivaroxaban_edoxaban_morning",
        "doac_higher_risk_rivaroxaban_edoxaban_evening",
        "urgent_higher_risk_procedure_after_morning_doac",
        "inr_below_4",
        "inr_4_or_above",
        "lmwh_prophylactic_dose",
        "lmwh_treatment_dose_or_uncertain_dose",
        "short_term_lmwh",
        "kidney_dialysis_and_heparin",
        "single_or_dual_antiplatelet_therapy"]
    principal_outcome_found = False
    for selected_subaspect in selected_subaspects:
        if selected_subaspect in principal_outcomes:
            principal_outcome_found = True
    if not principal_outcome_found:
        add_subaspect(selected_subaspects,"unclear_medication_or_medical_condition")
        return selected_subaspects
    if selected_subaspects and "inr_4_or_above" not in selected_subaspects:
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
    patient_id = "1306"
    assessed_context = assess_patient_context(patient_id)
    print("Selected subaspects:")
    pprint.pprint(get_recommendation_subaspects(assessed_context))
    print()
    print("Metadata filters:")
    pprint.pprint(build_metadata_filters(assessed_context))

if __name__ == "__main__":
    preview_guideline_filters()