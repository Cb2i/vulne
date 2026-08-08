import { useState } from "react";
import { downloadFile } from "../services/api";

export function ExportsPage() {
  const [loadingFindings, setLoadingFindings] = useState(false);
  const [loadingKpi, setLoadingKpi] = useState(false);

  async function exportFindings() {
    setLoadingFindings(true);
    try {
      await downloadFile("/exports/findings");
    } finally {
      setLoadingFindings(false);
    }
  }

  async function exportKpi() {
    setLoadingKpi(true);
    try {
      await downloadFile("/exports/kpi");
    } finally {
      setLoadingKpi(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Exports Excel</div>
          <div className="page-subtitle">// Rapports pour diffusion hors application</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// Findings</span>
          </div>
          <div className="panel-body">
            <p className="muted" style={{ fontSize: 12.5, marginBottom: 16 }}>
              Exporte l'ensemble des findings (tous statuts) avec score CAA, sévérité, échéance SLE et équipe
              assignée.
            </p>
            <button className="btn btn-primary" onClick={exportFindings} disabled={loadingFindings}>
              {loadingFindings ? "Génération…" : "Télécharger le classeur"}
            </button>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// KPI exécutifs</span>
          </div>
          <div className="panel-body">
            <p className="muted" style={{ fontSize: 12.5, marginBottom: 16 }}>
              Exporte le résumé des indicateurs clés (conformité SLE, répartition par sévérité et par équipe).
            </p>
            <button className="btn btn-primary" onClick={exportKpi} disabled={loadingKpi}>
              {loadingKpi ? "Génération…" : "Télécharger le classeur"}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
