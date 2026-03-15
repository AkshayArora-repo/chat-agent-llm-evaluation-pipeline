#!/usr/bin/env python3
"""Run the finalized judge on unlabeled traces and compute corrected metrics with judgy.

This combines HW3 Steps 5 and 6:
  - Step 5: Run judge on new (unlabeled) traces → raw success rate
  - Step 6: Use judgy to correct for judge bias → corrected rate + CI

Usage:
    python scripts/run_full_evaluation.py
"""

import sys
import os
import json
import functools
import time
import numpy as np
import pandas as pd
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from judgy import estimate_success_rate

load_dotenv(override=True)

print = functools.partial(print, flush=True)

# --- Config ---
MAX_WORKERS = 4
TIMEOUT_SECONDS = 120.0

LLM_EXEC_BASE_URL = os.environ.get("LLM_EXEC_BASE_URL", "")
LLM_EXEC_MODEL_PATH = os.environ.get("LLM_EXEC_MODEL_PATH", "")
INTUIT_PRIVATEAUTH_HEADER = os.environ.get("INTUIT_PRIVATEAUTH_HEADER", "")
INTUIT_EXPERIENCE_ID = os.environ.get("INTUIT_EXPERIENCE_ID", "")
INTUIT_ORIGINATING_ASSETALIAS = os.environ.get("INTUIT_ORIGINATING_ASSETALIAS", "")


def call_llm(prompt: str) -> Optional[str]:
    url = f"{LLM_EXEC_BASE_URL.rstrip('/')}/v3/{LLM_EXEC_MODEL_PATH}/chat/completions"
    headers = {
        "Authorization": INTUIT_PRIVATEAUTH_HEADER,
        "Content-Type": "application/json",
        "intuit_experience_id": INTUIT_EXPERIENCE_ID,
        "intuit_originating_assetalias": INTUIT_ORIGINATING_ASSETALIAS,
    }
    payload = {"messages": [{"role": "user", "content": prompt}]}
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"llm-exec {resp.status_code}: {resp.text[:300]}")
    return resp.json()["choices"][0]["message"]["content"].strip()


def judge_single_trace(args: tuple) -> int:
    """Run judge on one trace, return 1 (PASS) or 0 (FAIL)."""
    trace, judge_prompt = args

    formatted = judge_prompt.replace("__QUERY__", str(trace["query"]))
    formatted = formatted.replace("__DIETARY_RESTRICTION__", str(trace["dietary_restriction"]))
    formatted = formatted.replace("__RESPONSE__", str(trace["response"]))

    try:
        raw = call_llm(formatted)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(raw[start:end])
            return 1 if result.get("label", "").upper().strip() == "PASS" else 0
    except Exception:
        pass
    return 0  # default to FAIL on error


def run_judge_on_all(judge_prompt: str, traces: List[Dict[str, Any]]) -> List[int]:
    total = len(traces)
    predictions = []
    errors = 0

    print(f"Running judge on {total} unlabeled traces ({MAX_WORKERS} workers)...")

    tasks = [(trace, judge_prompt) for trace in traces]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(judge_single_trace, t): i for i, t in enumerate(tasks)}
        for future in as_completed(futures):
            pred = future.result()
            predictions.append(pred)
            idx = len(predictions)
            if idx % 25 == 0 or idx == total:
                print(f"  [{idx}/{total}] judged")

    print(f"Done. {sum(predictions)} PASS, {total - sum(predictions)} FAIL")
    return predictions


def main():
    script_dir = Path(__file__).resolve().parent
    hw3_dir = script_dir.parent
    data_dir = hw3_dir / "data"
    results_dir = hw3_dir / "results"

    prompt_path = results_dir / "judge_prompt.txt"
    judgy_path = results_dir / "judgy_test_data.json"
    traces_path = data_dir / "raw_traces_big.csv"

    for p, name in [(prompt_path, "judge prompt"), (judgy_path, "judgy test data"), (traces_path, "big traces")]:
        if not p.exists():
            print(f"ERROR: {p} not found ({name}). Run previous steps first.")
            sys.exit(1)

    print("=" * 60)
    print("Full Evaluation: Judge + judgy Correction")
    print("=" * 60)

    judge_prompt = prompt_path.read_text(encoding="utf-8")
    print(f"Loaded judge prompt ({len(judge_prompt)} chars)")

    with open(judgy_path) as f:
        judgy_data = json.load(f)
    test_labels = judgy_data["test_labels"]
    test_preds = judgy_data["test_preds"]
    print(f"Loaded test set data ({len(test_labels)} examples)")

    df = pd.read_csv(traces_path)
    df = df[df["success"] == True].reset_index(drop=True)
    traces = df.to_dict("records")
    print(f"Loaded {len(traces)} successful traces from {traces_path.name}")

    # --- Step 5: Run judge ---
    start = time.time()
    unlabeled_preds = run_judge_on_all(judge_prompt, traces)
    elapsed = time.time() - start
    print(f"Judge evaluation took {elapsed:.1f}s ({elapsed/len(traces):.1f}s per trace)")

    raw_success_rate = np.mean(unlabeled_preds)
    print(f"\nRaw observed success rate: {raw_success_rate:.3f} ({raw_success_rate*100:.1f}%)")

    # --- Step 6: judgy correction ---
    print("\nApplying judgy correction...")
    theta_hat, lower_bound, upper_bound = estimate_success_rate(
        test_labels=test_labels,
        test_preds=test_preds,
        unlabeled_preds=unlabeled_preds,
    )

    correction = theta_hat - raw_success_rate

    print(f"\n{'=' * 60}")
    print("FINAL RESULTS")
    print(f"{'=' * 60}")
    print(f"Traces evaluated:         {len(traces)}")
    print(f"Raw observed success rate: {raw_success_rate:.3f} ({raw_success_rate*100:.1f}%)")
    print(f"Corrected success rate:    {theta_hat:.3f} ({theta_hat*100:.1f}%)")
    print(f"95% Confidence Interval:   [{lower_bound:.3f}, {upper_bound:.3f}]")
    print(f"                           [{lower_bound*100:.1f}%, {upper_bound*100:.1f}%]")
    print(f"Correction applied:        {correction:+.3f} ({correction*100:+.1f} pp)")

    # --- Save ---
    results = {
        "final_evaluation": {
            "total_traces_evaluated": len(traces),
            "raw_observed_success_rate": float(raw_success_rate),
            "corrected_success_rate": float(theta_hat),
            "confidence_interval_95": {
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
            },
            "correction_applied": float(correction),
            "judge_metrics_used": {
                "tpr": float(np.mean([1 if tl == tp else 0 for tl, tp in zip(test_labels, test_preds) if tl == 1]) if any(tl == 1 for tl in test_labels) else 0),
                "tnr": float(np.mean([1 if tl == tp else 0 for tl, tp in zip(test_labels, test_preds) if tl == 0]) if any(tl == 0 for tl in test_labels) else 0),
            },
        }
    }

    eval_path = results_dir / "final_evaluation.json"
    with open(eval_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved → {eval_path}")

    preds_path = results_dir / "full_predictions.json"
    pred_details = [
        {
            "trace_id": traces[i].get("trace_id", i),
            "dietary_restriction": traces[i]["dietary_restriction"],
            "predicted_label": "PASS" if unlabeled_preds[i] == 1 else "FAIL",
        }
        for i in range(len(traces))
    ]
    with open(preds_path, "w") as f:
        json.dump(pred_details, f, indent=2)
    print(f"Saved → {preds_path}")

    print(f"\n{'=' * 60}")
    print("DONE. These are your final homework numbers.")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
