from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from ..core.state import State
from ..data.contacts import CONTACTS
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_main
from ..utils.prompt_manager import prompt_manager


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
            # Get field description from prompt manager
            field_description = prompt_manager.get_field_description(field)

            # Create extraction prompt using prompt manager
            prompt_value = prompt_manager.invoke_prompt(
                "processing",
                "extract_field",
                field=field,
                field_description=field_description,
                conversation_text=conversation_text,
            )

            try:
                response = llm_main.invoke(prompt_value)
                extracted_value = extract_answer_from_thinking_model(response)

                print(extracted_value)

                # Additional cleaning to ensure we get only the value
                # Get removal prefixes from prompt manager
                prefixes_to_remove = prompt_manager.get_extraction_prefixes(field)

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

        # Create contact validation prompt using prompt manager
        known_contacts_list = "\n".join([f"- {contact}" for contact in CONTACTS.keys()])

        prompt_value = prompt_manager.invoke_prompt(
            "processing",
            "validate_contact",
            known_contacts=known_contacts_list,
            conversation_text=conversation_text,
        )

        try:
            response = llm_main.invoke(prompt_value)
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
    # Get questions from prompt manager
    known_contacts_list = ", ".join(CONTACTS.keys())

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
            # Get question for this field from prompt manager
            if field == "contact_person":
                question_text = prompt_manager.get_field_question(
                    field, known_contacts=known_contacts_list
                )
            else:
                question_text = prompt_manager.get_field_question(field)

            question = AIMessage(content=question_text)
            state["messages"].append(question)
            print(f"🤔 Asking for missing field: {field}")
            return state

    # Fallback if somehow all fields are filled but we're still here
    fallback_question = prompt_manager.get_field_data("input_validation")[
        "fallback_question"
    ]
    question = AIMessage(content=fallback_question)
    state["messages"].append(question)
    return state
