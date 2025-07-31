import time
import os
import base64
from src.utils.llm_utilities import analyze_image_with_prompt

def threat_detector(image_b64):
    vision_data = analyze_image_with_prompt(
        image_b64, "threat_detector_prompt", "threat_schema"
    )

    if vision_data is None:
        print("Vision data extraction failed")
    else:
        is_dangerous = vision_data.get("dangerous_object", "unknown")
        is_angry = vision_data.get("angry_face", "unknown")

        if is_dangerous:
            print("❌ Threat detected, security is notified!")
        elif is_angry:
            print("⚠️ Chill bro, you are making me anxious.")

    time.sleep(0.1)  # Simulate some processing time

def image_processing_function(image_queue):
    print(f"[{os.getpid()}] [Processing Process] Starting image processing...")
    try:
        while True:
            if image_queue:
                latest_image = image_queue.popleft()
                image_b64 = base64.b64encode(latest_image["data"]).decode("utf-8")
                threat_detector(image_b64)
            else:
                time.sleep(2) # Wait for 2 seconds if the queue is empty
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Processing Process] KeyboardInterrupt caught. Shutting down processing."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Processing Process] Processing process exiting.")
