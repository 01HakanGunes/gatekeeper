import { useEffect, useState, useCallback, useRef } from "react";
import type { ReactNode, SyntheticEvent } from "react";

import { useSocket } from "../../hooks/useSocket";
import Button from "../../components/Button/Button";
import Input from "../../components/Input/Input";
import Camera, { type CameraRef } from "../../components/Camera/Camera";
import { UI_CONSTANTS } from "../../utils/constants";
import type { Message, VisitorProfile } from "../../services/socketClient";
import ThreatLogView from "../../components/ThreatLog/ThreatLog";
import styles from "./Dashboard.module.css";

function Dashboard() {
  const {
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
  } = useSocket();

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
      fetchProfile();
    }, UI_CONSTANTS.REFRESH_INTERVAL);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchHealth, fetchProfile]);

  // Auto-refresh threat logs
  useEffect(() => {
    const interval = setInterval(() => {
      fetchThreatLogs();
    }, 2000);

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fetchThreatLogs]);

  // Auto-upload image every 2 seconds
  useEffect(() => {
    if (!cameraEnabled) {
      return;
    }

    const imageUploadInterval = setInterval(async () => {
      if (cameraRef.current) {
        const capturedImage = await cameraRef.current.captureFrame();
        if (capturedImage) {
          await uploadImage(capturedImage);
        }
      }
    }, 500);

    return () => {
      clearInterval(imageUploadInterval);
    };
  }, [cameraEnabled, uploadImage]);

  const handleSendMessage = useCallback(
    async (e: SyntheticEvent) => {
      e.preventDefault();

      if (!messageInput.trim()) return;

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
      sendMessage(messageContent);

      // If we have separate endpoint enabled and an image, upload it separately
      if (uploadToSeparateEndpoint && capturedImage) {
        await uploadImage(capturedImage);
      }

      // Clear the captured image after sending
      setTimeout(() => setLastCapturedImage(null), 1000);
    },
    [
      messageInput,
      sendMessage,
      cameraEnabled,
      uploadToSeparateEndpoint,
      uploadImage,
    ],
  );

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

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage(e);
      }
    },
    [handleSendMessage],
  );

  const handleCameraSelect = useCallback(
    async (cameraId: string) => {
      try {
        await registerCamera(cameraId);
      } catch (error) {
        console.error("Failed to register camera:", error);
      }
    },
    [registerCamera],
  );

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
    action?: ReactNode,
  ) => (
    <div className={styles.emptyState}>
      <div className={styles.emptyStateIcon}>{icon}</div>
      <div className={styles.emptyStateText}>{title}</div>
      <div className={styles.emptyStateSubtext}>{subtitle}</div>
      {action}
    </div>
  );

  const renderCameraSelection = () => (
    <div className={styles.cameraSelectionContainer}>
      <h3 className={styles.sectionTitle}>Camera Selection</h3>
      {cameras.loading && (
        <div className={styles.loadingState}>Loading cameras...</div>
      )}
      {cameras.error &&
        renderErrorState(cameras.error, () => fetchCameraList())}
      {cameras.data && cameras.data.length > 0 && (
        <div className={styles.cameraSelection}>
          <select
            className={styles.cameraDropdown}
            onChange={(e) => handleCameraSelect(e.target.value)}
            disabled={cameras.loading}
            value={selectedCamera?.id || ""}
          >
            <option value="">Select a camera...</option>
            {cameras.data.map((camera) => (
              <option
                key={camera.id}
                value={camera.id}
                disabled={camera.status === "offline"}
              >
                {camera.id} - {camera.location} ({camera.status})
              </option>
            ))}
          </select>
          {selectedCamera && (
            <div className={styles.selectedCamera}>
              <div className={styles.selectedCameraInfo}>
                <span className={styles.selectedCameraLabel}>Active:</span>
                <span className={styles.selectedCameraValue}>
                  {selectedCamera.id} - {selectedCamera.location}
                </span>
              </div>
              <div
                className={`${styles.cameraStatus} ${
                  selectedCamera.status === "online"
                    ? styles.statusOnline
                    : styles.statusOffline
                }`}
              >
                {selectedCamera.status}
              </div>
            </div>
          )}
        </div>
      )}
      {cameras.data &&
        cameras.data.length === 0 &&
        connectionStatus === "connected" &&
        renderEmptyState("📹", "No Cameras", "No cameras are configured")}
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
          {/* Connection Status */}
          <div
            className={`${styles.statusIndicator} ${
              connectionStatus === "connected"
                ? styles.statusOnline
                : styles.statusOffline
            }`}
          >
            <div
              className={`${styles.statusDot} ${
                connectionStatus === "connected"
                  ? styles.statusDotOnline
                  : styles.statusDotOffline
              }`}
            />
            {connectionStatus === "connected" && "Socket Connected"}
            {connectionStatus === "connecting" && "Connecting..."}
            {connectionStatus === "reconnecting" && "Reconnecting..."}
            {connectionStatus === "disconnected" && "Disconnected"}
          </div>

          {/* System Health */}
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
        </div>
      </header>

      {/* Camera Selection */}
      <div className={styles.cameraSection}>{renderCameraSelection()}</div>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Sidebar - Profile */}
        <aside className={styles.sidebar}>
          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Visitor Profile</h2>
            </div>
            <div className={styles.profileContent}>
              {!profile.data &&
                connectionStatus === "connected" &&
                renderEmptyState(
                  "👤",
                  "No Profile Data",
                  "Waiting for visitor information...",
                )}

              {connectionStatus !== "connected" &&
                renderEmptyState(
                  "🔌",
                  "Not Connected",
                  "Connecting to security system...",
                )}

              {profile.data && (
                <div className={styles.profileData}>
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
                        {profile.data.decision_confidence !== null
                          ? (profile.data.decision_confidence * 100).toFixed(1)
                          : "N/A"}
                        %
                      </div>
                    </div>
                  )}

                  {renderVisitorProfile(profile.data.visitor_profile)}
                </div>
              )}

              {profile.error &&
                renderErrorState(profile.error, () => fetchProfile())}
            </div>
            {/* Camera Section */}
            <div className={styles.cameraSection}>
              <Camera
                ref={cameraRef}
                enabled={cameraEnabled}
                onToggle={handleCameraToggle}
                onCapture={handleCameraCapture}
              />

              {cameraEnabled && (
                <div className={styles.separateUploadToggle}>
                  <div className={styles.separateUploadLabel}>
                    <div className={styles.separateUploadTitle}>
                      Separate Upload
                    </div>
                    <div className={styles.separateUploadDescription}>
                      Also send images to separate endpoint
                    </div>
                  </div>
                  <div
                    className={`${styles.separateUploadSwitch} ${
                      uploadToSeparateEndpoint ? styles.active : ""
                    }`}
                    onClick={() =>
                      handleSeparateEndpointToggle(!uploadToSeparateEndpoint)
                    }
                    role="switch"
                    aria-checked={uploadToSeparateEndpoint}
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleSeparateEndpointToggle(!uploadToSeparateEndpoint);
                      }
                    }}
                  >
                    <div className={styles.separateUploadKnob} />
                  </div>
                </div>
              )}

              {lastCapturedImage && (
                <div className={styles.imageStatus}>
                  <div className={styles.imageStatusText}>
                    <span className={styles.imageStatusIcon}>📸</span> Last
                    captured frame (new frame will be taken on send)
                  </div>
                </div>
              )}

              {imageUpload.error && (
                <div className={styles.uploadError}>
                  Upload error: {imageUpload.error}
                </div>
              )}
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
                  disabled={connectionStatus !== "connected"}
                >
                  Refresh Profile
                </Button>
              </div>
            </div>
            <div className={styles.messagesContainer}>
              {connectionStatus !== "connected" &&
                renderEmptyState(
                  "🔌",
                  "Not Connected",
                  "Connecting to security agent...",
                )}

              {connectionStatus === "connected" &&
                messages.data &&
                messages.data.length === 0 &&
                renderEmptyState(
                  "👋",
                  "Ready to Chat",
                  "Start the conversation by sending a message",
                )}

              {messages.data && messages.data.length > 0 && (
                <div className={styles.messagesList}>
                  {messages.data.map(renderMessageEntry)}
                </div>
              )}

              {messages.error && renderErrorState(messages.error)}
            </div>

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
                    onKeyDown={handleKeyDown}
                    maxLength={UI_CONSTANTS.MESSAGE_MAX_LENGTH}
                    showCharacterCount
                    rows={3}
                    disabled={connectionStatus !== "connected"}
                    variant={messages.error ? "error" : "default"}
                    fullWidth={true}
                    helperText={
                      connectionStatus !== "connected"
                        ? "Connect to begin chatting"
                        : messages.error
                          ? "Failed to send message. Please try again."
                          : undefined
                    }
                  />
                  <Button
                    type="submit"
                    variant="primary"
                    size="small"
                    disabled={
                      !messageInput.trim() ||
                      connectionStatus !== "connected" ||
                      messageInput.length > UI_CONSTANTS.MESSAGE_MAX_LENGTH
                    }
                    loading={false}
                  >
                    Send
                  </Button>
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Threat Logs */}
        <aside className={styles.threatLogContainer}>
          <ThreatLogView
            logs={threatLogs.data || []}
            loading={threatLogs.loading}
            error={threatLogs.error}
          />
        </aside>
      </main>
    </div>
  );
}

export default Dashboard;
