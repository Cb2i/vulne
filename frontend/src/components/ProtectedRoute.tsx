import { Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import type { UserRole } from "../types";

export function ProtectedRoute({ children, roles }: { children: React.ReactNode; roles?: UserRole[] }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-state">
        <div className="spinner" />
        Chargement…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (roles && !roles.includes(user.role)) {
    return (
      <div className="empty-state">Accès refusé — cette section nécessite un rôle plus élevé.</div>
    );
  }

  return <>{children}</>;
}
