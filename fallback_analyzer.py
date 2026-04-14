"""
Fallback Analyzer — Keyword-based (no AI required)
Used automatically when Gemini API quota is exhausted.
"""

import re


# ── Sensitive Permissions ──────────────────────────────────────────
SENSITIVE_PERMISSIONS = [
    {"name": "Location",          "keywords": ["location", "gps", "geolocation", "precise location", "coarse location"], "severity": "high"},
    {"name": "Camera",            "keywords": ["camera", "photo", "video capture", "take pictures"],                      "severity": "high"},
    {"name": "Microphone",        "keywords": ["microphone", "audio recording", "record audio", "voice", "mic"],          "severity": "high"},
    {"name": "Contacts",          "keywords": ["contacts", "address book", "phonebook", "read contacts"],                  "severity": "high"},
    {"name": "Storage",           "keywords": ["read external storage", "write external storage", "storage access"],       "severity": "medium"},
    {"name": "Phone/SMS",         "keywords": ["call logs", "read sms", "send sms", "read phone state", "imei"],          "severity": "high"},
    {"name": "Calendar",          "keywords": ["calendar", "read calendar", "write calendar"],                             "severity": "medium"},
    {"name": "Biometric/Device",  "keywords": ["fingerprint", "face recognition", "biometric", "device id", "advertising id"], "severity": "high"},
    {"name": "Network/Bluetooth", "keywords": ["bluetooth", "nearby devices", "wifi", "network state"],                   "severity": "low"},
]

RISKY_KEYWORDS = [
    {"term": "collect",        "category": "Data Collection"},
    {"term": "we collect",     "category": "Data Collection"},
    {"term": "gather",         "category": "Data Collection"},
    {"term": "track",          "category": "Tracking"},
    {"term": "tracking",       "category": "Tracking"},
    {"term": "monitor",        "category": "Tracking"},
    {"term": "surveillance",   "category": "Surveillance"},
    {"term": "share",          "category": "Data Sharing"},
    {"term": "sell",           "category": "Data Selling"},
    {"term": "third party",    "category": "Third-Party Sharing"},
    {"term": "third-party",    "category": "Third-Party Sharing"},
    {"term": "advertiser",     "category": "Advertising"},
    {"term": "advertising",    "category": "Advertising"},
    {"term": "targeted ads",   "category": "Advertising"},
    {"term": "retain",         "category": "Data Retention"},
    {"term": "indefinitely",   "category": "Data Retention"},
    {"term": "profiling",      "category": "User Profiling"},
    {"term": "behavioral",     "category": "User Profiling"},
]

DATA_SHARING_PATTERNS = [
    r"we (may |will |can )?(collect|gather|obtain|receive) (your |personal |user )?data",
    r"(share|disclose|sell|transfer) (your |personal |user )?(data|information) (with|to)",
    r"third[- ]part(y|ies) (may |will |can )?(access|receive|use)",
    r"(use|process) (your |personal )?(data|information) for (advertising|marketing|profiling)",
    r"(retain|store|keep) (your |personal )?(data|information) (for|indefinitely)",
    r"track(ing)? (your )?(activity|behavior|location|usage)",
]


def analyze_with_keywords(content: str) -> dict:
    """
    Keyword-based privacy risk analysis. No AI required.
    Returns the same dict shape as analyze_with_gemini().
    """
    text = content.lower()
    words = content.split()
    word_count = len(words)

    # ── Detect permissions ─────────────────────────────────────────
    permissions_found = []
    for perm in SENSITIVE_PERMISSIONS:
        for kw in perm["keywords"]:
            if kw in text:
                permissions_found.append({
                    "permission": perm["name"],
                    "severity": perm["severity"],
                    "matched_term": kw,
                    "reason": f"Text contains '{kw}' which indicates {perm['name']} access.",
                })
                break

    # ── Detect risky keywords ──────────────────────────────────────
    risky_keywords = []
    for item in RISKY_KEYWORDS:
        pattern = rf"\b{re.escape(item['term'])}\b"
        matches = list(re.finditer(pattern, text))
        if matches:
            m = matches[0]
            start = max(0, m.start() - 50)
            end = min(len(content), m.end() + 50)
            context = content[start:end].replace("\n", " ").strip()
            risky_keywords.append({
                "term": item["term"],
                "category": item["category"],
                "count": len(matches),
                "context": f"...{context}...",
            })

    # ── Detect sharing patterns ────────────────────────────────────
    sharing_patterns = []
    for pat in DATA_SHARING_PATTERNS:
        if re.search(pat, text):
            sharing_patterns.append(pat)

    # ── Score & classify ───────────────────────────────────────────
    severity_scores = {"high": 3, "medium": 2, "low": 1}
    score = 0
    for p in permissions_found:
        score += severity_scores.get(p["severity"], 1)
    score += min(len(risky_keywords), 10)
    score += len(sharing_patterns) * 2

    if score >= 10:
        risk_level = "High"
    elif score >= 5:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # ── Build summary & recommendations ───────────────────────────
    perm_names = [p["permission"] for p in permissions_found]
    summary = (
        f"Keyword analysis detected {len(permissions_found)} sensitive permission(s) "
        f"({', '.join(perm_names) if perm_names else 'none'}), "
        f"{len(risky_keywords)} risky keyword(s), and "
        f"{len(sharing_patterns)} data-sharing pattern(s). "
        f"Risk score: {score}."
    )

    recs = {
        "Low":    ["App appears to have low privacy risk based on keyword analysis.",
                   "Still review the full privacy policy manually before installing.",
                   "Check if the app requests unnecessary permissions at runtime."],
        "Medium": ["This app has moderate privacy concerns — proceed with caution.",
                   f"Review permissions related to: {', '.join(perm_names) or 'none specifically flagged'}.",
                   "Consider denying non-essential permissions when the app requests them.",
                   "Read the full Terms & Conditions before accepting."],
        "High":   ["⚠️ HIGH RISK: This app has significant privacy red flags.",
                   "Multiple sensitive permissions and risky data practices detected.",
                   "Avoid installing unless the app is from a fully trusted source.",
                   "If already installed, revoke sensitive permissions in device settings."],
    }

    explanation = (
        f"This analysis was performed using keyword matching (AI fallback mode). "
        f"The text was scanned for {len(SENSITIVE_PERMISSIONS)} permission categories and "
        f"{len(RISKY_KEYWORDS)} risky privacy terms. "
        f"A total risk score of {score} was computed, placing this content in the '{risk_level}' category."
    )

    return {
        "source": "keyword_fallback",
        "word_count": word_count,
        "sentences_analyzed": content.count(".") + content.count("!") + content.count("?"),
        "permissions_found": permissions_found,
        "risky_keywords": risky_keywords,
        "sharing_patterns": sharing_patterns,
        "ai_risk_level": risk_level,
        "ai_risk_score": score,
        "ai_summary": summary,
        "ai_key_issues": [f"{p['permission']}: {p['reason']}" for p in permissions_found],
        "ai_recommendations": recs[risk_level],
        "ai_explanation": explanation,
    }
