"""
Module 2 (Text Path) — Text Pipeline
Cleans policy text, detects permissions & risky keywords using spaCy + regex.
"""

import re
import spacy
from keyword_config import SENSITIVE_PERMISSIONS, RISKY_KEYWORDS, DATA_SHARING_PATTERNS

# Load spaCy model (small English model)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback: blank model if en_core_web_sm not installed
    # Install with: python -m spacy download en_core_web_sm
    nlp = spacy.blank("en")
    print("[WARNING] spaCy 'en_core_web_sm' not found. Using blank model (reduced accuracy).")


def run_text_pipeline(raw_text: str) -> dict:
    """
    Full text processing pipeline.
    Returns structured extraction result dict.
    """
    cleaned   = _clean_text(raw_text)
    doc       = nlp(cleaned)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    permissions_found   = _detect_permissions(cleaned)
    risky_keywords_found = _detect_risky_keywords(cleaned)
    sharing_patterns    = _detect_sharing_patterns(cleaned)

    return {
        "source":             "text",
        "word_count":         len(cleaned.split()),
        "sentences_analyzed": len(sentences),
        "permissions_found":  permissions_found,
        "risky_keywords":     risky_keywords_found,
        "sharing_patterns":   sharing_patterns,
    }


# ─── Internal helpers ──────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Strip HTML tags, normalize whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)            # remove HTML
    text = re.sub(r"[^\x00-\x7F]+", " ", text)      # remove non-ASCII
    text = re.sub(r"\s+", " ", text)                 # collapse whitespace
    return text.strip()


def _detect_permissions(text: str) -> list[dict]:
    """Scan text for sensitive permission mentions."""
    text_lower = text.lower()
    found = []
    for perm in SENSITIVE_PERMISSIONS:
        for keyword in perm["keywords"]:
            if keyword in text_lower:
                found.append({
                    "permission": perm["name"],
                    "matched_term": keyword,
                    "severity": perm["severity"],
                })
                break  # one match per permission category is enough
    return found


def _detect_risky_keywords(text: str) -> list[dict]:
    """Detect risky privacy-related keywords with surrounding context."""
    text_lower = text.lower()
    found = []
    for item in RISKY_KEYWORDS:
        pattern = rf"\b{re.escape(item['term'])}\b"
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            # Grab first occurrence context (50 chars either side)
            m = matches[0]
            start = max(0, m.start() - 50)
            end   = min(len(text), m.end() + 50)
            context = text[start:end].replace("\n", " ").strip()
            found.append({
                "term":      item["term"],
                "category":  item["category"],
                "count":     len(matches),
                "context":   f"...{context}...",
            })
    return found


def _detect_sharing_patterns(text: str) -> list[str]:
    """Match data sharing / collection sentence patterns."""
    text_lower = text.lower()
    matched = []
    for pattern in DATA_SHARING_PATTERNS:
        if re.search(pattern, text_lower):
            matched.append(pattern)
    return matched
