from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def ask_question(question):
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful dentist."),
        ("human","My gums bleed when I brush."),
        ("assistant", "Bleeding gums may indicate gingivitis..."),
        ("human", "{question}")
    ])
    prompt = template.invoke({"question": question})
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()t
    ask_question("What is plaque?")
    ask_question("What is calculus?")
    ask_question("What is periodontitis?")

