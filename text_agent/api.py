#!/usr/bin/env python3
"""
Security Gate System - API Module

FastAPI web interface for the security gate system.
"""

import uuid
import threading
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cli import wait_for_ollama
from src.core.state import State
from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT

# Shared graph instance and session states
shared_graph = None
session_states: Dict[str, Any] = {}
sessions_lock = threading.Lock()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared graph on startup"""
    global shared_graph

    # Check Ollama connection
    if not wait_for_ollama():
        print("❌ Cannot start API: Ollama service is not available")
        yield
        return

    # Set global history mode
    import config.settings as settings
    settings.CURRENT_HISTORY_MODE = "summarize"  # Default for API mode

    print("🌐 Initializing Security Gate API...")

    # Create shared graph instance
    shared_graph = create_security_graph()
    print("✅ Shared graph initialized")

    yield

    # Cleanup on shutdown
    print("🔄 Shutting down Security Gate API...")

app = FastAPI(title="Security Gate API", version="1.0.0", lifespan=lifespan)

class UserInput(BaseModel):
    message: str

class SessionResponse(BaseModel):
    agent_response: str
    session_complete: bool

class StatusResponse(BaseModel):
    status: str
    message: str

class SessionStartResponse(BaseModel):
    session_id: str
    status: str
    message: str

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Security Gate System API",
        "version": "1.0.0",
        "endpoints": {
            "start_session": "POST /start-session",
            "chat": "POST /chat/{session_id}",
            "profile": "GET /profile/{session_id}",
            "end_session": "POST /end-session/{session_id}"
        }
    }

@app.post("/start-session", response_model=SessionStartResponse)
async def start_session():
    """Start a new security gate session"""
    if shared_graph is None:
        return SessionStartResponse(
            session_id="",
            status="error",
            message="API not properly initialized"
        )

    session_id = str(uuid.uuid4())

    try:
        # Create initial state for this session
        initial_state = create_initial_state()

        with sessions_lock:
            session_states[session_id] = initial_state

        return SessionStartResponse(
            session_id=session_id,
            status="success",
            message="Session started successfully"
        )
    except Exception as e:
        return SessionStartResponse(
            session_id="",
            status="error",
            message=f"Error starting session: {str(e)}"
        )

@app.post("/chat/{session_id}", response_model=SessionResponse)
async def chat(session_id: str, user_input: UserInput):
    """Send a message to the security agent"""
    if shared_graph is None:
        raise HTTPException(status_code=500, detail="Graph not initialized")

    with sessions_lock:
        if session_id not in session_states:
            raise HTTPException(status_code=404, detail="Session not found")

        current_state = session_states[session_id]

    try:
        # Update state with user input
        current_state["user_input"] = user_input.message

        # Process using shared graph
        updated_state = shared_graph.invoke(
            current_state, {"recursion_limit": DEFAULT_RECURSION_LIMIT}
        )

        # Update stored state
        with sessions_lock:
            session_states[session_id] = updated_state

        # Get the last assistant message
        assistant_response = ""
        if updated_state["messages"]:
            last_msg = updated_state["messages"][-1]
            if hasattr(last_msg, 'content'):
                assistant_response = last_msg.content

        # Check if session is complete (decision made)
        session_complete = bool(updated_state.get("decision"))

        return SessionResponse(
            agent_response=assistant_response,
            session_complete=session_complete
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/profile/{session_id}")
async def get_profile(session_id: str):
    """Get current visitor profile"""

    with sessions_lock:
        if session_id not in session_states:
            raise HTTPException(status_code=404, detail="Session not found")

        current_state = session_states[session_id]

    return {
        "visitor_profile": current_state["visitor_profile"],
        "decision": current_state["decision"],
        "decision_confidence": current_state["decision_confidence"],
        "session_active": True
    }

@app.post("/end-session/{session_id}", response_model=StatusResponse)
async def end_session(session_id: str):
    """End a specific security gate session"""

    with sessions_lock:
        if session_id not in session_states:
            return StatusResponse(
                status="error",
                message="Session not found"
            )

        del session_states[session_id]

    return StatusResponse(
        status="success",
        message="Session ended successfully"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    with sessions_lock:
        active_sessions = len(session_states)

    return {
        "status": "healthy",
        "graph_initialized": shared_graph is not None,
        "active_sessions": active_sessions
    }
