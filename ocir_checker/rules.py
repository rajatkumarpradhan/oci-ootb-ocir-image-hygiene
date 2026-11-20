"""OCIR001-OCIR004 rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .model import STALE_LATEST_DAYS


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    repo: str
    detail: str


def rule_public_prod_like(repos: tuple, as_of: date) -> list:
    """OCIR001 HIGH: public repo with production-looking tags."""
    del as_of
    out = []
    for r in repos:
        if not r.is_public:
            continue
        hits = [im.tag for im in r.images if im.is_prod_like()]
        if hits:
            out.append(
                Finding("OCIR001", "HIGH", r.name,
                        f"public repository contains production-looking tag(s) {hits}; anonymously pullable - "
                        f"confirm this exposure is intentional")
            )
    return out


def rule_latest_only(repos: tuple, as_of: date) -> list:
    """OCIR002 MEDIUM: repo whose images are tagged only 'latest'."""
    del as_of
    return [
        Finding("OCIR002", "MEDIUM", r.name,
                "all images are tagged only 'latest' with no version/digest tag recorded; "
                "deploys referencing them are not reproducible from this export")
        for r in repos if r.images and all(im.tag == "latest" for im in r.images)
    ]


def rule_empty_repo(repos: tuple, as_of: date) -> list:
    """OCIR003 MEDIUM: repository with zero images."""
    del as_of
    return [
        Finding("OCIR003", "MEDIUM", r.name,
                "repository contains zero images; stale scaffolding or a broken push pipeline, "
                "as far as the export records")
        for r in repos if not r.images
    ]


def rule_stale_latest(repos: tuple, as_of: date) -> list:
    """OCIR004 LOW: 'latest' tag points at an artifact older than STALE_LATEST_DAYS."""
    out = []
    for r in repos:
        for im in r.images:
            if im.tag == "latest" and im.age_days(as_of) > STALE_LATEST_DAYS:
                out.append(
                    Finding("OCIR004", "LOW", r.name,
                            f"'latest' was pushed {im.age_days(as_of)} days ago (> {STALE_LATEST_DAYS}); "
                            f"the floating tag points at a stale artifact as recorded in this export")
                )
    return out


ALL_RULES = (
    rule_public_prod_like,
    rule_latest_only,
    rule_empty_repo,
    rule_stale_latest,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(repos: tuple, as_of: date) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(repos, as_of))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.repo))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
