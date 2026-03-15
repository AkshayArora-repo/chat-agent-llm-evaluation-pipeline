#!/usr/bin/env python3
"""Part 3: Query Rewrite Agent — compare baseline BM25 vs agent-enhanced retrieval.

Three rewrite strategies tested against our 193 queries:
  1. keywords  — strip to core search terms only
  2. rewrite   — rephrase for BM25 effectiveness
  3. expand    — add synonyms and related cooking terms

Usage:
    python scripts/evaluate_retrieval_with_agent.py

Output:
    results/retrieval_comparison.json   — side-by-side metrics
    results/agent_enhanced.json         — best strategy detailed results
"""

import os
import sys
import json
import time
import functools
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import httpx

load_dotenv(override=True)
print = functools.partial(print, flush=True)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "backend"))
from retrieval import create_retriever
from evaluation_utils import BaseRetrievalEvaluator, load_queries

# ── llm-exec config ────────────────────────────────────────────────────────────
LLM_EXEC_BASE_URL             = os.environ.get("LLM_EXEC_BASE_URL", "")
LLM_EXEC_MODEL_PATH           = os.environ.get("LLM_EXEC_MODEL_PATH", "")
INTUIT_PRIVATEAUTH_HEADER     = os.environ.get("INTUIT_PRIVATEAUTH_HEADER", "")
INTUIT_EXPERIENCE_ID          = os.environ.get("INTUIT_EXPERIENCE_ID", "")
INTUIT_ORIGINATING_ASSETALIAS = os.environ.get("INTUIT_ORIGINATING_ASSETALIAS", "")

MAX_WORKERS = 4
TIMEOUT     = 45.0


_auth_error_shown = False

def call_llm(prompt: str) -> Optional[str]:
    global _auth_error_shown
    url = f"{LLM_EXEC_BASE_URL.rstrip('/')}/v3/{LLM_EXEC_MODEL_PATH}/chat/completions"
    headers = {
        "Authorization": INTUIT_PRIVATEAUTH_HEADER,
        "Content-Type": "application/json",
        "intuit_experience_id": INTUIT_EXPERIENCE_ID,
        "intuit_originating_assetalias": INTUIT_ORIGINATING_ASSETALIAS,
    }
    try:
        resp = httpx.Client(timeout=TIMEOUT).post(
            url, headers=headers,
            json={"messages": [{"role": "user", "content": prompt}]}
        )
        if resp.status_code == 401:
            if not _auth_error_shown:
                print("\n  ⚠ AUTH EXPIRED (401) — update INTUIT_PRIVATEAUTH_HEADER in .env and rerun")
                _auth_error_shown = True
            return None
        if resp.status_code >= 400:
            print(f"  ⚠ LLM error {resp.status_code}: {resp.text[:100]}")
            return None
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  ⚠ LLM exception: {e}")
        return None


# ── Three rewrite prompts ──────────────────────────────────────────────────────

KEYWORDS_PROMPT = """\
Extract the most important search keywords from this cooking query for a recipe database.
Keep only terms that would appear in recipe titles, ingredients, or instructions.
Remove question words, filler words, and conversational language.
Return keywords space-separated on one line only.

Query: "{query}"

Keywords:"""

REWRITE_PROMPT = """\
Rewrite this cooking question as a concise, effective recipe search query.
- Use specific cooking terms (not vague language)
- Include equipment, ingredients, techniques
- Remove question words — focus on content
- Add the dish type or recipe name if you can infer it
- Keep it under 15 words

Original: "{query}"

Search query:"""

EXPAND_PROMPT = """\
Expand this cooking query with synonyms and related cooking terms to improve recipe search.
- Add alternative names for techniques (e.g. "bake" → "bake roast oven")
- Add related ingredients or equipment
- Include both specific and general terms
- Keep it under 20 words

Original: "{query}"

Expanded query:"""


def rewrite_single(query: str, strategy: str) -> str:
    """Rewrite one query using the given strategy. Returns original on failure."""
    if strategy == "keywords":
        prompt = KEYWORDS_PROMPT.format(query=query)
    elif strategy == "rewrite":
        prompt = REWRITE_PROMPT.format(query=query)
    elif strategy == "expand":
        prompt = EXPAND_PROMPT.format(query=query)
    else:
        return query

    result = call_llm(prompt)
    return result if result and len(result.strip()) > 3 else query


