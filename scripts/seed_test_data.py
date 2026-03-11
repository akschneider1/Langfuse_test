#!/usr/bin/env python3
"""
Seed Langfuse with realistic test data — traces, spans, generations, scores, and events.
Run after creating a project in the Langfuse UI and setting your API keys in .env.

Usage:
    python scripts/seed_test_data.py              # 20 traces (default)
    python scripts/seed_test_data.py --count 100  # 100 traces
"""

import argparse
import os
import random
import time
from datetime import datetime, timedelta

from dotenv import load_dotenv
from faker import Faker
from langfuse import Langfuse

load_dotenv()

fake = Faker()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3000")

MODELS = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus", "claude-3-sonnet", "llama-3-70b"]
USE_CASES = [
    "customer-support-chat",
    "code-generation",
    "summarization",
    "rag-qa",
    "translation",
    "content-moderation",
]
TAGS = ["production", "staging", "experiment", "a/b-test", "baseline"]

SAMPLE_PROMPTS = [
    "Explain quantum computing in simple terms.",
    "Write a Python function to merge two sorted lists.",
    "Summarize the following document: {doc}",
    "Translate the following English text to French: {text}",
    "Is the following user message harmful? Respond yes or no: {msg}",
    "Based on the retrieved context, answer the user's question: {question}",
]

SAMPLE_RESPONSES = [
    "Quantum computing uses qubits that can be in superposition, allowing computations on many states simultaneously.",
    "```python\ndef merge(a, b):\n    result = []\n    i = j = 0\n    while i < len(a) and j < len(b):\n        if a[i] <= b[j]:\n            result.append(a[i]); i += 1\n        else:\n            result.append(b[j]); j += 1\n    return result + a[i:] + b[j:]\n```",
    "The document discusses recent advances in renewable energy, focusing on solar panel efficiency improvements.",
    "L'informatique quantique utilise des qubits qui peuvent exister en superposition.",
    "No, the message is not harmful.",
    "Based on the context, the answer is: The company was founded in 2015 and is headquartered in San Francisco.",
]


def create_langfuse_client() -> Langfuse:
    if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
        raise SystemExit(
            "ERROR: Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env "
            "(copy .env.example to .env and fill in values from the Langfuse UI)."
        )
    return Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )


def random_metadata():
    return {
        "user_id": fake.uuid4(),
        "session_id": fake.uuid4(),
        "user_agent": fake.user_agent(),
        "ip_country": fake.country_code(),
    }


def seed_trace(langfuse: Langfuse, index: int):
    """Create one rich trace with nested spans and a generation."""
    use_case = random.choice(USE_CASES)
    model = random.choice(MODELS)
    prompt = random.choice(SAMPLE_PROMPTS)
    response = random.choice(SAMPLE_RESPONSES)
    latency_ms = random.randint(200, 5000)
    input_tokens = random.randint(50, 2000)
    output_tokens = random.randint(20, 1500)

    trace = langfuse.trace(
        name=use_case,
        input={"message": prompt},
        output={"response": response},
        metadata=random_metadata(),
        tags=random.sample(TAGS, k=random.randint(1, 3)),
        user_id=f"user-{random.randint(1, 50)}",
        session_id=f"session-{random.randint(1, 20)}",
    )

    # --- Top-level span: "pipeline" ---
    pipeline_span = trace.span(
        name="pipeline",
        input={"message": prompt},
        metadata={"use_case": use_case},
    )

    # --- Retrieval span (for RAG use cases) ---
    if use_case == "rag-qa":
        retrieval_span = pipeline_span.span(
            name="retrieval",
            input={"query": prompt},
            output={
                "documents": [
                    {"id": fake.uuid4(), "score": round(random.uniform(0.7, 1.0), 3)}
                    for _ in range(random.randint(1, 5))
                ]
            },
            metadata={"index": "main", "top_k": 5},
        )
        retrieval_span.end()

    # --- LLM generation ---
    generation = pipeline_span.generation(
        name="llm-call",
        model=model,
        model_parameters={"temperature": round(random.uniform(0, 1), 2), "max_tokens": 1024},
        input=[{"role": "user", "content": prompt}],
        output=response,
        usage={
            "input": input_tokens,
            "output": output_tokens,
            "total": input_tokens + output_tokens,
        },
        metadata={"latency_ms": latency_ms},
    )
    generation.end()

    # --- Post-processing span ---
    post_span = pipeline_span.span(
        name="post-processing",
        input={"raw_response": response},
        output={"final_response": response},
    )
    post_span.end()

    pipeline_span.end()

    # --- Scores ---
    trace.score(name="quality", value=round(random.uniform(0, 1), 2))
    trace.score(name="relevance", value=round(random.uniform(0, 1), 2))
    if random.random() > 0.5:
        trace.score(
            name="user-feedback",
            value=random.choice([0, 1]),
            comment=fake.sentence() if random.random() > 0.5 else None,
        )

    if (index + 1) % 10 == 0:
        print(f"  created {index + 1} traces...")


def main():
    parser = argparse.ArgumentParser(description="Seed Langfuse with test data")
    parser.add_argument("--count", type=int, default=20, help="Number of traces to create")
    args = parser.parse_args()

    langfuse = create_langfuse_client()

    print(f"Seeding {args.count} traces to {LANGFUSE_HOST} ...")
    for i in range(args.count):
        seed_trace(langfuse, i)

    # Flush remaining events
    langfuse.flush()
    print(f"Done! {args.count} traces seeded successfully.")
    print(f"View them at {LANGFUSE_HOST}")


if __name__ == "__main__":
    main()
