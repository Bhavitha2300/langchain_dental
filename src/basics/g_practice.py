from pathlib import Path
from langchain_text_splitters import TokenTextSplitter

data_dir = Path(__file__).resolve().parent.parent.parent/ "data"
text_file = data_dir / "dentistry.md"

def main():
    dentistry_text = text_file.read_text()
    splitter = TokenTextSplitter(chunk_size=100, chunk_overlap=50)
    split = splitter.split_text(text=dentistry_text)
    print(split)

if __name__ == "__main__":
    main()

