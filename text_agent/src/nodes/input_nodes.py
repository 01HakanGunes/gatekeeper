from typing import Literal
import json
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..core.state import State
from config.settings import MAX_HUMAN_MESSAGES
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_summary, llm_session_json
from ..utils.prompt_manager import prompt_manager


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

    # Loop until we get valid input
    while True:
        user_input = input("User: ")  # Wait for terminal input

        # Basic check for empty input
        if not user_input.strip():
            print("❌ Input validation: Empty input detected")
            empty_message = prompt_manager.get_field_data("input_validation")[
                "empty_input_message"
            ]
            print(f"Agent: {empty_message}")
            continue  # Ask for input again

        # Create a validation prompt using prompt manager
        try:
            # Use prompt manager to get validation prompt
            prompt_value = prompt_manager.invoke_prompt(
                "input", "validate_input", user_input=user_input
            )

            # Use the centralized validation LLM
            from models.llm_config import llm_validation

            response = llm_validation.invoke(prompt_value)

            # Extract the response content (handling thinking models)
            result = extract_answer_from_thinking_model(response).lower()

            # Clean the response - sometimes LLM adds extra text
            if "valid" in result and "unrelated" not in result:
                print("✅ Input validation: Input is valid")
                # Valid input - add to messages and break the loop
                state["messages"].append(HumanMessage(content=user_input))
                break
            elif "unrelated" in result:
                print("❌ Input validation: Input is unrelated/invalid")
                invalid_message = prompt_manager.get_field_data("input_validation")[
                    "invalid_input_message"
                ]
                print(f"Agent: {invalid_message}")
                continue  # Ask for input again
            else:
                # Default to valid if unclear response
                print("⚠️ Input validation: Unclear response, defaulting to valid")
                state["messages"].append(HumanMessage(content=user_input))
                break

        except Exception as error:
            print(f"⚠️ Input validation error: {error}")
            # If validation fails, default to valid to avoid blocking legitimate users
            state["messages"].append(HumanMessage(content=user_input))
            break

    # Print current visitor profile status after each user input for debugging
    print(f"\n📋 Visitor Profile Status (after user input):")
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

    # Create session detection prompt using prompt manager with JSON schema
    try:
        prompt_value = prompt_manager.invoke_prompt(
            "input",
            "detect_session_json",
            conversation_context=conversation_context,
            last_user_message=last_user_message,
            json_schema=json.dumps(session_schema, indent=2),
        )

        response = llm_session_json.invoke(prompt_value)

        # Handle response content properly
        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

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
    Summarize conversation history to reduce context length while preserving key information.
    Keeps recent messages intact while condensing older conversation history.
    """
    messages = state["messages"]

    # Skip if too few messages
    if len(messages) < 8:
        return state

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
            f"🔄 Summarized conversation from {len(messages)} to {len(new_messages)} messages"
        )

        return state

    except Exception as error:
        print(f"⚠️ Summarization error: {error}")
        # On error, don't modify messages
        return state


def reset_conversation(state: State) -> State:
    """
    Reset conversation for a new visitor by clearing message history and visitor profile.
    """
    from ..core.state import VisitorProfile

    # Keep reference to the new visitor's message
    new_visitor_message = state["messages"][-1]

    # Create new message list with initial system message and new visitor's message
    system_msg_content = prompt_manager.format_prompt("input", "system_message")
    new_messages = [
        SystemMessage(content=system_msg_content),
        new_visitor_message,
    ]

    # Reset visitor profile
    new_visitor_profile: VisitorProfile = {
        "name": None,
        "purpose": None,
        "contact_person": None,
        "threat_level": None,
        "affiliation": None,
        "id_verified": None,
    }

    # Clear existing messages by popping them one by one
    messages_to_remove = len(state["messages"])
    for _ in range(messages_to_remove):
        if len(state["messages"]) > 0:
            state["messages"].pop(0)

    # Add new messages
    for message in new_messages:
        state["messages"].append(message)

    # Update visitor profile
    state["visitor_profile"] = new_visitor_profile

    print("🔄 Reset conversation: Properly cleared message history for new visitor")

    return state
