#!/usr/bin/env python3
"""
Email Configuration Test Script

This script allows you to test your email configuration without running the full application.
Run this after setting up your Gmail credentials in the .env file.

Usage:
    python test_email.py                    # Test configuration only
    python test_email.py --send-test        # Send a test email
"""

import argparse
import sys
import os

# Add the parent directory to Python path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.email import email_sender


def test_configuration():
    """Test email configuration validation."""
    print("🔧 Testing Email Configuration...")
    print("=" * 50)

    is_valid, message = email_sender.validate_configuration()

    if is_valid:
        print(f"✅ {message}")
        print(f"📧 Gmail Username: {email_sender.username}")
        print(f"👤 Sender Name: {email_sender.sender_name}")
        print(f"🖥️  SMTP Server: {email_sender.smtp_server}:{email_sender.port}")
    else:
        print(f"❌ {message}")
        print("\n💡 Setup Instructions:")
        print("1. Create a .env file in the project root")
        print("2. Add your Gmail credentials:")
        print("   GMAIL_USERNAME=your.email@gmail.com")
        print("   GMAIL_PASSWORD=your_app_password")
        print("   GMAIL_SENDER_NAME=Security Gate System")
        print(
            "3. Generate an App Password from: https://myaccount.google.com/apppasswords"
        )

    print("=" * 50)
    return is_valid


def send_test_email():
    """Send a test email to verify functionality."""
    print("📤 Sending Test Email...")
    print("=" * 50)

    # Get test recipient
    recipient = input("Enter test recipient email: ").strip()
    if not recipient:
        print("❌ No recipient provided")
        return False

    recipient_name = input("Enter recipient name (optional): ").strip() or None

    # Send test email
    subject = "Security Gate System - Test Email"
    message = """Hello!

This is a test email from the Security Gate System to verify that email sending is working correctly.

If you received this email, the email configuration is working properly.

Best regards,
Security Gate System
    
Test timestamp: """ + str(
        os.popen("date").read().strip()
    )

    success, result = email_sender.send_email(
        recipient_email=recipient,
        subject=subject,
        message=message,
        recipient_name=recipient_name,
    )

    if success:
        print(f"✅ {result}")
        print("📧 Test email sent successfully!")
    else:
        print(f"❌ {result}")
        print("💡 Check your Gmail credentials and App Password")

    print("=" * 50)
    return success


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test email configuration for Security Gate System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--send-test",
        action="store_true",
        help="Send a test email after configuration check",
    )

    args = parser.parse_args()

    print("🏢 Security Gate System - Email Configuration Test")
    print("=" * 60)

    # Test configuration
    config_valid = test_configuration()

    if not config_valid:
        print("❌ Email configuration invalid. Please fix the configuration first.")
        return 1

    # Send test email if requested
    if args.send_test:
        print()
        if not send_test_email():
            return 1

    print("🎉 Email configuration test completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())
