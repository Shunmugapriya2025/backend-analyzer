"""
Tests for Permission Analyzer Backend
Run: pytest tests/ -v
"""

import pytest
from app.input_handler   import detect_input_type, InputType
from app.text_pipeline   import run_text_pipeline
from app.risk_classifier import classify_risk
from app.report_generator import generate_report


# ─── Input Handler Tests ───────────────────────────────────────────

def test_detect_text_input():
    result = detect_input_type(text="We collect your location data.", image=None)
    assert result == InputType.TEXT

def test_detect_image_input():
    class FakeUpload:
        pass
    result = detect_input_type(text=None, image=FakeUpload())
    assert result == InputType.IMAGE

def test_detect_no_input():
    result = detect_input_type(text=None, image=None)
    assert result == InputType.NONE

def test_detect_both_inputs():
    class FakeUpload:
        pass
    result = detect_input_type(text="some text", image=FakeUpload())
    assert result == InputType.BOTH

def test_detect_empty_string_as_none():
    result = detect_input_type(text="   ", image=None)
    assert result == InputType.NONE


# ─── Text Pipeline Tests ───────────────────────────────────────────

HIGH_RISK_POLICY = """
This app collects your precise location data and microphone audio at all times.
We share your personal information with third-party advertising partners.
We track your browsing behavior to build a profile for targeted ads.
By using this app you consent to indefinite data retention.
"""

LOW_RISK_POLICY = """
This app uses network access to load content.
We do not collect any personal information.
No data is shared with third parties.
"""

def test_text_pipeline_detects_permissions():
    result = run_text_pipeline(HIGH_RISK_POLICY)
    perm_names = [p["permission"] for p in result["permissions_found"]]
    assert "Location" in perm_names
    assert "Microphone" in perm_names

def test_text_pipeline_detects_risky_keywords():
    result = run_text_pipeline(HIGH_RISK_POLICY)
    terms = [kw["term"] for kw in result["risky_keywords"]]
    assert "collect" in terms
    assert "third party" in terms or "track" in terms

def test_text_pipeline_low_risk():
    result = run_text_pipeline(LOW_RISK_POLICY)
    assert len(result["permissions_found"]) == 0

def test_text_pipeline_returns_word_count():
    result = run_text_pipeline("This app collects location data.")
    assert result["word_count"] > 0


# ─── Risk Classifier Tests ─────────────────────────────────────────

def test_classify_high_risk():
    analysis = run_text_pipeline(HIGH_RISK_POLICY)
    risk = classify_risk(analysis)
    assert risk.level == "High"
    assert risk.score >= 10

def test_classify_low_risk():
    analysis = run_text_pipeline(LOW_RISK_POLICY)
    risk = classify_risk(analysis)
    assert risk.level == "Low"

def test_risk_has_reasons():
    analysis = run_text_pipeline(HIGH_RISK_POLICY)
    risk = classify_risk(analysis)
    assert len(risk.reasons) > 0


# ─── Report Generator Tests ────────────────────────────────────────

def test_report_structure():
    analysis = run_text_pipeline(HIGH_RISK_POLICY)
    risk = classify_risk(analysis)
    report = generate_report(analysis, risk, "text")
    required_keys = [
        "status", "input_type", "risk_level", "risk_score",
        "summary", "permissions_detected", "risky_keywords_detected",
        "recommendations", "key_issues", "stats"
    ]
    for key in required_keys:
        assert key in report, f"Missing key: {key}"

def test_report_risk_level_matches():
    analysis = run_text_pipeline(HIGH_RISK_POLICY)
    risk = classify_risk(analysis)
    report = generate_report(analysis, risk, "text")
    assert report["risk_level"] == risk.level

def test_report_image_type_has_ocr_field():
    analysis = {"source": "image", "ocr_text": "test", "permissions_found": [],
                "risky_keywords": [], "sharing_patterns": [], "word_count": 1, "sentences_analyzed": 1}
    from app.risk_classifier import RiskResult
    risk = RiskResult(level="Low", score=0, reasons=[])
    report = generate_report(analysis, risk, "image")
    assert "ocr_extracted_text_preview" in report
