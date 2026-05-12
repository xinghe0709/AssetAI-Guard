function TemplateEditorModal({
  open,
  onClose,
  subject,
  body,
  onSubjectChange,
  onBodyChange,
  onSaveTemplate,
  onSendTestEmail,
  isSavingTemplate,
  disableSaveTemplate,
  isSendingTestEmail,
  templateError,
  testEmailSuccessFeedback,
  onDismissSuccess,
}) {
  if (!open) {
    return null;
  }

  return (
    <div className="template-modal-backdrop" role="dialog" aria-modal="true">
      <div className="template-modal-card template-modal-card-single">
        <div className="template-modal-header">
          <h2>Template Editor</h2>
          <button type="button" className="section-action" onClick={onClose}>
            CLOSE
          </button>
        </div>

        {testEmailSuccessFeedback && (
          <div className="template-success-banner">
            <span className="template-success-icon">&#10003;</span>
            {testEmailSuccessFeedback}
            <button
              type="button"
              className="template-success-dismiss"
              onClick={onDismissSuccess}
              aria-label="Dismiss"
            >
              &times;
            </button>
          </div>
        )}

        {templateError && (
          <p className="dashboard-error-message">{templateError}</p>
        )}

        <div className="template-editor-form">
          <label className="alerts-field">
            <span className="alerts-label">SUBJECT</span>
            <input
              type="text"
              value={subject}
              onChange={(event) => onSubjectChange(event.target.value)}
            />
          </label>

          <label className="alerts-field">
            <span className="alerts-label">BODY</span>
            <textarea
              rows="10"
              value={body}
              onChange={(event) => onBodyChange(event.target.value)}
            />
          </label>

          <div className="alerts-actions">
            <button
              type="button"
              className="new-evaluation-btn"
              onClick={onSaveTemplate}
              disabled={isSavingTemplate || disableSaveTemplate}
            >
              {isSavingTemplate && <span className="btn-spinner" />}
              {isSavingTemplate ? "SAVING..." : "SAVE TEMPLATE"}
            </button>
            <button
              type="button"
              className="new-evaluation-btn"
              onClick={onSendTestEmail}
              disabled={isSendingTestEmail}
            >
              {isSendingTestEmail && <span className="btn-spinner" />}
              {isSendingTestEmail ? "SENDING..." : "SEND TEST EMAIL"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TemplateEditorModal;
