# client/smoke.py
import os
from openai import OpenAI

client = OpenAI(base_url=os.getenv("LLM_BASE_URL", "http://localhost:8000/v1"),
                api_key="dummy")
resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "sim-model"),
    messages=[{"role": "user", "content": "Say hi in 5 words"}],
)
print(resp.choices[0].message.content)