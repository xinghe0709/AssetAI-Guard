import { useState } from "react";
import LoginEmailPage from "./pages/LoginEmailPage";
import PasswordSetupPage from "./pages/PasswordSetupPage";
import DashboardPage from "./pages/DashboardPage";

function App() {
  const [token, setToken] = useState("");
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState("login");

  const handleLoginSuccess = ({ token: nextToken, user: nextUser }) => {
    setToken(nextToken);
    setUser(nextUser);
    setCurrentPage(nextUser.isFirstLogin ? "password" : "dashboard");
  };

  const handlePasswordSetSuccess = () => {
    const nextUser = { ...(user || {}), isFirstLogin: false };
    setUser(nextUser);
    setCurrentPage("dashboard");
  };

  const handleLogout = () => {
    setToken("");
    setUser(null);
    setCurrentPage("login");
  };

  return (
    <>
      {currentPage === "login" && (
        <LoginEmailPage onLoginSuccess={handleLoginSuccess} />
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