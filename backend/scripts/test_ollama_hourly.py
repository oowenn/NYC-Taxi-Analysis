"""
Small standalone script to:

1. Initialize DuckDB using the same setup as the backend.
2. Run a small, aggregated "hourly trips by company" query over a short window.
3. Feed the aggregated result to a local Ollama model for a natural-language summary.

Usage (from project root, with backend venv activated):

    cd backend
    source venv/bin/activate
    python scripts/test_ollama_hourly.py

Requirements:
    - Parquet + CSV files in ../data (same as backend).
    - Ollama running locally (e.g. `ollama serve`) with a model pulled, e.g.:
        ollama pull llama2
"""

import os
from textwrap import shorten

import duckdb as db
import pandas as pd
import ollama

from db.duckdb_setup import init_duckdb, close_duckdb
from query.metrics import MetricTemplates
from query.engine import QueryEngine


def run_hourly_template_sample(conn: db.DuckDBPyConnection) -> pd.DataFrame:
    """
    Run a smaller, time-bounded version of the hourly_trips_by_company template
    to keep the result compact for LLM prompting.
    """
    # Restrict to one week of data to keep things small but interesting
    sql = """
        SELECT
            DATE_TRUNC('hour', pickup_datetime) AS pickup_hour,
            company,
            COUNT(*) AS trips
        FROM fhv_with_company
        WHERE pickup_datetime >= '2023-01-01' AND pickup_datetime < '2023-01-08'
        GROUP BY pickup_hour, company
        ORDER BY pickup_hour, company
    """

    print("Running sample hourly_trips_by_company query over 2023-01-01 .. 2023-01-07")
    df = conn.execute(sql).fetchdf()
    print(f"Query returned {len(df)} rows")
    return df


def format_df_for_prompt(df: pd.DataFrame, max_rows: int = 80) -> str:
    """
    Format a dataframe as a small CSV snippet for the prompt.
    """
    if len(df) > max_rows:
        df = df.head(max_rows)

    csv_text = df.to_csv(index=False)
    return csv_text


def build_prompt(csv_table: str) -> str:
    """
    Build a natural language prompt that gives the table as context and asks
    the model a couple of simple analytical questions.
    """
    prompt = f"""
You are a data analyst looking at NYC high volume for-hire vehicle (FHVHV) trips.

You are given an excerpt of an aggregated table in CSV format. Each row has:
  - pickup_hour: hour bucket (timestamp truncated to hour)
  - company: ridehail company (e.g., Uber, Lyft, Via, Other)
  - trips: number of trips in that hour for that company

Here is the table (CSV):

{csv_table}

Based ONLY on this table:

1. Which company appears to have the highest total trips in this sample week?
2. Roughly at what hours does that company peak (give 1–2 key hours or ranges)?
3. Mention any obvious patterns you see (time-of-day differences between companies), in 3–5 short bullet points.

Be concise and only refer to what is visible in the table.
"""
    return prompt.strip()


def chat_with_ollama(prompt: str) -> str:
    """
    Send the prompt to a local Ollama model and return the response text.
    """
    model = os.getenv("OLLAMA_MODEL", "llama3")

    print(f"\nCalling Ollama model '{model}' ...")
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return (
            "Error calling Ollama. Make sure ollama is running and the model is pulled.\n"
            f"Details: {e}"
        )

    message = response.get("message", {})
    content = message.get("content", "").strip()
    return content or "(No content returned from model)"


def main():
    # Initialize DuckDB and views
    conn = init_duckdb()

    try:
        # Run a small aggregate query
        df = run_hourly_template_sample(conn)
        if df.empty:
            print("No rows returned from sample query. Check your data time range.")
            return

        # Prepare table for the LLM prompt
        csv_snippet = format_df_for_prompt(df)
        prompt = build_prompt(csv_snippet)

        # Optionally print a shortened preview of the prompt
        print("\n--- Prompt preview (first 600 chars) ---")
        print(shorten(prompt, width=600, placeholder="..."))
        print("----------------------------------------")

        # Call Ollama
        answer = chat_with_ollama(prompt)

        print("\n=== Ollama answer ===")
        print(answer)
        print("=====================\n")
    finally:
        close_duckdb(conn)


if __name__ == "__main__":
    main()


