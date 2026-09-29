# b_vector_store.py

from config import load_config
from langchain_openai import OpenAIEmbeddings
from dynamic_filtering.a_load_split_guidelines import KNOWLEDGE_BASE_FILE, load_documents
from langchain_postgres import PGVector

load_config()

COLLECTION_NAME = "Yaml-CDSS-v4"
DB_CONNECTION = "postgresql+psycopg://langchain:langchain@localhost:6025/langchain"

def get_vector_store():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    store_vector = PGVector(
        embeddings=embed_model,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION
    )
    return store_vector

def load_vector():
    vector_store = get_vector_store()
    documents = load_documents()
    id_list = []
    for index, document in enumerate(documents):
        chunk_id = f"yaml-cdss-v4-{document.metadata.get('document_id', 'guideline')}-{index}"
        document.metadata["chunk_id"] = chunk_id
        document.metadata["source"]= KNOWLEDGE_BASE_FILE.name
        id_list.append(chunk_id)
    vector_store.add_documents(documents=documents, ids=id_list)
    print("Loaded vector store")

# def delete_collection():
#     vector_store = get_vector_store()
#     vector_store.delete_collection()
#     print("Deleted collection")

if __name__ == "__main__":
    load_vector()



