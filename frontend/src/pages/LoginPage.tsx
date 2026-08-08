import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { ApiError } from "../services/api";
import { useAuth } from "../hooks/useAuth";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erreur de connexion");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-logo">
          <div className="sidebar-logo-mark" style={{ width: 44, height: 44, fontSize: 15 }}>
            VA
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 800 }}>VulnAssist</div>
            <div className="sidebar-logo-sub">Gestion des vulnérabilités</div>
          </div>
        </div>

        {error && <div className="login-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label>Adresse e-mail</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="prenom.nom@organisation.local"
              required
              autoFocus
            />
          </div>
          <div className="field">
            <label>Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <button className="btn btn-primary" style={{ width: "100%", marginTop: 8 }} disabled={submitting}>
            {submitting ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
