from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def practice():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = PromptTemplate.from_template("""
    you are a dental assistant.
    Drug: {drug}
    Procedure: {procedure}
    should the medication be stopped before the procedure?
    """)
    prompt = template.invoke({
        "drug": "Warfarin",
        "procedure": "Tooth Extraction"
    })
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    practice()

