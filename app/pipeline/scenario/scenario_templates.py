# app/pipeline/scenario/scenario_templates.py

AUTH_TEMPLATES = {
    "login": [
        "User opens login page",
        "User enters email",
        "User enters password",
        "User clicks Login button"
    ],
    "logout": [
        "User clicks Logout",
        "System removes session",
        "Redirect user to homepage"
    ]
}

PAYMENT_TEMPLATES = {
    "checkout": [
        "User reviews cart",
        "User selects payment method",
        "User confirms checkout",
        "System processes payment"
    ],
    "topup": [
        "User opens top-up page",
        "User inputs amount",
        "User selects payment provider",
        "System verifies top-up"
    ]
}

CRUD_TEMPLATES = {
    "create": [
        "User opens create form",
        "User fills mandatory fields",
        "User clicks Submit",
        "System saves data"
    ]
}
