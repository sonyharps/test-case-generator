import json
from app.services.prompt_builder_json import build_tc_json_prompt
from app.utils.llm_client import ollama_generate

def generate_tc_json(requirement: str, model: str = "llama3.1:8b"):
    prompt = build_tc_json_prompt(requirement)
    raw_output = ollama_generate(model=model, prompt=prompt)

    # Normalize and clean JSON if needed
    cleaned = raw_output.strip()

    try:
        parsed = json.loads(cleaned)
        return parsed
    except json.JSONDecodeError:
        # fallback: try to fix minor common issues
        try:
            # Remove code fences if model returns ```json ... ```
            if "```" in cleaned:
                cleaned = cleaned.replace("```json", "").replace("```", "").strip()

            return json.loads(cleaned)
        except:
            raise ValueError(f"LLM returned invalid JSON:\n{raw_output}")
