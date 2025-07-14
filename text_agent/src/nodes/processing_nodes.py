from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from ..core.state import State
from ..data.contacts import CONTACTS
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_main


def check_visitor_profile_node(state: State) -> State:
    """
    Node function that performs LLM extraction and updates the visitor profile.
    """
    # Get current conversation context
    messages = state["messages"]
    conversation_text = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in messages
            if hasattr(msg, "type") and hasattr(msg, "content")
        ]
    )

    # Define fields to extract (excluding contact_person which is handled by validate_contact_person node)
    fields_to_extract = [
        "name",
        "purpose",
        "threat_level",
        "affiliation",
    ]  # contact_person is exclusively handled by validate_contact_person node

    # Try to extract information using LLM
    for field in fields_to_extract:
        if state["visitor_profile"][field] is None:
            # Define detailed descriptions for each field
            field_descriptions = {
                "name": "The visitor's full name (first and last name). Examples: 'John Smith', 'Maria Garcia', 'David Kim', '-1'",
                "purpose": "The reason for the visit or what they want to do. Examples: 'meeting', 'delivery', 'tour', 'interview', 'maintenance', '-1'",
                "contact_person": "The visitor's contact inside the company. Examples: 'David Smith', 'Alice Kimble', 'CEO', 'CTO', 'Mr. John, '-1''",
                "threat_level": "Security risk assessment based on items carried, behavior, or concerns mentioned. Examples: 'low', 'medium', 'high', '-1'",
                "affiliation": "Company, organization, or group they represent. Examples: 'Google', 'FedEx', 'University of XYZ', 'independent contractor', '-1'",
            }

            # Create extraction prompt with field-specific description
            extraction_prompt = f"""You are a data extraction tool. Your task is to extract ONLY the {field} value from the conversation.

FIELD DESCRIPTION:
{field} = {field_descriptions[field]}

STRICT RULES:
- Respond with ONLY the {field} value (no explanations, no sentences)
- If you cannot clearly determine the {field} from the conversation, respond with exactly: -1
- Maximum 3 words for the response
- No punctuation except necessary hyphens or periods

Examples:
- If extracting "name" and conversation mentions "I'm John Smith" → respond: John Smith
- If extracting "purpose" and visitor says "here for the meeting" → respond: meeting
- If extracting "affiliation" and they say "I work at Google" → respond: Google
- If extracting "threat_level" and they say "I have no restricted items" → respond: low
- If cannot determine the value → respond: -1

Conversation:
{conversation_text}

Extract {field}:"""

            try:
                response = llm_main.invoke([HumanMessage(content=extraction_prompt)])
                extracted_value = extract_answer_from_thinking_model(response)

                print(extracted_value)

                # Additional cleaning to ensure we get only the value
                # Remove common prefixes that LLM might add
                prefixes_to_remove = [
                    f"{field}:",
                    f"{field.capitalize()}:",
                    "Answer:",
                    "Response:",
                    "Value:",
                    "Result:",
                    "The " + field + " is",
                    "Their " + field + " is",
                ]

                for prefix in prefixes_to_remove:
                    if extracted_value.startswith(prefix):
                        extracted_value = extracted_value[len(prefix) :].strip()

                # Remove quotes if present
                extracted_value = extracted_value.strip("\"'")

                # Take only the first few words if response is too long
                words = extracted_value.split()
                if len(words) > 3:
                    extracted_value = " ".join(words[-3:])

                # Update profile if valid information found
                if extracted_value != "-1" and extracted_value:
                    state["visitor_profile"][field] = extracted_value
                    print(f"✅ Extracted {field}: '{extracted_value}'")

            except Exception as error:
                print(f"Error extracting {field}: {error}")
                # Continue with other fields if one fails
                continue

    # Print current visitor profile status for debugging
    print(f"\n📋 Current Visitor Profile:")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state


