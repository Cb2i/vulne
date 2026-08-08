export type UserRole = "admin" | "analyst" | "team_manager" | "readonly";

export type Severity = "Critique" | "Haute" | "Moyenne" | "Faible";

export type FindingStatus = "open" | "remediated" | "exception" | "decommissioned";

export type ImportStatus = "success" | "partial" | "failed";

export interface CurrentUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  team_id: number | null;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
  email: string;
}

export interface Team {
  id: number;
  name: string;
  description: string | null;
}

export interface Asset {
  id: number;
  hostname: string;
  fqdn: string | null;
  ip_address: string | null;
  os: string | null;
  exposition: string;
  criticite: string;
  classification: string | null;
  team_id: number | null;
  grade_actif: string | null;
  score_actif: number | null;
  last_seen_at: string | null;
  is_decommissioned: boolean;
}

export interface Finding {
  id: number;
  scan_id: number;
  asset_id: number;
  plugin_name: string;
  cve: string | null;
  grade: string | null;
  score: number | null;
  protocol: string | null;
  port: number | null;
  description: string | null;
  solution: string | null;
  cvss_version: string | null;
  cvss: number | null;
  exploitable: boolean;
  caa_score: number | null;
  caa_severity: Severity | null;
  sle_delay_days: number | null;
  sle_due_date: string | null;
  team_id: number | null;
  status: FindingStatus;
  remediation_comment: string | null;
  ticket_ref: string | null;
  exception_id: number | null;
  first_seen_at: string;
  last_seen_at: string;
  resolved_at: string | null;
  hostname: string | null;
  team_name: string | null;
}

export interface FindingListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Finding[];
}

export interface Scan {
  id: number;
  name: string;
  source_filename: string | null;
  imported_at: string;
  finding_count: number;
  status: ImportStatus;
}

export interface ImportResult {
  scan_id: number;
  scan_name: string;
  row_count: number;
  new_findings: number;
  updated_findings: number;
  resolved_findings: number;
  status: ImportStatus;
  warnings: string[];
}

export interface CAAConfig {
  id: number;
  name: string;
  description: string | null;
  is_active: boolean;
  weight_exposition_internet: number;
  weight_exposition_dmz: number;
  weight_exposition_internal: number;
  weight_exposition_airgapped: number;
  weight_criticite_critical: number;
  weight_criticite_high: number;
  weight_criticite_medium: number;
  weight_criticite_low: number;
  weight_exploitable: number;
  normalization_divisor: number;
}

export interface SLERule {
  id: number;
  severity: Severity;
  caa_min: number;
  caa_max: number;
  delay_days: number;
}

export interface OwnershipRule {
  id: number;
  team_id: number;
  hostname_pattern: string | null;
  os_pattern: string | null;
  priority: number;
  active: boolean;
}

export type ExceptionStatus = "active" | "expired" | "revoked";

export interface ExceptionRecord {
  id: number;
  vulnerability_match: string;
  asset_type: string | null;
  hostname_pattern: string | null;
  granted_by: string;
  granted_at: string;
  expires_at: string | null;
  confluence_link: string | null;
  justification: string | null;
  status: ExceptionStatus;
}

export interface Decommission {
  id: number;
  hostname: string;
  decommissioned_at: string | null;
  reason: string | null;
  asset_id: number | null;
}

export interface RemediationGroup {
  plugin_name: string;
  solution: string | null;
  finding_count: number;
  asset_count: number;
  team_ids: number[];
  max_caa_score: number | null;
  finding_ids: number[];
}

export interface RemediationAction {
  id: number;
  title: string;
  plugin_name: string;
  solution: string | null;
  team_id: number | null;
  ticket_ref: string | null;
  status: string;
  finding_count: number;
  closed_at: string | null;
}

export interface SeverityCount {
  severity: string;
  count: number;
}

export interface TeamCount {
  team_id: number | null;
  team_name: string;
  count: number;
  overdue_count: number;
}

export interface KPISummary {
  total_open_findings: number;
  total_assets: number;
  total_decommissioned_assets: number;
  active_exceptions: number;
  overdue_findings: number;
  sle_compliance_rate: number;
  by_severity: SeverityCount[];
  by_team: TeamCount[];
  remediated_last_30_days: number;
  new_last_30_days: number;
}

export interface AppUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  team_id: number | null;
  is_active: boolean;
}
