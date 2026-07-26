from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def run():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = PromptTemplate.from_template("""
    You are a professor teaching first-year dental students. Always explain concepts in simple language.
    Question: {question}
    """)
    prompt1 = template.invoke({
        "question": "what is gingivitis"
    })
    prompt2 = template.invoke({
        "question": "What causes tooth sensitivity?"
    })
    response1 = model.invoke(input=prompt1)
    response2 = model.invoke(input=prompt2)
    print(response1.content)
    print(response2.content)

if __name__ == "__main__":
    load_config()
    run()

