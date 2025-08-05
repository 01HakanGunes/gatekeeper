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
