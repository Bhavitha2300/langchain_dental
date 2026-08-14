from langchain_text_splitters import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
markdown_file = data_dir / "sdcep_guidelines.md"

_headers_to_split_on=[
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3"),
    ("####", "h4")
]

def chunks():
    markdown_text = markdown_file.read_text(encoding="utf-8")
    markdown_header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_headers_to_split_on)
    markdown_header_documents = markdown_header_splitter.split_text(markdown_text)
    recursive_character_text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    split_documents = recursive_character_text_splitter.split_documents(documents=markdown_header_documents)

    for chunk in split_documents:
        print(chunk.metadata)
        print()
        print(chunk.page_content)
        print()
        print("--"*30)
    return split_documents

if __name__ == "__main__":
    chunks()

