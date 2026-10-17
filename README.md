# reliable-llm-inference-platform
An OpenAI-compatible LLM serving platform on Kubernetes with production-grade observability, SLOs, eval-gated canary releases with automatic rollback, and documented failure experiments with a postmortem.

## Quick Start:
python3.12 -m venv .venv && source .venv/bin/activate  
pip install -r requirements.txt  
make up. 
kubectl port-forward svc/llm 8000:8000   # separate terminal. 
make smoke. 

## Stage 1: Serve
### Cold
pod:      llm-586976464d-2qngz  (node llm-worker2)
schedule:    11s
start:        4s   (image pull + container start)
ready:       10s   (app startup + readiness probe)
TOTAL:       25s   created -> Ready

59s         Normal    Pulling                   pod/llm-586976464d-2qngz    Pulling image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0"
56s         Normal    Pulled                    pod/llm-586976464d-2qngz    Successfully pulled image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0" in 2.946s (2.946s including waiting). Image size: 32218115 bytes.

### Warm
pod:      llm-6b5556f97c-dwkbz  (node llm-worker)
schedule:     0s
start:        4s   (image pull + container start)
ready:       10s   (app startup + readiness probe)
TOTAL:       14s   created -> Ready

2m40s       Normal    Pulling                   pod/llm-586976464d-2qngz    Pulling image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0"
2m37s       Normal    Pulled                    pod/llm-586976464d-2qngz    Successfully pulled image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0" in 2.946s (2.946s including waiting). Image size: 32218115 bytes.
57s         Normal    Pulling                   pod/llm-6b5556f97c-dwkbz    Pulling image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0"
54s         Normal    Pulled                    pod/llm-6b5556f97c-dwkbz    Successfully pulled image "ghcr.io/llm-d/llm-d-inference-sim:v0.9.0" in 3.079s (3.079s including waiting). Image size: 32218115 bytes.