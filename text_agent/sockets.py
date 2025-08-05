"""
Socket.IO communication channels for the security gate system.
"""
import socketio
import uuid
import base64
import json
import os
import time
from typing import Any, Dict, Optional
from pydantic import BaseModel
import threading
import multiprocessing
from config.settings import DEFAULT_RECURSION_LIMIT
from src.core.graph import create_initial_state

# Initialize objects vars
shared_graph = None
session_states: Dict[str, Any] = {}
sessions_lock = threading.Lock()
image_queue = multiprocessing.Queue(maxsize=10)
face_detection_queue = multiprocessing.Queue(maxsize=4)

# --- Pydantic models for request/response validation (if needed locally) ---
# Define them here or ensure they are accessible without importing api.py directly if there's a circular import issue.
class UserInput(BaseModel):
    message: str

class ImageUploadRequest(BaseModel):
    session_id: str
    image: str
    timestamp: str

class ImageUploadResponse(BaseModel):
    status: str
    message: str
    image_id: Optional[str] = None

# --- Socket.IO Server Instance ---
# Create the Socket.IO server instance
# Use 'asgi' for FastAPI integration and allow CORS for all origins (*)
# Adjust CORS settings as needed for production
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# --- Helper Functions ---
def _get_agent_response(updated_state):
    """Extracts the agent response and completion status from the state."""
    assistant_response = ""
    if updated_state["messages"]:
        last_msg = updated_state["messages"][-1]
        if hasattr(last_msg, 'content'):
            assistant_response = last_msg.content
    session_complete = bool(updated_state.get("decision"))
    return assistant_response, session_complete

# --- Socket.IO Event Handlers ---

