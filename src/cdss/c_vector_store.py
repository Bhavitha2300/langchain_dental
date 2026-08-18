from config import load_config
from langchain_openai import OpenAIEmbeddings
from cdss.a_split_markdown import chunks, markdown_file
from langchain_postgres import PGVector
import uuid

load_config()

COLLECTION_NAME = "CDSS-SDCEP"
DB_CONNECTION = "postgresql+psycopg://langchain:langchain@localhost:6025/langchain"

def get_vector_store():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    store_vector = PGVector(
        embeddings=embed_model,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
    )
    return store_vector

def load_vector():
    vector_store = get_vector_store()
    documents = chunks()
    id_list = []
    for document in documents:
        document.metadata["chunk_id"]=f"sdcep-{uuid.uuid4()}"
        document.metadata["source"]=markdown_file.name
        id_list.append(document.metadata["chunk_id"])
    vector_store.add_documents(documents=documents, ids=id_list)
    print("Loaded vector store")
# def delete_collection():
#     vector_store = get_vector_store()
#     vector_store.delete_collection()
#     print("Deleted collection")

if __name__ == "__main__":
    load_vector()



