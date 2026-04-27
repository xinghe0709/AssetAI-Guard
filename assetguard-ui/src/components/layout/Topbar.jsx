function Topbar({ user, onLogout }) {
  const fullLabel = user?.name || user?.email || "John Doe";
  const initials = fullLabel
    .split("@")[0]
    .split(/[\s._-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((token) => token[0]?.toUpperCase())
    .join("") || "JD";

  const handleLogout = () => {
    if (typeof onLogout === "function") {
      onLogout();
      return;
    }
    window.location.assign("/login");
  };

  return (
    <header className="topbar">
      <div className="topbar-brand">AssetGuard AI</div>
      <div className="topbar-user-group">
        <div className="topbar-user">{fullLabel}</div>
        <div className="topbar-avatar">{initials}</div>
        <button
          type="button"
          className="topbar-logout"
          aria-label="Log out"
          onClick={handleLogout}
        >
          ↪
        </button>
      </div>
    </header>
  );
}

export default Topbar;
