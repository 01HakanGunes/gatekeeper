import time
import os
import base64
import json
from datetime import datetime
from src.utils.llm_utilities import analyze_image_with_prompt

LOG_FILE = "./data/logs/vision_data_log.json"
LOG_LIMIT = 10
FACE_QUEUE_LIMIT = 3
LANGGRAPH_COOLDOWN_SECONDS = 10

def load_sessions_data():
    """Load sessions data from JSON file"""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_sessions_data(sessions_data):
    """Save sessions data to JSON file"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(sessions_data, f, indent=4)

def get_or_create_session(sessions_data, session_id):
    """Get existing session or create new one"""
    for session in sessions_data:
        if session["session_id"] == session_id:
            return session

    # Create new session
    new_session = {
        "session_id": session_id,
        "face_detected": [],
        "log_entries": [],
        "last_langgraph_trigger": None
    }
    sessions_data.append(new_session)
    return new_session

def write_log(session_id, log_entry):
    """Write log entry for specific session"""
    sessions_data = load_sessions_data()
    session = get_or_create_session(sessions_data, session_id)

    session["log_entries"].append(log_entry)

    # Keep only the last LOG_LIMIT entries per session
    session["log_entries"] = session["log_entries"][-LOG_LIMIT:]

    save_sessions_data(sessions_data)

def can_trigger_langgraph(session_id):
    """Check if langgraph can be triggered for this session (cooldown check)"""
    sessions_data = load_sessions_data()
    session = get_or_create_session(sessions_data, session_id)

    last_trigger = session.get("last_langgraph_trigger")
    if last_trigger is None:
        return True

    try:
        last_trigger_time = datetime.fromisoformat(last_trigger)
        time_since_last = datetime.now() - last_trigger_time
        return time_since_last.total_seconds() >= LANGGRAPH_COOLDOWN_SECONDS
    except (ValueError, TypeError):
        return True

def update_langgraph_trigger_time(session_id):
    """Update the last langgraph trigger time for a session"""
    sessions_data = load_sessions_data()
    session = get_or_create_session(sessions_data, session_id)
    session["last_langgraph_trigger"] = datetime.now().isoformat()
    save_sessions_data(sessions_data)

def update_session_state(session_id, updates, state_request_queue):
    """Update session state via queue communication"""
    try:
        state_request_queue.put_nowait({
            "action": "update",
            "session_id": session_id,
            "updates": updates
        })
        print(f"[{os.getpid()}] [Processing Process] Sent state update for session {session_id}: {updates}")
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] Failed to update session state: {e}")

def update_face_detection(session_id, face_detected, socketio_events_queue=None, state_request_queue=None):
    """Update face detection status for session and check if logging should continue"""
    sessions_data = load_sessions_data()
    session = get_or_create_session(sessions_data, session_id)

    # Add face detection result to session
    session["face_detected"].append(face_detected)

    # Keep only the last FACE_QUEUE_LIMIT values
    session["face_detected"] = session["face_detected"][-FACE_QUEUE_LIMIT:]

    save_sessions_data(sessions_data)

    print(f"[{os.getpid()}] [Processing Process] Face detected: {face_detected}, Session: {session_id}, Queue size: {len(session['face_detected'])}")

    # Update session_active flag based on face detection
    if face_detected and state_request_queue is not None:
        update_session_state(session_id, {"session_active": True}, state_request_queue)

    # Check if all face detection values are False and queue is full
    face_values = session["face_detected"]
    if len(face_values) == FACE_QUEUE_LIMIT and all(value == False for value in face_values):
        print(f"[{os.getpid()}] [Processing Process] All face detection values are False for session {session_id}. Clearing log entries.")

        # Clear the log entries for this session
        session["log_entries"] = []
        save_sessions_data(sessions_data)

        # Set session_active to False
        if state_request_queue is not None:
            update_session_state(session_id, {"session_active": False}, state_request_queue)

        print(f"[{os.getpid()}] [Processing Process] Stopping logging for session {session_id} - no faces detected.")

        # Send Socket.IO event for no face detected
        if socketio_events_queue is not None:
            try:
                event_data = {
                    "type": "no_face_detected",
                    "message": "No face detected. Please position yourself in front of the camera.",
                    "session_id": session_id
                }
                socketio_events_queue.put_nowait(event_data)
                print(f"[{os.getpid()}] [Processing Process] Sent no face detected event to Socket.IO queue for session {session_id}.")
            except Exception as e:
                print(f"[{os.getpid()}] [Processing Process] Failed to send Socket.IO event: {e}")

        return False  # stop logging

    return True  # Continue logging

def validate_vision_schema(vision_data):
    """Validate and clean vision data to match VisionSchema"""
    if vision_data is None:
        return None

    # Ensure all required fields exist with proper defaults
    validated_schema = {
        "face_detected": bool(vision_data.get("face_detected", False)),
        "angry_face": bool(vision_data.get("angry_face", False)),
        "dangerous_object": bool(vision_data.get("dangerous_object", False)),
        "threat_level": str(vision_data.get("threat_level", "low")),
        "details": str(vision_data.get("details", ""))
    }

    # Validate threat_level is one of the expected values
    valid_threat_levels = ["low", "medium", "high"]
    if validated_schema["threat_level"] not in valid_threat_levels:
        validated_schema["threat_level"] = "low"

    return validated_schema

def threat_detector(session_id, image_b64, socketio_events_queue=None, state_request_queue=None):
    """Analyze image for threats and update session data"""
    print(f"[{os.getpid()}] [Processing Process] Calling threat_detector for session {session_id}...")

    vision_data = analyze_image_with_prompt(
        image_b64, "security_vision_prompt", "vision_schema"
    )

    # Validate and clean the vision data
    validated_vision_schema = validate_vision_schema(vision_data)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "vision_data": validated_vision_schema,
        "message": ""
    }

    # Extract face detection boolean
    face_detected = False
    if validated_vision_schema is not None:
        face_detected = validated_vision_schema.get("face_detected", False)

    # Update face detection for this session
    continue_logging = update_face_detection(session_id, face_detected, socketio_events_queue, state_request_queue)

    if not continue_logging:
        print(f"No face detected for session {session_id}, logging stopped")
        return

    if validated_vision_schema is None:
        message = "Vision data extraction failed."
        print(f"[{os.getpid()}] [Processing Process] {message}")
        log_entry["message"] = message
    else:
        print(f"[{os.getpid()}] [Processing Process] Vision data extracted: {validated_vision_schema}")

        # Save complete vision schema to session state
        if state_request_queue is not None:
            update_session_state(session_id, {"vision_schema": validated_vision_schema}, state_request_queue)
            print(f"[{os.getpid()}] [Processing Process] Saved complete vision schema to session {session_id}")

        # Trigger langgraph if threat level is high (with cooldown)
        threat_level = validated_vision_schema.get("threat_level", "low")
        dangerous_object = validated_vision_schema.get("dangerous_object", False)
        if (threat_level == "high" and dangerous_object == True) and socketio_events_queue is not None:
            if can_trigger_langgraph(session_id):
                try:
                    langgraph_trigger_event = {
                        "type": "trigger_langgraph",
                        "session_id": session_id,
                        "message": "I am here to visit someone"
                    }
                    socketio_events_queue.put_nowait(langgraph_trigger_event)
                    update_langgraph_trigger_time(session_id)
                    print(f"[{os.getpid()}] [Processing Process] Triggered langgraph for high threat level in session {session_id}")
                except Exception as e:
                    print(f"[{os.getpid()}] [Processing Process] Failed to trigger langgraph: {e}")
            else:
                print(f"[{os.getpid()}] [Processing Process] Langgraph trigger skipped for session {session_id} - cooldown active")

        is_dangerous = validated_vision_schema.get("dangerous_object", False)
        is_angry = validated_vision_schema.get("angry_face", False)

        if is_dangerous:
            message = "❌ Threat detected, security is notified!"
            print(message)
            log_entry["message"] = message
        elif is_angry:
            message = "⚠️ Chill bro, you are making me anxious."
            print(message)
            log_entry["message"] = message
        else:
            message = f"[{os.getpid()}] [Processing Process] No threat detected in image."
            print(message)
            log_entry["message"] = "No threat detected in image."

    write_log(session_id, log_entry)

def image_processing_function(image_queue, socketio_events_queue=None, state_request_queue=None):
    """Main image processing loop"""
    print(f"[{os.getpid()}] [Processing Process] Starting image processing...")
    try:
        print(f"[{os.getpid()}] [Processing Process] Entering processing loop...")
        while True:
            if not image_queue.empty():
                print(f"[{os.getpid()}] [Processing Process] Image queue has items. Processing latest one.")
                # Extract all items to get the latest one
                temp_images = []
                while not image_queue.empty():
                    temp_images.append(image_queue.get())

                if temp_images:
                    # Get the latest (last) image for processing
                    latest_image_queue_element = temp_images[-1]

                    # Put back all images except the one we're processing
                    for img in temp_images[:-1]:
                        image_queue.put(img)

                    # Extract session_id and image data
                    session_id = latest_image_queue_element.get("session_id", "unknown")
                    image_b64 = base64.b64encode(latest_image_queue_element["data"]).decode("utf-8")

                    threat_detector(session_id, image_b64, socketio_events_queue, state_request_queue)
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print(f"[{os.getpid()}] [Processing Process] KeyboardInterrupt caught. Shutting down processing.")
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Processing Process] Processing process exiting.")
