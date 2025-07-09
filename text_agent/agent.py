from typing import Annotated, Literal, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


# ---- 1. Define Shared State ----
class VisitorProfile(TypedDict):
    name: Optional[str]
    purpose: Optional[str]
    threat_level: Optional[str]
    affiliation: Optional[str]
    id_verified: Optional[bool]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    visitor_profile: VisitorProfile
    decision: str


# ---- 2. Initialize Graph + LLM ----
graph_builder = StateGraph(State)
llm = ChatOllama(model="qwen3:0.6b", temperature=0)


# ---- 3. Node Implementations ----
def receive_input(state: State) -> State:
    # Display the most recent system message if one exists
    messages = state["messages"]
    if messages and hasattr(messages[-1], "type") and messages[-1].type == "system":
        print(f"Agent: {messages[-1].content}")

    user_input = input("User: ")  # Wait for terminal input
    state["messages"].append(HumanMessage(content=user_input))

    # Print current visitor profile status after each user input for debugging
    print(f"\n📋 Visitor Profile Status (after user input):")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state


def validate_input(state: State) -> Literal["valid", "unrelated"]:
    content = state["messages"][-1].content
    return "valid" if content.strip() else "unrelated"  # this is dummy always valid


def detect_session(state: State) -> Literal["same", "new"]:
    # Dummy logic: always go with same for this demo
    return "same"


def check_context_length(state: State) -> Literal["over_limit", "under_limit"]:
    return "under_limit"  # Assume always small for now


def summarize(state: State) -> State:
    state["messages"].append(SystemMessage(content="Summary: [Dummy summary]"))
    return state


def reset_conversation(state: State) -> State:
    state["messages"] = state["messages"][-1:]
    return state


def check_visitor_profile_node(state: State) -> State:
    """
    Node function that performs LLM extraction and updates the visitor profile.
    """
    # Get current conversation context
    messages = state["messages"]
    conversation_text = "\n".join(
        [
            f"{msg.type}: {msg.content}"
            for msg in messages
            if hasattr(msg, "type") and hasattr(msg, "content")
        ]
    )

    # Define fields to extract
    fields_to_extract = ["name", "purpose", "threat_level", "affiliation"]

    # Try to extract information using LLM
    for field in fields_to_extract:
        if state["visitor_profile"][field] is None:
            # Define detailed descriptions for each field
            field_descriptions = {
                "name": "The visitor's full name (first and last name). Examples: 'John Smith', 'Maria Garcia', 'David Kim', '-1'",
                "purpose": "The reason for the visit or what they want to do. Examples: 'meeting', 'delivery', 'tour', 'interview', 'maintenance', '-1'",
                "threat_level": "Security risk assessment based on items carried, behavior, or concerns mentioned. Examples: 'low', 'medium', 'high', '-1'",
                "affiliation": "Company, organization, or group they represent. Examples: 'Google', 'FedEx', 'University of XYZ', 'independent contractor', '-1'",
            }

            # Create extraction prompt with field-specific description
            extraction_prompt = f"""You are a data extraction tool. Your task is to extract ONLY the {field} value from the conversation.

FIELD DESCRIPTION:
{field} = {field_descriptions[field]}

STRICT RULES:
- Respond with ONLY the {field} value (no explanations, no sentences)
- If you cannot clearly determine the {field} from the conversation, respond with exactly: -1
- Maximum 3 words for the response
- No punctuation except necessary hyphens or periods

Examples:
- If extracting "name" and conversation mentions "I'm John Smith" → respond: John Smith
- If extracting "purpose" and visitor says "here for the meeting" → respond: meeting
- If extracting "affiliation" and they say "I work at Google" → respond: Google
- If cannot determine the value → respond: -1

Conversation:
{conversation_text}

Extract {field}:"""

            try:
                # Use LLM to extract information
                response = llm.invoke([HumanMessage(content=extraction_prompt)])
                print(response)

                # Handle the AIMessage response
                if hasattr(response, "content"):
                    extracted_value = str(response.content).strip()
                else:
                    extracted_value = str(response).strip()

                # Additional cleaning to ensure we get only the value
                # Remove common prefixes that LLM might add
                prefixes_to_remove = [
                    f"{field}:",
                    f"{field.capitalize()}:",
                    "Answer:",
                    "Response:",
                    "Value:",
                    "Result:",
                    "The " + field + " is",
                    "Their " + field + " is",
                ]

                for prefix in prefixes_to_remove:
                    if extracted_value.startswith(prefix):
                        extracted_value = extracted_value[len(prefix) :].strip()

                # Remove quotes if present
                extracted_value = extracted_value.strip("\"'")

                # Take only the first few words if response is too long
                words = extracted_value.split()
                if len(words) > 3:
                    extracted_value = " ".join(words[:3])

                # Update profile if valid information found
                if extracted_value != "-1" and extracted_value:
                    state["visitor_profile"][field] = extracted_value
                    print(f"✅ Extracted {field}: '{extracted_value}'")

            except Exception as error:
                print(f"Error extracting {field}: {error}")
                # Continue with other fields if one fails
                continue

    # Print current visitor profile status for debugging
    print(f"\n📋 Current Visitor Profile:")
    for field, value in state["visitor_profile"].items():
        status = "✅" if value is not None and value != "-1" else "❌"
        print(f"  {status} {field}: {value}")
    print()

    return state


