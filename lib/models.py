import os
from dotenv import load_dotenv

MODELS_MAP = {
    "deepseek-coder-v2": {
        # 8.9B
        "name":"deepseek-coder-v2",
        "embedding_name": "llama3.2"   
    },
    "llama3.2": {
        # 2B
        "name":"llama3.2",
        # embedding = "nomic-embed-text"
        "embedding_name": "llama3.2"   
    },
    "codellama": {
        "name":"codellama",
        "embedding_name": "llama3.2"   
    },
    "GitHub CoPilot": {
        "name":"copilot",
        "embedding_name": "llama3.2",
        "api_key": os.getenv("OPENAI_API_KEY")
    }
}
