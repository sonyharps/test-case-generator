"""
PII Redaction Service — lightweight regex-based data masking.

Scrubs common Indonesian + international PII patterns from document text BEFORE
it is sent to a cloud LLM, so sensitive internal data (account numbers, NIK,
phone, email, card numbers) never leaves the machine in cleartext.

This is a pragmatic first-line guardrail: it does not replace contractual data
handling terms with the LLM provider, but it materially reduces exposure for
the most common sensitive tokens found in PRDs / specs.
"""

import re
from typing import List, Tuple
from app.core.logging_config import get_logger

logger = get_logger(__name__)


# Each pattern: (compiled_regex, replacement_label)
# Ordered by specificity: most-structured tokens are masked first so the
# generic numeric patterns don't swallow them.
_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # Indonesian NIK / KTP (16 digits) — MUST run before generic card/account.
    (re.compile(r"\b3[0-9]{2}[0-1]\d[0-3]\d[0-9]{8}\b"), "[NIK]"),
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    # Indonesian phone numbers (+62 / 0 prefix, 8-13 significant digits) —
    # MUST run before the generic account-number rule.
    (re.compile(r"(?:\+62|0)[2-9]\d{7,12}"), "[PHONE]"),
    # IPv4 addresses — run before generic numeric patterns.
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP]"),
    # Credit card numbers (13-16 digits, optional separators)
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[CARD]"),
    # Bank account numbers (10-16 contiguous digits, common in ID banking docs)
    (re.compile(r"\b\d{10,16}\b"), "[ACCOUNT]"),
    # Generic API keys / bearer tokens (long hex / base64-ish runs, 32+ chars)
    (re.compile(r"\b(?:sk-|pk-|Bearer\s)?[A-Za-z0-9_-]{32,}\b"), "[TOKEN]"),
    # Currency amounts in IDR (Rp ... ) — masks the value, keeps currency context
    (re.compile(r"(?i)\bRp\.?\s*\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?"), "Rp[MASKED]"),
]


def redact(text: str, return_stats: bool = False):
    """Redact PII patterns from text.

    Args:
        text: Input text that may contain PII.
        return_stats: If True, also return per-label redaction counts.

    Returns:
        Redacted text, or (redacted_text, stats_dict) when return_stats is True.
    """
    if not text:
        return (text, {}) if return_stats else text

    stats = {label.rstrip("]"): 0 for _, label in _PATTERNS}
    redacted = text

    for pattern, label in _PATTERNS:
        redacted, n = pattern.subn(label, redacted)
        if n:
            stats[label.rstrip("]")] += n

    total = sum(stats.values())
    if total:
        logger.info("pii_redacted", total_tokens=total, breakdown=stats)

    return (redacted, stats) if return_stats else redacted


# Singleton-style module API
pii_redactor = type("PIIRedactor", (), {"redact": staticmethod(redact)})()
