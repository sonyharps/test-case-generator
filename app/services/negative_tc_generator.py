from app.services.prompt_negative_builder import build_negative_prompt
from app.utils.llm_client import ollama_generate

def generate_negative_tc(requirement: str, model: str = "llama3.1:8b"):
    prompt = build_negative_prompt(requirement)
    output = ollama_generate(model=model, prompt=prompt)
    return output
