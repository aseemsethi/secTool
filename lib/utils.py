from lib.models import MODELS_MAP

def read_prompt(file_name):
    with open(file_name, 'r') as file:
        return file.read()

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def retrieve_answer(output):
    return output.content

def load_LLM(llm_name):
    # need to return ollama ref here
    return True;

def load_embeddings(llm_name):
    # need to return ollama ref here
    return True;

def get_available_models():
    # need to return ollama.list() here
    return list(MODELS_MAP.keys())

def select_model():
    models = get_available_models()
    print("Available Models:", models)
    #for item in models:
    #    print(item)
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



