"""Tiny lexical search used in place of Azure AI Search / cross-encoder in DEMO_MODE."""
import re


_STOPWORDS = {"with", "and", "the", "from", "both", "mild", "severe", "moderate", "for", "his", "her", "after"}


def _tokens(text: str) -> set[str]:
    return {w[:5] for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 3 and w not in _STOPWORDS}


def overlap_score(query: str, doc: str) -> float:
    """Share of query tokens (5-char stems) found in the document."""
    q = _tokens(query)
    return len(q & _tokens(doc)) / len(q) if q else 0.0


def jaccard(a: str, b: str) -> float:
    ta, tb = set(re.findall(r"[a-z0-9]+", a.lower())), set(re.findall(r"[a-z0-9]+", b.lower()))
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0
