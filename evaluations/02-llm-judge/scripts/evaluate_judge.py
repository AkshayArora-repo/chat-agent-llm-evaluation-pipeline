#!/usr/bin/env python3
"""Evaluate the LLM judge on dev or test set using llm-exec.

Usage:
    python scripts/evaluate_judge.py --split dev    # iterate on dev
    python scripts/evaluate_judge.py --split test   # final measurement
"""

import sys
import os
import json
import argparse
import functools
import time
import pandas as pd
import httpx
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

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


# --- LLM call (reused from label_data.py) ---

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


def parse_judge_response(text: str) -> Tuple[str, str]:
    """Parse the judge's JSON response into (label, reasoning).
    Returns ("UNKNOWN", error_msg) on parse failure."""
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            inner = text.split("```")[1].split("```")[0].strip()
            if "{" in inner:
                text = inner
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            result = json.loads(text[start:end])
            label = result.get("label", "UNKNOWN").upper().strip()
            reasoning = result.get("reasoning", "")
            return label, reasoning
    except (json.JSONDecodeError, IndexError):
        pass
    return "UNKNOWN", f"Failed to parse: {text[:200]}"


# --- Single trace evaluation ---

def evaluate_single_trace(trace: Dict[str, Any], judge_prompt: str) -> Dict[str, Any]:
    query = trace["query"]
    dietary_restriction = trace["dietary_restriction"]
    response = trace["response"]
    true_label = trace["label"]

    formatted_prompt = judge_prompt.replace("__QUERY__", str(query))
    formatted_prompt = formatted_prompt.replace("__DIETARY_RESTRICTION__", str(dietary_restriction))
    formatted_prompt = formatted_prompt.replace("__RESPONSE__", str(response))

    try:
        raw_response = call_llm(formatted_prompt)
        predicted_label, reasoning = parse_judge_response(raw_response)

        return {
            "trace_id": trace.get("trace_id", "unknown"),
            "query": query,
            "dietary_restriction": dietary_restriction,
            "true_label": true_label,
            "predicted_label": predicted_label,
            "reasoning": reasoning,
            "success": True,
        }
    except Exception as e:
        return {
            "trace_id": trace.get("trace_id", "unknown"),
            "query": query,
            "dietary_restriction": dietary_restriction,
            "true_label": true_label,
            "predicted_label": "ERROR",
            "reasoning": f"Error: {str(e)}",
            "success": False,
        }


# --- Parallel evaluation ---

