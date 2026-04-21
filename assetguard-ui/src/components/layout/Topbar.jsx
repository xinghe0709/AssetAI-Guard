function Topbar({ user }) {
  const userLabel = user?.email || "Unknown User";

  return (
    <header className="topbar">
      <div></div>
      <div className="topbar-user">{userLabel} ▾</div>
    </header>
  );
}

export default Topbar;