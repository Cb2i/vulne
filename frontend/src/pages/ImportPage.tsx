import { ChangeEvent, useEffect, useState } from "react";
import { api, ApiError } from "../services/api";
import type { ImportResult, Scan } from "../types";

export function ImportPage() {
  const [scans, setScans] = useState<Scan[]>([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function loadScans() {
    api.get<Scan[]>("/scans").then(setScans).catch(() => undefined);
  }

  useEffect(loadScans, []);

  async function handleFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await api.postForm<ImportResult>("/scans/import", form);
      setResult(res);
      loadScans();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Échec de l'import");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Import Tenable</div>
          <div className="page-subtitle">// Charger un classeur Excel de vulnérabilités</div>
        </div>
      </div>

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <span className="panel-title">// Nouveau fichier</span>
        </div>
        <div className="panel-body">
          <p className="muted" style={{ fontSize: 12.5, marginBottom: 16 }}>
            Sélectionnez le classeur Excel exporté depuis Tenable (feuille « Vulnérabilités » requise). Le score CAA,
            les délais SLE et l'attribution d'équipe sont recalculés automatiquement pour chaque ligne importée.
          </p>
          <label className="btn btn-primary" style={{ display: "inline-flex", cursor: "pointer" }}>
            {uploading ? "Import en cours…" : "Choisir un fichier .xlsx"}
            <input type="file" accept=".xlsx,.xlsm" onChange={handleFile} disabled={uploading} style={{ display: "none" }} />
          </label>

          {error && <div className="login-error" style={{ marginTop: 16 }}>{error}</div>}

          {result && (
            <div style={{ marginTop: 20 }}>
              <div className="panel-title" style={{ marginBottom: 10 }}>
                Résultat de l'import — {result.scan_name}
              </div>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-value">{result.row_count}</div>
                  <div className="kpi-label">Lignes traitées</div>
                </div>
                <div className="kpi-card low">
                  <div className="kpi-value" style={{ color: "var(--low)" }}>
                    {result.new_findings}
                  </div>
                  <div className="kpi-label">Nouveaux findings</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{result.updated_findings}</div>
                  <div className="kpi-label">Findings mis à jour</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{result.resolved_findings}</div>
                  <div className="kpi-label">Findings remédiés</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{result.imported_exceptions}</div>
                  <div className="kpi-label">Exceptions importées</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-value">{result.imported_ownership_rules}</div>
                  <div className="kpi-label">Règles d'équipe importées</div>
                </div>
              </div>
              {(result.imported_exceptions > 0 || result.imported_ownership_rules > 0) && (
                <p className="muted" style={{ fontSize: 12, marginTop: 10 }}>
                  Ces exceptions et règles sont désormais enregistrées en base : elles s'appliqueront
                  automatiquement à tous les prochains imports, sans avoir besoin de réimporter ce fichier.
                </p>
              )}
              {result.warnings.length > 0 && (
                <div className="login-error" style={{ borderColor: "rgba(250,204,21,.3)", color: "var(--med)" }}>
                  {result.warnings.join(" · ")}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">// Historique des scans</span>
        </div>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Nom du scan</th>
                <th>Fichier source</th>
                <th>Importé le</th>
                <th>Findings</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              {scans.length === 0 && (
                <tr>
                  <td colSpan={5}>
                    <div className="empty-state">Aucun import pour le moment.</div>
                  </td>
                </tr>
              )}
              {scans.map((s) => (
                <tr key={s.id}>
                  <td>{s.name}</td>
                  <td className="muted">{s.source_filename ?? "—"}</td>
                  <td>{new Date(s.imported_at).toLocaleString("fr-CA")}</td>
                  <td>{s.finding_count}</td>
                  <td>
                    <span className={`badge ${s.status === "success" ? "badge-faible" : "badge-critique"}`}>
                      {s.status}
                    </span>
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
