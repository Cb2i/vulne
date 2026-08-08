import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { SeverityBadge } from "../components/Badges";
import { api } from "../services/api";
import type { Finding, Scan } from "../types";

interface ComparisonResult {
  baseline_scan_id: number;
  current_scan_id: number;
  new_finding_ids: number[];
  resolved_finding_ids: number[];
  persisting_finding_ids: number[];
  new_count: number;
  resolved_count: number;
  persisting_count: number;
}

const PREVIEW_LIMIT = 25;

export function ScanComparePage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [baselineId, setBaselineId] = useState("");
  const [currentId, setCurrentId] = useState("");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [newFindings, setNewFindings] = useState<Finding[]>([]);
  const [resolvedFindings, setResolvedFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<Scan[]>("/scans").then((data) => {
      setScans(data);
      if (data.length >= 2) {
        setCurrentId(String(data[0].id));
        setBaselineId(String(data[1].id));
      }
    });
  }, []);

  async function runComparison() {
    if (!baselineId || !currentId) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const comparison = await api.get<ComparisonResult>("/scans/compare", {
        baseline_scan_id: baselineId,
        current_scan_id: currentId,
      });
      setResult(comparison);

      const [newItems, resolvedItems] = await Promise.all([
        Promise.all(
          comparison.new_finding_ids.slice(0, PREVIEW_LIMIT).map((id) => api.get<Finding>(`/findings/${id}`)),
        ),
        Promise.all(
          comparison.resolved_finding_ids.slice(0, PREVIEW_LIMIT).map((id) => api.get<Finding>(`/findings/${id}`)),
        ),
      ]);
      setNewFindings(newItems);
      setResolvedFindings(resolvedItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de la comparaison");
    } finally {
      setLoading(false);
    }
  }

  const scanLabel = (s: Scan) => `${s.name} — ${new Date(s.imported_at).toLocaleString("fr-CA")} (${s.finding_count})`;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Comparaison de scans</div>
          <div className="page-subtitle">// Écarts entre deux imports (nouveaux / remédiés / persistants)</div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <span className="panel-title">// Sélection</span>
        </div>
        <div className="panel-body">
          <div className="form-grid">
            <div className="field">
              <label>Scan de référence (baseline)</label>
              <select value={baselineId} onChange={(e) => setBaselineId(e.target.value)}>
                <option value="">Sélectionner…</option>
                {scans.map((s) => (
                  <option key={s.id} value={s.id}>
                    {scanLabel(s)}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Scan courant</label>
              <select value={currentId} onChange={(e) => setCurrentId(e.target.value)}>
                <option value="">Sélectionner…</option>
                {scans.map((s) => (
                  <option key={s.id} value={s.id}>
                    {scanLabel(s)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button className="btn btn-primary" style={{ width: 200 }} disabled={!baselineId || !currentId || loading} onClick={runComparison}>
            {loading ? "Comparaison…" : "Comparer"}
          </button>
          {error && <div className="login-error" style={{ marginTop: 16 }}>{error}</div>}
        </div>
      </div>

      {result && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card low">
              <div className="kpi-value" style={{ color: "var(--low)" }}>{result.new_count}</div>
              <div className="kpi-label">Nouveaux findings</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{result.resolved_count}</div>
              <div className="kpi-label">Findings remédiés</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{result.persisting_count}</div>
              <div className="kpi-label">Findings persistants</div>
            </div>
          </div>

          <div className="grid-2">
            <div className="panel">
              <div className="panel-head">
                <span className="panel-title">// Nouveaux ({result.new_count})</span>
                {result.new_count > PREVIEW_LIMIT && (
                  <span className="pill-count">Aperçu des {PREVIEW_LIMIT} premiers</span>
                )}
              </div>
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Actif</th>
                      <th>Plugin</th>
                      <th>Sévérité</th>
                    </tr>
                  </thead>
                  <tbody>
                    {newFindings.length === 0 && (
                      <tr>
                        <td colSpan={3}>
                          <div className="empty-state">Aucun nouveau finding.</div>
                        </td>
                      </tr>
                    )}
                    {newFindings.map((f) => (
                      <tr key={f.id}>
                        <td style={{ fontFamily: "var(--mono)" }}>
                          <Link to={`/findings/${f.id}`}>{f.hostname}</Link>
                        </td>
                        <td>{f.plugin_name}</td>
                        <td>
                          <SeverityBadge severity={f.caa_severity} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <span className="panel-title">// Remédiés ({result.resolved_count})</span>
                {result.resolved_count > PREVIEW_LIMIT && (
                  <span className="pill-count">Aperçu des {PREVIEW_LIMIT} premiers</span>
                )}
              </div>
              <div className="data-table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Actif</th>
                      <th>Plugin</th>
                      <th>Sévérité</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resolvedFindings.length === 0 && (
                      <tr>
                        <td colSpan={3}>
                          <div className="empty-state">Aucun finding remédié.</div>
                        </td>
                      </tr>
                    )}
                    {resolvedFindings.map((f) => (
                      <tr key={f.id}>
                        <td style={{ fontFamily: "var(--mono)" }}>
                          <Link to={`/findings/${f.id}`}>{f.hostname}</Link>
                        </td>
                        <td>{f.plugin_name}</td>
                        <td>
                          <SeverityBadge severity={f.caa_severity} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
