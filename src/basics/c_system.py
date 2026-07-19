from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def run(prompt_text: str):
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    system_message = SystemMessage(content="You are a helpful dental expert that responds to messages with three exclamation marks.")
    human_message = HumanMessage(content=prompt_text)
    prompt= [system_message, human_message]
    response = model.invoke(input= prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    run(prompt_text="tell me about anticoagulant use during dental treatment")
