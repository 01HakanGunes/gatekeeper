#!/usr/bin/env python3
"""
Test script to verify the new history management modes work correctly.
"""

import sys
import os

# Add the text_agent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.core.state import State
from src.nodes.input_nodes import summarize
import config.settings as settings


def create_test_state_with_many_messages():
    """Create a test state with many messages to trigger history management."""
    messages = [
        SystemMessage(
            content="You are a helpful assistant at the gate. Ask necessary questions and decide on access."
        ),
        HumanMessage(content="Hello, I'm here to visit someone"),
        AIMessage(content="Welcome! Can you please tell me your name?"),
        HumanMessage(content="My name is John Smith"),
        AIMessage(content="Thank you, John. What is the purpose of your visit?"),
        HumanMessage(content="I'm here for a business meeting"),
        AIMessage(content="Who are you here to see?"),
        HumanMessage(content="I'm here to see Sarah Johnson"),
        AIMessage(content="What company are you from?"),
        HumanMessage(content="I'm from TechCorp Solutions"),
        AIMessage(content="Do you have any identification with you?"),
        HumanMessage(content="Yes, I have my driver's license"),
        AIMessage(content="Thank you for the information"),
        HumanMessage(content="Is there anything else you need?"),
    ]

    return {
        "messages": messages,
        "visitor_profile": {
            "name": "John Smith",
            "purpose": "business meeting",
            "contact_person": "Sarah Johnson",
            "threat_level": None,
            "affiliation": "TechCorp Solutions",
            "id_verified": None,
        },
        "decision": "",
        "decision_confidence": None,
        "decision_reasoning": None,
    }


def test_summarize_mode():
    """Test the summarize mode."""
    print("\n" + "=" * 60)
    print("🧪 TESTING SUMMARIZE MODE")
    print("=" * 60)

    # Set summarize mode
    settings.CURRENT_HISTORY_MODE = "summarize"

    # Create test state
    state = create_test_state_with_many_messages()
    original_count = len(state["messages"])
    print(f"📊 Original message count: {original_count}")

    # Run summarize function
    result_state = summarize(state)
    new_count = len(result_state["messages"])
    print(f"📊 New message count: {new_count}")

    # Print the resulting messages
    print("\n📋 Resulting messages:")
    for i, msg in enumerate(result_state["messages"], 1):
        print(f"  {i}. {msg.type}: {msg.content[:100]}...")


def test_shorten_mode():
    """Test the shorten mode."""
    print("\n" + "=" * 60)
    print("🧪 TESTING SHORTEN MODE")
    print("=" * 60)

    # Set shorten mode
    settings.CURRENT_HISTORY_MODE = "shorten"

    # Create test state
    state = create_test_state_with_many_messages()
    original_count = len(state["messages"])
    print(f"📊 Original message count: {original_count}")

    # Run summarize function (which will use shorten mode)
    result_state = summarize(state)
    new_count = len(result_state["messages"])
    print(f"📊 New message count: {new_count}")

    # Print the resulting messages
    print("\n📋 Resulting messages:")
    for i, msg in enumerate(result_state["messages"], 1):
        print(f"  {i}. {msg.type}: {msg.content[:100]}...")


def test_few_messages():
    """Test that the function skips processing when there are few messages."""
    print("\n" + "=" * 60)
    print("🧪 TESTING FEW MESSAGES (SHOULD SKIP)")
    print("=" * 60)

    # Create a state with few messages
    messages = [
        SystemMessage(content="You are a helpful assistant at the gate."),
        HumanMessage(content="Hello"),
        AIMessage(content="Hi! How can I help you?"),
    ]

    state = {
        "messages": messages,
        "visitor_profile": {},
        "decision": "",
        "decision_confidence": None,
        "decision_reasoning": None,
    }

    original_count = len(state["messages"])
    print(f"📊 Original message count: {original_count}")

    # Run summarize function
    result_state = summarize(state)
    new_count = len(result_state["messages"])
    print(f"📊 New message count: {new_count}")

    if original_count == new_count:
        print("✅ Correctly skipped processing for few messages")
    else:
        print("❌ Unexpectedly processed few messages")


if __name__ == "__main__":
    print("🧪 HISTORY MANAGEMENT MODES TEST")
    print("=" * 60)

    try:
        test_few_messages()
        test_shorten_mode()
        test_summarize_mode()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
