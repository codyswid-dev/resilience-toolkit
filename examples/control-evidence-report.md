# Control Evidence Report

As of 2026-11-15.

14 controls cover 34 in-scope requirements across 3 frameworks (ISO 27001, NIST 800-53, SOC 2). 27 of 34 requirements are met.
Each mapped control supports 3.4 requirements on average, so one test produces evidence for several frameworks at once.
22 findings: 9 high, 9 medium, 4 low.

## Coverage by framework

| Framework | In scope | Met | At risk | Gap | Met % |
|---|---|---|---|---|---|
| ISO 27001 | 13 | 9 | 3 | 1 | 69% |
| NIST 800-53 | 10 | 9 | 0 | 1 | 90% |
| SOC 2 | 11 | 9 | 1 | 1 | 82% |

## Findings

| Severity | Category | Subject | Detail |
|---|---|---|---|
| High | Failed test | BK-02 | Latest test on 2026-10-20 failed (Catalog DB restore missed 4h RTO (issue INC-2291)). Log an issue with an owner and due date, and retest after remediation. It supports 4 requirements across 3 frameworks. |
| High | Missing evidence | VR-02 | No test evidence on file for VR-02 (annual). It supports 3 requirements across 3 frameworks. |
| High | Requirement at risk | ISO 27001 A.5.15 | ISO 27001 A.5.15 (Access control) has mapped controls but none with current passing evidence: AC-02 stale. |
| High | Requirement at risk | ISO 27001 A.5.22 | ISO 27001 A.5.22 (Monitoring of supplier services) has mapped controls but none with current passing evidence: VR-02 missing evidence. |
| High | Requirement at risk | ISO 27001 A.8.15 | ISO 27001 A.8.15 (Logging) has mapped controls but none with current passing evidence: LG-01 stale. |
| High | Requirement at risk | SOC 2 CC7.2 | SOC 2 CC7.2 (Monitoring for anomalies) has mapped controls but none with current passing evidence: LG-01 stale. |
| High | Unmapped requirement | ISO 27001 A.5.7 | No control maps to ISO 27001 A.5.7 (Threat intelligence). An auditor testing it will find nothing. |
| High | Unmapped requirement | NIST 800-53 AT-2 | No control maps to NIST 800-53 AT-2 (Security awareness training). An auditor testing it will find nothing. |
| High | Unmapped requirement | SOC 2 CC7.5 | No control maps to SOC 2 CC7.5 (Recovery from incidents). An auditor testing it will find nothing. |
| Medium | No owner | AC-04 | AC-04 has no named owner, so nobody is accountable for testing it. |
| Medium | Requirement lapsing | ISO 27001 A.5.24 | ISO 27001 A.5.24 (Incident management planning) is met only by evidence that expires soon (IR-01; first expiry 2026-12-05). Without a new test it becomes at risk. |
| Medium | Requirement lapsing | ISO 27001 A.8.2 | ISO 27001 A.8.2 (Privileged access rights) is met only by evidence that expires soon (AC-04; first expiry 2026-11-28). Without a new test it becomes at risk. |
| Medium | Requirement lapsing | NIST 800-53 AC-6 | NIST 800-53 AC-6 (Least privilege) is met only by evidence that expires soon (AC-04; first expiry 2026-11-28). Without a new test it becomes at risk. |
| Medium | Requirement lapsing | SOC 2 CC6.3 | SOC 2 CC6.3 (Access changes and removal) is met only by evidence that expires soon (AC-04; first expiry 2026-11-28). Without a new test it becomes at risk. |
| Medium | Requirement lapsing | SOC 2 CC7.4 | SOC 2 CC7.4 (Incident response) is met only by evidence that expires soon (IR-01; first expiry 2026-12-05). Without a new test it becomes at risk. |
| Medium | Stale evidence | AC-02 | Latest evidence 2026-06-30 expired 2026-10-08 (38 days ago) for a quarterly control. It supports 6 requirements across 3 frameworks. |
| Medium | Stale evidence | LG-01 | Latest evidence 2026-11-02 expired 2026-11-09 (6 days ago) for a continuous control. It supports 3 requirements across 3 frameworks. |
| Medium | Unknown control ID | AC-09 | evidence.csv line 19 names AC-09, which is not in the control set. |
| Low | Evidence due soon | AC-04 | Evidence expires 2026-11-28 (13 days). |
| Low | Evidence due soon | IR-01 | Evidence expires 2026-12-05 (20 days). |
| Low | Out-of-scope mapping | CM-01 | CM-01 maps to PCI DSS 6.5.1, which is not in the in-scope requirements. Add the requirement to scope or drop the mapping. |
| Low | Unmapped control | HR-01 | HR-01 maps to no in-scope requirement. Map it, or retire it and stop testing it. |

