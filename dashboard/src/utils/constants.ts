// Deploy dev
export const SOCKET_BASE_URL = "https://192.168.0.86";

// Local dev
// export const SOCKET_BASE_URL = "http://localhost:8001";

export const SOCKET_EVENTS = {
  // Client to server events
  SEND_MESSAGE: "send_message",
  GET_PROFILE: "get_profile",
  REQUEST_HEALTH_CHECK: "request_health_check",
  UPLOAD_IMAGE: "upload_image",
  REQUEST_THREAT_LOGS: "request_threat_logs",
  GET_CAMERA_LIST: "getCameraList",
  REGISTER_CAMERA: "registerCamera",

  // Server to client events (responses)
  CHAT_RESPONSE: "chat_response",
  PROFILE_DATA: "profile_data",
  HEALTH_STATUS: "health_status",
  IMAGE_UPLOAD_RESPONSE: "image_upload_response",
  THREAT_LOGS: "threat_logs",
  CAMERA_LIST: "cameraList",
  CAMERA_REGISTERED: "cameraRegistered",

  // Real-time events from server
  SYSTEM_STATUS: "system_status",
  NOTIFICATION: "notification",
  STATUS: "status",
  ERROR: "error",

  // Connection events
  CONNECT: "connect",
  DISCONNECT: "disconnect",
} as const;

export const UI_CONSTANTS = {
  REFRESH_INTERVAL: 5000, // 5 seconds
  MESSAGE_MAX_LENGTH: 500,
  CAMERA_WIDTH: 640,
  CAMERA_HEIGHT: 480,
  IMAGE_QUALITY: 0.8,
} as const;

export const ERROR_MESSAGES = {
  NETWORK_ERROR: "Network error occurred. Please try again.",
  UNAUTHORIZED: "Unauthorized access. Please check your credentials.",
  SERVER_ERROR: "Server error occurred. Please try again later.",
  INVALID_MESSAGE: "Please enter a valid message.",

  CAMERA_ERROR: "Camera access denied or not available.",
  IMAGE_CAPTURE_ERROR: "Failed to capture image from camera.",
} as const;
