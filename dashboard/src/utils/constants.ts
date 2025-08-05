export const API_BASE_URL = "http://localhost:8001";

export const API_ENDPOINTS = {
  START_SESSION: "/start-session",
  CHAT: "/chat",
  PROFILE: "/profile",
  END_SESSION: "/end-session",
  HEALTH: "/health",
  IMAGE_UPLOAD: "/upload-image",
  THREAT_LOGS: "/threat-logs",
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
  SESSION_ERROR: "Session error. Please start a new session.",
  CAMERA_ERROR: "Camera access denied or not available.",
  IMAGE_CAPTURE_ERROR: "Failed to capture image from camera.",
} as const;

export const SESSION_STATUS = {
  ACTIVE: "active",
  COMPLETED: "completed",
  ENDED: "ended",
} as const;

export type SessionStatus =
  (typeof SESSION_STATUS)[keyof typeof SESSION_STATUS];