## Requirements not met

| Framework | Requirement | Title | Status | Mapped controls |
|---|---|---|---|---|
| ISO 27001 | A.5.7 | Threat intelligence | Gap | — |
| NIST 800-53 | AT-2 | Security awareness training | Gap | — |
| SOC 2 | CC7.5 | Recovery from incidents | Gap | — |
| ISO 27001 | A.5.15 | Access control | At risk | AC-02 (Stale) |
| ISO 27001 | A.5.22 | Monitoring of supplier services | At risk | VR-02 (Missing evidence) |
| ISO 27001 | A.8.15 | Logging | At risk | LG-01 (Stale) |
| SOC 2 | CC7.2 | Monitoring for anomalies | At risk | LG-01 (Stale) |

## Controls

Sorted by reach: the controls at the top support the most requirements, so a lapse there costs the most.

| Control | Title | Owner | Frequency | Automated | Frameworks | Requirements | Last evidence | Expires | Status |
|---|---|---|---|---|---|---|---|---|---|
| AC-02 | Quarterly user access review | IT Identity | quarterly | no | 3 | 6 | 2026-06-30 | 2026-10-08 | Stale |
| BK-02 | Restore tested from backup | Platform Eng | quarterly | no | 3 | 4 | 2026-10-20 | 2027-01-28 | Failing |
| LG-02 | Alert triage within SLA reviewed monthly | Security Operations | monthly | no | 3 | 4 | 2026-10-31 | 2026-12-05 | Current |
| AC-01 | Access requests approved before provisioning | IT Identity | quarterly | no | 3 | 3 | 2026-09-30 | 2027-01-08 | Current |
| AC-03 | MFA enforced on workforce SSO | IT Identity | continuous | yes | 3 | 3 | 2026-11-14 | 2026-11-21 | Current |
| AC-04 | Privileged access limited and reviewed | — | quarterly | no | 3 | 3 | 2026-08-20 | 2026-11-28 | Due soon |
| BK-01 | Backups complete and monitored | Platform Eng | continuous | yes | 3 | 3 | 2026-11-15 | 2026-11-22 | Current |
| CM-01 | Production changes approved before deploy | Platform Eng | continuous | yes | 3 | 3 | 2026-11-14 | 2026-11-21 | Current |
| DR-01 | Tier 1 disaster recovery test | Resilience | annual | no | 3 | 3 | 2026-03-10 | 2027-03-25 | Current |
| IR-01 | Incident response plan exercised | Security Operations | annual | no | 3 | 3 | 2025-11-20 | 2026-12-05 | Due soon |
| LG-01 | Security events sent to central logging | Security Operations | continuous | yes | 3 | 3 | 2026-11-02 | 2026-11-09 | Stale |
| VR-01 | Vendor risk assessed before onboarding | Third-Party Risk | quarterly | no | 3 | 3 | 2026-10-01 | 2027-01-09 | Current |
| VR-02 | Critical vendors reviewed annually | Third-Party Risk | annual | no | 3 | 3 | — | — | Missing evidence |
| HR-01 | Clean desk walkthrough | Facilities | semiannual | no | 0 | 0 | 2026-07-01 | 2027-01-07 | Current |

## Evidence requests by owner

What each owner needs to produce, most urgent first. "now" means the evidence is missing, stale, or failed.

**(no owner)**

- AC-04 Privileged access limited and reviewed: due soon, due 2026-11-28

**IT Identity**

- AC-02 Quarterly user access review: stale, due now

**Platform Eng**

- BK-02 Restore tested from backup: failing, due now

**Security Operations**

- LG-01 Security events sent to central logging: stale, due now
- IR-01 Incident response plan exercised: due soon, due 2026-12-05

**Third-Party Risk**

- VR-02 Critical vendors reviewed annually: missing evidence, due now
