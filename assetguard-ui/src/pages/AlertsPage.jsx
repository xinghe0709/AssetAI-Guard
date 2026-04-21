import { useMemo, useState } from "react";
import SectionHeader from "../components/dashboard/SectionHeader";

const initialDeliveryLogs = [
  {
    id: "DL-10045",
    recipient: "ops.team@assetguard.io",
    status: "Delivered",
    channel: "Threshold Alert",
    sentAt: "2026-04-21 08:14",
  },
  {
    id: "DL-10044",
    recipient: "safety.audit@assetguard.io",
    status: "Failed",
    channel: "Compliance Alert",
    sentAt: "2026-04-21 06:42",
  },
  {
    id: "DL-10043",
    recipient: "field.lead@assetguard.io",
    status: "Pending",
    channel: "Daily Digest",
    sentAt: "2026-04-20 22:17",
  },
];

function AlertsPage() {
  const [thresholdPercent, setThresholdPercent] = useState("85");
  const [recipients, setRecipients] = useState(
    "ops.team@assetguard.io, safety.audit@assetguard.io"
  );
  const [alertsEnabled, setAlertsEnabled] = useState(true);

  const [subject, setSubject] = useState("[ASSETGUARD] THRESHOLD BREACH DETECTED");
  const [body, setBody] = useState(
    "A monitored asset has exceeded the configured load threshold. Please review the latest evaluation report immediately."
  );

  const [statusFilter, setStatusFilter] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");

  const handleSendTestEmail = () => {
    // Placeholder for future API integration.
    console.log("SEND TEST EMAIL", {
      thresholdPercent,
      recipients,
      alertsEnabled,
      subject,
      body,
    });
  };

  const filteredLogs = useMemo(() => {
    return initialDeliveryLogs.filter((log) => {
      const matchesStatus = statusFilter === "All" || log.status === statusFilter;
      const matchesSearch =
        searchTerm.trim() === "" ||
        log.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.recipient.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.channel.toLowerCase().includes(searchTerm.toLowerCase());

      return matchesStatus && matchesSearch;
    });
  }, [statusFilter, searchTerm]);

  return (
    <>
      <header className="alerts-header">
        <h1 className="alerts-title">ALERTS</h1>
        <p className="alerts-subtitle">
          CONFIGURE ALERT RULES, EDIT MESSAGE TEMPLATES, AND TRACK DELIVERY STATUS.
        </p>
      </header>

      <section className="dashboard-section">
        <SectionHeader title="Email Preferences" action="SAVE PREFERENCES" />
        <div className="alerts-card">
          <div className="alerts-field-grid">
            <label className="alerts-field">
              <span className="alerts-label">THRESHOLD (%)</span>
              <input
                type="number"
                min="1"
                max="100"
                value={thresholdPercent}
                onChange={(event) => setThresholdPercent(event.target.value)}
              />
            </label>

            <label className="alerts-field alerts-field-wide">
              <span className="alerts-label">RECIPIENTS</span>
              <input
                type="text"
                value={recipients}
                onChange={(event) => setRecipients(event.target.value)}
                placeholder="name@company.com, another@company.com"
              />
            </label>
          </div>

          <div className="alerts-toggle-row">
            <div>
              <p className="alerts-label">EMAIL ALERTS</p>
              <p className="alerts-help">
                ENABLE OR DISABLE AUTOMATIC NOTIFICATIONS FOR THRESHOLD EVENTS.
              </p>
            </div>
            <button
              type="button"
              className={`alerts-toggle ${alertsEnabled ? "active" : ""}`}
              onClick={() => setAlertsEnabled((previous) => !previous)}
            >
              {alertsEnabled ? "ON" : "OFF"}
            </button>
          </div>
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeader title="Template Editor" action="SAVE TEMPLATE" />
        <div className="alerts-card">
          <label className="alerts-field">
            <span className="alerts-label">SUBJECT</span>
            <input
              type="text"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
            />
          </label>

          <label className="alerts-field">
            <span className="alerts-label">BODY</span>
            <textarea
              rows="5"
              value={body}
              onChange={(event) => setBody(event.target.value)}
            />
          </label>

          <div className="alerts-actions">
            <button
              type="button"
              className="new-evaluation-btn"
              onClick={handleSendTestEmail}
            >
              SEND TEST EMAIL
            </button>
          </div>
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeader title="Delivery Logs" action="EXPORT LOGS" />
        <div className="alerts-card">
          <div className="alerts-filter-row">
            <label className="alerts-field">
              <span className="alerts-label">STATUS FILTER</span>
              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
              >
                <option>All</option>
                <option>Delivered</option>
                <option>Pending</option>
                <option>Failed</option>
              </select>
            </label>

            <label className="alerts-field alerts-field-wide">
              <span className="alerts-label">SEARCH</span>
              <input
                type="text"
                value={searchTerm}
                onChange={(event) => setSearchTerm(event.target.value)}
                placeholder="Search by log ID, recipient, or channel"
              />
            </label>
          </div>

          <div className="table-card">
            <table className="data-table">
              <thead>
                <tr>
                  <th>LOG ID</th>
                  <th>RECIPIENT</th>
                  <th>TYPE</th>
                  <th>STATUS</th>
                  <th>SENT AT</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td>{log.id}</td>
                    <td>{log.recipient}</td>
                    <td>{log.channel}</td>
                    <td>
                      <span
                        className={`result-badge ${
                          log.status === "Failed"
                            ? "danger"
                            : log.status === "Pending"
                            ? "pending"
                            : "ok"
                        }`}
                      >
                        <span className="result-dot"></span>
                        {log.status}
                      </span>
                    </td>
                    <td>{log.sentAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </>
  );
}

export default AlertsPage;
