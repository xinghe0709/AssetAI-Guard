import { useState } from "react";

function Topbar({ user, onLogout }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const userLabel = user?.email || "Unknown User";

  const handleLogout = () => {
    setIsDropdownOpen(false);
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <header className="topbar">
      <div></div>
      <div 
        className="topbar-user-container"
        onMouseEnter={() => setIsDropdownOpen(true)}
        onMouseLeave={() => setIsDropdownOpen(false)}
      >
      <div className="topbar-user">{userLabel} ▾</div>
        {isDropdownOpen && (
          <div className="topbar-dropdown">
            <button className="topbar-dropdown-item" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Topbar;
