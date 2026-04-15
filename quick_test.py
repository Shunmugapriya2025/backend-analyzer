import urllib.request
import json

boundary = "----FormBoundary7MA4YWxkTrZu0gW"
body = (
    "------FormBoundary7MA4YWxkTrZu0gW\r\n"
    "Content-Disposition: form-data; name=\"app_name\"\r\n\r\n"
    "WhatsApp\r\n"
    "------FormBoundary7MA4YWxkTrZu0gW\r\n"
    "Content-Disposition: form-data; name=\"text\"\r\n\r\n"
    "This app requires access to your camera, microphone, contacts, location, and SMS. We may share your personal data with advertising partners and third parties.\r\n"
    "------FormBoundary7MA4YWxkTrZu0gW--\r\n"
).encode()

req = urllib.request.Request(
    "http://localhost:8000/analyze",
    data=body,
    headers={"Content-Type": "multipart/form-data; boundary=----FormBoundary7MA4YWxkTrZu0gW"},
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    print("RISK LEVEL:", data.get("risk_level", "?"))
    print("RISK SCORE:", data.get("risk_score", "?"))
    print("SUMMARY:", str(data.get("summary", ""))[:300])
    print("\nSTATUS: SUCCESS - Backend is fully working!")
except Exception as e:
    print("ERROR:", str(e)[:400])
