import React from "react";

export default function EmailLogsTable({ logs, loading }) {
  return (
    <section className="card">
      <h2>Alerts & Communication Logs</h2>
      <p className="sub">Track every email notification event for audit traceability.</p>

      {loading ? <p>Loading email logs...</p> : null}

      {!loading && logs.length === 0 ? <p>No logs available.</p> : null}

      {!loading && logs.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Time (UTC)</th>
              <th>Asset</th>
              <th>Status</th>
              <th>Recipient</th>
              <th>Delivery</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{log.sentAt}</td>
                <td>{log.assetName}</td>
                <td>{log.evaluationStatus}</td>
                <td>{log.recipient}</td>
                <td>{log.deliveryStatus}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
