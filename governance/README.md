# governance/

Bounded context for **governance, audit, assurance, and release controls**.

**Status: implemented (Milestone 8) as deterministic reference assurance.**
No live GRC platform, production IAM, SIEM, secrets manager, immutable audit
store, access-review workflow, certification, or production deployment exists.

## Module Map

| Module | Purpose |
|--------|---------|
| `controls.py` | Governance control catalogue with control id, objective, domain, evidence source, owner role, review frequency, attestation requirement, and exception handling. |
| `policies.py` | Lightweight deterministic policy checks for secret hygiene, agent tool governance, integration metadata, synthetic evidence labels, claim discipline, and release evidence source. |
| `audit.py` | Audit evidence model with stable ids, actor/source/correlation/provenance fields, and a simple chained SHA-256 digest. This is tamper-evidence, not legal-grade immutability. |
| `attestations.py` | Reference access-review attestations for privileged service roles, agent tool permissions, integration identities, and approval roles. |
| `release.py` | Release-assurance model combining quality gates, policy findings, controls, attestations, and unresolved critical findings. |
| `evidence.py` | Deterministic evidence generator. Run via `python -m governance.evidence`. |

## Evidence

`python -m governance.evidence` regenerates:

- `data/synthetic/audit_evidence.json`
- `data/synthetic/access_attestations.json`
- `reports/governance_summary.json`
- `reports/release_assurance.json`
- `reports/operational_readiness.md`
- `reports/final_assurance_report.md`

All are synthetic/reference artefacts. The intended release language is
bounded: `reference implementation release-assurance checks passed`.

## Boundary

Governance evaluates and documents controls around the existing platform. It
does not add service-operation business functionality, deploy infrastructure,
issue credentials, certify compliance, or operate live monitoring.
