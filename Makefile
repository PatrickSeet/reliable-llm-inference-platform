up:
	kind create cluster --name llm --config cluster/kind-config.yaml
	kubectl apply -f deploy/vllm/
	kubectl rollout status deploy/llm --timeout=120s

down:
	kind delete cluster --name llm

smoke:
	python client/smoke.py