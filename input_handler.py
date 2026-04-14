"""
Module 1 — Input Handler
Detects whether input is TEXT or IMAGE and routes accordingly.
"""

from enum import Enum
from typing import Optional


class InputType(str, Enum):
    TEXT  = "text"
    IMAGE = "image"
    NONE  = "none"
    BOTH  = "both"


def detect_input_type(text: Optional[str], image) -> InputType:
    """
    Returns the resolved input type.
    Rules:
      - Both provided  → error (BOTH)
      - Neither        → error (NONE)
      - Only text      → TEXT
      - Only image     → IMAGE
    """
    has_text  = bool(text and text.strip())
    has_image = image is not None

    if has_text and has_image:
        return InputType.BOTH
    if has_text:
        return InputType.TEXT
    if has_image:
        return InputType.IMAGE
    return InputType.NONE
