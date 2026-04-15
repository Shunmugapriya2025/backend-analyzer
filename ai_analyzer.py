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

_MODEL = "gemini-2.0-flash"
_MODEL_VISION = "gemini-2.0-flash"
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
# ROLE: Cybersecurity Risk Analyzer

# TASK: 
Analyze the provided app permissions or privacy policy text for the app "{app_name}". 
Determine the privacy risk level and provide actionable security insights.

# INPUT TEXT:
\"\"\"
{content}
\"\"\"

# ANALYTICAL RULES (STRICT COMPLIANCE):
1. DYNAMIC ASSESSMENT: Evaluate the permissions relative to the app's category. Do NOT give generic or repetitive answers.
2. GRANULAR SCORING: Provide a specific risk score from 0 to 100. Higher permissions/sensitive data access = higher risk.
3. STRICT IDENTIFICATION: Flag hidden tracking, third-party sharing, and surveillance patterns.
4. HONESTY: If the text is suspicious or fake, explicitly mention it in the "ai_explanation".

# OUTPUT FORMAT (STRICT JSON ONLY):
{{
  "risk_level": "Low" | "Medium" | "High",
  "risk_score": <granular_integer_0_to_100>,
  "summary": "<one-paragraph plain-English summary of findings>",
  "permissions_detected": [
    {{
      "permission": "<name>",
      "severity": "low" | "medium" | "high",
      "matched_term": "<exact term found>",
      "risk_explanation": "<detailed why it's risky>",
      "purpose": "<why app needs this>",
      "recommendation": "<actionable advice>"
    }}
  ],
  "risky_keywords_detected": [
    {{"term": "<term>", "category": "<category>", "count": <int>, "context": "<short snippet>"}}
  ],
  "data_sharing_patterns_detected": ["<description of sharing pattern>"],
  "key_issues": ["<concise bullet issue statements>"],
  "recommendations": ["<actionable recommendation for the user>"],
  "ai_explanation": "<detailed paragraph explaining the overall risk reasoning and dynamic assessment>"
}}
"""

def extract_text_from_image_ai(image_path: str) -> str:
    """
    Step 1: Extract all text from an image using Gemini Vision.
    """
    client = _get_client()
    try:
        img = Image.open(image_path)
        prompt = "Extract every single word of text found in this image. Do not summarize. Just provide the raw text."
        
        response = client.models.generate_content(model=_MODEL_VISION, contents=[prompt, img])
        text = response.text.strip()
        return text
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            raise ValueError("GEMINI_QUOTA_EXHAUSTED")
        raise e

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
    """
    User Request: Separate OCR and AI analysis.
    Step 1: Extract text.
    Step 2: Send extracted text to standard AI analysis.
    """
    # ── Step 1: Extract ──
    try:
        ocr_text = extract_text_from_image_ai(image_path)
    except Exception as e:
        raise e

    if not ocr_text.strip():
        raise ValueError("No text could be extracted from the image by the AI.")

    # ── Step 2: Analyze ──
    # Re-use the existing text analysis logic for consistency
    analysis = analyze_with_gemini(ocr_text, app_name)
    
    # Enrich with OCR specific metadata
    analysis["source"] = "ai_image"
    analysis["ocr_text"] = ocr_text
    analysis["detected_type"] = "Permissions Description" if analysis.get("ai_risk_score", 0) > 0 else "Terms & Conditions"
    
    return analysis

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
