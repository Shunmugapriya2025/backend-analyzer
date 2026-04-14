"""
Secure App Permission Analyzer — FastAPI Backend
Run: uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import shutil, tempfile, os
from datetime import datetime, timezone

# Load .env automatically
from dotenv import load_dotenv
load_dotenv()

from input_handler    import detect_input_type, InputType
from image_pipeline   import run_image_pipeline
from ai_analyzer      import analyze_with_gemini, classify_content_with_ai, analyze_image_with_gemini
from fallback_analyzer import analyze_with_keywords
from report_generator import generate_report_ai
from content_classifier import ContentClassifier

classifier = ContentClassifier()

app = FastAPI(
    title="Secure App Permission Analyzer",
    description="AI-powered privacy risk analyzer using Google Gemini. Analyzes mobile app privacy policies or permission screenshots.",
    version="2.0.0",
)


# Allow all origins for production flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health Check ──────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Permission Analyzer API is running.",
        "version": "2.0.0"
    }


# ─── Main Analyze Endpoint ─────────────────────────────────────────
@app.post("/analyze", tags=["Analyze"])
async def analyze(
    app_name: Optional[str] = Form(None, description="Name of the app being analyzed"),
    text: Optional[str] = Form(None, description="Paste privacy policy text here"),
    image: Optional[UploadFile] = None,
):
    """
    Accepts EITHER a privacy policy text OR a permission screenshot image.
    Following user's request: If image, extract text first, then analyze as text.
    """
    if not app_name or not app_name.strip():
        raise HTTPException(status_code=400, detail="App Name is required.")
    input_type = detect_input_type(text=text, image=image)

    if input_type == InputType.NONE:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'text' (privacy policy) or 'image' (permission screenshot), not both or neither."
        )

    # ── Step 1 & 3 Combined for Images: AI Vision Analysis ────────
    if input_type == InputType.IMAGE:
        suffix = os.path.splitext(image.filename)[-1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(image.file, tmp)
            tmp_path = tmp.name
        
        try:
            # Use Gemini Vision for both Extraction AND Analysis
            analysis = analyze_image_with_gemini(tmp_path, app_name)
            content = analysis.get("ocr_text", "")
            ocr_preview = content[:500]
            ai_mode = "gemini_vision"
            app_status = "VALID_APP" # Vision is more trusted for app identity
            detected_type = analysis.get("detected_type", "Permissions/Terms")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image AI Analysis failed: {str(e)}")
        finally:
            os.unlink(tmp_path)
    else:
        # Standard text path
        content = text
        ocr_preview = None

        # ── Step 2: Content Classification (Hybrid AI + Heuristic Fallback) ─────
        try:
            app_status, type_code = classify_content_with_ai(content, app_name)
            classification_source = "AI"
        except Exception:
            app_status = "VALID_APP"
            type_code = "INVALID_CONTENT"
            classification_source = "None"

        if app_status == "INVALID_APP":
            raise HTTPException(
                status_code=422,
                detail=f"Error: The app name '{app_name}' appears invalid."
            )

        # Fallback to heuristic if AI fails/rejects content
        if type_code == "INVALID_CONTENT":
            heuristic_code, confidence = classifier.classify(content)
            if heuristic_code != "INVALID":
                type_code = heuristic_code
                classification_source = "Heuristic Fallback"

        if type_code == "INVALID_CONTENT":
            raise HTTPException(
                status_code=422,
                detail=f"Analysis Failed: The provided text does not match the expected Terms or Permissions for '{app_name}'."
            )
        
        label_map = {
            "TERMS": "Terms & Conditions", "TC": "Terms & Conditions", "PP": "Terms & Conditions",
            "PERMISSIONS": "Permissions Description", "PD": "Permissions Description"
        }
        detected_type = label_map.get(type_code, "Policy/Permissions Document")

        # ── Step 3: AI Analysis (Text-only Gemini analysis) ───────────
        ai_mode = "gemini"
        try:
            analysis = analyze_with_gemini(content, app_name)
        except Exception:
            analysis = analyze_with_keywords(content)
            ai_mode = "keyword_fallback"

    # ── Step 4: Build report ───────────────────────────────────────
    report = generate_report_ai(analysis, input_type.value)
    report["analyzer"] = "Gemini AI Vision" if ai_mode == "gemini_vision" else ("Gemini AI" if ai_mode == "gemini" else "Keyword Analysis")
    report["detected_content_type"] = detected_type
    report["app_status_flag"] = app_status 

    if input_type == InputType.IMAGE and ocr_preview:
        report["ocr_extracted_text_preview"] = ocr_preview

    if app_name and app_name.strip():
        report["app_name"] = app_name.strip()

    report["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    return report
