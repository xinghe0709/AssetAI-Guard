const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api/v1";

export async function fetchEmailLogs(token) {
  const response = await fetch(`${API_BASE_URL}/alerts/email-logs`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error("Failed to fetch email logs");
  }
  return response.json();
}

export async function saveEmailPreferences(token, payload) {
  const response = await fetch(`${API_BASE_URL}/alerts/email-preferences`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to save preferences");
  }
  return response.json();
}

export async function saveEmailTemplate(token, payload) {
  const response = await fetch(`${API_BASE_URL}/alerts/email-template`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to save email template");
  }
  return response.json();
}