@sio.event
async def connect(sid: str, environ: dict, auth: Any = None):
    """Handle new client connections."""
    print(f"🔌 Client connected: {sid}")
    # Send a welcome message or initial state if needed
    await sio.emit('status', {'msg': 'Connected to Security Gate System'}, to=sid)
    await sio.emit('system_status', {'healthy': True, 'active_sessions': 0}, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnections."""
    print(f"🔌 Client disconnected: {sid}")

# --- Core API Functionality via Socket.IO ---

# Equivalent to POST /start-session
@sio.event
async def start_session(sid: str, data: Dict[str, Any]):
    """Start a new security gate session."""
    if shared_graph is None:
        await sio.emit('session_started', {
            "session_id": "",
            "status": "error",
            "message": "API not properly initialized"
        }, to=sid)
        return

    session_id = str(uuid.uuid4())
    try:
        # Create initial state for this session
        initial_state = create_initial_state()
        with sessions_lock:
            session_states[session_id] = initial_state
        await sio.emit('session_started', {
            "session_id": session_id,
            "status": "success",
            "message": "Session started successfully"
        }, to=sid)
    except Exception as e:
        await sio.emit('session_started', {
            "session_id": "",
            "status": "error",
            "message": f"Error starting session: {str(e)}"
        }, to=sid)

# Equivalent to POST /chat/{session_id}
@sio.event
async def send_message(sid: str, data: Dict[str, Any]):
    """Handle incoming chat message via Socket.IO"""
    session_id = data.get("session_id")
    user_message = data.get("message", "")

    if not session_id:
        await sio.emit('error', {'msg': 'session_id is required'}, to=sid)
        return

    if shared_graph is None:
        await sio.emit('error', {'msg': 'Graph not initialized'}, to=sid)
        return

    with sessions_lock:
        if session_id not in session_states:
            await sio.emit('error', {'msg': 'Session not found'}, to=sid)
            return
        current_state = session_states[session_id]

    try:
        # Update state with user input
        current_state["user_input"] = user_message

        # Process using shared graph
        updated_state = shared_graph.invoke(
            current_state, {"recursion_limit": DEFAULT_RECURSION_LIMIT}
        )

        # Update stored state
        with sessions_lock:
            session_states[session_id] = updated_state

        # Get response and completion status
        assistant_response, session_complete = _get_agent_response(updated_state)

        # Prepare response data
        response_data = {
            "agent_response": assistant_response,
            "session_complete": session_complete
        }

        # Emit response back to the specific client
        await sio.emit('chat_response', response_data, to=sid)

        # If session is complete or profile changed significantly, notify room members
        # This part depends on your frontend needs. Example:
        if session_complete:
             # Get profile data to send with completion
            profile_data = {
                "visitor_profile": updated_state.get("visitor_profile", {}),
                "decision": updated_state.get("decision"),
                "decision_confidence": updated_state.get("decision_confidence"),
                "session_active": True
            }
            await emit_session_update(session_id, {
                "type": "session_complete",
                "profile": profile_data,
                "final_response": assistant_response
            })

    except Exception as e:
        await sio.emit('error', {'msg': f"Error processing message: {str(e)}"}, to=sid)


# Equivalent to GET /profile/{session_id}
@sio.event
async def get_profile(sid: str, data: Dict[str, Any]):
    """Get current visitor profile for a session."""
    session_id = data.get("session_id")
    if not session_id:
        await sio.emit('error', {'msg': 'session_id is required'}, to=sid)
        return

    with sessions_lock:
        if session_id not in session_states:
            await sio.emit('error', {'msg': 'Session not found'}, to=sid)
            return
        current_state = session_states[session_id]

    profile_data = {
        "visitor_profile": current_state.get("visitor_profile", {}),
        "decision": current_state.get("decision"),
        "decision_confidence": current_state.get("decision_confidence"),
        "session_active": True
    }
    await sio.emit('profile_data', profile_data, to=sid)

# Equivalent to POST /end-session/{session_id}
@sio.event
async def end_session(sid: str, data: Dict[str, Any]):
    """End a specific security gate session."""
    session_id = data.get("session_id")
    if not session_id:
        await sio.emit('session_ended', {
            "status": "error",
            "message": "session_id is required"
        }, to=sid)
        return

    with sessions_lock:
        if session_id not in session_states:
            await sio.emit('session_ended', {
                "status": "error",
                "message": "Session not found"
            }, to=sid)
            return
        del session_states[session_id]

    await sio.emit('session_ended', {
        "status": "success",
        "message": "Session ended successfully"
    }, to=sid)

    # Notify room that session ended
    await emit_session_update(session_id, {"type": "session_ended", "message": "Session ended by user"})


# Equivalent to POST /upload-image
@sio.event
async def upload_image(sid: str, data: Dict[str, Any]):
    """Upload image separately via Socket.IO (queued processing)."""
    # Basic validation (consider using Pydantic models)
    session_id = data.get("session_id")
    image_b64 = data.get("image")
    timestamp = data.get("timestamp", str(time.time())) # Default timestamp if not provided

    if not session_id or not image_b64:
        await sio.emit('image_upload_response', {
            "status": "error",
            "message": "session_id and image are required"
        }, to=sid)
        return

    try:
        # Decode base64 image
        image_data = base64.b64decode(image_b64)
        image_id = str(uuid.uuid4())
        if image_queue.full():
            print("Queue is full, removing the oldest item.")
            try:
                image_queue.get_nowait() # Remove the oldest item to make space
            except:
                pass # Queue might have been emptied by another process

        image_queue.put({"id": image_id, "data": image_data, "timestamp": timestamp, "session_id": session_id}) # Include session_id
        print(f"📸 Image {image_id} added to the queue. Queue size: {image_queue.qsize()}")

        await sio.emit('image_upload_response', {
            "status": "success",
            "message": "Image added to the queue",
            "image_id": image_id
        }, to=sid)

    except Exception as e:
       await sio.emit('error', {'msg': f"Error uploading image: {str(e)}"}, to=sid)


# Equivalent to GET /health
@sio.event
async def request_health_check(sid: str, data: Dict[str, Any]):
    """Perform health check."""
    with sessions_lock:
        active_sessions = len(session_states)
    health_data = {
        "status": "healthy",
        "graph_initialized": shared_graph is not None,
        "active_sessions": active_sessions
    }
    await sio.emit('health_status', health_data, to=sid)

# Equivalent to GET /threat-logs
@sio.event
async def request_threat_logs(sid: str, data: Dict[str, Any]):
    """Get the threat detector logs."""
    log_file_path = "./data/logs/vision_data_log.json"
    if not os.path.exists(log_file_path):
        await sio.emit('error', {'msg': 'Log file not found.'}, to=sid)
        return

    try:
        with open(log_file_path, "r") as f:
            content = f.read()
            if not content:
                 await sio.emit('threat_logs', [], to=sid)
                 return
            log_data = json.loads(content)
        await sio.emit('threat_logs', log_data, to=sid)
    except json.JSONDecodeError:
        await sio.emit('error', {'msg': 'Invalid JSON format in log file.'}, to=sid)
    except Exception as e:
        await sio.emit('error', {'msg': f'Error reading log file: {str(e)}'}, to=sid)


# --- Session Subscription Events (already present, kept for clarity) ---

# Client can emit 'join_session_updates' to subscribe to updates for a specific session
@sio.event
async def join_session_updates(sid: str, data: Dict[str, Any]):
    """Allow client to join a room for session-specific updates."""
    session_id = data.get('session_id')
    if session_id:
        # Join a room named after the session ID
        await sio.enter_room(sid, session_id)
        await sio.emit('status', {'msg': f'Joined updates for session {session_id}'}, to=sid)
    else:
        await sio.emit('error', {'msg': 'session_id required'}, to=sid)

# Client can emit 'leave_session_updates'
@sio.event
async def leave_session_updates(sid: str, data: Dict[str, Any]):
    """Allow client to leave a room for session-specific updates."""
    session_id = data.get('session_id')
    if session_id:
        await sio.leave_room(sid, session_id)
        await sio.emit('status', {'msg': f'Left updates for session {session_id}'}, to=sid)
    else:
        await sio.emit('error', {'msg': 'session_id required'}, to=sid)

# --- Server-side Functions to Emit Events (already present, kept for clarity) ---
# These functions can be called from other parts of your application (e.g., api.py or background tasks)
# to push updates to connected clients.

async def emit_system_status(status_data: Dict[str, Any]):
    """Emit system status to all connected clients."""
    await sio.emit('system_status', status_data)

async def emit_session_update(session_id: str, update_data: Dict[str, Any]):
    """Emit an update specific to a session to clients in that session's room."""
    # Emit to the room named after the session_id
    await sio.emit('session_update', update_data, room=session_id)

async def emit_general_notification(message: str):
    """Emit a general notification to all clients."""
    await sio.emit('notification', {'message': message})

# Add more event handlers and emit functions as needed for your real-time features
