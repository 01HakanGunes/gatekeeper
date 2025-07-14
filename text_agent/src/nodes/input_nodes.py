from typing import Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..core.state import State
from config.settings import MAX_HUMAN_MESSAGES
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_validation, llm_session, llm_summary


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
            print(
                "Agent: I didn't understand that. Please provide relevant information for your visit. I need to know your name, purpose of visit, company/organization, and any security-related information."
            )
            continue  # Ask for input again

        # Create a validation prompt for the LLM
        validation_prompt = f"""You are an input validator for a security gate system. Your job is to determine if user input is relevant and appropriate for a security checkpoint conversation.

VALID inputs include:
- Personal information (names, company names, purposes)
- Responses to security questions
- Regular conversations
- Questions about the facility or visit process
- Explanations about their visit purpose
- Description of their belongings, visuals for thread assessment, behaviour (i am angry/chill/funny)

INVALID inputs include:
- Complete gibberish or random characters
- Curse words
- Spam or repetitive nonsense
- Completely irrelevant topics (sports, weather, unrelated subjects)

Respond with ONLY one word:
- "valid" if the input is appropriate for a security checkpoint
- "unrelated" if the input is gibberish, spam, offensive, or completely irrelevant

Input to validate: "{user_input}"

Response:"""

        try:
            # Use the centralized validation LLM
            response = llm_validation.invoke([HumanMessage(content=validation_prompt)])

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
                print(
                    "Agent: I didn't understand that. Please provide relevant information for your visit. I need to know your name, purpose of visit, company/organization, and any security-related information."
                )
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
    Detects if the current input is from a new visitor or the same visitor.
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

    # Create session detection prompt (prioritize continuing the same session if the session change is not explicit)
    session_prompt = f"""You are a session detector for a security gate system. Determine if the latest message indicates a NEW visitor has arrived or if it's the SAME visitor continuing the conversation. For most case if not apperent, choose SAME visitor.

NEW VISITOR indicators:
- Introductions with different names ("Hi, I'm John" when previous visitor was "Mary")
- Greetings that suggest a fresh start ("Hello", "Hi there", "Good morning" at unexpected times)
- References to being a different person

SAME VISITOR indicators:
- If not one of the new visitor indicators (for most cases).

CONVERSATION CONTEXT:
{conversation_context}

LATEST MESSAGE: {last_user_message}

Respond with ONLY one word:
- "new" if this appears to be a new visitor
- "same" if this is the same visitor continuing

Response:"""

    try:
        response = llm_session.invoke([HumanMessage(content=session_prompt)])
        result = extract_answer_from_thinking_model(response).lower()

        if "new" in result and "same" not in result:
            print("🆕 Session detection: New visitor detected")
            return "new"
        elif "same" in result:
            print("🔄 Session detection: Same visitor continuing")
            return "same"
        else:
            # Default to same session if unclear
            print("⚠️ Session detection: Unclear response, defaulting to same session")
            return "same"

    except Exception as error:
        print(f"⚠️ Session detection error: {error}")
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

    summary_prompt = f"""Summarize the following conversation between a security gate assistant and a visitor.
Focus ONLY on:
1. Key visitor information (name, purpose, affiliation)
2. Security-relevant details
3. Important context needed to continue the conversation

Keep the summary concise and focused on essential information.

Conversation:
{conversation_text}

Summary:"""

    try:
        # Use the centralized summary LLM
        response = llm_summary.invoke([HumanMessage(content=summary_prompt)])
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
    new_messages = [
        SystemMessage(
            content="You are a helpful assistant at the gate. Ask necessary questions and decide on access."
        ),
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
