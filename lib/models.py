import os
from dotenv import load_dotenv

MODELS_MAP = {
    "llama3.2": {
        "name":"llama3.2",
        # embedding = "nomic-embed-text"
        "embedding_name": "llama3.2"   
    },
    "codellama": {
        "name":"codellama",
        # embedding = "nomic-embed-text"
        "embedding_name": "llama3.2"   
    },
    "GitHub CoPilot": {
        "name":"copilot",
        # embedding = "nomic-embed-text"
        "embedding_name": "llama3.2",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
}
