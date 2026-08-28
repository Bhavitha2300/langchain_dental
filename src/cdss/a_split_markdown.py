from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MARKDOWN_FILE = DATA_DIR / "guidelines.md"

_headers_to_split_on=[
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4")
]

def chunks():
    markdown_text = MARKDOWN_FILE.read_text(encoding="utf-8")
    markdown_header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_headers_to_split_on)
    markdown_header_documents = markdown_header_splitter.split_text(markdown_text)
    recursive_character_text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    split_documents = recursive_character_text_splitter.split_documents(documents=markdown_header_documents)

    return split_documents

def preview_chunks():
    split_documents = chunks()
    for chunk in split_documents:
        print(chunk.metadata)
        print()
        print(chunk.page_content)
        print()
        print("--"*30)


if __name__ == "__main__":
    preview_chunks()

