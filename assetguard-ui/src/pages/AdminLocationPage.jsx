import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import "../styles/admin-location.css";

function AdminLocationPage({ user, onNavChange }) {
  const [activeNav, setActiveNav] = useState("Admin/Location");
  const [currentPage, setCurrentPage] = useState(1);

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };

  // Sample locations data
  const locationsData = [
    {
      id: "NDE-9942",
      location: "North Delta Energy",
      assetManager: "Sarah Mitchell",
      contractor: "Precision Infra Group",
      createdTime: "Oct 12, 2023",
      createdTimeDetailed: "09:42 AM",
      updateTime: "Just Now",
    },
    {
      id: "GLH-2281",
      location: "Global Logistics Hub",
      assetManager: "Marcus Chen",
      contractor: "Sterling Maintenance",
      createdTime: "Sep 28, 2023",
      createdTimeDetailed: "14:15 PM",
      updateTime: "2 days ago",
    },
    {
      id: "UGS-0012",
      location: "Urban Grid Solutions",
      assetManager: "Elena Rodriguez",
      contractor: "GridCare Partners",
      createdTime: "Aug 05, 2023",
      createdTimeDetailed: "08:00 AM",
      updateTime: "Sep 15, 2023",
    },
    {
      id: "SPA-6871",
      location: "Summit Peak Assets",
      assetManager: "David Vance",
      contractor: "In-House",
      createdTime: "Jul 22, 2023",
      createdTimeDetailed: "11:30 AM",
      updateTime: "Oct 01, 2023",
    },
  ];

  const handleAddNewLocation = () => {
    console.log("Add new location");
    // TODO: Open modal or navigate to location creation form
  };

  const handleLocationAction = (locationId) => {
    console.log("Action for location:", locationId);
    // TODO: Open context menu or action dialog
  };

  return (
    <AppLayout activeNav={activeNav} onNavChange={handleNavChange} user={user}>
      <div className="admin-location-container">
        {/* Top Breadcrumb */}
        <div className="breadcrumb-section">
          <span className="breadcrumb-text">Admin / Organisations</span>
        </div>

        {/* Page Content */}
        <div className="admin-content">
          {/* Header Section */}
          <div className="location-header">
            <h1 className="location-title">Locations</h1>
            <button className="btn-add-location" onClick={handleAddNewLocation}>
              <span className="btn-icon">+</span>
              <span>New Location</span>
            </button>
          </div>

          {/* Locations Table */}
          <div className="location-table-wrapper">
            <table className="location-table">
              <thead>
                <tr className="table-header-row">
                  <th className="table-header-cell cell-location">LOCATION</th>
                  <th className="table-header-cell cell-asset-manager">ASSET MANAGER</th>
                  <th className="table-header-cell cell-contractor">CONTRACTOR</th>
                  <th className="table-header-cell cell-created">CREATED TIME</th>
                  <th className="table-header-cell cell-updated">UPDATE TIME</th>
                  <th className="table-header-cell cell-action"></th>
                </tr>
              </thead>
              <tbody>
                {locationsData.map((location, idx) => (
                  <tr key={idx} className="table-body-row">
                    <td className="table-cell cell-location">
                      <div className="location-cell">
                        <div className="location-name">{location.location}</div>
                        <div className="location-id">ID: {location.id}</div>
                      </div>
                    </td>
                    <td className="table-cell cell-asset-manager">
                      <span className="manager-name">{location.assetManager}</span>
                    </td>
                    <td className="table-cell cell-contractor">
                      <span className="contractor-name">{location.contractor}</span>
                    </td>
                    <td className="table-cell cell-created">
                      <div className="created-time">
                        <div className="date">{location.createdTime}</div>
                        <div className="time">{location.createdTimeDetailed}</div>
                      </div>
                    </td>
                    <td className="table-cell cell-updated">
                      <span className="update-time">{location.updateTime}</span>
                    </td>
                    <td className="table-cell cell-action">
                      <button
                        className="action-button"
                        onClick={() => handleLocationAction(location.id)}
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
          <div className="pagination-section">
            <div className="pagination-info">
              <span>Displaying 1-4 of 12 registered organisations.</span>
            </div>
            <div className="pagination-controls">
              <button
                className="pagination-btn prev-btn"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>
              <button
                className="pagination-btn next-btn"
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                Next →
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminLocationPage;
