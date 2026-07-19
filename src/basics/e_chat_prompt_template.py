from cofig import load_config
from langchain_openai import OpenAI
from langchain_core.prompts import ChatPromptTemplate

def run():
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "" )
    ])

load_config