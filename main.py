"""
Secure App Permission Analyzer — FastAPI Backend
Run: uvicorn main:app --reload
Docs: http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os, tempfile, shutil
from datetime import datetime, timezone

# Load .env automatically
from dotenv import load_dotenv
load_dotenv()

from input_handler    import InputType
from ai_analyzer      import analyze_with_gemini, classify_content_with_ai
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
    file: Optional[UploadFile] = File(None, description="Screenshot image of a permission policy"),
):
    """
    Accepts privacy policy text OR a screenshot image and analyzes it for privacy risks.
    For images: Gemini Vision extracts text first, then the extracted text is analyzed.
    """
    if not app_name or not app_name.strip():
        raise HTTPException(status_code=400, detail="App Name is required.")

    ocr_preview = None
    content = None

    # ──────────────────────────────────────────────────────────────────
    # STEP 1 → IMAGE: Extract text via Gemini Vision OCR
    # ──────────────────────────────────────────────────────────────────
    if file and file.filename:
        suffix = os.path.splitext(file.filename)[1] or ".png"
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
            from ai_analyzer import extract_text_from_image_ai
            extracted = extract_text_from_image_ai(tmp_path)   # raises on failure
        except Exception as e:
            raise HTTPException(
                status_code=422,
                detail=f"Image text extraction failed: {str(e)}"
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # Guard: OCR returned empty
        if not extracted or not extracted.strip():
            raise HTTPException(
                status_code=422,
                detail="Text extraction failed. Please upload a clear, readable screenshot."
            )

        content = extracted.strip()
        ocr_preview = content[:600]
        input_type = InputType.IMAGE

    # ──────────────────────────────────────────────────────────────────
    # STEP 1 → TEXT: Use pasted text directly
    # ──────────────────────────────────────────────────────────────────
    elif text and text.strip():
        content = text.strip()
        input_type = InputType.TEXT
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either privacy policy text or a screenshot image."
        )

    # ──────────────────────────────────────────────────────────────────
    # STEP 2 → PRE-GEMINI VALIDATION: Final guard before sending
    # ──────────────────────────────────────────────────────────────────
    if not content or len(content.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="No valid text found to analyze. Please provide more content."
        )


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

    report = generate_report_ai(analysis, input_type)
    report["analyzer"] = "Gemini AI" if ai_mode == "gemini" else "Keyword Analysis"
    report["detected_content_type"] = detected_type
    report["app_status_flag"] = app_status 

    if app_name and app_name.strip():
        report["app_name"] = app_name.strip()

    if ocr_preview:
        report["ocr_extracted_text_preview"] = ocr_preview

    report["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    return report