def rewrite_all_queries(queries: List[Dict], strategy: str) -> List[str]:
    """Rewrite all queries in parallel for a given strategy."""
    rewritten = [""] * len(queries)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(rewrite_single, q["query"], strategy): i
                   for i, q in enumerate(queries)}
        done = 0
        for future in as_completed(futures):
            idx = futures[future]
            rewritten[idx] = future.result()
            done += 1
            if done % 25 == 0 or done == len(queries):
                print(f"    [{done}/{len(queries)}] rewritten")

    return rewritten


def evaluate_with_rewritten(retriever, queries: List[Dict],
                             rewritten_queries: List[str],
                             top_k: int = 10) -> List[Dict]:
    """Run BM25 on rewritten queries, compute per-query metrics."""
    results = []
    for q, rq in zip(queries, rewritten_queries):
        retrieved = retriever.retrieve_bm25(rq, top_k=top_k)
        retrieved_ids = [r["id"] for r in retrieved]
        target_id = q["source_recipe_id"]

        def recall_at_k(k):
            return 1 if target_id in retrieved_ids[:k] else 0

        rank = None
        if target_id in retrieved_ids:
            rank = retrieved_ids.index(target_id) + 1

        results.append({
            "original_query":   q["query"],
            "rewritten_query":  rq,
            "target_recipe_id": target_id,
            "target_recipe_name": q["source_recipe_name"],
            "target_rank":      rank,
            "recall_1":         recall_at_k(1),
            "recall_3":         recall_at_k(3),
            "recall_5":         recall_at_k(5),
            "recall_10":        recall_at_k(10),
            "reciprocal_rank":  (1.0 / rank) if rank else 0.0,
        })
    return results


def aggregate(results: List[Dict]) -> Dict:
    n = len(results)
    return {
        "recall_at_1":         sum(r["recall_1"] for r in results) / n,
        "recall_at_3":         sum(r["recall_3"] for r in results) / n,
        "recall_at_5":         sum(r["recall_5"] for r in results) / n,
        "recall_at_10":        sum(r["recall_10"] for r in results) / n,
        "mean_reciprocal_rank": sum(r["reciprocal_rank"] for r in results) / n,
        "queries_found":       sum(1 for r in results if r["target_rank"]),
        "queries_not_found":   sum(1 for r in results if not r["target_rank"]),
        "total_queries":       n,
    }


def print_metrics(label: str, m: Dict):
    print(f"\n  {label}")
    print(f"    Recall@1 : {m['recall_at_1']:.3f}  ({m['recall_at_1']*100:.1f}%)")
    print(f"    Recall@3 : {m['recall_at_3']:.3f}  ({m['recall_at_3']*100:.1f}%)")
    print(f"    Recall@5 : {m['recall_at_5']:.3f}  ({m['recall_at_5']*100:.1f}%)")
    print(f"    Recall@10: {m['recall_at_10']:.3f}  ({m['recall_at_10']*100:.1f}%)")
    print(f"    MRR      : {m['mean_reciprocal_rank']:.3f}")
    print(f"    Found    : {m['queries_found']}/{m['total_queries']}")


