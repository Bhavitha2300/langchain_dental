from config import load_config
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
markdown_file = data_dir / "dentistry.md"

_headers_to_split_on=[
    ("#", "h1"),
    ("##", "h2"),
    ("##", "h3")
]

def chunked_documents():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    markdown_text = markdown_file.read_text(encoding="utf-8")
    markdown_header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_headers_to_split_on)
    markdown_header_documents=markdown_header_splitter.split_text(markdown_text)
    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=20)
    _split_documents = recursive_splitter.split_documents(documents=markdown_header_documents)
    content_list=[]
    return _split_documents



    embeddings=embed_model.embed_documents(texts=content_list)
    print(embeddings)


if __name__ == "__main__":
    load_config()
    chunked_documents()
