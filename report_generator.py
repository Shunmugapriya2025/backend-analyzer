"""
Module 4 — Report Generator
Builds the final structured privacy risk report returned to the user.
"""

from risk_classifier import RiskResult


RECOMMENDATIONS = {
    "Low": [
        "This app appears to have a low privacy risk based on the analyzed content.",
        "Still review the full privacy policy manually before installing.",
        "Check if the app requests unnecessary permissions at runtime.",
    ],
    "Medium": [
        "This app has moderate privacy concerns — proceed with caution.",
        "Review permissions related to: " ,  # filled dynamically
        "Consider denying non-essential permissions when the app requests them.",
        "Read the full Terms & Conditions before accepting.",
        "Check if the app offers an opt-out for data sharing or advertising.",
    ],
    "High": [
        "⚠️  HIGH RISK: This app has significant privacy red flags.",
        "Multiple sensitive permissions and risky data practices detected.",
        "Avoid installing unless the app is from a fully trusted source.",
        "If already installed, revoke sensitive permissions in device settings.",
        "Report suspicious apps to your app store.",
    ],
}

RISK_ICONS = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}


def generate_report(analysis: dict, risk: RiskResult, input_type: str) -> dict:
    """
    Compose and return the final report dict.
    """
    recs = _build_recommendations(risk, analysis)
    total_percentage = _get_percentage(risk.score)

    report = {
        "status": "success",
        "input_type": input_type,
        "risk_level": risk.level,
        "risk_icon": RISK_ICONS[risk.level],
        "risk_score": risk.score,
        "risk_percentage": total_percentage,
        "risk_summary": calculate_risk_distribution({
            "low": sum(1 for p in analysis.get("permissions_found", []) if p["severity"].lower() == "low"),
            "medium": sum(1 for p in analysis.get("permissions_found", []) if p["severity"].lower() == "medium"),
            "high": sum(1 for p in analysis.get("permissions_found", []) if p["severity"].lower() == "high"),
        }),
        "risk_breakdown": _build_breakdown(risk.score, total_percentage, risk.breakdown),
        "summary": _build_summary(risk, analysis),
        "permissions_detected": [
            {
                "permission": p["permission"],
                "severity":   p["severity"],
                "matched_term": p["matched_term"],
            }
            for p in analysis.get("permissions_found", [])
        ],
        "risky_keywords_detected": [
            {
                "term":     kw["term"],
                "category": kw["category"],
                "count":    kw["count"],
                "context":  kw["context"],
            }
            for kw in analysis.get("risky_keywords", [])
        ],
        "data_sharing_patterns_detected": analysis.get("sharing_patterns", []),
        "key_issues": risk.reasons,
        "recommendations": recs,
        "stats": {
            "words_analyzed":         analysis.get("word_count", 0),
            "sentences_analyzed":     analysis.get("sentences_analyzed", 0),
            "permissions_count":      len(analysis.get("permissions_found", [])),
            "risky_keywords_count":   len(analysis.get("risky_keywords", [])),
            "sharing_patterns_count": len(analysis.get("sharing_patterns", [])),
        },
    }

    # Add OCR-specific fields if image input
    if input_type == "image":
        report["ocr_extracted_text_preview"] = analysis.get("ocr_text", "")
        if "ocr_warning" in analysis:
            report["ocr_warning"] = analysis["ocr_warning"]

    return report


# ─── Helpers ───────────────────────────────────────────────────────

def _get_percentage(score: int) -> int:
    """Matches the frontend non-linear mapping logic for perfection."""
    if score <= 4:
        return round((score / 4) * 33) if score > 0 else 0
    elif score <= 9:
        return round(50 + ((score - 5) / 4) * 16)
    else:
        # Score 10 is 83%, Score 15 is 100%
        pts_above_10 = min(5, score - 10)
        return round(83 + (pts_above_10 / 5) * 17)


