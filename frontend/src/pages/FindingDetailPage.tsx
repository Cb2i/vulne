import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { SeverityBadge, StatusBadge } from "../components/Badges";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { Finding, FindingStatus } from "../types";

export function FindingDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const [finding, setFinding] = useState<Finding | null>(null);
  const [comment, setComment] = useState("");
  const [ticketRef, setTicketRef] = useState("");
  const [saving, setSaving] = useState(false);
  const canEdit = user?.role === "admin" || user?.role === "analyst";

  function load() {
    api.get<Finding>(`/findings/${id}`).then((f) => {
      setFinding(f);
      setComment(f.remediation_comment ?? "");
      setTicketRef(f.ticket_ref ?? "");
    });
  }

  useEffect(load, [id]);

  async function updateStatus(status: FindingStatus) {
    setSaving(true);
    try {
      const updated = await api.patch<Finding>(`/findings/${id}`, { status });
      setFinding(updated);
    } finally {
      setSaving(false);
    }
  }

  async function saveNotes() {
    setSaving(true);
    try {
      const updated = await api.patch<Finding>(`/findings/${id}`, {
        remediation_comment: comment,
        ticket_ref: ticketRef,
      });
      setFinding(updated);
    } finally {
      setSaving(false);
    }
  }

  if (!finding) {
    return (
      <div className="loading-state">
        <div className="spinner" /> Chargement…
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <Link to="/findings" className="muted" style={{ fontSize: 12, fontFamily: "var(--mono)" }}>
            ← Retour aux findings
          </Link>
          <div className="page-title" style={{ marginTop: 6 }}>
            {finding.plugin_name}
          </div>
          <div className="page-subtitle">
            {finding.hostname} {finding.cve ? `· ${finding.cve}` : ""}
          </div>
        </div>
        <div className="chip-row">
          <SeverityBadge severity={finding.caa_severity} />
          <StatusBadge status={finding.status} />
        </div>
      </div>

      <div className="grid-2">
        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// Score</span>
          </div>
          <div className="panel-body">
            <table className="data-table">
              <tbody>
                <tr>
                  <td>CVSS brut</td>
                  <td style={{ fontFamily: "var(--mono)" }}>{finding.cvss?.toFixed(1) ?? "—"}</td>
                </tr>
                <tr>
                  <td>Score CAA ajusté</td>
                  <td style={{ fontFamily: "var(--mono)", fontWeight: 700 }}>
                    {finding.caa_score?.toFixed(2) ?? "—"}
                  </td>
                </tr>
                <tr>
                  <td>Délai SLE</td>
                  <td>{finding.sle_delay_days ? `${finding.sle_delay_days} jours` : "—"}</td>
                </tr>
                <tr>
                  <td>Échéance</td>
                  <td>{finding.sle_due_date ?? "—"}</td>
                </tr>
                <tr>
                  <td>Exploitable</td>
                  <td>{finding.exploitable ? "Oui" : "Non"}</td>
                </tr>
                <tr>
                  <td>Équipe assignée</td>
                  <td>{finding.team_name ?? "Non assignée"}</td>
                </tr>
                <tr>
                  <td>Première détection</td>
                  <td>{new Date(finding.first_seen_at).toLocaleDateString("fr-CA")}</td>
                </tr>
                <tr>
                  <td>Dernière détection</td>
                  <td>{new Date(finding.last_seen_at).toLocaleDateString("fr-CA")}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <span className="panel-title">// Description &amp; solution</span>
          </div>
          <div className="panel-body">
            <p style={{ fontSize: 13, color: "var(--text-dim)", marginBottom: 14, whiteSpace: "pre-wrap" }}>
              {finding.description ?? "Aucune description."}
            </p>
            <div className="panel-title" style={{ marginBottom: 8 }}>
              Solution recommandée
            </div>
            <p style={{ fontSize: 13, color: "var(--text-dim)", whiteSpace: "pre-wrap" }}>
              {finding.solution ?? "Aucune solution fournie."}
            </p>
          </div>
        </div>
      </div>

      {canEdit && (
        <div className="panel" style={{ marginTop: 16 }}>
          <div className="panel-head">
            <span className="panel-title">// Gestion de la remédiation</span>
          </div>
          <div className="panel-body">
            <div className="chip-row" style={{ marginBottom: 16 }}>
              <button className="btn btn-secondary btn-sm" disabled={saving} onClick={() => updateStatus("remediated")}>
                Marquer remédié
              </button>
              <button className="btn btn-secondary btn-sm" disabled={saving} onClick={() => updateStatus("open")}>
                Rouvrir
              </button>
            </div>
            <div className="form-grid">
              <div className="field">
                <label>Référence de ticket</label>
                <input type="text" value={ticketRef} onChange={(e) => setTicketRef(e.target.value)} />
              </div>
              <div className="field">
                <label>Commentaire de remédiation</label>
                <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} />
              </div>
            </div>
            <button className="btn btn-primary" disabled={saving} onClick={saveNotes}>
              Enregistrer
            </button>
          </div>
        </div>
      )}
    </>
  );
}
