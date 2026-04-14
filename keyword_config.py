"""
Keyword Configuration
Central list of sensitive permissions, risky terms, and data-sharing patterns.
Edit this file to tune detection without touching pipeline logic.
"""

# ─── Sensitive Permissions ─────────────────────────────────────────
# Each entry: name, detection keywords, severity (high/medium/low)
SENSITIVE_PERMISSIONS = [
    {
        "name": "Location",
        "keywords": ["location", "gps", "geolocation", "precise location", "coarse location", "lat/long"],
        "severity": "high",
    },
    {
        "name": "Camera",
        "keywords": ["camera", "photo", "video capture", "take pictures"],
        "severity": "high",
    },
    {
        "name": "Microphone",
        "keywords": ["microphone", "audio recording", "record audio", "voice", "mic"],
        "severity": "high",
    },
    {
        "name": "Contacts",
        "keywords": ["contacts", "address book", "phonebook", "read contacts"],
        "severity": "high",
    },
    {
        "name": "Storage",
        "keywords": ["read external storage", "write external storage", "files", "storage access"],
        "severity": "medium",
    },
    {
        "name": "Phone/SMS",
        "keywords": ["call logs", "read sms", "send sms", "read phone state", "imei"],
        "severity": "high",
    },
    {
        "name": "Calendar",
        "keywords": ["calendar", "read calendar", "write calendar"],
        "severity": "medium",
    },
    {
        "name": "Biometric / Device ID",
        "keywords": ["fingerprint", "face recognition", "biometric", "device id", "advertising id"],
        "severity": "high",
    },
    {
        "name": "Network / Bluetooth",
        "keywords": ["bluetooth", "nearby devices", "wifi", "network state"],
        "severity": "low",
    },
]

# ─── Risky Keywords ────────────────────────────────────────────────
# Each entry: term to match, category label
RISKY_KEYWORDS = [
    {"term": "collect",         "category": "Data Collection"},
    {"term": "we collect",      "category": "Data Collection"},
    {"term": "gather",          "category": "Data Collection"},
    {"term": "track",           "category": "Tracking"},
    {"term": "tracking",        "category": "Tracking"},
    {"term": "monitor",         "category": "Tracking"},
    {"term": "surveillance",    "category": "Tracking"},
    {"term": "share",           "category": "Data Sharing"},
    {"term": "sell",            "category": "Data Selling"},
    {"term": "sell your data",  "category": "Data Selling"},
    {"term": "third party",     "category": "Third-Party Sharing"},
    {"term": "third-party",     "category": "Third-Party Sharing"},
    {"term": "partners",        "category": "Third-Party Sharing"},
    {"term": "advertiser",      "category": "Advertising"},
    {"term": "advertising",     "category": "Advertising"},
    {"term": "targeted ads",    "category": "Advertising"},
    {"term": "consent",         "category": "User Consent"},
    {"term": "by using",        "category": "Implied Consent"},
    {"term": "by clicking",     "category": "Implied Consent"},
    {"term": "retain",          "category": "Data Retention"},
    {"term": "indefinitely",    "category": "Data Retention"},
    {"term": "aggregate",       "category": "Data Aggregation"},
    {"term": "anonymized",      "category": "Data Anonymization"},
    {"term": "profiling",       "category": "User Profiling"},
    {"term": "infer",           "category": "User Profiling"},
    {"term": "behavioral",      "category": "User Profiling"},
]

# ─── Data Sharing / Collection Sentence Patterns (regex) ──────────
DATA_SHARING_PATTERNS = [
    r"we (may |will |can )?(collect|gather|obtain|receive) (your |personal |user )?data",
    r"(share|disclose|sell|transfer) (your |personal |user )?(data|information) (with|to)",
    r"third[- ]part(y|ies) (may |will |can )?(access|receive|use)",
    r"(use|process) (your |personal )?(data|information) for (advertising|marketing|profiling)",
    r"(retain|store|keep) (your |personal )?(data|information) (for|indefinitely)",
    r"we (may )?combine (your )?data",
    r"track(ing)? (your )?(activity|behavior|location|usage)",
    r"(build|create|maintain) a profile",
    r"(opt[- ]out|opt[- ]in)",
]
