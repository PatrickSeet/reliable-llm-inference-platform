# Design Decisions

Decision records (DR) for the Reliable LLM Inference Platform, in the order
they were made. Each record states the context, the decision, its
consequences, and the alternatives considered. Environment notes that are
not design choices are collected at the end.

| ID | Title | Stage |
|---|---|---|
| DR-001 | Develop against an inference simulator before vLLM | 1 |
| DR-002 | Dummy model name for the simulator | 1 |
| DR-003 | TCP readiness probe for the simulator | 1 |
| DR-004 | Phoenix as trace backend, direct export, Collector deferred | 2 |
| DR-005 | Disable Kubernetes service links for Phoenix | 2 |
| DR-006 | Pin httpx explicitly | 2 |
| DR-007 | Ephemeral trace storage for Phoenix | 2 |
| DR-008 | Metrics to Prometheus, traces to Phoenix | 2 |
| DR-009 | Monitoring CRs applied after the Helm install | 2 |
| DR-010 | No error-rate SLI on the simulator | 2 |
| DR-011 | Node price as a constant recording rule | 2 |
| DR-012 | Dashboards provisioned from git | 2 |

---

### DR-001: Develop against an inference simulator before vLLM

**Context:** Real vLLM needs an NVIDIA GPU. Building the platform's
Kubernetes manifests, observability and release tooling does not depend on
real model output, only on the OpenAI-compatible API contract.

**Decision:** Serve `llm-d-inference-sim` (`ghcr.io/llm-d/llm-d-inference-sim:v0.9.0`)
behind the same Deployment name, Service name (`llm`), port (8000) and labels
that vLLM will use. Swap to vLLM on a rented GPU for work that depends on
real hardware behavior.

**Consequences:** Development is fast and free. Latency, throughput,
KV-cache pressure, OOM behavior and cold-start time are not meaningful on
the simulator; all such numbers in this repo will come from vLLM and are
labeled with what they ran on. The swap should be limited to the image,
model name and resources.

**Alternatives considered:**
- vLLM on a rented GPU from day one: rejected; pays for GPU time while
  debugging YAML.
- vLLM CPU backend: viable for functional tests, too slow for meaningful
  performance numbers.

### DR-002: Dummy model name for the simulator

**Context:** Given a real Hugging Face model name (`Qwen/Qwen3-0.6B`), the
simulator tokenizes via a separate render server at `localhost:8082`.
Without that server, requests fail with HTTP 500 ("Failed to tokenize").

**Decision:** Run the simulator with `--model sim-model --mode echo`, which
uses its built-in tokenizer and echoes the prompt.

**Consequences:** No render server and no Hugging Face access needed. The
model name differs between simulator (`sim-model`) and vLLM
(`Qwen/Qwen3-0.6B`), so the client reads it from `LLM_MODEL` to keep the
swap a configuration change.

**Alternatives considered:**
- Run the render server alongside the simulator: rejected; extra component
  with no benefit for API-contract testing.

### DR-003: TCP readiness probe for the simulator

**Context:** The readiness probe gates traffic to the pod. The simulator
starts in seconds and loads no model.

**Decision:** Use a `tcpSocket` probe on port 8000 with a 5s initial delay.
<!-- If /health returned 200, replace with: httpGet /health -->

**Consequences:** A TCP check only proves the port is open, not that the
server answers correctly; acceptable for a simulator with no warm-up.
Measured time to Ready on the simulator: cold 14s (including a 3s image
pull), warm 11s; about 10s of each is readiness-probe timing (5s initial
delay + 10s period), not application startup. This is only for comparison in Stage 3 vLLM. See README "Measurements". (`scripts/time_to_ready.py`).

**Planned for vLLM:** startup takes minutes (image pull, weight download,
GPU load, warm-up). Use a `startupProbe` on `/health` sized from measured
load time, an HTTP `readinessProbe`, and a persistent Hugging Face weight
cache so restarts don't re-download weights.

### DR-004: Phoenix as trace backend, direct export, Collector deferred

**Context:** Client calls need distributed tracing with LLM-specific
attributes (model, token counts) on a laptop-sized cluster.

**Decision:** Self-host Arize Phoenix (`arizephoenix/phoenix:version-20.21.1`)
as the trace backend. Instrument the client with OpenLLMetry
(`traceloop-sdk==0.62.4`), which auto-instruments the openai client using
the OpenTelemetry GenAI semantic conventions. Export spans directly to
Phoenix; add an OpenTelemetry Collector in between as a later step.

**Consequences:** One container, minimal code (two lines in the client).
Only client-side spans exist until vLLM's server-side tracing is enabled.
Without a Collector there is no batching, filtering or fan-out to multiple
backends yet.

**Alternatives considered:**
- Langfuse: rejected for now; more components and memory than a laptop
  cluster comfortably supports.
- Manual OpenTelemetry spans: more code for the same attributes.

### DR-005: Disable Kubernetes service links for Phoenix

**Context:** Kubernetes injects environment variables for every Service in
a namespace. For a Service named `phoenix` it sets
`PHOENIX_PORT=tcp://<ip>:6006`, which collides with Phoenix's own
`PHOENIX_PORT` setting (an integer). Phoenix exited with
`ValueError` and the pod went into CrashLoopBackOff.

**Decision:** Set `enableServiceLinks: false` on the pod and set
`PHOENIX_PORT: "6006"` explicitly.

