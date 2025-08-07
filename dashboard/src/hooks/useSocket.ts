import { useState, useCallback, useEffect, useRef } from "react";
import { socketClient, type ConnectionStatus } from "../services/socketClient";
import type {
  SessionResponse,
  ProfileResponse,
  HealthResponse,
  Message,
  ImageUploadResponse,
  ThreatLog,
  SystemStatus,
  Notification,
} from "../services/socketClient";

interface UseSocketState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseSocketReturn {
  // Connection status
  connectionStatus: ConnectionStatus;

  // Session management
  session: UseSocketState<SessionResponse>;
  startSession: () => Promise<string | null>;
  endSession: () => Promise<void>;

  // Chat
  messages: UseSocketState<Message[]>;
  sendMessage: (message: string) => Promise<void>;

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

  // Real-time data
  systemStatus: SystemStatus | null;
  notifications: Notification[];

  // Current session ID
  currentSessionId: string | null;

  // Global loading state
  isLoading: boolean;

  // Connection management
  connect: () => void;
  disconnect: () => void;
}

export const useSocket = (): UseSocketReturn => {
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Cleanup functions for real-time listeners
  const cleanupFunctions = useRef<(() => void)[]>([]);

  const [session, setSession] = useState<UseSocketState<SessionResponse>>({
    data: null,
    loading: false,
    error: null,
  });

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

  const isLoading =
    session.loading ||
    messages.loading ||
    profile.loading ||
    health.loading ||
    imageUpload.loading ||
    threatLogs.loading;

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

      // Session update listener
      const sessionUpdateCleanup = socketClient.onSessionUpdate((update) => {
        console.log("Session update received:", update);

        if (update.type === "session_complete" && update.profile) {
          // Update profile when session completes
          setProfile({
            data: update.profile as ProfileResponse,
            loading: false,
            error: null,
          });

          // Add final response to messages if provided
          if (update.final_response) {
            const finalMessage: Message = {
              id: `final-${Date.now()}`,
              content: update.final_response,
              timestamp: new Date().toISOString(),
              sender: "agent",
              session_complete: true,
            };

            setMessages((prev) => ({
              data: prev.data ? [finalMessage, ...prev.data] : [finalMessage],
              loading: false,
              error: null,
            }));
          }
        } else if (update.type === "session_ended") {
          // Clear session data
          setCurrentSessionId(null);
          setSession({ data: null, loading: false, error: null });
          setMessages({ data: [], loading: false, error: null });
          setProfile({ data: null, loading: false, error: null });
        }
      });
      cleanupFunctions.current.push(sessionUpdateCleanup);

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

  const startSession = useCallback(async (): Promise<string | null> => {
    if (connectionStatus !== "connected") {
      setSession((prev) => ({
        ...prev,
        error: "Socket not connected. Please wait for connection.",
      }));
      return null;
    }

    setSession((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.startSession();

      if (data.status === "error") {
        throw new Error(data.message);
      }

      setSession({ data, loading: false, error: null });
      setCurrentSessionId(data.session_id);
      setMessages({ data: [], loading: false, error: null });
      setProfile({ data: null, loading: false, error: null });

      // Join session updates to receive real-time updates
      await socketClient.joinSessionUpdates(data.session_id);

      return data.session_id;
    } catch (error) {
      setSession((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to start session",
      }));
      return null;
    }
  }, [connectionStatus]);

  const endSession = useCallback(async () => {
    if (!currentSessionId || connectionStatus !== "connected") return;

    setSession((prev) => ({ ...prev, loading: true, error: null }));
    try {
      // Leave session updates first
      await socketClient.leaveSessionUpdates(currentSessionId);

      // Then end session
      const response = await socketClient.endSession(currentSessionId);

      if (response.status === "error") {
        throw new Error(response.message);
      }

      setSession({ data: null, loading: false, error: null });
      setCurrentSessionId(null);
      setMessages({ data: [], loading: false, error: null });
      setProfile({ data: null, loading: false, error: null });
    } catch (error) {
      setSession((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to end session",
      }));
    }
  }, [currentSessionId, connectionStatus]);

  const fetchProfile = useCallback(async () => {
    if (!currentSessionId || connectionStatus !== "connected") return;

    setProfile((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await socketClient.getProfile(currentSessionId);
      setProfile({ data, loading: false, error: null });
    } catch (error) {
      setProfile((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch profile",
      }));
    }
  }, [currentSessionId, connectionStatus]);

  const sendMessage = useCallback(
    async (messageContent: string): Promise<void> => {
      if (!currentSessionId) {
        setMessages((prev) => ({
          ...prev,
          error: "No active session. Please start a new session.",
        }));
        return;
      }

      if (connectionStatus !== "connected") {
        setMessages((prev) => ({
          ...prev,
          error: "Socket not connected. Please wait for connection.",
        }));
        return;
      }

      setMessages((prev) => ({ ...prev, loading: true, error: null }));

      // Add user message to the list
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        content: messageContent,
        timestamp: new Date().toISOString(),
        sender: "user",
      };

      setMessages((prev) => ({
        ...prev,
        data: prev.data ? [userMessage, ...prev.data] : [userMessage],
      }));

      try {
        const response = await socketClient.sendMessage(
          currentSessionId,
          messageContent,
        );

        // Add agent response to the list
        const agentMessage: Message = {
          id: `agent-${Date.now()}`,
          content: response.agent_response,
          timestamp: new Date().toISOString(),
          sender: "agent",
          session_complete: response.session_complete,
        };

        setMessages((prev) => ({
          data: prev.data ? [agentMessage, ...prev.data] : [agentMessage],
          loading: false,
          error: null,
        }));

        // If session is complete, profile will be updated via session_update event
      } catch (error) {
        setMessages((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to send message",
        }));
      }
    },
    [currentSessionId, connectionStatus],
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
      if (!currentSessionId) {
        setImageUpload((prev) => ({
          ...prev,
          error: "No active session. Please start a new session.",
        }));
        return;
      }

      if (connectionStatus !== "connected") {
        setImageUpload((prev) => ({
          ...prev,
          error: "Socket not connected. Please wait for connection.",
        }));
        return;
      }

      setImageUpload((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const data = await socketClient.uploadImage(currentSessionId, image);

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
    [currentSessionId, connectionStatus],
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

  // Auto-fetch health when connected
  useEffect(() => {
    if (connectionStatus === "connected") {
      fetchHealth();
    }
  }, [connectionStatus, fetchHealth]);

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
    session,
    startSession,
    endSession,
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
    systemStatus,
    notifications,
    currentSessionId,
    isLoading,
    connect,
    disconnect,
  };
};

export default useSocket;
