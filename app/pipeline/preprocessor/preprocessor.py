# app/pipeline/preprocessor/preprocessor.py

from .normalizer import normalize
from .extractor import extract
from .classifier import classify


def preprocess(requirement: str) -> dict:
    """
    Preprocessing enterprise:
    - normalize text (bersihin noise)
    - extract entities (fields, actions)
    - classify domain (login, payment, crud, dll)

    Output DIJAMIN uniform & tidak berubah-ubah.
    """

    clean = normalize(requirement or "")
    entities = extract(clean)
    domain = classify(clean)

    return {
        "clean_requirement": clean,
        "entities": entities,    # ALWAYS list
        "domain": domain,        # ALWAYS string
    }


def preprocess_requirement(requirement: str) -> dict:
    """
    Wrapper agar backward compatible dengan orchestrator lama.
    """
    return preprocess(requirement)
