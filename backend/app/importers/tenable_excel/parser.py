"""Parses a Tenable Excel export (as produced by the organization's reporting workbook)
into plain Python rows, using openpyxl to locate the header row (the workbook has a
title/banner in the first rows) and pandas for tabular normalization.

Expected sheets (only 'Vulnérabilités' is required, the others enrich asset context and
persist reusable rules so they don't need to be re-entered by hand in the app):
  - "Vulnérabilités": one row per finding (plugin x asset).
  - "Analyse des tags des actifs": per-asset Exposition / Criticité / Classification.
  - "Actifs non vus plus 30jrs": last-seen tracking, used to flag stale assets.
  - "Décommissionés": pre-decommissioned hostnames, if present in the workbook.
  - "Exceptions": risk-acceptance exceptions, upserted as ExceptionRecord rows so they
    keep applying to every future scan, not just the workbook they were imported from.
  - "KPI": team-ownership rules (Equipes / Champ_nom d'hôtes / Champ_OS), upserted as
    OwnershipRule rows for the same reason.
"""
from dataclasses import dataclass, field
from datetime import date
from io import BytesIO

import openpyxl
import pandas as pd

VULN_SHEET_CANDIDATES = ["Vulnérabilités", "Vulnerabilites", "Vulnerabilities"]
ASSET_TAGS_SHEET_CANDIDATES = ["Analyse des tags des actifs"]
STALE_ASSETS_SHEET_CANDIDATES = ["Actifs non vus plus 30jrs"]
DECOMMISSIONED_SHEET_CANDIDATES = ["Décommissionés", "Decommissiones", "Décommissionnés"]
EXCEPTIONS_SHEET_CANDIDATES = ["Exceptions"]
OWNERSHIP_SHEET_CANDIDATES = ["KPI"]

VULN_HEADER_MARKER = "Nom du plugin"
ASSET_HEADER_MARKER = "Nom de l'actif"
DECOMMISSIONED_HEADER_MARKER = "Serveurs décommissionés"
EXCEPTIONS_HEADER_MARKER = "Vulnérabilité"
OWNERSHIP_HEADER_MARKER = "Equipes"

REQUIRED_VULN_COLUMNS = ["Nom du plugin", "Nom d'hôte"]

_FRENCH_MONTHS = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5,
    "juin": 6, "juillet": 7, "août": 8, "aout": 8, "septembre": 9,
    "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


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
class ParsedExceptionRow:
    vulnerability_match: str
    asset_type: str | None
    hostname_pattern: str | None
    granted_by: str
    granted_at: date
    confluence_link: str | None


@dataclass
class ParsedOwnershipRow:
    team_name: str
    hostname_pattern: str | None
    os_pattern: str | None


@dataclass
class ParsedImport:
    vulnerabilities: list[ParsedVulnerabilityRow] = field(default_factory=list)
    asset_context: dict[str, ParsedAssetContext] = field(default_factory=dict)
    decommissioned_hostnames: list[str] = field(default_factory=list)
    exceptions: list[ParsedExceptionRow] = field(default_factory=list)
    ownership_rules: list[ParsedOwnershipRow] = field(default_factory=list)
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


def _parse_granted(value) -> tuple[date, str]:
    """Parse the "Date et porteur" column, e.g. '27 Janvier 2023 par Eric Mercier'
    into (date(2023, 1, 27), "Eric Mercier"). Falls back to (today, raw text) for any
    format that doesn't match, so a malformed row never blocks the whole import."""
    text = _clean_str(value)
    if not text:
        return date.today(), "Import Excel"

    import re

    match = re.match(r"^\s*(\d{1,2})\s+(\S+)\s+(\d{4})\s+par\s+(.+?)\s*$", text, re.IGNORECASE)
    if match:
        day, month_name, year, name = match.groups()
        month = _FRENCH_MONTHS.get(month_name.strip().lower())
        if month:
            try:
                return date(int(year), month, int(day)), name.strip()
            except ValueError:
                pass
    return date.today(), text


