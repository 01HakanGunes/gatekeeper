from typing import Literal
import json
import os
from typing import cast
from src.core.state import VisionSchema
from langchain_core.messages import HumanMessage, SystemMessage
from src.core.state import State
from src.utils.llm_utilities import analyze_image_with_prompt
from config.settings import MAX_HUMAN_MESSAGES, SHORTEN_KEEP_MESSAGES
from src.utils.extraction import extract_answer_from_thinking_model
from models.llm_config import (
    llm_summary,
    llm_session_json,
    llm_validation_json,
)
from src.utils.prompt_manager import prompt_manager


def receive_input(state: State) -> State:
    """
    Handle user input with validation and conversation history display.
    """
    # Print conversation history
    messages = state["messages"]
    print("\n" + "=" * 50)
    print("📜 CONVERSATION HISTORY")
    print("=" * 50)

    for i, message in enumerate(messages, 1):
        if hasattr(message, "type") and hasattr(message, "content"):
            if message.type == "system":
                print(f"{i}. 🔧 System: {message.content}")
            elif message.type == "human":
                print(f"{i}. 👤 User: {message.content}")
            elif message.type == "ai":
                print(f"{i}. 🤖 Agent: {message.content}")
            else:
                print(f"{i}. {message.type}: {message.content}")

    print("=" * 50)

    # Display the most recent AI message if one exists
    if messages and hasattr(messages[-1], "type") and messages[-1].type == "ai":
        print(f"Agent: {messages[-1].content}")

    # Basic check for empty input
    user_input = state.get("user_input", "")
    state["invalid_input"] = False

    if not user_input.strip():
        print("❌ Input validation: Empty input detected")
        state["invalid_input"] = True
        empty_message = prompt_manager.get_field_data("input_validation")[
            "empty_input_message"
        ]
        print(f"Agent: {empty_message}")

        return state

    # Create a validation prompt using prompt manager
    try:
        # Use prompt manager to get validation prompt
        prompt_value = prompt_manager.invoke_prompt(
            "input", "validate_input", user_input=user_input
        )

        response = llm_validation_json.invoke(prompt_value)

        # Extract the response content (handling thinking models)
        result = extract_answer_from_thinking_model(response)

        # Clean the response - sometimes LLM adds extra text
        if "valid" in result and "unrelated" not in result:
            print("✅ Input validation: Input is valid")
            # Valid input - add to messages and break the loop
            state["messages"].append(HumanMessage(content=user_input))

            # Analyze the frame and extract the json schema accordingly
            vision_data = analyze_image_with_prompt(
                "visitor.png", "analyze_image_threat_json", "vision_schema"
            )

            # Delete the visitor.png file after analysis
            try:
                if os.path.exists("visitor.png"):
                    os.remove("visitor.png")
                    print("🗑️ Cleaned up visitor.png file")
            except Exception as e:
                print(f"⚠️ Failed to delete visitor.png: {e}")

            state["vision_schema"] = cast(VisionSchema, vision_data)

            # Check the face_detected field, if no face print a request to show up on the camera
            vision_schema = state.get("vision_schema")
            face_detected = False
            if isinstance(vision_schema, dict):
                face_detected = vision_schema.get("face_detected", False)
                details_face_debug = vision_schema.get("details", "details are not there for vision data!")
                print(details_face_debug)
            if not face_detected:
                print(
                    "❌ No face detected. Please show up on the camera and try again."
                )

                state["invalid_input"] = True
                return state
            else:
                print("✅ Face detected in the image.")
        elif "unrelated" in result:
            print("❌ Input validation: Input is unrelated/invalid")
            invalid_message = prompt_manager.get_field_data("input_validation")[
                "invalid_input_message"
            ]
            print(f"Agent: {invalid_message}")

            state["invalid_input"] = True
            return state
        else:
            # Default to valid if unclear response
            print("⚠️ Input validation: Unclear response, defaulting to valid")
            state["messages"].append(HumanMessage(content=user_input))

    except Exception as error:
        print(f"⚠️ Input validation error: {error}")
        # If validation fails, default to valid to avoid blocking legitimate users
        state["messages"].append(HumanMessage(content=user_input))

    # Print current visitor profile status after each user input for debugging
    print("\n📋 Visitor Profile Status (after user input):")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state

