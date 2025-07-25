#!/usr/bin/env python3
"""
Security Gate System - API Module

FastAPI web interface for the security gate system.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import SecurityGateAgent
import threading
from typing import Optional

app = FastAPI(title="Security Gate API", version="1.0.0")

# Global agent instance and lock for thread safety
agent_instance: Optional[SecurityGateAgent] = None
agent_lock = threading.Lock()

class UserInput(BaseModel):
    message: str

class SessionResponse(BaseModel):
    agent_response: str
    session_complete: bool

class StatusResponse(BaseModel):
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
            "chat": "POST /chat",
            "profile": "GET /profile",
            "end_session": "POST /end-session"
        }
    }

@app.post("/start-session", response_model=StatusResponse)
async def start_session():
    """Start a new security gate session"""
    global agent_instance

    with agent_lock:
        if agent_instance is not None:
            return StatusResponse(
                status="error",
                message="Session already active. End current session first."
            )

        try:
            agent_instance = SecurityGateAgent()
            success = agent_instance.setup()

            if success:
                return StatusResponse(
                    status="success",
                    message="Session started successfully"
                )
            else:
                agent_instance = None
                return StatusResponse(
                    status="error",
                    message="Failed to initialize agent"
                )
        except Exception as e:
            agent_instance = None
            return StatusResponse(
                status="error",
                message=f"Error starting session: {str(e)}"
            )

@app.post("/chat", response_model=SessionResponse)
async def chat(user_input: UserInput):
    """Send a message to the security agent"""
    global agent_instance

    if agent_instance is None:
        raise HTTPException(status_code=400, detail="No active session. Start a session first.")

    # TODO: This needs agent modification to support single interactions
    # For now, return a placeholder response
    try:
        return SessionResponse(
            agent_response="This endpoint requires agent modification for single-turn processing",
            session_complete=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/profile")
async def get_profile():
    """Get current visitor profile"""
    global agent_instance

    if agent_instance is None:
        raise HTTPException(status_code=400, detail="No active session")

    # TODO: This needs proper integration with agent state
    return {
        "visitor_profile": {},
        "session_active": True
    }

@app.post("/end-session", response_model=StatusResponse)
async def end_session():
    """End the current security gate session"""
    global agent_instance

    with agent_lock:
        if agent_instance is None:
            return StatusResponse(
                status="error",
                message="No active session to end"
            )

        try:
            agent_instance.cleanup()
            agent_instance = None
            return StatusResponse(
                status="success",
                message="Session ended successfully"
            )
        except Exception as e:
            # Still clean up the instance even if cleanup fails
            agent_instance = None
            return StatusResponse(
                status="warning",
                message=f"Session ended but cleanup had issues: {str(e)}"
            )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "session_active": agent_instance is not None
    }
