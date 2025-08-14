import { io, Socket } from "socket.io-client";
import { SOCKET_BASE_URL, SOCKET_EVENTS } from "../utils/constants";

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  agent_response: string;
  session_complete: boolean;
}

export interface ImageUploadRequest {
  image: string;
  timestamp?: string;
}

export interface ImageUploadResponse {
  status: "success" | "error";
  message: string;
  image_id?: string;
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
  decision: string | null;
  decision_confidence: number | null;
  session_active: boolean;
}

export interface HealthResponse {
  status: "healthy";
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

export interface ThreatLog {
  timestamp: string;
  level: string;
  message: string;
  source_ip: string;
  details: string;
}

export interface Camera {
  id: string;
  location: string;
  ip_address: string;
  resolution: string;
  status: "online" | "offline";
}

export interface CameraListResponse {
  cameras: Camera[];
}

export interface CameraRegistrationResponse {
  camera_id: string;
  session_id: string;
  message: string;
}

export interface SystemStatus {
  healthy: boolean;
  active_sessions: number;
  [key: string]: boolean | number | string;
}

export interface Notification {
  message: string;
}

export interface StatusResponse {
  msg: string;
}

export interface ErrorResponse {
  msg: string;
}

export type ConnectionStatus =
  | "connecting"
  | "connected"
  | "disconnected"
  | "reconnecting";

class SocketClient {
  private socket: Socket | null = null;
  private baseUrl: string;
  private connectionListeners: ((status: ConnectionStatus) => void)[] = [];
  private currentStatus: ConnectionStatus = "disconnected";

  constructor(baseUrl: string = SOCKET_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    this.setConnectionStatus("connecting");

    this.socket = io(this.baseUrl, {
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 10000,
    });

    this.setupEventListeners();
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.setConnectionStatus("disconnected");
  }

  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on(SOCKET_EVENTS.CONNECT, () => {
      this.setConnectionStatus("connected");
    });

    this.socket.on(SOCKET_EVENTS.DISCONNECT, () => {
      this.setConnectionStatus("disconnected");
    });

    this.socket.on("reconnect", () => {
      this.setConnectionStatus("connected");
    });

    this.socket.on("reconnect_attempt", () => {
      this.setConnectionStatus("reconnecting");
    });

    this.socket.on("connect_error", (error) => {
      console.error("Socket connection error:", error);
      this.setConnectionStatus("disconnected");
    });

    // Listen for connection status messages
    this.socket.on(SOCKET_EVENTS.STATUS, (data: StatusResponse) => {
      console.log("Status:", data.msg);
    });

    // Listen for system status updates
    this.socket.on(SOCKET_EVENTS.SYSTEM_STATUS, (data: SystemStatus) => {
      console.log("System status update:", data);
    });
  }

  private setConnectionStatus(status: ConnectionStatus): void {
    this.currentStatus = status;
    this.connectionListeners.forEach((listener) => listener(status));
  }

  getConnectionStatus(): ConnectionStatus {
    return this.currentStatus;
  }

  onConnectionStatusChange(
    callback: (status: ConnectionStatus) => void,
  ): () => void {
    this.connectionListeners.push(callback);
    return () => {
      this.connectionListeners = this.connectionListeners.filter(
        (cb) => cb !== callback,
      );
    };
  }

  sendMessage(message: string): void {
    if (!this.socket || !this.socket.connected) {
      throw new Error("Socket not connected");
    }

    const payload: ChatRequest = { message };
    this.socket.emit(SOCKET_EVENTS.SEND_MESSAGE, payload);
  }

  async getProfile(): Promise<ProfileResponse> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      const onProfileData = (response: ProfileResponse) => {
        this.socket?.off(SOCKET_EVENTS.PROFILE_DATA, onProfileData);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        resolve(response);
      };

      const onError = (error: ErrorResponse) => {
        this.socket?.off(SOCKET_EVENTS.PROFILE_DATA, onProfileData);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        reject(new Error(error.msg));
      };

      this.socket.on(SOCKET_EVENTS.PROFILE_DATA, onProfileData);
      this.socket.on(SOCKET_EVENTS.ERROR, onError);

