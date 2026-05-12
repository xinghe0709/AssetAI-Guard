import { useState, useEffect } from "react";
import AppLayout from "../components/layout/AppLayout";
import "../styles/evaluation.css";
import imgIndustrialTurbine from "../assets/building.png";
import { getAuthToken } from "../services/authSession";

const EQUIPMENT_OPTIONS = [
  "Crane with outriggers",
  "Mobile crane",
  "Heavy vehicle",
  "Elevated Work Platform",
  "Storage Load",
  "Vessel",
];

// Maps equipment to required load capacity name
const EQUIPMENT_TO_CAPACITY = {
  "Crane with outriggers": "max point load",
  "Mobile crane": "max axle load",
  "Heavy vehicle": "max axle load",
  "Elevated Work Platform": "max point load",
  "Storage Load": "max uniform distributor load",
  "Vessel": "max displacement size",
};

const LOAD_PARAMETER_MAPPING = {
  "Crane with outriggers": { label: "Max Outrigger Load", metric: "kN" },
  "Mobile crane": { label: "Max Axle Load", metric: "t" },
  "Heavy vehicle": { label: "Max Axle Load", metric: "t" },
  "Elevated Work Platform": { label: "Max Wheel Load", metric: "kN" },
  "Storage Load": { label: "Uniform Distributor Load", metric: "kPa" },
  "Vessel": { label: "Displacement", metric: "t" },
};

