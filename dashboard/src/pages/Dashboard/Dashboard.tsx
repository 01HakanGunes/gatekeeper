import React, { useEffect, useState, useCallback, useRef } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../../hooks/useApi";
import Button from "../../components/Button/Button";
import Input from "../../components/Input/Input";
import Camera, { type CameraRef } from "../../components/Camera/Camera";
import { UI_CONSTANTS } from "../../utils/constants";
import type { Message, VisitorProfile } from "../../services/apiClient";
import styles from "./Dashboard.module.css";

const Dashboard: React.FC = () => {
  const {
    session,
    startSession,
    endSession,
    messages,
    sendMessage,
    profile,
    fetchProfile,
    health,
    fetchHealth,
    currentSessionId,
    imageUpload,
    uploadImage,
  } = useApi();

  const cameraRef = useRef<CameraRef>(null);
  const [messageInput, setMessageInput] = useState("");
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [uploadToSeparateEndpoint, setUploadToSeparateEndpoint] =
    useState(false);
  const [lastCapturedImage, setLastCapturedImage] = useState<string | null>(
    null,
  );

  // Auto-refresh health
  useEffect(() => {
    const interval = setInterval(() => {
      fetchHealth();
      if (currentSessionId) {
        fetchProfile();
      }
    }, UI_CONSTANTS.REFRESH_INTERVAL);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchHealth, fetchProfile, currentSessionId]);

  const handleSendMessage = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!messageInput.trim() || !currentSessionId) return;

      const messageContent = messageInput.trim();
      setMessageInput("");

      // Auto-capture new frame if camera is enabled
      let capturedImage: string | undefined;
      if (cameraEnabled && cameraRef.current) {
        capturedImage = (await cameraRef.current.captureFrame()) || undefined;

        // Update preview image for UI feedback
        if (capturedImage) {
          setLastCapturedImage(capturedImage);
        }
      }

      // Send message with freshly captured image
      await sendMessage(messageContent, capturedImage);

      // If we have separate endpoint enabled and an image, upload it separately
      if (uploadToSeparateEndpoint && capturedImage) {
        await uploadImage(capturedImage);
      }

      // Clear the captured image after sending
      setTimeout(() => setLastCapturedImage(null), 1000);
    },
    [
      messageInput,
      currentSessionId,
      sendMessage,
      cameraEnabled,
      uploadToSeparateEndpoint,
      uploadImage,
    ],
  );

  const handleStartSession = useCallback(async () => {
    await startSession();
  }, [startSession]);

  const handleEndSession = useCallback(async () => {
    await endSession();
    // Reset camera state when session ends
    setCameraEnabled(false);
    setLastCapturedImage(null);
  }, [endSession]);

  const handleCameraToggle = useCallback((enabled: boolean) => {
    setCameraEnabled(enabled);
    if (!enabled) {
      setLastCapturedImage(null);
    }
  }, []);

  const handleCameraCapture = useCallback((imageData: string) => {
    setLastCapturedImage(imageData);
  }, []);

  const handleSeparateEndpointToggle = useCallback((enabled: boolean) => {
    setUploadToSeparateEndpoint(enabled);
  }, []);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

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
        <span>{message.sender === "user" ? "Visitor" : "Security Agent"}</span>
        <span>•</span>
        <span>{formatTimestamp(message.timestamp)}</span>
        {message.session_complete && (
          <>
            <span>•</span>
            <span style={{ color: "#10b981", fontWeight: "500" }}>
              Session Complete
            </span>
          </>
        )}
      </div>
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

  const renderVisitorProfile = (visitorProfile: VisitorProfile) => (
    <div className={styles.profileContainer}>
      <h3 className={styles.profileTitle}>Visitor Profile</h3>
      <div className={styles.profileGrid}>
        {visitorProfile.name && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>Name:</span>
            <span className={styles.profileValue}>{visitorProfile.name}</span>
          </div>
        )}
        {visitorProfile.purpose && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>Purpose:</span>
            <span className={styles.profileValue}>
              {visitorProfile.purpose}
            </span>
          </div>
        )}
        {visitorProfile.contact_person && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>Contact Person:</span>
            <span className={styles.profileValue}>
              {visitorProfile.contact_person}
            </span>
          </div>
        )}
        {visitorProfile.affiliation && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>Affiliation:</span>
            <span className={styles.profileValue}>
              {visitorProfile.affiliation}
            </span>
          </div>
        )}
        {visitorProfile.threat_level && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>Threat Level:</span>
            <span
              className={`${styles.profileValue} ${
                styles[
                  `threat${visitorProfile.threat_level.charAt(0).toUpperCase() + visitorProfile.threat_level.slice(1)}`
                ]
              }`}
            >
              {visitorProfile.threat_level.toUpperCase()}
            </span>
          </div>
        )}
        {visitorProfile.id_verified !== undefined && (
          <div className={styles.profileItem}>
            <span className={styles.profileLabel}>ID Verified:</span>
            <span
              className={`${styles.profileValue} ${
                visitorProfile.id_verified ? styles.verified : styles.unverified
              }`}
            >
              {visitorProfile.id_verified ? "Yes" : "No"}
            </span>
          </div>
        )}
      </div>
    </div>
  );

  const getDecisionStyle = (decision: string) => {
    switch (decision.toLowerCase()) {
      case "approved":
        return styles.decisionApproved;
      case "denied":
        return styles.decisionDenied;
      case "pending":
        return styles.decisionPending;
      default:
        return "";
    }
  };

  return (
    <div className={styles.dashboard}>
      {/* Header */}
      <header className={styles.header}>
        <h1 className={styles.headerTitle}>Security Gate Dashboard</h1>
        <div className={styles.statusContainer}>
          {health.data && (
            <div
              className={`${styles.statusIndicator} ${
                health.data.status === "healthy"
                  ? styles.statusOnline
                  : styles.statusOffline
              }`}
            >
              <div
                className={`${styles.statusDot} ${
                  health.data.status === "healthy"
                    ? styles.statusDotOnline
                    : styles.statusDotOffline
                }`}
              />
              {health.data.status === "healthy"
                ? "System Healthy"
                : "System Error"}
              {health.data.status === "healthy" && (
                <span>• {health.data.active_sessions} active sessions</span>
              )}
            </div>
          )}
          <Button
            variant="ghost"
            size="small"
            onClick={() => fetchHealth()}
            loading={health.loading}
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
        {/* Sidebar - Profile */}
        <aside className={styles.sidebar}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Session Info</h2>
              <div className={styles.sectionActions}>
                {currentSessionId ? (
                  <Button
                    variant="danger"
                    size="small"
                    onClick={handleEndSession}
                    loading={session.loading}
                  >
                    End Session
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="small"
                    onClick={handleStartSession}
                    loading={session.loading}
                  >
                    Start Session
                  </Button>
                )}
              </div>
            </div>
            <div className={styles.profileContent}>
              {!currentSessionId &&
                renderEmptyState(
                  "🔒",
                  "No Active Session",
                  "Start a new session to begin visitor screening",
                  <Button
                    variant="primary"
                    size="small"
                    onClick={handleStartSession}
                    loading={session.loading}
                  >
                    Start New Session
                  </Button>,
                )}

              {currentSessionId && !profile.data && (
                <div className={styles.sessionActive}>
                  <div className={styles.sessionId}>
                    Session ID: {currentSessionId}
                  </div>
                  <div className={styles.sessionStatus}>
                    Status: <span className={styles.statusActive}>Active</span>
                  </div>
                </div>
              )}

              {profile.data && (
                <div className={styles.profileData}>
                  <div className={styles.sessionId}>
                    Session ID: {currentSessionId}
                  </div>
                  <div className={styles.sessionStatus}>
                    Status:{" "}
                    <span
                      className={
                        profile.data.session_active
                          ? styles.statusActive
                          : styles.statusComplete
                      }
                    >
                      {profile.data.session_active ? "Active" : "Complete"}
                    </span>
                  </div>

                  {profile.data.decision && (
                    <div className={styles.decisionContainer}>
                      <div
                        className={`${styles.decision} ${getDecisionStyle(
                          profile.data.decision,
                        )}`}
                      >
                        Decision: {profile.data.decision.toUpperCase()}
                      </div>
                      <div className={styles.confidence}>
                        Confidence:{" "}
                        {(profile.data.decision_confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  )}

                  {renderVisitorProfile(profile.data.visitor_profile)}
                </div>
              )}

              {profile.error &&
                renderErrorState(profile.error, () => fetchProfile())}
            </div>
          </div>
        </aside>

        {/* Main Content - Chat */}
        <div className={styles.content}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Security Agent Chat</h2>
              <div className={styles.sectionActions}>
                <Button
                  variant="ghost"
                  size="small"
                  onClick={() => fetchProfile()}
                  loading={profile.loading}
                  disabled={!currentSessionId}
                >
                  🔄
                </Button>
              </div>
            </div>
            <div className={styles.messagesContainer}>
              {!currentSessionId &&
                renderEmptyState(
                  "💬",
                  "No Active Session",
                  "Start a session to begin chatting with the security agent",
                )}

              {currentSessionId &&
                messages.data &&
                messages.data.length === 0 &&
                renderEmptyState(
                  "👋",
                  "Session Started",
                  "Start the conversation by sending a message",
                )}

              {messages.data && messages.data.length > 0 && (
                <div className={styles.messagesList}>
                  {messages.data.map(renderMessageEntry)}
                </div>
              )}

              {messages.error && renderErrorState(messages.error)}
            </div>

            {/* Camera Section */}
            {currentSessionId && (
              <div
                style={{
                  padding: "1rem 1.5rem",
                  borderTop: "1px solid var(--border-color, #e5e7eb)",
                }}
              >
                <Camera
                  ref={cameraRef}
                  enabled={cameraEnabled}
                  onToggle={handleCameraToggle}
                  onCapture={handleCameraCapture}
                />

                {cameraEnabled && (
                  <div
                    style={{
                      marginTop: "1rem",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      gap: "1rem",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontSize: "0.75rem",
                          fontWeight: "500",
                          color: "var(--text-primary, #213547)",
                          marginBottom: "0.25rem",
                        }}
                      >
                        Separate Upload
                      </div>
                      <div
                        style={{
                          fontSize: "0.625rem",
                          color: "var(--text-secondary, #6b7280)",
                        }}
                      >
                        Also send images to separate endpoint
                      </div>
                    </div>
                    <div
                      style={{
                        position: "relative",
                        width: "2.5rem",
                        height: "1.25rem",
                        backgroundColor: uploadToSeparateEndpoint
                          ? "#646cff"
                          : "#d1d5db",
                        borderRadius: "0.625rem",
                        cursor: "pointer",
                        transition: "background-color 0.2s ease",
                      }}
                      onClick={() =>
                        handleSeparateEndpointToggle(!uploadToSeparateEndpoint)
                      }
                      role="switch"
                      aria-checked={uploadToSeparateEndpoint}
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          handleSeparateEndpointToggle(
                            !uploadToSeparateEndpoint,
                          );
                        }
                      }}
                    >
                      <div
                        style={{
                          position: "absolute",
                          top: "0.125rem",
                          left: "0.125rem",
                          width: "1rem",
                          height: "1rem",
                          backgroundColor: "white",
                          borderRadius: "50%",
                          transition: "transform 0.2s ease",
                          transform: uploadToSeparateEndpoint
                            ? "translateX(1.25rem)"
                            : "translateX(0)",
                          boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
                        }}
                      />
                    </div>
                  </div>
                )}

                {lastCapturedImage && (
                  <div style={{ marginTop: "0.5rem", textAlign: "center" }}>
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: "var(--text-secondary, #6b7280)",
                        marginBottom: "0.25rem",
                      }}
                    >
                      📸 Last captured frame (new frame will be taken on send)
                    </div>
                  </div>
                )}

                {imageUpload.error && (
                  <div
                    style={{
                      marginTop: "0.5rem",
                      fontSize: "0.75rem",
                      color: "#dc2626",
                    }}
                  >
                    Upload error: {imageUpload.error}
                  </div>
                )}
              </div>
            )}

            {/* Message Input */}
            <div className={styles.messageInput}>
              <form
                onSubmit={handleSendMessage}
                className={styles.messageInputForm}
              >
                <div className={styles.messageInputField}>
                  <Input.Textarea
                    placeholder="Type your message to the security agent..."
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    maxLength={UI_CONSTANTS.MESSAGE_MAX_LENGTH}
                    showCharacterCount
                    rows={3}
                    disabled={!currentSessionId}
                    variant={messages.error ? "error" : "default"}
                    helperText={
                      !currentSessionId
                        ? "Start a session to begin chatting"
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
                    !currentSessionId ||
                    messageInput.length > UI_CONSTANTS.MESSAGE_MAX_LENGTH
                  }
                  loading={messages.loading || imageUpload.loading}
                >
                  {cameraEnabled ? "Send with 📸" : "Send"}
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
