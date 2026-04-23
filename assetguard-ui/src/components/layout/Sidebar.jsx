import { useState } from "react";

const menuItems = [
  "Dashboard",
  "Evaluation",
  "Assets",
  "History",
  "Alerts",
];

const adminSubmenu = [
  { label: "User", value: "Admin/User" },
  { label: "Location", value: "Admin/Location" },
];

function Sidebar({ activeItem = "Dashboard", onSelectItem }) {
  const [adminExpanded, setAdminExpanded] = useState(
    activeItem?.startsWith("Admin")
  );

  const handleAdminClick = () => {
    setAdminExpanded(!adminExpanded);
    if (!adminExpanded) {
      // When expanding, select User by default
      onSelectItem?.("Admin/User");
    }
  };

  const handleSubmenuClick = (value) => {
    onSelectItem?.(value);
  };

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

        {/* Admin Menu Item with Submenu */}
        <div className="sidebar-menu-group">
          <button
            className={`sidebar-link ${
              activeItem?.startsWith("Admin") ? "active" : ""
            } ${adminExpanded ? "expanded" : ""}`}
            type="button"
            onClick={handleAdminClick}
          >
            Admin
            <span className="submenu-toggle">
              {adminExpanded ? "▼" : "▶"}
            </span>
          </button>

          {adminExpanded && (
            <div className="sidebar-submenu">
              {adminSubmenu.map((item) => (
                <button
                  key={item.value}
                  className={`sidebar-submenu-link ${
                    activeItem === item.value ? "active" : ""
                  }`}
                  type="button"
                  onClick={() => handleSubmenuClick(item.value)}
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </nav>
    </aside>
  );
}

export default Sidebar;
