# a_load_split_guidelines.py

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
                "medication_action",
                "recommendation_strength",
                "evidence_certainty"
            ]
            for field in single_value_fields:
                value = subsection.get(field)
                if value:
                    metadata[field] = normalize_value(value)
            page_content = f"""
    Guideline: {document_title}
    Section: {section_title}
    Subsection: {subsection.get("title", "")}
    {content}""".strip()
            document = Document(page_content=page_content, metadata=metadata)
            documents.append(document)
    recursive_character_text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    split_documents = recursive_character_text_splitter.split_documents(documents=documents)
    chunk_counts = {}
    for document in split_documents:
        subaspect = document.metadata.get("subaspect", "")
        if subaspect not in chunk_counts:
            chunk_counts[subaspect] = 0
        chunk_counts[subaspect] = chunk_counts[subaspect] + 1
        document.metadata["subsection_chunk_number"] = chunk_counts[subaspect]
    for document in split_documents:
        subaspect = document.metadata.get("subaspect", "")
        document.metadata["subsection_chunk_count"] = chunk_counts[subaspect]

    return split_documents

def preview_documents():
    documents = load_documents()
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