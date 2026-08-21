# integrations/

Bounded context for the **API-first integration layer** connecting
case-management platforms, automation, agentic AI, and analytics.

**Status: placeholder — not implemented.** This directory currently contains no
API clients, service contracts, or message schemas, because none has been
built yet.

**Intended scope (future milestone):** the integration/API layer through which
[`dynamics365/`](../dynamics365/), [`salesforce/`](../salesforce/),
[`copilot/`](../copilot/), and [`ai/`](../ai/) exchange case data —
enforcing loose coupling (platforms integrate through contracts, never
directly against each other) and giving [`governance/`](../governance/) a
single place to observe cross-system activity. See
[`docs/architecture.md`](../docs/architecture.md).
