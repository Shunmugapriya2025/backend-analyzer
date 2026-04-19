"""Quick test to verify gemini-2.5-flash pipeline works end-to-end."""
import os, sys
from dotenv import load_dotenv
load_dotenv()
sys.path.insert(0, '.')
from ai_analyzer import classify_content_with_ai, analyze_with_gemini

TEST_TEXT = (
    "This app collects your location, contacts, and microphone data. "
    "We share information with third-party advertisers. "
    "We may access device storage to store cached files."
)
APP = "TestApp"

print("Testing classify_content_with_ai ...")
try:
    status, code = classify_content_with_ai(TEST_TEXT, APP)
    print(f"  Classification OK: app_status={status}, content_code={code}")
except Exception as e:
    print(f"  Classification FAILED: {e}")

print("Testing analyze_with_gemini ...")
try:
    result = analyze_with_gemini(TEST_TEXT, APP)
    print(f"  Analysis OK: risk={result['ai_risk_level']}, score={result['ai_risk_score']}")
    print(f"  Permissions found: {len(result['permissions_found'])}")
    print(f"  Summary: {result['ai_summary'][:100]}")
except Exception as e:
    print(f"  Analysis FAILED: {e}")
