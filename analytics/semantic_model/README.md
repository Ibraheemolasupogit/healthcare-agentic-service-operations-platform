# analytics/semantic_model/

Reference semantic model suitable for a future Power BI dataset. This is
metadata only; there is no deployed semantic model, dataset refresh, Power BI
workspace, or XMLA endpoint.

## Dimensions

- Date
- Service Category
- Priority
- Queue
- Case Status
- Resolution Outcome
- Automation Workflow
- Agent
- Tool Risk Class

## Facts

- Case
- Case Event
- SLA Event
- Automation Execution
- Agent Interaction
- Approval Decision

## Modelling Decisions

- Grain is explicitly documented per fact in `model.py`.
- Relationships assume single-direction filtering from dimensions to facts.
- Slowly changing attributes are not modelled for the small synthetic dataset.
- Measures are reference DAX-style definitions; they are not deployed.
- Canonical enumerations remain sourced from `business_process`, not copied
  into the semantic layer as a competing rule source.
