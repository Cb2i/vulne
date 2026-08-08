import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { Team } from "../types";

export function TeamsPage() {
  const { user } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const isAdmin = user?.role === "admin";

  function load() {
    api.get<Team[]>("/teams").then(setTeams);
  }
  useEffect(load, []);

  async function createTeam(e: FormEvent) {
    e.preventDefault();
    await api.post<Team>("/teams", { name, description: description || null });
    setName("");
    setDescription("");
    load();
  }

  async function removeTeam(id: number) {
    await api.delete(`/teams/${id}`);
    load();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Équipes</div>
          <div className="page-subtitle">// Équipes propriétaires des actifs</div>
        </div>
      </div>

      {isAdmin && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-head">
            <span className="panel-title">// Nouvelle équipe</span>
          </div>
          <div className="panel-body">
            <form onSubmit={createTeam} className="form-grid">
              <div className="field">
                <label>Nom</label>
                <input value={name} onChange={(e) => setName(e.target.value)} required />
              </div>
              <div className="field">
                <label>Description</label>
                <input value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <button className="btn btn-primary" style={{ gridColumn: "1 / -1", width: 180 }}>
                Ajouter
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
                <th>Description</th>
                {isAdmin && <th></th>}
              </tr>
            </thead>
            <tbody>
              {teams.map((t) => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td className="muted">{t.description ?? "—"}</td>
                  {isAdmin && (
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => removeTeam(t.id)}>
                        Supprimer
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