function EvaluationPage({ user, onNavChange, onLogout }) {
  const [activeNav, setActiveNav] = useState("Evaluation");
  const [showResult, setShowResult] = useState(false);
  
  // Form data state
  const [formData, setFormData] = useState({
    location: "",
    asset: "",
    equipment: "",
    equipmentModel: "",
    loadParameter: "",
    detailedDescription: "",
  });
  
  // Backend data state
  const [locations, setLocations] = useState([]);
  const [assetsByLocation, setAssetsByLocation] = useState({});
  const [assetsWithCapacities, setAssetsWithCapacities] = useState({});
  const [selectedAssetLoadCapacities, setSelectedAssetLoadCapacities] = useState([]);
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [loadingAssets, setLoadingAssets] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");

  const [evaluationResult, setEvaluationResult] = useState(null);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailMessage, setEmailMessage] = useState(null);

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };

  // Fetch locations on component mount
  useEffect(() => {
    const fetchLocations = async () => {
      setLoadingLocations(true);
      setError("");
      try {
        const token = getAuthToken();
        if (!token) {
          setError("No authentication token found. Please log in again.");
          return;
        }

        const response = await fetch(
          "http://127.0.0.1:5000/api/v1/locations/",
          {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch locations: ${response.statusText}`);
        }

        const result = await response.json();
        if (result.success && Array.isArray(result.data)) {
          setLocations(result.data);
        } else {
          setError("Invalid response format from server");
        }
      } catch (err) {
        console.error("Error fetching locations:", err);
        setError(err.message || "Failed to load locations");
      } finally {
        setLoadingLocations(false);
      }
    };

    fetchLocations();
  }, []);

  // Fetch assets when location is selected
  useEffect(() => {
    if (!formData.location) {
      setAssetsByLocation({});
      return;
    }

    const fetchAssets = async () => {
      setLoadingAssets(true);
      setError("");
      try {
        const token = getAuthToken();
        if (!token) {
          setError("No authentication token found. Please log in again.");
          return;
        }

        const response = await fetch(
          `http://127.0.0.1:5000/api/v1/assets/?locationId=${formData.location}`,
          {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch assets: ${response.statusText}`);
        }

        const result = await response.json();
        if (result.success && result.data?.items) {
          // Map assets to a simple format for the select dropdown
          const assets = result.data.items.map(item => ({
            id: item.id,
            name: item.name,
          }));
          setAssetsByLocation(prev => ({
            ...prev,
            [formData.location]: assets,
          }));
          
          // Also store complete asset data with loadCapacities
          const assetsWithLoadCapacities = {};
          result.data.items.forEach(item => {
            assetsWithLoadCapacities[item.id] = item;
          });
          setAssetsWithCapacities(prev => ({
            ...prev,
            [formData.location]: assetsWithLoadCapacities,
          }));
        } else {
          setError("Invalid response format from server");
        }
      } catch (err) {
        console.error("Error fetching assets:", err);
        setError(err.message || "Failed to load assets");
      } finally {
        setLoadingAssets(false);
      }
    };

    fetchAssets();
  }, [formData.location]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));

    // If asset selection changed, get its load capacities from stored data
    if (name === "asset" && value) {
      const assetWithCapacities = assetsWithCapacities[formData.location]?.[value];
      if (assetWithCapacities) {
        setSelectedAssetLoadCapacities(assetWithCapacities.loadCapacities || []);
      } else {
        setSelectedAssetLoadCapacities([]);
      }
      // Reset equipment and load parameter when asset changes
      setFormData(prev => ({
        ...prev,
        equipment: "",
        loadParameter: "",
      }));
    }
  };

  const handleLocationChange = (e) => {
    const locationId = e.target.value;
    setFormData(prev => ({
      ...prev,
      location: locationId,
      asset: "", // Reset asset when location changes
    }));
  };

  const handleEquipmentChange = (e) => {
    const equipment = e.target.value;
    setFormData(prev => ({
      ...prev,
      equipment,
      loadParameter: "", // Reset load parameter when equipment changes
    }));
  };

  const handleEvaluate = async () => {
    // Validate required fields
    if (!formData.location || !formData.asset || !formData.equipment || !formData.loadParameter) {
      setError("Please fill in all required fields: Location, Asset, Equipment, and Load Parameter");
      return;
    }

    setEvaluating(true);
    setError("");
    try {
      const token = getAuthToken();
      if (!token) {
        setError("No authentication token found. Please log in again.");
        return;
      }

      const response = await fetch(
        "http://127.0.0.1:5000/api/v1/evaluations/check",
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            locationId: parseInt(formData.location),
            assetId: parseInt(formData.asset),
            equipment: formData.equipment,
            equipmentModel: formData.equipmentModel || null,
            loadParameterValue: parseFloat(formData.loadParameter),
            remark: formData.detailedDescription || null,
          }),
        }
      );

      if (!response.ok) {
        const errorResult = await response.json();
        throw new Error(errorResult.message || `Failed to evaluate: ${response.statusText}`);
      }

      const result = await response.json();
      if (result.success && result.data) {
        setEvaluationResult(result.data);
        setShowResult(true);
      } else {
        setError("Invalid response format from server");
      }
    } catch (err) {
      console.error("Error evaluating:", err);
      setError(err.message || "Failed to evaluate asset");
    } finally {
      setEvaluating(false);
    }
  };

  const handleSendEmail = async () => {
    if (!evaluationResult?.id) return;
    setSendingEmail(true);
    setEmailMessage(null);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `http://127.0.0.1:5000/api/v1/evaluations/${evaluationResult.id}/notify`,
        {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.message || `Request failed: ${response.status}`);
      }
      const result = await response.json();
      if (result.success) {
        setEmailMessage({
          type: result.data.emailStatus === "Delivered" ? "success" : "warning",
          text: result.data.emailStatus === "Delivered"
            ? "Email sent successfully!"
            : `Email status: ${result.data.emailStatus}`,
        });
      }
    } catch (err) {
      setEmailMessage({ type: "error", text: err.message || "Failed to send email" });
    } finally {
      setSendingEmail(false);
    }
  };

  // Get available assets based on selected location
  const availableAssets = formData.location 
    ? assetsByLocation[formData.location] || [] 
    : [];

  // Get available equipment based on selected asset's load capacities
  const availableEquipment = EQUIPMENT_OPTIONS.filter(equipment => {
    const requiredCapacity = EQUIPMENT_TO_CAPACITY[equipment];
    return selectedAssetLoadCapacities.some(
      capacity => capacity.name === requiredCapacity
    );
  });

  // Get load parameter info based on selected equipment
  const loadParameterInfo = formData.equipment 
    ? LOAD_PARAMETER_MAPPING[formData.equipment] 
    : null;

  return (
    <AppLayout
      activeNav={activeNav}
      onNavChange={handleNavChange}
      user={user}
      onLogout={onLogout}
    >
      <div className="evaluation-container">
          {/* Page Header */}
        <div className="page-header">
          <div className="header-left">
            <h1 className="header-title">New Evaluation</h1>
            <p className="header-description">
              The AI will verify compliance against current engineering standards.
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="evaluation-content">
          {/* Error Message */}
          {error && (
            <div className="alert alert-error">
              ⚠️ {error}
            </div>
          )}

          {/* Email Message */}
          {emailMessage && (
            <div className={`alert alert-${emailMessage.type}`}>
              {emailMessage.type === "success" ? "✓" : emailMessage.type === "warning" ? "⚠️" : "✕"} {emailMessage.text}
            </div>
          )}

          {/* Input Form Section */}
          {!showResult && (
          <div className="input-form-section">
            <div className="form-grid-layout">
              {/* Row 1: Location & Asset */}
              <div className="form-group form-group-col-1">
                <label className="form-label">LOCATION</label>
                <div className="select-wrapper">
                  <select
                    name="location"
                    value={formData.location}
                    onChange={handleLocationChange}
                    className="form-select"
                    disabled={loadingLocations}
                  >
                    <option value="">
                      {loadingLocations ? "Loading locations..." : "Select a Location"}
                    </option>
                    {locations.map(loc => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group form-group-col-2">
                <label className="form-label">ASSET</label>
                <div className="select-wrapper">
                  <select
                    name="asset"
                    value={formData.asset}
                    onChange={handleInputChange}
                    className="form-select"
                    disabled={!formData.location || loadingAssets}
                  >
                    <option value="">
                      {loadingAssets 
                        ? "Loading assets..." 
                        : (!formData.location ? "Select a Location first" : "Select an Asset")}
                    </option>
                    {availableAssets.map(asset => (
                      <option key={asset.id} value={asset.id}>
                        {asset.name}
                      </option>
                    ))}
                  </select>
                  <span className="select-icon">▼</span>
                </div>
              </div>

              {/* Row 2: Equipment, Equipment Model, Load Parameter */}
              <div className="form-group form-group-col-1">
                <label className="form-label">EQUIPMENT</label>
                <div className="select-wrapper">
                  <select
                    name="equipment"
                    value={formData.equipment}
                    onChange={handleEquipmentChange}
                    className="form-select"
                    disabled={!formData.asset || availableEquipment.length === 0}
                  >
                    <option value="">
                      {!formData.asset 
                        ? "Select an Asset first" 
                        : availableEquipment.length === 0
                        ? "No compatible equipment"
                        : "Select Equipment"}
                    </option>
                    {availableEquipment.map(eq => (
                      <option key={eq} value={eq}>
                        {eq}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group form-group-col-2">
                <label className="form-label">EQUIPMENT MODEL</label>
                <input
                  type="text"
                  name="equipmentModel"
                  value={formData.equipmentModel}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Enter equipment model details"
                />
              </div>

              {loadParameterInfo && (
                <div className="form-group form-group-col-3">
                  <label className="form-label">
                    {loadParameterInfo.label.toUpperCase()}
                  </label>
                  <div className="load-parameter-input-group">
                    <input
                      type="number"
                      name="loadParameter"
                      value={formData.loadParameter}
                      onChange={handleInputChange}
                      className="form-input"
                      placeholder="Enter value"
                    />
                    <span className="load-parameter-metric">{loadParameterInfo.metric}</span>
                  </div>
                </div>
              )}

              {/* Row 3: Detailed Description */}
              <div className="form-group form-group-full-width">
                <label className="form-label">DETAILED DESCRIPTION</label>
                <textarea
                  name="detailedDescription"
                  value={formData.detailedDescription}
                  onChange={handleInputChange}
                  className="form-textarea"
                  placeholder="Enter detailed description about the evaluation"
                  rows="4"
                />
              </div>
            </div>

            {/* Evaluate Button */}
            <div className="form-actions">
              <button 
                className="btn btn-primary" 
                onClick={handleEvaluate}
                disabled={evaluating}
              >
                {evaluating ? "Evaluating..." : "Evaluate Asset"}
              </button>
            </div>
          </div>
          )}

          {/* Evaluation Result Section */}
          {showResult && evaluationResult && (
          <div className="evaluation-result-section">
            <div className="result-header">
              <h2 className="result-title">Evaluation Result</h2>
              <span className="result-badge">LIVE ANALYSIS</span>
            </div>

            <div className="result-grid">
              {/* Compliance Card */}
              <div className="compliance-card">
                <div 
                  className="compliance-badge"
                  style={{
                    background: evaluationResult.status === "Compliant" 
                      ? "linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)"
                      : "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)"
                  }}
                >
                  <span 
                    className="badge-icon"
                    style={{
                      color: evaluationResult.status === "Compliant" ? "#006d73" : "#f87171"
                    }}
                  >
                    {evaluationResult.status === "Compliant" ? "✓" : "✕"}
                  </span>
                </div>
                <h3 
                  className="compliance-status"
                  style={{
                    color: evaluationResult.status === "Compliant" ? "#006d73" : "#dc2626"
                  }}
                >
                  {evaluationResult.status}
                </h3>
                <p className="safety-score">
                  {evaluationResult.loadParameterValue} {evaluationResult.loadParameterMetric}
                </p>
                <p className="result-date">
                  {evaluationResult.matchedCapacityName}
                </p>
              </div>

              {/* Load Safety Margin */}
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">LOAD SAFETY MARGIN</span>
                  <span className="metric-icon">📊</span>
                </div>
                <div className="metric-value">
                  {evaluationResult.status === "Compliant" 
                    ? ((evaluationResult.capacityMaxLoad - evaluationResult.loadParameterValue) / evaluationResult.capacityMaxLoad * 100).toFixed(1)
                    : ((evaluationResult.overloadPercentage * 100).toFixed(1))
                  }%
                </div>
                <p className="metric-subtitle">
                  {evaluationResult.status === "Compliant" 
                    ? "Remaining capacity headroom"
                    : "Overload percentage above limit"
                  }
                </p>
              </div>

              {/* Equipment & Capacity Details Card */}
              <div className="metric-card">
                <div className="metric-header">
                  <span className="metric-label">EVALUATION DETAILS</span>
                  <span className="metric-icon">⚙️</span>
                </div>
                <div style={{ fontSize: "13px", lineHeight: "1.6", color: "#64748b" }}>
                  <div style={{ marginBottom: "8px" }}>
                    <strong>Equipment:</strong> {evaluationResult.equipment}
                  </div>
                  {evaluationResult.equipmentModel && (
                    <div style={{ marginBottom: "8px" }}>
                      <strong>Model:</strong> {evaluationResult.equipmentModel}
                    </div>
                  )}
                  <div style={{ marginBottom: "8px" }}>
                    <strong>Max Capacity:</strong> {evaluationResult.capacityMaxLoad} {evaluationResult.loadParameterMetric}
                  </div>
                  <div style={{ marginBottom: "8px" }}>
                    <strong>Your Load:</strong> {evaluationResult.loadParameterValue} {evaluationResult.loadParameterMetric}
                  </div>
                  {evaluationResult.remark && (
                    <div>
                      <strong>Remark:</strong> {evaluationResult.remark}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Result Footer */}
            <div className="result-footer">
              <div className="result-actions">
                {evaluationResult.status !== "Compliant" && (
                  <button
                    className="btn btn-primary"
                    onClick={handleSendEmail}
                    disabled={sendingEmail}
                    style={{ minWidth: 180 }}
                  >
                    {sendingEmail ? "Sending..." : "Send Email Alert"}
                  </button>
                )}
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowResult(false);
                    setEvaluationResult(null);
                    setEmailMessage(null);
                  }}
                >
                  ← New Evaluation
                </button>
              </div>
              {evaluationResult.emailStatus && (
                <div style={{
                  marginTop: 8,
                  fontSize: 12,
                  color: "#64748b",
                }}>
                  Auto-send status: {evaluationResult.emailStatus}
                  {evaluationResult.emailError && ` — ${evaluationResult.emailError}`}
                </div>
              )}
            </div>
          </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

export default EvaluationPage;
