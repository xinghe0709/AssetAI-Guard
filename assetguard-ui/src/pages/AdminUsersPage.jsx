import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import "../styles/admin-users.css";

function AdminUsersPage({ user, onNavChange }) {
  const [activeNav, setActiveNav] = useState("Admin/User");
  const [currentPage, setCurrentPage] = useState(1);

  // Handle nav changes
  const handleNavChange = (newNav) => {
    if (onNavChange) {
      onNavChange(newNav);
    } else {
      setActiveNav(newNav);
    }
  };

  // Sample users data
  const usersData = [
    {
      id: "#AG-8821",
      name: "Marcus Thorne",
      role: "System Architect",
      organization: "Global Nexus",
      createdTime: "2023-10-12 09:44",
      updateTime: "2024-05-01 14:20",
      status: "ACTIVE",
      statusColor: "#006767",
    },
    {
      id: "#AG-8824",
      name: "Elena Rodriguez",
      role: "Asset Auditor",
      organization: "FinCorp Europe",
      createdTime: "2024-05-18 11:05",
      updateTime: "2024-05-18 11:05",
      status: "NEW",
      statusColor: "#008282",
    },
    {
      id: "#AG-8829",
      name: "Julian Voss",
      role: "Operational Lead",
      organization: "Nexus Dynamics",
      createdTime: "2023-11-20 16:30",
      updateTime: "2024-04-12 08:15",
      status: "ACTIVE",
      statusColor: "#006767",
    },
    {
      id: "#AG-8901",
      name: "Sarah Jenkins",
      role: "Maintenance Tech",
      organization: "Global Nexus",
      createdTime: "2022-09-01 10:00",
      updateTime: "2024-02-14 11:22",
      status: "DISABLED",
      statusColor: "#dc2626",
    },
    {
      id: "#AG-8912",
      name: "Chen Wei",
      role: "Data Analyst",
      organization: "Zenith Analytics",
      createdTime: "2024-01-05 14:50",
      updateTime: "2024-05-20 17:01",
      status: "ACTIVE",
      statusColor: "#006767",
    },
  ];

  const handleAddNewUser = () => {
    console.log("Add new user");
    // TODO: Open modal or navigate to user creation form
  };

  const handleUserAction = (userId) => {
    console.log("Action for user:", userId);
    // TODO: Open context menu or action dialog
  };

  return (
    <AppLayout activeNav={activeNav} onNavChange={handleNavChange} user={user}>
      <div className="admin-users-container">
        {/* Top Breadcrumb */}
        <div className="breadcrumb-section">
          <span className="breadcrumb-text">Admin / User Management</span>
        </div>

        {/* Page Content */}
        <div className="admin-content">
          {/* Header Section */}
          <div className="users-header">
            <h1 className="users-title">Users</h1>
            <button className="btn-add-user" onClick={handleAddNewUser}>
              <span className="btn-icon">+</span>
              <span>Add New User</span>
            </button>
          </div>

          {/* Users Table */}
          <div className="users-table-wrapper">
            <table className="users-table">
              <thead>
                <tr className="table-header-row">
                  <th className="table-header-cell cell-user-id">USER ID</th>
                  <th className="table-header-cell cell-name">NAME</th>
                  <th className="table-header-cell cell-role">ROLE</th>
                  <th className="table-header-cell cell-org">ORGANISATION</th>
                  <th className="table-header-cell cell-created">CREATED TIME</th>
                  <th className="table-header-cell cell-updated">UPDATE TIME</th>
                  <th className="table-header-cell cell-status">STATUS</th>
                  <th className="table-header-cell cell-action"></th>
                </tr>
              </thead>
              <tbody>
                {usersData.map((userRow, idx) => (
                  <tr key={idx} className="table-body-row">
                    <td className="table-cell cell-user-id">
                      <span className="user-id">{userRow.id}</span>
                    </td>
                    <td className="table-cell cell-name">
                      <span className="user-name">{userRow.name}</span>
                    </td>
                    <td className="table-cell cell-role">
                      <span className="user-role">{userRow.role}</span>
                    </td>
                    <td className="table-cell cell-org">
                      <span className="user-org">{userRow.organization}</span>
                    </td>
                    <td className="table-cell cell-created">
                      <span className="user-date">{userRow.createdTime}</span>
                    </td>
                    <td className="table-cell cell-updated">
                      <span className="user-date">{userRow.updateTime}</span>
                    </td>
                    <td className="table-cell cell-status">
                      <div className="status-badge">
                        <span
                          className="status-dot"
                          style={{ backgroundColor: userRow.statusColor }}
                        />
                        <span
                          className="status-text"
                          style={{ color: userRow.statusColor }}
                        >
                          {userRow.status}
                        </span>
                      </div>
                    </td>
                    <td className="table-cell cell-action">
                      <button
                        className="action-button"
                        onClick={() => handleUserAction(userRow.id)}
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
              <span>Showing 1-5 of 124 users</span>
            </div>
            <div className="pagination-controls">
              <button
                className="pagination-btn prev-btn"
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
              >
                ←
              </button>
              <button className="pagination-btn active">1</button>
              <button className="pagination-btn">2</button>
              <button className="pagination-btn">3</button>
              <span className="pagination-ellipsis">...</span>
              <button className="pagination-btn">25</button>
              <button
                className="pagination-btn next-btn"
                onClick={() => setCurrentPage(currentPage + 1)}
              >
                →
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

export default AdminUsersPage;