def calculate_risk_distribution(counts: dict) -> dict:
    """
    Normalizes raw risk counts (low, medium, high) into percentages that sum exactly to 100%.
    Implements specific user logic for handling rounding, overflows, and zero-state.
    """
    low_count = counts.get("low", 0)
    medium_count = counts.get("medium", 0)
    high_count = counts.get("high", 0)

    total = low_count + medium_count + high_count

    if total == 0:
        # Default distribution for zero items
        low, medium, high = 30, 40, 30
    else:
        low = round((low_count / total) * 100)
        medium = round((medium_count / total) * 100)
        high = round((high_count / total) * 100)

    # Fix rounding overflow/underflow
    total_percentage = low + medium + high
    if total_percentage != 100:
        diff = 100 - total_percentage
        medium += diff   # adjust medium to fix rounding issue

    # Prevent multiple 100% error (exclusive 100% rule)
    if low == 100:
        medium = 0
        high = 0
    elif medium == 100:
        low = 0
        high = 0
    elif high == 100:
        low = 0
        medium = 0

    return {
        "low": low,
        "medium": medium,
        "high": high
    }


def _build_breakdown(score: int, total_pct: int, data: dict) -> dict:
    """
    Distributes the total percentage among all detected items proportionally.
    Sum of all item percentages will equal total_pct.
    """
    if score <= 0:
        return {"permissions": [], "keywords": [], "patterns": [], "totals": {"permissions": 0, "keywords": 0, "patterns": 0}}
    
    pct_per_point = total_pct / score
    
    breakdown = {
        "permissions": [],
        "keywords": [],
        "patterns": [],
        "totals": {"permissions": 0, "keywords": 0, "patterns": 0}
    }
    
    # Permissions
    for p in data.get("permissions", []):
        item_pct = round(p["points"] * pct_per_point)
        breakdown["permissions"].append({"name": p["name"], "percentage": item_pct, "severity": p["severity"]})
        breakdown["totals"]["permissions"] += item_pct

    # Keywords
    for k in data.get("keywords", []):
        item_pct = round(k["points"] * pct_per_point)
        breakdown["keywords"].append({"name": k["name"], "percentage": item_pct, "category": k["category"]})
        breakdown["totals"]["keywords"] += item_pct

    # Patterns
    for pat in data.get("patterns", []):
        item_pct = round(pat["points"] * pct_per_point)
        breakdown["patterns"].append({"name": pat["name"], "percentage": item_pct})
        breakdown["totals"]["patterns"] += item_pct

    # Adjust rounding errors to ensure sum == total_pct
    current_sum = breakdown["totals"]["permissions"] + breakdown["totals"]["keywords"] + breakdown["totals"]["patterns"]
    diff = total_pct - current_sum
    if diff != 0:
        # Just add/sub from the first permission if exists, else anywhere
        if breakdown["permissions"]: breakdown["permissions"][0]["percentage"] += diff
        elif breakdown["keywords"]: breakdown["keywords"][0]["percentage"] += diff
        
    return breakdown


def _build_summary(risk: RiskResult, analysis: dict) -> str:
    perm_count = len(analysis.get("permissions_found", []))
    kw_count   = len(analysis.get("risky_keywords", []))
    sp_count   = len(analysis.get("sharing_patterns", []))

    return (
        f"{RISK_ICONS[risk.level]} Risk Level: {risk.level.upper()} (score: {risk.score}). "
        f"Detected {perm_count} sensitive permission(s), "
        f"{kw_count} risky keyword(s), and "
        f"{sp_count} data-sharing pattern(s) in the analyzed content."
    )


def _build_recommendations(risk: RiskResult, analysis: dict) -> list[str]:
    recs = list(RECOMMENDATIONS[risk.level])

    # Inject detected permission names into medium-risk rec
    if risk.level == "Medium":
        perms = [p["permission"] for p in analysis.get("permissions_found", [])]
        recs[1] = recs[1] + (", ".join(perms) if perms else "none specifically flagged")

    return recs


# ─── AI Report Generator ───────────────────────────────────────────

