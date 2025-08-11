from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage
from src.core.state import State
from src.utils.prompt_manager import prompt_manager

from src.nodes.input_nodes import (
    receive_input,
    detect_session,
    check_context_length,
    summarize,
    reset_conversation
)
from src.nodes.processing_nodes import (
    analyze_threat_level_node,
    check_visitor_profile_node,
    validate_contact_person,
    question_visitor,
    check_visitor_profile_condition,
)
from src.nodes.decision_nodes import (
    make_decision,
    notify_contact,
    check_decision_for_notification,
)


def create_security_graph():
    """
    Create and configure the security gate graph with all nodes and edges.

    Returns:
        StateGraph: Compiled graph ready for execution
    """
    # Initialize graph builder
    graph_builder = StateGraph(State)

    # ---- Add Nodes ----
    graph_builder.add_node("receive_input", receive_input)
    graph_builder.add_node("summarize", summarize)
    graph_builder.add_node("reset_conversation", reset_conversation)
    graph_builder.add_node("check_visitor_profile", check_visitor_profile_node)
    graph_builder.add_node("analyze_threat_level", analyze_threat_level_node)
    graph_builder.add_node("validate_contact_person", validate_contact_person)
    graph_builder.add_node("question_visitor", question_visitor)
    graph_builder.add_node("make_decision", make_decision)
    graph_builder.add_node("notify_contact", notify_contact)

    # ---- Add Edges (Logic Flow) ----
    graph_builder.set_entry_point("receive_input")

    # Route after input based on session and context length
    def route_after_input(state):
        if state["invalid_input"] == True:
            # End the session if the input is invalid
            return "invalid"

        if state["session_active"] == False:
            return "reset_conversation"

        threat_level_value = state['vision_schema']['threat_level']
        if threat_level_value == "high":
            return "call_security"

        session_result = detect_session(state)
        if session_result == "new":
            return "reset_conversation"
        else:  # same session
            context_result = check_context_length(state)
            if context_result == "over_limit":
                return "summarize"
            else:
                return "check_visitor_profile"

    graph_builder.add_conditional_edges(
        "receive_input",
        route_after_input,
        {
            "invalid": END,
            "reset_conversation": "reset_conversation",
            "summarize": "summarize",
            "check_visitor_profile": "check_visitor_profile",
            "call_security": "make_decision",
        },
    )
    graph_builder.add_edge("summarize", "check_visitor_profile")
    graph_builder.add_edge("check_visitor_profile", "analyze_threat_level")
    graph_builder.add_edge("analyze_threat_level", "validate_contact_person")
    graph_builder.add_conditional_edges(
        "validate_contact_person",
        check_visitor_profile_condition,
        {
            "complete": "make_decision",
            "not_complete": "question_visitor",
        },
    )
    graph_builder.add_edge("question_visitor", END)
    graph_builder.add_conditional_edges(
        "make_decision",
        check_decision_for_notification,
        {
            "call_security": "reset_conversation",
            "notify": "notify_contact",
            "end": "reset_conversation",
        },
    )
    graph_builder.add_edge("notify_contact", "reset_conversation")
    graph_builder.add_edge("reset_conversation", END)

    # Compile and return the graph
    return graph_builder.compile()


def create_initial_state() -> State:
    """
    Create the initial state for a new security gate session.

    Returns:
        State: Initial state with system message and empty visitor profile
    """

    system_msg_content = prompt_manager.format_prompt("input", "system_message")
    initial_messages = [
        SystemMessage(content=system_msg_content),
    ]

    return {
        "messages": initial_messages,
        "visitor_profile": {
            "name": None,
            "purpose": None,
            "contact_person": None,
            "threat_level": None,
            "affiliation": None,
            "id_verified": None,
        },
        "decision": "",
        "decision_confidence": None,
        "decision_reasoning": None,
        "vision_schema": None,
        "user_input": "",
        "invalid_input": False,
        "session_active": False,
    }
