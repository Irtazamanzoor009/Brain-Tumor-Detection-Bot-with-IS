import React, { useEffect, useState } from 'react';
import './logs.css';

const LogsViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:5000/logs", {
         method: ['GET'],
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await response.json();
        if (data.success) {
          setLogs(data.logs);
        } else {
          setError(data.error || "Failed to fetch logs.");
          console.log("details: ", data.details)
        }
      } catch (err) {
        setError("An error occurred while fetching logs.");
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    window.location.href = "/signin";
};

  return (
    <div className="signup-container">
        <button className="logout-button" onClick={handleLogout}>
                Logout
            </button>
      <div className="signup logs-container">
        <h3>Security Logs</h3>
        {loading ? (
          <p>Loading logs...</p>
        ) : error ? (
          <p className="red msgs">{error}</p>
        ) : logs.length === 0 ? (
          <p>No logs found.</p>
        ) : (
          <div className="logs-table-wrapper">
            <table className="logs-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Email</th>
                  <th>IP Address</th>
                  <th>Event Type</th>
                  <th>User Agent</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log._id}>
                    <td>{new Date(log.timestamp).toLocaleString()}</td>
                    <td>{log.user_email || 'N/A'}</td>
                    <td>{log.ip || 'Unknown'}</td>
                    <td>{log.event_type || 'Unknown'}</td>
                    <td>{log.user_agent || 'Unknown'}</td>
                    <td>{log.details || 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsViewer;
