import {
  useRef,
  useEffect,
  useState,
  useCallback,
  useImperativeHandle,
} from "react";
import type { Ref } from "react";
import { UI_CONSTANTS, ERROR_MESSAGES } from "../../utils/constants";
import styles from "./Camera.module.css";

export interface CameraProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  onCapture?: (imageData: string) => void;
  autoCapture?: boolean;
  ref?: Ref<CameraRef>;
}

export interface CameraRef {
  captureFrame: () => Promise<string | null>;
}

function Camera({
  enabled,
  onToggle,
  onCapture,
  autoCapture = false,
  ref,
}: CameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: UI_CONSTANTS.CAMERA_WIDTH,
          height: UI_CONSTANTS.CAMERA_HEIGHT,
          facingMode: "user",
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsStreaming(true);
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setError(ERROR_MESSAGES.CAMERA_ERROR);
      setIsStreaming(false);
      onToggle(false);
    }
  }, [onToggle]);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
    setError(null);
  }, []);

  const captureFrame = useCallback(async (): Promise<string | null> => {
    if (!videoRef.current || !canvasRef.current || !isStreaming) {
      return null;
    }

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const context = canvas.getContext("2d");

      if (!context) {
        throw new Error("Canvas context not available");
      }

      // Set canvas dimensions to match video
      canvas.width = video.videoWidth || UI_CONSTANTS.CAMERA_WIDTH;
      canvas.height = video.videoHeight || UI_CONSTANTS.CAMERA_HEIGHT;

      // Draw the video frame to canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to base64 JPEG
      const imageData = canvas.toDataURL(
        "image/jpeg",
        UI_CONSTANTS.IMAGE_QUALITY,
      );

      // Remove data URL prefix to get just the base64 data
      const base64Data = imageData.split(",")[1];

      return base64Data;
    } catch (err) {
      console.error("Image capture error:", err);
      setError(ERROR_MESSAGES.IMAGE_CAPTURE_ERROR);
      return null;
    }
  }, [isStreaming]);

  const handleCapture = useCallback(async () => {
    const imageData = await captureFrame();
    if (imageData && onCapture) {
      onCapture(imageData);
    }
  }, [captureFrame, onCapture]);

  // Expose captureFrame function via ref
  useImperativeHandle(
    ref,
    () => ({
      captureFrame,
    }),
    [captureFrame],
  );

  const handleToggle = useCallback(() => {
    const newEnabled = !enabled;
    onToggle(newEnabled);
  }, [enabled, onToggle]);

  // Effect to start/stop camera based on enabled state
  useEffect(() => {
    if (enabled) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [enabled, startCamera, stopCamera]);

  // Auto-capture effect
  useEffect(() => {
    if (autoCapture && isStreaming && onCapture) {
      handleCapture();
    }
  }, [autoCapture, isStreaming, handleCapture, onCapture]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return (
    <div className={styles.cameraContainer}>
      <div className={styles.cameraHeader}>
        <h3 className={styles.cameraTitle}>Camera</h3>
        <div className={styles.cameraControls}>
          <div
            className={`${styles.toggle} ${enabled ? styles.active : ""}`}
            onClick={handleToggle}
            role="switch"
            aria-checked={enabled}
            aria-label="Toggle camera"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                handleToggle();
              }
            }}
          >
            <div className={styles.toggleKnob} />
          </div>
        </div>
      </div>

      {error && (
        <div className={styles.errorMessage}>
          <span className={styles.errorIcon}>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      <div className={styles.videoContainer}>
        {enabled && !error ? (
          <>
            <video
              ref={videoRef}
              className={styles.video}
              autoPlay
              muted
              playsInline
            />
            <canvas
              ref={canvasRef}
              style={{ display: "none" }}
              aria-hidden="true"
            />

            {isStreaming && (
              <>
                <div className={styles.videoOverlay}>
                  <div
                    className={`${styles.statusIndicator} ${styles.statusLive}`}
                  >
                    <div className={styles.statusDot} />
                    LIVE
                  </div>
                </div>

                <button
                  className={styles.captureButton}
                  onClick={handleCapture}
                  aria-label="Capture photo"
                  title="Capture photo"
                >
                  📸
                </button>
              </>
            )}
          </>
        ) : (
          <div className={styles.videoPlaceholder}>📷</div>
        )}
      </div>

      {enabled && !error && (
        <div className={styles.cameraSettings}>
          <div className={styles.settingGroup}>
            <div className={styles.settingLabel}>
              <div className={styles.settingTitle}>Status</div>
              <div className={styles.settingDescription}>
                {isStreaming
                  ? "Camera is active and ready"
                  : "Starting camera..."}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

Camera.displayName = "Camera";

export default Camera;
