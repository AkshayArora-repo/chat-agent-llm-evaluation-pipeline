#!/usr/bin/env python3
"""My BM25 retrieval evaluation — saves to retrieval_evaluation.json.

Usage:
    python scripts/evaluate_retrieval.py
"""

import json
import sys
import statistics
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent.parent.parent / "backend"))
from retrieval import create_retriever
from evaluation_utils import BaseRetrievalEvaluator, load_queries


class MyRetrievalEvaluator(BaseRetrievalEvaluator):

    def analyze_by_query_characteristics(self, results: List[Dict[str, Any]]):
        print("\n--- Query Length Analysis ---")
        short = [r for r in results if len(r["original_query"].split()) <= 15]
        medium = [r for r in results if 15 < len(r["original_query"].split()) <= 25]
        long = [r for r in results if len(r["original_query"].split()) > 25]
        for label, group in [("short (≤15 words)", short), ("medium (16-25 words)", medium), ("long (>25 words)", long)]:
            if group:
                r5 = statistics.mean([r["recall_5"] for r in group])
                mrr = statistics.mean([r["reciprocal_rank"] for r in group])
                print(f"  {label}: {len(group)} queries | Recall@5={r5:.3f} | MRR={mrr:.3f}")

        print("\n--- Failure Analysis (target NOT in top 5) ---")
        failures = [r for r in results if r["recall_5"] == 0]
        print(f"  Total failures: {len(failures)}/200")
        for i, r in enumerate(failures[:8], 1):
            print(f"\n  MISS #{i}")
            print(f"    Query:   {r['original_query'][:100]}...")
            print(f"    Target:  {r['target_recipe_name']}")
            print(f"    Got:     {r['retrieved_names'][:3]}")

    def print_final_summary(self, results: List[Dict[str, Any]]):
        m = self.calculate_aggregate_metrics(results)
        print(f"\n{'='*70}")
        print("MY RETRIEVAL EVALUATION SUMMARY")
        print(f"{'='*70}")
        print(f"  Recall@1 : {m['recall_at_1']:.3f}  ({m['recall_at_1']*100:.1f}%)")
        print(f"  Recall@3 : {m['recall_at_3']:.3f}  ({m['recall_at_3']*100:.1f}%)")
        print(f"  Recall@5 : {m['recall_at_5']:.3f}  ({m['recall_at_5']*100:.1f}%)")
        print(f"  Recall@10: {m['recall_at_10']:.3f}  ({m['recall_at_10']*100:.1f}%)")
        print(f"  MRR      : {m['mean_reciprocal_rank']:.3f}")
        print(f"  Found    : {m['queries_found']}/{m['total_queries']} ({m['queries_found']/m['total_queries']*100:.1f}%)")
        print(f"  Not found: {m['queries_not_found']}/{m['total_queries']}")
        if m.get("average_rank_when_found"):
            print(f"  Avg rank when found : {m['average_rank_when_found']:.2f}")
            print(f"  Median rank when found: {m['median_rank_when_found']:.0f}")
        print(f"{'='*70}")


def main():
    base = Path(__file__).resolve().parent.parent
    recipes_path = base / "data" / "processed_recipes.json"
    queries_path = base / "data" / "synthetic_queries.json"
    index_path   = base / "data" / "bm25_index.pkl"
    results_path = base / "results" / "retrieval_evaluation.json"

    for p, name in [(recipes_path, "processed_recipes.json"), (queries_path, "synthetic_queries.json")]:
        if not p.exists():
            print(f"ERROR: {name} not found at {p}")
            sys.exit(1)

    queries = load_queries(queries_path)
    print(f"Loaded {len(queries)} queries")

    print("Building/loading BM25 retriever...")
    retriever = create_retriever(recipes_path, index_path)
    stats = retriever.get_stats()
    print(f"Retriever ready: {stats['total_recipes']} recipes indexed")

    evaluator = MyRetrievalEvaluator(retriever)
    results = evaluator.evaluate_all_queries(queries, top_k=10)

    evaluator.analyze_by_query_characteristics(results)
    evaluator.save_results(results, results_path, experiment_name="baseline_bm25")
    evaluator.print_final_summary(results)
    print(f"\nSaved → {results_path}")


if __name__ == "__main__":
    main()
