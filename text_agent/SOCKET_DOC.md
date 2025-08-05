# Socket.IO API Documentation for Security Gate System

This document outlines the Socket.IO communication channels for the security gate system, designed for frontend developers to integrate real-time features.

## Overview

The system uses **Socket.IO** with an ASGI server for real-time communication, integrated with FastAPI. CORS is set to allow all origins (`*`) for development.

## Connection Events

### `connect`

- **Triggered**: When a client connects to the server.
- **Emits**:
  - `status`: `{ msg: "Connected to Security Gate System" }`
  - `system_status`: `{ healthy: true, active_sessions: 0 }`
- **Frontend Action**: Listen for these events to confirm connection and system health.

### `disconnect`

- **Triggered**: When a client disconnects.
- **Frontend Action**: Handle UI updates for disconnection (e.g., disable features).

## Core API Events

### `start_session`

- **Payload**: `{}` (no data required)
- **Description**: Starts a new security gate session, generating a unique `session_id`.
- **Emits**:
  - `session_started`: `{ session_id: string, status: "success" | "error", message: string }`
- **Frontend Action**: Store `session_id` for subsequent requests.

### `send_message`

- **Payload**: `{ session_id: string, message: string }`
- **Description**: Sends a user message for processing. Updates session state and returns agent response.
- **Emits**:
  - `chat_response`: `{ agent_response: string, session_complete: boolean }`
  - `error`: `{ msg: string }` (if session_id missing or invalid)
  - `session_update`: `{ type: "session_complete", profile: object, final_response: string }` (if session completes)
- **Frontend Action**: Display `agent_response` and handle session completion (e.g., show final profile).

### `get_profile`

- **Payload**: `{ session_id: string }`
- **Description**: Retrieves the current visitor profile for a session.
- **Emits**:
  - `profile_data`: `{ visitor_profile: object, decision: any, decision_confidence: any, session_active: boolean }`
  - `error`: `{ msg: string }` (if session_id missing or invalid)
- **Frontend Action**: Display profile data in UI.

### `end_session`

- **Payload**: `{ session_id: string }`
- **Description**: Ends a session and removes its state.
- **Emits**:
  - `session_ended`: `{ status: "success" | "error", message: string }`
  - `session_update`: `{ type: "session_ended", message: string }` (to room)
- **Frontend Action**: Clear session data and update UI.

### `upload_image`

- **Payload**: `{ session_id: string, image: string, timestamp?: string }`
- **Description**: Queues a base64 image for processing.
- **Emits**:
  - `image_upload_response`: `{ status: "success" | "error", message: string, image_id?: string }`
  - `error`: `{ msg: string }` (if invalid data)
- **Frontend Action**: Show upload status and store `image_id` if needed.

### `request_health_check`

- **Payload**: `{}`
- **Description**: Checks system health.
- **Emits**:
  - `health_status`: `{ status: "healthy", graph_initialized: boolean, active_sessions: number }`
- **Frontend Action**: Update UI with system status.

### `request_threat_logs`

- **Payload**: `{}`
- **Description**: Retrieves threat detection logs.
- **Emits**:
  - `threat_logs`: `array` (log data)
  - `error`: `{ msg: string }` (if log file missing or invalid)
- **Frontend Action**: Display logs in UI.

## Session Subscription Events

### `join_session_updates`

- **Payload**: `{ session_id: string }`
- **Description**: Subscribes client to a session’s updates (joins a room named after `session_id`).
- **Emits**:
  - `status`: `{ msg: string }`
  - `error`: `{ msg: "session_id required" }`
- **Frontend Action**: Listen for `session_update` events for real-time session updates.

### `leave_session_updates`

- **Payload**: `{ session_id: string }`
- **Description**: Unsubscribes client from session updates.
- **Emits**:
  - `status`: `{ msg: string }`
  - `error`: `{ msg: "session_id required" }`
- **Frontend Action**: Stop processing updates for the session.

## General Notifications

### `system_status`

- **Emitted**: By server to all clients.
- **Payload**: `{ healthy: boolean, active_sessions: number, ... }`
- **Frontend Action**: Update system status indicators.

### `notification`

- **Emitted**: By server to all clients.
- **Payload**: `{ message: string }`
- **Frontend Action**: Display general notifications.

### `session_update`

- **Emitted**: To clients in a session’s room.
- **Payload**: `{ type: string, profile?: object, final_response?: string, message?: string }`
- **Frontend Action**: Update UI with session-specific changes (e.g., completion or end).
