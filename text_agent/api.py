"""
Security Gate System - API Module

FastAPI web interface for the security gate system.
"""

import json
import uuid
import threading
import base64
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
import os
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT
import time
import ollama
import multiprocessing

# Shared graph instance and session states
shared_graph = None
session_states: Dict[str, Any] = {}
sessions_lock = threading.Lock()
image_queue = multiprocessing.Queue(maxsize=10)

# This queue stores face detection true false values. If a new one added, oldest one is removed.
face_detection_queue = multiprocessing.Queue(maxsize=4)

def wait_for_ollama(timeout: int = 30) -> bool:
    """Wait for the Ollama service to become available."""
    print("⏳ Waiting for Ollama service...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            ollama.list()
            print("✅ Ollama service is available")
            return True
        except Exception:
            time.sleep(1)
    return False

def _generate_graph_visualization():
    """Generate graph visualization as Mermaid diagram"""
    print("📊 Generating graph visualization...")

    if shared_graph is None:
        print("⚠️ Graph not initialized, skipping visualization")
        return

    try:
        compiled_graph = shared_graph.get_graph()

        # Save Mermaid source code (.mmd file)
        try:
            mermaid_source = compiled_graph.draw_mermaid()
            mermaid_filename = "security_gate_diagram.mmd"
            with open(mermaid_filename, "w", encoding="utf-8") as f:
                f.write(mermaid_source)
            print(f"✅ Mermaid source saved to {mermaid_filename}")
        except Exception as e:
            print(f"⚠️ Could not save Mermaid source: {e}")

        # Save PNG visualization
        png_data = compiled_graph.draw_mermaid_png()
        if png_data:
            png_filename = "security_gate_diagram.png"
            with open(png_filename, "wb") as f:
                f.write(png_data)
            print(f"✅ Mermaid diagram (PNG) saved to {png_filename}")
        else:
            print("❌ Could not generate Mermaid PNG data.")

    except Exception as e:
        print(f"⚠️ Could not generate graph diagram: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared graph on startup"""
    global shared_graph

    # Set global history mode
    import config.settings as settings
    settings.CURRENT_HISTORY_MODE = "summarize"  # Default for API mode

    print("🌐 Initializing Security Gate API...")

    # Create shared graph instance
    shared_graph = create_security_graph()
    print("✅ Shared graph initialized")

    # Generate graph visualization
    _generate_graph_visualization()

    yield

    # Cleanup on shutdown
    print("🔄 Shutting down Security Gate API...")

app = FastAPI(title="Security Gate API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class UserInput(BaseModel):
    message: str
    image: Optional[str] = None

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

# To be used for image upload requests
class ImageUploadRequest(BaseModel):
    session_id: str
    image: str
    timestamp: str

class ImageUploadResponse(BaseModel):
    status: str
    message: str
    image_id: Optional[str] = None

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

        # Save image if provided
        if user_input.image:
            try:
                # Decode base64 image
                image_data = base64.b64decode(user_input.image)

                # Save to visitor.png in project root
                image_path = "visitor.png"
                with open(image_path, "wb") as f:
                    f.write(image_data)

                print(f"📸 Image saved to {image_path}")
            except Exception as e:
                print(f"❌ Error saving image: {str(e)}")
        else:
            print("No image provided")

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

@app.post("/upload-image", response_model=ImageUploadResponse)
async def upload_image(request: ImageUploadRequest):
    """Upload image separately"""
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image)
        image_id = str(uuid.uuid4())

        if image_queue.full():
            print("Queue is full, removing the oldest item.")
            image_queue.get_nowait() # Remove the oldest item to make space

        image_queue.put({"id": image_id, "data": image_data, "timestamp": request.timestamp})

        print(f"📸 Image {image_id} added to the queue. Queue size: {image_queue.qsize()}")

        return ImageUploadResponse(
            status="success",
            message="Image added to the queue",
            image_id=image_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@app.get("/threat-logs")
async def get_threat_logs():
    """Get the threat detector logs."""
    log_file_path = "./data/logs/vision_data_log.json"

    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail="Log file not found.")

    try:
        with open(log_file_path, "r") as f:
            content = f.read()
            if not content:
                return []
            log_data = json.loads(content)

        return log_data

    except json.JSONDecodeError:
        # Handle cases where the file exists but is not valid JSON
        raise HTTPException(status_code=500, detail="Invalid JSON format in log file.")
