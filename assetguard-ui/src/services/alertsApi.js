import { requestJson } from "./apiClient";

export function getEmailPreferences() {
  return requestJson("/alerts/email-preferences", { method: "GET" });
}

export function updateEmailPreferences(preferences) {
  return requestJson("/alerts/email-preferences", {
    method: "PUT",
    body: JSON.stringify(preferences),
  });
}

export function getEmailTemplate() {
  return requestJson("/alerts/email-template", { method: "GET" });
}

export function updateEmailTemplate(template) {
  return requestJson("/alerts/email-template", {
    method: "PUT",
    body: JSON.stringify(template),
  });
}

export function getEmailLogs() {
  return requestJson("/alerts/email-logs", { method: "GET" }).then((data) =>
    Array.isArray(data?.items) ? data.items : []
  );
}
export function sendTestEmail() {
  return requestJson("/alerts/test-email", { method: "POST" });
}
