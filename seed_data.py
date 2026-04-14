"""
seed_data.py — Inserts demo analysis reports into MongoDB
Run: python seed_data.py
"""

import asyncio
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGODB_DB",  "permission_analyzer")

DEMO_REPORTS = [
    {
        "status": "success",
        "analyzer": "AI Analyzer",
        "input_type": "text",
        "risk_level": "High",
        "risk_icon": "🚨",
        "risk_score": 24,
        "summary": (
            "This privacy policy reveals extensive data collection including precise GPS location, "
            "contacts, microphone access, and third-party advertising data sharing. Multiple high-risk "
            "indicators were detected suggesting aggressive user tracking practices."
        ),
        "ai_explanation": (
            "The app collects a wide range of sensitive personal data and shares it with advertising "
            "networks. The combination of real-time location tracking, microphone access, and contact "
            "harvesting represents a significant privacy threat. Data is retained indefinitely with no "
            "clear user opt-out mechanism."
        ),
        "permissions_detected": [
            {"permission": "Location (GPS)", "severity": "high", "matched_term": "precise location", "reason": "Tracks user in real-time"},
            {"permission": "Microphone", "severity": "high", "matched_term": "microphone access", "reason": "Can record audio without explicit indication"},
            {"permission": "Contacts", "severity": "high", "matched_term": "address book", "reason": "Harvests personal contact data"},
            {"permission": "Camera", "severity": "medium", "matched_term": "camera", "reason": "Can capture images/video"},
            {"permission": "Storage", "severity": "low", "matched_term": "external storage", "reason": "Access to all files on device"},
        ],
        "risky_keywords_detected": [
            {"term": "third-party advertising", "category": "Data Sharing", "count": 4, "context": "...share data with third-party advertising partners..."},
            {"term": "precise location", "category": "Tracking", "count": 3, "context": "...collect precise location data continuously..."},
            {"term": "behavioral profiling", "category": "Surveillance", "count": 2, "context": "...used for behavioral profiling and targeted ads..."},
            {"term": "data broker", "category": "Data Sharing", "count": 1, "context": "...may sell anonymized data to data broker partners..."},
        ],
        "data_sharing_patterns_detected": [
            "Data shared with advertising networks for targeted marketing",
            "User profiles sold to third-party data brokers",
            "Analytics data sent to Google Firebase and Facebook SDK",
        ],
        "key_issues": [
            "Real-time GPS tracking enabled by default",
            "Microphone access requested without clear justification",
            "Contact list uploaded to remote servers",
            "No clear data deletion mechanism provided",
            "Data shared with multiple advertising platforms",
        ],
        "recommendations": [
            "⚠️ HIGH RISK: This app has significant privacy red flags.",
            "Multiple sensitive permissions and risky data practices detected.",
            "Avoid installing unless the app is from a fully trusted source.",
            "If already installed, revoke sensitive permissions in device settings.",
            "Report suspicious apps to your app store.",
        ],
        "stats": {
            "words_analyzed": 1842,
            "sentences_analyzed": 97,
            "permissions_count": 5,
            "risky_keywords_count": 4,
            "sharing_patterns_count": 3,
        },
        "analyzed_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "app_name": "FreeVPN Pro",
    },
    {
        "status": "success",
        "analyzer": "AI Analyzer",
        "input_type": "text",
        "risk_level": "Medium",
        "risk_icon": "⚠️",
        "risk_score": 11,
        "summary": (
            "This app collects standard usage analytics and device identifiers. "
            "Some data is shared with analytics providers but the policy is reasonably transparent. "
            "Camera and notification permissions are requested for core functionality."
        ),
        "ai_explanation": (
            "The privacy policy is moderately detailed. Data collection is limited to app analytics "
            "and crash reporting. Location data is only collected when the app is in use. "
            "The app does not appear to sell user data, but shares with analytics partners."
        ),
        "permissions_detected": [
            {"permission": "Camera", "severity": "medium", "matched_term": "camera access", "reason": "Used for QR scanning feature"},
            {"permission": "Notifications", "severity": "low", "matched_term": "push notifications", "reason": "Sends marketing notifications"},
            {"permission": "Location", "severity": "medium", "matched_term": "approximate location", "reason": "Used only while app is active"},
        ],
        "risky_keywords_detected": [
            {"term": "analytics partners", "category": "Data Sharing", "count": 2, "context": "...share anonymized data with analytics partners..."},
            {"term": "device identifiers", "category": "Tracking", "count": 3, "context": "...collect device identifiers such as IDFA and GAID..."},
        ],
        "data_sharing_patterns_detected": [
            "Anonymized crash reports sent to Sentry",
            "Usage analytics shared with Mixpanel",
        ],
        "key_issues": [
            "Device identifiers collected and shared with analytics services",
            "Location data collected while app is in use",
            "No opt-out for analytics data collection",
        ],
        "recommendations": [
            "This app has moderate privacy concerns — proceed with caution.",
            "Review permissions related to: Camera, Location",
            "Consider denying non-essential permissions when the app requests them.",
            "Read the full Terms & Conditions before accepting.",
        ],
        "stats": {
            "words_analyzed": 963,
            "sentences_analyzed": 54,
            "permissions_count": 3,
            "risky_keywords_count": 2,
            "sharing_patterns_count": 2,
        },
        "analyzed_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        "app_name": "ShopEasy",
    },
    {
        "status": "success",
        "analyzer": "AI Analyzer",
        "input_type": "text",
        "risk_level": "Low",
        "risk_icon": "✅",
        "risk_score": 3,
        "summary": (
            "This app collects minimal data limited to account credentials and basic usage statistics. "
            "No sensitive permissions are required. Data is not shared with third parties."
        ),
        "ai_explanation": (
            "The privacy policy is clear, concise, and user-friendly. Data collection is minimal and "
            "limited to what is strictly necessary for the app to function. No advertising SDKs are "
            "mentioned. The app appears to follow privacy-by-design principles."
        ),
        "permissions_detected": [
            {"permission": "Internet", "severity": "low", "matched_term": "internet access", "reason": "Required for app functionality"},
        ],
        "risky_keywords_detected": [],
        "data_sharing_patterns_detected": [
            "No third-party data sharing detected",
        ],
        "key_issues": [
            "Standard internet access required for core features",
        ],
        "recommendations": [
            "This app appears to have a low privacy risk based on the analyzed content.",
            "Still review the full privacy policy manually before installing.",
            "Check if the app requests unnecessary permissions at runtime.",
        ],
        "stats": {
            "words_analyzed": 412,
            "sentences_analyzed": 23,
            "permissions_count": 1,
            "risky_keywords_count": 0,
            "sharing_patterns_count": 1,
        },
        "analyzed_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "app_name": "NoteKeeper",
    },
    {
        "status": "success",
        "analyzer": "AI Analyzer",
        "input_type": "image",
        "risk_level": "High",
        "risk_icon": "🚨",
        "risk_score": 19,
        "summary": (
            "The permission screenshot reveals this app requests access to contacts, SMS, call logs, "
            "precise location, and microphone — a combination typical of spyware or highly invasive apps."
        ),
        "ai_explanation": (
            "The set of permissions requested is disproportionate to what a typical utility app needs. "
            "Requesting SMS, call log, and microphone access together is a major red flag. "
            "Users should carefully evaluate whether to grant these permissions."
        ),
        "permissions_detected": [
            {"permission": "Read SMS", "severity": "high", "matched_term": "READ_SMS", "reason": "Can read all text messages"},
            {"permission": "Read Call Log", "severity": "high", "matched_term": "READ_CALL_LOG", "reason": "Access to all call history"},
            {"permission": "Precise Location", "severity": "high", "matched_term": "ACCESS_FINE_LOCATION", "reason": "Real-time GPS tracking"},
            {"permission": "Microphone", "severity": "high", "matched_term": "RECORD_AUDIO", "reason": "Can record audio at any time"},
            {"permission": "Read Contacts", "severity": "high", "matched_term": "READ_CONTACTS", "reason": "Access to full address book"},
        ],
        "risky_keywords_detected": [
            {"term": "READ_SMS", "category": "Surveillance", "count": 1, "context": "Permission: READ_SMS"},
            {"term": "RECORD_AUDIO", "category": "Surveillance", "count": 1, "context": "Permission: RECORD_AUDIO"},
            {"term": "ACCESS_FINE_LOCATION", "category": "Tracking", "count": 1, "context": "Permission: ACCESS_FINE_LOCATION"},
        ],
        "data_sharing_patterns_detected": [
            "Permissions suggest potential data exfiltration to remote servers",
        ],
        "key_issues": [
            "SMS and call log access — unusually high privilege",
            "Microphone + location combination is a spyware indicator",
            "5 high-severity permissions requested simultaneously",
        ],
        "recommendations": [
            "⚠️ HIGH RISK: This app has significant privacy red flags.",
            "Do not grant SMS, Call Log, or Microphone permissions.",
            "Avoid installing unless the app is from a fully trusted source.",
            "Report suspicious apps to your app store.",
        ],
        "stats": {
            "words_analyzed": 78,
            "sentences_analyzed": 12,
            "permissions_count": 5,
            "risky_keywords_count": 3,
            "sharing_patterns_count": 1,
        },
        "ocr_extracted_text_preview": "READ_SMS READ_CALL_LOG ACCESS_FINE_LOCATION RECORD_AUDIO READ_CONTACTS WRITE_EXTERNAL_STORAGE...",
        "analyzed_at": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
        "app_name": "FlashLight Ultra",
    },
    {
        "status": "success",
        "analyzer": "Google Gemini AI",
        "input_type": "text",
        "risk_level": "Medium",
        "risk_icon": "⚠️",
        "risk_score": 8,
        "summary": (
            "This social media app collects profile data, usage patterns, and shares data with "
            "advertising partners. Standard for the industry but worth reviewing before use."
        ),
        "ai_explanation": (
            "Data practices are typical for a social platform. Ad targeting and cross-app tracking "
            "are present. Users can opt-out of some personalization features. Policy is somewhat vague "
            "about data retention periods."
        ),
        "permissions_detected": [
            {"permission": "Camera", "severity": "medium", "matched_term": "camera", "reason": "For posting photos/videos"},
            {"permission": "Location", "severity": "medium", "matched_term": "location", "reason": "For location-tagged posts"},
            {"permission": "Contacts", "severity": "medium", "matched_term": "contacts", "reason": "To find friends on the platform"},
        ],
        "risky_keywords_detected": [
            {"term": "targeted advertising", "category": "Data Sharing", "count": 5, "context": "...used for targeted advertising across our network..."},
            {"term": "cross-app tracking", "category": "Tracking", "count": 2, "context": "...enable cross-app tracking for personalization..."},
        ],
        "data_sharing_patterns_detected": [
            "Data shared with advertising ecosystem partners",
            "Cross-app tracking enabled via Meta Pixel",
        ],
        "key_issues": [
            "Cross-app tracking enabled by default",
            "Data shared with advertising partners",
            "Vague data retention policy",
        ],
        "recommendations": [
            "This app has moderate privacy concerns — proceed with caution.",
            "Review permissions related to: Camera, Location, Contacts",
            "Disable cross-app tracking in app settings if available.",
            "Check if the app offers an opt-out for data sharing or advertising.",
        ],
        "stats": {
            "words_analyzed": 2104,
            "sentences_analyzed": 118,
            "permissions_count": 3,
            "risky_keywords_count": 2,
            "sharing_patterns_count": 2,
        },
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "app_name": "ConnectMe Social",
    },
]


async def seed():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    col = db["analyses"]

    # Clear existing demo data
    deleted = await col.delete_many({})
    print(f"🗑️  Cleared {deleted.deleted_count} existing document(s).")

    # Insert demo records
    result = await col.insert_many(DEMO_REPORTS)
    print(f"✅ Inserted {len(result.inserted_ids)} demo records into '{MONGO_DB}.analyses'")
    print("\nInserted apps:")
    for report in DEMO_REPORTS:
        print(f"  {report['risk_icon']}  [{report['risk_level']:6}] {report['app_name']} (input: {report['input_type']})")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
