"""
Email Validation Utilities
"""

import re
from email_validator import validate_email, EmailNotValidError


def is_valid_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate and normalize
        validation = validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def normalize_email(email: str) -> str:
    """
    Normalize email address (lowercase, trim whitespace)
    
    Args:
        email: Email address
        
    Returns:
        Normalized email
    """
    return email.strip().lower()


def validate_email_format(email: str) -> tuple[bool, str]:
    """
    Validate email and return validation result with message
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Validate
        validation = validate_email(email, check_deliverability=False)
        normalized_email = validation.normalized
        return True, normalized_email
    except EmailNotValidError as e:
        return False, str(e)
