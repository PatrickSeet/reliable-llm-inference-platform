# Reliable LLM Inference Platform

An OpenAI-compatible LLM serving platform on Kubernetes with production-grade
observability, SLOs, eval-gated canary releases with automatic rollback, and
documented failure experiments with a postmortem.

> **Status:** Stages 1–2 complete on an inference simulator
> (`llm-d-inference-sim`). Real vLLM on GPU arrives in Stage 3; see
> [DR-001](docs/design.md#dr-001-develop-against-an-inference-simulator-before-vllm).

## Architecture

```
client (smoke.py + OpenLLMetry) ──► Service llm:8000 ──► simulator pod
        │                                                  │ /metrics
        │ OTLP traces                                       ▼
        ▼                                     Prometheus (ServiceMonitor)
     Phoenix                                               │
                                                           ▼
                                                 Grafana "LLM Serving"
```

## Quick start

Prerequisites: Docker Desktop (8 GB+ memory), kind, kubectl, Helm, Python 3.12.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make up            # kind cluster + simulator + Phoenix
make monitoring    # kube-prometheus-stack, ServiceMonitor, rules, dashboard
```

In separate terminals:

```bash
kubectl port-forward svc/llm 8000:8000
kubectl -n observability port-forward svc/phoenix 6006:6006
kubectl -n monitoring port-forward svc/mon-grafana 3000:80
```

Then run `make smoke`. Traces appear at http://localhost:6006, the dashboard
at http://localhost:3000.

## Stages

| Stage | Scope | Status |
|---|---|---|
| 1. Serve | Simulator on Kubernetes, OpenAI-compatible API | Done |
| 2. Observe | Prometheus metrics, Phoenix traces, cost per 1K tokens, dashboard | Done (Collector pending) |
| 3. SLOs & load | Load tests, SLOs, burn-rate alerts, autoscaling (vLLM on GPU) | Next |
| 4. Eval-gated rollouts | promptfoo evals, Argo Rollouts canary + auto-rollback | Planned |
| 5. Failure & postmortem | Chaos experiments, MTTD/MTTR, postmortem | Planned |

## Measurements

Time from pod creation to Ready, simulator on kind (laptop), measured with
`scripts/time_to_ready.py`. Timestamps have 1-second resolution.

| Start type | Total | Image pull | Notes |
|---|---|---|---|
| Cold, fresh cluster | 25s | 2.9s | Includes 11s waiting for new cluster nodes |
| Cold, existing cluster | 14s | 3.1s | Image not yet cached on that node |
| Warm | 11s | none | Image cached on node |

Readiness (about 10s) is dominated by probe timing (5s initial delay + 10s
period), not application startup. vLLM measurements will be added in Stage 3.

## Design decisions

See [docs/design.md](docs/design.md) for decision records DR-001 to DR-012.