import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SeverityBadge, StatusBadge } from "../components/Badges";
import { api } from "../services/api";
import type { FindingListResponse, FindingStatus, Severity, Team } from "../types";

const STATUS_OPTIONS: { value: FindingStatus | ""; label: string }[] = [
  { value: "", label: "Tous les statuts" },
  { value: "open", label: "Ouvert" },
  { value: "remediated", label: "Remédié" },
  { value: "exception", label: "Exception" },
  { value: "decommissioned", label: "Décommissionné" },
];

const SEVERITY_OPTIONS: { value: Severity | ""; label: string }[] = [
  { value: "", label: "Toutes sévérités" },
  { value: "Critique", label: "Critique" },
  { value: "Haute", label: "Haute" },
  { value: "Moyenne", label: "Moyenne" },
  { value: "Faible", label: "Faible" },
];

export function FindingsPage() {
  const [data, setData] = useState<FindingListResponse | null>(null);
  const [teams, setTeams] = useState<Team[]>([]);
  const [status, setStatus] = useState<FindingStatus | "">("open");
  const [severity, setSeverity] = useState<Severity | "">("");
  const [teamId, setTeamId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get<Team[]>("/teams").then(setTeams).catch(() => undefined);
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .get<FindingListResponse>("/findings", {
        status: status || undefined,
        severity: severity || undefined,
        team_id: teamId || undefined,
        search: search || undefined,
        overdue_only: overdueOnly || undefined,
        page,
        page_size: 25,
      })
      .then(setData)
      .finally(() => setLoading(false));
  }, [status, severity, teamId, search, overdueOnly, page]);

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Findings</div>
          <div className="page-subtitle">// File de priorisation des vulnérabilités</div>
        </div>
        {data && <span className="pill-count">{data.total} résultat(s)</span>}
      </div>

      <div className="toolbar">
        <input
          type="text"
          placeholder="Rechercher plugin / CVE…"
          value={search}
          onChange={(e) => {
            setPage(1);
            setSearch(e.target.value);
          }}
          style={{ maxWidth: 260 }}
        />
        <select
          value={status}
          onChange={(e) => {
            setPage(1);
            setStatus(e.target.value as FindingStatus | "");
          }}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={severity}
          onChange={(e) => {
            setPage(1);
            setSeverity(e.target.value as Severity | "");
          }}
        >
          {SEVERITY_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <select
          value={teamId}
          onChange={(e) => {
            setPage(1);
            setTeamId(e.target.value);
          }}
        >
          <option value="">Toutes les équipes</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <label className="flex-row" style={{ fontSize: 12, color: "var(--text-dim)" }}>
          <input
            type="checkbox"
            style={{ width: "auto" }}
            checked={overdueOnly}
            onChange={(e) => {
              setPage(1);
              setOverdueOnly(e.target.checked);
            }}
          />
          En retard uniquement
        </label>
      </div>

      <div className="panel">
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Actif</th>
                <th>Plugin</th>
                <th>CVE</th>
                <th>CVSS</th>
                <th>CAA</th>
                <th>Sévérité</th>
                <th>Échéance SLE</th>
                <th>Équipe</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={9}>
                    <div className="loading-state">
                      <div className="spinner" /> Chargement…
                    </div>
                  </td>
                </tr>
              )}
              {!loading && data?.items.length === 0 && (
                <tr>
                  <td colSpan={9}>
                    <div className="empty-state">Aucun finding ne correspond aux filtres.</div>
                  </td>
                </tr>
              )}
              {!loading &&
                data?.items.map((f) => {
                  const overdue = f.sle_due_date && new Date(f.sle_due_date) < new Date() && f.status === "open";
                  return (
                    <tr key={f.id}>
                      <td style={{ fontFamily: "var(--mono)" }}>
                        <Link to={`/findings/${f.id}`}>{f.hostname}</Link>
                      </td>
                      <td>{f.plugin_name}</td>
                      <td style={{ fontFamily: "var(--mono)" }}>{f.cve ?? "—"}</td>
                      <td>{f.cvss?.toFixed(1) ?? "—"}</td>
                      <td style={{ fontFamily: "var(--mono)", fontWeight: 700 }}>{f.caa_score?.toFixed(2) ?? "—"}</td>
                      <td>
                        <SeverityBadge severity={f.caa_severity} />
                      </td>
                      <td style={{ color: overdue ? "var(--crit)" : undefined }}>
                        {f.sle_due_date ?? "—"} {overdue && "⚠"}
                      </td>
                      <td>{f.team_name ?? "Non assigné"}</td>
                      <td>
                        <StatusBadge status={f.status} />
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
        <div className="panel-body flex-between" style={{ borderTop: "1px solid var(--border)" }}>
          <span className="muted" style={{ fontSize: 12 }}>
            Page {page} / {totalPages}
          </span>
          <div className="flex-row">
            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Précédent
            </button>
            <button
              className="btn btn-secondary btn-sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Suivant
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
