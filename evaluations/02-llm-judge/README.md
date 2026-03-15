# LLM-as-Judge: Automated Dietary Adherence Evaluation

Built a complete automated evaluation pipeline covering trace generation, manual labeling, judge prompt engineering, calibration, and statistical bias correction. Measures one thing precisely: **does the Recipe Bot's response actually match the user's stated dietary restriction?**

## Pipeline

```
Generate traces → Human-label ground truth → Engineer judge prompt
    → Calibrate on held-out test set → Run on full dataset → Correct for judge bias
```

## Key Results

| Metric | Value |
|--------|-------|
| Ground truth labeled traces | 241 (161 PASS / 80 FAIL) |
| Judge TPR (test set) | 82.2% |
| Judge TNR (test set) | 88.9% |
| Judge Balanced Accuracy | 85.5% |
| Traces evaluated | 439 |
| Raw observed pass rate | 55.6% |
| **Corrected pass rate** | **62.6%** |
| 95% Confidence Interval | [53.0%, 72.8%] |

## What I Built

1. **Trace generation**: Generated 439 traces from our Recipe Bot (not reference traces, our model, our prompt) across dietary queries
2. **Ground truth labeling**: Pre-labeled with an LLM, then human-reviewed every label. 241 traces with verified PASS/FAIL labels
3. **Judge prompt engineering**: Iterated on a dev set. One iteration softened a policy rule on ambiguous ingredients, lifting TPR from 68.8% to 82.2%
4. **Statistical correction**: Used [`judgy`](https://github.com/HamelHusain/judgy) to correct for judge bias. The judge has a slight false-negative tendency (misses some PASSes), so the corrected rate is higher than raw

## Why the Correction Matters

Raw judge output said 55.6% pass. Bias-corrected answer: 62.6%. A 7pp difference changes your launch decision. The wide CI (±10pp) reflects 439 traces. You'd need ~1000+ to tighten to ±5pp.

## How to Run

```bash
# From repo root
python evaluations/02-llm-judge/scripts/generate_traces.py
python evaluations/02-llm-judge/scripts/label_data.py
python evaluations/02-llm-judge/scripts/split_data.py
python evaluations/02-llm-judge/scripts/evaluate_judge.py --split dev
python evaluations/02-llm-judge/scripts/evaluate_judge.py --split test
python evaluations/02-llm-judge/scripts/run_full_evaluation.py
```

## Files

**Scripts** — 8 pipeline scripts in `scripts/`

| Script | What It Does |
|--------|-------------|
| `generate_traces.py` | Generates initial traces from dietary queries |
| `generate_traces_big.py` | Generates 439 traces in 4 parallel batches |
| `label_data.py` | Pre-labels traces using LLM |
| `review_labels.py` | Local browser UI for human review of labels |
| `split_data.py` | Stratified train/dev/test split |
| `evaluate_judge.py` | Runs judge prompt against dev and test sets |
| `review_predictions.py` | Browser UI to inspect judge predictions vs. ground truth |
| `run_full_evaluation.py` | Runs judge on all traces + applies statistical correction |

**Data** — labeled traces and splits in `data/`

**Results** — judge calibration, predictions, and final evaluation in `results/`. See [evaluation_narrative.md](results/evaluation_narrative.md) for the full story connecting error analysis to automated measurement.
