import { useEffect, useMemo, useState } from "react";
import TemplateEditorModal from "../components/dashboard/TemplateEditorModal";
import {
  getEmailLogs,
  getEmailPreferences,
  getEmailTemplate,
  updateEmailPreferences,
  updateEmailTemplate,
  sendTestEmail,
} from "../services/alertsApi";

const defaultPreferences = {
  thresholdPercent: "85",
  recipients: "ops.team@assetguard.io, safety.audit@assetguard.io",
  alertsEnabled: true,
};

const defaultTemplate = {
  subject: "[ASSETGUARD] THRESHOLD BREACH DETECTED",
  body: "A monitored asset has exceeded the configured load threshold. Please review the latest evaluation report immediately.",
};

function AlertsPage() {
  const [thresholdPercent, setThresholdPercent] = useState(
    defaultPreferences.thresholdPercent
  );
  const [recipients, setRecipients] = useState(defaultPreferences.recipients);
  const [alertsEnabled, setAlertsEnabled] = useState(defaultPreferences.alertsEnabled);
  const [preferencesSnapshot, setPreferencesSnapshot] = useState(defaultPreferences);

  const [subject, setSubject] = useState(defaultTemplate.subject);
  const [body, setBody] = useState(defaultTemplate.body);
  const [templateSnapshot, setTemplateSnapshot] = useState(defaultTemplate);

  const [deliveryLogs, setDeliveryLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState("");

  const [preferencesError, setPreferencesError] = useState("");
  const [templateError, setTemplateError] = useState("");
  const [isSavingPreferences, setIsSavingPreferences] = useState(false);
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);
  const [isSendingTestEmail, setIsSendingTestEmail] = useState(false);

  const [statusFilter, setStatusFilter] = useState("All Communications");
  const [dateRange, setDateRange] = useState("Last 30 Days");
  const [searchTerm, setSearchTerm] = useState("");
  const [isTemplateEditorOpen, setIsTemplateEditorOpen] = useState(false);

  useEffect(() => {
    const loadAlertsData = async () => {
      setLogsLoading(true);
      setLogsError("");
      setPreferencesError("");
      setTemplateError("");

      const [preferencesResult, templateResult, logsResult] =
        await Promise.allSettled([
          getEmailPreferences(),
          getEmailTemplate(),
          getEmailLogs(),
        ]);

      if (preferencesResult.status === "fulfilled") {
        const preferences = preferencesResult.value || {};
        const nextPreferences = {
          thresholdPercent:
            preferences.thresholdPercent != null
              ? String(preferences.thresholdPercent)
              : defaultPreferences.thresholdPercent,
          recipients: Array.isArray(preferences.recipients)
            ? preferences.recipients.join(", ")
            : preferences.recipients || defaultPreferences.recipients,
          alertsEnabled:
            preferences.alertsEnabled != null
              ? Boolean(preferences.alertsEnabled)
              : defaultPreferences.alertsEnabled,
        };
        setThresholdPercent(nextPreferences.thresholdPercent);
        setRecipients(nextPreferences.recipients);
        setAlertsEnabled(nextPreferences.alertsEnabled);
        setPreferencesSnapshot(nextPreferences);
      } else {
        setPreferencesError("Unable to load email preferences.");
      }

      if (templateResult.status === "fulfilled") {
        const template = templateResult.value || {};
        const nextTemplate = {
          subject: template.subject || defaultTemplate.subject,
          body: template.body || defaultTemplate.body,
        };
        setSubject(nextTemplate.subject);
        setBody(nextTemplate.body);
        setTemplateSnapshot(nextTemplate);
      } else {
        setTemplateError("Unable to load email template.");
      }

      if (logsResult.status === "fulfilled") {
        setDeliveryLogs(Array.isArray(logsResult.value) ? logsResult.value : []);
      } else {
        setLogsError(logsResult.reason?.message || "Unable to load email logs.");
      }

      setLogsLoading(false);
    };

    loadAlertsData();
  }, []);

  const isPreferencesDirty =
    thresholdPercent !== preferencesSnapshot.thresholdPercent ||
    recipients !== preferencesSnapshot.recipients ||
    alertsEnabled !== preferencesSnapshot.alertsEnabled;

  const isTemplateDirty =
    subject !== templateSnapshot.subject || body !== templateSnapshot.body;

  const handleSavePreferences = async () => {
    if (isSavingPreferences || !isPreferencesDirty) return;
    setIsSavingPreferences(true);
    setPreferencesError("");
    try {
      await updateEmailPreferences({
        thresholdPercent: Number(thresholdPercent),
        recipients: recipients
          .split(",")
          .map((email) => email.trim())
          .filter(Boolean),
        alertsEnabled,
      });
      setPreferencesSnapshot({ thresholdPercent, recipients, alertsEnabled });
    } catch (error) {
      setPreferencesError(error.message || "Unable to save email preferences.");
    } finally {
      setIsSavingPreferences(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (isSavingTemplate || !isTemplateDirty) return;
    setIsSavingTemplate(true);
    setTemplateError("");
    try {
      await updateEmailTemplate({ subject, body });
      setTemplateSnapshot({ subject, body });
    } catch (error) {
      setTemplateError(error.message || "Unable to save email template.");
    } finally {
      setIsSavingTemplate(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (isSendingTestEmail) return;

    setIsSendingTestEmail(true);
    setTemplateError("");
    try {
      const testResult = await sendTestEmail();
      setDeliveryLogs((previous) => [testResult, ...previous]);
    } catch (error) {
      setTemplateError(error.message || "Unable to send test email.");
    } finally {
      setIsSendingTestEmail(false);
    }
  };

  const filteredLogs = useMemo(() => {
    return deliveryLogs.filter((log) => {
      const matchesStatus =
        statusFilter === "All Communications" || log.status === statusFilter;
      const matchesSearch =
        searchTerm.trim() === "" ||
        log.id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.recipient?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.channel?.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [deliveryLogs, statusFilter, searchTerm]);

  return (
    <>
      <header className="alerts-header">
        <h1 className="alerts-title">Alerts &amp; Communication Logs</h1>
        <p className="alerts-subtitle alerts-subtitle-readable">
          Track and manage system-generated email notifications, including load
          warnings and compliance reports.
        </p>
      </header>

      <section className="dashboard-section">
        <div className="alerts-filter-row alerts-filter-row-wide">
          <label className="alerts-field alerts-filter-search">
            <span className="alerts-label">SEARCH</span>
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search by Evaluation ID or Asset Name..."
            />
          </label>

          <label className="alerts-field">
            <span className="alerts-label">STATUS</span>
            <select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value)}
            >
              <option>All Communications</option>
              <option>Delivered</option>
              <option>Pending</option>
              <option>Failed</option>
            </select>
          </label>

          <label className="alerts-field">
            <span className="alerts-label">DATE RANGE</span>
            <select
              value={dateRange}
              onChange={(event) => setDateRange(event.target.value)}
            >
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
              <option>Last 90 Days</option>
            </select>
          </label>
        </div>

        <div className="alerts-page-actions">
          <button
            type="button"
            className="new-evaluation-btn"
            onClick={() => setIsTemplateEditorOpen(true)}
          >
            TEMPLATE EDITOR
          </button>
        </div>

        <div className="table-card">
          {logsError && <p className="dashboard-error-message alerts-inline-error">{logsError}</p>}
          {logsLoading ? (
            <p className="muted-note alerts-inline-loading">Loading delivery logs...</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>EVALUATION ID</th>
                  <th>ASSET NAME</th>
                  <th>RECIPIENT</th>
                  <th>MAX / PLANNED</th>
                  <th>OVER-CAP %</th>
                  <th>STATUS</th>
                  <th>TIME SENT</th>
                </tr>
              </thead>
              <tbody>
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="alerts-id-cell">{log.id}</td>
                    <td>{log.channel || "-"}</td>
                    <td>{log.recipient || "-"}</td>
                    <td>{log.maxPlanned || "-"}</td>
                    <td>{log.overCap || "-"}</td>
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
                    <td>{log.sentAt || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {(preferencesError || templateError) && (
        <p className="dashboard-error-message">{preferencesError || templateError}</p>
      )}

      <TemplateEditorModal
        open={isTemplateEditorOpen}
        onClose={() => setIsTemplateEditorOpen(false)}
        thresholdPercent={thresholdPercent}
        recipients={recipients}
        alertsEnabled={alertsEnabled}
        onThresholdChange={setThresholdPercent}
        onRecipientsChange={setRecipients}
        onToggleAlerts={() => setAlertsEnabled((previous) => !previous)}
        onSavePreferences={handleSavePreferences}
        isSavingPreferences={isSavingPreferences}
        disableSavePreferences={!isPreferencesDirty}
        subject={subject}
        body={body}
        onSubjectChange={setSubject}
        onBodyChange={setBody}
        onSaveTemplate={handleSaveTemplate}
        onSendTestEmail={handleSendTestEmail}
        isSavingTemplate={isSavingTemplate}
        disableSaveTemplate={!isTemplateDirty}
        isSendingTestEmail={isSendingTestEmail}
      />
    </>
  );
}

export default AlertsPage;
