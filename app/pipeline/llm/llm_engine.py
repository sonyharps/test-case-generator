from .client import call_model
from .prompts import TC_PROMPT

def generate_test_cases(scenarios, model="llama3.1:8b"):
    prompt = TC_PROMPT.format(scenarios=scenarios)
    return call_model(prompt, model=model)
