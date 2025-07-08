from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama


# ---- 1. Define Shared State ----
class VisitorProfile(TypedDict):
    name: Optional[str]
    request: Optional[str]
    threat_level: Optional[str]
    affiliation: Optional[str]
    id_verified: Optional[bool]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    visitor_profile: VisitorProfile
    decision: str


# ---- 2. Initialize Graph + LLM ----
graph_builder = StateGraph(State)
llm = ChatOllama(model="gemma3n:e4b", temperature=0)


# ---- 3. Node Implementations ----
def receive_input(state: State) -> State:
    # Display the most recent system message if one exists
    messages = state["messages"]
    if messages and messages[-1]["role"] == "system":
        print(f"Agent: {messages[-1]['content']}")

    user_input = input("User: ")  # Wait for terminal input
    state["messages"].append({"role": "user", "content": user_input})
    return state


def validate_input(state: State) -> Literal["valid", "unrelated"]:
    content = state["messages"][-1]["content"]
    return "valid" if content.strip() else "unrelated"  # this is dummy always valid


def detect_session(state: State) -> Literal["same", "new"]:
    # Dummy logic: always start new for this demo
    return "new"


def check_context_length(state: State) -> Literal["over_limit", "under_limit"]:
    return "under_limit"  # Assume always small for now


def summarize(state: State) -> State:
    state["messages"].append({"role": "system", "content": "Summary: [Dummy summary]"})
    return state


def reset_conversation(state: State) -> State:
    state["messages"] = state["messages"][-1:]
    return state


def check_visitor_profile(state: State) -> Literal["complete", "not_complete"]:
    return "complete" if state["visitor_profile"] else "not_complete"  # always complete


def question_visitor(state: State) -> State:
    question = {"role": "system", "content": "Can you tell me more about yourself?"}
    state["messages"].append(question)
    return state


def make_decision(state: State) -> State:
    state["decision"] = "let_in"
    state["messages"].append({"role": "system", "content": "Access granted."})
    return state


# ---- 4. Add Nodes ----
graph_builder.add_node("receive_input", receive_input)
graph_builder.add_node("validate_input", validate_input)
graph_builder.add_node("detect_session", detect_session)
graph_builder.add_node("check_context_length", check_context_length)
graph_builder.add_node("summarize", summarize)
graph_builder.add_node("reset_conversation", reset_conversation)
graph_builder.add_node("check_visitor_profile", check_visitor_profile)
graph_builder.add_node("question_visitor", question_visitor)
graph_builder.add_node("make_decision", make_decision)

# ---- 5. Add Edges (Logic Flow) ----
graph_builder.set_entry_point("receive_input")
graph_builder.add_conditional_edges(
    "validate_input",
    validate_input,
    {
        "valid": "detect_session",
        "unrelated": "receive_input",
    },
)
graph_builder.add_conditional_edges(
    "detect_session",
    detect_session,
    {
        "same": "check_context_length",
        "new": "reset_conversation",
    },
)
graph_builder.add_conditional_edges(
    "check_context_length",
    check_context_length,
    {
        "over_limit": "summarize",
        "under_limit": "check_visitor_profile",
    },
)
graph_builder.add_edge("summarize", "check_visitor_profile")
graph_builder.add_edge("reset_conversation", "check_visitor_profile")
graph_builder.add_conditional_edges(
    "check_visitor_profile",
    check_visitor_profile,
    {
        "complete": "make_decision",
        "not_complete": "question_visitor",
    },
)
graph_builder.add_edge("question_visitor", "receive_input")
graph_builder.add_edge("make_decision", END)

# ---- 6. Compile the Graph ----
graph = graph_builder.compile()


# ---- 7. Run Demo ----
initial_messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant at the gate. Ask necessary questions and decide on access.",
    },
    {"role": "user", "content": "Hi, I'm here for the tour."},
]

initial_state = {
    "messages": initial_messages,
    "visitor_profile": {
        "name": None,
        "request": None,
        "threat_level": None,
        "affiliation": None,
        "purpose": None,
        "id_verified": None,
    },
    "decision": "",
}

result = graph.invoke(initial_state)
print("Final decision:", result["decision"])
print("Last message:", result["messages"][-1]["content"])
