#!/usr/bin/env python3
"""
Direct Email Utility

This module provides a simple interface for sending emails directly without going through tools.
Useful for integration with other parts of the application.

Example usage:
    from src.utils.email.direct import send_direct_email

    success, message = send_direct_email(
        to_email="user@example.com",
        subject="Test Subject",
        message="Test message",
        to_name="John Doe"
    )
"""

from .sender import email_sender
from typing import Optional, Tuple


def send_direct_email(
    to_email: str, subject: str, message: str, to_name: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Send an email directly using the configured email sender.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email message body
        to_name: Optional recipient name

    Returns:
        Tuple containing success status (bool) and result message (str)
    """
    return email_sender.send_email(
        recipient_email=to_email,
        subject=subject,
        message=message,
        recipient_name=to_name,
    )


def validate_email_config() -> Tuple[bool, str]:
    """
    Validate the email configuration.

    Returns:
        Tuple containing validation status (bool) and message (str)
    """
    return email_sender.validate_configuration()


def is_email_configured() -> bool:
    """
    Quick check if email is configured properly.

    Returns:
        bool: True if email is configured, False otherwise
    """
    is_valid, _ = email_sender.validate_configuration()
    return is_valid
