from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def practice():
    model = ChatOpenAI(model="gpt-4o-mini")
    template=ChatPromptTemplate.from_messages([
        ("system","You are a dental assistant."),
        ("human","{question}")
    ])
    prompt=template.invoke({"question":"A patient takes warfarin and needs scaling. Explain your reasoning before giving your recommendation."})
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    practice()