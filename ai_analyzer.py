"""
AI Analyzer — Powered by Google Gemini
Uses Gemini API to perform deep privacy risk analysis on text or image content.
"""

import os
import json
import re
from typing import Optional, Tuple
from google import genai
from PIL import Image

_MODEL = "models/gemini-2.0-flash-lite"
_client: Optional[genai.Client] = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Check your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client

CLASSIFICATION_PROMPT = """
Analyze the request for the app "{app_name}".

STEP 1: APP NAME INTEGRITY
- Determine if "{app_name}" is a realistic app name or total garbage.

STEP 2: INTENT-BASED CONTENT CLASSIFICATION
You must differentiate between POLICY INTENT and NARRATIVE INTENT.

✅ ACCEPT (Policy Intent): 
- Language defining rules, rights, permissions, or data usage.
- Look for: "you agree", "we may", "we collect", "access to", "permission", "allow". 
- Context: "By using this service, you agree to allow camera access." -> VALID.

❌ REJECT (Narrative/Story Intent): 
- Language telling a story, describing events, or characters.
- Look for: Names (e.g. "Arjun"), past tense stories, causal actions ("opened the app", "clicked the button").
- Context: "Arjun opened the app and used the camera to take a picture." -> INVALID (Story).

CATEGORIES:
- TERMS: Legitimate Terms/Policy for "{app_name}" (Policy Intent).
- PERMISSIONS: Legitimate Permission list for "{app_name}" (Policy Intent).
- INVALID_APP: "{app_name}" is garbage (symbols/random chars).
- INVALID_CONTENT: Text is a story, random chatter, or unrelated to "{app_name}".

Return ONLY two codes (APP_CODE, CONTENT_CODE). 
Example: "VALID_APP, TERMS"

INPUT TEXT:
\"\"\"
{content}
\"\"\"
"""

ANALYSIS_PROMPT = """
You are a privacy and security expert. Analyze the following app permission text or privacy policy for the app "{app_name}".

CONTEXTUAL RISK ASSESSMENT:
1. Verify if these permissions and terms are consistent with what "{app_name}" actually does in the real world.
2. If a permission is core to "{app_name}" (e.g., Camera for Instagram Reels), mark it as Low-Medium risk with a clear purpose.
3. If a permission is unnecessary for "{app_name}" (e.g., Location for a basic Calculator), mark it as High/Critical risk.
4. If the text looks fake or radically different from the real "{app_name}" policies, flag it in the "ai_explanation".

TEXT TO ANALYZE:
\"\"\"
{content}
\"\"\"

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "risk_level": "Low" | "Medium" | "High",
  "risk_score": <integer 0-30>,
  "summary": "<one-paragraph plain-English summary of findings>",
  "permissions_detected": [
    {
      "permission": "<name>",
      "severity": "low" | "medium" | "high",
      "matched_term": "<exact term found>",
      "risk_explanation": "<detailed why it's risky e.g. 'Can reveal travel patterns'>",
      "purpose": "<why app needs this e.g. 'For reels/stories'>",
      "recommendation": "<actionable advice e.g. 'Allow only while using app'>"
    }
  ],
  "risky_keywords_detected": [
    {{"term": "<term>", "category": "<category e.g. Data Collection / Surveillance / Tracking>", "count": <int>, "context": "<short snippet showing usage>"}}
  ],
  "data_sharing_patterns_detected": ["<plain English description of each data sharing pattern found>"],
  "key_issues": ["<concise bullet issue statements>"],
  "recommendations": ["<actionable recommendation for the user>"],
  "ai_explanation": "<detailed paragraph explaining the overall risk assessment and reasoning>"
}}

Scoring guidelines:
- Each high-severity permission: +3 points
- Each medium-severity permission: +2 points  
- Each low-severity permission: +1 point
- Each risky keyword: +1 point (max +10)
- Each data sharing pattern: +2 points
- Score 0-4: Low, 5-9: Medium, 10+: High

Be thorough, accurate, and conservative in risk assessment. Flag anything that could compromise user privacy.
"""

