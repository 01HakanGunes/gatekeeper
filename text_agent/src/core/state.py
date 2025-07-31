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


class VisionSchema(TypedDict):
    """Schema for the vision analysis results provided by the API."""
    face_detected: bool  # true if there is a face
    angry_face: bool  # true if the face is angry
    threat_level: str  # one of: low, medium, high
    dangerous_object_detected: bool  # true if any dangerous object is detected
    details: str  # very short description of what do you see


class State(TypedDict):
    messages: Annotated[list, add_messages]
    visitor_profile: VisitorProfile
    decision: str
    decision_confidence: Optional[float]
    decision_reasoning: Optional[str]
    vision_schema: Optional[VisionSchema]  # stores vision analysis results
    user_input: str
    invalid_input: bool