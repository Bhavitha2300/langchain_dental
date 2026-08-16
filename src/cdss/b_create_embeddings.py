from config import load_config
from langchain_openai import OpenAIEmbeddings
from a_split_markdown import chunks

def embed():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    documents = chunks()
    content_list = []

    for document in documents:
        content_list.append(document.page_content)
    embeddings = embed_model.embed_documents(texts=content_list)
    print(embeddings)

    return embeddings


if __name__ == "__main__":
    load_config()
    embed()
