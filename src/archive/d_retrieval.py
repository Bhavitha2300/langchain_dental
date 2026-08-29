from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from cdss.b_vector_store import get_vector_store
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
output_file = DATA_DIR / "Answer.md"

load_config()

def retrieve():
    question = "Patient taking aspirin needs one simple extraction"
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system","Answer from the context, if you cannot answer from the context, say 'I dont know'."),
        ("human","context:{context}"),
        ("human","question:{question}")
    ])
    vect_store = get_vector_store()

    retriever = vect_store.as_retriever(
        search_kwargs={
            "k":5
        }
    )
    documents = retriever.invoke(question)
    context_list =[]
    for document in documents:
        context_list.append(document.page_content)


    prompt = template.invoke({
        "context": context_list,
        "question": question
    })
    response = chat_model.invoke(input=prompt)
    output_file.write_text(data=response.content)
    print(response.content)

if __name__ == "__main__":
    retrieve()




# 1. SDCEP Management of Dental Patients Taking Anticoagulants or Antiplatelet Drugs [1]

# 2. ADA Oral Anticoagulant and Antiplatelet Medications and Dental Procedures [2]

# 3. CHEST Perioperative Management of Antithrombotic Therapy [17]

# 4. Venous Thromboembolism: DVT and Pulmonary Embolism

# 5. Valvular Heart Disease and Mechanical Prosthetic Valves

# 6. Acute Coronary Syndromes, PCI, and Coronary Stents

# 7. Chronic Coronary Disease

# 8. Ischemic Stroke and Transient Ischemic Attack

# 9. Peripheral Artery Disease

# 10. Atrial Fibrillation

# 11. Drug-Specific Information
## 11.1 Apixaban
## 11.2 Rivaroxaban
## 11.3 Dabigatran
## 11.4 Edoxaban
## 11.5 Warfarin
## 11.6 Aspirin
## 11.7 Clopidogrel
## 11.8 Ticagrelor
## 11.9 Prasugrel
## 11.10 Enoxaparin






