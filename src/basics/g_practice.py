from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_config()

def run():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate([
        ("system", "Answer only from the context given, if question cannot be answered from the context then say 'I don't know'."),
        ("human", "context: {context}"),
        ("human", "question: {question}")
    ])
    chain = template | model
    response = chain.invoke({
        "context": "Anticoagulants are a family of medications that stop your blood from clotting too easily. They can break down existing clots or prevent clots from forming in the first place. These medications can help stop life-threatening conditions like strokes, heart attacks and pulmonary embolisms, all of which can happen because of blood clots.",
        "question": "Should anticoagulants stopped during an extraction?"
    })
    print(response.content)

if __name__ == "__main__":
    run()