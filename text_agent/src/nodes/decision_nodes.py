from typing import Literal
import json
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from src.core.state import State
from data.contacts import CONTACTS
from src.utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_email, llm_decision_json
from src.tools.communication import tools
from src.utils.prompt_manager import prompt_manager


def make_decision(state: State) -> State:
    """
    Make a security decision based on visitor profile and conversation context.
    Uses LLM to analyze all information and choose appropriate action with structured JSON output.
    """
    # Get visitor profile and conversation context
    profile = state["visitor_profile"]
    messages = state["messages"]
    if state["vision_schema"] is None:
        raise ValueError("Vision schema is missing")
    threat_level_value = state["vision_schema"]["threat_level"]

    if threat_level_value == "high":
        state["decision"] = "call_security"
    # Get recent conversation context for decision making
    conversation_text = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in messages[-10:]  # Last 10 messages for context
            if hasattr(msg, "type") and hasattr(msg, "content")
        ]
    )

    # Define available decisions from prompt manager
    decisions = prompt_manager.get_data("decision", "available_decisions")

    # Create decision prompt using prompt manager with JSON schema
    decisions_list = "\n".join(
        [
            f"{i+1}. {decision_id} - {description}"
            for i, (decision_id, description) in enumerate(decisions.items())
        ]
    )

    # Get JSON schema from prompt manager
    decision_schema = prompt_manager.get_schema("decision_schema")

    prompt_value = prompt_manager.invoke_prompt(
        "decision",
        "make_decision_json",
        profile_name=profile["name"],
        profile_purpose=profile["purpose"],
        profile_contact_person=profile["contact_person"],
        profile_threat_level=profile["threat_level"],
        profile_affiliation=profile["affiliation"],
        profile_id_verified=profile["id_verified"],
        decisions_list=decisions_list,
        conversation_text=conversation_text,
        json_schema=json.dumps(decision_schema, indent=2),
    )

    try:
        response = llm_decision_json.invoke(prompt_value)

        # Handle response content properly - it might be a string or have .content attribute
        if hasattr(response, "content"):
            content = response.content
        else:
            content = str(response)

        content = extract_answer_from_thinking_model(response)

        # Ensure content is a string for JSON parsing
        if isinstance(content, str):
            decision_data = json.loads(content)
        else:
            raise ValueError("Response content is not a string")

        # Validate decision is one of the allowed options
        decision_result = decision_data.get("decision", "").strip().lower()
        confidence = decision_data.get("confidence", 0.0)
        reasoning = decision_data.get("reasoning", "No reasoning provided")

        if decision_result in decisions.keys():
            state["decision"] = decision_result
            state["decision_confidence"] = confidence
            state["decision_reasoning"] = reasoning

            # Add appropriate response message from prompt manager
            decision_messages = prompt_manager.get_data("decision", "decision_messages")
            message_content = (
                f"{decision_messages[decision_result]} (Confidence: {confidence:.2f})"
            )
            state["messages"].append(AIMessage(content=message_content))

            print(f"🔒 Security Decision: {decision_result.upper()}")
            print(f"📊 Confidence: {confidence:.2f}")
            print(f"📋 Reason: {reasoning}")

            # Log threat indicators if any
            if (
                "threat_indicators" in decision_data
                and decision_data["threat_indicators"]
            ):
                print(
                    f"⚠️ Threat Indicators: {', '.join(decision_data['threat_indicators'])}"
                )

            return state

        # Fallback if invalid decision
        print(
            "⚠️ Decision making: Invalid decision in JSON response, defaulting to deny_request"
        )
        state["decision"] = "deny_request"
        state["decision_confidence"] = 0.0
        fallback_message = prompt_manager.get_data("decision", "fallback_messages")[
            "unclear_decision"
        ]
        state["messages"].append(AIMessage(content=fallback_message))
        return state

    except (json.JSONDecodeError, KeyError, Exception) as error:
        print(f"⚠️ Decision making error: {error}")
        # Set default fallback decision
        state["decision"] = "deny_request"
        state["decision_confidence"] = 0.0
        error_message = prompt_manager.get_data("decision", "fallback_messages")[
            "error_decision"
        ]
        state["messages"].append(AIMessage(content=error_message))
        return state


def notify_contact(state: State) -> State:
    """
    Send email notification to the contact person when visitor is granted access.
    """
    profile = state["visitor_profile"]
    contact_name = profile.get("contact_person")
    visitor_name = profile.get("name", "Unknown visitor")
    visitor_purpose = profile.get("purpose", "Unknown purpose")
    visitor_affiliation = profile.get("affiliation", "Unknown affiliation")

    if contact_name and contact_name in CONTACTS:
        # Create email content using prompt manager
        subject = prompt_manager.format_prompt(
            "communication", "email_subject", visitor_name=visitor_name
        )

        message = prompt_manager.format_prompt(
            "communication",
            "email_body",
            contact_name=contact_name,
            visitor_name=visitor_name,
            visitor_purpose=visitor_purpose,
            visitor_affiliation=visitor_affiliation,
        )

        # Use the LLM with tool calling to send the email
        email_prompt = prompt_manager.format_prompt(
            "communication",
            "email_notification",
            contact_name=contact_name,
            subject=subject,
            message=message,
        )

        try:
            # Call LLM with tools to send email
            response = llm_email.invoke([HumanMessage(content=email_prompt)])

            # Check if there are tool calls to execute
            tool_calls = getattr(response, "tool_calls", None)
            if tool_calls:
                tool_node = ToolNode(tools=tools)
                # Execute the tool calls
                tool_result = tool_node.invoke({"messages": [response]})

                success_message = prompt_manager.get_data(
                    "communication", "notification_messages"
                )["success"]
                state["messages"].append(
                    AIMessage(content=success_message.format(contact_name=contact_name))
                )
                print(f"✅ Email notification sent to {contact_name}")
            else:
                print(f"⚠️ Failed to send email notification to {contact_name}")
                failure_message = prompt_manager.get_data(
                    "communication", "notification_messages"
                )["failure"]
                state["messages"].append(
                    AIMessage(content=failure_message.format(contact_name=contact_name))
                )

        except Exception as error:
            print(f"⚠️ Email notification error: {error}")
            failure_message = prompt_manager.get_data(
                "communication", "notification_messages"
            )["failure"]
            state["messages"].append(
                AIMessage(content=failure_message.format(contact_name=contact_name))
            )
    else:
        print("ℹ️ No valid contact person found for email notification")
        no_contact_message = prompt_manager.get_data(
            "communication", "notification_messages"
        )["no_contact"]
        state["messages"].append(AIMessage(content=no_contact_message))

    return state


def check_decision_for_notification(state: State) -> Literal["notify", "end"]:
    """
    Check if the decision requires email notification.
    """
    decision = state.get("decision", "")
    if decision == "allow_request":
        return "notify"
    else:
        return "end"
