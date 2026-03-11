#!/usr/bin/env python3
"""
Continuously stream realistic traces into Langfuse at a configurable rate.
Useful for testing dashboards, alerts, and real-time features.

Usage:
    python scripts/stream_test_data.py                     # 1 trace/sec, run forever
    python scripts/stream_test_data.py --rate 5 --limit 200  # 5/sec, stop after 200
"""

import argparse
import os
import random
import signal
import sys
import time

from dotenv import load_dotenv
from faker import Faker
from langfuse import Langfuse

load_dotenv()

fake = Faker()

LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

MODELS = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet"]
SCENARIOS = [
    {
        "name": "chatbot",
        "prompts": [
            "Hello, how can I reset my password?",
            "What are your business hours?",
            "I want to cancel my subscription.",
            "Can you help me track my order?",
        ],
    },
    {
        "name": "code-assistant",
        "prompts": [
            "Write a binary search in Rust.",
            "Refactor this function to use async/await.",
            "Explain this regex: ^(?=.*[A-Z])(?=.*\\d).{8,}$",
            "Add type hints to this Python code.",
        ],
    },
    {
        "name": "document-qa",
        "prompts": [
            "What was the revenue in Q3?",
            "Summarize the key risks section.",
            "Who are the board members listed?",
            "What's the net income trend?",
        ],
    },
    {
        "name": "content-gen",
        "prompts": [
            "Write a product description for wireless earbuds.",
            "Generate 5 blog title ideas about sustainable living.",
            "Create an email subject line for a flash sale.",
            "Write a social media caption for a coffee shop.",
        ],
    },
]

shutdown = False


def handle_signal(sig, frame):
    global shutdown
    print("\nShutting down gracefully...")
    shutdown = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


def create_client() -> Langfuse:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        raise SystemExit(
            "ERROR: Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env"
        )
    return Langfuse(public_key=public_key, secret_key=secret_key, host=LANGFUSE_HOST)


def emit_trace(langfuse: Langfuse, seq: int):
    scenario = random.choice(SCENARIOS)
    model = random.choice(MODELS)
    prompt = random.choice(scenario["prompts"])
    input_tokens = random.randint(30, 1500)
    output_tokens = random.randint(20, 1200)
    latency = random.uniform(0.1, 4.0)

    # Simulate occasional errors
    is_error = random.random() < 0.05
    status = "error" if is_error else "default"
    response = "Internal server error: model timeout" if is_error else fake.paragraph(nb_sentences=3)

    trace = langfuse.trace(
        name=scenario["name"],
        input={"message": prompt},
        output={"response": response} if not is_error else {"error": response},
        user_id=f"user-{random.randint(1, 100)}",
        session_id=f"stream-session-{random.randint(1, 30)}",
        tags=["streaming-test", scenario["name"]],
        metadata={
            "seq": seq,
            "environment": random.choice(["prod", "staging", "dev"]),
            "region": random.choice(["us-east-1", "eu-west-1", "ap-southeast-1"]),
        },
    )

    # Multi-step generation with parent span
    span = trace.span(name="inference-pipeline")

    # Preprocessing
    pre = span.span(name="preprocessing", input={"raw": prompt})
    pre.end(output={"processed": prompt.lower().strip()})

    # LLM call
    gen = span.generation(
        name="llm-call",
        model=model,
        input=[{"role": "user", "content": prompt}],
        output=response,
        usage={"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens},
        model_parameters={"temperature": round(random.uniform(0, 1), 2)},
        level="ERROR" if is_error else "DEFAULT",
        status_message=response if is_error else None,
    )
    gen.end()

    span.end()

    # Scores
    if not is_error:
        trace.score(name="quality", value=round(random.uniform(0.3, 1.0), 2))
        if random.random() > 0.6:
            trace.score(name="user-feedback", value=random.choice([0, 1]))

    return scenario["name"]


def main():
    parser = argparse.ArgumentParser(description="Stream test traces into Langfuse")
    parser.add_argument("--rate", type=float, default=1.0, help="Traces per second")
    parser.add_argument("--limit", type=int, default=0, help="Max traces (0 = unlimited)")
    args = parser.parse_args()

    langfuse = create_client()
    interval = 1.0 / args.rate
    count = 0

    print(f"Streaming traces to {LANGFUSE_HOST} at {args.rate}/sec ...")
    print("Press Ctrl+C to stop.\n")

    while not shutdown:
        if args.limit and count >= args.limit:
            break

        scenario_name = emit_trace(langfuse, count)
        count += 1

        if count % 10 == 0:
            langfuse.flush()
            print(f"  [{count}] traces sent (last: {scenario_name})")

        time.sleep(interval)

    langfuse.flush()
    print(f"\nDone. Sent {count} traces total.")


if __name__ == "__main__":
    main()
