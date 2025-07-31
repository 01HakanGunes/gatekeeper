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

### Upload Image
Upload an image for threat detection. The image is added to a queue for processing.

```http
POST /upload-image
```

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "image": "<base64_encoded_image_string>",
  "timestamp": "2025-07-31T12:00:00Z"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Image added to the queue",
  "image_id": "uuid-string"
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
2. **(Optional) Upload images** for threat analysis via `/upload-image`.
3. **Send messages** via `/chat/{session_id}` until `session_complete: true`
4. **Check progress** via `/profile/{session_id}`
5. **End session** when done

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

// Upload an image
const imageResponse = await fetch('http://localhost:8001/upload-image', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: session_id,
    image: "<base64_encoded_image_string>",
    timestamp: new Date().toISOString()
  })
});
const imageData = await imageResponse.json();

// Send message
const chatResponse = await fetch(`http://localhost:8001/chat/${session_id}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    message: "Hello, I'm here for a meeting"
  })
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

# Upload an image
curl -X POST http://localhost:8001/upload-image \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "image": "<base64_encoded_image_string>", "timestamp": "2025-07-31T12:00:00Z"}'

# Send message
curl -X POST http://localhost:8001/chat/your-session-id \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I am here for a meeting"}'

# Get profile
curl -X GET http://localhost:8001/profile/your-session-id

# End session
curl -X POST http://localhost:8001/end-session/your-session-id
```
```

## Notes

- Each session maintains its own conversation state
- Multiple concurrent sessions are supported
- Sessions persist until explicitly ended
- The `session_complete` flag indicates when screening is finished
- Always check for errors in API responses
