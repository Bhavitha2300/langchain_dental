from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

load_config()

def main():
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    prompt = [
        HumanMessage(content="My name is Bhavitha"),
        AIMessage(content="Hi Bhavitha! how can i help you today"),
        HumanMessage(content="what is my age"),
        AIMessage(content="I don’t have information about your birth date, so I can’t calculate your age. However, if you share your birth year, I can help you figure it out!"),
        HumanMessage(content="I was born in 2000"),
        HumanMessage(content="what year is this"),
        AIMessage(content="The current year is 2023. If you were born in 2000, you would be 23 years old as of this year."),
        HumanMessage(content="this is 2026")
              ]
    response = model.invoke(input=prompt)
    print(response.content)
    print(response.usage_metadata)

if __name__ == "__main__":
    main()