**Consequences:** Removes the whole class of collision; services are found
by DNS name, so nothing relied on the injected variables. Applies to any
app whose config variables start with its own Service name.

### DR-006: Pin httpx explicitly

**Context:** openai 3.x replaced its HTTP dependency `httpx` with `httpx2`.
`traceloop-sdk==0.62.4` imports `httpx` but does not declare it, so a clean
install fails at import time with `ModuleNotFoundError: No module named 'httpx'`.

**Decision:** Pin `httpx==0.28.1` in `requirements.txt` with a comment
explaining why.

**Consequences:** Clean installs work. Revisit when upgrading traceloop-sdk;
the pin can be dropped once it declares the dependency.

### DR-007: Ephemeral trace storage for Phoenix

**Context:** Phoenix stores data in `PHOENIX_WORKING_DIR`. Its Kubernetes
documentation recommends PostgreSQL for production.

**Decision:** Use an `emptyDir` volume for local development.

**Consequences:** Traces are lost on pod restart or `make down`. Acceptable
while traces are used for development and debugging, not history. A
persistent volume or PostgreSQL is required before traces are used as
evidence across sessions.

### DR-008: Metrics to Prometheus, traces to Phoenix

**Context:** traceloop-sdk also exports client-side metrics to the same
endpoint as traces. Phoenix accepts traces only and returns HTTP 405 for
metrics.

**Decision:** Disable traceloop's metrics export
(`TRACELOOP_METRICS_ENABLED=false`). Server metrics come from Prometheus
scraping `/metrics`; traces go to Phoenix.

**Consequences:** Clear separation of signals and no export errors. If
client-side metrics are needed later, route them through the OpenTelemetry
Collector to Prometheus.

### DR-009: Monitoring CRs applied after the Helm install

**Context:** ServiceMonitor and PrometheusRule are custom resources whose
definitions (CRDs) are installed by kube-prometheus-stack. Applying them on
a fresh cluster before the chart fails. The chart's Prometheus also only
selects resources labeled `release: mon`.

**Decision:** Keep these resources in `deploy/monitoring/`, applied by the
`make monitoring` target after `helm upgrade --install`. Label every
ServiceMonitor and PrometheusRule with `release: mon`. Chart version
pinned: `kube-prometheus-stack-92.10.1`.

**Consequences:** `make up` then `make monitoring` rebuilds the full stack
reproducibly. A missing `release` label silently results in no target or no
rules, so the label is part of every new monitoring resource.

### DR-010: No error-rate SLI on the simulator

**Context:** The simulator exposes `vllm:request_success_total` but no
failure counter, so a server-side error rate cannot be computed.

**Decision:** Omit the error-rate panel rather than show a panel that is
always zero. Availability is measured after the vLLM swap, from vLLM's
metrics, or from client-side span status in Phoenix.

**Consequences:** The Stage 2 dashboard has no availability signal while on
the simulator. Stage 3 SLO work on availability is blocked until the swap or
until client-side errors are counted.

**Alternatives considered:**
- Panel computing errors as `total - success`: rejected; there is no
  total-requests counter to subtract from.
- Client-side error counter: viable later; measures what users see,
  including network failures the server never records.

### DR-011: Node price as a constant recording rule

**Context:** Cost per 1K output tokens needs the serving node's hourly
price. A ConfigMap was considered, but PromQL can only read metrics, not
Kubernetes objects.

**Decision:** Define the price as a recording rule
(`llm:node_hourly_cost_usd`, `vector(<price>)`) in
`deploy/monitoring/rules-llm.yaml`. All cost queries reference it.

**Consequences:** The price lives in one place, in git, and changing it is a
reviewed commit. Queries use `scalar()` to combine it with other series. The
current value ($0.80) is a placeholder; the simulator runs on a laptop, so
this number describes no real hardware. Replace it with the actual GPU
instance price when vLLM is deployed.

**Alternatives considered:**
- ConfigMap: rejected; not readable by PromQL.
- Hard-coding the price in each panel's query: rejected; duplicated, easy to
  miss when the price changes.
- Exporting price as a metric from a small service: more realistic for
  multi-instance-type clusters, unnecessary for one node type.

### DR-012: Dashboards provisioned from git

**Context:** Dashboards created in the Grafana UI are lost when the cluster
is rebuilt and are not reviewable.

**Decision:** Store dashboard JSON in `deploy/monitoring/dashboards/` and
load it through a ConfigMap labeled `grafana_dashboard: "1"`, which the
chart's Grafana sidecar watches.

**Consequences:** Dashboards survive rebuilds and changes are reviewed in
git. Provisioned dashboards cannot be saved from the UI; edits are exported
as JSON and committed. A missing label means the sidecar silently ignores
the ConfigMap.

---

## Environment notes

- **Python 3.12 required.** openai 3.x requires Python >= 3.10. macOS's
  built-in `python3` is 3.9, so create the venv with `python3.12 -m venv .venv`.
- **Port-forwards.** Laptop access to in-cluster services uses
  `kubectl port-forward` (llm: 8000, Phoenix: 6006, Prometheus: 9090,
  Grafana: 3000). They stop when the pod restarts or the terminal closes.
- **Docker Desktop memory.** The monitoring stack needs roughly 8 GB
  allocated to Docker Desktop; pods otherwise stay Pending or are
  OOM-killed.
