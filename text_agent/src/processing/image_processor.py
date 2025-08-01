import time
import os
import base64
import json
from datetime import datetime
from src.utils.llm_utilities import analyze_image_with_prompt

LOG_FILE = "./data/logs/threat_detector.json"
LOG_LIMIT = 10

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

def threat_detector(image_b64):
    print(f"[{os.getpid()}] [Processing Process] Calling threat_detector...")
    vision_data = analyze_image_with_prompt(
        image_b64, "threat_detector_prompt", "threat_schema"
    )

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "vision_data": vision_data,
        "message": ""
    }

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

def image_processing_function(image_queue):
    print(f"[{os.getpid()}] [Processing Process] Starting image processing...")
    try:
        print(f"[{os.getpid()}] [Processing Process] Entering processing loop...")
        while True:
            if not image_queue.empty():
                print(f"[{os.getpid()}] [Processing Process] Image queue has items. Processing one.")
                latest_image = image_queue.get()
                image_b64 = base64.b64encode(latest_image["data"]).decode("utf-8")
                threat_detector(image_b64)
            else:
                # The get() method will block until an item is available, so this sleep is not strictly necessary
                # but it can prevent a tight loop if the queue is frequently empty.
                time.sleep(1)
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Processing Process] KeyboardInterrupt caught. Shutting down processing."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Processing Process] Processing process exiting.")
