import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import "../styles/history.css";

function HistoryPage({ user, onNavChange }) {
  const [activeNav, setActiveNav] = useState("History");
  const [evaluatorFilter, setEvaluatorFilter] = useState("all");
  const [organizationFilter, setOrganizationFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [managerFilter, setManagerFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };

  // Sample evaluation history data
  const evaluationData = [
    {
      id: "#EV-2024-0891",
      evaluator: "Sarah Jenkins",
      evaluatorAvatar: "SJ",
      asset: "XJ-900 Core",
      assetType: "Turbine Unit",
      organization: "Aero Precision Ltd",
      equipment: "Industrial Press-02",
      capacity: "1200kg",
      load: "850kg",
      status: "Compliance",
      statusBg: "#d1fae5",
      statusColor: "#047857",
      alert: "Unsent",
      alertIcon: "📤",
    },
    {
      id: "#EV-2024-0889",
      evaluator: "Michael Chen",
      evaluatorAvatar: "MC",
      asset: "Hydro-Lift S1",
      assetType: "Crane",
      organization: "Skybound Logistics",
      equipment: "Heavy Crane X-1",
      capacity: "5000kg",
      load: "4500kg",
      status: "Non-Compliance",
      statusBg: "#fee2e2",
      statusColor: "#dc2626",
      alert: "Resolved",
      alertIcon: "✓",
    },
    {
      id: "#EV-2024-0880",
      evaluator: "Alice Mane",
      evaluatorAvatar: "AM",
      asset: "Delta Pump 4",
      assetType: "Fluid Handler",
      organization: "Global Freight Co",
      equipment: "Valve Matrix 09",
      capacity: "450L/min",
      load: "320L/min",
      status: "Compliance",
      statusBg: "#d1fae5",
      statusColor: "#047857",
      alert: "Sent",
      alertIcon: "✓",
    },
    {
      id: "#EV-2024-0880",
      evaluator: "David Wright",
      evaluatorAvatar: "DW",
      asset: "Thermal-X P1",
      assetType: "Heat Exchanger",
      organization: "Aero Precision Ltd",
      equipment: "Condenser Unit 4",
      capacity: "800kW",
      load: "750kW",
      status: "Compliance",
      statusBg: "#d1fae5",
      statusColor: "#047857",
      alert: "Sent",
      alertIcon: "✓",
    },
  ];

  const handleNewEvaluation = () => {
    console.log("Create new evaluation");
    // TODO: Navigate to evaluation creation page or open modal
  };

  const handleAction = (evaluationId) => {
    console.log("Action for:", evaluationId);
    // TODO: Implement action menu
  };

  const uniqueEvaluators = ["All Evaluators", "Sarah Jenkins", "Michael Chen", "Alice Mane", "David Wright"];
  const uniqueOrganizations = ["All Organisations", "Aero Precision Ltd", "Skybound Logistics", "Global Freight Co"];
  const statuses = ["All Results", "Compliance", "Non-Compliance"];
  const managers = ["All Managers", "Manager 1", "Manager 2", "Manager 3"];

  return (
    <AppLayout activeNav={activeNav} onNavChange={handleNavChange} user={user}>
      <div className="history-container">
        {/* Page Header */}
        <div className="history-header">
          <div className="header-left">
            <h1 className="header-title">Evaluation History</h1>
            <p className="header-description">
              Complete audit trail of asset integrity checks and compliance reporting across all active operational zones.
            </p>
          </div>
          <button className="btn-new-evaluation" onClick={handleNewEvaluation}>
            <span className="btn-icon">+</span>
            <span>New Evaluation</span>
          </button>
        </div>

        {/* Filters Section */}
        <div className="filters-area">
          <div className="filter-group">
            <label className="filter-label">EVALUATOR</label>
            <select
              className="filter-select"
              value={evaluatorFilter}
              onChange={(e) => setEvaluatorFilter(e.target.value)}
            >
              {uniqueEvaluators.map((evaluator) => (
                <option key={evaluator} value={evaluator.toLowerCase()}>
                  {evaluator}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">ORGANISATION</label>
            <select
              className="filter-select"
              value={organizationFilter}
              onChange={(e) => setOrganizationFilter(e.target.value)}
            >
              {uniqueOrganizations.map((org) => (
                <option key={org} value={org.toLowerCase()}>
                  {org}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">RESULT STATUS</label>
            <select
              className="filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              {statuses.map((status) => (
                <option key={status} value={status.toLowerCase()}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label className="filter-label">ASSET MANAGERS</label>
            <select
              className="filter-select"
              value={managerFilter}
              onChange={(e) => setManagerFilter(e.target.value)}
            >
              {managers.map((manager) => (
                <option key={manager} value={manager.toLowerCase()}>
                  {manager}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Evaluation History Table */}
        <div className="history-table-container">
          <table className="history-table">
            <thead>
              <tr className="table-header-row">
                <th className="table-header-cell table-cell-id">EVALUATION ID</th>
                <th className="table-header-cell table-cell-evaluator">EVALUATOR</th>
                <th className="table-header-cell table-cell-asset">ASSET</th>
                <th className="table-header-cell table-cell-org">ORGANISATION</th>
                <th className="table-header-cell table-cell-equipment">EQUIPMENT</th>
                <th className="table-header-cell table-cell-capacity">CAPACITY</th>
                <th className="table-header-cell table-cell-result">RESULT</th>
                <th className="table-header-cell table-cell-alert">ALERT</th>
                <th className="table-header-cell table-cell-action">ACTION</th>
              </tr>
            </thead>
            <tbody>
              {evaluationData.map((evaluation, idx) => (
                <tr key={idx} className="table-body-row">
                  <td className="table-cell table-cell-id">
                    <span className="eval-id">{evaluation.id}</span>
                  </td>
                  <td className="table-cell table-cell-evaluator">
                    <div className="evaluator-cell">
                      <div className="evaluator-avatar">{evaluation.evaluatorAvatar}</div>
                      <span className="evaluator-name">{evaluation.evaluator}</span>
                    </div>
                  </td>
                  <td className="table-cell table-cell-asset">
                    <div className="asset-info">
                      <div className="asset-name">{evaluation.asset}</div>
                      <div className="asset-type">{evaluation.assetType}</div>
                    </div>
                  </td>
                  <td className="table-cell table-cell-org">
                    <div className="org-info">{evaluation.organization}</div>
                  </td>
                  <td className="table-cell table-cell-equipment">
                    <div className="equipment-info">{evaluation.equipment}</div>
                  </td>
                  <td className="table-cell table-cell-capacity">
                    <div className="capacity-info">
                      <div className="capacity-value">{evaluation.capacity}</div>
                      <div className="capacity-load">Load: {evaluation.load}</div>
                    </div>
                  </td>
                  <td className="table-cell table-cell-result">
                    <span
                      className="status-badge"
                      style={{
                        backgroundColor: evaluation.statusBg,
                        color: evaluation.statusColor,
                      }}
                    >
                      {evaluation.status}
                    </span>
                  </td>
                  <td className="table-cell table-cell-alert">
                    <div className="alert-cell">
                      <span className="alert-icon">{evaluation.alertIcon}</span>
                      <span className="alert-status">{evaluation.alert}</span>
                    </div>
                  </td>
                  <td className="table-cell table-cell-action">
                    <button
                      className="action-btn"
                      onClick={() => handleAction(evaluation.id)}
                      title="More options"
                    >
                      ⋮
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="pagination-container">
          <div className="pagination-info">
            <span>SHOWING 1 TO 10 OF 1,240 ENTRIES</span>
          </div>
          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              ←
            </button>
            <button className="pagination-btn active">1</button>
            <button className="pagination-btn">2</button>
            <button className="pagination-btn">3</button>
            <span className="pagination-ellipsis">...</span>
            <button className="pagination-btn">124</button>
            <button
              className="pagination-btn"
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              →
            </button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default HistoryPage;
