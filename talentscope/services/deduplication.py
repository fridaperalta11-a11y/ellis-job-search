"""
Deduplication service — generates a fingerprint for each job so the same
posting from different sources is stored only once.
"""
import hashlib
import re


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation/whitespace for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def make_fingerprint(company: str, title: str, city: str) -> str:
    """SHA-1 fingerprint of normalized company + title + city."""
    raw = _normalize(company) + "|" + _normalize(title) + "|" + _normalize(city)
    return hashlib.sha1(raw.encode()).hexdigest()
