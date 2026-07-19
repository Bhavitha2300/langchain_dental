from certifi import contents

from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

load_config()

def main():
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    prompt = [
        HumanMessage(content="what is the capital of france")
        AIMessage(content="What is the capital of france")
        HumanMessage(content="What is the capital of france")
              ]
    response = model.invoke(input=prompt)
    print(response.content)
    print(response.usage_metadata)

if __name__ == "__main__":
    main()

