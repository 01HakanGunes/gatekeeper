import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from typing import Optional, Tuple

# Load environment variables from .env file
load_dotenv()


class EmailSender:
    """
    Utility class for sending emails via Gmail SMTP.
    Reads credentials from environment variables.
    """

    def __init__(self):
        """Initialize email sender with credentials from .env file."""
        self.username = "unoapp16@gmail.com"
        self.password = os.getenv("GMAIL_PASSWORD")
        self.sender_name = "Security Gate System"
        self.smtp_server = "smtp.gmail.com"
        self.port = 587  # For starttls

        # Verify credentials are available
        if not self.username or not self.password:
            print("⚠️ Warning: Gmail credentials not found in .env file")

    def send_email(
        self,
        recipient_email: str,
        subject: str,
        message: str,
        recipient_name: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Send an email using Gmail SMTP.

        Args:
            recipient_email: Email address of recipient
            subject: Email subject line
            message: Email message body (plain text)
            recipient_name: Optional name of recipient for personalized "To" field

        Returns:
            Tuple containing success status (bool) and result message (str)
        """
        if not self.username or not self.password:
            return False, "Gmail credentials not configured in .env file"

        try:
            # Create message container
            email_message = MIMEMultipart()
            email_message["From"] = f"{self.sender_name} <{self.username}>"

            # Set To field with recipient name if provided
            if recipient_name:
                email_message["To"] = f"{recipient_name} <{recipient_email}>"
            else:
                email_message["To"] = recipient_email

            email_message["Subject"] = subject

            # Attach message body
            email_message.attach(MIMEText(message, "plain"))

            # Create secure SSL context
            context = ssl.create_default_context()

            # Connect to server and send email
            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(self.username, self.password)
                server.sendmail(
                    self.username, recipient_email, email_message.as_string()
                )

            return True, f"Email successfully sent to {recipient_email}"

        except Exception as e:
            error_message = f"Failed to send email: {str(e)}"
            return False, error_message

    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate that the email sender is properly configured.

        Returns:
            Tuple containing validation status (bool) and message (str)
        """
        if not self.username:
            return False, "GMAIL_USERNAME not found in .env file"
        if not self.password:
            return False, "GMAIL_PASSWORD not found in .env file"

        return True, "Email configuration valid"


# Create a singleton instance
email_sender = EmailSender()
