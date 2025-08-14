import { useState, useCallback, useEffect, useRef } from "react";
import { socketClient, type ConnectionStatus } from "../services/socketClient";
import type {
  ProfileResponse,
  HealthResponse,
  Message,
  ImageUploadResponse,
  ThreatLog,
  SystemStatus,
  Notification,
  Camera,
} from "../services/socketClient";

interface UseSocketState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseSocketReturn {
  // Connection status
  connectionStatus: ConnectionStatus;

  // Chat
  messages: UseSocketState<Message[]>;
  sendMessage: (message: string) => void;

  // Profile
  profile: UseSocketState<ProfileResponse>;
  fetchProfile: () => Promise<void>;

  // Health
  health: UseSocketState<HealthResponse>;
  fetchHealth: () => Promise<void>;

  // Image upload
  imageUpload: UseSocketState<ImageUploadResponse>;
  uploadImage: (image: string) => Promise<void>;

  // Threat logs
  threatLogs: UseSocketState<ThreatLog[]>;
  fetchThreatLogs: () => Promise<void>;

  // Camera functionality
  cameras: UseSocketState<Camera[]>;
  selectedCamera: Camera | null;
  fetchCameraList: () => Promise<void>;
  registerCamera: (cameraId: string) => Promise<void>;

  // Real-time data
  systemStatus: SystemStatus | null;
  notifications: Notification[];

  // Global loading state
  isLoading: boolean;

  // Connection management
  connect: () => void;
  disconnect: () => void;
}

