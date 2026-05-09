import { useEffect, useMemo, useState } from "react";
import TemplateEditorModal from "../components/dashboard/TemplateEditorModal";
import {
  getEmailLogs,
  getEmailTemplate,
  updateEmailTemplate,
  sendTestEmail,
} from "../services/alertsApi";
import "../styles/alerts.css";

const defaultTemplate = {
  subject: "[ASSETGUARD] THRESHOLD BREACH DETECTED",
  body: "A monitored asset has exceeded the configured load threshold. Please review the latest evaluation report immediately.",
};

function AlertsPage() {
  const [subject, setSubject] = useState(defaultTemplate.subject);
  const [body, setBody] = useState(defaultTemplate.body);
  const [templateSnapshot, setTemplateSnapshot] = useState(defaultTemplate);

  const [deliveryLogs, setDeliveryLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState("");

  const [templateError, setTemplateError] = useState("");
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);
  const [isSendingTestEmail, setIsSendingTestEmail] = useState(false);
  const [testEmailSuccessFeedback, setTestEmailSuccessFeedback] = useState("");

  const [statusFilter, setStatusFilter] = useState("All Communications");
  const [dateRange, setDateRange] = useState("Last 30 Days");
  const [searchTerm, setSearchTerm] = useState("");
  const [isTemplateEditorOpen, setIsTemplateEditorOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 10;

  useEffect(() => {
    const loadAlertsData = async () => {
      setLogsLoading(true);
      setLogsError("");
      setTemplateError("");

      const [templateResult, logsResult] = await Promise.allSettled([
        getEmailTemplate(),
        getEmailLogs(),
      ]);

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

  const isTemplateDirty =
    subject !== templateSnapshot.subject || body !== templateSnapshot.body;

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
    setTestEmailSuccessFeedback("");
    try {
      const testResult = await sendTestEmail();
      setDeliveryLogs((previous) => [testResult, ...previous]);
      setTestEmailSuccessFeedback(
        `Test email sent successfully to ${testResult.recipient || "your email"}.`
      );
    } catch (error) {
      setTemplateError(error.message || "Unable to send test email.");
    } finally {
      setIsSendingTestEmail(false);
    }
  };

  const allFilteredLogs = useMemo(() => {
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

  const totalPages = Math.ceil(allFilteredLogs.length / PAGE_SIZE);
  const filteredLogs = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    const end = start + PAGE_SIZE;
    return allFilteredLogs.slice(start, end);
  }, [allFilteredLogs, currentPage]);

  return (
    <>
      <header className="alerts-header">
        <div className="header-left">
          <h1 className="header-title">Alerts &amp; Communication Logs</h1>
          <p className="header-description">
            Track and manage system-generated email notifications, including load
            warnings and compliance reports.
          </p>
        </div>
        <button
          type="button"
          className="btn-new-evaluation"
          onClick={() => setIsTemplateEditorOpen(true)}
        >
          <span>Template Editor</span>
        </button>
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

        <div className="table-card">
          {logsError && <p className="dashboard-error-message alerts-inline-error">{logsError}</p>}
          {logsLoading ? (
            <p className="muted-note alerts-inline-loading">Loading delivery logs...</p>
          ) : (
            <>
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

              {/* Pagination */}
              <div className="pagination-container">
                <div className="pagination-info">
                  <span>Showing {filteredLogs.length > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0}-{Math.min(currentPage * PAGE_SIZE, allFilteredLogs.length)} of {allFilteredLogs.length} logs</span>
                </div>
                <div className="pagination-controls">
                  <button
                    className="pagination-button"
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                  >
                    ←
                  </button>
                  <span className="pagination-number">{currentPage}</span>
                  <button
                    className="pagination-button"
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages || totalPages === 0}
                  >
                    →
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </section>

      {templateError && !isTemplateEditorOpen && (
        <p className="dashboard-error-message">{templateError}</p>
      )}

      <TemplateEditorModal
        open={isTemplateEditorOpen}
        onClose={() => {
          setTestEmailSuccessFeedback("");
          setIsTemplateEditorOpen(false);
        }}
        subject={subject}
        body={body}
        onSubjectChange={setSubject}
        onBodyChange={setBody}
        onSaveTemplate={handleSaveTemplate}
        onSendTestEmail={handleSendTestEmail}
        isSavingTemplate={isSavingTemplate}
        disableSaveTemplate={!isTemplateDirty}
        isSendingTestEmail={isSendingTestEmail}
        templateError={templateError}
        testEmailSuccessFeedback={testEmailSuccessFeedback}
        onDismissSuccess={() => setTestEmailSuccessFeedback("")}
      />
    </>
  );
}

export default AlertsPage;
