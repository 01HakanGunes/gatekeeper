"""
Security Gate System - Main Entry Point

This is the main entry point for the security gate system.
"""

import sys
import uvicorn
import socketio
from sockets import image_queue, face_detection_queue, socketio_events_queue, sio
from src.processing.image_processor import image_processing_function
import multiprocessing
import asyncio

def main():
    """Main entry point for the security gate system."""
    try:
        # Start image processing in a separate process
        processing_process = multiprocessing.Process(target=image_processing_function, args=(image_queue, face_detection_queue, socketio_events_queue))
        processing_process.start()



        # --- Socket.IO Integration ---
        print("🌐 Integrating Socket.IO with FastAPI...")
        # Wrap the FastAPI app with Socket.IO ASGI middleware
        # This creates the combined ASGI application
        asgi_app = socketio.ASGIApp(sio)
        print("🔗 FastAPI and Socket.IO combined into ASGI app")

        # --- Server Startup ---
        print("🌐 Starting Security Gate System (API + Socket.IO) on http://localhost:8001 ...")
        # Run the combined ASGI application using Uvicorn
        uvicorn.run(asgi_app, host="0.0.0.0", port=8001)

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
