"""
Quick test harness to call the LLM text-to-SQL generator with guardrails.

Usage (from repo root, with backend venv activated and Ollama running):
    cd backend
    PYTHONPATH=. python scripts/test_generate_sql.py

Environment:
    LLM_PROVIDER=ollama
    OLLAMA_BASE_URL=http://127.0.0.1:11434
    OLLAMA_MODEL=llama3  # or any pulled model
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List

# Ensure backend package is importable when run as a script
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm.llm_client import LLMClient  # noqa: E402


EXAMPLE_QA: List[str] = [
    "What are the top 5 pickup zones by trip count in the last 30 days?",
    "Show daily trips for Uber vs Lyft over the last 7 days.",
    "Average trip miles by borough for the last 14 days.",
]


async def main():
    client = LLMClient()
    print(f"Provider={client.provider}, model={client.ollama_model if client.provider == 'ollama' else ''}")

    # Focus on the first example only for now
    questions = [
        "Show hourly trips by company for the first 3 days of January 2023.",
    ]

    # Optionally prepend a few exemplar questions to bias the model (acts like few-shot).
    preface = "Here are examples of the kinds of analytics users ask:\n- " + "\n- ".join(EXAMPLE_QA) + "\n\nNow answer this new question: "

    for q in questions:
        print("\n===================================================")
        print("User question:", q)
        augmented_q = preface + q
        raw_response = None
        try:
            result = await client.generate_sql(augmented_q, max_attempts=1)
            if result:
                raw_response = result.get("raw_response")
        except Exception as e:
            import traceback
            print("Error calling LLM:", repr(e))
            traceback.print_exc()
            raw_response = getattr(e, "args", [None])[0] or raw_response
            result = None

        sql_text = result.get("sql") if result else None

        # Terminal output in the requested format
        print("Question:", q)
        print("SQL:")
        print(sql_text or "(no SQL parsed)")

        # Write minimal debug payload (question + raw response)
        out_path = ROOT / "scripts" / "last_generated_sql.json"
        payload = {
            "question": q,
            "raw_response": raw_response,
        }
        import json
        out_path.write_text(json.dumps(payload, indent=2))
        print(f"Wrote debug payload to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())

