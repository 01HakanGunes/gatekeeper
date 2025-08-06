import { Link } from "react-router-dom";
import { useState, useCallback, useEffect } from "react";
import { useApi } from "../../hooks/useApi";
import Button from "../../components/Button/Button";
import Input from "../../components/Input/Input";
import { API_BASE_URL, UI_CONSTANTS } from "../../utils/constants";
import styles from "./Settings.module.css";

interface SettingsData {
  apiEndpoint: string;
  refreshInterval: number;
  autoRefresh: boolean;
  showTimestamps: boolean;
  enableNotifications: boolean;
}

function Settings() {
  const { health, fetchHealth } = useApi();

  const [settings, setSettings] = useState<SettingsData>({
    apiEndpoint: API_BASE_URL,
    refreshInterval: UI_CONSTANTS.REFRESH_INTERVAL / 1000, // Convert to seconds
    autoRefresh: true,
    showTimestamps: true,
    enableNotifications: true,
  });

  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem("dashboardSettings");
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings((prevSettings) => ({ ...prevSettings, ...parsed }));
      } catch (error) {
        console.error("Failed to load settings:", error);
      }
    }
  }, []);

  // Fetch health status on mount
  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  const handleSettingChange = useCallback(
    (key: keyof SettingsData, value: unknown) => {
      setSettings((prev) => ({
        ...prev,
        [key]: value,
      }));
      setHasUnsavedChanges(true);
      setSaveMessage(null);
    },
    [],
  );

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    try {
      // Save to localStorage
      localStorage.setItem("dashboardSettings", JSON.stringify(settings));

      // Simulate API call delay
      await new Promise((resolve) => setTimeout(resolve, 1000));

      setHasUnsavedChanges(false);
      setSaveMessage({
        type: "success",
        text: "Settings saved successfully!",
      });
    } catch (error) {
      console.error(error);
      setSaveMessage({
        type: "error",
        text: "Failed to save settings. Please try again.",
      });
    } finally {
      setIsSaving(false);
    }
  }, [settings]);

  const handleReset = useCallback(() => {
    const defaultSettings: SettingsData = {
      apiEndpoint: API_BASE_URL,
      refreshInterval: UI_CONSTANTS.REFRESH_INTERVAL / 1000,
      autoRefresh: true,
      showTimestamps: true,
      enableNotifications: true,
    };
    setSettings(defaultSettings);
    setHasUnsavedChanges(true);
    setSaveMessage(null);
  }, []);

  const handleClearCache = useCallback(async () => {
    try {
      localStorage.removeItem("dashboardSettings");
      localStorage.removeItem("dashboardCache");
      setSaveMessage({
        type: "success",
        text: "Cache cleared successfully!",
      });
    } catch (error) {
      console.error(error);
      setSaveMessage({
        type: "error",
        text: "Failed to clear cache.",
      });
    }
  }, []);

  const renderToggle = (
    key: keyof SettingsData,
    title: string,
    description: string,
    value: boolean,
  ) => (
    <div className={styles.toggleGroup}>
      <div className={styles.toggleLabel}>
        <div className={styles.toggleTitle}>{title}</div>
        <div className={styles.toggleDescription}>{description}</div>
      </div>
      <div
        className={`${styles.toggle} ${value ? styles.active : ""}`}
        onClick={() => handleSettingChange(key, !value)}
        role="switch"
        aria-checked={value}
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            handleSettingChange(key, !value);
          }
        }}
      >
        <div className={styles.toggleKnob} />
      </div>
    </div>
  );

  return (
    <div className={styles.settings}>
      {/* Header */}
      <header className={styles.header}>
        <Link to="/dashboard" className={styles.backButton}>
          ← Back to Dashboard
        </Link>
        <h1 className={styles.headerTitle}>Settings</h1>
        <div />
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        <div className={styles.container}>
          {/* System Health */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>System Health</h2>
            <p className={styles.sectionDescription}>
              Current status and information about the security gate system.
            </p>

            {health.data && (
              <>
                <div
                  className={`${styles.connectionStatus} ${
                    health.data.status === "healthy"
                      ? styles.connectionOnline
                      : styles.connectionOffline
                  }`}
                >
                  <div
                    className={`${styles.connectionDot} ${
                      health.data.status === "healthy"
                        ? styles.connectionDotOnline
                        : styles.connectionDotOffline
                    }`}
                  />
                  {health.data.status === "healthy"
                    ? "System Healthy"
                    : "System Error"}
                </div>

                <div className={styles.statusGrid}>
                  <div className={styles.statusCard}>
                    <div className={styles.statusLabel}>Status</div>
                    <div className={styles.statusValue}>
                      {health.data.status}
                    </div>
                  </div>
                  <div className={styles.statusCard}>
                    <div className={styles.statusLabel}>Active Sessions</div>
                    <div className={styles.statusValue}>
                      {health.data.active_sessions}
                    </div>
                  </div>
                  <div className={styles.statusCard}>
                    <div className={styles.statusLabel}>Graph Initialized</div>
                    <div className={styles.statusValue}>
                      {health.data.graph_initialized ? "Yes" : "No"}
                    </div>
                  </div>
                </div>
              </>
            )}

            <Button
              variant="secondary"
              size="small"
              onClick={() => fetchHealth()}
              loading={health.loading}
            >
              Refresh Status
            </Button>
          </section>

          {/* API Configuration */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>API Configuration</h2>
            <p className={styles.sectionDescription}>
              Configure the connection to your security gate backend.
            </p>

            <div className={styles.formGroup}>
              <Input
                label="API Endpoint"
                placeholder="http://localhost:8001"
                value={settings.apiEndpoint}
                onChange={(e) =>
                  handleSettingChange("apiEndpoint", e.target.value)
                }
                helperText="The base URL for your security gate API"
              />
            </div>

            <div className={styles.formGroup}>
              <Input
                label="Refresh Interval (seconds)"
                type="number"
                min="1"
                max="300"
                value={settings.refreshInterval.toString()}
                onChange={(e) =>
                  handleSettingChange(
                    "refreshInterval",
                    parseInt(e.target.value),
                  )
                }
                helperText="How often to refresh data from the API"
              />
            </div>
          </section>

          {/* Display Settings */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>Display Settings</h2>
            <p className={styles.sectionDescription}>
              Customize how information is displayed in the dashboard.
            </p>

            {renderToggle(
              "autoRefresh",
              "Auto Refresh",
              "Automatically refresh data at the specified interval",
              settings.autoRefresh,
            )}

            {renderToggle(
              "showTimestamps",
              "Show Timestamps",
              "Display timestamps for log entries and messages",
              settings.showTimestamps,
            )}

            {renderToggle(
              "enableNotifications",
              "Notifications",
              "Show browser notifications for important events",
              settings.enableNotifications,
            )}
          </section>

          {/* Actions */}
          <div className={styles.formActions}>
            {saveMessage && (
              <div
                style={{
                  color: saveMessage.type === "success" ? "#059669" : "#dc2626",
                  fontSize: "0.875rem",
                  fontWeight: "500",
                }}
              >
                {saveMessage.text}
              </div>
            )}
            <Button
              variant="secondary"
              onClick={handleReset}
              disabled={isSaving}
            >
              Reset to Defaults
            </Button>
            <Button
              variant="primary"
              onClick={handleSave}
              loading={isSaving}
              disabled={!hasUnsavedChanges}
            >
              Save Settings
            </Button>
          </div>

          {/* Danger Zone */}
          <section className={`${styles.section} ${styles.dangerZone}`}>
            <h2 className={`${styles.sectionTitle} ${styles.dangerTitle}`}>
              Danger Zone
            </h2>
            <p
              className={`${styles.sectionDescription} ${styles.dangerDescription}`}
            >
              These actions cannot be undone. Please proceed with caution.
            </p>

            <div className={styles.formActions}>
              <Button variant="danger" onClick={handleClearCache} size="small">
                Clear All Cache
              </Button>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

export default Settings;
