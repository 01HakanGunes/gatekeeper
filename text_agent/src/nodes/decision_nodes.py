from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import ToolNode
from ..core.state import State
from ..data.contacts import CONTACTS
from ..utils.extraction import extract_answer_from_thinking_model
from models.llm_config import llm_decision, llm_email
from ..tools.communication import tools


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

    # Define available decisions
    decisions = {
        "allow_request": "Standard access granted - visitor approved and the related people notified.",
        "call_security": "Call security immediately - high threat or suspicious behavior",
        "deny_request": "Access denied - insufficient credentials or policy violation",
    }

    # Create decision prompt
    decision_prompt = f"""You are a security gate decision system. Based on the visitor profile and conversation, choose the most appropriate security action.

VISITOR PROFILE:
- Name: {profile['name']}
- Purpose: {profile['purpose']}
- Contact Person: {profile['contact_person']}
- Threat Level: {profile['threat_level']}
- Affiliation: {profile['affiliation']}
- ID Verified: {profile['id_verified']}


AVAILABLE DECISIONS:
{chr(10).join([f"{i+1}. {decision_id} - {description}" for i, (decision_id, description) in enumerate(decisions.items())])}


RECENT CONVERSATION:
{conversation_text}

Respond with ONLY the decision ID (e.g., "allow_request", "call_security", etc.):"""

    try:
        response = llm_decision.invoke([HumanMessage(content=decision_prompt)])
        decision_result = extract_answer_from_thinking_model(response).strip().lower()

        # Clean and validate decision
        for decision_id in decisions.keys():
            if decision_id in decision_result:
                state["decision"] = decision_id

                # Add appropriate response message
                decision_messages = {
                    "allow_request": "✅ Access granted. Welcome! Please proceed to the main entrance.",
                    "call_security": "⚠️ Please wait here. Security has been notified and will assist you shortly.",
                    "deny_request": "❌ Access denied. Please contact the appropriate department to arrange your visit.",
                }

                state["messages"].append(
                    AIMessage(content=decision_messages[decision_id])
                )
                print(f"🔒 Security Decision: {decision_id.upper()}")
                print(f"📋 Reason: {decisions[decision_id]}")
                return state

        # Fallback if no valid decision found
        print("⚠️ Decision making: Unclear response, defaulting to deny_request")
        state["decision"] = "deny_request"
        state["messages"].append(
            AIMessage(
                content="❌ I cannot process your request at this time. Please contact reception for assistance."
            )
        )
        return state

    except Exception as error:
        print(f"⚠️ Decision making error: {error}")
        # Safe fallback decision
        state["decision"] = "deny_request"
        state["messages"].append(
            AIMessage(
                content="❌ I cannot process your request at this time. Please contact reception for assistance."
            )
        )
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
        # Create email content
        subject = f"Visitor Arrival Notification - {visitor_name}"
        message = f"""Hello {contact_name},

This is an automated notification that your visitor has arrived:

Visitor Details:
- Name: {visitor_name}
- Purpose: {visitor_purpose}
- Affiliation: {visitor_affiliation}
- Status: Access Granted

The visitor has been cleared through security and is proceeding to the main entrance.

Best regards,
Security Gate System"""

        # Use the LLM with tool calling to send the email
        email_prompt = f"""Send an email notification to the contact person about visitor arrival.

Contact: {contact_name}
Subject: {subject}
Message: {message}

Please send this email using the send_email tool."""

        try:
            # Call LLM with tools to send email
            response = llm_email.invoke([HumanMessage(content=email_prompt)])

            # Check if there are tool calls to execute
            tool_calls = getattr(response, "tool_calls", None)
            if tool_calls:
                tool_node = ToolNode(tools=tools)
                # Execute the tool calls
                tool_result = tool_node.invoke({"messages": [response]})

                state["messages"].append(
                    AIMessage(
                        content=f"📧 Notification sent to {contact_name} about your arrival."
                    )
                )
                print(f"✅ Email notification sent to {contact_name}")
            else:
                print(f"⚠️ Failed to send email notification to {contact_name}")
                state["messages"].append(
                    AIMessage(
                        content=f"⚠️ Could not send notification to {contact_name}. Please contact them directly."
                    )
                )

        except Exception as error:
            print(f"⚠️ Email notification error: {error}")
            state["messages"].append(
                AIMessage(
                    content=f"⚠️ Could not send notification to {contact_name}. Please contact them directly."
                )
            )
    else:
        print("ℹ️ No valid contact person found for email notification")
        state["messages"].append(
            AIMessage(
                content="ℹ️ No contact person on file. Please proceed to reception."
            )
        )

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
