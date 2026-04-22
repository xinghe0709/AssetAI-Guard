import React, { useState } from "react";
import "../../styles/create-asset-form.css";

const uploadIcon = "http://localhost:3845/assets/19592b2e222112a0ebef7edea88b834685bb0888.svg";
const aiIcon = "http://localhost:3845/assets/41a90af1f048e0b3e88eb6f2ff8c4da2c914e262.svg";

function CreateAssetForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    assetName: "",
    maxLoadCapacity: "0.00",
    unit: "kiloNewtons (kN)",
    organisation: "",
    attachment: null,
  });

  const [dragActive, setDragActive] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setFormData((prev) => ({
        ...prev,
        attachment: file,
      }));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFormData((prev) => ({
        ...prev,
        attachment: file,
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onSubmit) {
      onSubmit(formData);
    }
  };

  return (
    <form className="create-asset-form" onSubmit={handleSubmit}>
      {/* Form Fields Container */}
      <div className="form-fields">
        {/* Asset Name Field */}
        <div className="form-field asset-name-field">
          <label htmlFor="assetName" className="form-label">
            Asset Name
          </label>
          <input
            type="text"
            id="assetName"
            name="assetName"
            placeholder="e.g. Industrial HVAC System 04"
            value={formData.assetName}
            onChange={handleInputChange}
            className="form-input"
          />
        </div>

        {/* Load Capacity and Unit Fields */}
        <div className="form-row">
          <div className="form-field form-field-half">
            <label htmlFor="maxLoadCapacity" className="form-label">
              Maximum Load Capacity
            </label>
            <input
              type="number"
              id="maxLoadCapacity"
              name="maxLoadCapacity"
              placeholder="0.00"
              value={formData.maxLoadCapacity}
              onChange={handleInputChange}
              className="form-input"
              step="0.01"
            />
          </div>

          <div className="form-field form-field-half">
            <label htmlFor="unit" className="form-label">
              Unit
            </label>
            <select
              id="unit"
              name="unit"
              value={formData.unit}
              onChange={handleInputChange}
              className="form-select"
            >
              <option>kiloNewtons (kN)</option>
              <option>Newtons (N)</option>
              <option>Kilogram-force (kgf)</option>
              <option>Pounds-force (lbf)</option>
            </select>
          </div>
        </div>

        {/* Organisation Field */}
        <div className="form-field">
          <label htmlFor="organisation" className="form-label">
            Organisation
          </label>
          <select
            id="organisation"
            name="organisation"
            value={formData.organisation}
            onChange={handleInputChange}
            className="form-select"
          >
            <option value="">Select an organisation...</option>
            <option value="global-energy">Global Energy Corp</option>
            <option value="omnicorp">OmniCorp Industrial</option>
            <option value="skyline">Skyline Logistics</option>
            <option value="biolab">BioLab Systems</option>
            <option value="metalforge">MetalForge Co.</option>
          </select>
        </div>

        {/* Attachment Field */}
        <div className="form-field">
          <label htmlFor="attachment" className="form-label">
            Attachment
          </label>
          <div
            className={`file-upload-area ${dragActive ? "drag-active" : ""}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <img
              src={uploadIcon}
              alt="Upload"
              className="upload-icon"
            />
            <p className="upload-text">
              Drag files here or{" "}
              <button
                type="button"
                className="browse-link"
                onClick={() =>
                  document.getElementById("attachment")?.click()
                }
              >
                browse
              </button>
            </p>
            <p className="upload-hint">
              Support: PDF, JPEG, PNG (Max 10MB)
            </p>
            <input
              type="file"
              id="attachment"
              name="attachment"
              onChange={handleFileSelect}
              className="file-input"
              style={{ display: "none" }}
              accept=".pdf,.jpg,.jpeg,.png"
            />
          </div>
          {formData.attachment && (
            <p className="file-selected">
              📎 {formData.attachment.name}
            </p>
          )}
        </div>

        {/* AI Insight Box */}
        <div className="ai-insight-box">
          <img src={aiIcon} alt="AI" className="ai-icon" />
          <div className="ai-content">
            <div className="ai-label">AI Insight</div>
            <p className="ai-message">
              Complete all metadata fields to ensure high-fidelity predictive maintenance modeling for this asset.
            </p>
          </div>
        </div>
      </div>

      {/* Form Footer */}
      <div className="form-footer">
        <button
          type="button"
          className="btn-cancel"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn-create-asset"
        >
          Create Asset
        </button>
      </div>
    </form>
  );
}

export default CreateAssetForm;
