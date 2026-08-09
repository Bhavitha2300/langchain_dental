from config import load_config
from langchain_openai import OpenAIEmbeddings
from splitting_embedding.splitter import chunked_documents, markdown_file
from langchain_postgres import PGVector
import uuid

load_config()

COLLECTION_NAME = "dental"
DB_CONNECTION = "postgresql+psycopg://langchain:langchain@localhost:6025/langchain"

def get_vector_store():
    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    vect_store = PGVector(
        embeddings=embedding_model,
        connection=DB_CONNECTION,
        collection_name=COLLECTION_NAME
    )
    return vect_store

def load_vector():
    vector_store = get_vector_store()
    id_list = []
    for document in chunked_documents():
        document.metadata["chunk_id"]=f"dental-{uuid.uuid4()}"
        document.metadata["source"]=markdown_file.name
        id_list.append(document.metadata["chunk_id"])
    vector_store.add_documents(documents=chunked_documents(), ids=id_list)
    print("Loaded vector store")

def delete_collection
    vector_store = get_vector_store()
    vector_store.delete_collection()

if __name__ == "__main__":
    load_vector()
