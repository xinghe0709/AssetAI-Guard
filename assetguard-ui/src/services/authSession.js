let authToken = "";
let unauthorizedHandler = null;

export function setAuthToken(token) {
  authToken = token || "";
}

export function getAuthToken() {
  return authToken;
}

export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = typeof handler === "function" ? handler : null;
}

export function notifyUnauthorized() {
  unauthorizedHandler?.();
}
