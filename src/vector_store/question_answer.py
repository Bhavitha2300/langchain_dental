from config import load_config
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from vector_store.load_vector_store import get_vector_store

load_config()

def run():
    question_string = "tell me about anticoagulants"
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    template = ChatPromptTemplate.from_messages([
        ("system", "Answer from the context below, if you cannot answer from the context, say 'I dont know'"),
        ("human", "context: {context}"),
        ("human", "question: {question}"),
    ])
    vector_store = get_vector_store()
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k":5
        }
    )
    documents = retriever.invoke(question_string)
    context_list = []
    for document in documents:
        context_list.append(document.page_content)

    prompt = template.invoke({
        "context": context_list,
        "question": question_string
    })
    response = chat_model.invoke(input=prompt)
    print(response.content)

if __name__ == "__main__":
    load_config()
    run()