def _parse_exceptions_sheet(workbook, sheet_name: str, result: "ParsedImport") -> None:
    """Reads only the *first* table in the 'Exceptions' sheet (Vulnérabilité / Type d'actif
    / Hostname / Date et porteur / Lien confluence), stopping at the first fully blank row.

    In practice this sheet often contains additional, differently-shaped tables below the
    main one (e.g. a "blanket exception by category" list, or a wildcard decommission
    list) that a real workbook from this organization was found to contain. Auto-importing
    those as literal exceptions/decommissions would be a real, hard-to-reverse mistake --
    silently marking whole categories of findings as excepted, or assets as decommissioned,
    from loosely-structured free text nobody reviewed. So they are left alone and reported
    as a warning instead, for a human to act on deliberately via the app if desired.

    Uses a single forward-only openpyxl row iterator throughout (rather than random cell
    access), since the workbook is opened in read_only mode where only sequential access
    is supported.
    """
    header_row_idx = _find_header_row_index(workbook, sheet_name, EXCEPTIONS_HEADER_MARKER)
    ws = workbook[sheet_name]
    rows = ws.iter_rows(min_row=header_row_idx, values_only=True)

    header_values = next(rows)
    col_index = {str(v).strip(): i for i, v in enumerate(header_values) if v is not None}

    def get(row_values: tuple, name: str) -> str | None:
        idx = col_index.get(name)
        if idx is None or idx >= len(row_values):
            return None
        return _clean_str(row_values[idx])

    trailing_row_num = header_row_idx
    table_ended = False

    for offset, row_values in enumerate(rows, start=1):
        row_num = header_row_idx + offset
        if all(v is None or (isinstance(v, str) and not v.strip()) for v in row_values):
            table_ended = True
            trailing_row_num = row_num
            continue

        if table_ended:
            # First non-blank row after the table's blank-row boundary: report it and stop
            # looking further (there may be several more mini-tables; one warning suffices).
            result.warnings.append(
                f"La feuille '{sheet_name}' contient du contenu supplémentaire à partir de la ligne "
                f"{row_num} qui n'a pas été importé automatiquement (structure différente de la table "
                "principale). Ajoutez-le manuellement via l'application si nécessaire."
            )
            break

        vulnerability_match = get(row_values, "Vulnérabilité")
        if not vulnerability_match:
            continue
        granted_at, granted_by = _parse_granted(row_values[col_index["Date et porteur"]] if "Date et porteur" in col_index and col_index["Date et porteur"] < len(row_values) else None)
        result.exceptions.append(
            ParsedExceptionRow(
                vulnerability_match=vulnerability_match,
                asset_type=get(row_values, "Type d'actif"),
                hostname_pattern=get(row_values, "Hostname"),
                granted_by=granted_by,
                granted_at=granted_at,
                confluence_link=get(row_values, "Lien confluence"),
            )
        )


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

    exceptions_sheet = _find_sheet(workbook, EXCEPTIONS_SHEET_CANDIDATES)
    if exceptions_sheet:
        try:
            _parse_exceptions_sheet(workbook, exceptions_sheet, result)
        except TenableImportError as exc:
            result.warnings.append(str(exc))
    else:
        result.warnings.append(
            f"Aucune feuille « {EXCEPTIONS_SHEET_CANDIDATES[0]} » trouvée dans ce classeur — "
            "aucune exception n'a été importée. Feuilles présentes : "
            f"{', '.join(workbook.sheetnames)}."
        )

    ownership_sheet = _find_sheet(workbook, OWNERSHIP_SHEET_CANDIDATES)
    if ownership_sheet:
        try:
            own_header_row = _find_header_row_index(workbook, ownership_sheet, OWNERSHIP_HEADER_MARKER)
            own_df = _sheet_to_dataframe(file_bytes, ownership_sheet, own_header_row)
            own_df.columns = [str(c).strip() for c in own_df.columns]
            hostname_col = next((c for c in own_df.columns if "nom d'h" in c.lower() or "nom d'hotes" in c.lower()), None)
            os_col = next((c for c in own_df.columns if c.strip().lower() == "champ_os"), None)
            for _, row in own_df.iterrows():
                team_name = _clean_str(row.get("Equipes"))
                if not team_name:
                    continue
                result.ownership_rules.append(
                    ParsedOwnershipRow(
                        team_name=team_name,
                        hostname_pattern=_clean_str(row.get(hostname_col)) if hostname_col else None,
                        os_pattern=_clean_str(row.get(os_col)) if os_col else None,
                    )
                )
        except TenableImportError as exc:
            result.warnings.append(str(exc))
    else:
        result.warnings.append(
            f"Aucune feuille « {OWNERSHIP_SHEET_CANDIDATES[0]} » trouvée dans ce classeur — "
            "aucune règle d'équipe n'a été importée."
        )

    workbook.close()

    if not result.vulnerabilities:
        result.warnings.append("No valid vulnerability rows found after parsing.")

    return result
