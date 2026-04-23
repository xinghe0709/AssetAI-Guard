import { useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import StatCard from "../components/dashboard/StatCard";
import SectionHeader from "../components/dashboard/SectionHeader";
import DataTable from "../components/dashboard/DataTable";
import EvaluationPage from "./EvaluationPage";
import AssetsPage from "./AssetsPage";
import HistoryPage from "./HistoryPage";
import AdminUsersPage from "./AdminUsersPage";
import AdminLocationPage from "./AdminLocationPage";
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

function DashboardPage({ user }) {
  const [activeNav, setActiveNav] = useState("Dashboard");

  if (activeNav === "Evaluation") {
    return <EvaluationPage user={user} onNavChange={setActiveNav} />;
  }

  if (activeNav === "Assets") {
    return <AssetsPage user={user} onNavChange={setActiveNav} />;
  }

  if (activeNav === "History") {
    return <HistoryPage user={user} onNavChange={setActiveNav} />;
  }

  if (activeNav === "Admin/User") {
    return <AdminUsersPage user={user} onNavChange={setActiveNav} />;
  }

  if (activeNav === "Admin/Location") {
    return <AdminLocationPage user={user} onNavChange={setActiveNav} />;
  }

  if (activeNav === "Alerts") {
  return (
    <AppLayout activeNav={activeNav} onNavChange={setActiveNav} user={user}>
      <AlertsPage />
    </AppLayout>
  );
}

  if (activeNav !== "Dashboard") {
    return (
      <AppLayout activeNav={activeNav} onNavChange={setActiveNav} user={user}>
        <section className="module-placeholder">
          <h1>{activeNav}</h1>
          <p>{navDescriptions[activeNav]}</p>
          <p className="muted-note">
            This module is now selectable from the sidebar. Detailed screens can be
            implemented next.
          </p>
        </section>
      </AppLayout>
    );
  }

  return (
    <AppLayout activeNav={activeNav} onNavChange={setActiveNav} user={user}>
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