import { useEffect, useMemo, useState } from "react";
import SectionHeader from "../components/dashboard/SectionHeader";
import {
  getEmailLogs,
  getEmailPreferences,
  getEmailTemplate,
  updateEmailPreferences,
  updateEmailTemplate,
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
  const [preferencesLoading, setPreferencesLoading] = useState(true);
  const [preferencesError, setPreferencesError] = useState("");
  const [templateLoading, setTemplateLoading] = useState(true);
  const [templateError, setTemplateError] = useState("");
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState("");

  const [isSavingPreferences, setIsSavingPreferences] = useState(false);
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);

  const [statusFilter, setStatusFilter] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [isTemplateEditorOpen, setIsTemplateEditorOpen] = useState(false);

  useEffect(() => {
    const loadAlertsData = async () => {
      setPreferencesLoading(true);
      setTemplateLoading(true);
      setLogsLoading(true);
      setPreferencesError("");
      setTemplateError("");
      setLogsError("");

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
        setPreferencesError(
          preferencesResult.reason?.message ||
            "Unable to load email preferences."
        );
      }
      setPreferencesLoading(false);

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
        setTemplateError(
          templateResult.reason?.message || "Unable to load email template."
        );
      }
      setTemplateLoading(false);

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
    if (isSavingPreferences || !isPreferencesDirty) {
      return;
    }

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
    if (isSavingTemplate || !isTemplateDirty) {
      return;
    }

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

  useEffect(() => {
    const loadAlertsData = async () => {
      setPreferencesLoading(true);
      setTemplateLoading(true);
      setLogsLoading(true);
      setPreferencesError("");
      setTemplateError("");
      setLogsError("");

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
        setPreferencesError(
          preferencesResult.reason?.message ||
            "Unable to load email preferences."
        );
      }
      setPreferencesLoading(false);

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
        setTemplateError(
          templateResult.reason?.message || "Unable to load email template."
        );
      }
      setTemplateLoading(false);

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
    if (isSavingPreferences || !isPreferencesDirty) {
      return;
    }

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
    if (isSavingTemplate || !isTemplateDirty) {
      return;
    }

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

  const handleSendTestEmail = () => {
    console.log("SEND TEST EMAIL", {
      thresholdPercent,
      recipients,
      alertsEnabled,
      subject,
      body,
    });
  };

  const filteredLogs = useMemo(() => {
    return deliveryLogs.filter((log) => {
      const matchesStatus = statusFilter === "All" || log.status === statusFilter;
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
        <h1 className="alerts-title">ALERTS</h1>
        <p className="alerts-subtitle">
          CONFIGURE ALERT RULES, EDIT MESSAGE TEMPLATES, AND TRACK DELIVERY STATUS.
        </p>
      </header>

      <section className="dashboard-section">
        <SectionHeader
          title="Email Preferences"
          action={isSavingPreferences ? "SAVING..." : "SAVE PREFERENCES"}
          onAction={handleSavePreferences}
          actionDisabled={isSavingPreferences || !isPreferencesDirty}
        />
        <div className="alerts-card">
          {preferencesError && (
            <p className="dashboard-error-message">{preferencesError}</p>
          )}
          {preferencesLoading ? (
            <p className="muted-note">Loading preferences...</p>
          ) : (
            <>
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
            </>
          )}
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeader
          title="Template Editor"
          action={isTemplateEditorOpen ? "CLOSE" : "OPEN EDITOR"}
          onAction={() => setIsTemplateEditorOpen((previous) => !previous)}
        />
        <div className="alerts-card">
          {templateError && <p className="dashboard-error-message">{templateError}</p>}
          {templateLoading ? (
            <p className="muted-note">Loading template...</p>
          ) : isTemplateEditorOpen ? (
            <div className="template-editor-panel">
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
                  rows="6"
                  value={body}
                  onChange={(event) => setBody(event.target.value)}
                />
              </label>

              <div className="alerts-actions">
                <button
                  type="button"
                  className="section-action template-cancel-btn"
                  onClick={() => setIsTemplateEditorOpen(false)}
                >
                  CANCEL
                </button>
                <button
                  type="button"
                  className="new-evaluation-btn"
                  onClick={handleSaveTemplate}
                  disabled={isSavingTemplate || !isTemplateDirty}
                >
                  {isSavingTemplate ? "SAVING..." : "SAVE TEMPLATE"}
                </button>
                <button
                  type="button"
                  className="new-evaluation-btn"
                  onClick={handleSendTestEmail}
                >
                  SEND TEST EMAIL
                </button>
              </div>
            </div>
          ) : (
            <div className="template-preview-card">
              <p className="alerts-label">CURRENT TEMPLATE</p>
              <h3>{subject}</h3>
              <p>{body}</p>
              <button
                type="button"
                className="new-evaluation-btn"
                onClick={() => setIsTemplateEditorOpen(true)}
              >
                CREATE / EDIT TEMPLATE
              </button>
            </div>
          )}
        </div>
      </section>

      <section className="dashboard-section">
        <SectionHeader title="Delivery Logs" action="EXPORT LOGS" />
        <div className="alerts-card">
          {logsError && <p className="dashboard-error-message">{logsError}</p>}
          {logsLoading ? (
            <p className="muted-note">Loading delivery logs...</p>
          ) : (
            <>
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
            </>
          )}
        </div>
      </section>
    </>
  );
}

export default AlertsPage;
