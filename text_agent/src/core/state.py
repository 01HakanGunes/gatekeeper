from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class VisitorProfile(TypedDict):
    name: Optional[str]
    purpose: Optional[str]
    contact_person: Optional[str]
    threat_level: Optional[str]
    affiliation: Optional[str]
    id_verified: Optional[bool]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    visitor_profile: VisitorProfile
    decision: str
    decision_confidence: Optional[float]
    decision_reasoning: Optional[str]
