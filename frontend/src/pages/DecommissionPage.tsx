import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { Decommission } from "../types";

export function DecommissionPage() {
  const { user } = useAuth();
  const [items, setItems] = useState<Decommission[]>([]);
  const [hostname, setHostname] = useState("");
  const [reason, setReason] = useState("");
  const isAdmin = user?.role === "admin";

  function load() {
    api.get<Decommission[]>("/decommission").then(setItems);
  }
  useEffect(load, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    await api.post("/decommission", { hostname, reason: reason || null });
    setHostname("");
    setReason("");
    load();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Actifs décommissionnés</div>
          <div className="page-subtitle">// Retrait des actifs hors périmètre de remédiation</div>
        </div>
      </div>

      {isAdmin && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-head">
            <span className="panel-title">// Décommissionner un actif</span>
          </div>
          <div className="panel-body">
            <form onSubmit={submit} className="form-grid">
              <div className="field">
                <label>Hostname</label>
                <input value={hostname} onChange={(e) => setHostname(e.target.value)} required />
              </div>
              <div className="field">
                <label>Raison</label>
                <input value={reason} onChange={(e) => setReason(e.target.value)} />
              </div>
              <button className="btn btn-primary" style={{ gridColumn: "1 / -1", width: 220 }}>
                Décommissionner
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
                <th>Hostname</th>
                <th>Décommissionné le</th>
                <th>Raison</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan={3}>
                    <div className="empty-state">Aucun actif décommissionné.</div>
                  </td>
                </tr>
              )}
              {items.map((d) => (
                <tr key={d.id}>
                  <td style={{ fontFamily: "var(--mono)" }}>{d.hostname}</td>
                  <td>{d.decommissioned_at ?? "—"}</td>
                  <td className="muted">{d.reason ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
