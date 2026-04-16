### Observability Checklist

**Always — every new code path:**

| Aspect              | Check                                                            |
| ------------------- | ---------------------------------------------------------------- |
| **Structured logs** | Key events emit structured log with correlation ID               |
| **Error logs**      | All `catch` / error handlers log at ERROR level with stack trace |

**Where the stack supports it:**

| Aspect      | Check                                                     |
| ----------- | --------------------------------------------------------- |
| **Metrics** | Counters/histograms for request rate, error rate, latency |
| **Traces**  | Distributed trace spans created for cross-service calls   |

**Consider — based on risk and system maturity:**

Think through how failures and performance degradation will be visible in production.
Not every item is required, but each should be consciously decided:

| Aspect         | Question                                                       |
| -------------- | -------------------------------------------------------------- |
| **Alerts**     | How will an error spike or reliability degradation be noticed? |
| **Dashboards** | Where will this service/endpoint show up in monitoring?        |
| **Runbook**    | If this fails at 3am, does someone know what to do?            |

> **SLI / SLO / SLA** — three related concepts:
>
> - **SLI** (Indicator): the actual measurement — e.g. error rate, p99 latency
> - **SLO** (Objective): the internal target — e.g. "error rate < 0.1%", "p99 < 200ms"
> - **SLA** (Agreement): the contractual promise to customers, with consequences if missed
>
> Alerts fire when an SLO is at risk. Not every project needs formal SLOs — but every project benefits from knowing what "degraded" looks like.

*Observability is first-class scope, not post-launch cleanup.*
