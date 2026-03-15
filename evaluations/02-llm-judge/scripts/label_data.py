#!/usr/bin/env python3
"""Pre-label our raw traces for dietary adherence using llm-exec (Gemini 2.5 Pro).

Reads raw_traces.csv, sends each trace to the LLM for PASS/FAIL labeling,
and writes results to labeled_traces.csv.

NOTE: These are pre-labels for manual review, NOT final ground truth.
"""

import sys
import os
import json
import pandas as pd
import functools
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import httpx

load_dotenv(override=True)

print = functools.partial(print, flush=True)

MAX_WORKERS = 4  # conservative to avoid 429s

LLM_EXEC_BASE_URL = os.environ.get("LLM_EXEC_BASE_URL", "")
LLM_EXEC_MODEL_PATH = os.environ.get("LLM_EXEC_MODEL_PATH", "")
INTUIT_PRIVATEAUTH_HEADER = os.environ.get("INTUIT_PRIVATEAUTH_HEADER", "")
INTUIT_EXPERIENCE_ID = os.environ.get("INTUIT_EXPERIENCE_ID", "")
INTUIT_ORIGINATING_ASSETALIAS = os.environ.get("INTUIT_ORIGINATING_ASSETALIAS", "")

LABELING_PROMPT = """You are an expert nutritionist and dietary specialist. Your task is to evaluate whether a recipe response properly adheres to the specified dietary restriction.

DIETARY RESTRICTION DEFINITIONS:
- Vegan: No animal products (meat, dairy, eggs, honey, etc.)
- Vegetarian: No meat or fish, but dairy and eggs are allowed
- Gluten-free: No wheat, barley, rye, or other gluten-containing grains
- Dairy-free: No milk, cheese, butter, yogurt, or other dairy products
- Keto: Very low carb (typically <20g net carbs), high fat, moderate protein
- Paleo: No grains, legumes, dairy, refined sugar, or processed foods
- Pescatarian: No meat except fish and seafood
- Kosher: Follows Jewish dietary laws (no pork, shellfish, mixing meat/dairy)
- Halal: Follows Islamic dietary laws (no pork, alcohol, proper slaughter)
- Nut-free: No tree nuts or peanuts
- Low-carb: Significantly reduced carbohydrates (typically <50g per day)
- Sugar-free: No added sugars or high-sugar ingredients
- Raw vegan: Vegan foods not heated above 118F (48C)
- Whole30: No grains, dairy, legumes, sugar, alcohol, or processed foods
- Diabetic-friendly: Low glycemic index, controlled carbohydrates
- Low-sodium: Reduced sodium content for heart health

EVALUATION CRITERIA:
- PASS: The recipe clearly adheres to the dietary restriction with appropriate ingredients and preparation methods
- FAIL: The recipe contains ingredients or methods that violate the dietary restriction
- Consider both explicit ingredients AND optional add-ons/toppings suggested
- "Optional" non-compliant ingredients still count as FAIL (e.g., "optional cheese topping" on a dairy-free recipe)
- Be strict but reasonable

Query: {query}
Dietary Restriction: {dietary_restriction}
Recipe Response: {response}

Respond ONLY with valid JSON (no markdown, no extra text):
{{"reasoning": "your detailed explanation citing specific ingredients or methods", "label": "PASS" or "FAIL", "confidence": "HIGH" or "MEDIUM" or "LOW"}}"""


def call_llm(prompt: str) -> Optional[str]:
    url = f"{LLM_EXEC_BASE_URL.rstrip('/')}/v3/{LLM_EXEC_MODEL_PATH}/chat/completions"
    headers = {
        "Authorization": INTUIT_PRIVATEAUTH_HEADER,
        "Content-Type": "application/json",
        "intuit_experience_id": INTUIT_EXPERIENCE_ID,
        "intuit_originating_assetalias": INTUIT_ORIGINATING_ASSETALIAS,
    }
    payload = {"messages": [{"role": "user", "content": prompt}]}
    with httpx.Client(timeout=90.0) as client:
        resp = client.post(url, headers=headers, json=payload)
    if resp.status_code >= 400:
        raise RuntimeError(f"llm-exec {resp.status_code}: {resp.text[:200]}")
    return resp.json()["choices"][0]["message"]["content"].strip()


def parse_label_response(text: str) -> Optional[Dict[str, Any]]:
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, IndexError):
        pass
    return None


def label_one(trace: Dict[str, Any]) -> Dict[str, Any]:
    prompt = LABELING_PROMPT.format(
        query=trace["query"],
        dietary_restriction=trace["dietary_restriction"],
        response=trace["response"],
    )
    result = trace.copy()
    try:
        raw = call_llm(prompt)
        parsed = parse_label_response(raw)
        if parsed:
            result["label"] = parsed.get("label", "UNKNOWN")
            result["reasoning"] = parsed.get("reasoning", "")
            result["confidence"] = parsed.get("confidence", "UNKNOWN")
            result["labeled"] = True
        else:
            result["label"] = "PARSE_ERROR"
            result["reasoning"] = raw[:500] if raw else ""
            result["confidence"] = "UNKNOWN"
            result["labeled"] = False
    except Exception as e:
        result["label"] = "ERROR"
        result["reasoning"] = str(e)[:300]
        result["confidence"] = "UNKNOWN"
        result["labeled"] = False
    return result


def main():
    hw3_dir = Path(__file__).resolve().parent.parent
    input_path = hw3_dir / "data" / "raw_traces.csv"
    output_path = hw3_dir / "data" / "labeled_traces.csv"

    df = pd.read_csv(input_path)
    traces = df.to_dict("records")
    total = len(traces)
    print(f"Loaded {total} traces from {input_path.name}")
    print(f"Labeling all {total} traces with llm-exec, workers={MAX_WORKERS}")

    labeled: List[Dict[str, Any]] = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(label_one, t): t for t in traces}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            labeled.append(result)
            if i % 10 == 0 or i == total:
                elapsed = time.time() - start
                rate = i / elapsed if elapsed > 0 else 0
                eta = (total - i) / rate if rate > 0 else 0
                lbl = result.get("label", "?")
                conf = result.get("confidence", "?")
                print(f"  [{i}/{total}] {lbl} ({conf}) | trace_id={result.get('trace_id','')} | {rate:.2f}/s | ETA {eta:.0f}s")

    out_df = pd.DataFrame(labeled)
    out_df.to_csv(output_path, index=False)

    elapsed = time.time() - start
    success_count = out_df[out_df["labeled"] == True].shape[0]
    fail_labels = out_df[out_df["label"] == "FAIL"].shape[0]
    pass_labels = out_df[out_df["label"] == "PASS"].shape[0]

    print(f"\nDone in {elapsed:.1f}s")
    print(f"  Successfully labeled: {success_count}/{total}")
    print(f"  PASS: {pass_labels}, FAIL: {fail_labels}")
    print(f"  Saved to: {output_path}")


if __name__ == "__main__":
    main()