def classify_content_with_ai(content: str, app_name: str) -> Tuple[str, str]:
    try:
        client = _get_client()
        prompt = CLASSIFICATION_PROMPT.format(content=content[:5000], app_name=app_name)
        response = client.models.generate_content(model=_MODEL, contents=prompt)
        result = response.text.upper()
        
        # Default fallbacks
        app_status = "VALID_APP"
        content_status = "INVALID_CONTENT"

        if "INVALID_APP" in result: app_status = "INVALID_APP"
        elif "SUSPICIOUS_APP" in result: app_status = "SUSPICIOUS_APP"
        
        if "TERMS" in result: content_status = "TERMS"
        elif "PERMISSIONS" in result: content_status = "PERMISSIONS"

        return app_status, content_status
    except Exception as e:
        raise e

def analyze_with_gemini(content: str, app_name: str) -> dict:
    client = _get_client()
    prompt = ANALYSIS_PROMPT.format(content=content[:8000], app_name=app_name)
    response = client.models.generate_content(model=_MODEL, contents=prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}")

    return {
        "source": "ai",
        "word_count": len(content.split()),
        "sentences_analyzed": content.count(".") + content.count("!") + content.count("?"),
        "permissions_found": _normalize_permissions(data.get("permissions_detected", [])),
        "risky_keywords": _normalize_keywords(data.get("risky_keywords_detected", [])),
        "sharing_patterns": data.get("data_sharing_patterns_detected", []),
        "ai_risk_level": data.get("risk_level", "Unknown"),
        "ai_risk_score": data.get("risk_score", 0),
        "ai_summary": data.get("summary", ""),
        "ai_key_issues": data.get("key_issues", []),
        "ai_recommendations": data.get("recommendations", []),
        "ai_explanation": data.get("ai_explanation", ""),
    }

def analyze_image_with_gemini(image_path: str, app_name: str) -> dict:
    client = _get_client()
    img = Image.open(image_path)
    prompt = ANALYSIS_PROMPT.format(content="[IMAGE ATTACHED]", app_name=app_name) + "\nIMPORTANT: Analyze the text visible in this image."
    response = client.models.generate_content(model=_MODEL, contents=[prompt, img])
    raw = response.text.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini image analysis returned invalid JSON: {e}")

    return {
        "source": "ai_image",
        "word_count": 0,
        "sentences_analyzed": 0,
        "permissions_found": _normalize_permissions(data.get("permissions_detected", [])),
        "risky_keywords": _normalize_keywords(data.get("risky_keywords_detected", [])),
        "sharing_patterns": data.get("data_sharing_patterns_detected", []),
        "ai_risk_level": data.get("risk_level", "Unknown"),
        "ai_risk_score": data.get("risk_score", 0),
        "ai_summary": data.get("summary", ""),
        "ai_key_issues": data.get("key_issues", []),
        "ai_recommendations": data.get("recommendations", []),
        "ai_explanation": data.get("ai_explanation", ""),
        "detected_type": "Permissions Description" if data.get("risk_score", 0) > 0 else "Terms & Conditions"
    }

def _normalize_permissions(raw: list) -> list:
    normalized = []
    for p in raw:
        normalized.append({
            "permission": p.get("permission", "Unknown"),
            "severity": p.get("severity", "low"),
            "matched_term": p.get("matched_term", ""),
            "risk_explanation": p.get("risk_explanation", p.get("reason", "No detailed risk data.")),
            "purpose": p.get("purpose", "Likely app functionality."),
            "recommendation": p.get("recommendation", "Review trust before allowing."),
        })
    return normalized

def _normalize_keywords(raw: list) -> list:
    normalized = []
    for kw in raw:
        normalized.append({
            "term": kw.get("term", ""),
            "category": kw.get("category", "General"),
            "count": kw.get("count", 1),
            "context": kw.get("context", ""),
        })
    return normalized
