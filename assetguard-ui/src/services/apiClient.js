export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok || (payload && payload.success === false)) {
    throw new Error(
      payload?.message || `Request failed with status ${response.status}.`
    );
  }

  return payload?.data ?? payload;
}
