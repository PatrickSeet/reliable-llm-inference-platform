# reliable-llm-inference-platform
An OpenAI-compatible LLM serving platform on Kubernetes with production-grade observability, SLOs, eval-gated canary releases with automatic rollback, and documented failure experiments with a postmortem.

Quick Start:
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make up
kubectl port-forward svc/llm 8000:8000   # separate terminal
make smoke