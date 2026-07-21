from config import load_config, DATA_DIR
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

def run():
    model=ChatOpenAI(model="gpt-4o-mini")
    template=ChatPromptTemplate.from_messages([
    ("system", "You are a dental assistant. Answer only from the context present here, if the answer is not present in the context say 'context is not present'."),
    ("human", "Context: {context}"),
    ("human", "Question: {question}")
    ])
    prompt=template.invoke({
        "question":"what happens if nitrous oxide is given during pregnancy? Give reason too",
        "context": "Nitrous oxide is classified as a pregnancy risk group Category C medication, meaning that there is a risk of fetal harm if administered during pregnancy. It is recommended that pregnant individuals, both patients and staff, avoid exposure to nitrous oxide.18 The National Institute of Occupational Safety and Health (NIOSH), a federal agency affiliated with the Centers for Disease Control and Prevention, recommends use of a scavenging system and exposure limits of N2O concentrations in dental operations to approximately 25 ppm during analgesia administration."
    })
    response = model.invoke(input=prompt)
    output_file = DATA_DIR/ "Nitrous Oxide Pregnancy Risk.md"
    output_file.write_text(response.content)
    print(f"Output is saved in {output_file}")

if __name__ == "__main__":
    load_config()
    run()