def evaluate_all(judge_prompt: str, traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    total = len(traces)
    predictions = []
    errors = 0

    print(f"Evaluating {total} traces with {MAX_WORKERS} workers...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(evaluate_single_trace, trace, judge_prompt): i
            for i, trace in enumerate(traces)
        }
        for future in as_completed(futures):
            result = future.result()
            predictions.append(result)

            idx = len(predictions)
            if not result["success"]:
                errors += 1
                print(f"  [{idx}/{total}] ERROR trace {result['trace_id']}: {result['reasoning'][:80]}")
            elif idx % 10 == 0 or idx == total:
                print(f"  [{idx}/{total}] evaluated")

    print(f"Done. {total - errors}/{total} succeeded, {errors} errors.")
    return predictions


# --- Metrics ---

def compute_metrics(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [p for p in predictions if p["predicted_label"] in ("PASS", "FAIL")]

    tp = sum(1 for p in valid if p["true_label"] == "PASS" and p["predicted_label"] == "PASS")
    fn = sum(1 for p in valid if p["true_label"] == "PASS" and p["predicted_label"] == "FAIL")
    tn = sum(1 for p in valid if p["true_label"] == "FAIL" and p["predicted_label"] == "FAIL")
    fp = sum(1 for p in valid if p["true_label"] == "FAIL" and p["predicted_label"] == "PASS")

    tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.0

    skipped = len(predictions) - len(valid)

    return {
        "true_positive_rate": tpr,
        "true_negative_rate": tnr,
        "balanced_accuracy": (tpr + tnr) / 2,
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "total_valid": len(valid),
        "total_skipped": skipped,
    }


def print_error_analysis(predictions: List[Dict[str, Any]]) -> None:
    false_positives = [p for p in predictions if p["true_label"] == "FAIL" and p["predicted_label"] == "PASS"]
    false_negatives = [p for p in predictions if p["true_label"] == "PASS" and p["predicted_label"] == "FAIL"]

    print(f"\n{'='*60}")
    print("ERROR ANALYSIS")
    print(f"{'='*60}")
    print(f"False Positives (judge=PASS, truth=FAIL): {len(false_positives)}  ← DANGEROUS: missed violations")
    print(f"False Negatives (judge=FAIL, truth=PASS): {len(false_negatives)}  ← ANNOYING: falsely rejected good recipes")

    if false_positives:
        print(f"\n--- FALSE POSITIVES (judge missed these violations) ---")
        for i, fp in enumerate(false_positives, 1):
            print(f"\n  FP #{i} | trace_id: {fp['trace_id']} | diet: {fp['dietary_restriction']}")
            print(f"  Query: {fp['query'][:100]}")
            print(f"  Judge reasoning: {fp['reasoning'][:200]}")

    if false_negatives:
        print(f"\n--- FALSE NEGATIVES (judge falsely rejected these) ---")
        for i, fn_item in enumerate(false_negatives, 1):
            print(f"\n  FN #{i} | trace_id: {fn_item['trace_id']} | diet: {fn_item['dietary_restriction']}")
            print(f"  Query: {fn_item['query'][:100]}")
            print(f"  Judge reasoning: {fn_item['reasoning'][:200]}")

    if not false_positives and not false_negatives:
        print("\n  No errors! Perfect agreement with ground truth.")


# --- Save results ---

def save_results(split_name: str, metrics: Dict[str, Any],
                 predictions: List[Dict[str, Any]], results_dir: Path) -> None:

    perf = {f"{split_name}_set_performance": metrics}
    perf_path = results_dir / f"judge_performance_{split_name}.json"
    with open(perf_path, "w") as f:
        json.dump(perf, f, indent=2)
    print(f"\nSaved metrics     → {perf_path}")

    preds_path = results_dir / f"{split_name}_predictions.json"
    preds_clean = []
    for p in predictions:
        preds_clean.append({
            "trace_id": p["trace_id"],
            "query": p["query"][:150],
            "dietary_restriction": p["dietary_restriction"],
            "true_label": p["true_label"],
            "predicted_label": p["predicted_label"],
            "reasoning": p["reasoning"],
        })
    with open(preds_path, "w") as f:
        json.dump(preds_clean, f, indent=2)
    print(f"Saved predictions → {preds_path}")

    if split_name == "test":
        judgy_data = {
            "test_labels": [1 if p["true_label"] == "PASS" else 0 for p in predictions],
            "test_preds": [1 if p["predicted_label"] == "PASS" else 0 for p in predictions],
        }
        judgy_path = results_dir / "judgy_test_data.json"
        with open(judgy_path, "w") as f:
            json.dump(judgy_data, f, indent=2)
        print(f"Saved judgy data  → {judgy_path}")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM judge on dev or test set")
    parser.add_argument("--split", choices=["dev", "test"], required=True,
                        help="Which data split to evaluate against")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    hw3_dir = script_dir.parent
    data_dir = hw3_dir / "data"
    results_dir = hw3_dir / "results"

    csv_path = data_dir / f"{args.split}_set.csv"
    prompt_path = results_dir / "judge_prompt.txt"

    if not csv_path.exists():
        print(f"ERROR: {csv_path} not found. Run split_data.py first.")
        sys.exit(1)
    if not prompt_path.exists():
        print(f"ERROR: {prompt_path} not found.")
        sys.exit(1)

    print(f"{'='*60}")
    print(f"LLM Judge Evaluation — {args.split.upper()} set")
    print(f"{'='*60}")

    judge_prompt = prompt_path.read_text(encoding="utf-8")
    print(f"Loaded judge prompt ({len(judge_prompt)} chars)")

    df = pd.read_csv(csv_path)
    traces = df.to_dict("records")
    n_pass = sum(1 for t in traces if t["label"] == "PASS")
    n_fail = sum(1 for t in traces if t["label"] == "FAIL")
    print(f"Loaded {len(traces)} traces from {csv_path.name} ({n_pass} PASS, {n_fail} FAIL)")

    start = time.time()
    predictions = evaluate_all(judge_prompt, traces)
    elapsed = time.time() - start
    print(f"Evaluation took {elapsed:.1f}s ({elapsed/len(traces):.1f}s per trace)")

    metrics = compute_metrics(predictions)

    print(f"\n{'='*60}")
    print(f"RESULTS — {args.split.upper()} SET")
    print(f"{'='*60}")
    print(f"TPR (True Positive Rate):  {metrics['true_positive_rate']:.3f}  ({metrics['tp']} TP, {metrics['fn']} FN)")
    print(f"TNR (True Negative Rate):  {metrics['true_negative_rate']:.3f}  ({metrics['tn']} TN, {metrics['fp']} FP)")
    print(f"Balanced Accuracy:         {metrics['balanced_accuracy']:.3f}")
    if metrics["total_skipped"] > 0:
        print(f"Skipped (parse errors):    {metrics['total_skipped']}")

    print_error_analysis(predictions)
    save_results(args.split, metrics, predictions, results_dir)

    print(f"\n{'='*60}")
    if args.split == "dev":
        print("Dev run complete. Review errors above.")
        print("If satisfied, run: python scripts/evaluate_judge.py --split test")
        print("If not, tweak judge_prompt.txt and re-run with --split dev")
    else:
        print("TEST RUN COMPLETE. These are your final numbers.")
        print("Do NOT re-run on test. Use these TPR/TNR for Step 6 (judgy).")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
