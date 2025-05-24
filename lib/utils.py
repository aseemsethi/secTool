from lib.models import MODELS_MAP
from langchain_ollama.llms import OllamaLLM
from langchain_ollama import OllamaEmbeddings


def read_prompt(file_name):
    with open(file_name, 'r') as file:
        return file.read()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def retrieve_answer(output):
    return output

def load_LLM(llm_name):
    model_info = MODELS_MAP[llm_name]["name"]
    llm = OllamaLLM(model=model_info)
    return llm

def load_embeddings(llm_name):
    embedding_info = MODELS_MAP[llm_name]["embedding_name"]
    print(f"Embeddings selected: ", embedding_info)
    embeddings = OllamaEmbeddings(
        model="llama3.2",
    )
    return embeddings

def get_available_models():
    # need to return ollama.list() here
    return list(MODELS_MAP.keys())

def select_model():
    models = get_available_models()
    print("Available Models:", models)
    for i, model in enumerate(models):
        print(f"{i+1}, {model}")
    
    while True:
        try:
            choice = int(input("Select a model by number: ")) - 1
            if 0 <= choice < len(models):
                return models[choice]
            else:
                print("Invalid choice")
        except ValueError:
            print("Invalid input..please enter a number ")



