from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def practice():
    model = ChatOpenAI(model="gpt-4o-mini")
    template=ChatPromptTemplate.from_messages([
        ("system","You are a dental assistant."),
        ("human","What is plaque in dentistry?"),
        ("assistant","""
        Definition: Plaque is a soft, sticky film of bacteria that constantly forms on the teeth and along the gumline.
        Cause: It develops when bacteria in the mouth combine with food particles and saliva, especially if teeth are not brushed and flossed regularly.
        Prevention: Plaque can be prevented by brushing twice daily with fluoride toothpaste, flossing every day, limiting sugary foods, and having regular dental cleanings."""),
        ("human","What is gingivitis in dentistry?"),
        ("assistant","""
        Definition: Gingivitis is the early stage of gum disease in which the gums become inflamed.
        Cause: It is primarily caused by the buildup of dental plaque around the gumline, which irritates the gum tissue.
        Prevention: Gingivitis can be prevented by maintaining good oral hygiene, removing plaque through regular brushing and flossing, and visiting the dentist regularly for professional cleanings.
        """),
        ("human","{question}")
    ])
    prompt=template.invoke({"question":"What is calculus in dentistry?"})
    response = model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    practice()