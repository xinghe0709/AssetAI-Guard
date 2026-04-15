import { useMemo, useState } from "react";
import NotificationPreferences from "./components/NotificationPreferences";
import EmailTemplateEditor from "./components/EmailTemplateEditor";
import EmailLogsTable from "./components/EmailLogsTable";
import { fetchEmailLogs, saveEmailPreferences, saveEmailTemplate } from "./api/emailApi";

const MOCK_LOGS = [
  {
    id: "log-1",
    sentAt: "2026-04-15T09:45:00Z",
    assetName: "Berth 5",
    evaluationStatus: "Non-Compliant",
    recipient: "asset.manager@demo.com",
    deliveryStatus: "Delivered",
  },
  {
    id: "log-2",
    sentAt: "2026-04-15T09:50:00Z",
    assetName: "Hardstand A",
    evaluationStatus: "Compliant",
    recipient: "safety@demo.com",
    deliveryStatus: "Delivered",
  },
];

export default function App() {
  const [token, setToken] = useState("");
  const [logs, setLogs] = useState(MOCK_LOGS);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [message, setMessage] = useState("");

  const [form, setForm] = useState({
    escalationThresholdPercent: 20,
    digestTimeUtc: "09:00",
    recipientsCsv: "asset.manager@demo.com,safety@demo.com",
    sendOnNonCompliant: true,
  });

  const [template, setTemplate] = useState({
    subject: "[AssetGuard] {status} - {assetName}",
    body: "Evaluation result: {status}\nAsset: {assetName}\nOverload: {overloadPercent}%",
  });

  const canSync = useMemo(() => token.trim().length > 0, [token]);

  const updateForm = (key, value) => setForm((prev) => ({ ...prev, [key]: value }));
  const updateTemplate = (key, value) => setTemplate((prev) => ({ ...prev, [key]: value }));

  const syncLogs = async () => {
    if (!canSync) {
      setMessage("No token set. Showing mock logs only.");
      return;
    }
    try {
      setLoadingLogs(true);
      const payload = await fetchEmailLogs(token);
      setLogs(payload?.data?.items || []);
      setMessage("Email logs synced from backend.");
    } catch (error) {
      setMessage(`Sync failed: ${error.message}`);
    } finally {
      setLoadingLogs(false);
    }
  };

  const handleSavePreferences = async () => {
    if (!canSync) {
      setMessage("No token set. Preferences not sent.");
      return;
    }
    try {
      setSavingPrefs(true);
      await saveEmailPreferences(token, form);
      setMessage("Preferences saved successfully.");
    } catch (error) {
      setMessage(`Save preferences failed: ${error.message}`);
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!canSync) {
      setMessage("No token set. Template not sent.");
      return;
    }
    try {
      setSavingTemplate(true);
      await saveEmailTemplate(token, template);
      setMessage("Template saved successfully.");
    } catch (error) {
      setMessage(`Save template failed: ${error.message}`);
    } finally {
      setSavingTemplate(false);
    }
  };

  return (
    <main className="container">
      <header className="header">
        <div>
          <h1>Email Notification Module (React)</h1>
          <p>Focused scope for the email owner: preferences, template, and communication logs.</p>
        </div>
        <div className="tokenBox">
          <label>
            Bearer Token
            <input
              type="password"
              placeholder="paste token from /api/v1/auth/login"
              value={token}
              onChange={(e) => setToken(e.target.value)}
            />
          </label>
          <button onClick={syncLogs}>Sync Logs</button>
        </div>
      </header>

      {message ? <div className="message">{message}</div> : null}

      <div className="layout">
        <div className="leftCol">
          <NotificationPreferences
            form={form}
            onChange={updateForm}
            onSave={handleSavePreferences}
            saving={savingPrefs}
          />
          <EmailTemplateEditor
            template={template}
            onTemplateChange={updateTemplate}
            onSave={handleSaveTemplate}
            saving={savingTemplate}
          />
        </div>

        <div className="rightCol">
          <EmailLogsTable logs={logs} loading={loadingLogs} />
        </div>
      </div>
    </main>
  );
}
