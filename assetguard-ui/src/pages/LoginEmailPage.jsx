import { useState } from "react";
import AuthLayout from "../components/layout/AuthLayout";
import buildingImage from "../assets/building.png";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function LoginEmailPage({ onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage("");

    if (!email.trim() || !password) {
      setErrorMessage("Please enter both email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });
      const payload = await response.json();
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.message || "Login failed.");
      }
      onLoginSuccess(payload.data);
    } catch (error) {
      setErrorMessage(error.message || "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const leftContent = (
    <div className="login-hero">
      <div className="brand">AssetGuard AI</div>

      <div className="hero-image-wrapper">
        <img src={buildingImage} alt="Building" className="hero-image" />
      </div>

      <div className="hero-text">
        <h1>Ethereal Precision in Asset Intelligence.</h1>
        <p>
          Advanced engineering oversight for complex infrastructure environments,
          delivered through minimalistic clarity.
        </p>
      </div>

      <div className="hero-tags">
        <span>ENGINEERING EXCELLENCE</span>
        <span>AI DRIVEN INSIGHTS</span>
      </div>
    </div>
  );

  const rightContent = (
    <div className="form-panel">
      <p className="eyebrow">WELCOME BACK</p>
      <h2 className="form-title">Sign in to your dashboard</h2>

      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label>CORPORATE EMAIL</label>
          <input
            type="email"
            placeholder="john.doe@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>SECURE PASSWORD</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {errorMessage && (
          <p style={{ color: "#f87171", marginTop: "-4px", marginBottom: "8px" }}>
            {errorMessage}
          </p>
        )}

        <button type="submit" className="primary-btn" disabled={isSubmitting}>
          {isSubmitting ? "Signing In..." : "Sign In"} <span>→</span>
        </button>
      </form>

      <p className="small-note">
        Authorized personnel only. Access to this system is monitored and logged
        in accordance with corporate security policies.
      </p>

      <div className="status-card">
        <div className="status-title">
          <span className="dot"></span>
          SYSTEM HEALTH
        </div>
        <p>All monitoring nodes are active. Latency is optimized at 12ms.</p>
      </div>
    </div>
  );

  return <AuthLayout leftContent={leftContent} rightContent={rightContent} />;
}

export default LoginEmailPage;