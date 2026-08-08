import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";
import { api } from "../services/api";
import type { ExceptionRecord } from "../types";

const EMPTY_FORM = {
  vulnerability_match: "",
  asset_type: "",
  hostname_pattern: "",
  granted_by: "",
  granted_at: new Date().toISOString().slice(0, 10),
  expires_at: "",
  confluence_link: "",
  justification: "",
};

export function ExceptionsPage() {
  const { user } = useAuth();
  const [exceptions, setExceptions] = useState<ExceptionRecord[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const isAdmin = user?.role === "admin";

  function load() {
    api.get<ExceptionRecord[]>("/exceptions").then(setExceptions);
  }
  useEffect(load, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    await api.post("/exceptions", {
      ...form,
      asset_type: form.asset_type || null,
      hostname_pattern: form.hostname_pattern || null,
      expires_at: form.expires_at || null,
      confluence_link: form.confluence_link || null,
      justification: form.justification || null,
    });
    setForm(EMPTY_FORM);
    setShowForm(false);
    load();
  }

  async function revoke(id: number) {
    await api.patch(`/exceptions/${id}`, { status: "revoked" });
    load();
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Exceptions</div>
          <div className="page-subtitle">// Acceptations de risque documentées</div>
        </div>
        {isAdmin && (
          <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
            {showForm ? "Annuler" : "+ Nouvelle exception"}
          </button>
        )}
      </div>

      {isAdmin && showForm && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-head">
            <span className="panel-title">// Nouvelle exception</span>
          </div>
          <div className="panel-body">
            <form onSubmit={submit} className="form-grid">
              <div className="field">
                <label>Vulnérabilité (plugin / CVE, ou "contient …")</label>
                <input
                  value={form.vulnerability_match}
                  onChange={(e) => setForm({ ...form, vulnerability_match: e.target.value })}
                  required
                />
              </div>
              <div className="field">
                <label>Type d'actif</label>
                <input value={form.asset_type} onChange={(e) => setForm({ ...form, asset_type: e.target.value })} />
              </div>
              <div className="field">
                <label>Hostname (ou motif)</label>
                <input value={form.hostname_pattern} onChange={(e) => setForm({ ...form, hostname_pattern: e.target.value })} />
              </div>
              <div className="field">
                <label>Porteur / approbateur</label>
                <input value={form.granted_by} onChange={(e) => setForm({ ...form, granted_by: e.target.value })} required />
              </div>
              <div className="field">
                <label>Date d'octroi</label>
                <input type="date" value={form.granted_at} onChange={(e) => setForm({ ...form, granted_at: e.target.value })} required />
              </div>
              <div className="field">
                <label>Date d'expiration</label>
                <input type="date" value={form.expires_at} onChange={(e) => setForm({ ...form, expires_at: e.target.value })} />
              </div>
              <div className="field">
                <label>Lien Confluence</label>
                <input value={form.confluence_link} onChange={(e) => setForm({ ...form, confluence_link: e.target.value })} />
              </div>
              <div className="field">
                <label>Justification</label>
                <textarea value={form.justification} onChange={(e) => setForm({ ...form, justification: e.target.value })} />
              </div>
              <button className="btn btn-primary" style={{ gridColumn: "1 / -1", width: 180 }}>
                Créer l'exception
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
                <th>Vulnérabilité</th>
                <th>Actif / Hostname</th>
                <th>Porteur</th>
                <th>Octroyée le</th>
                <th>Expire le</th>
                <th>Statut</th>
                {isAdmin && <th></th>}
              </tr>
            </thead>
            <tbody>
              {exceptions.length === 0 && (
                <tr>
                  <td colSpan={7}>
                    <div className="empty-state">Aucune exception enregistrée.</div>
                  </td>
                </tr>
              )}
              {exceptions.map((exc) => (
                <tr key={exc.id}>
                  <td>{exc.vulnerability_match}</td>
                  <td className="muted">{exc.hostname_pattern ?? exc.asset_type ?? "*"}</td>
                  <td>{exc.granted_by}</td>
                  <td>{exc.granted_at}</td>
                  <td>{exc.expires_at ?? "—"}</td>
                  <td>
                    <span className={`badge ${exc.status === "active" ? "badge-faible" : "badge-neutral"}`}>
                      {exc.status}
                    </span>
                  </td>
                  {isAdmin && (
                    <td>
                      {exc.status === "active" && (
                        <button className="btn btn-danger btn-sm" onClick={() => revoke(exc.id)}>
                          Révoquer
                        </button>
                      )}
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
