from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def run():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful dental expert that responds to questions with three exclamation marks"),
        ("human", "context: {context}"),
        ("human", "question: {question}"),
    ])
    prompt = template.invoke({
        "context": "Without the anticoagulant/antiplatelet medications, these patients are at higher risk for blood clot development, which could result in thromboembolism, stroke, or myocardial infarction (MI). The serious risks of stopping or reducing these medication regimens need to be balanced against the potential consequences of prolonged bleeding,8-12 which can be controlled with local measures such as mechanical pressure, hemostatic agents (e.g., Gelfoam® or Surgicel®), suturing, and/or antifibrinolytics, such as tranexamic acid.13-20 The following sections review the evidence on management of patients taking these drugs and undergoing dental procedures.",
        "question": "tell me about Coumadin"
    })
    for item in prompt:
        for message in item[1]:
            print(message.content)

if __name__ == "__main__":
    load_config()
    run()