from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def ask_question():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful dentist."),
        ("human", "{question}")
    ])
    while True:
        question = input("Enter your question here:")
        prompt = template.invoke({"question": question})
        response = model.invoke(input=prompt)
        print(response.content)

        again = input("Do you agree with this question? (y/n)")
        if again != "y":
            break

if __name__ == "__main__":
    load_config()
    ask_question()

