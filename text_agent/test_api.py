#!/usr/bin/env python3
"""
Simple test script for the Security Gate API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api():
    """Test the basic API functionality"""
    print("🧪 Testing Security Gate API")
    print("=" * 50)

    try:
        # Test root endpoint
        print("1. Testing root endpoint...")
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        print()

        # Test health check
        print("2. Testing health check...")
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            if not data.get("graph_initialized"):
                print("   ⚠️ Graph not initialized - this might cause issues")
        print()

        # Start a new session
        print("3. Starting new session...")
        response = requests.post(f"{BASE_URL}/start-session")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            session_id = data.get("session_id")
            if not session_id:
                print("   ❌ No session ID returned")
                return
        else:
            print(f"   ❌ Failed to start session: {response.text}")
            return
        print()

        # Test profile endpoint
        print("4. Getting initial profile...")
        response = requests.get(f"{BASE_URL}/profile/{session_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()

        # Test chat endpoint
        print("5. Testing chat with greeting...")
        chat_data = {"message": "Hello, I'm here for a meeting"}
        response = requests.post(f"{BASE_URL}/chat/{session_id}", json=chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Agent Response: {data.get('agent_response')}")
            print(f"   Session Complete: {data.get('session_complete')}")
        else:
            print(f"   ❌ Chat failed: {response.text}")
        print()

        # Test profile after chat
        print("6. Getting profile after chat...")
        response = requests.get(f"{BASE_URL}/profile/{session_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print()

        # Test another chat message
        print("7. Testing another chat message...")
        chat_data = {"message": "My name is John Doe and I'm here to see Alice Smith"}
        response = requests.post(f"{BASE_URL}/chat/{session_id}", json=chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Agent Response: {data.get('agent_response')}")
            print(f"   Session Complete: {data.get('session_complete')}")
        print()

        # Test concurrent sessions
        print("8. Testing concurrent session...")
        response2 = requests.post(f"{BASE_URL}/start-session")
        if response2.status_code == 200:
            session_id2 = response2.json().get("session_id")
            print(f"   Second session created: {session_id2}")

            # Send message to second session
            chat_data = {"message": "Hi, I'm visitor 2"}
            response = requests.post(f"{BASE_URL}/chat/{session_id2}", json=chat_data)
            if response.status_code == 200:
                print(f"   Second session response: {response.json().get('agent_response')}")

            # Clean up second session
            requests.post(f"{BASE_URL}/end-session/{session_id2}")
        print()

        # End original session
        print("9. Ending session...")
        response = requests.post(f"{BASE_URL}/end-session/{session_id}")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
        print()

        # Test health check after session end
        print("10. Final health check...")
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")

        print("\n✅ API test completed!")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Make sure the server is running.")
        print("   Start the API with: python main.py --api-mode")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_api()
