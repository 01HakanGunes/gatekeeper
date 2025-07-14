from typing import Literal
import json
from langchain_core.messages import HumanMessage, AIMessage
from ..core.state import State
from data.contacts import CONTACTS
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_main_json, llm_validation_json
from ..utils.prompt_manager import prompt_manager


def check_visitor_profile_node(state: State) -> State:
    """
    Node function that performs LLM extraction and updates the visitor profile using structured JSON output.
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
    ]

    # Check which fields are missing
    missing_fields = [
        field for field in fields_to_extract if state["visitor_profile"][field] is None
    ]

    if not missing_fields:
        print("✅ All fields already extracted")
        return state

    # Get JSON schema template from prompt manager and customize for missing fields
    base_schema = prompt_manager.get_schema("extraction_schema")
    extraction_schema = {
        "extracted_fields": {
            field: "string or null (if not found)" for field in missing_fields
        },
        "confidence": {field: "number between 0 and 1" for field in missing_fields},
    }

    # Create unified extraction prompt using prompt manager
    fields_descriptions = {
        field: prompt_manager.get_field_description(field) for field in missing_fields
    }

    prompt_value = prompt_manager.invoke_prompt(
        "processing",
        "extract_multiple_fields_json",
        fields_to_extract=", ".join(missing_fields),
        fields_descriptions=json.dumps(fields_descriptions, indent=2),
        conversation_text=conversation_text,
        json_schema=json.dumps(extraction_schema, indent=2),
    )

    try:
        response = llm_main_json.invoke(prompt_value)
        # Handle response content properly
        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

        if isinstance(content, str):
            extraction_data = json.loads(content)
        else:
            raise ValueError("Response content is not a string")

        # Update profile with extracted fields
        extracted_fields = extraction_data.get("extracted_fields", {})
        confidence_scores = extraction_data.get("confidence", {})

        for field in missing_fields:
            if field in extracted_fields:
                value = extracted_fields[field]
                confidence = confidence_scores.get(field, 0.0)

                # Validate and clean the extracted value
                if value and value != "-1" and value.lower() != "null":
                    # Additional cleaning
                    value = str(value).strip("\"'")

                    # Take only the first few words if response is too long
                    words = value.split()
                    if len(words) > 3:
                        value = " ".join(words[-3:])

                    state["visitor_profile"][field] = value
                    print(
                        f"✅ Extracted {field}: '{value}' (confidence: {confidence:.2f})"
                    )
                else:
                    print(f"❌ Could not extract {field}")

    except (json.JSONDecodeError, KeyError, Exception) as error:
        print(f"⚠️ JSON extraction failed: {error}")
        # Set fields as None if JSON extraction fails
        for field in missing_fields:
            if state["visitor_profile"][field] is None:
                print(f"❌ Could not extract {field}")

    # Print current visitor profile status for debugging
    print(f"\n📋 Current Visitor Profile:")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state


def validate_contact_person(state: State) -> State:
    """
    Dedicated node for extracting and validating contact persons against known contacts list using JSON output.
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

        # Create contact validation prompt using prompt manager with JSON schema
        known_contacts_list = list(CONTACTS.keys())

        # Get JSON schema from prompt manager
        validation_schema = prompt_manager.get_schema("contact_validation_schema")

        prompt_value = prompt_manager.invoke_prompt(
            "processing",
            "validate_contact_json",
            known_contacts=json.dumps(known_contacts_list),
            conversation_text=conversation_text,
            json_schema=json.dumps(validation_schema, indent=2),
        )

        try:
            response = llm_validation_json.invoke(prompt_value)
            # Handle response content properly
            if hasattr(response, "content"):
                content = response.content
            else:
                content = str(response)

            if isinstance(content, str):
                validation_data = json.loads(content)
            else:
                raise ValueError("Response content is not a string")

            extracted_contact = validation_data.get("extracted_contact", "")
            matched_contact = validation_data.get("matched_contact")
            confidence = validation_data.get("confidence", 0.0)
            is_valid = validation_data.get("is_valid_contact", False)

            # Only set contact_person if it's a valid contact from our list
            if is_valid and matched_contact and matched_contact in CONTACTS:
                state["visitor_profile"]["contact_person"] = matched_contact
                print(
                    f"✅ Contact validation: Matched '{matched_contact}' (confidence: {confidence:.2f})"
                )
            elif extracted_contact and extracted_contact != "-1":
                print(
                    f"⚠️ Contact person '{extracted_contact}' not in known list, keeping as None (confidence: {confidence:.2f})"
                )
            else:
                print("❌ Contact validation: No contact person found in conversation")

        except (json.JSONDecodeError, KeyError, Exception) as error:
            print(f"⚠️ JSON contact validation failed: {error}")
            # Keep contact_person as None if JSON validation fails
            print("❌ Contact validation: Failed to process contact information")
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
