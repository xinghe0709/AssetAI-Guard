import { useEffect, useState } from "react";
import LoginEmailPage from "./pages/LoginEmailPage";
import PasswordSetupPage from "./pages/PasswordSetupPage";
import DashboardPage from "./pages/DashboardPage";
import {
  setAuthToken,
  setUnauthorizedHandler,
} from "./services/authSession";

function App() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("login");
  const [systemMessage, setSystemMessage] = useState("");

  const handleLogout = (message = "") => {
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

  const handleLoginSuccess = ({ token: nextToken, user: nextUser }) => {
    setToken(nextToken);
    setAuthToken(nextToken);
    setUser(nextUser);
    setSystemMessage("");
    setCurrentPage(nextUser.isFirstLogin ? "password" : "dashboard");
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
      {currentPage === "dashboard" && <DashboardPage user={user} />}
    </>
  );
}

export default App;
