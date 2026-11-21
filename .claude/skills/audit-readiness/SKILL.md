---
name: audit-readiness
description: Assess audit readiness for a control set and draft evidence requests for control owners. Use when asked which requirements an auditor would find unsupported, what evidence is missing or stale, or to prepare owner requests before an audit or assessment.
---

# Audit readiness and evidence requests

Produce a readiness summary for an upcoming audit and one evidence request per control owner. The output is for the GRC lead to review and send. It does not change any control, mapping, or evidence record.

## Inputs

1. The control data directory holding `controls.csv`, `requirements.csv`, `mappings.csv`, and `evidence.csv` (default `sample/controls`).
2. The assessment date. Use the audit fieldwork start date if the user gives one, otherwise today. Evidence that expires before fieldwork is a problem now, so assess against fieldwork, not today.
3. Optional: which frameworks are in scope for this audit. If the user names one (for example "the SOC 2 audit"), report on that framework only.

## Steps

1. Run the checker against the assessment date:
   ```
   python -m controls.check <data-dir> --as-of <date> --report out/control-evidence-report.md --status-csv out/requirement-status.csv
   ```
2. Read the report. If the user limited scope to one framework, filter requirements and findings to it, but keep every control that maps to it.
3. Write `out/audit-readiness.md` with:
   - **Readiness summary:** requirements in scope, how many are met, at risk, and gaps, as of the assessment date. One sentence on the biggest exposure.
   - **Blockers:** every gap and every at-risk requirement, each with the controls involved and what would fix it (map a control, collect evidence, retest after remediation). Gaps first.
   - **Failed tests:** each failing control, the evidence reference, and the requirements it leaves exposed. Say whether another current control still covers each requirement.
   - **Lapsing before fieldwork:** requirements met only by evidence that expires before the assessment date plus 30 days.
   - **Data hygiene:** controls with no owner, unknown control IDs, unmapped controls, out-of-scope mappings. These are the questions an auditor asks first about the control inventory.
4. Write one file per owner, `out/requests/<owner>.md`, from the report's evidence request list. For each control: the control title, why evidence is needed (missing, stale, failed, or expiring), the due date, the requirements it supports, and what evidence usually satisfies it, based on the control title and the most recent evidence source and reference. Keep each request short enough to paste into a ticket or email.
5. For controls with no owner, do not guess one. List them in the readiness summary under "Owner needed" for the GRC lead to assign.
6. Tell the user the readiness numbers, the top blockers, and where the files are.

## Rules

- Use only what the data and the user provide. Never mark evidence as collected, change a test result, or invent a requirement mapping.
- A failed test is not fixed by new evidence alone. Say that it needs an issue, remediation, and a retest.
- Do not soften findings. "At risk" and "Gap" mean an auditor would find the requirement unsupported on the assessment date.
- Write plainly. No marketing language.
