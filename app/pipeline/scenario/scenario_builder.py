# app/pipeline/scenario/scenario_builder.py
from app.pipeline.preprocessor.preprocessor import preprocess
from .scenario_templates import AUTH_TEMPLATES, PAYMENT_TEMPLATES, CRUD_TEMPLATES
from .scenario_steps import render_step

def build_scenario(requirement: str) -> dict:
    """Build a scenario list based on requirement analysis."""

    prep = preprocess(requirement)
    domain = prep["domain"]
    intent = prep["meta"]["intent"]

    scenario = []

    # Select template set
    if domain == "authentication":
        template = AUTH_TEMPLATES.get(intent, [])
    elif domain == "payment":
        template = PAYMENT_TEMPLATES.get(intent, [])
    elif domain == "crud":
        template = CRUD_TEMPLATES.get(intent, [])
    else:
        template = ["User starts interaction", "System processes action"]

    # Render steps
    for step in template:
        scenario.append(step)

    return {
        "domain": domain,
        "intent": intent,
        "steps": scenario
    }
