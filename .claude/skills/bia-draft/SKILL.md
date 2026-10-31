---
name: bia-draft
description: Draft a Business Impact Analysis for one service from the service inventory, dependency map, and tiering report. Use when asked to draft, start, or update a BIA for a named service.
---

# Draft a Business Impact Analysis

Produce a first-draft BIA for one service, using `templates/bia-template.md`. The draft is for the service owner to review and correct. It is not an approved BIA.

## Inputs

1. The service ID. If the user did not give one, list the IDs in the services CSV and ask.
2. The service inventory CSV (default `sample/services.csv`) and dependencies CSV (default `sample/dependencies.csv`). Use different paths if the user names them.
3. Any notes the user provides: incident history, revenue per hour, SLA terms, vendor contracts.

## Steps

1. Run the tiering script so the draft uses current tiers and findings:
   ```
   python -m tiering.tier <services.csv> <dependencies.csv> --report out/tiering-report.md
   ```
2. Read the service's row, its upstream and downstream dependencies, its final tier and tier reason, and every finding that names the service or one of its hard dependencies.
3. Copy `templates/bia-template.md` to `out/bia-<service-id>.md` and fill it in:
   - **Header and section 1:** from the inventory row. Write the description in plain language from the business function and dependents.
   - **Section 2 (impact over time):** the inventory gives one rating per category. Put that rating in the column closest to the service's MTPD, and leave the other columns blank with `[owner to confirm]`. Do not invent a curve.
   - **Section 3:** copy MTPD, RTO, RPO and tier from the data. If the tier was inherited, say from which service. If RPO is missing, write `[missing: owner to set]`.
   - **Section 4:** list every upstream dependency with its type and RTO, and compute the gap against this service's RTO. List every downstream dependent with its tier. Leave vendor and people tables with `[owner to complete]` unless the user supplied that information.
   - **Section 5:** list data stores that appear as dependencies. Leave restore test dates blank.
   - **Section 7 (gaps):** one row per tiering finding that involves this service. Use the finding text as the gap, and propose a specific action. Leave owner and due date blank.
4. At the top of the draft, add a short "Draft status" note listing every field marked `[owner to confirm]`, `[owner to complete]`, or `[missing]`, so the reviewer can see what is unverified.
5. Tell the user where the file is, the service's tier, and the top gaps.

## Rules

- Use only data from the inputs and what the user tells you. Mark anything else as a question for the owner. Never fill an impact rating, RTO, vendor SLA, or restore date with a guess.
- Keep the template's section order and headings so drafts are comparable across services.
- Write plainly. No marketing language.
- If the service has a dependency cycle or an RTO inversion, put it first in section 7. Those block a credible recovery plan.
