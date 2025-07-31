#!/usr/bin/env python3
"""
Security Gate System - Main Entry Point

This is the main entry point for the security gate system.
"""

import sys
import uvicorn
from api import app, wait_for_ollama

def main():
    """Main entry point for the security gate system."""
    try:
        # Check Ollama connection before starting the API
        if not wait_for_ollama():
            print("❌ Cannot start API: Ollama service is not available.", file=sys.stderr)
            return 1

        print("🌐 Starting Security Gate System in API mode...")
        uvicorn.run(app, host="0.0.0.0", port=8001)
        return 0

    except ImportError:
        print("❌ FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"❌ API startup error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
