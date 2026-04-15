const messageEl = document.getElementById("message");
const summaryCardsEl = document.getElementById("summaryCards");
const equipmentRowsEl = document.getElementById("equipmentRows");
const assetRowsEl = document.getElementById("assetRows");
const historyRowsEl = document.getElementById("historyRows");

let authToken = "";

function renderSummaryCards(data) {
  const cards = [
    { label: "Total evaluations", value: data.totals.evaluations },
    { label: "Compliant", value: data.totals.compliant },
    { label: "Non-Compliant", value: data.totals.nonCompliant },
    { label: "Compliance %", value: `${data.totals.complianceRatePercentage}%` },
    { label: "Avg overload %", value: `${data.overloadStats.averageOverloadPercentage}%` },
    { label: "Max overload %", value: `${data.overloadStats.maxOverloadPercentage}%` },
  ];
  summaryCardsEl.innerHTML = cards
    .map(
      (card) => `<div class="card"><div class="label">${card.label}</div><div class="value">${card.value}</div></div>`,
    )
    .join("");
}

function renderEquipmentRows(rows) {
  equipmentRowsEl.innerHTML = rows
    .map((row) => `<tr><td>${row.equipment}</td><td>${row.evaluationCount}</td></tr>`)
    .join("");
}

function renderAssetRows(rows) {
  assetRowsEl.innerHTML = rows
    .map((row) => `<tr><td>${row.assetName}</td><td>${row.evaluationCount}</td></tr>`)
    .join("");
}

function renderHistoryRows(rows) {
  historyRowsEl.innerHTML = rows
    .map((row) => {
      const statusClass = row.status === "Compliant" ? "status-ok" : "status-bad";
      return `<tr>
        <td>${new Date(row.evaluatedAt).toLocaleString()}</td>
        <td>${row.assetName ?? "-"}</td>
        <td>${row.equipment}</td>
        <td>${row.loadParameterValue} ${row.loadParameterMetric}</td>
        <td class="${statusClass}">${row.status}</td>
        <td>${row.overloadPercentage}%</td>
      </tr>`;
    })
    .join("");
}

async function fetchDashboardSummary() {
  const res = await fetch("/api/v1/evaluations/dashboard-summary?limit=10", {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  const payload = await res.json();
  if (!res.ok || !payload.success) {
    throw new Error(payload.message || "Failed to load dashboard summary");
  }
  return payload.data;
}

async function loginAndLoad() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  if (!email || !password) {
    messageEl.textContent = "Please enter email and password.";
    return;
  }

  messageEl.textContent = "";
  const loginRes = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const loginPayload = await loginRes.json();
  if (!loginRes.ok || !loginPayload.success) {
    messageEl.textContent = loginPayload.message || "Login failed.";
    return;
  }

  authToken = loginPayload.data.token;
  const summary = await fetchDashboardSummary();
  renderSummaryCards(summary);
  renderEquipmentRows(summary.equipmentStats);
  renderAssetRows(summary.topAssets);
  renderHistoryRows(summary.recentEvaluations);
  messageEl.style.color = "#047857";
  messageEl.textContent = "Dashboard loaded.";
}

document.getElementById("loginBtn").addEventListener("click", async () => {
  try {
    await loginAndLoad();
  } catch (error) {
    messageEl.style.color = "#b91c1c";
    messageEl.textContent = error.message || "Unexpected error.";
  }
});
