#!/usr/bin/env python3
"""
Security Gate System - Main Application

This is the main entry point for the security gate system.
"""

from src.core.graph import create_security_graph, create_initial_state
from config.settings import DEFAULT_RECURSION_LIMIT


def main():
    print("=" * 60)
    print("🏢 SECURITY GATE SYSTEM")
    print("=" * 60)
    print("Welcome to the security checkpoint!")
    print("This system will ask you questions to verify your visit.")
    print("=" * 60)

    # Create the security graph
    graph = create_security_graph()

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
