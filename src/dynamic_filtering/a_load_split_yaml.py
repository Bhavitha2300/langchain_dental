# a_load_split_yaml.py

from pathlib import Path

import yaml
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
KNOWLEDGE_BASE_FILE = DATA_DIR / "guidelines.yaml"

def normalize_value(value):
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def load_documents():

    with open(KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as file:
        knowledge_base = yaml.safe_load(file)

    documents = []

    document_id = knowledge_base.get("document_id", "")
    document_title = knowledge_base.get("title", "")
    source = knowledge_base.get("source", {})
    sections = knowledge_base.get("sections", [])

    for section in sections:
        aspect = section.get("aspect", "")
        section_title = section.get("title", "")
        subsections = section.get("subsections", [])

        for subsection in subsections:
            content = subsection.get("content", "").strip()
            if not content:
                continue

            metadata = {
                "document_id": document_id,
                "document_title": document_title,
                "source_organization": source.get("organization", ""),
                "source_edition": source.get("edition", ""),
                "source_publication_year": source.get("publication_year", ""),
                "source_isbn": source.get("isbn", ""),
                "source_website": source.get("website", ""),
                "aspect": aspect,
                "section_title": section_title,
                "subaspect": subsection.get("subaspect", ""),
                "subsection_title": subsection.get("title", ""),
                "source_section": subsection.get("source_section", ""),
                "record_type": subsection.get("record_type", "")
            }

            if subsection.get("source_table"):
                metadata["source_table"] = subsection["source_table"]

            single_value_fields = [
                "recommendation_type",
                "medication_action",
                "risk_type",
                "bleeding_likelihood",
                "postoperative_bleeding_risk",
                "recommendation_strength",
                "evidence_certainty",
                "condition_group",
                "inr_category",
                "dose_category",
                "therapy_type",
                "treatment_duration",
                "medication_context",
                "patient_bleeding_risk_factor"
            ]

            for field in single_value_fields:
                value = subsection.get(field)

                if value:
                    metadata[field] = normalize_value(value)

            list_value_fields = [
                "medications",
                "medication_classes",
                "conditions",
                "procedures",
                "clinical_contexts",
                "interacting_medications",
                "trade_names",
                "other_names",
                "alternative_names",
                "substances",
                "commonly_used_treatments",
                "commonly_used_medications",
                "combination_trade_names",
                "examples"
            ]

            for field in list_value_fields:
                values = subsection.get(field, [])

                if values:
                    normalized_values = []

                    for value in values:
                        normalized_values.append(normalize_value(value))

                    metadata[field] = normalized_values

            interactions = subsection.get("interactions", [])

            if interactions:
                interacting_drugs = []
                interaction_effects = []

                for interaction in interactions:
                    interacting_drug = interaction.get("interacting_drug", "")
                    possible_effect = interaction.get("possible_effect", "")

                    if interacting_drug:
                        interacting_drugs.append(normalize_value(interacting_drug))

                    if possible_effect:
                        interaction_effects.append(normalize_value(possible_effect))

                metadata["interacting_drugs"] = interacting_drugs
                metadata["interaction_effects"] = interaction_effects

            page_content = f"""
    Guideline: {document_title}
    Section: {section_title}
    Subsection: {subsection.get("title", "")}

    {content}
                """.strip()

            document = Document(page_content=page_content, metadata=metadata)
            documents.append(document)

    recursive_character_text_splitter =RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    split_documents = recursive_character_text_splitter.split_documents(documents=documents)

    return split_documents


def preview_documents():
    documents = load_documents()

    print(f"Total documents: {len(documents)}")
    print()

    for document in documents:
        print("Metadata:")
        print(document.metadata)
        print()
        print("content:")
        print(document.page_content)
        print()
        print("--" * 40)


if __name__ == "__main__":
    preview_documents()