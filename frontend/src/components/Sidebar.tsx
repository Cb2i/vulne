import { NavLink } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types";

interface NavItem {
  to: string;
  label: string;
  roles?: UserRole[];
}

interface NavSection {
  label: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    label: "Vue d'ensemble",
    items: [{ to: "/", label: "Tableau de bord" }],
  },
  {
    label: "Vulnérabilités",
    items: [
      { to: "/findings", label: "Findings" },
      { to: "/assets", label: "Actifs" },
      { to: "/remediation", label: "Remédiation" },
      { to: "/import", label: "Import Tenable", roles: ["admin", "analyst"] },
    ],
  },
  {
    label: "Gouvernance",
    items: [
      { to: "/exceptions", label: "Exceptions" },
      { to: "/decommission", label: "Décommissionnés" },
      { to: "/teams", label: "Équipes" },
    ],
  },
  {
    label: "Administration",
    items: [
      { to: "/rules", label: "Règles CAA / SLE", roles: ["admin"] },
      { to: "/users", label: "Utilisateurs", roles: ["admin"] },
    ],
  },
  {
    label: "Rapports",
    items: [{ to: "/exports", label: "Exports Excel", roles: ["admin", "analyst"] }],
  },
];

const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Administrateur",
  analyst: "Analyste sécurité",
  team_manager: "Gestionnaire d'équipe",
  readonly: "Lecture seule",
};

export function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">VA</div>
        <div>
          <div className="sidebar-logo-text">VulnAssist</div>
          <div className="sidebar-logo-sub">Vuln. Management</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) => !item.roles || (user && item.roles.includes(user.role)));
          if (!visibleItems.length) return null;
          return (
            <div key={section.label}>
              <div className="sidebar-section-label">{section.label}</div>
              {visibleItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          );
        })}
      </nav>
      <div className="sidebar-footer">
        {user && (
          <div className="sidebar-user">
            <div className="sidebar-user-name">{user.full_name}</div>
            <div className="sidebar-user-role">{ROLE_LABEL[user.role]}</div>
          </div>
        )}
        <button className="btn btn-secondary btn-sm" style={{ width: "100%" }} onClick={logout}>
          Déconnexion
        </button>
      </div>
    </aside>
  );
}
