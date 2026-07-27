from langchain_text_splitters import MarkdownHeaderTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
markdown_file = data_dir / "dentistry.md"

_headers_to_split_on=[
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3")
]

def main():
    markdown_text = markdown_file.read_text(encoding="utf-8")
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_headers_to_split_on)
    documents=splitter.split_text(markdown_text)
    for chunk in chunks:
        chunk.metadata['source']=markdown_file.name
        print(chunk.metadata)
        print()
        print(chunk.page_content)
        print("---"*40)


if __name__ == "__main__":
    main()
