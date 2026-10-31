# Business Impact Analysis: {Service name}

| Field | Value |
|---|---|
| Service ID | {id} |
| Service owner | {owner} |
| Business function supported | {business_function} |
| BIA version / date | {version} / {YYYY-MM-DD} |
| Prepared by | {name} |
| Reviewed and approved by | {name, role, date} |
| Next review due | {date; at least annually or on material change} |

## 1. Service description

{Two or three sentences: what the service does, who uses it, and what business process stops if it is unavailable.}

## 2. Impact over time

Rate each impact category 1 (minimal) to 5 (severe) at each point after the start of an outage.

| Impact category | 1 hour | 4 hours | 24 hours | 72 hours | 1 week |
|---|---|---|---|---|---|
| Financial (lost revenue, penalties, recovery cost) | | | | | |
| Customer (customers unable to transact, contractual SLAs) | | | | | |
| Regulatory / legal (reportable events, filing deadlines) | | | | | |
| Operational (downstream processes and teams blocked) | | | | | |
| Reputational (external visibility, media, partners) | | | | | |

Basis for ratings: {data sources, e.g. transaction volumes, revenue per hour, SLA terms, prior incidents.}

## 3. Recovery requirements

| Metric | Value | Basis |
|---|---|---|
| Maximum tolerable period of disruption (MTPD) | {hours} | {first point where impact reaches 5 in any category} |
| Recovery time objective (RTO) | {hours} | {must be shorter than MTPD} |
| Recovery point objective (RPO) | {minutes} | {acceptable data loss} |
| Minimum service level during disruption | {e.g. read-only, 50% capacity, manual workaround} | |
| Recovery tier | {1-4} | {from tiering output; note if inherited} |

## 4. Dependencies

### Upstream (this service needs)

| Dependency | Type (hard / soft) | Dependency RTO | Gap vs. this service's RTO | Workaround if unavailable |
|---|---|---|---|---|
| | | | | |

### Downstream (needs this service)

| Dependent service | Type | Dependent's tier |
|---|---|---|
| | | |

### Third parties and vendors

| Vendor / product | What it provides | Contractual SLA / RTO | Exit or alternate option |
|---|---|---|---|
| | | | |

### People and locations

| Role or skill | Minimum staff to operate | Single points of failure (people) | Location dependency |
|---|---|---|---|
| | | | |

## 5. Data

| Data store | Classification | Backup / replication method | Tested restore date | Achieved RPO |
|---|---|---|---|---|
| | | | | |

## 6. Manual workarounds

{What the business can do while the service is down, how long the workaround can be sustained, and who runs it.}

## 7. Gaps and actions

| Gap | Risk | Action | Owner | Due |
|---|---|---|---|---|
| | | | | |

## 8. Approval

| Role | Name | Date |
|---|---|---|
| Service owner | | |
| Business process owner | | |
| Resilience program | | |
