import time
import os
import base64
import json
from datetime import datetime
from src.utils.llm_utilities import analyze_image_with_prompt

LOG_FILE = "./data/logs/vision_data_log.json"
FACE_DETECTION_FILE = "./data/shared/face_detected.json"
LOG_LIMIT = 10
FACE_QUEUE_LIMIT = 4

def write_log(log_entry):
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    logs.append(log_entry)

    # Keep only the last 10 logs
    logs = logs[-LOG_LIMIT:]

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)

def write_face_detection_to_file(face_detection_queue):
    """Write current face detection queue values to shared JSON file"""
    face_values = []
    temp_queue = []

    # Extract all values from queue while preserving them
    while not face_detection_queue.empty():
        try:
            value = face_detection_queue.get_nowait()
            temp_queue.append(value)
            face_values.append(value)
        except:
            break

    # Put values back into queue
    for value in temp_queue:
        face_detection_queue.put(value)

    # Write to shared JSON file
    os.makedirs(os.path.dirname(FACE_DETECTION_FILE), exist_ok=True)
    with open(FACE_DETECTION_FILE, "w") as f:
        json.dump(face_values, f, indent=4)

    # Check if all face detection values are False and queue is full
    if len(face_values) == FACE_QUEUE_LIMIT and all(value == False for value in face_values):
        print(f"[{os.getpid()}] [Processing Process] All face detection values are False. Clearing vision data log.")
        # Clear the vision data log
        with open(LOG_FILE, "w") as f:
            json.dump([], f, indent=4)
        print(f"[{os.getpid()}] [Processing Process] Stopping image processing - no faces detected.")
        return False  # Signal to stop logging

    return True  # Continue logging

def threat_detector(image_b64, face_detection_queue):
    print(f"[{os.getpid()}] [Processing Process] Calling threat_detector...")
    vision_data = analyze_image_with_prompt(
        image_b64, "security_vision_prompt", "vision_schema"
    )

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "vision_data": vision_data,
        "message": ""
    }

    # Extract face detection boolean and add to queue
    face_detected = False
    if vision_data is not None:
        # Check if there's any face-related data (angry_face or general face detection)
        face_detected = vision_data.get("angry_face", False) or vision_data.get("face_detected", False)

    # Add face detection result to queue
    if face_detection_queue.qsize() >= FACE_QUEUE_LIMIT:
        # Remove oldest entry if queue is full
        try:
            face_detection_queue.get_nowait()
        except:
            pass  # Queue might be empty due to race condition

    face_detection_queue.put(face_detected)
    print(f"[{os.getpid()}] [Processing Process] Face detected: {face_detected}, Queue size: {face_detection_queue.qsize()}")

    continue_logging = write_face_detection_to_file(face_detection_queue)

    if not continue_logging:
        print("no face detected so the logging stopped")
        return

    if vision_data is None:
        message = "Vision data extraction failed."
        print(f"[{os.getpid()}] [Processing Process] {message}")
        log_entry["message"] = message
    else:
        print(f"[{os.getpid()}] [Processing Process] Vision data extracted: {vision_data}")
        is_dangerous = vision_data.get("dangerous_object", False)
        is_angry = vision_data.get("angry_face", False)

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

    write_log(log_entry)
    time.sleep(0.1)  # Simulate some processing time

def image_processing_function(image_queue, face_detection_queue):
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
                    latest_image = temp_images[-1]

                    # Put back all images except the one we're processing
                    for img in temp_images[:-1]:
                        image_queue.put(img)

                    image_b64 = base64.b64encode(latest_image["data"]).decode("utf-8")
                    threat_detector(image_b64, face_detection_queue)

            else:
                time.sleep(1)
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Processing Process] KeyboardInterrupt caught. Shutting down processing."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Processing Process] Processing process exiting.")
