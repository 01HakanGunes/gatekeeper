# Email Utility Documentation

This directory contains the email sending functionality for the Security Gate System.

## Overview

The email utility provides Gmail SMTP integration for sending notifications when visitors are granted access. It uses environment variables for secure credential management and provides both tool integration and direct usage interfaces.

## Features

- **Gmail SMTP Integration**: Uses modern Gmail App Password authentication
- **Environment Variable Configuration**: Secure credential storage in `.env` file
- **Error Handling**: Comprehensive error handling and validation
- **Test Utilities**: Built-in testing and validation scripts
- **Multiple Interfaces**: Both tool integration and direct usage APIs

## Quick Setup

1. **Create Gmail App Password**:
   - Enable 2-Factor Authentication on your Gmail account
   - Generate an App Password at: https://myaccount.google.com/apppasswords
   - Save the generated password

2. **Configure Environment Variables**:
   ```bash
   # Edit the .env file in project root
   GMAIL_USERNAME=your.email@gmail.com
   GMAIL_PASSWORD=your_app_password_here
   GMAIL_SENDER_NAME=Security Gate System
   ```

3. **Test Configuration**:
   ```bash
   cd text_agent
   python test_email.py --send-test
   ```

## File Structure

```
src/utils/email/
├── __init__.py      # Package exports
├── sender.py        # Core EmailSender class
└── direct.py        # Direct usage interface
```

## Usage Examples

### Tool Integration (Current Implementation)
The system automatically uses the email sender through the `send_email` tool:

```python
# This happens automatically in notify_contact node
from src.tools.communication import send_email

result = send_email("David Smith", "Visitor Arrival", "Your visitor has arrived")
```

### Direct Usage
For custom email sending in other parts of the application:

```python
from src.utils.email import send_direct_email

success, message = send_direct_email(
    to_email="user@example.com",
    subject="Custom Notification",
    message="Custom message content",
    to_name="John Doe"
)

if success:
    print("Email sent successfully!")
else:
    print(f"Failed to send email: {message}")
```

### Configuration Validation
Check if email is properly configured:

```python
from src.utils.email import is_email_configured, validate_email_config

if is_email_configured():
    print("Email is ready to use")
else:
    is_valid, error_message = validate_email_config()
    print(f"Email configuration error: {error_message}")
```

## Security Notes

- **Never commit real credentials** to version control
- Use Gmail App Passwords, not your regular password
- The `.env` file should be in your `.gitignore`
- App Passwords are more secure than "Less Secure Apps" option

## Troubleshooting

### Common Issues

1. **"Gmail credentials not configured"**
   - Check that `.env` file exists in project root
   - Verify `GMAIL_USERNAME` and `GMAIL_PASSWORD` are set
   - Run `python test_email.py` to validate configuration

2. **"Failed to send email: Authentication failed"**
   - Verify you're using an App Password, not your regular password
   - Check that 2-Factor Authentication is enabled on your Gmail account
   - Regenerate App Password if needed

3. **"Connection refused" or "Timeout"**
   - Check your internet connection
   - Verify firewall/proxy settings allow SMTP connections
   - Ensure Gmail SMTP (smtp.gmail.com:587) is accessible

### Testing Commands

```bash
# Test configuration only
python test_email.py

# Test configuration and send test email
python test_email.py --send-test
```

## Integration with Existing System

The email utility integrates seamlessly with the existing Security Gate System:

1. **Contact Validation**: Works with the existing `CONTACTS` dictionary
2. **Prompt Management**: Uses existing prompt templates for email content
3. **Tool System**: Replaces the mock `send_email` tool with real functionality
4. **Error Handling**: Maintains the same error reporting interface

## Dependencies

The email utility uses these packages (already in requirements.txt):
- `python-dotenv`: Environment variable loading
- Built-in `smtplib`, `ssl`, `email` modules for SMTP functionality

No additional package installation required!
