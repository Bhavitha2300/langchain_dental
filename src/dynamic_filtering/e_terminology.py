# e_terminology.py

from pathlib import Path
import pprint
import requests
import yaml
from dynamic_filtering.c_fhir import get_fhir_patient_data

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VALUE_SETS_FILE = DATA_DIR / "sdcep_value_sets.yaml"

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


def load_value_sets():
    with open(VALUE_SETS_FILE, "r", encoding="utf-8") as file:
        value_sets = yaml.safe_load(file)

    return value_sets


def get_rxnorm_ingredients(rxnorm_code: str):
    url = f"{RXNORM_BASE_URL}/rxcui/{rxnorm_code}/related.json"
    response = requests.get(url,params={"tty": "IN"}, timeout=10)
    response.raise_for_status()
    rxnorm_data = response.json()

    ingredients = {}
    concept_groups = (rxnorm_data.get("relatedGroup", {}).get("conceptGroup", []))

    for concept_group in concept_groups:
        if concept_group.get("tty") != "IN":
            continue

        for concept in concept_group.get("conceptProperties",[]):
            code = concept.get("rxcui", "")
            name = concept.get("name", "")

            if code:
                ingredients[code] = name

    ingredient_list = []

    for code, name in ingredients.items():
        ingredient = {
            "code": code,
            "name": name
        }

        ingredient_list.append(ingredient)

    return ingredient_list


def find_medication_class(ingredient_code: str,value_sets: dict):
    medication_value_sets = value_sets.get("medication_value_sets",{})

    for medication_class, medications in medication_value_sets.items():
        for medication in medications:
            if medication.get("code") == ingredient_code:
                return medication_class

    return ""


def enrich_patient_context(patient_id: str):
    normalized_context = get_fhir_patient_data(patient_id)
    value_sets = load_value_sets()
    medications = normalized_context.get("medications",[])

    for medication in medications:
        rxnorm_code = medication.get("rxnorm_code","")

        if not rxnorm_code:
            medication["terminology_status"] = ("rxnorm_code_missing_in_patient_data")
            continue

        # first check whether the FHIR code is already an ingredient code in our value sets
        medication_class = find_medication_class(
            rxnorm_code,
            value_sets
        )

        if medication_class:
            medication["ingredient_name"] = (medication.get("medication_name", ""))
            medication["ingredient_rxnorm_code"] = (rxnorm_code)
            medication["medication_class"] = (medication_class)
            medication["terminology_status"] = "mapped"

            continue

        # If it is not an ingredient code then ask RxNorm for the ingredient.
        try:
            ingredients = get_rxnorm_ingredients(rxnorm_code)
        except requests.RequestException:
            medication["terminology_status"] = ("rxnorm_service_unavailable")
            continue

        if not ingredients:
            medication["terminology_status"] = ("ingredient_not_found")
            continue

        # Do not automatically choose one ingredient when a medication contains multiple ingredients.
        if len(ingredients) > 1:
            medication["ingredients"] = ingredients
            medication["terminology_status"] = ("multiple_ingredients_require_review")
            continue

        ingredient = ingredients[0]

        ingredient_code = ingredient.get("code","")
        ingredient_name = ingredient.get("name","")
        medication_class = find_medication_class(ingredient_code,value_sets)
        medication["ingredient_name"] = (ingredient_name)
        medication["ingredient_rxnorm_code"] = (ingredient_code)
        medication["medication_class"] = (medication_class)

        if medication_class:
            medication["terminology_status"] = "mapped"
        else:
            medication["terminology_status"] = ("ingredient_not_in_sdcep_value_sets")

    return normalized_context


def preview_enriched_context():
    patient_id = "1256"
    enriched_context = enrich_patient_context(patient_id)
    pprint.pprint(enriched_context)


if __name__ == "__main__":
    preview_enriched_context()