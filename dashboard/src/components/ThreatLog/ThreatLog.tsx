import React from "react";
import styles from "./ThreatLog.module.css";
import type { ThreatLog } from "../../services/apiClient";

interface ThreatLogViewProps {
  logs: ThreatLog[];
  loading: boolean;
  error: string | null;
}

const ThreatLogView: React.FC<ThreatLogViewProps> = ({
  logs,
  loading,
  error,
}) => {
  return (
    <div className={styles.container}>
      <h2>Threat Logs</h2>
      {loading && <p>Loading...</p>}
      {error && <p className={styles.error}>{error}</p>}
      <div className={styles.logContainer}>
        {logs.map((log, index) => (
          <pre key={index} className={styles.logEntry}>
            {JSON.stringify(log, null, 2)}
          </pre>
        ))}
      </div>
    </div>
  );
};

export default ThreatLogView;
