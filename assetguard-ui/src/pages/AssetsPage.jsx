import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import Modal from "../components/modal/Modal";
import CreateAssetForm from "../components/forms/CreateAssetForm";
import "../styles/assets.css";

function AssetsPage({ user, onNavChange }) {
  const [activeNav, setActiveNav] = useState("Assets");
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [isCreateAssetModalOpen, setIsCreateAssetModalOpen] = useState(false);

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };

  // Sample assets data - In production, this would come from the API
  const assetsData = [
    {
      id: 1,
      name: "Titan-X Generator 400",
      organization: "OmniCorp Industrial",
      maxLoad: "12,500 kg",
      updateTime: "24 Oct 2023, 14:32",
      status: "compliant",
    },
    {
      id: 2,
      name: "Atlas Crane v2.1",
      organization: "Skyline Logistics",
      maxLoad: "45,000 kg",
      updateTime: "23 Oct 2023, 09:15",
      status: "compliant",
    },
    {
      id: 3,
      name: "Centrifuge Unit 7",
      organization: "BioLab Systems",
      maxLoad: "250 kg",
      updateTime: "22 Oct 2023, 18:45",
      status: "non-compliant",
    },
    {
      id: 4,
      name: "Hydraulic Press PX-9",
      organization: "MetalForge Co.",
      maxLoad: "8,000 kg",
      updateTime: "21 Oct 2023, 11:20",
      status: "compliant",
    },
    {
      id: 5,
      name: "Conveyor System Alpha",
      organization: "Global Distribution",
      maxLoad: "1,200 kg",
      updateTime: "20 Oct 2023, 16:55",
      status: "compliant",
    },
  ];

  const filteredAssets = assetsData.filter((asset) =>
    asset.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    asset.organization.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleBatchImport = () => {
    console.log("Batch Import clicked");
    // TODO: Implement batch import functionality
  };

  const handleCreateAsset = () => {
    setIsCreateAssetModalOpen(true);
  };

  const handleCreateAssetSubmit = (formData) => {
    console.log("Create Asset - Form Data:", formData);
    // TODO: Send data to backend API
    setIsCreateAssetModalOpen(false);
  };

  const handleCloseCreateAssetModal = () => {
    setIsCreateAssetModalOpen(false);
  };

  const handleAssetAction = (assetId) => {
    console.log("Asset action for:", assetId);
    // TODO: Implement asset actions (edit, delete, view details)
  };

  const getStatusIndicatorColor = (status) => {
    return status === "compliant" ? "#006767" : "#ba1a1a";
  };

  return (
    <AppLayout activeNav={activeNav} onNavChange={handleNavChange} user={user}>
      <div className="assets-container">
        {/* Page Header */}
        <div className="assets-header">
          <div className="header-left">
            <h1 className="header-title">Assets</h1>
            <p className="header-description">
              Manage and monitor your industrial assets with surgical precision
              and AI-driven insights.
            </p>
          </div>
          <div className="header-actions">
            <button className="btn-secondary" onClick={handleBatchImport}>
              <span className="icon">📥</span>
              <span>Batch Import</span>
            </button>
            <button className="btn-primary" onClick={handleCreateAsset}>
              <span className="icon">➕</span>
              <span>Create New Asset</span>
            </button>
          </div>
        </div>

        {/* Search & Filter */}
        <div className="search-filter-area">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder="Filter by asset name or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* Assets Table */}
        <div className="assets-table-container">
          <table className="assets-table">
            <thead>
              <tr className="table-header-row">
                <th className="table-cell table-header-cell">Asset Name</th>
                <th className="table-cell table-header-cell">Organisation</th>
                <th className="table-cell table-header-cell">Max Load Capacity</th>
                <th className="table-cell table-header-cell">Update Time</th>
                <th className="table-cell table-header-cell table-actions-cell">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredAssets.map((asset) => (
                <tr key={asset.id} className="table-body-row">
                  <td className="table-cell table-data-cell">
                    <div className="asset-name-cell">
                      <div
                        className="status-indicator"
                        style={{
                          backgroundColor: getStatusIndicatorColor(asset.status),
                        }}
                      />
                      <span className="asset-name">{asset.name}</span>
                    </div>
                  </td>
                  <td className="table-cell table-data-cell">
                    <span className="organization">{asset.organization}</span>
                  </td>
                  <td className="table-cell table-data-cell">
                    <span className="max-load">{asset.maxLoad}</span>
                  </td>
                  <td className="table-cell table-data-cell">
                    <span className="update-time">{asset.updateTime}</span>
                  </td>
                  <td className="table-cell table-data-cell table-actions-cell">
                    <button
                      className="action-button"
                      onClick={() => handleAssetAction(asset.id)}
                      title="More actions"
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
            <span>Showing {filteredAssets.length} of {assetsData.length} assets</span>
          </div>
          <div className="pagination-controls">
            <button
              className="pagination-button"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              ←
            </button>
            <span className="pagination-number">{currentPage}</span>
            <button
              className="pagination-button"
              onClick={() => setCurrentPage(currentPage + 1)}
            >
              →
            </button>
          </div>
        </div>
      </div>

      {/* Create Asset Modal */}
      <Modal
        isOpen={isCreateAssetModalOpen}
        title="Create New Asset"
        subtitle="Enter the technical specifications to register a new industrial asset to the monitoring matrix."
        onClose={handleCloseCreateAssetModal}
        size="medium"
      >
        <CreateAssetForm
          onSubmit={handleCreateAssetSubmit}
          onCancel={handleCloseCreateAssetModal}
        />
      </Modal>
    </AppLayout>
  );
}

export default AssetsPage;
