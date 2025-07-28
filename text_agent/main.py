#!/usr/bin/env python3
"""
Security Gate System - Main Entry Point

This is the main entry point for the security gate system.
It creates and runs a SecurityGateAgent instance.
"""

import sys
from cli import SecurityGateAgent, parse_arguments


def main():
    """Main entry point for the security gate system."""
    try:
        # Parse command-line arguments
        args = parse_arguments()

        # Check if API mode is requested
        if args.api_mode:
            print("🌐 Starting Security Gate System in API mode...")
            try:
                import uvicorn
                from api import app
                uvicorn.run(app, host="0.0.0.0", port=8001)
                return 0
            except ImportError:
                print("❌ FastAPI/Uvicorn not installed. Install with: pip install fastapi uvicorn")
                return 1
            except Exception as e:
                print(f"❌ API startup error: {e}")
                return 1
        else:
            # CLI mode (original behavior)
            print("💻 Starting Security Gate System in CLI mode...")

            # Create the security gate agent
            agent = SecurityGateAgent(
                history_mode=args.history_mode,
                camera_index=args.camera_index,
                enable_threat_detection=args.enable_threat_detection
            )

            # Run the agent
            exit_code = agent.run()
            return exit_code

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
