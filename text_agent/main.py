#!/usr/bin/env python3
"""
Security Gate System - Main Application

This is the main entry point for the security gate system.
"""

import argparse
import os
import time
import requests
from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT, DEFAULT_HISTORY_MODE


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

    # Create initial state
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

    except KeyboardInterrupt:
        print("\n\n👋 Security session terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("Please contact system administrator.")


if __name__ == "__main__":
    main()
