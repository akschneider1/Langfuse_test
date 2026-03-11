#!/usr/bin/env python3
"""
Test the Langfuse REST API directly with raw HTTP requests.
Useful for understanding the API without the SDK, or for debugging.

Usage:
    python scripts/test_api_direct.py
"""

import json
import os
import time
import uuid

import requests
from dotenv import load_dotenv

load_dotenv()

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")
PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")

if not PUBLIC_KEY or not SECRET_KEY:
    raise SystemExit("ERROR: Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")

BASE_URL = f"{LANGFUSE_HOST}/api/public"
AUTH = (PUBLIC_KEY, SECRET_KEY)
HEADERS = {"Content-Type": "application/json"}


def check_health():
    """Check if Langfuse is healthy."""
    print("--- Health Check ---")
    resp = requests.get(f"{BASE_URL}/health", auth=AUTH)
    print(f"  Status: {resp.status_code}")
    print(f"  Body:   {resp.json()}")
    return resp.status_code == 200


def create_trace_via_api():
    """Create a trace using the ingestion API."""
    print("\n--- Create Trace (REST API) ---")
    trace_id = str(uuid.uuid4())

    payload = {
        "batch": [
            {
                "id": str(uuid.uuid4()),
                "type": "trace-create",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "body": {
                    "id": trace_id,
                    "name": "api-direct-test",
                    "input": {"message": "What is the meaning of life?"},
                    "output": {"response": "42, according to Douglas Adams."},
                    "userId": "api-test-user",
                    "tags": ["api-test", "direct"],
                    "metadata": {"source": "test_api_direct.py"},
                },
            }
        ],
    }

    resp = requests.post(f"{BASE_URL}/ingestion", json=payload, auth=AUTH, headers=HEADERS)
    print(f"  Status:   {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)}")
    return trace_id


def create_generation_via_api(trace_id: str):
    """Create a generation linked to the trace."""
    print("\n--- Create Generation (REST API) ---")
    gen_id = str(uuid.uuid4())

    payload = {
        "batch": [
            {
                "id": str(uuid.uuid4()),
                "type": "generation-create",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "body": {
                    "id": gen_id,
                    "traceId": trace_id,
                    "name": "llm-call",
                    "model": "gpt-4",
                    "input": [{"role": "user", "content": "What is the meaning of life?"}],
                    "output": "42, according to Douglas Adams.",
                    "usage": {"input": 15, "output": 8, "total": 23},
                    "modelParameters": {"temperature": 0.7, "maxTokens": 256},
                },
            }
        ],
    }

    resp = requests.post(f"{BASE_URL}/ingestion", json=payload, auth=AUTH, headers=HEADERS)
    print(f"  Status:   {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)}")
    return gen_id


def create_score_via_api(trace_id: str):
    """Create a score for the trace."""
    print("\n--- Create Score (REST API) ---")
    payload = {
        "batch": [
            {
                "id": str(uuid.uuid4()),
                "type": "score-create",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "body": {
                    "traceId": trace_id,
                    "name": "accuracy",
                    "value": 0.95,
                    "comment": "Correct and concise answer",
                },
            }
        ],
    }

    resp = requests.post(f"{BASE_URL}/ingestion", json=payload, auth=AUTH, headers=HEADERS)
    print(f"  Status:   {resp.status_code}")
    print(f"  Response: {json.dumps(resp.json(), indent=2)}")


def fetch_traces():
    """List recent traces via the API."""
    print("\n--- Fetch Traces (REST API) ---")
    resp = requests.get(f"{BASE_URL}/traces", auth=AUTH, params={"limit": 5})
    data = resp.json()
    print(f"  Status: {resp.status_code}")
    print(f"  Total traces: {data.get('meta', {}).get('totalItems', 'N/A')}")
    for t in data.get("data", [])[:5]:
        print(f"    - {t['id'][:8]}... name={t.get('name')} tags={t.get('tags')}")


def main():
    if not check_health():
        raise SystemExit("Langfuse is not healthy. Is it running?")

    trace_id = create_trace_via_api()
    create_generation_via_api(trace_id)
    create_score_via_api(trace_id)

    # Give ingestion a moment to process
    print("\nWaiting 2s for ingestion...")
    time.sleep(2)

    fetch_traces()

    print(f"\nAll done! View the trace at {LANGFUSE_HOST}/trace/{trace_id}")


if __name__ == "__main__":
    main()
