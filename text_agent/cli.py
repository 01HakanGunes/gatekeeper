#!/usr/bin/env python3
"""
Security Gate System - Agent Module

This module contains the SecurityGateAgent class and related functionality
for the security gate system.
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


def camera_process_function(
    image_stack,
    stack_lock,
    interval_seconds=2,
    camera_index=0,
    max_images=20,
    enable_camera=True,
):
    """
    Function to run in a separate process for camera operations.
    Captures images and adds filenames to the shared stack.
    """
    print(
        f"[{os.getpid()}] [Camera Process] Starting camera operations (interval: {interval_seconds}s, camera: {camera_index}, enabled: {enable_camera})..."
    )
    count = 0
    try:
        while enable_camera:
            image_filename = f"data/images/captured_image_{count}.jpg"
            success = camera_utils.capture_photo(image_filename)
            if not success:
                print(
                    f"[{os.getpid()}] [Camera Process] Failed to capture image {count}. Retrying..."
                )
                time.sleep(0.5)
                continue
            # Add the image filename to the stack, keeping only the last max_images
            with stack_lock:
                if len(image_stack) >= max_images:
                    oldest_image = image_stack.pop(0)
                    try:
                        os.remove(oldest_image)
                        print(
                            f"[{os.getpid()}] [Camera Process] Deleted oldest image {oldest_image}"
                        )
                    except OSError as e:
                        print(
                            f"[{os.getpid()}] [Camera Process] Failed to delete {oldest_image}: {e}"
                        )
                image_stack.append(image_filename)
            count += 1
            time.sleep(interval_seconds)
        if not enable_camera:
            print(f"[{os.getpid()}] [Camera Process] Camera is disabled, exiting loop.")
    except KeyboardInterrupt:
        print(
            f"[{os.getpid()}] [Camera Process] KeyboardInterrupt caught. Shutting down camera operations."
        )
    except Exception as e:
        print(f"[{os.getpid()}] [Camera Process] An unexpected error occurred: {e}")
    finally:
        print(f"[{os.getpid()}] [Camera Process] Camera process exiting.")


def threat_detector(image_filename):

    vision_data = analyze_image_with_prompt(
        image_filename, "threat_detector_prompt", "threat_schema"
    )

    if vision_data is None:
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


def image_processing_function(image_stack, stack_lock, enable_threat_detection=False):
    """
    Function to run in a separate process for processing images from the stack.
    Processes the most recent image (last item) and deletes it.
    """
    print(
        f"[{os.getpid()}] [Processing Process] Starting image processing... Threat detection enabled: {enable_threat_detection}"
    )
    try:
        while True:
            try:
                # Check for stack items and process the most recent one
                with stack_lock:
                    if image_stack:
                        image_filename = image_stack.pop()  # Get the last item (LIFO)
                    else:
                        time.sleep(0.1)  # Brief sleep to avoid busy-waiting
                        continue

                if enable_threat_detection:
                    threat_detector(image_filename)
                # Delete the processed image
                try:
                    os.remove(image_filename)
                except OSError as e:
                    print(
                        f"[{os.getpid()}] [Processing Process] Failed to delete {image_filename}: {e}"
                    )
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
                print("⏳ Waiting for Ollama to start...")
            time.sleep(retry_delay)
            continue

    print(
        f"❌ Failed to connect to Ollama at {ollama_host} after {max_retries} seconds"
    )
    print("Make sure Ollama is running and accessible")
    return False


class SecurityGateAgent:
    """
    Security Gate Agent - Handles the main security screening process
    """

    def __init__(self, history_mode=DEFAULT_HISTORY_MODE, camera_index=0, enable_threat_detection=False):
        self.history_mode = history_mode
        self.camera_index = camera_index
        self.enable_threat_detection = enable_threat_detection
        self.graph = None
        self.manager = None
        self.image_stack = None
        self.stack_lock = None
        self.camera_process = None
        self.processing_process = None

    def setup(self):
        """Initialize the security gate system"""
        # Check Ollama connection
        if not wait_for_ollama():
            print("❌ Cannot start application: Ollama service is not available")
            return False

        # Set global history mode
        import config.settings as settings
        settings.CURRENT_HISTORY_MODE = self.history_mode

        print("=" * 60)
        print("🏢 SECURITY GATE SYSTEM Actions version")
        print("=" * 60)
        print("Welcome to the security checkpoint!")
        print("This system will ask you questions to verify your visit.")
        print(f"📋 History management mode: {self.history_mode}")
        print(f"📸 Camera index to use: {self.camera_index}")
        print("=" * 60)

        # Create the security graph
        self.graph = create_security_graph()

        # Generate and save graph visualization
        self._generate_graph_visualization()

        # Setup camera and processing processes
        self._setup_camera_processes()

        return True

    def _generate_graph_visualization(self):
        print("📊 Generating graph visualization...")

        if self.graph is None:
                print("⚠️ Graph not initialized, skipping visualization")
                return

        try:
            compiled_graph = self.graph.get_graph()

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

    def _setup_camera_processes(self):
        """Setup camera and processing processes"""
        self.manager = multiprocessing.Manager()
        self.image_stack = self.manager.list()
        self.stack_lock = self.manager.Lock()

        self.camera_process = multiprocessing.Process(
            target=camera_process_function,
            args=(
                self.image_stack,
                self.stack_lock,
                2,
                self.camera_index,
                20,
                self.enable_threat_detection,
            ),
        )
        self.camera_process.daemon = True
        self.camera_process.start()
        print(
            f"[Main Process] Camera process started with PID: {self.camera_process.pid} "
            f"(Camera enabled: {self.enable_threat_detection})"
        )

        self.processing_process = multiprocessing.Process(
            target=image_processing_function,
            args=(self.image_stack, self.stack_lock, self.enable_threat_detection),
        )
        self.processing_process.daemon = True
        self.processing_process.start()
        print(
            f"[Main Process] Processing process started with PID: {self.processing_process.pid} "
            f"(Threat detection enabled: {self.enable_threat_detection})"
        )



    def run_security_session(self):
        """Run a single security screening session"""
        initial_state = create_initial_state()

        if self.graph is None:
                print("⚠️ Graph not initialized, skipping visualization")
                return

        result = self.graph.invoke(
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

        return result

    def run(self):
        """Run the main security gate loop"""
        if not self.setup():
            return 1

        try:
            while True:
                self.run_security_session()
        except KeyboardInterrupt:
            print("\n\n👋 Security session terminated by user. Goodbye!")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please contact system administrator.")
        finally:
            self.cleanup()

        return 0

    def cleanup(self):
        """Clean up processes and resources"""
        # Graceful shutdown of camera and processing processes
        for proc, name in [(self.camera_process, "Camera"), (self.processing_process, "Processing")]:
            if proc and proc.is_alive():
                print(f"[Main Process] Terminating {name} process (PID: {proc.pid})...")
                proc.terminate()
                proc.join(timeout=5)
                if proc.is_alive():
                    print(
                        f"[Main Process] {name} process (PID: {proc.pid}) did not terminate gracefully, killing."
                    )
                    proc.kill()

        # Clean up any remaining images in the stack
        if self.image_stack and self.stack_lock:
            with self.stack_lock:
                while self.image_stack:
                    image_filename = self.image_stack.pop()
                    try:
                        os.remove(image_filename)
                        print(f"[Main Process] Cleaned up {image_filename}")
                    except OSError as e:
                        print(f"[Main Process] Failed to clean up {image_filename}: {e}")

        print("[Main Process] All processes handled. Exiting main application.")


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

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Index of the camera to use (default: 0, typically the default webcam)",
    )

    parser.add_argument(
        "--enable-threat-detection",
        action="store_true",
        default=False,
        help="Enable threat detection on captured images (default: disabled)",
    )

    parser.add_argument(
        "--api-mode",
        action="store_true",
        default=False,
        help="Start the application in API mode using FastAPI (default: CLI mode)",
    )

    return parser.parse_args()
