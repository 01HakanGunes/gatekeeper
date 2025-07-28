# Security Gate API Documentation

## Base URL
```
http://localhost:8001
```

## Authentication
None required

## Endpoints

### Start Session
Create a new visitor screening session.

```http
POST /start-session
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "status": "success",
  "message": "Session started successfully"
}
```

### Send Message
Send a message to the security agent for a specific session.

```http
POST /chat/{session_id}
```

**Request Body:**
```json
{
  "message": "Hello, I'm here for a meeting"
}
```

**Response:**
```json
{
  "agent_response": "Welcome! Can you tell me your name and who you're here to see?",
  "session_complete": false
}
```

### Get Profile
Get the current visitor profile and session status.

```http
GET /profile/{session_id}
```

**Response:**
```json
{
  "visitor_profile": {
    "name": "John Doe",
    "purpose": "meeting",
    "contact_person": "Alice Smith",
    "threat_level": "low",
    "affiliation": "Company ABC",
    "id_verified": true
  },
  "decision": "approved",
  "decision_confidence": 0.9,
  "session_active": true
}
```

### End Session
Terminate a visitor screening session.

```http
POST /end-session/{session_id}
```

**Response:**
```json
{
  "status": "success",
  "message": "Session ended successfully"
}
```

### Health Check
Check API status and active sessions.

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "graph_initialized": true,
  "active_sessions": 2
}
```

## Workflow

1. **Start session** → Get `session_id`
2. **Send messages** via `/chat/{session_id}` until `session_complete: true`
3. **Check progress** via `/profile/{session_id}`
4. **End session** when done

## Error Responses

- `404` - Session not found
- `500` - Server error
- `405` - Method not allowed

## Example Usage

### JavaScript/Fetch
```javascript
// Start session
const sessionResponse = await fetch('http://localhost:8001/start-session', {
  method: 'POST'
});
const { session_id } = await sessionResponse.json();

// Send message
const chatResponse = await fetch(`http://localhost:8001/chat/${session_id}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: "Hello, I'm here for a meeting" })
});
const chatData = await chatResponse.json();

// Check profile
const profileResponse = await fetch(`http://localhost:8001/profile/${session_id}`);
const profileData = await profileResponse.json();

// End session
await fetch(`http://localhost:8001/end-session/${session_id}`, {
  method: 'POST'
});
```

### cURL
```bash
# Start session
curl -X POST http://localhost:8001/start-session

# Send message
curl -X POST http://localhost:8001/chat/session-id \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I am here for a meeting"}'

# Get profile
curl -X GET http://localhost:8001/profile/session-id

# End session
curl -X POST http://localhost:8001/end-session/session-id
```

## Notes

- Each session maintains its own conversation state
- Multiple concurrent sessions are supported
- Sessions persist until explicitly ended
- The `session_complete` flag indicates when screening is finished
- Always check for errors in API responses