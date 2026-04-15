import cv2
import numpy as np
import os
from typing import Optional

# Local OCR Tool (as requested by user template)
# Fallback logic: EasyOCR -> Tesseract -> Empty
_READER = None

def _get_easyocr_reader():
    global _READER
    if _READER is None:
        try:
            import easyocr
            # Note: This might download models (~100MB) on first run
            _READER = easyocr.Reader(['en'], gpu=False) 
        except ImportError:
            return None
    return _READER

def run_image_pipeline(image_path: str) -> str:
    """
    User Request: "Never send image to Gemini directly"
    Step 1: Extract text using local OCR (EasyOCR).
    Step 2: Return cleaned plain text.
    """
    print(f"DEBUG: Running local OCR on {image_path}")
    
    # 1. Try EasyOCR
    reader = _get_easyocr_reader()
    if reader:
        try:
            results = reader.readtext(image_path, detail=0)
            text = " ".join(results)
            if text.strip():
                return _clean_and_normalize(text)
        except Exception as e:
            print(f"DEBUG: EasyOCR failed: {e}")

    # 2. Try Tesseract (as fallback)
    try:
        import pytesseract
        from PIL import Image
        # Check for Windows path if not in PATH
        tess_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(tess_path):
            pytesseract.pytesseract.tesseract_cmd = tess_path
            
        text = pytesseract.image_to_string(Image.open(image_path))
        if text.strip():
            return _clean_and_normalize(text)
    except Exception as e:
        print(f"DEBUG: Tesseract failed: {e}")

    return ""

def _clean_and_normalize(text: str) -> str:
    """Follows Template Step 3: Text Cleaning Layer"""
    import re
    # Remove junk symbols and normalize whitespace
    text = re.sub(r"[^\w\s,.!?@-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
