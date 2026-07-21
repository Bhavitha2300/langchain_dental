from config import load_config, DATA_DIR
from langchain_openai import ChatOpenAI

load_config()

def run():
    model = ChatOpenAI(model="gpt-4o-mini-2024-07-18")
    response = model.invoke(input = "Tell me about anticoagulants during dental treatments")
    output_file = DATA_DIR / "output.md"
    output_file.write_text(str(response))
    print(f"Output written to {output_file}")

if __name__ == "__main__":
    run()


