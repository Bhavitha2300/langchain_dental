from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def run():
    model = ChatOpenAI(model="gpt-40-mini")
    template = PromptTemplate.from_template("""
    You are a dental assistant.
    Drug: {drug}
    Procedure: {procedure}
    Should the medication be stopped before the procedure? why?
    """)
    prompt = template.invoke({
        "drug": "Warfarin",
        "procedure": "Tooth extraction"
    })
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    run()

