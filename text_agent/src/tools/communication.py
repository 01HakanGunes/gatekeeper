from langchain_core.tools import tool
from data.contacts import CONTACTS
from src.utils import email_sender


@tool
def send_email(contact_name: str, subject: str, message: str) -> str:
    """
    Send an email to a contact from the approved contact list.

    Args:
        contact_name: Full name of the contact
        subject: Subject line of the email
        message: Body content of the email

    Returns:
        Confirmation message about the email being sent
    """
    if contact_name not in CONTACTS:
        available_contacts = ", ".join(CONTACTS.keys())
        return f"Error: Contact '{contact_name}' not found. Available contacts: {available_contacts}"

    email_address = CONTACTS[contact_name]

    # Send email using the email_sender utility
    success, result_message = email_sender.send_email(
        recipient_email=email_address,
        subject=subject,
        message=message,
        recipient_name=contact_name,
    )

    if success:
        print(f"\n📧 EMAIL SENT:")
        print(f"To: {contact_name} ({email_address})")
        print(f"Subject: {subject}")
        print(f"Message: {message}")
        print("=" * 50)
        return f"✅ Email successfully sent to {contact_name} ({email_address}) with subject '{subject}'"
    else:
        print(f"⚠️ EMAIL SENDING FAILED:")
        print(f"Error: {result_message}")
        print("=" * 50)
        return f"⚠️ Failed to send email to {contact_name}: {result_message}"


# Define tools list
tools = [send_email]
