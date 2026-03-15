#!/usr/bin/env python3
"""Generate fresh Recipe Bot traces in parallel batches.

Usage (run all 4 in separate terminals simultaneously):
    python scripts/generate_traces_big.py --batch 1
    python scripts/generate_traces_big.py --batch 2
    python scripts/generate_traces_big.py --batch 3
    python scripts/generate_traces_big.py --batch 4

Then merge:
    python scripts/generate_traces_big.py --merge
"""

import sys
import os
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import functools

print = functools.partial(print, flush=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils import get_agent_response

TRACES_PER_QUERY = 9
MAX_WORKERS = 4
TOTAL_BATCHES = 4


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


def run_batch(batch_num: int, all_queries: List[Dict[str, Any]], data_dir: Path):
    queries_per_batch = len(all_queries) // TOTAL_BATCHES
    start_idx = (batch_num - 1) * queries_per_batch
    end_idx = start_idx + queries_per_batch if batch_num < TOTAL_BATCHES else len(all_queries)
    batch_queries = all_queries[start_idx:end_idx]

    output_path = data_dir / f"raw_traces_batch_{batch_num}.csv"

    print(f"Batch {batch_num}: queries {start_idx+1}-{end_idx} ({len(batch_queries)} queries x {TRACES_PER_QUERY} runs = {len(batch_queries)*TRACES_PER_QUERY} traces)")

    tasks = []
    for q in batch_queries:
        for run in range(1, TRACES_PER_QUERY + 1):
            tasks.append((q, run))

    total = len(tasks)
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
                print(f"  [batch {batch_num}] [{i}/{total}] {status} | {trace['trace_id']} | {rate:.1f}/s | ETA {eta:.0f}s")

    successes = [t for t in all_traces if t["success"]]
    failures = [t for t in all_traces if not t["success"]]

    df = pd.DataFrame(successes)
    df.to_csv(output_path, index=False)

    elapsed = time.time() - start
    print(f"\nBatch {batch_num} done in {elapsed:.1f}s — {len(successes)} OK, {len(failures)} failed → {output_path.name}")

    if failures:
        for f in failures[:3]:
            print(f"  FAILED: {f['trace_id']}: {f['error'][:100]}")


def merge_batches(data_dir: Path):
    dfs = []
    for b in range(1, TOTAL_BATCHES + 1):
        path = data_dir / f"raw_traces_batch_{b}.csv"
        if not path.exists():
            print(f"ERROR: {path.name} not found. Run batch {b} first.")
            return
        df = pd.read_csv(path)
        dfs.append(df)
        print(f"  Loaded {path.name}: {len(df)} traces")

    merged = pd.concat(dfs, ignore_index=True)
    output_path = data_dir / "raw_traces_big.csv"
    merged.to_csv(output_path, index=False)
    print(f"\nMerged {len(merged)} traces → {output_path}")
    print(f"  PASS (success=True): {merged['success'].sum()}")


def main():
    parser = argparse.ArgumentParser(description="Generate traces in parallel batches")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--batch", type=int, choices=[1, 2, 3, 4], help="Batch number to run")
    group.add_argument("--merge", action="store_true", help="Merge all batch CSVs into one")
    args = parser.parse_args()

    hw3_dir = Path(__file__).resolve().parent.parent
    data_dir = hw3_dir / "data"
    queries_path = data_dir / "dietary_queries.csv"

    if args.merge:
        print("Merging batch files...")
        merge_batches(data_dir)
        return

    all_queries = load_queries(queries_path)
    print(f"Loaded {len(all_queries)} queries total")
    run_batch(args.batch, all_queries, data_dir)


if __name__ == "__main__":
    main()
