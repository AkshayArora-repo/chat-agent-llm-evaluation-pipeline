#!/usr/bin/env python3
"""Generate our own Recipe Bot traces for dietary adherence evaluation.

Reads dietary_queries.csv, runs each query through get_agent_response
multiple times, and writes results to raw_traces.csv.
"""

import sys
import os
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import functools

# Force unbuffered print
print = functools.partial(print, flush=True)

# Add project root so we can import backend.utils
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils import get_agent_response

TRACES_PER_QUERY = 5
MAX_WORKERS = 8

def load_queries(csv_path: Path) -> List[Dict[str, Any]]:
    df = pd.read_csv(csv_path)
    return df.to_dict("records")


def generate_single_trace(query: str, dietary_restriction: str) -> Dict[str, Any]:
    messages = [{"role": "user", "content": query}]
    try:
        updated = get_agent_response(messages)
        return {
            "query": query,
            "dietary_restriction": dietary_restriction,
            "response": updated[-1]["content"],
            "success": True,
            "error": None,
        }
    except Exception as e:
        return {
            "query": query,
            "dietary_restriction": dietary_restriction,
            "response": None,
            "success": False,
            "error": str(e),
        }


def generate_trace_with_id(args: tuple) -> Dict[str, Any]:
    query_data, run_num = args
    trace = generate_single_trace(query_data["query"], query_data["dietary_restriction"])
    trace["trace_id"] = f"{query_data['id']}_{run_num}"
    trace["query_id"] = query_data["id"]
    return trace


def main():
    hw3_dir = Path(__file__).resolve().parent.parent
    queries_path = hw3_dir / "data" / "dietary_queries.csv"
    output_path = hw3_dir / "data" / "raw_traces.csv"

    queries = load_queries(queries_path)
    print(f"Loaded {len(queries)} queries from {queries_path.name}")

    tasks = []
    for q in queries:
        for run in range(1, TRACES_PER_QUERY + 1):
            tasks.append((q, run))

    total = len(tasks)
    print(f"Generating {total} traces ({len(queries)} queries x {TRACES_PER_QUERY} runs), workers={MAX_WORKERS}")

    all_traces: List[Dict[str, Any]] = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(generate_trace_with_id, t): t for t in tasks}
        for i, future in enumerate(as_completed(futures), 1):
            trace = future.result()
            all_traces.append(trace)
            if i % 10 == 0 or i == total:
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                status = "OK" if trace["success"] else "FAIL"
                print(f"  [{i}/{total}] {status} | trace_id={trace['trace_id']} | {rate:.1f} traces/s | ETA {eta:.0f}s")

    successes = [t for t in all_traces if t["success"]]
    failures = [t for t in all_traces if not t["success"]]

    df = pd.DataFrame(successes)
    df.to_csv(output_path, index=False)

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")
    print(f"  Successful: {len(successes)}")
    print(f"  Failed:     {len(failures)}")
    print(f"  Saved to:   {output_path}")

    if failures:
        print("\nFailed traces:")
        for f in failures[:5]:
            print(f"  {f['trace_id']}: {f['error'][:100]}")


if __name__ == "__main__":
    main()
