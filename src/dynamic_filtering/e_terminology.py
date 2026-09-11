# e_terminology.py

from pathlib import Path
import pprint
import requests
import yaml
from dynamic_filtering.d_normalize_patient_context import normalize_patient_context

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
VALUE_SETS_FILE = DATA_DIR / "sdcep_value_sets.yaml"

RXNORM_BASE_URL = "https://rxnav.nlm.nih.gov/REST"


def load_value_sets():
    with open(VALUE_SETS_FILE, "r", encoding="utf-8") as file:
        value_sets = yaml.safe_load(file)

    return value_sets


def get_rxnorm_ingredient(rxnorm_code: str):
    url = f"{RXNORM_BASE_URL}/rxcui/{rxnorm_code}/related.json"
    response = requests.get(url,params={"tty": "IN"})
    response.raise_for_status()
    rxnorm_data = response.json()

    concept_groups = (rxnorm_data.get("relatedGroup", {}).get("conceptGroup", []))

    for concept_group in concept_groups:
        if concept_group.get("tty") == "IN":
            ingredients = concept_group.get("conceptProperties",[])

            if ingredients:
                ingredient = ingredients[0]
                return {
                    "code": ingredient.get("rxcui", ""),
                    "name": ingredient.get("name", "")
                }

    return {}


def find_medication_class(ingredient_code: str,value_sets: dict):
    medication_value_sets = value_sets.get("medication_value_sets",{})

    for medication_class, medications in medication_value_sets.items():
        for medication in medications:
            if medication.get("code") == ingredient_code:
                return medication_class

    return ""


def enrich_patient_context(patient_id: str):
    normalized_context = normalize_patient_context(patient_id)
    value_sets = load_value_sets()

    for medication in normalized_context.get("medications",[]):
        rxnorm_code = medication.get("rxnorm_code", "")

        if not rxnorm_code:
            medication["terminology_status"] = ("rxnorm_code_missing")
            continue

        try:
            ingredient = get_rxnorm_ingredient(rxnorm_code)
        except requests.RequestException:
            medication["terminology_status"] = ("rxnorm_service_unavailable")
            continue

        if not ingredient:
            medication["terminology_status"] = ("ingredient_not_found")
            continue

        ingredient_code = ingredient.get("code", "")
        medication_class = find_medication_class(ingredient_code,value_sets)

        medication["ingredient_name"] = ingredient.get("name","")
        medication["ingredient_rxnorm_code"] = ingredient_code
        medication["medication_class"] = medication_class

        if medication_class:
            medication["terminology_status"] = "mapped"
        else:
            medication["terminology_status"] = ("ingredient_not_in_sdcep_value_sets")

    return normalized_context


def preview_enriched_context():
    patient_id = "1000"
    enriched_context = enrich_patient_context(patient_id)
    pprint.pprint(enriched_context)


if __name__ == "__main__":
    preview_enriched_context()