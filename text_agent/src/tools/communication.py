from langchain_core.tools import tool
from ..core.constants import CONTACTS


@tool
def send_email(contact_name: str, subject: str, message: str) -> str:
    """
    Send an email to a contact from the approved contact list.

    Args:
        contact_name: Full name of the contact (e.g., "David Smith", "Alice Kimble")
        subject: Subject line of the email
        message: Body content of the email

    Returns:
        Confirmation message about the email being sent
    """
    if contact_name not in CONTACTS:
        available_contacts = ", ".join(CONTACTS.keys())
        return f"Error: Contact '{contact_name}' not found. Available contacts: {available_contacts}"

    email_address = CONTACTS[contact_name]

    # Mock email sending (replace with actual email service)
    print(f"\n📧 EMAIL SENT:")
    print(f"To: {contact_name} ({email_address})")
    print(f"Subject: {subject}")
    print(f"Message: {message}")
    print("=" * 50)

    return f"✅ Email successfully sent to {contact_name} ({email_address}) with subject '{subject}'"


# Define tools list
tools = [send_email]
