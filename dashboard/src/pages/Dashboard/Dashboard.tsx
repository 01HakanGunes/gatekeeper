import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import Button from "../../components/Button/Button";
import Input from "../../components/Input/Input";
import { UI_CONSTANTS } from "../../utils/constants";
import type { LogEntry, Message } from "../../services/apiClient";
import styles from "./Dashboard.module.css";

const Dashboard: React.FC = () => {
  const {
    logs,
    fetchLogs,
    clearLogs,
    messages,
    fetchMessages,
    sendMessage,
    status,
    fetchStatus,
  } = useApi();

  const [messageInput, setMessageInput] = useState("");

  // Auto-refresh data
  useEffect(() => {
    const interval = setInterval(() => {
      fetchLogs();
      fetchMessages();
      fetchStatus();
    }, UI_CONSTANTS.REFRESH_INTERVAL);

    // Initial fetch
    fetchLogs();
    fetchMessages();

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchLogs, fetchMessages, fetchStatus]);

  const handleSendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!messageInput.trim()) {
        return;
      }

      if (messageInput.length > UI_CONSTANTS.MESSAGE_MAX_LENGTH) {
        return;
      }

      const messageContent = messageInput.trim();
      setMessageInput("");

      const result = await sendMessage({
        content: messageContent,
        metadata: {
          timestamp: new Date().toISOString(),
          source: "dashboard",
        },
      });

      if (result) {
        // Message sent successfully, fetchMessages will be called by interval
        // or we could manually refresh messages here
        fetchMessages();
      }
    },
    [messageInput, sendMessage, fetchMessages],
  );

  const handleClearLogs = useCallback(async () => {
    await clearLogs();
    fetchLogs();
  }, [clearLogs, fetchLogs]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatUptime = (uptime: number) => {
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const renderLogEntry = (log: LogEntry) => (
    <div key={log.id} className={styles.logEntry}>
      <div
        className={`${styles.logLevel} ${styles[`logLevel${log.level.charAt(0).toUpperCase() + log.level.slice(1)}`]}`}
      >
        {log.level}
      </div>
      <div className={styles.logContent}>
        <div className={styles.logMessage}>{log.message}</div>
        <div className={styles.logTimestamp}>
          {formatTimestamp(log.timestamp)}
          {log.source && (
            <span className={styles.logSource}> • {log.source}</span>
          )}
        </div>
      </div>
    </div>
  );

  const renderMessageEntry = (message: Message) => (
    <div
      key={message.id}
      className={`${styles.messageEntry} ${
        message.sender === "user" ? styles.messageUser : styles.messageAgent
      }`}
    >
      <div
        className={`${styles.messageBubble} ${
          message.sender === "user"
            ? styles.messageBubbleUser
            : styles.messageBubbleAgent
        }`}
      >
        {message.content}
      </div>
      <div className={styles.messageInfo}>
        <span>{message.sender === "user" ? "You" : "AI Agent"}</span>
        <span>•</span>
        <span>{formatTimestamp(message.timestamp)}</span>
        {message.status && (
          <>
            <span>•</span>
            <span>{message.status}</span>
          </>
        )}
      </div>
    </div>
  );

  const renderLoadingState = () => (
    <div className={styles.loadingState}>
      <div className={styles.loadingSpinner} />
      <div>Loading...</div>
    </div>
  );

  const renderErrorState = (error: string, onRetry?: () => void) => (
    <div className={styles.errorState}>
      <div className={styles.errorIcon}>⚠️</div>
      <div className={styles.errorText}>Error</div>
      <div className={styles.errorSubtext}>{error}</div>
      {onRetry && (
        <Button variant="secondary" size="small" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );

  const renderEmptyState = (
    icon: string,
    title: string,
    subtitle: string,
    action?: React.ReactNode,
  ) => (
    <div className={styles.emptyState}>
      <div className={styles.emptyStateIcon}>{icon}</div>
      <div className={styles.emptyStateText}>{title}</div>
      <div className={styles.emptyStateSubtext}>{subtitle}</div>
      {action}
    </div>
  );

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>AI Agent Dashboard</h1>
        <div className={styles.statusContainer}>
          {status.data && (
            <div
              className={`${styles.statusIndicator} ${
                status.data.online ? styles.statusOnline : styles.statusOffline
              }`}
            >
              <div
                className={`${styles.statusDot} ${
                  status.data.online
                    ? styles.statusDotOnline
                    : styles.statusDotOffline
                }`}
              />
              {status.data.online ? "Online" : "Offline"}
              {status.data.online && (
                <span>• {formatUptime(status.data.uptime)}</span>
              )}
            </div>
          )}
          <Button
            variant="ghost"
            size="small"
            onClick={() => fetchStatus()}
            loading={status.loading}
          >
            🔄
          </Button>
          <Link to="/settings">
            <Button variant="ghost" size="small">
              ⚙️
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Sidebar - Logs */}
        <aside className={styles.sidebar}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>System Logs</h2>
              <div className={styles.sectionActions}>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={() => fetchLogs()}
                  loading={logs.loading}
                >
                  🔄
                </Button>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={handleClearLogs}
                  disabled={!logs.data?.length}
                >
                  🗑️
                </Button>
              </div>
            </div>
            <div className={styles.logsContainer}>
              {logs.loading && !logs.data && renderLoadingState()}
              {logs.error &&
                !logs.data &&
                renderErrorState(logs.error, () => fetchLogs())}
              {logs.data &&
                logs.data.length === 0 &&
                renderEmptyState(
                  "📝",
                  "No logs yet",
                  "System logs will appear here",
                  <Button
                    variant="secondary"
                    size="small"
                    onClick={() => fetchLogs()}
                  >
                    Refresh Logs
                  </Button>,
                )}
              {logs.data && logs.data.length > 0 && (
                <div className={styles.logsList}>
                  {logs.data.map(renderLogEntry)}
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content - Messages */}
        <div className={styles.content}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>AI Agent Chat</h2>
              <div className={styles.sectionActions}>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={() => fetchMessages()}
                  loading={messages.loading}
                >
                  🔄
                </Button>
              </div>
            </div>
            <div className={styles.messagesContainer}>
              {messages.loading && !messages.data && renderLoadingState()}
              {messages.error &&
                !messages.data &&
                renderErrorState(messages.error, () => fetchMessages())}
              {messages.data &&
                messages.data.length === 0 &&
                renderEmptyState(
                  "💬",
                  "No messages yet",
                  "Start a conversation with your AI agent",
                )}
              {messages.data && messages.data.length > 0 && (
                <div className={styles.messagesList}>
                  {messages.data.map(renderMessageEntry)}
                </div>
              )}
            </div>

            {/* Message Input */}
            <div className={styles.messageInput}>
              <form
                onSubmit={handleSendMessage}
                className={styles.messageInputForm}
              >
                <div className={styles.messageInputField}>
                  <Input.Textarea
                    placeholder="Type your message to the AI agent..."
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    maxLength={UI_CONSTANTS.MESSAGE_MAX_LENGTH}
                    showCharacterCount
                    rows={3}
                    disabled={!status.data?.online}
                    variant={messages.error ? "error" : "default"}
                    helperText={
                      !status.data?.online
                        ? "Agent is offline"
                        : messages.error
                          ? "Failed to send message. Please try again."
                          : undefined
                    }
                  />
                </div>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={
                    !messageInput.trim() ||
                    !status.data?.online ||
                    messageInput.length > UI_CONSTANTS.MESSAGE_MAX_LENGTH
                  }
                  loading={messages.loading}
                >
                  Send
                </Button>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
