# Disaster Recovery Test Plan: {Test name}

| Field | Value |
|---|---|
| Test ID | {DR-YYYY-NN} |
| Services in scope | {ids and tiers} |
| Test type | {tabletop / component failover / full region failover / restore from backup} |
| Environment | {production / production-like staging} |
| Scheduled window | {date, start-end time, time zone} |
| Test lead | {name} |
| Change record | {ticket ID} |
| Approved by | {name, role, date} |

## 1. Objectives

Each objective must be measurable and pass or fail.

| # | Objective | Success criterion |
|---|---|---|
| 1 | Recover {service} in the secondary environment within RTO | Service passes health checks within {RTO} of failover start |
| 2 | Confirm data loss is within RPO | Last replicated transaction is no older than {RPO} at cutover |
| 3 | Validate the runbook | Recovery completed using only the documented runbook; deviations logged |
| 4 | | |

## 2. Scope

**In scope:** {services, data stores, regions, teams}

**Out of scope:** {and why}

**Dependencies assumed available:** {list; anything not on this list is treated as failed or must be tested}

## 3. Scenario

{The failure being simulated, e.g. "Loss of primary region us-east for all Tier 1 services." Describe how the failure is induced: DNS cutover, traffic drain, instance termination, network block.}

## 4. Recovery sequence

Use the recovery waves from the tiering report. A service starts only after its hard dependencies pass health checks.

| Step | Wave | Action | Owner | Expected duration | Start | End | Result |
|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | |
| 2 | 1 | | | | | | |
| 3 | 2 | | | | | | |

## 5. Roles

| Role | Name | Backup |
|---|---|---|
| Test lead / incident commander | | |
| Scribe and timekeeper | | |
| Service recovery owners | | |
| Business validation | | |
| Communications | | |

## 6. Safety and rollback

- **Abort criteria:** {customer impact beyond agreed threshold, data integrity error, recovery exceeding RTO by more than X%}
- **Rollback procedure:** {steps to return to primary; who decides}
- **Customer and stakeholder notice:** {who is told before and after}
- **Monitoring during test:** {dashboards and alerts watched}

## 7. Evidence to capture

- Timestamps for each step (failover start, each wave healthy, business validation complete)
- Screenshots or logs of health checks and data validation
- Runbook deviations and their reasons
- Achieved RTO and RPO per service

## 8. Results

| Service | Target RTO | Achieved RTO | Target RPO | Achieved RPO | Pass / fail |
|---|---|---|---|---|---|
| | | | | | |

## 9. Findings and actions

| Finding | Severity | Action | Owner | Due | Retest required |
|---|---|---|---|---|---|
| | | | | | |

## 10. Sign-off

| Role | Name | Date |
|---|---|---|
| Test lead | | |
| Service owners | | |
| Resilience program | | |
