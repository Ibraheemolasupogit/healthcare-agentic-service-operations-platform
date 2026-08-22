"""Generate deterministic Milestone 8 governance and release-assurance evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from governance.attestations import build_reference_attestations, validate_attestations
from governance.audit import build_reference_audit_evidence, verify_audit_chain
from governance.controls import CONTROL_CATALOG, validate_control_catalog
from governance.policies import evaluate_policies
from governance.release import build_release_assurance

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data" / "synthetic"
DEFAULT_REPORTS_DIR = REPO_ROOT / "reports"


def build_governance_summary() -> dict[str, Any]:
    """Build a compact governance-control summary."""
    validate_control_catalog()
    attestations = build_reference_attestations()
    validate_attestations(attestations)
    audit_events = build_reference_audit_evidence()
    audit_payload = tuple(event.to_dict() for event in audit_events)
    assert verify_audit_chain(audit_payload)
    policy_findings = evaluate_policies()
    return {
        "generated_from": "governance.evidence (deterministic, synthetic/reference)",
        "control_count": len(CONTROL_CATALOG),
        "controls": [control.to_dict() for control in CONTROL_CATALOG],
        "policy_findings": [finding.to_dict() for finding in policy_findings],
        "attestation_count": len(attestations),
        "audit_event_count": len(audit_events),
        "audit_chain_verified": True,
        "note": (
            "Reference governance evidence only. This is not a live GRC platform, "
            "compliance certification, production audit store, or legal immutability claim."
        ),
    }


def build_operational_readiness_report(release_payload: dict[str, Any]) -> str:
    """Build concise operational-readiness evidence."""
    status = release_payload["status"]
    rows = [
        ("Ownership", "Owner roles defined", "Named owners and RACI"),
        ("Support model", "Reference responsibilities documented", "Service desk/on-call model"),
        ("Logging", "Audit shape and hash chain implemented", "Central logging/SIEM"),
        ("Alerting", "Observability evidence generated", "Live alert rules and rota"),
        ("Retry/dead-letter", "Reference retry/dead-letter model", "Broker runbook"),
        ("Reconciliation", "Synthetic reconciliation report", "Scheduled live job"),
        ("Backup/recovery", "Out of scope for fixtures", "Backup/restore procedures"),
        ("Access review", "Reference attestations generated", "Live access reviews"),
        ("Incident handling", "Exception handling documented", "Incident severity model"),
        ("Change/release", "Quality gates and assurance modelled", "Release workflow"),
        ("Rollback", "No deployment artefact", "Deployment rollback plan"),
        ("Dependency management", "Minimal dependencies checked", "Patch/vulnerability SLAs"),
        ("AI evaluation", "Deterministic AI evidence exists", "Production model monitoring"),
        ("Human approval", "Consequential actions approval-gated", "Live approval audit store"),
        ("Data classification", "Synthetic-only policy documented", "Production data controls"),
    ]
    table = "\n".join(f"| {area} | {reference} | {future} |" for area, reference, future in rows)
    return "\n".join(
        [
            "# Operational Readiness Checklist",
            "",
            "Synthetic/reference readiness evidence only. This is not a production support "
            "commitment or live operational acceptance record.",
            "",
            "| Area | Reference status | Future live requirement |",
            "|---|---|---|",
            table,
            "",
            f"Reference release status: `{status}`.",
            "",
        ]
    )


def build_final_assurance_report(release_payload: dict[str, Any]) -> str:
    """Build final repository-level assurance report."""
    return (
        "# Final Assurance Report\n\n"
        "This report describes the repository/reference implementation only. It does not "
        "claim production deployment, regulatory compliance, real NHS controls, or live "
        "tenant operation.\n\n"
        "## Implemented Control Areas\n\n"
        "- Governance control catalogue\n"
        "- Deterministic policy evaluation\n"
        "- Audit evidence model with chained SHA-256 digests\n"
        "- Access-review/attestation reference model\n"
        "- Agent tool and prompt governance checks\n"
        "- Integration schema/auth/retry/reconciliation governance checks\n"
        "- Release assurance and operational readiness evidence\n\n"
        "## Release Decision\n\n"
        f"- Status: `{release_payload['status']}`\n"
        f"- Decision: {release_payload['decision']}\n"
        f"- Unresolved critical findings: {release_payload['unresolved_critical_findings']}\n\n"
        "## Limitations\n\n"
        "- No live tenant deployment.\n"
        "- No production IAM, SIEM, secrets manager, monitoring backend, "
        "or immutable audit store.\n"
        "- No regulatory certification, security certification, or production support commitment.\n"
        "- Access reviews and attestations are synthetic/reference evidence only.\n"
    )


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_all(
    *, data_dir: Path = DEFAULT_DATA_DIR, reports_dir: Path = DEFAULT_REPORTS_DIR
) -> dict[str, Path]:
    """Generate Milestone 8 assurance evidence."""
    validate_control_catalog()
    attestations = build_reference_attestations()
    validate_attestations(attestations)
    audit_payload = [event.to_dict() for event in build_reference_audit_evidence()]
    if not verify_audit_chain(tuple(audit_payload)):
        raise ValueError("audit evidence hash chain failed verification")
    policy_findings = evaluate_policies()
    release = build_release_assurance(
        controls=CONTROL_CATALOG,
        attestations=attestations,
        policy_findings=policy_findings,
    )
    release_payload = release.to_dict()
    governance_summary = build_governance_summary()

    outputs: dict[Path, Any] = {
        data_dir / "audit_evidence.json": audit_payload,
        data_dir / "access_attestations.json": [item.to_dict() for item in attestations],
        reports_dir / "governance_summary.json": governance_summary,
        reports_dir / "release_assurance.json": release_payload,
    }
    for path, payload in outputs.items():
        _write_json(path, payload)

    operational = reports_dir / "operational_readiness.md"
    operational.write_text(build_operational_readiness_report(release_payload), encoding="utf-8")
    final = reports_dir / "final_assurance_report.md"
    final.write_text(build_final_assurance_report(release_payload), encoding="utf-8")
    outputs[operational] = release_payload
    outputs[final] = release_payload
    return {path.name: path for path in outputs}


if __name__ == "__main__":  # pragma: no cover
    for name, path in generate_all().items():
        print(f"wrote {name} -> {path}")


__all__ = [
    "build_final_assurance_report",
    "build_governance_summary",
    "build_operational_readiness_report",
    "generate_all",
]