def detect_session(state: State) -> Literal["same", "new"]:
    """
    Detects if the current input is from a new visitor or the same visitor using structured JSON output.
    Uses LLM to analyze conversation patterns and detect session changes.
    """
    messages = state["messages"]

    # Get the last user message and some conversation context
    last_user_message = messages[-1].content

    # Get recent conversation context (last 6 messages to keep it manageable)
    recent_messages = messages[-6:] if len(messages) >= 6 else messages[1:]
    conversation_context = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in recent_messages
            if hasattr(msg, "type") and hasattr(msg, "content")
        ]
    )

    # Get JSON schema from prompt manager
    session_schema = prompt_manager.get_schema("session_schema")

    # Format visitor profile for prompt
    visitor_profile = state.get("visitor_profile", {})
    visitor_profile_text = "\n".join(
        [
            f"- {field.replace('_', ' ').title()}: {value}"
            for field, value in visitor_profile.items()
        ]
    )

    # Create session detection prompt using prompt manager with JSON schema and visitor profile
    try:
        prompt_value = prompt_manager.invoke_prompt(
            "input",
            "detect_session_json",
            conversation_context=conversation_context,
            visitor_profile_text=visitor_profile_text,
            last_user_message=last_user_message,
            json_schema=json.dumps(session_schema, indent=2),
        )

        response = llm_session_json.invoke(prompt_value)

        # Handle response content properly
        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

        content = extract_answer_from_thinking_model(content)

        if isinstance(content, str):
            session_data = json.loads(content)
        else:
            raise ValueError("Response content is not a string")

        session_type = session_data.get("session_type", "same").lower()
        confidence = session_data.get("confidence", 0.0)
        indicators = session_data.get("indicators", [])
        greeting_detected = session_data.get("greeting_detected", False)

        # Validate session type
        if session_type in ["new", "same"]:
            print(
                f"🔍 Session detection: {session_type.upper()} (confidence: {confidence:.2f})"
            )
            if indicators:
                print(f"📝 Indicators: {', '.join(indicators)}")
            if greeting_detected:
                print("👋 New greeting/introduction detected")
            return session_type
        else:
            print("⚠️ Invalid session type in JSON response, defaulting to same session")
            return "same"

    except (json.JSONDecodeError, KeyError, Exception) as error:
        print(f"⚠️ JSON session detection failed: {error}")
        # Default to same session if JSON detection fails
        print("🔄 Session detection: Defaulting to same session")
        return "same"


def check_context_length(state: State) -> Literal["over_limit", "under_limit"]:
    """
    Check if conversation context is too long by counting human messages.

    Limits conversation to x human messages to keep context manageable.
    """
    # Count human messages
    human_message_count = 0
    for message in state["messages"]:
        if hasattr(message, "type") and message.type == "human":
            human_message_count += 1

    # Check against threshold
    if human_message_count > MAX_HUMAN_MESSAGES:
        print(
            f"⚠️ Context length: {human_message_count} human messages exceeds limit of {MAX_HUMAN_MESSAGES}"
        )
        return "over_limit"

    print(
        f"✅ Context length: {human_message_count}/{MAX_HUMAN_MESSAGES} human messages"
    )
    return "under_limit"


def summarize(state: State) -> State:
    """
    Manage conversation history using either summarization or shortening strategy.

    Two modes:
    1. "summarize": Use AI to create a summary while keeping recent messages
    2. "shorten": Simply keep the last N messages without AI processing
    """
    from config.settings import CURRENT_HISTORY_MODE

    messages = state["messages"]

    # Skip if too few messages
    if len(messages) < 8:
        return state

    print(f"🔄 History management mode: {CURRENT_HISTORY_MODE}")

    if CURRENT_HISTORY_MODE == "shorten":
        return _shorten_history(state)
    else:  # default to summarize mode
        return _summarize_history(state)


