import { useState } from "react";
import AuthLayout from "../components/layout/AuthLayout";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function PasswordSetupPage({ token, onPasswordSetSuccess, onBackToLogin }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSetPassword = async () => {
    setErrorMessage("");

    if (!token) {
      setErrorMessage("Session missing. Please sign in again.");
      return;
    }
    if (!newPassword || !confirmPassword) {
      setErrorMessage("Please fill in both password fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/auth/set-initial-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ newPassword }),
      });
      const payload = await response.json();
      if (!response.ok || !payload?.success) {
        throw new Error(payload?.message || "Failed to set password.");
      }
      onPasswordSetSuccess();
    } catch (error) {
      setErrorMessage(error.message || "Unable to set password.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const leftContent = (
    <div className="setup-left-content">
      <div className="brand">AssetGuard AI</div>

      <div className="setup-copy">
        <p className="eyebrow dark">SECURITY PROTOCOL 01</p>

        <h1>Initialize your secure gateway.</h1>

        <p className="setup-description">
          First-time authentication requires a robust password to anchor your
          account&apos;s cryptographic identity within the AssetGuard network.
        </p>

        <div className="feature-list">
          <div className="feature-item">
            <span className="feature-dot"></span>
            <div>
              <strong>End-to-End Encryption</strong>
              <p>
                Passwords are hashed locally before transmission to ensure
                zero-knowledge architecture.
              </p>
            </div>
          </div>

          <div className="feature-item">
            <span className="feature-dot"></span>
            <div>
              <strong>Multi-Layer Validation</strong>
              <p>
                Real-time entropy analysis checks for common patterns and
                dictionary vulnerabilities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const rightContent = (
    <div className="setup-right-content">
      <div className="password-card">
        <div className="form-group boxed">
          <label>NEW PASSWORD</label>
          <div className="password-box">
            <input
              type="password"
              placeholder="••••••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <span className="eye">◉</span>
          </div>
        </div>

        <div className="form-group boxed">
          <label>CONFIRM PASSWORD</label>
          <div className="password-box">
            <input
              type="password"
              placeholder="••••••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </div>
        </div>

        <div className="requirements-box">
          <p className="requirements-title">REQUIREMENTS</p>

          <ul>
            <li className="active">Minimum 12 characters</li>
            <li>Uppercase & lowercase letters</li>
            <li>Numbers & special symbols</li>
            <li>No personal information</li>
          </ul>
        </div>

        {errorMessage && (
          <p style={{ color: "#f87171", marginTop: "0", marginBottom: "8px" }}>
            {errorMessage}
          </p>
        )}

        <button
          type="button"
          className="primary-btn"
          onClick={handleSetPassword}
          disabled={isSubmitting}
        >
          {isSubmitting ? "Saving..." : "Initialize Secure Access"} <span>→</span>
        </button>
        <button type="button" className="primary-btn" onClick={onBackToLogin}>
          Back to Login
        </button>
      </div>

      <div className="tip-card">
        <div className="tip-title">✧ AI SECURITY TIP</div>
        <p>
          Our GuardNet engine suggests using a unique passphrase of four
          unrelated words for optimal cryptographic strength.
        </p>
      </div>
    </div>
  );

  const footer = (
    <>
      <div>© 2024 ASSETGUARD AI</div>
      <div className="footer-links">
        <span>PRIVACY PROTOCOL</span>
        <span>SUPPORT</span>
      </div>
    </>
  );

  return (
    <AuthLayout
      leftContent={leftContent}
      rightContent={rightContent}
      footer={footer}
    />
  );
}

export default PasswordSetupPage;