"""Remediation grouping engine: consolidates open findings that share the same
plugin/solution across assets so a team can remediate them as a single action."""
from collections import defaultdict
from dataclasses import dataclass, field

from app.models.finding import Finding


@dataclass
class RemediationGroup:
    plugin_name: str
    solution: str | None
    finding_ids: list[int] = field(default_factory=list)
    asset_ids: set[int] = field(default_factory=set)
    team_ids: set[int] = field(default_factory=set)
    max_caa_score: float | None = None


def group_findings_for_remediation(findings: list[Finding]) -> list[RemediationGroup]:
    groups: dict[str, RemediationGroup] = {}
    for f in findings:
        key = f.plugin_name
        group = groups.setdefault(key, RemediationGroup(plugin_name=f.plugin_name, solution=f.solution))
        group.finding_ids.append(f.id)
        group.asset_ids.add(f.asset_id)
        if f.team_id:
            group.team_ids.add(f.team_id)
        if f.caa_score is not None:
            group.max_caa_score = max(group.max_caa_score or 0.0, f.caa_score)
    return sorted(groups.values(), key=lambda g: (g.max_caa_score or 0.0), reverse=True)
