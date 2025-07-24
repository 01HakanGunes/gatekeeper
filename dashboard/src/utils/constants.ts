export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  LOGS: "/api/logs",
  MESSAGES: "/api/messages",
  STATUS: "/api/status",
  SEND_MESSAGE: "/api/send-message",
} as const;

export const UI_CONSTANTS = {
  MAX_LOG_ENTRIES: 1000,
  REFRESH_INTERVAL: 5000, // 5 seconds
  MESSAGE_MAX_LENGTH: 500,
} as const;

export const ERROR_MESSAGES = {
  NETWORK_ERROR: "Network error occurred. Please try again.",
  UNAUTHORIZED: "Unauthorized access. Please check your credentials.",
  SERVER_ERROR: "Server error occurred. Please try again later.",
  INVALID_MESSAGE: "Please enter a valid message.",
} as const;

export const LOG_LEVELS = {
  INFO: "info",
  WARNING: "warning",
  ERROR: "error",
  DEBUG: "debug",
} as const;

export type LogLevel = (typeof LOG_LEVELS)[keyof typeof LOG_LEVELS];
