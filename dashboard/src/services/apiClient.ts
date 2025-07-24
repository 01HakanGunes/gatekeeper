import {
  API_BASE_URL,
  API_ENDPOINTS,
  ERROR_MESSAGES,
} from "../utils/constants";

export interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warning" | "error" | "debug";
  message: string;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface Message {
  id: string;
  content: string;
  timestamp: string;
  sender: "user" | "agent";
  status?: "sent" | "delivered" | "error";
}

export interface AgentStatus {
  online: boolean;
  lastSeen: string;
  activeConnections: number;
  uptime: number;
  version: string;
}

export interface SendMessageRequest {
  content: string;
  metadata?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(ERROR_MESSAGES.UNAUTHORIZED);
        }
        if (response.status >= 500) {
          throw new Error(ERROR_MESSAGES.SERVER_ERROR);
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof TypeError) {
        throw new Error(ERROR_MESSAGES.NETWORK_ERROR);
      }
      throw error;
    }
  }

  async getLogs(limit: number = 100): Promise<LogEntry[]> {
    const response = await this.request<ApiResponse<LogEntry[]>>(
      `${API_ENDPOINTS.LOGS}?limit=${limit}`,
    );
    return response.data;
  }

  async getMessages(limit: number = 50): Promise<Message[]> {
    const response = await this.request<ApiResponse<Message[]>>(
      `${API_ENDPOINTS.MESSAGES}?limit=${limit}`,
    );
    return response.data;
  }

  async getStatus(): Promise<AgentStatus> {
    const response = await this.request<ApiResponse<AgentStatus>>(
      API_ENDPOINTS.STATUS,
    );
    return response.data;
  }

  async sendMessage(messageRequest: SendMessageRequest): Promise<Message> {
    const response = await this.request<ApiResponse<Message>>(
      API_ENDPOINTS.SEND_MESSAGE,
      {
        method: "POST",
        body: JSON.stringify(messageRequest),
      },
    );
    return response.data;
  }

  async clearLogs(): Promise<void> {
    await this.request<ApiResponse<void>>(`${API_ENDPOINTS.LOGS}`, {
      method: "DELETE",
    });
  }
}

export const apiClient = new ApiClient();
export default ApiClient;
