---
name: dr-test-plan
description: Draft a disaster recovery test plan for a set of services, with the recovery sequence taken from the dependency map. Use when asked to plan a DR test, failover exercise, or restore test.
---

# Draft a DR test plan

Produce a first-draft DR test plan using `templates/dr-test-plan-template.md`. The test lead and service owners review it before any change record is raised.

## Inputs

1. Scope: a list of service IDs, a tier (for example "all Tier 1"), or a scenario such as "loss of the message bus". Ask if none is given.
2. Test type: tabletop, component failover, region failover, or restore from backup. Default to tabletop if the user does not say, and state that you did.
3. The services and dependencies CSVs (defaults in `sample/`).

## Steps

1. Run the tiering script:
   ```
   python -m tiering.tier <services.csv> <dependencies.csv> --report out/tiering-report.md
   ```
2. Resolve the scope to a list of service IDs. Add every hard dependency of an in-scope service that is not already in scope, and list those under "Dependencies assumed available" unless the user wants them tested too. Ask if that choice would change the test materially.
3. Copy the template to `out/dr-test-plan-<short-name>.md` and fill it in:
   - **Objectives:** one RTO objective and one RPO objective per Tier 1 service in scope, using its targets. Add the runbook validation objective.
   - **Scenario:** describe the failure plainly. For a scenario based on a shared dependency, name the services that depend on it.
   - **Recovery sequence:** use the recovery waves from the tiering report, restricted to services in scope. One row per service, in wave order. Leave durations blank for owners to estimate.
   - **Safety and rollback:** propose abort criteria based on the tightest RTO in scope. Leave the rollback procedure for the owner unless a runbook was provided.
   - **Results table:** pre-fill target RTO and RPO for each service; leave achieved values blank.
4. Add a "Pre-test findings" note above section 1 listing tiering findings for in-scope services. Flag any RTO inversion or cycle as a likely test failure, so the team can decide whether to fix it first or test to confirm it.
5. Tell the user where the file is, the number of services and waves, and any findings that are likely to cause a failed objective.

## Rules

- Do not invent runbook steps, hostnames, tools, or durations. Leave them for the owner.
- A service never appears in a wave before its hard dependencies.
- Services in a dependency cycle are recovered in the same wave; note that a manual bootstrap procedure is needed.
- Write plainly.
