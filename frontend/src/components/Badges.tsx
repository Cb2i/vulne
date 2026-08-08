import type { FindingStatus, Severity } from "../types";

const SEVERITY_CLASS: Record<string, string> = {
  Critique: "badge-critique",
  Haute: "badge-haute",
  Moyenne: "badge-moyenne",
  Faible: "badge-faible",
};

export function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) return <span className="badge badge-neutral">Non évalué</span>;
  return <span className={`badge ${SEVERITY_CLASS[severity] ?? "badge-neutral"}`}>{severity}</span>;
}

const STATUS_LABEL: Record<FindingStatus, string> = {
  open: "Ouvert",
  remediated: "Remédié",
  exception: "Exception",
  decommissioned: "Décommissionné",
};

export function StatusBadge({ status }: { status: FindingStatus }) {
  return <span className={`badge badge-status-${status}`}>{STATUS_LABEL[status]}</span>;
}