def main():
    hw4_dir      = Path(__file__).resolve().parent.parent
    data_dir     = hw4_dir / "data"
    results_dir  = hw4_dir / "results"

    recipes_path = data_dir / "processed_recipes.json"
    index_path   = data_dir / "bm25_index.pkl"
    queries_path = data_dir / "synthetic_queries.json"

    for p, name in [(recipes_path, "processed_recipes.json"),
                    (queries_path, "synthetic_queries.json")]:
        if not p.exists():
            print(f"ERROR: {name} not found"); sys.exit(1)

    # ── Auth check ────────────────────────────────────────────────────────────
    print("Checking llm-exec auth...")
    test = call_llm("Say OK")
    if test is None:
        print("ERROR: LLM auth failed. Update INTUIT_PRIVATEAUTH_HEADER in .env and rerun.")
        sys.exit(1)
    print(f"Auth OK — LLM responded: '{test[:30]}'")

    # Load
    retriever = create_retriever(recipes_path, index_path)
    queries   = load_queries(queries_path)
    print(f"Loaded {len(queries)} queries")

    # ── Baseline (no rewrite) ──────────────────────────────────────────────────
    print("\n[1/4] Baseline BM25 (no rewrite)...")
    evaluator = BaseRetrievalEvaluator(retriever)
    baseline_results = evaluator.evaluate_all_queries(queries, top_k=10)
    baseline_metrics = aggregate(baseline_results)
    print_metrics("BASELINE", baseline_metrics)

    # ── Three rewrite strategies ───────────────────────────────────────────────
    strategy_results = {}
    strategy_metrics = {}

    for strategy in ["keywords", "rewrite", "expand"]:
        print(f"\n[?/4] Strategy: {strategy} — rewriting {len(queries)} queries...")
        start = time.time()
        rewritten = rewrite_all_queries(queries, strategy)
        elapsed = time.time() - start
        print(f"  Rewrite done in {elapsed:.0f}s")

        results = evaluate_with_rewritten(retriever, queries, rewritten, top_k=10)
        metrics = aggregate(results)
        strategy_results[strategy] = results
        strategy_metrics[strategy] = metrics
        print_metrics(f"STRATEGY: {strategy}", metrics)

    # ── Comparison summary ─────────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print("COMPARISON SUMMARY")
    print(f"{'='*65}")
    print(f"{'Strategy':<12} {'R@1':>6} {'R@3':>6} {'R@5':>6} {'R@10':>6} {'MRR':>6} {'Found':>8}")
    print(f"{'-'*65}")

    all_metrics = {"baseline": baseline_metrics, **strategy_metrics}
    for name, m in all_metrics.items():
        found_str = f"{m['queries_found']}/{m['total_queries']}"
        print(f"{name:<12} {m['recall_at_1']:>6.3f} {m['recall_at_3']:>6.3f} "
              f"{m['recall_at_5']:>6.3f} {m['recall_at_10']:>6.3f} "
              f"{m['mean_reciprocal_rank']:>6.3f} {found_str:>8}")

    # Best strategy
    best = max(strategy_metrics, key=lambda s: strategy_metrics[s]["recall_at_5"])
    best_r5  = strategy_metrics[best]["recall_at_5"]
    base_r5  = baseline_metrics["recall_at_5"]
    delta_r5 = best_r5 - base_r5
    print(f"\nBest strategy: {best}  (Recall@5 {base_r5:.3f} → {best_r5:.3f}, {delta_r5:+.3f})")

    # Rescue analysis — queries fixed by best strategy
    baseline_miss_ids = {r["target_recipe_id"] for r in baseline_results if not r["target_rank"]}
    best_results = strategy_results[best]
    rescued = [r for r in best_results
               if r["target_recipe_id"] in baseline_miss_ids and r["target_rank"]]
    degraded = [r for r in best_results
                if r["target_recipe_id"] not in baseline_miss_ids and not r["target_rank"]]

    print(f"\nQuery rescue  : {len(rescued)} previously-missed queries now found")
    print(f"Query degraded: {len(degraded)} previously-found queries now missed")

    if rescued:
        print("\nRescued examples (first 3):")
        for r in rescued[:3]:
            print(f"  Target : {r['target_recipe_name']}")
            print(f"  Original  : {r['original_query'][:80]}...")
            print(f"  Rewritten : {r['rewritten_query'][:80]}")
            print(f"  Rank now  : {r['target_rank']}")
            print()

    # ── Save ──────────────────────────────────────────────────────────────────
    comparison = {
        "baseline": {"metrics": baseline_metrics},
        **{s: {"metrics": strategy_metrics[s]} for s in strategy_metrics},
        "best_strategy": best,
        "recall_at_5_improvement": float(delta_r5),
        "queries_rescued": len(rescued),
        "queries_degraded": len(degraded),
    }
    comp_path = results_dir / "retrieval_comparison.json"
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"\nSaved → {comp_path}")

    agent_path = results_dir / "agent_enhanced.json"
    with open(agent_path, "w") as f:
        json.dump({"strategy": best, "metrics": strategy_metrics[best],
                   "results": strategy_results[best]}, f, indent=2)
    print(f"Saved → {agent_path}")


if __name__ == "__main__":
    main()
