import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import "../styles/evaluation.css";
import imgIndustrialTurbine from "../assets/building.png";

function EvaluationPage({ user, onNavChange }) {
  const [activeNav, setActiveNav] = useState("Evaluation");

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };
  const [formData, setFormData] = useState({
    assetSelection: "Turbine Unit Alpha-7",
    equipmentType: "Rotary Propulsion",
    plannedLoad: "8500",
    unit: "RPM (Revolutions)",
    description: "Standard quarterly stress test under peak seasonal thermal variance.",
  });

  const [evaluationResult, setEvaluationResult] = useState({
    status: "Compliant",
    safetyScore: "98/100",
    date: "Oct 24, 2023",
    operationalMargin: "14.2%",
    thermalStability: "Optimal",
    thermalDetail: "Temperature remains within 2% variance of nominal threshold.",
    modelMatch: "The evaluated load parameters perfectly align with Alpha-7's historical peak performance signatures. No structural fatigue detected in digital twin simulation.",
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleEvaluate = () => {
    // API call would go here
    console.log("Evaluating with:", formData);
  };

  return (
    <AppLayout activeNav={activeNav} onNavChange={handleNavChange} user={user}>
      <div className="evaluation-container">
        {/* Page Header */}
        <div className="evaluation-header">
          <div className="page-heading">
            <h1 className="page-title">New Evaluation</h1>
            <p className="page-description">
              Initiate a precision diagnostic by selecting the industrial asset and
              defining load parameters. The AI will verify compliance against
              current engineering standards.
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="evaluation-content">
          {/* Input Form Section */}
          <div className="input-form-section">
            <div className="form-grid">
              {/* Asset Selection */}
              <div className="form-group form-group-asset">
                <label className="form-label">ASSET SELECTION</label>
                <div className="select-wrapper">
                  <select
                    name="assetSelection"
                    value={formData.assetSelection}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                    <option>Turbine Unit Alpha-7</option>
                    <option>Turbine Unit Beta-3</option>
                  </select>
                  <span className="select-icon">▼</span>
                </div>
              </div>

              {/* Equipment Type */}
              <div className="form-group">
                <label className="form-label">EQUIPMENT TYPE</label>
                <input
                  type="text"
                  name="equipmentType"
                  value={formData.equipmentType}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>

              {/* Planned Load */}
              <div className="form-group">
                <label className="form-label">PLANNED LOAD</label>
                <input
                  type="text"
                  name="plannedLoad"
                  value={formData.plannedLoad}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>

              {/* Unit */}
              <div className="form-group form-group-unit">
                <label className="form-label">UNIT</label>
                <div className="select-wrapper">
                  <select
                    name="unit"
                    value={formData.unit}
                    onChange={handleInputChange}
                    className="form-select"
                  >
                    <option>RPM (Revolutions)</option>
                    <option>PSI (Pressure)</option>
                  </select>
                  <span className="select-icon">▼</span>
                </div>
              </div>

              {/* Detailed Description */}
              <div className="form-group form-group-description">
                <label className="form-label">DETAILED DESCRIPTION</label>
                <input
                  type="text"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  className="form-input"
                />
              </div>
            </div>

            {/* Evaluate Button */}
            <div className="form-actions">
              <button className="btn btn-primary" onClick={handleEvaluate}>
                ⚡ Evaluate Asset
              </button>
            </div>
          </div>

          {/* Evaluation Result Section */}
          <div className="evaluation-result-section">
            <div className="result-header">
              <h2 className="result-title">Evaluation Result</h2>
              <span className="result-badge">LIVE ANALYSIS</span>
            </div>

            <div className="result-grid">
              {/* Compliance Card */}
              <div className="compliance-card">
                <div className="compliance-badge">
                  <span className="badge-icon">✓</span>
                </div>
                <h3 className="compliance-status">{evaluationResult.status}</h3>
                <p className="safety-score">Safety Score: {evaluationResult.safetyScore}</p>
                <p className="result-date">{evaluationResult.date}</p>
              </div>

              {/* Metrics Cards */}
              <div className="metrics-column">
                {/* Operational Margin */}
                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-label">OPERATIONAL MARGIN</span>
                    <span className="metric-icon">📈</span>
                  </div>
                  <div className="metric-value">{evaluationResult.operationalMargin}</div>
                  <p className="metric-subtitle">Current Load vs Structural Limit</p>
                  <div className="metric-bar">
                    <div className="metric-bar-fill" style={{ width: "14.2%" }}></div>
                  </div>
                </div>

                {/* Thermal Stability */}
                <div className="metric-card">
                  <div className="metric-header">
                    <span className="metric-label">THERMAL STABILITY</span>
                    <span className="metric-icon">🌡️</span>
                  </div>
                  <h3 className="thermal-status">{evaluationResult.thermalStability}</h3>
                  <p className="thermal-detail">{evaluationResult.thermalDetail}</p>
                </div>
              </div>

              {/* Model Signature Match */}
              <div className="model-signature-card">
                <h3 className="signature-title">Model Signature Match</h3>
                <div className="signature-content">
                  <img src={imgIndustrialTurbine} alt="Turbine" className="signature-image" />
                  <p className="signature-text">{evaluationResult.modelMatch}</p>
                </div>
                <div className="signature-actions">
                  <button className="btn-link">Download PDF Report</button>
                  <button className="btn-link">Export JSON Data</button>
                </div>
              </div>
            </div>

            {/* Result Footer */}
            <div className="result-footer">
              <div className="system-status">
                <span className="status-indicator">●</span>
                <span className="status-text">All Nodes Operational</span>
              </div>
              <div className="result-actions">
                <button className="btn btn-secondary">← Reset Parameters</button>
                <button className="btn btn-primary">Finalize Evaluation</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default EvaluationPage;
