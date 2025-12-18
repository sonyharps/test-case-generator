# app/pipeline/scenario/scenario_steps.py

BASE_STEPS = {
    "open_page": "User opens the {page} page.",
    "input": "User inputs {field}.",
    "click": "User clicks {button}.",
    "system_validate": "System validates {field}.",
    "system_response": "System responds with {message}."
}

def render_step(template: str, **kwargs):
    """Replace placeholders in a step template."""
    return template.format(**kwargs)
