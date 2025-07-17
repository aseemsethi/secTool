import os
from dotenv import load_dotenv

MODELS_MAP = {
    "deepseek-coder-v2": {
        # 8.9B
        "name":"deepseek-coder-v2",
        "embedding_name": "llama3.2",
        "chat": "False"   
    },
    "llama3.2 Chat with Tools": {
        "name":"llama3.2",
        "embedding_name": "llama3.2",
        "chat": "True"   
    },
    "codellama": {
        "name":"codellama",
        "embedding_name": "llama3.2",
        "chat": "False"   
    },
    "GitHub CoPilot": {
        "name":"copilot",
        "embedding_name": "llama3.2",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "chat": "False"   
    },
    "qwen2-math:latest": {
        "name":"qwen2-math:latest",
        "embedding_name": "llama3.2",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "chat": "False"   
    }
    


}
