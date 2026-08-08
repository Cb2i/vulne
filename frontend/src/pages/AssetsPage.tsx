import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { Asset, Team } from "../types";

export function AssetsPage() {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const canEdit = user?.role === "admin" || user?.role === "analyst";

  useEffect(() => {
    api.get<Team[]>("/teams").then(setTeams).catch(() => undefined);
  }, []);

  function load() {
    setLoading(true);
    api
      .get<Asset[]>("/assets", { search: search || undefined })
      .then(setAssets)
      .finally(() => setLoading(false));
  }

  useEffect(load, [search]);

  async function assignTeam(assetId: number, teamId: string) {
    const updated = await api.patch<Asset>(`/assets/${assetId}`, { team_id: teamId ? Number(teamId) : null });
    setAssets((prev) => prev.map((a) => (a.id === assetId ? updated : a)));
  }

  const teamName = (id: number | null) => teams.find((t) => t.id === id)?.name ?? "Non assigné";

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Actifs</div>
          <div className="page-subtitle">// Inventaire des actifs scannés</div>
        </div>
        <span className="pill-count">{assets.length} actif(s)</span>
      </div>

      <div className="toolbar">
        <input
          type="text"
          placeholder="Rechercher un hostname…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ maxWidth: 280 }}
        />
      </div>

      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Hostname</th>
                <th>OS</th>
                <th>IP</th>
                <th>Exposition</th>
                <th>Criticité</th>
                <th>Score actif</th>
                <th>Équipe</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7}>
                    <div className="loading-state">
                      <div className="spinner" /> Chargement…
                    </div>
                  </td>
                </tr>
              )}
              {!loading && assets.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">Aucun actif. Importez un scan Tenable pour commencer.</div>
                  </td>
                </tr>
              )}
              {!loading &&
                assets.map((a) => (
                  <tr key={a.id}>
                    <td style={{ fontFamily: "var(--mono)" }}>{a.hostname}</td>
                    <td>{a.os ?? "—"}</td>
                    <td style={{ fontFamily: "var(--mono)" }}>{a.ip_address ?? "—"}</td>
                    <td>{a.exposition}</td>
                    <td>{a.criticite}</td>
                    <td>{a.score_actif ?? "—"}</td>
                    <td>
                      {canEdit ? (
                        <select value={a.team_id ?? ""} onChange={(e) => assignTeam(a.id, e.target.value)}>
                          <option value="">Non assigné</option>
                          {teams.map((t) => (
                            <option key={t.id} value={t.id}>
                              {t.name}
                            </option>
                          ))}
                        </select>
                      ) : (
                        teamName(a.team_id)
                      )}
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
