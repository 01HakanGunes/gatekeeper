import { useState, useCallback, useEffect } from "react";
import { apiClient } from "../services/apiClient";
import type {
  SessionResponse,
  ProfileResponse,
  HealthResponse,
  Message,
  ImageUploadResponse,
  ThreatLog,
} from "../services/apiClient";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn {
  // Session management
  session: UseApiState<SessionResponse>;
  startSession: () => Promise<string | null>;
  endSession: () => Promise<void>;

  // Chat
  messages: UseApiState<Message[]>;
  sendMessage: (message: string) => Promise<void>;

  // Profile
  profile: UseApiState<ProfileResponse>;
  fetchProfile: () => Promise<void>;

  // Health
  health: UseApiState<HealthResponse>;
  fetchHealth: () => Promise<void>;

  // Image upload
  imageUpload: UseApiState<ImageUploadResponse>;
  uploadImage: (image: string) => Promise<void>;

  // Threat logs
  threatLogs: UseApiState<ThreatLog[]>;
  fetchThreatLogs: () => Promise<void>;

  // Current session ID
  currentSessionId: string | null;

  // Global loading state
  isLoading: boolean;
}

export const useApi = (): UseApiReturn => {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

  const [session, setSession] = useState<UseApiState<SessionResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [messages, setMessages] = useState<UseApiState<Message[]>>({
    data: [],
    loading: false,
    error: null,
  });

  const [profile, setProfile] = useState<UseApiState<ProfileResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [health, setHealth] = useState<UseApiState<HealthResponse>>({
    data: null,
    loading: false,
    error: null,
  });

  const [imageUpload, setImageUpload] = useState<
    UseApiState<ImageUploadResponse>
  >({
    data: null,
    loading: false,
    error: null,
  });

  const [threatLogs, setThreatLogs] = useState<UseApiState<ThreatLog[]>>({
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

  const startSession = useCallback(async (): Promise<string | null> => {
    setSession((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.startSession();
      setSession({ data, loading: false, error: null });
      setCurrentSessionId(data.session_id);
      setMessages({ data: [], loading: false, error: null });
      setProfile({ data: null, loading: false, error: null });
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
  }, []);

  const endSession = useCallback(async () => {
    if (!currentSessionId) return;

    setSession((prev) => ({ ...prev, loading: true, error: null }));
    try {
      await apiClient.endSession(currentSessionId);
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
  }, [currentSessionId]);

  const fetchProfile = useCallback(async () => {
    if (!currentSessionId) return;

    setProfile((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getProfile(currentSessionId);
      setProfile({ data, loading: false, error: null });
    } catch (error) {
      setProfile((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch profile",
      }));
    }
  }, [currentSessionId]);

  const sendMessage = useCallback(
    async (messageContent: string): Promise<void> => {
      if (!currentSessionId) {
        setMessages((prev) => ({
          ...prev,
          error: "No active session. Please start a new session.",
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
        const response = await apiClient.sendMessage(
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

        // If session is complete, fetch the final profile
        if (response.session_complete) {
          fetchProfile();
        }
      } catch (error) {
        setMessages((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to send message",
        }));
      }
    },
    [currentSessionId, fetchProfile],
  );

  const fetchHealth = useCallback(async () => {
    setHealth((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getHealth();
      setHealth({ data, loading: false, error: null });
    } catch (error) {
      setHealth((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch health",
      }));
    }
  }, []);

  const uploadImage = useCallback(
    async (image: string): Promise<void> => {
      if (!currentSessionId) {
        setImageUpload((prev) => ({
          ...prev,
          error: "No active session. Please start a new session.",
        }));
        return;
      }

      setImageUpload((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const data = await apiClient.uploadImage(currentSessionId, image);
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
    [currentSessionId],
  );

  const fetchThreatLogs = useCallback(async () => {
    setThreatLogs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getThreatLogs();
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
  }, []);

  // Auto-fetch health on mount
  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return {
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
    currentSessionId,
    isLoading,
  };
};

export default useApi;
