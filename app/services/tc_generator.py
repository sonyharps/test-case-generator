from app.services.prompt_builder import build_tc_prompt
from app.utils.llm_client import ollama_generate

def generate_tc(requirement: str, model: str = "llama3.1:8b"):
    prompt = build_tc_prompt(requirement)
    output = ollama_generate(model=model, prompt=prompt)
    return output
