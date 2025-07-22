from typing import Literal
import json
from langchain_core.messages import HumanMessage, AIMessage
from src.core.state import State
from data.contacts import CONTACTS
from src.utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_profiler_json
from src.utils.prompt_manager import prompt_manager
from models.llm_config import llm_vision_json


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

    # Define fields to extract (excluding threat_level, which is handled by vision analysis)
    fields_to_extract = [
        "name",
        "purpose",
        "contact_person",
        "affiliation",
    ]

    # Check which fields are missing (excluding threat_level)
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
        response = llm_profiler_json.invoke(prompt_value)
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

                    # For contact_person, keep the full name, for others limit to 3 words
                    if field != "contact_person":
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


def analyze_threat_level_node(state: State) -> State:
    """
    Node function that performs vision analysis to determine the threat level of the visitor.
    """
    # Only run if threat_level is still missing or None
    if state["visitor_profile"].get("threat_level") in [None, "-1", "low", "medium"]:
        from src.utils.camera import image_file_to_base64

        image_path = "visitor.png"
        print("Using existing photo for vision analysis.")
        # Convert image to base64
        try:
            image_b64 = image_file_to_base64(image_path)
        except Exception as e:
            print(f"⚠️ Could not convert image to base64: {e}")
            image_b64 = None

        if image_b64:
            # Use prompt_manager to generate the vision prompt, including the schema
            vision_schema = prompt_manager.get_schema("vision_schema")
            vision_prompt = prompt_manager.invoke_prompt(
                "vision",
                "analyze_image_threat_json",
                json_schema=json.dumps(vision_schema, indent=2),
            )
            # Prepare multimodal message as per LLM API requirements
            image_part = {
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{image_b64}",
            }
            text_part = {"type": "text", "text": vision_prompt}
            message = {
                "role": "user",
                "content": [image_part, text_part],
            }
            try:
                response = llm_vision_json.invoke([message])
                content = (
                    response.content if hasattr(response, "content") else str(response)
                )
                # If response is a list, join to string
                if isinstance(content, list):
                    content = "\n".join(str(x) for x in content)
                try:
                    vision_data = json.loads(content)
                except Exception:
                    # Try to extract JSON from text if LLM returns extra text
                    import re

                    match = re.search(r"\{.*\}", content, re.DOTALL)
                    if match:
                        vision_data = json.loads(match.group(0))
                    else:
                        raise ValueError("No valid JSON found in LLM response")
                threat_level = vision_data.get("threat_level", "-1")
                state["visitor_profile"]["threat_level"] = threat_level
                print(f"🔍 Vision analysis result: {vision_data}")
            except Exception as e:
                print(f"⚠️ Vision LLM response error: {e}")
        else:
            print("⚠️ Skipping vision analysis due to missing image base64.")

    # Print current visitor profile status for debugging
    print(f"\n📋 Current Visitor Profile (after threat analysis):")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state


def validate_contact_person(state: State) -> State:
    """
    Simplified node for validating the already-extracted contact person against known contacts list.
    No LLM call needed - pure validation logic.
    """
    contact_person = state["visitor_profile"]["contact_person"]

    # If no contact person was extracted, keep as None
    if not contact_person or contact_person == "-1":
        print("❌ Contact validation: No contact person found in conversation")
        state["visitor_profile"]["contact_person"] = None
        return state

    # Check if the extracted contact person matches our known contacts
    if contact_person in CONTACTS:
        print(f"✅ Contact validation: '{contact_person}' is valid")
        # Keep the validated contact person
        state["visitor_profile"]["contact_person"] = contact_person
    else:
        # Try case-insensitive matching for better user experience
        contact_lower = contact_person.lower()
        matched_contact = None

        for known_contact in CONTACTS.keys():
            if known_contact.lower() == contact_lower:
                matched_contact = known_contact
                break

        if matched_contact:
            print(
                f"✅ Contact validation: Matched '{matched_contact}' (case corrected)"
            )
            state["visitor_profile"]["contact_person"] = matched_contact
        else:
            print(
                f"⚠️ Contact person '{contact_person}' not in known list, keeping as None"
            )
            state["visitor_profile"]["contact_person"] = None

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
