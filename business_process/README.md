# business_process/

Platform-neutral business process domain. This is the one domain implemented
in Milestone 1.

Defines the synthetic service taxonomy (`ServiceCategory`) and conceptual case
lifecycle (`CaseStage`, `CASE_LIFECYCLE_ORDER`) that every platform bounded
context (Dynamics 365, Salesforce, Power Platform, Copilot Studio, agentic AI)
is expected to implement against, rather than each platform defining its own.

**Scope in this milestone:** types only — enums and a reference ordering. No
workflow engine, no enforced state transitions, no persistence. See
[`docs/roadmap.md`](../docs/roadmap.md) for when lifecycle rules are planned.

See also [`docs/architecture.md`](../docs/architecture.md) for how this domain
relates to the rest of the platform.
