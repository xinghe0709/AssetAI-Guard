function SectionHeader({ title, action, onAction, actionDisabled = false }) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      <button
        type="button"
        className="section-action"
        onClick={onAction}
        disabled={actionDisabled}
      >
        {action}
      </button>
    </div>
  );
}

export default SectionHeader;
