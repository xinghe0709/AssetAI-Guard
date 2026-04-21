function DashboardHeader() {
    return (
      <section className="dashboard-header">
        <div>
          <h1 className="dashboard-title">AssetGuard AI</h1>
          <p className="dashboard-subtitle">
            Precision Management for critical infrastructure. Monitor, evaluate,
            and secure your physical assets with Ethereal Precision.
          </p>
        </div>
  
        <button type="button" className="new-evaluation-btn">
          + New Evaluation
        </button>
      </section>
    );
  }
  
  export default DashboardHeader;