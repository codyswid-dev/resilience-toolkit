# Chaos Experiment: {Experiment name}

| Field | Value |
|---|---|
| Experiment ID | {CE-YYYY-NN} |
| Target service | {id, tier} |
| Owner | {name, team} |
| Environment | {staging / production} |
| Date and window | {date, time, time zone} |
| Approved by | {name, date} |

## 1. Hypothesis

State what should stay true while the fault is active.

> When {fault} occurs in {component}, {service} will continue to {steady-state behavior}, and {alert / failover} will happen within {time}.

## 2. Steady state

The measurable signals that show the service is healthy. Record baseline values before starting.

| Signal | Source | Baseline | Acceptable range during experiment |
|---|---|---|---|
| Request success rate | {dashboard} | | |
| p99 latency | | | |
| Business metric (e.g. orders per minute) | | | |

## 3. Fault

| Item | Detail |
|---|---|
| Fault type | {instance termination / dependency latency / dependency error / network partition / zone loss / resource exhaustion} |
| Injection method | {tool and command} |
| Blast radius | {percentage of traffic, hosts, or one zone} |
| Duration | {minutes} |
| Linked finding | {e.g. "Concentration risk: message-bus" from the tiering report} |

## 4. Safety controls

- **Stop conditions:** {steady-state signal leaves acceptable range for more than N minutes; any customer-visible error spike; on-call request}
- **Stop method:** {exact command or switch to remove the fault}
- **On-call aware:** {yes / no, names}
- **Customer impact expected:** {none / limited, with description}

## 5. Run log

| Time | Event | Observation |
|---|---|---|
| | Baseline recorded | |
| | Fault injected | |
| | First alert fired | |
| | Failover or mitigation | |
| | Fault removed | |
| | Steady state restored | |

## 6. Result

- **Hypothesis held:** {yes / no / partially}
- **Time to detect:** {minutes}
- **Time to recover:** {minutes}
- **What was different from expectation:**

## 7. Follow-up actions

| Action | Owner | Due | Re-run experiment after fix |
|---|---|---|---|
| | | | |
