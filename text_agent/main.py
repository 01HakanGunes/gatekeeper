"""
Security Gate System - Main Entry Point

This is the main entry point for the security gate system.
"""

import sys
import uvicorn
from api import app, wait_for_ollama, image_queue
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
        processing_process = multiprocessing.Process(target=image_processing_function, args=(image_queue,))
        processing_process.start()

        print("🌐 Starting Security Gate System in API mode...")
        uvicorn.run(app, host="0.0.0.0", port=8001)
        
        # Terminate the processing process when the API server stops
        processing_process.terminate()
        processing_process.join()

        return 0

    except ImportError:
        print("❌ FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ API startup error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
