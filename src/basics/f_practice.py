from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def practice():
    model = ChatOpenAI(model="gpt-4o-mini")
    template=ChatPromptTemplate.from_messages([
        ("system","You are a professor teaching dental students."),
        ("human","{question}")
    ])
    prompt=template.invoke({"question":"Explain the difference between gingivitis and periodontitis."})
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    practice()