from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from ..core.state import State
from ..data.contacts import CONTACTS
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_decision, llm_email
from ..tools.communication import tools
from prompts.manager import prompt_manager


def make_decision(state: State) -> State:
    """
    Make a security decision based on visitor profile and conversation context.
    Uses LLM to analyze all information and choose appropriate action.
    """
    # Get visitor profile and conversation context
    profile = state["visitor_profile"]
    messages = state["messages"]

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

    # Create decision prompt using prompt manager
    decisions_list = "\n".join(
        [
            f"{i+1}. {decision_id} - {description}"
            for i, (decision_id, description) in enumerate(decisions.items())
        ]
    )

    prompt_value = prompt_manager.invoke_prompt(
        "decision",
        "make_decision",
        profile_name=profile["name"],
        profile_purpose=profile["purpose"],
        profile_contact_person=profile["contact_person"],
        profile_threat_level=profile["threat_level"],
        profile_affiliation=profile["affiliation"],
        profile_id_verified=profile["id_verified"],
        decisions_list=decisions_list,
        conversation_text=conversation_text,
    )

    try:
        response = llm_decision.invoke(prompt_value)
        decision_result = extract_answer_from_thinking_model(response).strip().lower()

        # Clean and validate decision
        for decision_id in decisions.keys():
            if decision_id in decision_result:
                state["decision"] = decision_id

                # Add appropriate response message from prompt manager
                decision_messages = prompt_manager.get_data(
                    "decision", "decision_messages"
                )
                state["messages"].append(
                    AIMessage(content=decision_messages[decision_id])
                )
                print(f"🔒 Security Decision: {decision_id.upper()}")
                print(f"📋 Reason: {decisions[decision_id]}")
                return state

        # Fallback if no valid decision found
        print("⚠️ Decision making: Unclear response, defaulting to deny_request")
        state["decision"] = "deny_request"
        fallback_message = prompt_manager.get_data("decision", "fallback_messages")[
            "unclear_decision"
        ]
        state["messages"].append(AIMessage(content=fallback_message))
        return state

    except Exception as error:
        print(f"⚠️ Decision making error: {error}")
        # Safe fallback decision
        state["decision"] = "deny_request"
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
