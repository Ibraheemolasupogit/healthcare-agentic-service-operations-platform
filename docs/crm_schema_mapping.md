# CRM Schema Mapping: Canonical → Dynamics 365 & Salesforce

Reference documentation for the Milestone 3 adapters in
[`dynamics365/`](../dynamics365/) and [`salesforce/`](../salesforce/). It
expands on the boundary described in
[`docs/business_process.md`](business_process.md) §7
("Canonical Domain → Future Platform Adapters").

**Scope reminder:** every mapping below is a reference/illustrative
representation implemented as plain Python — no SDK, no live tenant, no
credentials, no fabricated API responses. See the
[portfolio scope statement](../README.md#portfolio-scope).

## Why a common canonical model is useful

Dynamics 365 and Salesforce model service cases with genuinely different
shapes — a two-tier `state`/`status` split vs. a flat `Status` picklist, a
`queueitem` join vs. a native `Group`-owned `Case`, `incidentresolution`
entities vs. flat resolution fields, `slakpiinstance` vs. `CaseMilestone`.
If lifecycle, priority, SLA, routing, or escalation rules were defined
inside each CRM, the *same* case could behave differently depending on
which platform happened to touch it last, and replacing a CRM would mean
rewriting business rules, not just swapping a UI. Keeping those rules in
[`business_process/`](../business_process/) and treating both CRMs as
adapters means:

- one place to test lifecycle/SLA/escalation/routing correctness;
- both platforms can be run side by side (or one swapped for the other, or
  for a future third platform) without touching business logic;
- audit/governance has one canonical event stream to review, not two
  platform-specific ones that could disagree.

## How to read the tables

- **Required/Optional** describes the *canonical* field's requirement,
  mirrored to whether the adapter's output field can be `None`.
- **Lossy?** — "No" means the value round-trips through the adapter and
  back losslessly for any value the canonical model can produce today; "Yes"
  means information can be lost or a reverse mapping is ambiguous/unsupported.
- Python attribute names are snake_case (idiomatic); the real platform API
  field name is called out separately.

## Identity

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `Case.case_id` | `ticketnumber` (human-readable case number) | `Canonical_Case_Id__c` (custom **external ID** field) | Required | Copied verbatim | No | This is the identity used for idempotent upserts — see "Idempotency and external IDs" below. **Not** the same as the platform's own primary key. |
| *(adapter-generated)* | `incidentid` (GUID primary key) | `Id` (18-char record id) | — | Deterministic `uuid5`/`sha256` hash of `case_id` | N/A | Synthetic, reference-only ids — not a real Dataverse GUID or Salesforce base62 id algorithm. Never used as the upsert key (see below). |
| — | — | `CaseNumber` (native auto-number field) | — | Deterministic synthetic 8-digit number derived from `case_id` | N/A | Real Salesforce auto-assigns this sequentially on insert; this reference adapter cannot replicate that, so it synthesizes an illustrative value instead. |

## Priority

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `Case.priority` (`Priority`: Low/Medium/High/Critical) | `prioritycode` (reference 4-value option set: 1=Critical,2=High,3=Normal,4=Low) | `Priority` (reference 4-value picklist: Critical/High/Medium/Low) | Required | 1:1 dict lookup (`PRIORITY_TO_DYNAMICS` / `PRIORITY_TO_SALESFORCE`) | No | **Both platforms ship only 3 priority levels out of the box** (no native "Critical"). This reference mapping assumes a 4-value option set/picklist — a common real-world customization — specifically to avoid collapsing two canonical priorities onto one native value. A real environment without that customization would need it added, or would need a documented, lossy 4→3 collapse instead. |

## Lifecycle / Status

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `Case.stage` (`CaseStage`, 8 values) | `statecode` (native, fixed: Active/Resolved/Cancelled) + `statuscode` (reference status-reason labels) | `Status` (reference 8-value flat picklist) | Required | `STAGE_TO_DYNAMICS_STATUS` / `STAGE_TO_SALESFORCE_STATUS` dict lookups | **Yes for Dynamics, No for Salesforce** | Dataverse's two-tier model has **no native distinction between "resolved" and "closed"** — resolving an incident *is* closing it (`statecode=Resolved`). Both canonical `RESOLVED` and `CLOSED` therefore map forward to the same Dynamics state, and the reverse mapping deliberately, always resolves `(Resolved, Problem Solved)` back to canonical `RESOLVED` — never `CLOSED` — because further progression to `CLOSED` cannot be inferred from Dynamics state alone. Salesforce's single flat `Status` picklist has no such constraint: all 8 canonical stages map to 8 distinct values, round-tripping losslessly. |
| — | `statecode=Cancelled` | — | — | No canonical equivalent | — | Dynamics' native "Cancelled" state has no canonical `CaseStage`. `stage_from_dynamics()` raises `UnsupportedDynamicsValueError` for it rather than guessing — extending the canonical lifecycle with a cancellation concept is a decision for `business_process`, not either adapter. |
| — | — | `IsClosed` (native boolean) | — | `status == SalesforceStatus.CLOSED` | No | Mirrors Salesforce's real behaviour: `IsClosed` is derived from whether the current `Status` picklist value is flagged "closed" in its metadata, not stored independently. |

## Queue / Ownership

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `Case.queue` (`Queue`, 6 values) | `queue_name` (adapter field; real Dataverse tracks this via a separate `queueitem` record) | `Queue.queue_name` / Queue `Group.DeveloperName` | Optional (`None` until routed) | 1:1 dict lookup (`QUEUE_TO_DYNAMICS_NAME` / `QUEUE_TO_SALESFORCE_NAME`) | No | Real Dataverse queue membership is a `queueitem` join, not a field on `incident` — this reference adapter simplifies it to a display-name field. Salesforce natively supports queue-owned records via a polymorphic `OwnerId` pointing at a `Group` of type Queue, which is a closer structural fit. |
| `Case.owner` (team identifier string) | `owning_team` (adapter field; real Dataverse `ownerid` is a polymorphic `systemuser`/`team` lookup) | `OwnerId` (adapter-synthesized id representing the queue's `Group` record) | Optional (`None` until routed) | Copied verbatim (Dynamics) / hashed from queue (Salesforce) | No (Dynamics) / N/A (Salesforce, synthetic id) | Canonical ownership is always a team, never a named individual (see [`business_process/queues.py`](../business_process/queues.py)) — neither adapter introduces person-level ownership. |

## SLA metadata

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `SLAStatus.response_due_at` | `responsebyapplicable` (native SLA due-date field) | `CaseMilestone` (`milestone_type="First Response"`).`target_date` | Optional (`None` if not yet computed) | Passed straight through by the caller — see "no adapter computes SLA" below | No | Real Dynamics ties this to `slakpiinstance` records driven by an assigned `sla`/entitlement; real Salesforce computes it via Entitlement Management. Neither is reproduced — the adapter just carries the value business_process already computed. |
| `SLAStatus.resolution_due_at` | `resolvebyapplicable` | `CaseMilestone` (`milestone_type="Resolution"`).`target_date` | Optional | Same as above | No | Same caveat as above. |
| `SLAStatus.response_breached` | `sla_response_breached` (**adapter-only** field — not a native Dataverse field) | `CaseMilestone.is_violated` (mirrors Salesforce's real `IsViolated` field) | Optional | Passed straight through | No | Dynamics' real breach status lives on `slakpiinstance.status`, a separate entity/subsystem this adapter does not model — hence the adapter-only annotation. Salesforce's `CaseMilestone.IsViolated` is a real, native field, so this one is a closer structural match. |
| `SLAStatus.resolution_breached` | `sla_resolution_breached` (adapter-only) | `CaseMilestone.is_violated` (`milestone_type="Resolution"`) | Optional | Passed straight through | No | Same as above. |
| — | — | `Entitlement.entitlement_name` (adapter field) | — | Synthesized as `f"{category} {priority} Entitlement"` | N/A | Illustrative label only — not a decision, just a readable reference to "which entitlement process would apply" in a real org. |

**No adapter computes SLA due dates or breach state.** `to_dynamics_incident()`
and `to_salesforce_case()` accept them as plain optional keyword arguments;
the caller (in the Milestone 3 evidence generator,
[`integrations/examples.py`](../integrations/examples.py))
gets them from `business_process.sla.evaluate_sla()` first. See "Critical
architecture rule" in the root README and `tests/test_adapter_boundary.py`.

## CaseEvent / Audit timeline

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `CaseEvent` (one per audit entry) | `DynamicsTimelineEntry` — a generic `annotation`-style record | `SalesforceFeedItem` — a generic Chatter `FeedItem` (`Type="TextPost"`) | N/A (list, can be empty) | One adapter record per `CaseEvent`, in order | Yes (representation, not content) | **Neither platform has one native "generic audit event" entity.** Dataverse's real Case Timeline aggregates `annotation` notes plus `task`/`phonecall`/`email` activities; Salesforce's real case timeline aggregates `CaseComment`, `FeedItem`/`FeedComment`, and activities. Both adapters collapse every `CaseEvent` onto a single representative shape for simplicity — a real integration would likely need to choose a more specific native type per event, which this reference adapter does not attempt. |
| `CaseEvent.detail` | `notetext` | `body` | Required | Copied verbatim | No | — |
| `CaseEvent.actor` | `createdby` (adapter field; real Dataverse `createdby` is a `systemuser` lookup) | `created_by` (adapter field; real Salesforce `CreatedById` is a `User` lookup) | Required | Copied verbatim | No | Canonical actors are role/team strings, never named individuals — see [`docs/business_process.md`](business_process.md) §6. |

## Resolution

| Canonical field | Dynamics 365 / Dataverse | Salesforce | Required? | Conversion rule | Lossy? | Caveats |
|---|---|---|---|---|---|---|
| `Case.resolution` (`ResolutionOutcome`) | `incidentresolution.subject` | `Resolution_Code__c` (adapter/custom field) | Optional (`None` until resolved) | `.value` copied verbatim | No | Real Dynamics creates a distinct `incidentresolution` entity via the "Resolve Case" action/SDK message (`CloseIncidentRequest`), which this adapter does not call — it only produces the reference shape. Salesforce has no equivalent native sub-entity; resolution is conventionally flattened onto the `Case` record via custom fields, which is what this adapter mirrors. |
| `Case.resolution_notes` | `incidentresolution.description` | `Resolution_Notes__c` | Optional | Copied verbatim (`""` if `None` on Dynamics; `None` preserved on Salesforce) | No | — |
| — | — | `ClosedDate` (native field) | — | `case.updated_at` when `stage == CLOSED`, else `None` | No | Reflects the timestamp of the case's `CLOSED` transition specifically — not necessarily when it was first `RESOLVED`. |

## Where CRM-specific extension fields belong

Nothing above should ever grow a field that encodes a *new* business
decision (e.g. a Dynamics-only "risk score" that changes routing, or a
Salesforce-only field that changes SLA maths). Extension fields that are
genuinely platform-specific — a Dynamics `msdyn_`-prefixed customization, a
Salesforce custom field with no canonical equivalent — belong:

- as **additional, clearly-optional fields** on the adapter's own model
  (`dynamics365/models.py` / `salesforce/models.py`), never by adding a
  platform-shaped field to `business_process/models.py`;
- documented in this file if they represent a mapping of an existing
  canonical concept, or simply left as adapter-only fields if they don't;
- never read by `business_process` — the canonical domain must stay
  ignorant of both CRMs, or the "adapters, not redefinitions" boundary
  breaks down.

## Idempotency and external IDs

`Case.case_id` (e.g. `"SR-DS-1001"`) is the one identity that must stay
stable across every system. The pattern Milestone 3 reference adapters
are built for:

- **Dynamics 365**: use `ticketnumber` (not `incidentid`) as the external
  key. A real connector would look up-or-create by `ticketnumber`, since
  `incidentid` is assigned by Dataverse itself and cannot be chosen by the
  caller in the way a designated external-id field can.
- **Salesforce**: use the custom `Canonical_Case_Id__c` field (not `Id`),
  marked **External ID + Unique** in a real org. This is the standard
  Salesforce pattern for idempotent integration upserts — e.g. the
  Composite/External-ID REST endpoints (`.../sobjects/Case/Canonical_Case_Id__c/{value}`)
  perform an insert-or-update keyed on that field automatically.
- **`IntegrationEnvelope.canonical_case_id`** ([`integrations/envelope.py`](../integrations/envelope.py))
  carries this identity alongside any translated payload so a future
  connector can always resolve "which canonical case is this?" regardless
  of which platform's record id it also holds
  (`IntegrationEnvelope.source_record_id`).

An operation replayed with the same `canonical_case_id` should always
converge to the same platform record — never create a duplicate. Neither
adapter enforces this today (there is no persistence or live API call to
enforce it against); it is documented here as the contract a real connector
built on top of these adapters must honour.

## How a future API connector would sit around these adapters

```
business_process (decides)  --state-->  integrations (orchestrates)  --calls-->  dynamics365 / salesforce (translate)
                                              |
                                              +--wraps result in--> IntegrationEnvelope
                                              |
                                    (future) transport/API client
                                    (future) retry / delivery guarantees
                                    (future) webhook ingestion back into business_process
```

[`integrations/examples.py`](../integrations/examples.py) plays this
orchestrator role today, but only to generate deterministic example files —
it has no transport, no retry logic, and no live endpoint. A real connector
would keep the same shape (ask `business_process` for current state, call an
adapter's pure `to_*` function, wrap the result in an `IntegrationEnvelope`)
and add exactly one new layer on top: an actual HTTP/SDK client and a
delivery mechanism. Neither adapter needs to change for that to happen —
this is precisely the "modular, replaceable SaaS components" principle
from the root README.
