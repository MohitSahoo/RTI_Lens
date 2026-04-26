"""
Shared enum definitions for constrained RTI-Lens domain fields.
"""
from enum import Enum


class AppealOutcome(str, Enum):
    ALLOWED = "allowed"
    DENIED = "denied"
    PARTIALLY_ALLOWED = "partially_allowed"


class AppealLevel(str, Enum):
    FIRST_APPEAL = "first_appeal"
    SECOND_APPEAL = "second_appeal"


class ExtractionMethod(str, Enum):
    TXT = "txt"
    PDFPLUMBER = "pdfplumber"
    OCR = "ocr"
