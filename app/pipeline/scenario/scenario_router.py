# app/pipeline/scenario/scenario_router.py

def route_scenario(meta: dict) -> str:
    """Choose scenario path based on extracted metadata."""
    intent = meta.get("intent")

    if intent in ["login", "logout"]:
        return "authentication"

    if intent in ["checkout", "topup", "pay"]:
        return "payment"

    if intent in ["create", "update", "delete"]:
        return "crud"

    return "general"
