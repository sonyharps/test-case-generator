from .parser import parse_output
from .dedupe import remove_duplicates
from .validator import validate

def postprocess_llm_output(text):
    tc = parse_output(text)
    tc = remove_duplicates(tc)
    validate(tc)
    return tc
