import {
  API_BASE_URL,
  API_ENDPOINTS,
  ERROR_MESSAGES,
} from "../utils/constants";

export interface SessionResponse {
  session_id: string;
  status: string;
  message: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  agent_response: string;
  session_complete: boolean;
}

export interface VisitorProfile {
  name?: string;
  purpose?: string;
  contact_person?: string;
  threat_level?: string;
  affiliation?: string;
  id_verified?: boolean;
}

export interface ProfileResponse {
  visitor_profile: VisitorProfile;
  decision: string;
  decision_confidence: number;
  session_active: boolean;
}

export interface EndSessionResponse {
  status: string;
  message: string;
}

export interface HealthResponse {
  status: string;
  graph_initialized: boolean;
  active_sessions: number;
}

export interface Message {
  id: string;
  content: string;
  timestamp: string;
  sender: "user" | "agent";
  session_complete?: boolean;
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
        if (response.status === 404) {
          throw new Error("Session not found");
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

  async startSession(): Promise<SessionResponse> {
    return await this.request<SessionResponse>(API_ENDPOINTS.START_SESSION, {
      method: "POST",
    });
  }

  async sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
    return await this.request<ChatResponse>(
      `${API_ENDPOINTS.CHAT}/${sessionId}`,
      {
        method: "POST",
        body: JSON.stringify({ message }),
      },
    );
  }

  async getProfile(sessionId: string): Promise<ProfileResponse> {
    return await this.request<ProfileResponse>(
      `${API_ENDPOINTS.PROFILE}/${sessionId}`,
    );
  }

  async endSession(sessionId: string): Promise<EndSessionResponse> {
    return await this.request<EndSessionResponse>(
      `${API_ENDPOINTS.END_SESSION}/${sessionId}`,
      {
        method: "POST",
      },
    );
  }

  async getHealth(): Promise<HealthResponse> {
    return await this.request<HealthResponse>(API_ENDPOINTS.HEALTH);
  }
}

export const apiClient = new ApiClient();
export default ApiClient;
