export default function EmailTemplateEditor({ template, onTemplateChange, onSave, saving }) {
  return (
    <section className="card">
      <h2>Email Template</h2>
      <p className="sub">Use placeholders like {'{assetName}'}, {'{status}'}, {'{overloadPercent}'}.</p>

      <label>
        Subject
        <input
          type="text"
          value={template.subject}
          onChange={(e) => onTemplateChange("subject", e.target.value)}
        />
      </label>

      <label>
        Body
        <textarea
          rows={8}
          value={template.body}
          onChange={(e) => onTemplateChange("body", e.target.value)}
        />
      </label>

      <button onClick={onSave} disabled={saving}>
        {saving ? "Saving..." : "Save Template"}
      </button>
    </section>
  );
}
