#!/usr/bin/env python3
"""
Security Gate System - Main Application

This is the main entry point for the security gate system.
"""

import argparse
import os
import time
import requests
import multiprocessing
from src.utils import camera as camera_utils
from src.utils import analyze_image_with_prompt

from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT, DEFAULT_HISTORY_MODE


def camera_process_function(image_queue, interval_seconds=2, camera_index=0):
    """
    Function to run in a separate process for camera operations.
    Captures images and adds filenames to the shared queue.
    """
    print(
        f"[{os.getpid()}] [Camera Process] Starting camera operations (interval: {interval_seconds}s, camera: {camera_index})..."
    )
    count = 0
    try:
        while True:
            image_filename = f"data/images/captured_image_{count}.jpg"
            success = camera_utils.capture_photo(image_filename)
            if not success:
                print(
                    f"[{os.getpid()}] [Camera Process] Failed to capture image {count}. Retrying..."
                )
                time.sleep(0.5)
                continue
            # Add the image filename to the queue
            image_queue.put(image_filename)
            count += 1
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Camera Process] KeyboardInterrupt caught. Shutting down camera operations."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Camera Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Camera Process] Camera process exiting.")


def threat_detector(image_filename):
    """
    Placeholder for dummy functionality to process the captured image.
    This function runs within the processing process.
    """
    print(
        f"[{os.getpid()}] [Processing Process]   --> Dummy processing image ID: {image_filename}."
    )

    vision_data = analyze_image_with_prompt(
        image_filename, "threat_detector_prompt", "threat_schema"
    )

    if vision_data == None:
        print("Vision data extraction failed")
    else:
        is_dangerous = vision_data.get("dangerous_object", "unknown")
        is_angry = vision_data.get("angry_face", "unknown")

        if is_dangerous:
            print("❌ Threat detected, security is notified!")
            # TODO can use tool here
        elif is_angry:
            print("⚠️ Chill bro, you are making me anxious.")

    time.sleep(0.1)  # Simulate some processing time


def image_processing_function(image_queue):
    """
    Function to run in a separate process for processing images from the queue.
    Dequeues and processes images one by one, then deletes them.
    """
    print(f"[{os.getpid()}] [Processing Process] Starting image processing...")
    try:
        while True:
            try:
                # Non-blocking check for queue items
                if not image_queue.empty():
                    image_filename = image_queue.get()
                    print(
                        f"[{os.getpid()}] [Processing Process] Dequeued {image_filename}"
                    )
                    threat_detector(image_filename)
                    # Delete the processed image
                    try:
                        os.remove(image_filename)
                        print(
                            f"[{os.getpid()}] [Processing Process] Deleted {image_filename}"
                        )
                    except OSError as e:
                        print(
                            f"[{os.getpid()}] [Processing Process] Failed to delete {image_filename}: {e}"
                        )
                else:
                    time.sleep(0.1)  # Brief sleep to avoid busy-waiting
            except Exception as e:
                print(
                    f"[{os.getpid()}] [Processing Process] Error processing image: {e}"
                )
                time.sleep(0.5)  # Prevent rapid error looping
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Processing Process] KeyboardInterrupt caught. Shutting down processing."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Processing Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Processing Process] Processing process exiting.")


def wait_for_ollama():
    """Wait for Ollama service to be ready before starting the application."""
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    max_retries = 30  # Wait up to 30 seconds
    retry_delay = 1  # 1 second between retries

    print(f"🔍 Checking Ollama connection at {ollama_host}...")

    for attempt in range(max_retries):
        try:
            response = requests.get(f"{ollama_host}/api/tags", timeout=5)
            if response.status_code == 200:
                print(f"✅ Ollama is ready at {ollama_host}")
                return True
        except (requests.ConnectionError, requests.Timeout):
            if attempt == 0:
                print(f"⏳ Waiting for Ollama to start...")
            time.sleep(retry_delay)
            continue

    print(
        f"❌ Failed to connect to Ollama at {ollama_host} after {max_retries} seconds"
    )
    print("Make sure Ollama is running and accessible")
    return False


