# sockets.py
"""
Socket.IO communication channels for the security gate system.
Handles real-time updates, notifications, etc.
"""
import socketio
from typing import Any, Dict
from api import shared_graph

# --- Socket.IO Server Instance ---
# Create the Socket.IO server instance
# Use 'asgi' for FastAPI integration and allow CORS for all origins (*)
# Adjust CORS settings as needed for production
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# --- Socket.IO Event Handlers ---

@sio.event
async def connect(sid: str, environ: dict, auth: Any = None):
    """Handle new client connections."""
    print(f"🔌 Client connected: {sid}")
    # Send a welcome message or initial state if needed
    await sio.emit('status', {'msg': 'Connected to Security Gate System'}, to=sid)
    # Example: Emit initial system status
    # await sio.emit('system_status', {'healthy': True, 'active_sessions': 0}, to=sid)

@sio.event
async def disconnect(sid: str):
    """Handle client disconnections."""
    print(f"🔌 Client disconnected: {sid}")

# --- Example Event Handlers ---
# These are examples of how clients can communicate with the server via Socket.IO
# and how the server can push updates.

# Client can emit 'request_system_status' to get the latest status
@sio.event
async def request_system_status(sid: str, data: Dict[str, Any]):
    """Handle request for system status."""
    # In a real scenario, you might query the FastAPI app or a shared state
    # For now, sending a mock status
    status_data = {'healthy': True, 'message': 'System running'}
    await sio.emit('system_status', status_data, to=sid)

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

# --- Server-side Functions to Emit Events ---
# These functions can be called from other parts of your application (e.g., api.py)
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

# --- New Chat Message Handler via Socket.IO ---
@sio.event
async def send_message(sid: str, data: Dict[str, Any]):
    """Handle incoming chat message via Socket.IO"""
    session_id = data.get("session_id")
    user_message = data.get("message", "")
    image_b64 = data.get("image")  # Optional base64 string

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

        # Save image if provided
        if image_b64:
            try:
                image_data = base64.b64decode(image_b64)
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

        # Check if session is complete
        session_complete = bool(updated_state.get("decision"))

        # Emit response back to the client
        await sio.emit(
            'chat_response',
            {
                "agent_response": assistant_response,
                "session_complete": session_complete
            },
            to=sid
        )

    except Exception as e:
        await sio.emit('error', {'msg': f"Error processing message: {str(e)}"}, to=sid)
