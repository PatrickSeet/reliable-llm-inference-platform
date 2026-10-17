A real Hugging Face model name makes the simulator call a render server on port 8082 for tokenization. I used a dummy model name to get the built-in tokenizer.” Small findings like this are good interview material.

## Observability
Kubernetes service-link environment variables collided with Phoenix’s own PHOENIX_PORT setting; fixed with enableServiceLinks: false and an explicit port.” It’s a real Kubernetes gotcha that catches many tools, and the general point that injected environment variables can clash with an app’s own configuration applies well beyond Phoenix.

A major version change in openai removed a dependency that traceloop-sdk relied on without declaring; pinned httpx explicitly.