export const useSocket = (): UseSocketReturn => {
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Cleanup functions for real-time listeners
  const cleanupFunctions = useRef<(() => void)[]>([]);

  const [messages, setMessages] = useState<UseSocketState<Message[]>>({
    data: [],
    loading: false,
    error: null,
  });

  const [profile, setProfile] = useState<UseSocketState<ProfileResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [health, setHealth] = useState<UseSocketState<HealthResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [imageUpload, setImageUpload] = useState<
    UseSocketState<ImageUploadResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });

  const [threatLogs, setThreatLogs] = useState<UseSocketState<ThreatLog[]>>({
    data: [],
    loading: false,
    error: null,
  });

  const [cameras, setCameras] = useState<UseSocketState<Camera[]>>({
    data: [],
    loading: false,
    error: null,
  });

  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null);

  const isLoading =
    profile.loading ||
    health.loading ||
    imageUpload.loading ||
    threatLogs.loading ||
    cameras.loading;

  // Connection management
  const connect = useCallback(() => {
    socketClient.connect();
  }, []);

  const disconnect = useCallback(() => {
    socketClient.disconnect();
    // Clean up all listeners
    cleanupFunctions.current.forEach((cleanup) => cleanup());
    cleanupFunctions.current = [];
  }, []);

  // Setup connection status listener
  useEffect(() => {
    const cleanup = socketClient.onConnectionStatusChange(setConnectionStatus);
    cleanupFunctions.current.push(cleanup);

    // Set initial status
    setConnectionStatus(socketClient.getConnectionStatus());

    return () => {
      cleanup();
    };
  }, []);

  // Setup real-time listeners when connected
  useEffect(() => {
    if (connectionStatus === "connected") {
      // Chat response listener
      const chatCleanup = socketClient.onChatResponse((response) => {
        const agentMessage: Message = {
          id: `agent-${Date.now()}`,
          content: response.agent_response,
          timestamp: new Date().toISOString(),
          sender: "agent",
          session_complete: response.session_complete,
        };

        setMessages((prev) => ({
          data: prev.data ? [...prev.data, agentMessage] : [agentMessage],
          loading: false,
          error: null,
        }));
      });
      cleanupFunctions.current.push(chatCleanup);

      // System status listener
      const systemStatusCleanup = socketClient.onSystemStatus((status) => {
        setSystemStatus(status);
      });
      cleanupFunctions.current.push(systemStatusCleanup);

      // Notification listener
      const notificationCleanup = socketClient.onNotification(
        (notification) => {
          setNotifications((prev) => [notification, ...prev.slice(0, 49)]); // Keep last 50
        },
      );
      cleanupFunctions.current.push(notificationCleanup);

      // General error listener
      const errorCleanup = socketClient.onError((error) => {
        console.error("Socket error:", error.msg);
        // You can set global error state here if needed
      });
      cleanupFunctions.current.push(errorCleanup);
    }

    return () => {
      // Cleanup will be handled by the main cleanup effect
    };
  }, [connectionStatus]);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const fetchProfile = useCallback(async () => {
    if (connectionStatus !== "connected") return;

    setProfile((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.getProfile();
      setProfile({ data, loading: false, error: null });
    } catch (error) {
      setProfile((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch profile",
      }));
    }
  }, [connectionStatus]);

  const sendMessage = useCallback(
    (messageContent: string): void => {
      if (connectionStatus !== "connected") {
        setMessages((prev) => ({
          ...prev,
          error: "Socket not connected. Please wait for connection.",
        }));
        return;
      }

      // Add user message to the list immediately
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        content: messageContent,
        timestamp: new Date().toISOString(),
        sender: "user",
      };

      setMessages((prev) => ({
        data: prev.data ? [...prev.data, userMessage] : [userMessage],
        loading: false,
        error: null,
      }));

      try {
        // Send message (fire and forget - response will come via event listener)
        socketClient.sendMessage(messageContent);
      } catch (error) {
        setMessages((prev) => ({
          ...prev,
          error:
            error instanceof Error ? error.message : "Failed to send message",
        }));
      }
    },
    [connectionStatus],
  );

  const fetchHealth = useCallback(async () => {
    if (connectionStatus !== "connected") {
      setHealth((prev) => ({
        ...prev,
        error: "Socket not connected. Please wait for connection.",
      }));
      return;
    }

    setHealth((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.getHealth();
      setHealth({ data, loading: false, error: null });
    } catch (error) {
      setHealth((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch health",
      }));
    }
  }, [connectionStatus]);

  const uploadImage = useCallback(
    async (image: string): Promise<void> => {
      if (connectionStatus !== "connected") {
        setImageUpload((prev) => ({
          ...prev,
          error: "Socket not connected. Please wait for connection.",
        }));
        return;
      }

      setImageUpload((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const data = await socketClient.uploadImage(image);

        if (data.status === "error") {
          throw new Error(data.message);
        }

        setImageUpload({ data, loading: false, error: null });
      } catch (error) {
        setImageUpload((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to upload image",
        }));
      }
    },
    [connectionStatus],
  );

  const fetchThreatLogs = useCallback(async () => {
    if (connectionStatus !== "connected") {
      setThreatLogs((prev) => ({
        ...prev,
        error: "Socket not connected. Please wait for connection.",
      }));
      return;
    }

    setThreatLogs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.getThreatLogs();
      setThreatLogs({ data, loading: false, error: null });
    } catch (error) {
      setThreatLogs((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to fetch threat logs",
      }));
    }
  }, [connectionStatus]);

  const fetchCameraList = useCallback(async () => {
    if (connectionStatus !== "connected") {
      setCameras((prev) => ({
        ...prev,
        error: "Socket not connected. Please wait for connection.",
      }));
      return;
    }

    setCameras((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.getCameraList();
      setCameras({ data, loading: false, error: null });
    } catch (error) {
      setCameras((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error
            ? error.message
            : "Failed to fetch camera list",
      }));
    }
  }, [connectionStatus]);

  const registerCamera = useCallback(
    async (cameraId: string): Promise<void> => {
      if (connectionStatus !== "connected") {
        setCameras((prev) => ({
          ...prev,
          error: "Socket not connected. Please wait for connection.",
        }));
        return;
      }

      setCameras((prev) => ({ ...prev, loading: true, error: null }));
      try {
        await socketClient.registerCamera(cameraId);
        const camera = cameras.data?.find((c) => c.id === cameraId) || null;
        setSelectedCamera(camera);
        setCameras((prev) => ({ ...prev, loading: false, error: null }));
      } catch (error) {
        setCameras((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error
              ? error.message
              : "Failed to register camera",
        }));
      }
    },
    [connectionStatus, cameras.data],
  );

  // Auto-fetch health and cameras when connected
  useEffect(() => {
    if (connectionStatus === "connected") {
      fetchHealth();
      fetchCameraList();
    }
  }, [connectionStatus, fetchHealth, fetchCameraList]);

  // Clear notifications older than 5 minutes
  useEffect(() => {
    const interval = setInterval(
      () => {
        setNotifications((prev) =>
          prev.filter(() => {
            // Assuming notifications don't have timestamps, keep last 50
            return true;
          }),
        );
      },
      5 * 60 * 1000,
    ); // 5 minutes

    return () => clearInterval(interval);
  }, []);

  return {
    connectionStatus,
    messages,
    sendMessage,
    profile,
    fetchProfile,
    health,
    fetchHealth,
    imageUpload,
    uploadImage,
    threatLogs,
    fetchThreatLogs,
    cameras,
    selectedCamera,
    fetchCameraList,
    registerCamera,
    systemStatus,
    notifications,
    isLoading,
    connect,
    disconnect,
  };
};

export default useSocket;
