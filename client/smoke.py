# client/smoke.py
import os
from openai import OpenAI
from traceloop.sdk import Traceloop

# Sends spans to TRACELOOP_BASE_URL (Phoenix). disable_batch sends each span
# immediately, so this short script doesn't exit before its spans are sent.     
Traceloop.init(app_name="smoke-client", disable_batch=True)

client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                api_key="dummy")
resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "sim-model"),
    messages=[{"role": "user", "content": "Say hi in 5 words"}],
)
print(resp.choices[0].message.content)