def generate_report_ai(analysis: dict, input_type: str) -> dict:
    """
    Build the final report from AI analyzer output (Gemini).
    Uses the AI's provided score (0-100) and level directly as per User Template.
    """
    # 1. Gather Items
    permissions = analysis.get("permissions_found", [])
    keywords = analysis.get("risky_keywords", [])
    patterns = analysis.get("sharing_patterns", [])

    # 2. Extract AI Results
    score = analysis.get("ai_risk_score", 0)
    risk_level = analysis.get("ai_risk_level", "Low")
    
    # Ensure risk_level is capitalized correctly
    risk_level = risk_level.strip().capitalize()
    if risk_level not in ["Low", "Medium", "High"]:
        if score >= 70: risk_level = "High"
        elif score >= 40: risk_level = "Medium"
        else: risk_level = "Low"

    # 3. Build Synth Data for Breakdown UI
    # Since we use the AI score [0-100], we distribute it proportionally for the UI breakdown
    synth_data = {"permissions": [], "keywords": [], "patterns": []}
    
    total_weights = (len(permissions) * 3) + (len(keywords) * 1) + (len(patterns) * 2)
    multiplier = score / total_weights if total_weights > 0 else 0

    for p in permissions:
        sev = p.get("severity", "low").lower()
        pts = 3 if sev == "high" else (2 if sev == "medium" else 1)
        synth_data["permissions"].append({"name": p.get("permission", "Unknown"), "points": pts * multiplier, "severity": sev})
    
    for kw in keywords:
        synth_data["keywords"].append({"name": kw.get("term", "Unknown"), "points": 1 * multiplier, "category": kw.get("category", "General")})
    
    for pat in patterns:
        synth_data["patterns"].append({"name": pat, "points": 2 * multiplier})

    icon = RISK_ICONS.get(risk_level, "✅")
    total_pct = score # Direct 0-100 mapping

    report = {
        "status": "success",
        "analyzer": "Gemini AI",
        "app_name": analysis.get("app_name", ""),
        "input_type": input_type,
        "risk_level": risk_level,
        "risk_icon": icon,
        "risk_score": score,
        "risk_percentage": total_pct,
        "risk_summary": calculate_risk_distribution({
            "low": sum(1 for p in permissions if p.get("severity", "low").lower() == "low"),
            "medium": sum(1 for p in permissions if p.get("severity", "low").lower() == "medium"),
            "high": sum(1 for p in permissions if p.get("severity", "low").lower() == "high"),
        }),
        "risk_breakdown": _build_breakdown(score, total_pct, synth_data),
        "summary": analysis.get("ai_summary", ""),
        "ai_explanation": analysis.get("ai_explanation", ""),
        "permissions_detected": [
            {
                "permission": p.get("permission"),
                "severity": p.get("severity"),
                "matched_term": p.get("matched_term"),
                "risk_explanation": p.get("risk_explanation", ""), # Important for UI
                "purpose": p.get("purpose", ""),                   # Important for UI
                "recommendation": p.get("recommendation", ""),     # Important for UI
            }
            for p in permissions
        ],
        "risky_keywords_detected": [
            {
                "term": kw.get("term"),
                "category": kw.get("category"),
                "count": kw.get("count"),
                "context": kw.get("context"),
            }
            for kw in keywords
        ],
        "data_sharing_patterns_detected": patterns,
        "key_issues": analysis.get("ai_key_issues", []),
        "recommendations": analysis.get("ai_recommendations", []) or _build_recommendations_standalone(risk_level, permissions),
        "stats": {
            "words_analyzed": analysis.get("word_count", 0),
            "sentences_analyzed": analysis.get("sentences_analyzed", 0),
            "permissions_count": len(permissions),
            "risky_keywords_count": len(keywords),
            "sharing_patterns_count": len(patterns),
        },
    }

    # Add OCR text for UI display
    if input_type == "image":
        report["ocr_extracted_text_preview"] = analysis.get("ocr_text", "")

    return report


def _build_recommendations_standalone(level: str, permissions: list) -> list[str]:
    recs = list(RECOMMENDATIONS.get(level, RECOMMENDATIONS["Low"]))
    if level == "Medium":
        perms = [p.get("permission", "Unknown") for p in permissions]
        recs[1] = recs[1] + (", ".join(perms) if perms else "none specifically flagged")
    return recs
