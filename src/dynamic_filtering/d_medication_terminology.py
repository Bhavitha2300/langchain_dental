# d_medication_terminology.py

import requests
import yaml
import pprint
from pathlib import Path
from dynamic_filtering.c_retrieve_fhir_patient_data import get_fhir_patient_data

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VALUE_SETS_FILE = DATA_DIR / "sdcep_value_sets.yaml"

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

def load_value_sets():
    with open(VALUE_SETS_FILE, "r", encoding="utf-8") as file:
        value_sets = yaml.safe_load(file)
    return value_sets

# Using the code present in patient's Medication resource, get ingredient for that medication from RxNorm server
def get_rxnorm_ingredients(rxnorm_code: str):
    url = f"{RXNORM_BASE_URL}/rxcui/{rxnorm_code}/related.json"
    response = requests.get(url,params={"tty": "IN"})
    response.raise_for_status()
    rxnorm_data = response.json()

    ingredients = []
    concept_groups = rxnorm_data.get("relatedGroup", {}).get("conceptGroup", [])
    for concept_group in concept_groups:
        # if the concept group is not equal to Ingredient, then contiue
        if concept_group.get("tty", "") != "IN":
            continue
        for concept in concept_group.get("conceptProperties", []):
            code = concept.get("rxcui", "")
            name = concept.get("name", "")
            # continue only if code is present
            if code:
                ingredients.append({"code": code,
                                    "name": name})

    return ingredients

# For the ingredient code we got from RxNorm server, identify the medication class from the value sets
def find_medication_class_from_value_sets(ingredient_code, value_sets):
    medication_value_sets = value_sets.get("medication_value_sets", {})
    for medication_class, medications in medication_value_sets.items():
        for medication in medications:
            if medication.get("code", "") == ingredient_code:
                return medication_class

    return ""

# adding the medicaiton class, ingredient to the fhir patient data
def add_medication_class_to_fhir_patient_data(patient_id):
    fhir_patient_data =  get_fhir_patient_data(patient_id)
    value_sets = load_value_sets()

    for medication in fhir_patient_data.get("medications", []):
        rxnorm_code = medication.get("rxnorm_code", "")
        # if rxnorm code is not present in the fhir patient data then it says rxnorm_code_missing_in_patient_data
        if not rxnorm_code:
            medication["terminology_status"] = "rxnorm_code_missing_in_fhir_patient_data"
            continue
        # try contacting rxnorm for ingredient, if rxnorm fails raise rxnorm_service_unavailable error
        try:
            ingredients = get_rxnorm_ingredients(rxnorm_code)
        except requests.RequestException:
            medication["terminology_status"] = "rxnorm_service_unavailable"
            continue
        # if ingredient is not found raise this error
        if not ingredients:
            medication["terminology_status"] = "ingredient_not_found"
            continue
        # if ingredients are more then 1
        if len(ingredients) > 1:
            medication["ingredients"] = ingredients
            medication["terminology_status"] = "multiple_ingredients_require_review"
            continue

        ingredient = ingredients[0]
        ingredient_code = ingredient.get("code", "")
        ingredient_name = ingredient.get("name", "")
        medication_class = find_medication_class_from_value_sets(ingredient_code, value_sets)

        medication["ingredient_name"] = ingredient_name
        medication["ingredient_rxnorm_code"] = ingredient_code
        medication["medication_class"] = medication_class
        # if ingredient or medication present does not come under medication class present in sdcep value sets then raise this error
        if medication_class:
            medication["terminology_status"] = "mapped"
        else:
            medication["terminology_status"] = "ingredient_not_in_sdcep_value_sets"

    return fhir_patient_data

def preview_enriched_context():
    patient_id = "1256"
    added_medication_details_to_fhir = add_medication_class_to_fhir_patient_data(patient_id)
    pprint.pprint(added_medication_details_to_fhir)


if __name__ == "__main__":
    preview_enriched_context()





