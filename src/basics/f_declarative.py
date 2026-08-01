from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


def main():
    model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "Answer from the context below, if you dont know say 'i dont know'."),
        ("human", "context: {context}"),
        ("human", "question: {question}"),
    ])
    chain= template | model
    response = chain.invoke({
        "context": """
Oral Anticoagulant and Antiplatelet Medications and Dental Procedures
Key Points
There is both a growing number of individuals prescribed anticoagulation or antiplatelet therapy, as well as medications for this purpose. There is strong evidence for the older medications (i.e., warfarin, antiplatelet agents), as well as limited evidence for the newer direct-acting oral anticoagulants medications that, for most patients, it is not necessary to alter anticoagulation or antiplatelet therapy prior to dental intervention.

Drug Class	Drug Names
Anticoagulant*	
warfarin (Coumadin®)
Antiplatelet agents*	
clopidogrel (Plavix®)
ticlopidine (Ticlid®)
prasugrel (Effient®)
ticagrelor (Brilinta®)
aspirin
Direct-acting oral anticoagulants**	
dabigatran (Pradaxa®)
rivaroxaban (Xarelto®)
apixaban (Eliquis®)
edoxaban (Savaysa® [Lixiana® in Europe, Japan, elsewhere])
* Strong evidence
** Limited evidence

Typical Patient

No need to discontinue medication; use local measures to control bleeding

Patients with Higher Risk of Bleeding

Any suggested modification to the medication regimen prior to dental surgery should be done in consultation with and on advice of the patient’s physician

Introduction
Oral anticoagulant and antiplatelet agents are prescribed for individuals who are at high risk for or who have had thromboembolic events (e.g., blood clots).  These include patients who have experienced deep-vein thrombosis (DVT) or pulmonary embolism (PE) or who have nonvalvular atrial fibrillation (NVAF), a cardiac arrhythmia that predisposes patients to clot formation.  Oral anticoagulants include the vitamin K antagonist warfarin (Coumadin®) and the newer direct-acting agents, including the direct thrombin inhibitor dabigatran (Pradaxa®) and the factor Xa inhibitors apixaban (Eliquis®), rivaroxaban (Xarelto®), and edoxaban (Savaysa® [Lixiana® in the European Union, Japan, and others]).1-6 Oral antiplatelet agents include clopidogrel (Plavix®), ticlopidine (Ticlid®), prasugrel (Effient®), ticagrelor (Brilinta®), and/or aspirin.7  Adverse effects associated with these drugs can include prolonged bleeding or bruising.
        """,
        "question": "what is anticoagulant?"
    })
    print(response.content)

if __name__ == '__main__':
    load_config()
    main()