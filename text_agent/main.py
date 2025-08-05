# main.py
"""
Security Gate System - Main Entry Point

This is the main entry point for the security gate system.
"""

import sys
import uvicorn
import socketio
# Import the FastAPI app and queues from api.py
from api import app, wait_for_ollama, image_queue, face_detection_queue
# Import the Socket.IO server instance from sockets.py
from sockets import sio
from src.processing.image_processor import image_processing_function
import multiprocessing

def main():
    """Main entry point for the security gate system."""
    try:
        # Check Ollama connection before starting the API
        if not wait_for_ollama():
            print("❌ Cannot start API: Ollama service is not available.", file=sys.stderr)
            return 1

        # Start image processing in a separate process
        processing_process = multiprocessing.Process(target=image_processing_function, args=(image_queue, face_detection_queue))
        processing_process.start()

        # --- Socket.IO Integration ---
        print("🌐 Integrating Socket.IO with FastAPI...")
        # Wrap the FastAPI app with Socket.IO ASGI middleware
        # This creates the combined ASGI application
        combined_asgi_app = socketio.ASGIApp(socketio_server=sio, other_asgi_app=app)
        print("🔗 FastAPI and Socket.IO combined into ASGI app")

        # --- Server Startup ---
        print("🌐 Starting Security Gate System (API + Socket.IO) on http://0.0.0.0:8001 ...")
        # Run the combined ASGI application using Uvicorn
        uvicorn.run(combined_asgi_app, host="0.0.0.0", port=8001)

        # --- Cleanup ---
        print("🛑 Shutting down image processing...")
        processing_process.terminate()
        processing_process.join()
        print("✅ Image processing stopped.")

        return 0

    except ImportError as ie:
        print(f"❌ Dependency not installed: {ie}. Install with: pip install fastapi uvicorn python-socketio[asyncio_client]", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ Startup error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
