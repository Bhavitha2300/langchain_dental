from langchain_openai import OpenAIEmbeddings
from config import load_config
from langchain_core.documents import Document

load_config()

def main():
    embed_model = OpenAIEmbeddings(model="text-embedding-3-small")
    documents=[
        Document(
            metadata={'h1': 'Oral Anticoagulant and Antiplatelet Medications and Dental Procedures', 'h2': 'Key Points', 'source': 'dentistry.md'},
            page_content="""
            There is both a growing number of individuals prescribed anticoagulation or antiplatelet therapy, as well as medications for this purpose. There is strong evidence for the older medications (i.e., warfarin, antiplatelet agents), as well as limited evidence for the newer direct-acting oral anticoagulants medications that, for most patients, it is not necessary to alter anticoagulation or antiplatelet therapy prior to dental intervention.  
            - Anticoagulant
            - warfarin (Coumadin®)  
            - Antiplatelet agents
            * clopidogrel (Plavix®)
            * ticlopidine (Ticlid®)
            * prasugrel (Effient®)
            * ticagrelor (Brilinta®)
            * aspirin  
            - Direct-acting oral anticoagulants**
            * dabigatran (Pradaxa®)
            * rivaroxaban (Xarelto®)
            * apixaban (Eliquis®)
            * edoxaban (Savaysa® [Lixiana® in Europe, Japan, elsewhere])  
            Typical Patient- No need to discontinue medication; use local measures to control bleeding
            """
        ),
        Document(
            metadata={'h1': 'Oral Anticoagulant and Antiplatelet Medications and Dental Procedures', 'h2': 'Key Points', 'h3': 'Patients with Higher Risk of Bleeding', 'source': 'dentistry.md'},
            page_content=""""
            Any suggested modification to the medication regimen prior to dental surgery should be done in consultation with and on advice of the patient’s physician
            """
        )
    ]
    content_list=[]
    for document in documents:
        content_list.append(document.page_content)
    embeddings=embed_model.embed_documents(texts=documents)
    print(embeddings)

if __name__ == "__main__":
    main()