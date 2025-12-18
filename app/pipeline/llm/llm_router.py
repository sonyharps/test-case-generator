from .client_ollama import OllamaClient

def get_llm_client(model="llama3.1:8b"):
    return OllamaClient(model=model)
