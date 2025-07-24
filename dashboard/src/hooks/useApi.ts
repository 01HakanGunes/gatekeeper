import { useState, useCallback, useEffect } from "react";
import { apiClient } from "../services/apiClient";
import type {
  LogEntry,
  Message,
  AgentStatus,
  SendMessageRequest,
} from "../services/apiClient";

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn {
  // Logs
  logs: UseApiState<LogEntry[]>;
  fetchLogs: (limit?: number) => Promise<void>;
  clearLogs: () => Promise<void>;

  // Messages
  messages: UseApiState<Message[]>;
  fetchMessages: (limit?: number) => Promise<void>;
  sendMessage: (messageRequest: SendMessageRequest) => Promise<Message | null>;

  // Status
  status: UseApiState<AgentStatus>;
  fetchStatus: () => Promise<void>;

  // Global loading state
  isLoading: boolean;
}

export const useApi = (): UseApiReturn => {
  const [logs, setLogs] = useState<UseApiState<LogEntry[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [messages, setMessages] = useState<UseApiState<Message[]>>({
    data: null,
    loading: false,
    error: null,
  });

  const [status, setStatus] = useState<UseApiState<AgentStatus>>({
    data: null,
    loading: false,
    error: null,
  });

  const isLoading = logs.loading || messages.loading || status.loading;

  const fetchLogs = useCallback(async (limit?: number) => {
    setLogs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getLogs(limit);
      setLogs({ data, loading: false, error: null });
    } catch (error) {
      setLogs((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to fetch logs",
      }));
    }
  }, []);

  const clearLogs = useCallback(async () => {
    setLogs((prev) => ({ ...prev, loading: true, error: null }));
    try {
      await apiClient.clearLogs();
      setLogs({ data: [], loading: false, error: null });
    } catch (error) {
      setLogs((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : "Failed to clear logs",
      }));
    }
  }, []);

  const fetchMessages = useCallback(async (limit?: number) => {
    setMessages((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getMessages(limit);
      setMessages({ data, loading: false, error: null });
    } catch (error) {
      setMessages((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch messages",
      }));
    }
  }, []);

  const sendMessage = useCallback(
    async (messageRequest: SendMessageRequest): Promise<Message | null> => {
      setMessages((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const newMessage = await apiClient.sendMessage(messageRequest);

        // Add the new message to the existing messages
        setMessages((prev) => ({
          data: prev.data ? [newMessage, ...prev.data] : [newMessage],
          loading: false,
          error: null,
        }));

        return newMessage;
      } catch (error) {
        setMessages((prev) => ({
          ...prev,
          loading: false,
          error:
            error instanceof Error ? error.message : "Failed to send message",
        }));
        return null;
      }
    },
    [],
  );

  const fetchStatus = useCallback(async () => {
    setStatus((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const data = await apiClient.getStatus();
      setStatus({ data, loading: false, error: null });
    } catch (error) {
      setStatus((prev) => ({
        ...prev,
        loading: false,
        error:
          error instanceof Error ? error.message : "Failed to fetch status",
      }));
    }
  }, []);

  // Auto-fetch status on mount
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return {
    logs,
    fetchLogs,
    clearLogs,
    messages,
    fetchMessages,
    sendMessage,
    status,
    fetchStatus,
    isLoading,
  };
};

export default useApi;
