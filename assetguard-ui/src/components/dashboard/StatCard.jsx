function StatCard({ label, value, meta, description }) {
    return (
      <div className="stat-card">
        <div className="stat-label">{label}</div>
        <div className="stat-row">
          <span className="stat-value">{value}</span>
          <span className="stat-meta">{meta}</span>
        </div>
        <div className="stat-divider"></div>
        <p className="stat-description">{description}</p>
      </div>
    );
  }
  
  export default StatCard;