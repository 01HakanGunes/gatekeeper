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
import multiprocessing
import asyncio
import aiofiles
from config.settings import DEFAULT_RECURSION_LIMIT
from src.core.graph import create_initial_state, create_security_graph

# Utility

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


# Initialize objects vars
shared_graph = create_security_graph()
session_states: Dict[str, Any] = {}  # Now keyed by sid
active_connections: Dict[str, bool] = {}  # Track active sids
sessions_lock = asyncio.Lock()
image_queue = multiprocessing.Queue(maxsize=10)
face_detection_queue = multiprocessing.Queue(maxsize=4)
socketio_events_queue = multiprocessing.Queue(maxsize=20)
state_request_queue = multiprocessing.Queue(maxsize=50)
state_response_queue = multiprocessing.Queue(maxsize=50)

# Graph visualized and saved as image
_generate_graph_visualization()

# --- Pydantic models for request/response validation ---
class UserInput(BaseModel):
    message: str

class ImageUploadRequest(BaseModel):
    image: str
    timestamp: str

class ImageUploadResponse(BaseModel):
    status: str
    message: str
    image_id: Optional[str] = None

# --- Socket.IO Server Instance ---
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
    print("Assistant response: " + assistant_response)
    return assistant_response, session_complete

async def reset_session_state(sid: str):
    """Reset session state immediately when session becomes inactive."""
    from langchain_core.messages import SystemMessage
    from src.utils.prompt_manager import prompt_manager

    if sid not in session_states:
        return

    state = session_states[sid]
    # Clear state
    state["messages"].clear()
    state["visitor_profile"] = {
        "name": None,
        "purpose": None,
        "contact_person": None,
        "threat_level": None,
        "affiliation": None,
        "id_verified": None,
    }
    state["decision"] = ""
    state["decision_confidence"] = None
    state["decision_reasoning"] = None
    state["user_input"] = ""
    state["invalid_input"] = False
    state["session_active"] = False

        # Re-add system message
    system_msg_content = prompt_manager.format_prompt("input", "system_message")
    state["messages"].append(SystemMessage(content=system_msg_content))

    print(f"🔄 Session {sid} state reset due to inactivity")

# --- Socket.IO Event Handlers ---

