#!/usr/bin/env python3
"""Print startup timings for the newest pod.

Usage: kubectl get pods -l app=llm -o json | python scripts/time_to_ready.py
"""
import json
import sys
from datetime import datetime


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ") if s else None


pods = json.load(sys.stdin)["items"]
if not pods:
    sys.exit("No pods found for that selector.")

pod = max(pods, key=lambda p: p["metadata"]["creationTimestamp"])
cond = {c["type"]: ts(c.get("lastTransitionTime"))
        for c in pod["status"].get("conditions", [])}
created = ts(pod["metadata"]["creationTimestamp"])
cs = (pod["status"].get("containerStatuses") or [{}])[0]
started = ts(cs.get("state", {}).get("running", {}).get("startedAt"))

print(f"pod:      {pod['metadata']['name']}  (node {pod['spec'].get('nodeName')})")
if not cs.get("ready"):
    sys.exit("Pod is not Ready yet; wait and rerun.")


def span(a, b):
    return f"{(b - a).total_seconds():>5.0f}s" if a and b else "  n/a"


print(f"schedule: {span(created, cond.get('PodScheduled'))}")
print(f"start:    {span(cond.get('PodScheduled'), started)}   (image pull + container start)")
print(f"ready:    {span(started, cond.get('Ready'))}   (app startup + readiness probe)")
print(f"TOTAL:    {span(created, cond.get('Ready'))}   created -> Ready")