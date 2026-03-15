# Retrieval Evaluation: Measuring and Improving Recipe Search

Built and evaluated a BM25 retrieval system for the Recipe Bot. Generated a synthetic query set, established a baseline, and tested three LLM query rewrite strategies to find which one actually helps.

## Key Results

| Strategy | Recall@5 | MRR |
|----------|----------|-----|
| BM25 baseline | 81.3% | 0.704 |
| + keywords rewrite | **91.2%** | **0.785** |
| + full rewrite | 83.4% | 0.705 |
| + expand (synonyms) | 74.6% | 0.641 |

**Keywords won.** It strips conversational noise and lets BM25 focus on rare discriminative terms. Expand *hurt* performance because adding synonyms dilutes rare-term scores in lexical search. More is not better.

16 queries rescued by keywords rewrite, only 2 degraded.

## What I Built

1. **Synthetic query generation**: 2-step LLM pipeline that extracts a salient fact from each recipe, then generates a natural-language query targeting that fact. Produced 193 queries that are harder and more realistic than the reference set
2. **Baseline evaluation**: BM25 retrieval on both reference and our queries, measuring Recall@5 and MRR
3. **Query rewrite agent evaluation**: Tested 3 strategies (keywords extraction, full rewrite, synonym expansion) and compared per-query impact

## Why This Matters

For a dietary-sensitive product, retrieving the wrong recipe means answering from incorrect context. The 10pp Recall improvement (81% to 91%) means ~18 fewer wrong-recipe answers per 193 queries. At scale, that's tens of thousands of potentially incorrect dietary answers prevented daily.

The strategic unlock: once you have a grounded retrieval layer, the **corpus becomes a product lever** you can operate independently of the model: add recipes without retraining, audit which recipe answered any question, A/B test recipe versions.

## How to Run

```bash
# From repo root
python evaluations/03-retrieval/scripts/generate_queries.py
python evaluations/03-retrieval/scripts/evaluate_retrieval.py
python evaluations/03-retrieval/scripts/evaluate_retrieval_with_agent.py
```

## Files

| File | Description |
|------|------------|
| `scripts/generate_queries.py` | 2-step LLM pipeline to generate 193 synthetic queries |
| `scripts/evaluate_retrieval.py` | BM25 baseline on reference + own queries |
| `scripts/evaluate_retrieval_with_agent.py` | Tests 3 query rewrite strategies |
| `data/synthetic_queries.json` | 193 generated queries |
| `data/processed_recipes.json` | Recipe corpus (200 recipes) |
| `results/hw4_analysis.md` | Full write-up with failure analysis |
| `results/retrieval_comparison.json` | Side-by-side metrics for all strategies |

See [hw4_analysis.md](results/hw4_analysis.md) for the full analysis including BM25 failure modes.
