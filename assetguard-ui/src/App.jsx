import { useEffect, useState } from "react";
import LoginEmailPage from "./pages/LoginEmailPage";
import PasswordSetupPage from "./pages/PasswordSetupPage";
import DashboardPage from "./pages/DashboardPage";
import {
  setAuthToken,
  setUnauthorizedHandler,
} from "./services/authSession";

const LAST_LOGIN_EMAIL_KEY = "assetguard:last-login-email";

function App() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("login");
  const [systemMessage, setSystemMessage] = useState("");

  const handleLogout = (message = "") => {
    try {
      localStorage.removeItem(LAST_LOGIN_EMAIL_KEY);
    } catch {
      // Ignore storage failures (e.g. private mode restrictions).
    }
    setToken("");
    setAuthToken("");
    setUser(null);
    setCurrentPage("login");
    setSystemMessage(message);
  };

  useEffect(() => {
    setUnauthorizedHandler(() => {
      handleLogout("Your session has expired. Please sign in again.");
    });

    return () => {
      setUnauthorizedHandler(null);
    };
  }, []);

  const handleLoginSuccess = (loginPayload = {}) => {
    const nextToken = loginPayload?.token || "";
    const nextUser = loginPayload?.user || {};

    if (!nextToken) {
      setSystemMessage("Login response is missing token. Please verify backend response shape.");
      setCurrentPage("login");
      return;
    }

    setToken(nextToken);
    setAuthToken(nextToken);
    setUser(nextUser);
    setSystemMessage("");
    setCurrentPage(nextUser?.isFirstLogin ? "password" : "dashboard");
  };

  const handlePasswordSetSuccess = () => {
    const nextUser = { ...(user || {}), isFirstLogin: false };
    setUser(nextUser);
    setCurrentPage("dashboard");
  };

  return (
    <>
      {currentPage === "login" && (
        <LoginEmailPage
          onLoginSuccess={handleLoginSuccess}
          systemMessage={systemMessage}
        />
      )}
      {currentPage === "password" && (
        <PasswordSetupPage
          token={token}
          onPasswordSetSuccess={handlePasswordSetSuccess}
          onBackToLogin={handleLogout}
        />
      )}
      {currentPage === "dashboard" && (
        <DashboardPage user={user} onLogout={() => handleLogout("")} />
      )}
    </>
  );
}

export default App;