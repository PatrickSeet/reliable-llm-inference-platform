up:
	kind create cluster --name llm --config cluster/kind-config.yaml
	kubectl apply -f deploy/vllm/
	kubectl apply -f deploy/observability/
	kubectl rollout status deploy/llm --timeout=120s

down:
	kind delete cluster --name llm

smoke:
	TRACELOOP_BASE_URL=http://localhost:6006 TRACELOOP_METRICS_ENABLED=false python client/smoke.py