# Secure App Permission Analyzer — Backend

FastAPI backend that analyzes mobile app privacy policies or permission screenshots
and returns a structured **Low / Medium / High** privacy risk report.

---

## Project Structure

```
permission_analyzer/
├── app/
│   ├── main.py              # FastAPI app & /analyze endpoint
│   ├── input_handler.py     # Module 1 – detect TEXT vs IMAGE input
│   ├── text_pipeline.py     # Module 2a – NLP text analysis (spaCy)
│   ├── image_pipeline.py    # Module 2b – OpenCV preprocessing + Tesseract OCR
│   ├── keyword_config.py    # Central keyword/permission lists (edit to tune)
│   ├── risk_classifier.py   # Module 3 – Low/Medium/High scoring
│   └── report_generator.py  # Module 4 – Final JSON report
├── tests/
│   └── test_backend.py      # pytest test suite
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Install spaCy language model
```bash
python -m spacy download en_core_web_sm
```

### 3. Install Tesseract OCR (for image input)

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

---

## Run the Server

```bash
uvicorn app.main:app --reload
```

Server starts at: **http://127.0.0.1:8000**  
Auto docs (Swagger UI): **http://127.0.0.1:8000/docs**

---

## API Usage

### POST `/analyze`

Accepts **either** privacy policy text **or** a permission screenshot image (not both).

#### Option A — Text Input (form field)
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "text=We collect your location and share it with third-party advertisers."
```

#### Option B — Image Input (file upload)
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -F "image=@/path/to/screenshot.png"
```

### Sample Response
```json
{
  "status": "success",
  "input_type": "text",
  "risk_level": "High",
  "risk_icon": "🚨",
  "risk_score": 14,
  "summary": "🚨 Risk Level: HIGH (score: 14). Detected 2 sensitive permission(s), 4 risky keyword(s)...",
  "permissions_detected": [
    { "permission": "Location", "severity": "high", "matched_term": "location" }
  ],
  "risky_keywords_detected": [
    { "term": "collect", "category": "Data Collection", "count": 1, "context": "...We collect your..." }
  ],
  "data_sharing_patterns_detected": [
    "we (may |will |can )?(collect|gather|obtain|receive) (your |personal |user )?data"
  ],
  "key_issues": [
    "Location permission detected (severity: high)",
    "Risky term 'collect' found 1x [Data Collection]"
  ],
  "recommendations": [
    "⚠️ HIGH RISK: This app has significant privacy red flags.",
    "Avoid installing unless the app is from a fully trusted source."
  ],
  "stats": {
    "words_analyzed": 18,
    "sentences_analyzed": 1,
    "permissions_count": 1,
    "risky_keywords_count": 3,
    "sharing_patterns_count": 1
  }
}
```

---

## Run Tests

```bash
pytest tests/ -v
```

---

## Tuning Detection

Edit **`app/keyword_config.py`** to:
- Add/remove sensitive permissions
- Add/change risky keyword terms
- Add new data-sharing regex patterns

No changes needed in pipeline or scoring logic.
