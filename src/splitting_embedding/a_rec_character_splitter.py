from langchain_text_splitters import RecursiveCharacterTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
text_file = data_dir / "dentistry.md"

def main():
    markdown_text= text_file.read_text()
    splitter = RecursiveCharacterTextSplitter(chunk_size=300,chunk_overlap=20)
    chunks = splitter.split_text(text=markdown_text)
    print(chunks)

if __name__ == "__main__":
    main()

