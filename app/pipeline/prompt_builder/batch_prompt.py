"""
Batched Test Case Generation Prompt

Combines summary, functional, negative, and boundary test cases into a single request
to reduce API calls and improve performance.
"""

from typing import Dict, Any


def build_batched_prompt(preprocessed: Dict[str, Any], include_boundary: bool = True) -> str:
    """
    Build a single prompt that generates all test case types at once.

    This reduces 8 API calls to just 1, significantly reducing time for local LLMs.
    """
    requirement = preprocessed.get("requirement", "")
    domain = preprocessed.get("domain", "general")
    context = preprocessed.get("context", "")
    keywords = preprocessed.get("keywords", [])

    # Build keyword string
    keyword_str = ", ".join(keywords) if keywords else "various"

    # Build context string
    context_str = f"\nContext: {context}" if context else ""

    prompt = f"""You are an expert QA Test Case Designer. Generate comprehensive test cases for the following requirement.

REQUIREMENT:
{requirement}

Domain: {domain}
Keywords: {keyword_str}{context_str}

INSTRUCTIONS:
Generate a JSON response with ALL of the following sections:

1. **summary** - Object with: id (string), nama (string), deskripsi (string), prioritas (string), kategori (string)
2. **functional** - Array of 3-5 functional test cases (happy path, main flows)
3. **negative** - Array of 3-5 negative test cases (error handling, edge cases)
4. **boundary** - Array of 2-4 boundary/value limit test cases

FORMAT REQUIREMENTS:
- Return ONLY valid JSON wrapped in ```json ... ``` code blocks
- Each test case must have: tc_id, title, preconditions, steps, expected_result
- preconditions: array of strings (e.g., ["User is logged in", "Product exists"])
- steps: array of strings (e.g., ["Open login page", "Enter username", "Click login"])
- expected_result: array of strings (e.g., ["User is logged in successfully", "Dashboard appears"])
- Use prefixes: TC-F-01, TC-N-01, TC-B-01 for functional, negative, boundary

RESPONSE FORMAT EXAMPLE:
```json
{{
  "summary": {{
    "id": "REQ-001",
    "nama": "User Login Feature",
    "deskripsi": "Authentication system for user access",
    "prioritas": "high",
    "kategori": "authentication"
  }},
  "functional": [
    {{
      "tc_id": "TC-F-01",
      "title": "Successful login with valid credentials",
      "preconditions": ["User is registered", "Login page is accessible"],
      "steps": ["Navigate to login page", "Enter valid username", "Enter valid password", "Click login button"],
      "expected_result": ["User is authenticated", "Dashboard is displayed", "Success message appears"]
    }}
  ],
  "negative": [
    {{
      "tc_id": "TC-N-01",
      "title": "Login with invalid credentials",
      "preconditions": ["User is registered", "Login page is accessible"],
      "steps": ["Navigate to login page", "Enter invalid username", "Enter invalid password", "Click login button"],
      "expected_result": ["Authentication fails", "Error message displayed", "User remains on login page"]
    }}
  ],
  "boundary": [
    {{
      "tc_id": "TC-B-01",
      "title": "Login with empty fields",
      "preconditions": ["Login page is accessible"],
      "steps": ["Navigate to login page", "Leave username empty", "Leave password empty", "Click login button"],
      "expected_result": ["Validation error appears", "Login is prevented", "Error message: 'Required fields missing'"]
    }}
  ]
}}
```

IMPORTANT:
- Generate 3-5 functional test cases
- Generate 3-5 negative test cases
- Generate 2-4 boundary test cases
- Return ONLY the JSON, no additional text outside the code block
- Ensure all arrays have proper string values, not empty or null"""

    return prompt


def build_batched_prompt_simple(preprocessed: Dict[str, Any]) -> str:
    """
    Simplified batched prompt for smaller/faster models.
    """
    requirement = preprocessed.get("requirement", "")

    prompt = f"""Generate test cases for this requirement in JSON format:

REQUIREMENT: {requirement}

Return JSON with:
- summary: {{id, nama, deskripsi, prioritas, kategori}}
- functional: 3-5 test cases with tc_id, title, preconditions, steps, expected_result
- negative: 3-5 test cases (error cases) with same structure
- boundary: 2-4 test cases (limit cases) with same structure

Format: preconditions/steps/expected_result as string arrays.
Use prefixes: TC-F-XX, TC-N-XX, TC-B-XX
Return ONLY valid JSON in ```json code blocks."""

    return prompt
