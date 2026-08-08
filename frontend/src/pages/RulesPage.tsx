import { FormEvent, useEffect, useState } from "react";
import { api } from "../services/api";
import type { CAAConfig, OwnershipRule, SLERule, Team } from "../types";

export function RulesPage() {
  const [caa, setCaa] = useState<CAAConfig | null>(null);
  const [sleRules, setSleRules] = useState<SLERule[]>([]);
  const [ownershipRules, setOwnershipRules] = useState<OwnershipRule[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [savingCaa, setSavingCaa] = useState(false);
  const [newRule, setNewRule] = useState({ team_id: "", hostname_pattern: "", os_pattern: "", priority: 100 });

  function loadAll() {
    api.get<CAAConfig>("/rules/caa").then(setCaa);
    api.get<SLERule[]>("/rules/sle").then(setSleRules);
    api.get<OwnershipRule[]>("/rules/ownership").then(setOwnershipRules);
    api.get<Team[]>("/teams").then(setTeams);
  }
  useEffect(loadAll, []);

  async function saveCaa(e: FormEvent) {
    e.preventDefault();
    if (!caa) return;
    setSavingCaa(true);
    try {
      const updated = await api.patch<CAAConfig>("/rules/caa", caa);
      setCaa(updated);
    } finally {
      setSavingCaa(false);
    }
  }

  function updateCaaField(key: keyof CAAConfig, value: string) {
    if (!caa) return;
    setCaa({ ...caa, [key]: Number(value) });
  }

  async function saveSleRule(rule: SLERule) {
    const updated = await api.patch<SLERule>(`/rules/sle/${rule.id}`, {
      caa_min: rule.caa_min,
      caa_max: rule.caa_max,
      delay_days: rule.delay_days,
    });
    setSleRules((prev) => prev.map((r) => (r.id === rule.id ? updated : r)));
  }

  async function createOwnershipRule(e: FormEvent) {
    e.preventDefault();
    if (!newRule.team_id) return;
    await api.post<OwnershipRule>("/rules/ownership", {
      team_id: Number(newRule.team_id),
      hostname_pattern: newRule.hostname_pattern || null,
      os_pattern: newRule.os_pattern || null,
      priority: newRule.priority,
      active: true,
    });
    setNewRule({ team_id: "", hostname_pattern: "", os_pattern: "", priority: 100 });
    loadAll();
  }

  async function deleteOwnershipRule(id: number) {
    await api.delete(`/rules/ownership/${id}`);
    loadAll();
  }

  async function toggleOwnershipRule(rule: OwnershipRule) {
    const updated = await api.patch<OwnershipRule>(`/rules/ownership/${rule.id}`, { active: !rule.active });
    setOwnershipRules((prev) => prev.map((r) => (r.id === rule.id ? updated : r)));
  }

  const teamName = (id: number) => teams.find((t) => t.id === id)?.name ?? `#${id}`;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="page-title">Règles CAA / SLE / Propriété</div>
          <div className="page-subtitle">// Configuration du moteur de priorisation</div>
        </div>
      </div>

      {caa && (
        <div className="panel" style={{ marginBottom: 20 }}>
          <div className="panel-head">
            <span className="panel-title">// Pondérations du score CAA</span>
          </div>
          <div className="panel-body">
            <p className="muted" style={{ fontSize: 12.5, marginBottom: 16 }}>
              Score CAA = CVSS + poids(exposition) + poids(criticité de l'actif) + poids(exploitabilité), borné entre
              0 et 10. Toute modification recalcule immédiatement tous les findings ouverts.
            </p>
            <form onSubmit={saveCaa} className="form-grid">
              <div className="field">
                <label>Exposition — Internet</label>
                <input type="number" step="0.1" value={caa.weight_exposition_internet} onChange={(e) => updateCaaField("weight_exposition_internet", e.target.value)} />
              </div>
              <div className="field">
                <label>Exposition — DMZ</label>
                <input type="number" step="0.1" value={caa.weight_exposition_dmz} onChange={(e) => updateCaaField("weight_exposition_dmz", e.target.value)} />
              </div>
              <div className="field">
                <label>Exposition — Interne</label>
                <input type="number" step="0.1" value={caa.weight_exposition_internal} onChange={(e) => updateCaaField("weight_exposition_internal", e.target.value)} />
              </div>
              <div className="field">
                <label>Exposition — Air-gapped</label>
                <input type="number" step="0.1" value={caa.weight_exposition_airgapped} onChange={(e) => updateCaaField("weight_exposition_airgapped", e.target.value)} />
              </div>
              <div className="field">
                <label>Criticité — Critique</label>
                <input type="number" step="0.1" value={caa.weight_criticite_critical} onChange={(e) => updateCaaField("weight_criticite_critical", e.target.value)} />
              </div>
              <div className="field">
                <label>Criticité — Haute</label>
                <input type="number" step="0.1" value={caa.weight_criticite_high} onChange={(e) => updateCaaField("weight_criticite_high", e.target.value)} />
              </div>
              <div className="field">
                <label>Criticité — Moyenne</label>
                <input type="number" step="0.1" value={caa.weight_criticite_medium} onChange={(e) => updateCaaField("weight_criticite_medium", e.target.value)} />
              </div>
              <div className="field">
                <label>Criticité — Faible</label>
                <input type="number" step="0.1" value={caa.weight_criticite_low} onChange={(e) => updateCaaField("weight_criticite_low", e.target.value)} />
              </div>
              <div className="field">
                <label>Exploitabilité confirmée</label>
                <input type="number" step="0.1" value={caa.weight_exploitable} onChange={(e) => updateCaaField("weight_exploitable", e.target.value)} />
              </div>
              <div className="field">
                <label>Diviseur de normalisation</label>
                <input type="number" step="0.1" value={caa.normalization_divisor} onChange={(e) => updateCaaField("normalization_divisor", e.target.value)} />
              </div>
              <button className="btn btn-primary" disabled={savingCaa} style={{ gridColumn: "1 / -1", width: 220 }}>
                {savingCaa ? "Enregistrement…" : "Enregistrer & recalculer"}
              </button>
            </form>
          </div>
        </div>
      )}

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="panel-head">
          <span className="panel-title">// Délais SLE par sévérité</span>
        </div>
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Sévérité</th>
                <th>CAA min</th>
                <th>CAA max</th>
                <th>Délai (jours)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sleRules.map((rule) => (
                <tr key={rule.id}>
                  <td>{rule.severity}</td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={rule.caa_min}
                      style={{ width: 90 }}
                      onChange={(e) =>
                        setSleRules((prev) => prev.map((r) => (r.id === rule.id ? { ...r, caa_min: Number(e.target.value) } : r)))
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      step="0.1"
                      value={rule.caa_max}
                      style={{ width: 90 }}
                      onChange={(e) =>
                        setSleRules((prev) => prev.map((r) => (r.id === rule.id ? { ...r, caa_max: Number(e.target.value) } : r)))
                      }
                    />
                  </td>
                  <td>
                    <input
                      type="number"
                      value={rule.delay_days}
                      style={{ width: 90 }}
                      onChange={(e) =>
                        setSleRules((prev) => prev.map((r) => (r.id === rule.id ? { ...r, delay_days: Number(e.target.value) } : r)))
                      }
                    />
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => saveSleRule(rule)}>
                      Enregistrer
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <span className="panel-title">// Règles d'attribution d'équipe</span>
        </div>
        <div className="panel-body">
          <form onSubmit={createOwnershipRule} className="form-grid" style={{ marginBottom: 18 }}>
            <div className="field">
              <label>Équipe</label>
              <select value={newRule.team_id} onChange={(e) => setNewRule({ ...newRule, team_id: e.target.value })} required>
                <option value="">Sélectionner…</option>
                {teams.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Motif hostname (ex: "commence par q2")</label>
              <input
                value={newRule.hostname_pattern}
                onChange={(e) => setNewRule({ ...newRule, hostname_pattern: e.target.value })}
              />
            </div>
            <div className="field">
              <label>Motif OS</label>
              <input value={newRule.os_pattern} onChange={(e) => setNewRule({ ...newRule, os_pattern: e.target.value })} />
            </div>
            <div className="field">
              <label>Priorité (plus petit = prioritaire)</label>
              <input
                type="number"
                value={newRule.priority}
                onChange={(e) => setNewRule({ ...newRule, priority: Number(e.target.value) })}
              />
            </div>
            <button className="btn btn-primary" style={{ gridColumn: "1 / -1", width: 180 }}>
              Ajouter la règle
            </button>
          </form>

          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Priorité</th>
                  <th>Équipe</th>
                  <th>Hostname</th>
                  <th>OS</th>
                  <th>Active</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {ownershipRules.map((r) => (
                  <tr key={r.id}>
                    <td>{r.priority}</td>
                    <td>{teamName(r.team_id)}</td>
                    <td className="muted">{r.hostname_pattern ?? "*"}</td>
                    <td className="muted">{r.os_pattern ?? "*"}</td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => toggleOwnershipRule(r)}>
                        {r.active ? "Oui" : "Non"}
                      </button>
                    </td>
                    <td>
                      <button className="btn btn-danger btn-sm" onClick={() => deleteOwnershipRule(r.id)}>
                        Supprimer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
