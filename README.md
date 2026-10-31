# Resilience Toolkit

Tools for the analysis work behind a business continuity and disaster recovery program: tiering services by impact, checking a dependency map for recovery gaps, and drafting BIAs and DR test plans with Claude Code.

All data in this repository is synthetic. The sample is a fictional online retailer with 17 services.

## Contents

| Path | What it is |
|---|---|
| [`tiering/`](tiering/) | Python script that assigns recovery tiers, propagates them through dependencies, and reports gaps. Standard library only. |
| [`.claude/skills/bia-draft/`](.claude/skills/bia-draft/SKILL.md) | Claude Code skill that drafts a Business Impact Analysis for one service from the inventory and tiering output. |
| [`.claude/skills/dr-test-plan/`](.claude/skills/dr-test-plan/SKILL.md) | Claude Code skill that drafts a DR test plan, with the recovery sequence taken from the dependency map. |
| [`templates/`](templates/) | BIA, DR test plan, and chaos experiment templates in Markdown. |
| [`sample/`](sample/) | Synthetic service inventory and dependency map. |
| [`examples/`](examples/) | Output from the sample: [tiering report](examples/tiering-report.md) and a [drafted BIA](examples/bia-orders.md). |

## Why dependency analysis matters

A service's recovery target is only achievable if everything it depends on recovers first. Inventories usually set RTOs one service at a time, so the gaps show up only when the dependencies are put side by side. In the sample data:

- **Checkout** targets a 1-hour RTO but depends on Inventory and Product Catalog, which target 8 hours.
- **Product Catalog** is rated Tier 2 on its own impact, but Checkout cannot run without it, so it is effectively Tier 1 and its 8-hour RTO misses the Tier 1 standard.
- **Secrets Manager** and **Feature Flags** depend on each other. In a full recovery, neither can start first without a manual bootstrap step.
- **DNS**, **Message Bus**, and **Secrets Manager** each have four or more services that cannot run without them.

The tiering script finds these automatically. See the [full report](examples/tiering-report.md).

## Quick start

Requires Python 3.10 or later.

```bash
git clone https://github.com/codyswid-dev/resilience-toolkit.git
cd resilience-toolkit
python -m tiering.tier sample/services.csv sample/dependencies.csv
```

Options:

```bash
# Write the report and a CSV of final tiers
python -m tiering.tier sample/services.csv sample/dependencies.csv \
  --report out/report.md --tiers-csv out/tiers.csv

# Exit non-zero if any high-severity finding exists (for a CI gate on the service catalog)
python -m tiering.tier services.csv dependencies.csv --fail-on high
```

Run the tests:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## How tiering works

**Input.** `services.csv` holds one row per service with four impact ratings (financial, customer, regulatory, operational, each 1 to 5), maximum tolerable period of disruption (MTPD), and target RTO and RPO. `dependencies.csv` lists each dependency as hard (the service cannot run without it) or soft (the service degrades but runs).

**Base tier.** A service gets the first tier whose threshold it meets on either its highest impact rating or its MTPD:

| Tier | Highest impact | or MTPD | Maximum RTO |
|---|---|---|---|
| 1 | 5 | 4h or less | 4h |
| 2 | 4 | 24h or less | 24h |
| 3 | 3 | 72h or less | 72h |
| 4 | any | any | 168h |

The thresholds are constants at the top of [`tier.py`](tiering/tier.py) and should be set to match an organization's own standard.

**Propagation.** If a service has a hard dependency, the dependency's tier is raised to match. This repeats until nothing changes, so it carries through chains of dependencies. Soft dependencies do not propagate.

**Findings.**

| Finding | Severity | Meaning |
|---|---|---|
| RTO inversion | High | A hard dependency has a longer RTO than the service that needs it. |
| RTO exceeds tier standard | High (Tier 1–2), Medium | The service's RTO is longer than its final tier allows. |
| RTO exceeds MTPD | High | The recovery target is longer than the business can tolerate. |
| Dependency cycle | High | Services depend on each other, so neither can be recovered first. |
| Concentration risk | Medium | Four or more services hard-depend on this one. |
| Missing RPO | Medium | A Tier 1 or 2 service has no RPO target. |
| Unknown service ID | Medium | The dependency map references a service not in the inventory. |

**Recovery order.** The report groups services into recovery waves. Each wave depends only on services in earlier waves. Services in a cycle are placed in the same wave.

**Dependency map.** The report includes a Mermaid diagram, which GitHub renders directly.

## Claude Code skills

The skills in `.claude/skills/` load automatically when Claude Code runs in this repository. Example prompts:

- "Draft a BIA for the orders service."
- "Plan a tabletop DR test for all Tier 1 services."
- "Plan a DR test for loss of the message bus."

Each skill runs the tiering script first, so drafts use current tiers and findings. The skills fill in what the data supports and mark everything else for the service owner to confirm. They do not invent impact ratings, RTOs, vendor SLAs, or runbook steps. [`examples/bia-orders.md`](examples/bia-orders.md) shows the output for one service.

## Using your own data

Export your service catalog and dependency data to the two CSV formats in `sample/`. Common sources are a CMDB, a service catalog such as Backstage, or the output of a dependency discovery tool. The `notes` and `business_function` columns are optional and are not used in calculations.

## Author

Cody Swidler. I lead business continuity, disaster recovery, crisis management, and GRC programs, and I build AI-assisted tooling for that work with Claude Code. [LinkedIn](https://www.linkedin.com/in/codyswidler)

## License

[MIT](LICENSE)
