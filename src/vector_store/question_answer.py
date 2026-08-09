from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from vector_store.load_vector_store import get_vector_store

load_config()

def run():
    question_string = "tell me about anticoagulants"
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "Answer from the context below, if you cannot answer from the context, say 'I dont know'"),
        ("human", "context: {context}"),
        ("human", "question: {question}"),
    ])
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k":5
        }
    )


    prompt = template.invoke({
        "context": "Without the anticoagulant/antiplatelet medications, these patients are at higher risk for blood clot development, which could result in thromboembolism, stroke, or myocardial infarction (MI). The serious risks of stopping or reducing these medication regimens need to be balanced against the potential consequences of prolonged bleeding,8-12 which can be controlled with local measures such as mechanical pressure, hemostatic agents (e.g., Gelfoam® or Surgicel®), suturing, and/or antifibrinolytics, such as tranexamic acid.13-20 The following sections review the evidence on management of patients taking these drugs and undergoing dental procedures.",
        "question": question_string
    })
    response = chat_model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    run()