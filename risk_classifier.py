"""
Module 3 — Risk Classifier
Assigns Low / Medium / High based on findings from the pipeline.
"""

from dataclasses import dataclass


@dataclass
class RiskResult:
    level: str          # "Low" | "Medium" | "High"
    score: int          # raw numeric score
    reasons: list[str]  # human-readable reasons for the level
    breakdown: dict     # component-wise point breakdown


def classify_risk(analysis: dict) -> RiskResult:
    """
    Scoring rules:
      Each HIGH-severity permission    → +3
      Each MEDIUM-severity permission  → +2
      Each LOW-severity permission     → +1
      Each risky keyword found         → +1 (max +10 from keywords)
      Each data sharing pattern match  → +2
    """
    score = 0
    reasons = []
    
    breakdown = {
        "permissions": [],
        "keywords": [],
        "patterns": []
    }

    # 1. Permissions
    severity_scores = {"high": 3, "medium": 2, "low": 1}
    for perm in analysis.get("permissions_found", []):
        pts = severity_scores.get(perm["severity"], 1)
        score += pts
        item = {
            "name": perm["permission"],
            "points": pts,
            "severity": perm["severity"]
        }
        breakdown["permissions"].append(item)
        reasons.append(f"{perm['permission']} permission detected (severity: {perm['severity']})")

    # 2. Risky keywords (capped at 10 points)
    keywords = analysis.get("risky_keywords", [])
    keyword_pts_total = min(len(keywords), 10)
    
    if len(keywords) > 0:
        # Distribute the capped 10 points proportionally among found keywords
        # For simplicity, 1pt each until we hit 10.
        for i, kw in enumerate(keywords):
            pts = 1 if i < 10 else 0
            if pts > 0:
                item = {
                    "name": kw["term"],
                    "points": pts,
                    "category": kw.get("category", "General")
                }
                breakdown["keywords"].append(item)
                reasons.append(f"Risky term '{kw['term']}' found [{kw['category']}]")
        score += keyword_pts_total

    # 3. Data sharing patterns
    patterns = analysis.get("sharing_patterns", [])
    for pattern in patterns:
        pts = 2
        score += pts
        item = {
            "name": pattern,
            "points": pts
        }
        breakdown["patterns"].append(item)
        reasons.append(f"Data sharing pattern detected: \"{pattern}\"")

    # Determine level
    if score >= 10:
        level = "High"
    elif score >= 5:
        level = "Medium"
    else:
        level = "Low"

    return RiskResult(level=level, score=score, reasons=reasons, breakdown=breakdown)