@sio.event
async def connect(sid: str, environ: dict, auth: Any = None):
    """Handle new client connections."""
    print(f"🔌 Client connected: {sid}")
    await start_event_processor_if_needed()
    await start_state_processor_if_needed()

    # Initialize session state and register active connection
    async with sessions_lock:
        initial_state = create_initial_state()
        session_states[sid] = initial_state
        active_connections[sid] = True

    await sio.emit('status', {'msg': 'Connected to Security Gate System'}, to=sid)
    await sio.emit('session_ready', {'session_id': sid}, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnections."""
    print(f"🔌 Client disconnected: {sid}")

    # Automatic cleanup
    async with sessions_lock:
        session_states.pop(sid, None)
        active_connections.pop(sid, None)

@sio.event
async def send_message(sid: str, data: Dict[str, Any]):
    """Handle incoming chat message via Socket.IO"""
    user_message = data.get("message", "")

    if shared_graph is None:
        await sio.emit('error', {'msg': 'Graph not initialized'}, to=sid)
        return

    async with sessions_lock:
        if sid not in session_states:
            await sio.emit('error', {'msg': 'Session not found'}, to=sid)
            return
        current_state = session_states[sid].copy()

    try:
        # Update state with user input
        current_state["user_input"] = user_message

        updated_state = await asyncio.to_thread(
            shared_graph.invoke,
            current_state,
            {"recursion_limit": DEFAULT_RECURSION_LIMIT}
        )

        # Update stored state
        async with sessions_lock:
            session_states[sid] = updated_state

        # Get response and completion status
        assistant_response, session_complete = _get_agent_response(updated_state)

        # Prepare response data
        response_data = {
            "agent_response": assistant_response,
            "session_complete": session_complete
        }

        # Emit response back to the specific client
        await sio.emit('chat_response', response_data, to=sid)

        # If session is complete, notify room members
        if session_complete:
            profile_data = {
                "visitor_profile": updated_state.get("visitor_profile", {}),
                "decision": updated_state.get("decision"),
                "decision_confidence": updated_state.get("decision_confidence"),
                "session_active": True
            }
            await emit_session_update(sid, {
                "type": "session_complete",
                "profile": profile_data,
                "final_response": assistant_response
            })

    except Exception as e:
        await sio.emit('error', {'msg': f"Error processing message: {str(e)}"}, to=sid)

@sio.event
async def get_profile(sid: str, data: Dict[str, Any]):
    """Get current visitor profile for a session."""
    async with sessions_lock:
        if sid not in session_states:
            await sio.emit('error', {'msg': 'Session not found'}, to=sid)
            return
        current_state = session_states[sid]

    profile_data = {
        "visitor_profile": current_state.get("visitor_profile", {}),
        "decision": current_state.get("decision"),
        "decision_confidence": current_state.get("decision_confidence"),
        "session_active": True
    }
    await sio.emit('profile_data', profile_data, to=sid)

@sio.event
async def upload_image(sid: str, data: Dict[str, Any]):
    """Upload image separately via Socket.IO (queued processing)."""
    image_b64 = data.get("image")
    timestamp = data.get("timestamp", str(time.time()))

    if not image_b64:
        await sio.emit('image_upload_response', {
            "status": "error",
            "message": "image is required"
        }, to=sid)
        return

    try:
        # Decode base64 image
        image_data = base64.b64decode(image_b64)
        image_id = str(uuid.uuid4())

        # Safe queue operation with timeout
        try:
            if image_queue.full():
                print("Queue is full, removing the oldest item.")
                try:
                    image_queue.get_nowait()
                except:
                    pass

            image_queue.put_nowait({"id": image_id, "data": image_data, "timestamp": timestamp, "session_id": sid})
            print(f"📸 Image {image_id} added to the queue. Queue size: {image_queue.qsize()}")
        except Exception as queue_error:
            await sio.emit('image_upload_response', {
                "status": "error",
                "message": f"Queue operation failed: {str(queue_error)}"
            }, to=sid)
            return

        await sio.emit('image_upload_response', {
            "status": "success",
            "message": "Image added to the queue",
            "image_id": image_id
        }, to=sid)

    except Exception as e:
       await sio.emit('error', {'msg': f"Error uploading image: {str(e)}"}, to=sid)

@sio.event
async def request_health_check(sid: str, _data: Dict[str, Any]):
    """Perform health check."""
    async with sessions_lock:
        active_sessions = len(session_states)
    health_data = {
        "status": "healthy",
        "graph_initialized": shared_graph is not None,
        "active_sessions": active_sessions
    }
    await sio.emit('health_status', health_data, to=sid)

@sio.event
async def request_threat_logs(sid: str, data: Dict[str, Any]):
    """Get the threat detector logs."""
    log_file_path = "./data/logs/vision_data_log.json"
    if not os.path.exists(log_file_path):
        await sio.emit('error', {'msg': 'Log file not found.'}, to=sid)
        return

    try:
        async with aiofiles.open(log_file_path, "r") as f:
            content = await f.read()
            if not content:
                 await sio.emit('threat_logs', [], to=sid)
                 return
            log_data = json.loads(content)

        # Filter logs by session_id (now sid)
        session_logs = [log for log in log_data if log.get("session_id") == sid]
        await sio.emit('threat_logs', session_logs, to=sid)
    except json.JSONDecodeError:
        await sio.emit('error', {'msg': 'Invalid JSON format in log file.'}, to=sid)
    except Exception as e:
        await sio.emit('error', {'msg': f'Error reading log file: {str(e)}'}, to=sid)

# --- Session Subscription Events ---

@sio.event
async def join_session_updates(sid: str, data: Dict[str, Any]):
    """Allow client to join a room for session-specific updates."""
    # Join a room named after the session ID (which is now the sid)
    await sio.enter_room(sid, sid)
    await sio.emit('status', {'msg': f'Joined updates for session {sid}'}, to=sid)

@sio.event
async def leave_session_updates(sid: str, data: Dict[str, Any]):
    """Allow client to leave a room for session-specific updates."""
    await sio.leave_room(sid, sid)
    await sio.emit('status', {'msg': f'Left updates for session {sid}'}, to=sid)

# --- Server-side Functions to Emit Events ---

async def send_to_sid(sid: str, event: str, data: Dict[str, Any]) -> bool:
    """Send event to specific client by sid. Returns True if sent successfully."""
    async with sessions_lock:
        if sid not in active_connections:
            return False
    try:
        await sio.emit(event, data, to=sid)
        return True
    except Exception as e:
        print(f"Failed to send to sid {sid}: {e}")
        return False

async def send_to_all_active(event: str, data: Dict[str, Any]):
    """Send event to all active clients."""
    await sio.emit(event, data)

async def get_active_sids() -> list[str]:
    """Get list of all active sids."""
    async with sessions_lock:
        return list(active_connections.keys())

async def is_sid_active(sid: str) -> bool:
    """Check if sid is currently active."""
    async with sessions_lock:
        return sid in active_connections

async def emit_system_status(status_data: Dict[str, Any]):
    """Emit system status to all connected clients."""
    await sio.emit('system_status', status_data)

async def emit_session_update(session_id: str, update_data: Dict[str, Any]):
    """Emit an update specific to a session to clients in that session's room."""
    await sio.emit('session_update', update_data, room=session_id)

async def emit_general_notification(message: str):
    """Emit a general notification to all clients."""
    await sio.emit('notification', {'message': message})

# --- Background Task for Processing Socket.IO Events from Other Processes ---

_event_processor_started = False

async def process_socketio_events():
    """Background task to process Socket.IO events from the event queue."""
    while True:
        try:
            events_processed = 0
            max_events_per_cycle = 5

            while not socketio_events_queue.empty() and events_processed < max_events_per_cycle:
                try:
                    event_data = socketio_events_queue.get_nowait()
                    event_type = event_data.get("type")
                    message = event_data.get("message", "")

                    if event_type == "no_face_detected":
                        await sio.emit('camera_instruction', {
                            'type': 'no_face_detected',
                            'message': message,
                            'instruction': 'Please position yourself in front of the camera'
                        })
                        print(f"📢 Emitted no face detected event: {message}")
                    elif event_type == "trigger_langgraph":
                        session_id = event_data.get("session_id")
                        dummy_message = event_data.get("message", "I am here to visit someone")

                        if session_id:
                            await send_message(session_id, {"message": dummy_message})
                            print(f"📢 Triggered langgraph for high threat level in session {session_id}")

                    events_processed += 1
                except:
                    break

            await asyncio.sleep(0.05 if events_processed > 0 else 0.1)
        except Exception as e:
            print(f"Error processing Socket.IO events: {e}")
            await asyncio.sleep(1)

async def start_event_processor_if_needed():
    """Start the event processor task if not already started."""
    global _event_processor_started
    if not _event_processor_started:
        asyncio.create_task(process_socketio_events())
        _event_processor_started = True
        print("🔄 Started Socket.IO event processor")

# --- State Management for Image Processor ---

_state_processor_started = False

async def process_state_requests():
    """Background task to handle state requests from image processor."""
    while True:
        try:
            requests_processed = 0
            max_requests_per_cycle = 10

            while not state_request_queue.empty() and requests_processed < max_requests_per_cycle:
                try:
                    request = state_request_queue.get_nowait()
                    action = request.get("action")
                    session_id = request.get("session_id")

                    if action == "update" and session_id:
                        updates = request.get("updates", {})
                        async with sessions_lock:
                            if session_id in session_states:
                                # Check if session_active is being updated
                                if "session_active" in updates:
                                    old_active = session_states[session_id].get("session_active")
                                    new_active = updates["session_active"]

                                    # Send message if status changed
                                    if old_active != new_active:
                                        if new_active:
                                            await sio.emit('chat_response', {
                                                "agent_response": "Dur yolcu, sen kimsin!",
                                                "session_complete": False
                                            }, to=session_id)
                                        else:
                                            await sio.emit('chat_response', {
                                                "agent_response": "Tekrar görüşecez...",
                                                "session_complete": False
                                            }, to=session_id)

                                            # Immediately reset conversation state
                                            await reset_session_state(session_id)

                                session_states[session_id].update(updates)
                                print(f"🔄 Updated state for session {session_id}: {updates}")

                    requests_processed += 1
                except:
                    break

            await asyncio.sleep(0.01 if requests_processed > 0 else 0.05)
        except Exception as e:
            print(f"Error processing state requests: {e}")
            await asyncio.sleep(1)

async def start_state_processor_if_needed():
    """Start the state processor task if not already started."""
    global _state_processor_started
    if not _state_processor_started:
        asyncio.create_task(process_state_requests())
        _state_processor_started = True
        print("🔄 Started state processor")
