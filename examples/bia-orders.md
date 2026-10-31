# Business Impact Analysis: Order Service

> **Example output.** Drafted with the `bia-draft` skill from the synthetic data in `sample/`. All names and values are fictional.

**Draft status.** Fields still to be confirmed by the service owner: impact ratings at 1h, 24h, 72h and 1 week (section 2); minimum service level (section 3); vendors and people (section 4); restore test dates (section 5); manual workaround (section 6); action owners and dates (section 7).

| Field | Value |
|---|---|
| Service ID | orders |
| Service owner | Commerce Eng |
| Business function supported | Order capture |
| BIA version / date | 0.1 draft |
| Prepared by | bia-draft skill |
| Reviewed and approved by | [pending] |
| Next review due | [owner to set] |

## 1. Service description

The Order Service records customer orders placed through Checkout and makes them available to the Support Portal. If it is unavailable, customers cannot complete purchases and support staff cannot look up orders.

## 2. Impact over time

The inventory provides one rating per category. They are placed at the 4-hour column, the column closest to the 8-hour MTPD without exceeding it.

| Impact category | 1 hour | 4 hours | 24 hours | 72 hours | 1 week |
|---|---|---|---|---|---|
| Financial | [owner to confirm] | 4 | [owner to confirm] | [owner to confirm] | [owner to confirm] |
| Customer | [owner to confirm] | 4 | [owner to confirm] | [owner to confirm] | [owner to confirm] |
| Regulatory / legal | [owner to confirm] | 2 | [owner to confirm] | [owner to confirm] | [owner to confirm] |
| Operational | [owner to confirm] | 4 | [owner to confirm] | [owner to confirm] | [owner to confirm] |
| Reputational | [owner to confirm] | [owner to confirm] | [owner to confirm] | [owner to confirm] | [owner to confirm] |

## 3. Recovery requirements

| Metric | Value | Basis |
|---|---|---|
| MTPD | 8 hours | Service inventory |
| RTO | 4 hours | Service inventory |
| RPO | 5 minutes | Service inventory |
| Minimum service level during disruption | [owner to confirm] | |
| Recovery tier | 1 | Base tier 2 from impact; raised to Tier 1 because Checkout (Tier 1) has a hard dependency on it |

## 4. Dependencies

### Upstream

| Dependency | Type | Dependency RTO | Gap vs. 4h RTO | Workaround if unavailable |
|---|---|---|---|---|
| order-db | hard | 6h | **2h longer** | [owner to complete] |
| inventory | hard | 8h | **4h longer** | [owner to complete] |
| message-bus | hard | 2h | none | [owner to complete] |
| secrets | hard | 1h | none | [owner to complete] |

### Downstream

| Dependent service | Type | Dependent's tier |
|---|---|---|
| checkout | hard | 1 |
| support-portal | hard | 3 |

### Third parties and vendors

[owner to complete]

### People and locations

[owner to complete]

## 5. Data

| Data store | Classification | Backup / replication method | Tested restore date | Achieved RPO |
|---|---|---|---|---|
| order-db | [owner to confirm] | [owner to confirm] | | |

## 6. Manual workarounds

[owner to complete]

## 7. Gaps and actions

| Gap | Risk | Proposed action | Owner | Due |
|---|---|---|---|---|
| RTO inversion: order-db targets 6h, orders targets 4h | Orders cannot meet its RTO | Reduce order-db RTO to 4h or less (warm standby or managed failover), or raise the orders RTO with business sign-off | | |
| RTO inversion: inventory targets 8h, orders targets 4h | Orders cannot meet its RTO | Reduce inventory RTO to 4h or less, or make the dependency soft by accepting orders with deferred stock checks | | |
| Checkout targets 1h RTO and depends on orders (4h) | Checkout cannot meet its RTO | Agree a shared target with the Checkout owner; see the Checkout BIA | | |
| Upstream secrets has a dependency cycle with feature-flags | Secrets may not start cleanly in a full recovery, blocking orders | Confirm with Security Eng that a manual bootstrap procedure exists and has been tested | | |
| Upstream message-bus and secrets each have 4 hard dependents | A single failure affects orders and several other services | Confirm redundancy and include both in the next DR test | | |

## 8. Approval

| Role | Name | Date |
|---|---|---|
| Service owner | | |
| Business process owner | | |
| Resilience program | | |
