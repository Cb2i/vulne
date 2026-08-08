import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { RemediationAction, RemediationGroup, Team } from "../types";

export function RemediationPage() {
  const { user } = useAuth();
  const [groups, setGroups] = useState<RemediationGroup[]>([]);
  const [actions, setActions] = useState<RemediationAction[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const canCreate = user?.role === "admin" || user?.role === "analyst";

  function load() {
    api.get<RemediationGroup[]>("/remediation/groups").then(setGroups);
    api.get<RemediationAction[]>("/remediation/actions").then(setActions);
    api.get<Team[]>("/teams").then(setTeams);
  }
  useEffect(load, []);

  async function createAction(group: RemediationGroup) {
    await api.post("/remediation/actions", {
      plugin_name: group.plugin_name,
      finding_ids: group.finding_ids,
    });
    load();
  }

  const teamName = (id: number | null) => teams.find((t) => t.id === id)?.name ?? "Multi-équipes";

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Remédiation groupée</div>
          <div className="page-subtitle">// Regroupement des findings par plugin / solution</div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <span className="panel-title">// Groupes à traiter</span>
        </div>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Plugin</th>
                <th>Actifs affectés</th>
                <th>Findings</th>
                <th>Score CAA max</th>
                <th>Équipe(s)</th>
                {canCreate && <th></th>}
              </tr>
            </thead>
            <tbody>
              {groups.length === 0 && (
                <tr>
                  <td colSpan={6}>
                    <div className="empty-state">Aucun finding ouvert à regrouper.</div>
                  </td>
                </tr>
              )}
              {groups.map((g) => (
                <tr key={g.plugin_name}>
                  <td>{g.plugin_name}</td>
                  <td>{g.asset_count}</td>
                  <td>{g.finding_count}</td>
                  <td style={{ fontFamily: "var(--mono)", fontWeight: 700 }}>{g.max_caa_score?.toFixed(2) ?? "—"}</td>
                  <td>{g.team_ids.length === 1 ? teamName(g.team_ids[0]) : g.team_ids.length === 0 ? "Non assigné" : "Multi-équipes"}</td>
                  {canCreate && (
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => createAction(g)}>
                        Créer l'action
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">// Actions de remédiation créées</span>
        </div>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Titre</th>
                <th>Équipe</th>
                <th>Findings</th>
                <th>Ticket</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {actions.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state">Aucune action créée.</div>
                  </td>
                </tr>
              )}
              {actions.map((a) => (
                <tr key={a.id}>
                  <td>{a.title}</td>
                  <td>{teamName(a.team_id)}</td>
                  <td>{a.finding_count}</td>
                  <td className="muted">{a.ticket_ref ?? "—"}</td>
                  <td>
                    <span className="badge badge-neutral">{a.status}</span>
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
