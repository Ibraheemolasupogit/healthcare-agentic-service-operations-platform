# Service Operations Analytics Report

Synthetic/generated portfolio evidence only. This report is derived from repository fixtures and generated CRM, automation, approval, and AI evidence. It is not production telemetry.

## Service Volume

- Total cases: 6
- Open cases: 3
- Resolved/closed cases: 3
- Case volume by category: {'Access and Identity': 1, 'Application Support': 1, 'Clinical Equipment': 1, 'Data and Reporting': 1, 'Digital Support': 1, 'Facilities': 1}
- Case volume by priority: {'Critical': 1, 'High': 1, 'Low': 2, 'Medium': 2}

## SLA and Escalation

- SLA compliance rate: 83.33%
- SLA breach count: 1
- Escalation count: 1
- Escalation rate: 16.67%

## Resolution Performance

- Mean resolution minutes: 145.0
- Median resolution minutes: 90.0
- Resolution outcomes: {'Fixed': 2, 'No Action Required': 1, 'Unknown': 3}

## Automation Observations

- Automation executions: 1
- Simulated success rate: 100.0%
- Approval decisions: 2

## AI-Assistance Observations

- Agent/tool invocations: 2
- Tool invocation mix by risk: {'read-only': 1, 'recommendation': 0, 'state-changing': 1, 'consequential': 0}
- Approval-required AI actions: 1

## Limitations and Provenance

- Dataset is intentionally tiny and synthetic.
- No production baseline exists, so no improvement claim is made.
- SLA calculations are delegated to `business_process.sla`.
- Analytics is downstream only and is not a transactional source of truth.
