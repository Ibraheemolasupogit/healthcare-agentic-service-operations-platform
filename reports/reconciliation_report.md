# Integration Reconciliation Report

Synthetic/reference evidence only. This is not a live reconciliation job.

| Check | Severity | Case | Correlation | Finding | Recommended action |
|---|---|---|---|---|---|
| undelivered-envelope | error | SR-AI-1004 | 65908f53-f8d1-5f38-9238-d2620bc95b5f | Delivery state is failed | Send to manual review and retry after root cause is corrected. |
| undelivered-envelope | error | SR-DR-1006 | 9a0ecfe7-ec1c-5b47-b2b7-4712ec45776d | Delivery state is dead_lettered | Send to manual review and retry after root cause is corrected. |
| duplicate-external-record-mapping | error | SR-CE-1002 | 5f94e7bc-022f-5b60-9683-4f59076d37f1 | External record case-duplicate-001 is mapped to SR-DR-1006 and SR-CE-1002. | Quarantine mapping and resolve canonical/external identity conflict. |
| correlation-mismatch | error | SR-CE-1002 | 5f94e7bc-022f-5b60-9683-4f59076d37f1 | Envelope and delivery correlation ids differ. | Preserve original correlation id across retry and provider hops. |

The reconciliation layer detects delivery and representation inconsistencies only; it does not update canonical service state.
