from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage
from src.core.state import State
from src.utils.prompt_manager import prompt_manager

from src.nodes.input_nodes import (
    receive_input,
    detect_session,
    check_context_length,
    summarize,
    reset_conversation,
)
from src.nodes.processing_nodes import (
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
    graph_builder.add_node("validate_contact_person", validate_contact_person)
    graph_builder.add_node("question_visitor", question_visitor)
    graph_builder.add_node("make_decision", make_decision)
    graph_builder.add_node("notify_contact", notify_contact)

    # ---- Add Edges (Logic Flow) ----
    graph_builder.set_entry_point("receive_input")

    # Combined session detection and routing logic
    def session_and_context_router(state):
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
        session_and_context_router,
        {
            "reset_conversation": "reset_conversation",
            "summarize": "summarize",
            "check_visitor_profile": "check_visitor_profile",
        },
    )
    graph_builder.add_edge("summarize", "check_visitor_profile")
    graph_builder.add_edge("reset_conversation", "check_visitor_profile")
    graph_builder.add_edge("check_visitor_profile", "validate_contact_person")
    graph_builder.add_conditional_edges(
        "validate_contact_person",
        check_visitor_profile_condition,
        {
            "complete": "make_decision",
            "not_complete": "question_visitor",
        },
    )
    graph_builder.add_edge("question_visitor", "receive_input")
    graph_builder.add_conditional_edges(
        "make_decision",
        check_decision_for_notification,
        {
            "notify": "notify_contact",
            "end": END,
        },
    )
    graph_builder.add_edge("notify_contact", END)

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
    }