      // Send request
      this.socket.emit(SOCKET_EVENTS.GET_PROFILE, {});
    });
  }

  async getHealth(): Promise<HealthResponse> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      this.socket.once(
        SOCKET_EVENTS.HEALTH_STATUS,
        (response: HealthResponse) => {
          resolve(response);
        },
      );

      // Send request
      this.socket.emit(SOCKET_EVENTS.REQUEST_HEALTH_CHECK, {});
    });
  }

  async uploadImage(image: string): Promise<ImageUploadResponse> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      const onImageResponse = (response: ImageUploadResponse) => {
        this.socket?.off(SOCKET_EVENTS.IMAGE_UPLOAD_RESPONSE, onImageResponse);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        resolve(response);
      };

      const onError = (error: ErrorResponse) => {
        this.socket?.off(SOCKET_EVENTS.IMAGE_UPLOAD_RESPONSE, onImageResponse);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        reject(new Error(error.msg));
      };

      this.socket.on(SOCKET_EVENTS.IMAGE_UPLOAD_RESPONSE, onImageResponse);
      this.socket.on(SOCKET_EVENTS.ERROR, onError);

      // Send request
      const payload: ImageUploadRequest = {
        image,
        timestamp: new Date().toISOString(),
      };
      this.socket.emit(SOCKET_EVENTS.UPLOAD_IMAGE, payload);
    });
  }

  async getThreatLogs(): Promise<ThreatLog[]> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      const onThreatLogs = (response: ThreatLog[]) => {
        this.socket?.off(SOCKET_EVENTS.THREAT_LOGS, onThreatLogs);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        resolve(response);
      };

      const onError = (error: ErrorResponse) => {
        this.socket?.off(SOCKET_EVENTS.THREAT_LOGS, onThreatLogs);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        reject(new Error(error.msg));
      };

      this.socket.on(SOCKET_EVENTS.THREAT_LOGS, onThreatLogs);
      this.socket.on(SOCKET_EVENTS.ERROR, onError);

      // Send request
      this.socket.emit(SOCKET_EVENTS.REQUEST_THREAT_LOGS, {});
    });
  }

  async getCameraList(): Promise<Camera[]> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      const onCameraList = (response: CameraListResponse) => {
        this.socket?.off(SOCKET_EVENTS.CAMERA_LIST, onCameraList);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        resolve(response.cameras);
      };

      const onError = (error: ErrorResponse) => {
        this.socket?.off(SOCKET_EVENTS.CAMERA_LIST, onCameraList);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        reject(new Error(error.msg));
      };

      this.socket.on(SOCKET_EVENTS.CAMERA_LIST, onCameraList);
      this.socket.on(SOCKET_EVENTS.ERROR, onError);

      // Send request
      this.socket.emit(SOCKET_EVENTS.GET_CAMERA_LIST, {});
    });
  }

  async registerCamera(cameraId: string): Promise<CameraRegistrationResponse> {
    return new Promise((resolve, reject) => {
      if (!this.socket || !this.socket.connected) {
        reject(new Error("Socket not connected"));
        return;
      }

      // Listen for response
      const onCameraRegistered = (response: CameraRegistrationResponse) => {
        this.socket?.off(SOCKET_EVENTS.CAMERA_REGISTERED, onCameraRegistered);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        resolve(response);
      };

      const onError = (error: ErrorResponse) => {
        this.socket?.off(SOCKET_EVENTS.CAMERA_REGISTERED, onCameraRegistered);
        this.socket?.off(SOCKET_EVENTS.ERROR, onError);
        reject(new Error(error.msg));
      };

      this.socket.on(SOCKET_EVENTS.CAMERA_REGISTERED, onCameraRegistered);
      this.socket.on(SOCKET_EVENTS.ERROR, onError);

      // Send request
      this.socket.emit(SOCKET_EVENTS.REGISTER_CAMERA, { camera_id: cameraId });
    });
  }

  // Real-time event listeners
  onChatResponse(callback: (response: ChatResponse) => void): () => void {
    if (!this.socket) return () => {};

    this.socket.on(SOCKET_EVENTS.CHAT_RESPONSE, callback);
    return () => {
      if (this.socket) {
        this.socket.off(SOCKET_EVENTS.CHAT_RESPONSE, callback);
      }
    };
  }

  onSystemStatus(callback: (status: SystemStatus) => void): () => void {
    if (!this.socket) return () => {};

    this.socket.on(SOCKET_EVENTS.SYSTEM_STATUS, callback);
    return () => {
      if (this.socket) {
        this.socket.off(SOCKET_EVENTS.SYSTEM_STATUS, callback);
      }
    };
  }

  onNotification(callback: (notification: Notification) => void): () => void {
    if (!this.socket) return () => {};

    this.socket.on(SOCKET_EVENTS.NOTIFICATION, callback);
    return () => {
      if (this.socket) {
        this.socket.off(SOCKET_EVENTS.NOTIFICATION, callback);
      }
    };
  }

  // General error listener
  onError(callback: (error: ErrorResponse) => void): () => void {
    if (!this.socket) return () => {};

    this.socket.on(SOCKET_EVENTS.ERROR, callback);
    return () => {
      if (this.socket) {
        this.socket.off(SOCKET_EVENTS.ERROR, callback);
      }
    };
  }

  // Check if socket is connected
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  // Get socket instance for advanced usage
  getSocket(): Socket | null {
    return this.socket;
  }
}

export const socketClient = new SocketClient();
export default SocketClient;
