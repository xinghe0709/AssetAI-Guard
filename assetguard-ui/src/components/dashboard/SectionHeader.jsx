function SectionHeader({ title, action }) {
    return (
      <div className="section-header">
        <h2>{title}</h2>
        <button type="button" className="section-action">
          {action}
        </button>
      </div>
    );
  }
  
  export default SectionHeader;