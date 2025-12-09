import json
from app.services.prompt_negative_builder_json import build_negative_json_prompt
from app.utils.llm_client import ollama_generate

def generate_negative_tc_json(requirement: str, model: str = "llama3.1:8b"):
    prompt = build_negative_json_prompt(requirement)
    raw_output = ollama_generate(model=model, prompt=prompt)

    cleaned = raw_output.strip()

    # Try direct JSON load
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try removing ```json ... ```
        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except:
            raise ValueError(f"Invalid JSON returned by model:\n{raw_output}")
