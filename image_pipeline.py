"""
Module 2 (Image Path) — Image Pipeline
Preprocesses screenshot with OpenCV then runs Tesseract OCR.
Extracted text is passed to the shared text analysis module.
"""

import cv2
import numpy as np
import pytesseract
import os

# Configure tesseract path for Apple Silicon Mac (Homebrew)
_TESSERACT_BIN = "/opt/homebrew/bin/tesseract"
if os.path.exists(_TESSERACT_BIN):
    pytesseract.pytesseract.tesseract_cmd = _TESSERACT_BIN


def run_image_pipeline(image_path: str) -> dict:
    """
    Full image processing pipeline:
      1. Load image with OpenCV
      2. Preprocess (grayscale → denoise → threshold → deskew)
      3. OCR with Tesseract
      4. Return raw OCR text for AI analysis
    """
    preprocessed = _preprocess_image(image_path)
    extracted_text = _run_ocr(preprocessed)

    if not extracted_text.strip():
        return {
            "source": "image",
            "ocr_text": "",
            "word_count": 0,
            "sentences_analyzed": 0,
            "permissions_found": [],
            "risky_keywords": [],
            "sharing_patterns": [],
            "ocr_warning": "No text could be extracted from the image. Ensure the screenshot is clear and readable.",
        }

    return {
        "source": "image",
        "ocr_text": extracted_text,
    }


# ─── Internal helpers ──────────────────────────────────────────────

def _preprocess_image(path: str) -> np.ndarray:
    """
    OpenCV preprocessing steps to maximize OCR accuracy:
      - Convert to grayscale
      - Resize if too small (upscale to at least 1000px wide)
      - Denoise
      - Adaptive threshold (better than simple binary for varied backgrounds)
      - Deskew
    """
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot read image: {path}")

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 2. Upscale if narrow (OCR accuracy improves on larger images)
    h, w = gray.shape
    if w < 1000:
        scale = 1000 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # 3. Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # 4. Adaptive threshold — handles uneven lighting on phone screenshots
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11, C=2
    )

    # 5. Deskew
    thresh = _deskew(thresh)

    return thresh


def _deskew(image: np.ndarray) -> np.ndarray:
    """Correct slight rotation using moments."""
    coords = np.column_stack(np.where(image < 128))  # dark pixel coords
    if len(coords) == 0:
        return image
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.5:
        return image  # skip if nearly straight
    h, w = image.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def _run_ocr(image: np.ndarray) -> str:
    """Run Tesseract OCR with tuned config for permission/policy text."""
    # PSM 6 = assume uniform block of text (good for policy pages)
    # OEM 3 = default LSTM engine
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(image, config=config)
    return text.strip()
