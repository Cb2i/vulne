import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../services/api";
import type { KPISummary } from "../types";

const SEVERITY_COLORS: Record<string, string> = {
  Critique: "#f43f5e",
  Haute: "#fb923c",
  Moyenne: "#facc15",
  Faible: "#4ade80",
  "Non évalué": "#64748b",
};

export function DashboardPage() {
  const [summary, setSummary] = useState<KPISummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<KPISummary>("/kpi/summary")
      .then(setSummary)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="empty-state">{error}</div>;
  if (!summary) {
    return (
      <div className="loading-state">
        <div className="spinner" /> Chargement du tableau de bord…
      </div>
    );
  }

  const severityCritOrHigh = summary.by_severity
    .filter((s) => s.severity === "Critique" || s.severity === "Haute")
    .reduce((acc, s) => acc + s.count, 0);

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Tableau de bord</div>
          <div className="page-subtitle">// Vue d'ensemble du risque</div>
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card crit">
          <div className="kpi-value" style={{ color: "var(--crit)" }}>
            {severityCritOrHigh}
          </div>
          <div className="kpi-label">Critique + Haute</div>
        </div>
        <div className="kpi-card high">
          <div className="kpi-value">{summary.total_open_findings}</div>
          <div className="kpi-label">Findings ouverts</div>
        </div>
        <div className="kpi-card med">
          <div className="kpi-value" style={{ color: summary.overdue_findings > 0 ? "var(--crit)" : "var(--low)" }}>
            {summary.overdue_findings}
          </div>
          <div className="kpi-label">En retard (SLE)</div>
        </div>
        <div className="kpi-card low">
          <div className="kpi-value" style={{ color: "var(--low)" }}>
            {summary.sle_compliance_rate}%
          </div>
          <div className="kpi-label">Conformité SLE</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.total_assets}</div>
          <div className="kpi-label">Actifs suivis</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.active_exceptions}</div>
          <div className="kpi-label">Exceptions actives</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.total_decommissioned_assets}</div>
          <div className="kpi-label">Actifs décommissionnés</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{summary.remediated_last_30_days}</div>
          <div className="kpi-label">Remédiés (30j)</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// Répartition par sévérité CAA</span>
          </div>
          <div className="panel-body" style={{ height: 280 }}>
            {summary.by_severity.length === 0 ? (
              <div className="empty-state">Aucune donnée. Importez un scan pour commencer.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={summary.by_severity}
                    dataKey="count"
                    nameKey="severity"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={2}
                  >
                    {summary.by_severity.map((entry) => (
                      <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] ?? "#38bdf8"} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: "#161a24", border: "1px solid #2a3045", fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// Findings ouverts par équipe</span>
          </div>
          <div className="panel-body" style={{ height: 280 }}>
            {summary.by_team.length === 0 ? (
              <div className="empty-state">Aucune donnée par équipe.</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={summary.by_team} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e2433" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" fontSize={11} />
                  <YAxis dataKey="team_name" type="category" stroke="#64748b" fontSize={11} width={120} />
                  <Tooltip contentStyle={{ background: "#161a24", border: "1px solid #2a3045", fontSize: 12 }} />
                  <Bar dataKey="count" fill="#38bdf8" radius={[0, 3, 3, 0]} />
                  <Bar dataKey="overdue_count" fill="#f43f5e" radius={[0, 3, 3, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
