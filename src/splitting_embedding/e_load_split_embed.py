from config import load_config
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent.parent / "data"
markdown_file = data_dir / "dentistry.md"

_headers_to_split_on=[
    ("#", "h1"),
    ("##", "h2")
]

def main():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    markdown_text = markdown_file.read_text(encoding="utf-8")
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=_headers_to_split_on)
    documents=splitter.split_text(markdown_text)
    content_list=[]
    for document in documents:
        content_list.append(document.page_content)

    embeddings=embed_model.embed_documents(texts=content_list)
    print(embeddings)


if __name__ == "__main__":
    load_config()
    main()
