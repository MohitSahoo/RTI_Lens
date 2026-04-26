"""
Input sanitization utilities for security
"""
import re
from typing import Optional


def sanitize_text_input(
    text: str,
    max_length: int = 5000,
    allow_newlines: bool = True
) -> str:
    """
    Sanitize user text input to prevent injection attacks

    Args:
        text: Raw user input
        max_length: Maximum allowed length
        allow_newlines: Whether to preserve newline characters

    Returns:
        Sanitized text string
    """
    if not text:
        return ""

    # Remove control characters except newlines/tabs if allowed
    if allow_newlines:
        # Keep \n and \t, remove other control chars
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    else:
        # Remove all control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Enforce length limit
    if len(text) > max_length:
        text = text[:max_length]

    return text


def sanitize_question(question: str) -> str:
    """Sanitize Q&A question input"""
    return sanitize_text_input(question, max_length=500, allow_newlines=False)


def sanitize_context(context: str) -> str:
    """Sanitize draft context input"""
    return sanitize_text_input(context, max_length=5000, allow_newlines=True)


def sanitize_raw_text(raw_text: str) -> str:
    """Sanitize prediction raw text input"""
    return sanitize_text_input(raw_text, max_length=50000, allow_newlines=True)


def validate_ministry_name(ministry: str) -> Optional[str]:
    """
    Validate and sanitize ministry name

    Returns None if invalid, sanitized string if valid
    """
    if not ministry:
        return None

    # Remove control characters
    ministry = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', ministry)
    ministry = ministry.strip()

    # Check length
    if len(ministry) < 3 or len(ministry) > 200:
        return None

    # Allow letters, numbers, spaces, hyphens, parentheses, commas
    if not re.match(r'^[a-zA-Z0-9\s\-(),&.]+$', ministry):
        return None

    return ministry


def validate_section_cited(section: str) -> Optional[str]:
    """
    Validate and sanitize RTI section citation

    Returns None if invalid, sanitized string if valid
    """
    if not section:
        return None

    # Remove control characters
    section = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', section)
    section = section.strip()

    # Check length
    if len(section) < 1 or len(section) > 50:
        return None

    # Allow section format like "8(1)(a)", "6(3)", etc.
    if not re.match(r'^[0-9]+(\([0-9a-zA-Z]+\))*$', section):
        return None

    return section
