import { useMemo, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import StatCard from "../components/dashboard/StatCard";
import SectionHeader from "../components/dashboard/SectionHeader";
import DataTable from "../components/dashboard/DataTable";
import AlertsPage from "./AlertsPage";

const recentEvaluations = [
  ["Main Turbine G7", "Siemens SGT-800", "Compliant", "14:22 PM"],
  ["Hydraulic Lift B4", "Terex HC 110", "Non-Compliant", "12:05 PM"],
  ["Conveyor System Alpha", "Intralox S2400", "Compliant", "09:48 AM"],
];

const assetList = [
  ["North Wing HVAC", "Global Logistics Hub", "450 kN", "Just now"],
  ["Pressure Tank 09", "Arcturus Energy", "2,100 PSI", "2h ago"],
  ["Solar Array Matrix", "GreenPulse Systems", "1.2 MW", "6h ago"],
  ["Data Center Rack A1-12", "CloudHorizon", "32 kW", "Yesterday"],
];

const navDescriptions = {
  Evaluation: "Create and review load evaluations for selected assets.",
  Assets: "Browse and manage registered assets and their load capacities.",
  History: "Review previous evaluation records and outcomes.",
  Alerts: "Monitor warning signals and non-compliance notifications.",
  Admin: "Manage users, roles, and system-level settings.",
};

const roleNavAccess = {
  admin: ["Dashboard", "Evaluation", "Assets", "History", "Alerts", "Admin"],
  manager: ["Dashboard", "Evaluation", "Assets", "History", "Alerts"],
  operator: ["Dashboard", "Evaluation", "Assets", "History", "Alerts"],
  viewer: ["Dashboard", "Assets", "History", "Alerts"],
};

function DashboardPage({ user }) {
  const userRole = String(user?.role || "viewer").toLowerCase();
  const allowedNavItems = useMemo(() => {
    return roleNavAccess[userRole] || roleNavAccess.viewer;
  }, [userRole]);

  const [activeNav, setActiveNav] = useState("Dashboard");

  const safeActiveNav = allowedNavItems.includes(activeNav)
    ? activeNav
    : "Dashboard";

  const handleNavChange = (nextNav) => {
    if (allowedNavItems.includes(nextNav)) {
      setActiveNav(nextNav);
    }
  };

  if (safeActiveNav !== "Dashboard") {
    return (
      <AppLayout
        activeNav={safeActiveNav}
        onNavChange={handleNavChange}
        user={user}
        menuItems={allowedNavItems}
      >
        {safeActiveNav === "Alerts" ? (
          <AlertsPage />
        ) : allowedNavItems.includes(safeActiveNav) ? (
          <section className="module-placeholder">
            <h1>{safeActiveNav}</h1>
            <p>{navDescriptions[safeActiveNav]}</p>
            <p className="muted-note">
              This module is now selectable from the sidebar. Detailed screens can be
              implemented next.
            </p>
          </section>
        ) : (
          <section className="module-placeholder">
            <h1>Access Restricted</h1>
            <p>You do not have permission to view this module.</p>
          </section>
        )}
      </AppLayout>
    );
  }

  return (
    <AppLayout
      activeNav={safeActiveNav}
      onNavChange={handleNavChange}
      user={user}
      menuItems={allowedNavItems}
    >
      <DashboardHeader />

      <section className="stats-grid">
        <StatCard
          label="TOTAL ASSETS"
          value="1,428"
          meta="+12%"
          description="Verified infrastructure components across all regions."
        />
        <StatCard
          label="TOTAL EVALUATIONS"
          value="8,942"
          meta="98.4% Accuracy"
          description="Real-time safety and performance audits completed."
        />
      </section>

      <section className="dashboard-section">
        <SectionHeader title="Recent Evaluations" action="VIEW HISTORY" />
        <DataTable
          columns={["ASSET", "EQUIPMENT", "RESULT", "TIME"]}
          rows={recentEvaluations}
          resultColumnIndex={2}
        />
      </section>

      <section className="dashboard-section">
        <SectionHeader title="Asset List" action="MANAGE ALL" />
        <DataTable
          columns={["ASSET", "ORGANISATION", "MAX LOAD", "UPDATE TIME"]}
          rows={assetList}
        />
      </section>
    </AppLayout>
  );
}

export default DashboardPage;
