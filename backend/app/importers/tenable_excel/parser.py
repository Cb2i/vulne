"""Parses a Tenable Excel export (as produced by the organization's reporting workbook)
into plain Python rows, using openpyxl to locate the header row (the workbook has a
title/banner in the first rows) and pandas for tabular normalization.

Expected sheets (only 'Vulnérabilités' is required, the others enrich asset context):
  - "Vulnérabilités": one row per finding (plugin x asset).
  - "Analyse des tags des actifs": per-asset Exposition / Criticité / Classification.
  - "Actifs non vus plus 30jrs": last-seen tracking, used to flag stale assets.
  - "Décommissionés": pre-decommissioned hostnames, if present in the workbook.
"""
from dataclasses import dataclass, field
from io import BytesIO

import openpyxl
import pandas as pd

VULN_SHEET_CANDIDATES = ["Vulnérabilités", "Vulnerabilites", "Vulnerabilities"]
ASSET_TAGS_SHEET_CANDIDATES = ["Analyse des tags des actifs"]
STALE_ASSETS_SHEET_CANDIDATES = ["Actifs non vus plus 30jrs"]
DECOMMISSIONED_SHEET_CANDIDATES = ["Décommissionés", "Decommissiones", "Décommissionnés"]

VULN_HEADER_MARKER = "Nom du plugin"
ASSET_HEADER_MARKER = "Nom de l'actif"
DECOMMISSIONED_HEADER_MARKER = "Serveurs décommissionés"

REQUIRED_VULN_COLUMNS = ["Nom du plugin", "Nom d'hôte"]


class TenableImportError(ValueError):
    pass


@dataclass
class ParsedVulnerabilityRow:
    scan_name: str
    plugin_name: str
    cve: str | None
    grade: str | None
    score: float | None
    grade_actif: str | None
    score_actif: float | None
    fqdn: str | None
    hostname: str
    ip_address: str | None
    os: str | None
    protocol: str | None
    port: int | None
    description: str | None
    solution: str | None
    cvss_version: str | None
    cvss: float | None
    exploitable: bool


@dataclass
class ParsedAssetContext:
    hostname: str
    exposition: str | None
    criticite: str | None
    classification: str | None


@dataclass
class ParsedImport:
    vulnerabilities: list[ParsedVulnerabilityRow] = field(default_factory=list)
    asset_context: dict[str, ParsedAssetContext] = field(default_factory=dict)
    decommissioned_hostnames: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _find_sheet(workbook: openpyxl.workbook.Workbook, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in workbook.sheetnames:
            return name
    return None


def _find_header_row_index(workbook, sheet_name: str, marker: str, max_scan_rows: int = 10) -> int:
    ws = workbook[sheet_name]
    for row_idx in range(1, max_scan_rows + 1):
        row_values = [
            str(c.value).strip() if c.value is not None else "" for c in ws[row_idx]
        ]
        if marker in row_values:
            return row_idx
    raise TenableImportError(
        f"Could not locate header row (looking for column '{marker}') in sheet '{sheet_name}'."
    )


def _sheet_to_dataframe(file_bytes: bytes, sheet_name: str, header_row_index: int) -> pd.DataFrame:
    return pd.read_excel(
        BytesIO(file_bytes), sheet_name=sheet_name, header=header_row_index - 1, engine="openpyxl"
    )


def _clean_str(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text or None


def _clean_float(value) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_int(value) -> int | None:
    f = _clean_float(value)
    return int(f) if f is not None else None


def _clean_bool_oui_non(value) -> bool:
    text = _clean_str(value)
    if not text:
        return False
    return text.strip().lower() in ("oui", "yes", "true", "1")


def parse_tenable_workbook(file_bytes: bytes, filename: str = "import.xlsx") -> ParsedImport:
    result = ParsedImport()

    try:
        workbook = openpyxl.load_workbook(BytesIO(file_bytes), read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - surfaced to the API as a 400
        raise TenableImportError(f"Unable to open workbook '{filename}': {exc}") from exc

    vuln_sheet = _find_sheet(workbook, VULN_SHEET_CANDIDATES)
    if vuln_sheet is None:
        raise TenableImportError(
            f"No 'Vulnérabilités' sheet found in '{filename}'. Sheets present: {workbook.sheetnames}"
        )

    header_row = _find_header_row_index(workbook, vuln_sheet, VULN_HEADER_MARKER)
    df = _sheet_to_dataframe(file_bytes, vuln_sheet, header_row)
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_VULN_COLUMNS if c not in df.columns]
    if missing:
        raise TenableImportError(f"Missing required columns in '{vuln_sheet}': {missing}")

    for _, row in df.iterrows():
        hostname = _clean_str(row.get("Nom d'hôte"))
        plugin_name = _clean_str(row.get("Nom du plugin"))
        if not hostname or not plugin_name:
            continue
        result.vulnerabilities.append(
            ParsedVulnerabilityRow(
                scan_name=_clean_str(row.get("Nom du scan")) or "Import sans nom",
                plugin_name=plugin_name,
                cve=_clean_str(row.get("CVE")),
                grade=_clean_str(row.get("Grade")),
                score=_clean_float(row.get("Score")),
                grade_actif=_clean_str(row.get("Grade actif")),
                score_actif=_clean_float(row.get("Score actif")),
                fqdn=_clean_str(row.get("FQDN")),
                hostname=hostname,
                ip_address=_clean_str(row.get("IP")),
                os=_clean_str(row.get("OS")),
                protocol=_clean_str(row.get("Protocole")),
                port=_clean_int(row.get("Port")),
                description=_clean_str(row.get("Description")),
                solution=_clean_str(row.get("Solution")),
                cvss_version=_clean_str(row.get("Version CVSS")),
                cvss=_clean_float(row.get("CVSS")),
                exploitable=_clean_bool_oui_non(row.get("Exploitable")),
            )
        )

    asset_sheet = _find_sheet(workbook, ASSET_TAGS_SHEET_CANDIDATES)
    if asset_sheet:
        try:
            asset_header_row = _find_header_row_index(workbook, asset_sheet, ASSET_HEADER_MARKER)
            asset_df = _sheet_to_dataframe(file_bytes, asset_sheet, asset_header_row)
            asset_df.columns = [str(c).strip() for c in asset_df.columns]
            for _, row in asset_df.iterrows():
                hostname = _clean_str(row.get(ASSET_HEADER_MARKER))
                if not hostname:
                    continue
                result.asset_context[hostname] = ParsedAssetContext(
                    hostname=hostname,
                    exposition=_clean_str(row.get("Exposition")),
                    criticite=_clean_str(row.get("Criticité")),
                    classification=_clean_str(row.get("Classification")),
                )
        except TenableImportError as exc:
            result.warnings.append(str(exc))

    decommissioned_sheet = _find_sheet(workbook, DECOMMISSIONED_SHEET_CANDIDATES)
    if decommissioned_sheet:
        try:
            decom_header_row = _find_header_row_index(
                workbook, decommissioned_sheet, DECOMMISSIONED_HEADER_MARKER
            )
            decom_df = _sheet_to_dataframe(file_bytes, decommissioned_sheet, decom_header_row)
            decom_df.columns = [str(c).strip() for c in decom_df.columns]
            for _, row in decom_df.iterrows():
                hostname = _clean_str(row.get(DECOMMISSIONED_HEADER_MARKER))
                if hostname:
                    result.decommissioned_hostnames.append(hostname)
        except TenableImportError as exc:
            result.warnings.append(str(exc))

    workbook.close()

    if not result.vulnerabilities:
        result.warnings.append("No valid vulnerability rows found after parsing.")

    return result