def check_visitor_profile_condition(
    state: State,
) -> Literal["complete", "not_complete"]:
    """
    Simple conditional function that only checks if profile is complete.
    """
    # Check if all required fields are completed
    profile = state["visitor_profile"]
    all_fields_complete = all(
        [
            profile["name"] is not None and profile["name"] != "-1",
            profile["purpose"] is not None and profile["purpose"] != "-1",
            profile["threat_level"] is not None and profile["threat_level"] != "-1",
            profile["affiliation"] is not None and profile["affiliation"] != "-1",
        ]
    )

    # Set id_verified based on completeness
    if all_fields_complete:
        state["visitor_profile"]["id_verified"] = True
        return "complete"
    else:
        state["visitor_profile"]["id_verified"] = False
        return "not_complete"


def question_visitor(state: State) -> State:
    # Define specific questions for each field
    field_questions = {
        "name": "What is your name?",
        "purpose": "What is the purpose of your visit today?",
        "threat_level": "Are you carrying any restricted items or have any security concerns I should know about?",
        "affiliation": "What company or organization are you with?",
    }

    # Find the first missing field that needs to be completed
    fields_to_check = ["name", "purpose", "threat_level", "affiliation"]

    for field in fields_to_check:
        if (
            state["visitor_profile"][field] is None
            or state["visitor_profile"][field] == "-1"
        ):
            # Ask specific question for this missing field
            question_text = field_questions[field]
            question = SystemMessage(content=question_text)
            state["messages"].append(question)
            print(f"🤔 Asking for missing field: {field}")
            return state

    # Fallback if somehow all fields are filled but we're still here
    question = SystemMessage(content="Can you tell me more about yourself?")
    state["messages"].append(question)
    return state


def make_decision(state: State) -> State:
    state["decision"] = "let_in"
    state["messages"].append(SystemMessage(content="Access granted."))
    return state


# ---- 4. Add Nodes ----
graph_builder.add_node("receive_input", receive_input)
graph_builder.add_node(
    "validate_input", lambda state: state
)  # passthrough for decision node
graph_builder.add_node(
    "detect_session", lambda state: state
)  # passthrough for decision node
graph_builder.add_node(
    "check_context_length", lambda state: state
)  # passthrough for decision node
graph_builder.add_node("summarize", summarize)
graph_builder.add_node("reset_conversation", reset_conversation)
graph_builder.add_node(
    "check_visitor_profile", check_visitor_profile_node
)  # Use the actual node function
graph_builder.add_node("question_visitor", question_visitor)
graph_builder.add_node("make_decision", make_decision)

# ---- 5. Add Edges (Logic Flow) ----
graph_builder.set_entry_point("receive_input")
graph_builder.add_edge("receive_input", "validate_input")
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
    check_visitor_profile_condition,  # Use the simple conditional function
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
    SystemMessage(
        content="You are a helpful assistant at the gate. Ask necessary questions and decide on access."
    ),
]

initial_state: State = {
    "messages": initial_messages,
    "visitor_profile": {
        "name": None,
        "purpose": None,
        "threat_level": None,
        "affiliation": None,
        "id_verified": None,
    },
    "decision": "",
}

result = graph.invoke(initial_state, {"recursion_limit": 100})
print("Final decision:", result["decision"])
print("Last message:", result["messages"][-1].content)
