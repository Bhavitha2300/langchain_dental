from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

def run():
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    template = PromptTemplate.from_template(
        """
        Answer the question from the context below, if question cannot be answered say context is not present.
        Context: {context}
        
        Question: {question}
        
        Answer:
        """
    )
    prompt = template.invoke({
        "context": """
        Oral anticoagulant and antiplatelet agents are prescribed for individuals who are at high risk for or who have had thromboembolic events (e.g., blood clots).  These include patients who have experienced deep-vein thrombosis (DVT) or pulmonary embolism (PE) or who have nonvalvular atrial fibrillation (NVAF), a cardiac arrhythmia that predisposes patients to clot formation.  Oral anticoagulants include the vitamin K antagonist warfarin (Coumadin®) and the newer direct-acting agents, including the direct thrombin inhibitor dabigatran (Pradaxa®) and the factor Xa inhibitors apixaban (Eliquis®), rivaroxaban (Xarelto®), and edoxaban (Savaysa® [Lixiana® in the European Union, Japan, and others]).1-6 Oral antiplatelet agents include clopidogrel (Plavix®), ticlopidine (Ticlid®), prasugrel (Effient®), ticagrelor (Brilinta®), and/or aspirin.7  Adverse effects associated with these drugs can include prolonged bleeding or bruising.

Without the anticoagulant/antiplatelet medications, these patients are at higher risk for blood clot development, which could result in thromboembolism, stroke, or myocardial infarction (MI). The serious risks of stopping or reducing these medication regimens need to be balanced against the potential consequences of prolonged bleeding,8-12 which can be controlled with local measures such as mechanical pressure, hemostatic agents (e.g., Gelfoam® or Surgicel®), suturing, and/or antifibrinolytics, such as tranexamic acid.13-20 The following sections review the evidence on management of patients taking these drugs and undergoing dental procedures.
        """,
        "question": "tell me more about anticoagulant use during dental treatment"
    })
    response = model.invoke(input=prompt)
    print(response.content)



if __name__ == "__main__":
    load_config()
    run()