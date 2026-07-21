from config import load_config, DATA_DIR
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def practice():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "You are a professor teaching first-year dental students. Always explain concepts in simple language."),
        ("human", "Question:{question}")
    ])
    prompt = template.invoke({
        "question": "Explain why plaque causes gingivitis."
    })
    response = model.invoke(input=prompt)
    output = DATA_DIR/"practice_output.txt"
    output.write_text(response.text)
    print(response.content)

if __name__ == "__main__":
    load_config()
    practice()