def validate_contact_person(state: State) -> State:
    """
    Dedicated node for extracting and validating contact persons against known contacts list.
    This is the only node that handles contact_person field.
    """
    # Only process if contact_person is not already set
    if state["visitor_profile"]["contact_person"] is None:
        # Get current conversation context
        messages = state["messages"]
        conversation_text = "\n".join(
            [
                f"{msg.type}: {msg.content}"
                for msg in messages
                if hasattr(msg, "type") and hasattr(msg, "content")
            ]
        )

        # Create contact validation prompt
        known_contacts_list = "\n".join([f"- {contact}" for contact in CONTACTS.keys()])

        validation_prompt = f"""You are a strict contact person validator. Your task is to determine if the visitor is referring to any of the known contacts in our organization.

KNOWN CONTACTS:
{known_contacts_list}

STRICT MATCHING RULES:
- ONLY match if the visitor mentions a name that is clearly the SAME PERSON as one of the known contacts
- Match variations like "David", "Mr. Smith", "Dave Smith" to "David Smith" 
- Match "Alice", "Ms. Kimble", "Alice K" to "Alice Kimble"
- Match "John", "Martinez", "J. Martinez" to "John Martinez"
- DO NOT match similar sounding but different names: "Ahmad Kim" is NOT "Alice Kimble"
- DO NOT match partial similarities: "Mike Chen" is NOT "Michael Chen" unless clearly referring to the same person
- If the names are completely different people, respond with -1
- Only respond with the EXACT name from the list if you are certain it's the same person
- When in doubt, respond with -1

Examples:
- Visitor says "Ahmad Kim" → -1 (not in our list)
- Visitor says "Dave" or "David" → "David Smith" (clear match)
- Visitor says "Alice" or "Ms. Kimble" → "Alice Kimble" (clear match)
- Visitor says "Johnson" → -1 (could be Sarah Johnson but not specific enough)

Conversation:
{conversation_text}

Contact person:"""

        try:
            response = llm_main.invoke([HumanMessage(content=validation_prompt)])
            extracted_contact = extract_answer_from_thinking_model(response).strip()

            # Only set contact_person if it's a valid contact from our list
            if extracted_contact in CONTACTS:
                state["visitor_profile"]["contact_person"] = extracted_contact
                print(f"✅ Contact validation: Matched '{extracted_contact}'")
            elif extracted_contact != "-1":
                print(
                    f"⚠️ Contact person '{extracted_contact}' not in known list, keeping as None"
                )
            else:
                print("❌ Contact validation: No known contact found")

        except Exception as error:
            print(f"Error validating contact person: {error}")
    else:
        print(
            f"ℹ️ Contact validation: Already set to '{state['visitor_profile']['contact_person']}'"
        )

    return state


def check_visitor_profile_condition(
    state: State,
) -> Literal["complete", "not_complete"]:
    """
    Simple conditional function that only checks if profile is complete.
    """
    # Check if all required fields are completed
    profile = state["visitor_profile"]
    all_fields_complete = all(
        [
            profile["name"] is not None and profile["name"] != "-1",
            profile["purpose"] is not None and profile["purpose"] != "-1",
            profile["contact_person"] is not None and profile["contact_person"] != "-1",
            profile["threat_level"] is not None and profile["threat_level"] != "-1",
            profile["affiliation"] is not None and profile["affiliation"] != "-1",
        ]
    )

    # Set id_verified based on completeness
    if all_fields_complete:
        state["visitor_profile"]["id_verified"] = True
        return "complete"
    else:
        state["visitor_profile"]["id_verified"] = False
        return "not_complete"


def question_visitor(state: State) -> State:
    """
    Ask specific questions for missing visitor profile fields.
    """
    # Define specific questions for each field
    known_contacts_list = ", ".join(CONTACTS.keys())
    field_questions = {
        "name": "What is your name?",
        "purpose": "What is the purpose of your visit today?",
        "contact_person": f"Who is your contact? (Known contacts include: {known_contacts_list})",
        "threat_level": "Are you carrying any restricted items or have any security concerns I should know about?",
        "affiliation": "What company or organization are you with?",
    }

    # Find the first missing field that needs to be completed
    fields_to_check = [
        "name",
        "purpose",
        "contact_person",
        "threat_level",
        "affiliation",
    ]

    for field in fields_to_check:
        if (
            state["visitor_profile"][field] is None
            or state["visitor_profile"][field] == "-1"
        ):
            # Ask specific question for this missing field
            question_text = field_questions[field]
            question = AIMessage(content=question_text)
            state["messages"].append(question)
            print(f"🤔 Asking for missing field: {field}")
            return state

    # Fallback if somehow all fields are filled but we're still here
    question = AIMessage(content="Can you tell me more about yourself?")
    state["messages"].append(question)
    return state
