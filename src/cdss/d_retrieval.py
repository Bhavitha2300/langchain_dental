from config import load_config, DATA_DIR
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from cdss.c_vector_store import get_vector_store
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
output_file = DATA_DIR / "Answer.md"

load_config()

def retrieve():
    question = "Patient taking aspirin needs one simple extraction"
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system","Answer from the context, if you cannot answer from the context, say 'I dont know'."),
        ("human","context:{context}"),
        ("human","question:{question}")
    ])
    vect_store = get_vector_store()

    retriever = vect_store.as_retriever(
        search_kwargs={
            "k":5
        }
    )
    documents = retriever.invoke(question)
    context_list =[]
    for document in documents:
        context_list.append(document.page_content)


    prompt = template.invoke({
        "context": context_list,
        "question": question
    })
    response = chat_model.invoke(input=prompt)
    output_file.write_text(data=response.content)
    print(response.content)

if __name__ == "__main__":
    retrieve()

