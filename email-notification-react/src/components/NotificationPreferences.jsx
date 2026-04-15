export default function NotificationPreferences({ form, onChange, onSave, saving }) {
  return (
    <section className="card">
      <h2>Email Notification Preferences</h2>
      <p className="sub">Configure who receives alerts and when emails should be triggered.</p>

      <div className="grid2">
        <label>
          Escalation threshold (%)
          <input
            type="number"
            min="1"
            max="100"
            value={form.escalationThresholdPercent}
            onChange={(e) => onChange("escalationThresholdPercent", Number(e.target.value))}
          />
        </label>

        <label>
          Daily digest time (UTC)
          <input
            type="time"
            value={form.digestTimeUtc}
            onChange={(e) => onChange("digestTimeUtc", e.target.value)}
          />
        </label>
      </div>

      <label>
        Recipients (comma separated)
        <textarea
          rows={3}
          value={form.recipientsCsv}
          onChange={(e) => onChange("recipientsCsv", e.target.value)}
          placeholder="asset.manager@company.com, safety@company.com"
        />
      </label>

      <div className="row">
        <label className="toggle">
          <input
            type="checkbox"
            checked={form.sendOnNonCompliant}
            onChange={(e) => onChange("sendOnNonCompliant", e.target.checked)}
          />
          Send immediately for Non-Compliant evaluations
        </label>
      </div>

      <button onClick={onSave} disabled={saving}>
        {saving ? "Saving..." : "Save Preferences"}
      </button>
    </section>
  );
}
