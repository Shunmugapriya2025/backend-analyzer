import re

class ContentClassifier:
    """
    Classifies input text into Terms & Conditions, Privacy Policy, Permissions, or Invalid.
    Prioritizes 'Policy Nature' and 'Legal Tone' to handle real-world T&C (Instagram/Facebook).
    """
    
    TYPES = {
        "TC": "Terms & Conditions",
        "PP": "Privacy Policy",
        "PD": "Permissions Description",
        "INVALID": "Invalid Content"
    }

    # Indicators - Broadened for real-world legal docs
    INDICATORS = {
        "TC": [
            "terms of use", "terms of service", "user agreement", "legal agreement",
            "terms and conditions", "by using", "you agree", "your account",
            "we reserve the right", "liability", "governing law", "termination",
            "dispute", "warranty", "limitations", "intellectual property", "ownership"
        ],
        "PP": [
            "privacy policy", "data policy", "data use", "we collect", "personal data", 
            "information we collect", "how we use", "third-party", "sharing", "cookies", 
            "data retention", "gdpr", "ccpa", "transparency", "security practices",
            "marketing purposes", "opt-out", "unsubscribe"
        ],
        "PD": [
            "requires access", "permission to", "allow access", "needs access",
            "camera", "location", "microphone", "contacts", "photos", "storage",
            "to provide features", "functionality requires", "system permissions"
        ]
    }

    # Phrases that strongly indicate "Legal/Policy" intent regardless of category
    LEGAL_TONE_MARKERS = [
        "you agree to", "we may", "subject to", "at our discretion",
        "in accordance with", "including but not limited to", "third parties",
        "applicable law", "right to modify", "this agreement", "the following"
    ]

    # Contextual "Reject" terms (UI instructions focus)
    UI_REJECT_PATTERNS = [
        r"^click (the )?.* button$",
        r"^tap (the )?.* icon$",
        r"^press (the )?.*$",
        r"login page",
        r"welcome to our app",
        r"swipe (left|right|up|down)",
        r"select the option",
        r"navigation bar"
    ]

    def classify(self, text: str) -> tuple[str, float]:
        """
        Returns (type_code, confidence_score)
        Aims for 'Inclusive Acceptance' for anything legal-style.
        """
        text_lower = text.lower()
        word_count = len(text.split())
        
        # 1. Reject very short items (clearly not a document)
        if word_count < 10:
            return "INVALID", 1.0

        # 2. Check for explicit UI-only instructions (but only if short)
        # Long documents might contain "tap here" instructions within a help section, 
        # so only reject UI patterns if the total length is relatively short (< 100 words).
        if word_count < 100:
            for pattern in self.UI_REJECT_PATTERNS:
                if re.search(pattern, text_lower):
                    return "INVALID", 1.0

        scores = {"TC": 0, "PP": 0, "PD": 0}
        legal_tone_count = 0
        
        # 3. Check for Legal Tone (The "Always Accept" signal)
        for marker in self.LEGAL_TONE_MARKERS:
            if marker in text_lower:
                legal_tone_count += text_lower.count(marker)

        # 4. Weighted Keyword Scoring
        for code, keywords in self.INDICATORS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[code] += text_lower.count(kw)

        # 5. Decision Logic
        # If it has more than 5 legal markers OR total scores > 2, it is a document.
        total_score = sum(scores.values())
        
        if legal_tone_count >= 2 or total_score >= 2 or word_count > 150:
            # Determine which type it is most likely
            winner = max(scores, key=scores.get)
            
            # If scores are tied at 0 but it has legal tone/length, default based on signals
            if scores[winner] == 0:
                if "privacy" in text_lower or "data" in text_lower:
                    return "PP", 1.0
                return "TC", 1.0
                
            return winner, scores[winner]

        return "INVALID", 0.0

    def get_label(self, code: str) -> str:
        return self.TYPES.get(code, "Invalid Content")
