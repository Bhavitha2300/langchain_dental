from langchain_text_splitters import MarkdownTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
markdown_file = data_dir / "dentistry.md"

def main():
    markdown_text = markdown_file.read_text(encoding="utf-8")
    splitter = MarkdownTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks=splitter.split_text(markdown_text)
    print(chunks)

if __name__ == "__main__":
    main()