def parse_arguments():
    """Parse command-line arguments for the security gate system."""
    parser = argparse.ArgumentParser(
        description="Security Gate System - AI-powered visitor screening",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Use default summarize mode
  python main.py --history-mode summarize  # Use summarize mode (AI-powered)
  python main.py --history-mode shorten    # Use shorten mode (keep recent messages)
        """,
    )

    parser.add_argument(
        "--history-mode",
        choices=["summarize", "shorten"],
        default=DEFAULT_HISTORY_MODE,
        help="Message history management strategy (default: %(default)s)",
    )

    # New argument for camera index
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Index of the camera to use (default: 0, typically the default webcam)",
    )

    return parser.parse_args()


def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Check Ollama connection before starting
    if not wait_for_ollama():
        print("❌ Cannot start application: Ollama service is not available")
        return 1

    # Set global history mode for use throughout the application
    import config.settings as settings

    settings.CURRENT_HISTORY_MODE = args.history_mode

    print("=" * 60)
    print("🏢 SECURITY GATE SYSTEM Actions version")
    print("=" * 60)
    print("Welcome to the security checkpoint!")
    print("This system will ask you questions to verify your visit.")
    print(f"📋 History management mode: {args.history_mode}")
    print(f"📸 Camera index to use: {args.camera_index}")  # Print camera index
    print("=" * 60)

    # Create the security graph
    graph = create_security_graph()

    # Generate and save graph visualization
    print("📊 Generating graph visualization...")
    try:
        compiled_graph = graph.get_graph()

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
        print("   (This is optional and won't affect the main functionality)")

    # --- Start the Camera and Processing Processes Here ---
    image_queue = multiprocessing.Queue()

    camera_p = multiprocessing.Process(
        target=camera_process_function,
        args=(image_queue, 2, args.camera_index),
    )
    camera_p.daemon = True
    camera_p.start()
    print(f"[Main Process] Camera process started with PID: {camera_p.pid}")

    processing_p = multiprocessing.Process(
        target=image_processing_function,
        args=(image_queue,),
    )
    processing_p.daemon = True
    processing_p.start()
    print(f"[Main Process] Processing process started with PID: {processing_p.pid}")
    # --- End Camera and Processing Processes Start ---

    while True:
        initial_state = create_initial_state()
        try:
            # Run the security screening process
            result = graph.invoke(
                initial_state, {"recursion_limit": DEFAULT_RECURSION_LIMIT}
            )

            # Display final results
            print("\n" + "=" * 60)
            print("🏁 FINAL RESULTS")
            print("=" * 60)
            print(f"Final decision: {result['decision']}")
            if result["messages"]:
                print(f"Last message: {result['messages'][-1].content}")

            # Display visitor profile summary
            print("\n📋 VISITOR PROFILE SUMMARY:")
            profile = result["visitor_profile"]
            for field, value in profile.items():
                status = "✅" if value is not None and value != "-1" else "❌"
                print(f"  {status} {field.replace('_', ' ').title()}: {value}")

            print(
                "\n🔄 Restarting security gate for next visitor... (Press Ctrl+C to exit)"
            )

        except KeyboardInterrupt:
            print("\n\n👋 Security session terminated by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please contact system administrator.")
            break

    # --- Graceful Shutdown of Camera and Processing Processes ---
    # This block will be executed when the main loop breaks (e.g., via Ctrl+C)
    for proc, name in [(camera_p, "Camera"), (processing_p, "Processing")]:
        if proc.is_alive():
            print(f"[Main Process] Terminating {name} process (PID: {proc.pid})...")
            proc.terminate()
            proc.join(timeout=5)
            if proc.is_alive():
                print(
                    f"[Main Process] {name} process (PID: {proc.pid}) did not terminate gracefully, killing."
                )
                proc.kill()
    print("[Main Process] All processes handled. Exiting main application.")
    # --- End Graceful Shutdown ---


if __name__ == "__main__":
    main()