def _shorten_history(state: State) -> State:
    """
    Shorten conversation history by keeping only the last N messages.
    This is faster and doesn't require LLM processing.
    """
    messages = state["messages"]

    # Find the system message to preserve
    system_message = next(
        (
            m
            for m in messages
            if hasattr(m, "type")
            and m.type == "system"
            and "You are a helpful assistant" in m.content
        ),
        None,
    )

    # Keep only the last SHORTEN_KEEP_MESSAGES messages
    recent_messages = messages[-SHORTEN_KEEP_MESSAGES:]

    # Create new message list
    new_messages = []
    if system_message:
        new_messages.append(system_message)

    # Add a note about shortened history
    new_messages.append(
        SystemMessage(
            content="[HISTORY SHORTENED: Earlier conversation truncated to manage context length]"
        )
    )

    # Add recent messages
    new_messages.extend(recent_messages)

    # Clear existing messages by popping them one by one
    messages_to_remove = len(state["messages"])
    for _ in range(messages_to_remove):
        if len(state["messages"]) > 0:
            state["messages"].pop(0)

    # Add new messages one by one
    for message in new_messages:
        state["messages"].append(message)

    print(
        f"Shortened conversation from {len(messages)} to {len(new_messages)} messages"
    )

    return state


def _summarize_history(state: State) -> State:
    """
    Summarize conversation history using AI to preserve important context.
    This preserves more semantic information but requires LLM processing.
    """
    messages = state["messages"]

    # Keep initial system message and 4 most recent messages intact
    recent_messages = messages[-4:]
    system_message = next(
        (
            m
            for m in messages
            if hasattr(m, "type")
            and m.type == "system"
            and "You are a helpful assistant" in m.content
        ),
        None,
    )

    # Prepare conversation for summarization
    conversation_to_summarize = messages[1:-4] if system_message else messages[:-4]
    conversation_text = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in conversation_to_summarize
            if hasattr(msg, "type") and hasattr(msg, "content")
        ]
    )

    try:
        # Use prompt manager for summarization
        prompt_value = prompt_manager.invoke_prompt(
            "input", "summarize_conversation", conversation_text=conversation_text
        )

        # Use the centralized summary LLM
        response = llm_summary.invoke(prompt_value)
        summary = extract_answer_from_thinking_model(response)

        # Create a new condensed message list
        new_messages = []
        if system_message:
            new_messages.append(system_message)

        # Add summary as system message
        new_messages.append(SystemMessage(content=f"[CONVERSATION SUMMARY: {summary}]"))

        # Add recent messages
        new_messages.extend(recent_messages)

        # Clear existing messages by popping them one by one
        messages_to_remove = len(state["messages"])
        for _ in range(messages_to_remove):
            if len(state["messages"]) > 0:
                state["messages"].pop(0)

        # Add new messages one by one
        for message in new_messages:
            state["messages"].append(message)

        print(
            f"✅ Summarized conversation from {len(messages)} to {len(new_messages)} messages"
        )

        return state

    except Exception as error:
        print(f"⚠️ Summarization error: {error}")
        # On error, don't modify messages
        return state


def _clear_state(state: State):
    """
    Helper function to clear the entire state for a new visitor/session.
    """
    # Clear messages
    state["messages"].clear()
    # Reset visitor profile
    state["visitor_profile"] = {
        "name": None,
        "purpose": None,
        "contact_person": None,
        "threat_level": None,
        "affiliation": None,
        "id_verified": None,
    }
    # Reset decision fields
    state["decision"] = ""
    state["decision_confidence"] = None
    state["decision_reasoning"] = None


def reset_conversation(state: State) -> State:
    """
    Reset conversation for a new visitor by clearing the entire state.
    """
    # Keep reference to the new visitor's message
    new_visitor_message = state["messages"][-1] if state["messages"] else None

    # Clear the whole state
    _clear_state(state)

    # Create new message list with initial system message and new visitor's message
    system_msg_content = prompt_manager.format_prompt("input", "system_message")
    state["messages"].append(SystemMessage(content=system_msg_content))
    if new_visitor_message:
        state["messages"].append(new_visitor_message)

    print("🔄 Reset conversation: Properly cleared state for new visitor")
    return state
