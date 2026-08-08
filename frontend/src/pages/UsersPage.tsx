import { FormEvent, useEffect, useState } from "react";
import { api } from "../services/api";
import type { AppUser, Team, UserRole } from "../types";

const ROLE_LABEL: Record<UserRole, string> = {
  admin: "Administrateur",
  analyst: "Analyste sécurité",
  team_manager: "Gestionnaire d'équipe",
  readonly: "Lecture seule",
};

const EMPTY_FORM = { email: "", full_name: "", role: "readonly" as UserRole, team_id: "", password: "" };

export function UsersPage() {
  const [users, setUsers] = useState<AppUser[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<AppUser[]>("/users").then(setUsers);
    api.get<Team[]>("/teams").then(setTeams);
  }
  useEffect(load, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    await api.post("/users", {
      email: form.email,
      full_name: form.full_name,
      role: form.role,
      team_id: form.team_id ? Number(form.team_id) : null,
      password: form.password,
    });
    setForm(EMPTY_FORM);
    setShowForm(false);
    load();
  }

  async function toggleActive(u: AppUser) {
    if (u.is_active) {
      await api.delete(`/users/${u.id}`);
    } else {
      await api.patch(`/users/${u.id}`, { is_active: true });
    }
    load();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Utilisateurs</div>
          <div className="page-subtitle">// Comptes et rôles applicatifs</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? "Annuler" : "+ Nouvel utilisateur"}
        </button>
      </div>

      {showForm && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-head">
            <span className="panel-title">// Nouvel utilisateur</span>
          </div>
          <div className="panel-body">
            <form onSubmit={submit} className="form-grid">
              <div className="field">
                <label>Nom complet</label>
                <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
              </div>
              <div className="field">
                <label>E-mail</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
              </div>
              <div className="field">
                <label>Rôle</label>
                <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}>
                  {Object.entries(ROLE_LABEL).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Équipe (si gestionnaire d'équipe)</label>
                <select value={form.team_id} onChange={(e) => setForm({ ...form, team_id: e.target.value })}>
                  <option value="">Aucune</option>
                  {teams.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Mot de passe initial</label>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  minLength={8}
                  required
                />
              </div>
              <button className="btn btn-primary" style={{ gridColumn: "1 / -1", width: 180 }}>
                Créer
              </button>
            </form>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nom</th>
                <th>E-mail</th>
                <th>Rôle</th>
                <th>Équipe</th>
                <th>Statut</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.full_name}</td>
                  <td className="muted">{u.email}</td>
                  <td>{ROLE_LABEL[u.role]}</td>
                  <td>{teams.find((t) => t.id === u.team_id)?.name ?? "—"}</td>
                  <td>
                    <span className={`badge ${u.is_active ? "badge-faible" : "badge-neutral"}`}>
                      {u.is_active ? "Actif" : "Désactivé"}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => toggleActive(u)}>
                      {u.is_active ? "Désactiver" : "Réactiver"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
