const menuItems = [
  "Dashboard",
  "Evaluation",
  "Assets",
  "History",
  "Alerts",
  "Admin",
];

function Sidebar({ activeItem = "Dashboard", onSelectItem }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-title">AssetGuard AI</div>
        <div className="brand-subtitle">ETHEREAL PRECISION</div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item}
            className={`sidebar-link ${item === activeItem ? "active" : ""}`}
            type="button"
            onClick={() => onSelectItem?.(item)}
          >
            {item}
          </button>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;