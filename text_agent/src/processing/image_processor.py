import time
import os
import base64
from src.utils.llm_utilities import analyze_image_with_prompt

def threat_detector(image_b64):
    print(f"[{os.getpid()}] [Processing Process] Calling threat_detector...")
    vision_data = analyze_image_with_prompt(
        image_b64, "threat_detector_prompt", "threat_schema"
    )

    if vision_data is None:
        print(f"[{os.getpid()}] [Processing Process] Vision data extraction failed.")
    else:
        print(f"[{os.getpid()}] [Processing Process] Vision data extracted: {vision_data}")
        is_dangerous = vision_data.get("dangerous_object", False)
        is_angry = vision_data.get("angry_face", False)

        if is_dangerous:
            print("❌ Threat detected, security is notified!")
        elif is_angry:
            print("⚠️ Chill bro, you are making me anxious.")
        else:
            print(f"[{os.getpid()}] [Processing Process] No threat detected in image.")

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
