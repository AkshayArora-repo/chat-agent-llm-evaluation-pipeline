# Portfolio Tracker — AI Evals Course

> **Purpose**: Track everything we built HW by HW. Use this at the end of the course to:
> 1. Know exactly which files are ours vs. pre-existing course scaffolding
> 2. Write a clean root-level README for GitHub
> 3. Decide what to keep, delete, or reorganize before making the repo public

---

## Repo Structure — What Came Pre-Installed vs. What We Built

### Pre-existing course scaffolding (NOT ours — do not highlight)

| Path | What it is |
|------|-----------|
| `backend/` | Recipe Bot FastAPI app (course-provided) |
| `frontend/index.html` | Recipe Bot UI (course-provided) |
| `data/sample_queries.csv` | Course-provided sample queries |
| `results/results_*.csv` | Auto-generated run logs from the Recipe Bot app |
| `scripts/bulk_test.py` | Course-provided bulk test runner |
| `annotation/annotation.py` | Course-provided annotation helper |
| `lesson-4/` | Lesson 4 demo files (NurtureBoss example) |
| `lesson-7/` | Lesson 7 demo files |
| `lesson-8/` | Lesson 8 demo files (SMS spam cascade) |
| `homeworks/hw1/readme.md` | HW1 assignment instructions |
| `homeworks/hw2/README.md` | HW2 assignment instructions |
| `homeworks/hw2/hw2_solution_walkthrough.ipynb` | Reference walkthrough notebook |
| `homeworks/hw2/failure_mode_taxonomy.md` | Reference taxonomy (not ours) |
| `homeworks/hw2/error_analysis_template.csv` | Template file |
| `homeworks/hw2/generate_synthetic_queries.py` | Reference script |
| `homeworks/hw2/review_traces.py` | Reference review UI |
| `homeworks/hw2/synthetic_queries_for_analysis.csv` | Reference queries |
| `homeworks/hw3/` (non-`my_` files) | Reference scripts and data from course |
| `homeworks/hw4/hw4_walkthrough.py` | Reference walkthrough |
| `homeworks/hw4/data/processed_recipes.json` | Course-provided corpus |
| `homeworks/hw4/data/synthetic_queries.json` | Course-provided reference queries |
| `homeworks/hw4/scripts/evaluate_retrieval.py` | Reference evaluation script |
| `homeworks/hw4/scripts/evaluate_retrieval_with_agent.py` | Reference agent script |
| `homeworks/hw5/` | HW5 (not yet started) |
| `homeworks/optional/` | Optional HW (not yet started) |
| `env.example` | Course-provided env template |
| `requirements.txt` | Course-provided dependencies |
| `README.md` | Course-provided root README (replace with ours at end) |

### Files to delete before publishing

| Path | Reason |
|------|--------|
| `.env` | Contains secrets (auth tokens) — already in `.gitignore` |
| `.!67432!.env` | Temp file, should not exist |
| `curl command.txt` | Scratch file |
| `uvicorn.log` | Runtime log |
| `uvicorn_no_reload.log` | Runtime log |
| `results/results_*.csv` | 40+ auto-generated run logs, not meaningful |
| `homeworks/hw2/results_20250518_215844.csv` | Auto-generated run log |
| `homeworks/hw3/data/my_raw_traces_batch_*.csv` | Intermediate batch files (merged into big) |
| `homeworks/hw4/data/my_bm25_index.pkl` | Binary file, regeneratable from script |
| `.DS_Store` files | macOS metadata |
| `ai-evals-project.code-workspace` | IDE config, not relevant to portfolio |

---

## HW1 — Recipe Bot Baseline

**What we did**: Ran the Recipe Bot app and observed its behavior manually. Captured a screenshot.

**Our files**:
- `screenshots/hw1.png` — screenshot of the Recipe Bot UI

**Key finding**: Established the baseline — Recipe Bot answers dietary queries but with no systematic quality measurement.

**Status**: Complete

---

## HW2 — Failure Mode Discovery (Broad Exploration)

**What we did**: Ran 100 traces through Recipe Bot, manually reviewed them, and built a failure mode taxonomy.

**Our files**:

| File | What it contains |
|------|-----------------|
| `homeworks/hw2/my_failure_mode_taxonomy.md` | Our taxonomy of Recipe Bot failure modes |
| `homeworks/hw2/error_analysis.csv` | Our labeled error analysis (100 traces) |

**Key findings**:
- ~47% pass rate on 100 traces (broad, informal)
- 4 failure mode categories identified:
  1. Missing dietary substitutions (most common)
  2. Ambiguous ingredient handling (e.g., "may contain dairy")
  3. Ignoring explicit constraints
  4. Hallucinated ingredients

**Status**: Complete

---

## HW3 — LLM-as-Judge Pipeline (Narrow, Measured Evaluation)

**What we did**: Built a full automated evaluation pipeline — from trace generation → manual labeling → judge prompt engineering → statistical correction.

### Our scripts

| Script | What it does |
|--------|-------------|
| `homeworks/hw3/scripts/my_generate_traces.py` | Generates initial small batch of traces from `dietary_queries.csv` |
| `homeworks/hw3/scripts/my_generate_traces_big.py` | Generates 540 traces in 4 parallel batches (9 runs × 15 queries × 4 batches) |
| `homeworks/hw3/scripts/my_label_data.py` | Pre-labels traces using LLM to speed up manual review |
| `homeworks/hw3/scripts/my_review_labels.py` | Local browser UI for human review of LLM-pre-labeled traces |
| `homeworks/hw3/scripts/my_split_data.py` | Stratified train/dev/test split of labeled traces |
| `homeworks/hw3/scripts/my_evaluate_judge.py` | Runs judge prompt against dev and test sets, computes TPR/TNR |
| `homeworks/hw3/scripts/my_review_predictions.py` | Browser UI to inspect judge predictions vs. ground truth |
| `homeworks/hw3/scripts/my_run_full_evaluation.py` | Runs judge on all 439 big traces + applies `judgy` statistical correction |

### Our data

| File | What it contains |
|------|-----------------|
| `homeworks/hw3/data/my_raw_traces.csv` | Initial ~60 traces (small batch) |
| `homeworks/hw3/data/my_raw_traces_big.csv` | 439 traces generated by our Recipe Bot (merged from 4 batches) |
| `homeworks/hw3/data/my_labeled_traces.csv` | 241 human-reviewed ground truth labels (161 PASS, 80 FAIL) |
| `homeworks/hw3/data/my_train_set.csv` | 96 traces for few-shot example selection |
| `homeworks/hw3/data/my_dev_set.csv` | 36 traces for prompt iteration |
| `homeworks/hw3/data/my_test_set.csv` | 109 traces for unbiased final calibration |

### Our results

| File | What it contains |
|------|-----------------|
| `homeworks/hw3/results/my_judge_prompt.txt` | Final judge prompt (iterated on dev set) |
| `homeworks/hw3/results/my_judgy_test_data.json` | Judge calibration data for `judgy` library |
| `homeworks/hw3/results/my_judge_performance_dev.json` | Dev set performance (used for prompt iteration) |
| `homeworks/hw3/results/my_judge_performance_test.json` | Test set performance (final calibration) |
| `homeworks/hw3/results/my_dev_predictions.json` | Per-trace judge predictions on dev set |
| `homeworks/hw3/results/my_test_predictions.json` | Per-trace judge predictions on test set |
| `homeworks/hw3/results/my_final_evaluation.json` | Final corrected success rate + CI |
| `homeworks/hw3/results/my_full_predictions.json` | Per-trace predictions on all 439 big traces |
| `homeworks/hw3/results/my_evaluation_narrative.md` | Full narrative connecting HW2 → HW3 |

### Key metrics

| Metric | Value |
|--------|-------|
| Ground truth labeled traces | 241 (161 PASS / 80 FAIL) |
| Judge TPR (test set) | 82.2% |
| Judge TNR (test set) | 88.9% |
| Judge Balanced Accuracy | 85.5% |
| Traces in full evaluation | 439 |
| Raw observed pass rate | 55.6% |
| **Corrected pass rate (judgy)** | **62.6%** |
| 95% Confidence Interval | [53.0%, 72.8%] |

### Key decisions & learnings
- Generated our own 439 traces using our Recipe Bot (not the reference traces) because the reference may have used a different model/system prompt
- Iterated judge prompt once on dev set: softened Policy Rule 2 on ambiguous ingredients → TPR improved from 68.8% to 82.2%
- `judgy` corrects upward because our judge has a slight false-negative bias (misses some PASSes)
- Wide CI (±10pp) reflects 439 traces — need ~1000+ traces to tighten to ±5pp

**Status**: Complete

---

## HW4 — Retrieval Evaluation (RAG Component)

**What we did**: Built and evaluated a BM25 retrieval system for Recipe Bot, generated our own synthetic query set, and tested three LLM query rewrite strategies.

### Our scripts

| Script | What it does |
|--------|-------------|
| `homeworks/hw4/scripts/my_evaluate_retrieval.py` | Evaluates BM25 on reference queries + our own queries |
| `homeworks/hw4/scripts/my_generate_queries.py` | 2-step LLM pipeline to generate 193 synthetic queries |
| `homeworks/hw4/scripts/my_evaluate_retrieval_with_agent.py` | Tests 3 query rewrite strategies (keywords, rewrite, expand) |

### Our data

| File | What it contains |
|------|-----------------|
| `homeworks/hw4/data/my_synthetic_queries.json` | 193 LLM-generated queries (2-step: salient fact → query) |
| `homeworks/hw4/data/my_bm25_index.pkl` | Serialized BM25 index (regeneratable, ok to delete) |

### Our results

| File | What it contains |
|------|-----------------|
| `homeworks/hw4/results/my_retrieval_evaluation.json` | BM25 on reference queries (Recall@5: 73.0%) |
| `homeworks/hw4/results/my_retrieval_evaluation_own_queries.json` | BM25 on our queries (Recall@5: 81.3%) |
| `homeworks/hw4/results/my_retrieval_comparison.json` | Comparison across all 4 strategies |
| `homeworks/hw4/results/my_agent_enhanced.json` | Detailed results for best strategy (keywords) |
| `homeworks/hw4/results/my_hw4_analysis.md` | Full write-up with failure analysis |

### Key metrics

| Strategy | Recall@5 | MRR |
|----------|----------|-----|
| BM25 baseline (reference queries) | 73.0% | 0.623 |
| BM25 baseline (our queries) | 81.3% | 0.704 |
| + keywords rewrite | **91.2%** | **0.785** |
| + full rewrite | 83.4% | 0.705 |
| + expand | 74.6% | 0.641 |

### Key decisions & learnings
- Our 2-step query generation (extract salient fact → generate query) produced harder, more realistic queries than the reference set — yet BM25 scored higher, meaning our queries were better anchored to specific recipe content
- `keywords` strategy won: strips conversational noise, lets BM25 focus on rare discriminative terms
- `expand` strategy hurt: adding synonyms dilutes rare-term scores in BM25 (more is not better for lexical search)
- 16 queries rescued by keywords rewrite, only 2 degraded
- BM25 failure modes: generic bread competition, high-competition ingredient clusters, queries with no rare terms, numeric context loss

**Status**: Complete

---

## HW5 — Failure Transition Heat-Map

**What we did**: Pure analysis — no LLM calls, no data generation. Given 100 pre-labeled agent traces, each containing exactly one failure, we built a transition matrix showing where the agent succeeds last and fails first, then visualized it as a heat-map.

**The core concept**: The agent has 10 internal pipeline states:
```
ParseRequest → PlanToolCalls → GenCustomerArgs → GetCustomerProfile
→ GenRecipeArgs → GetRecipes → GenWebArgs → GetWebInfo
→ ComposeResponse → DeliverResponse
```
Each trace gives you one directed edge: `(last_success_state → first_failure_state)`. Count all 100 edges → build the matrix → visualize.

### Key insight discovered during data inspection

**The agent keeps talking after it fails.** After the `first_failure_state`, the assistant continues responding — the conversation looks complete from the outside. This is a **silent failure** pattern.

The analogy: a restaurant kitchen where the chef burns the sauce at station 6, but the dish still goes out. The customer gets a plate. It just has burnt sauce on it.

**Why this matters for production AI systems**: you cannot detect these failures by looking for crashes or error codes. The agent always "responds." The response is just wrong, incomplete, or hallucinated because a step upstream broke quietly. This is exactly why you need an automated eval pipeline (like HW3) — silent failures require explicit quality measurement, not just uptime monitoring.

**What the heat-map actually shows**: not "where did the agent stop" but **"where did quality silently degrade."** That's a fundamentally different and more dangerous failure mode than a hard crash.

### Data observation
- README lists 10 canonical states
- Only 9 appear in the data
- `DeliverResponse` is missing — because if the agent successfully delivers a response, the trace succeeded. Since every trace in this dataset contains exactly one failure, `DeliverResponse` never appears as `first_failure_state`. And it's never `last_success_state` because nothing fails after delivery.

### Our scripts

| Script | What it does |
|--------|-------------|
| `homeworks/hw5/analysis/my_transition_analysis.py` | Our version of the transition matrix + analysis |
| `homeworks/hw5/results/my_trace_explorer.html` | Interactive browser dashboard — heatmap + drilldown + trace inspector |

### Our results

| File | What it contains |
|------|-----------------|
| `homeworks/hw5/results/my_trace_explorer.html` | Interactive dashboard (no server needed, open in browser) |
| `homeworks/hw5/results/my_hw5_analysis.md` | Full write-up with failure analysis and PM learnings |

### Key findings from data inspection

**All 27 traces across the top 3 cells are caused by the same 3 user queries:**
- "I need a gluten-free dinner idea for four"
- "What vegetarian high-protein meal can I cook tonight?"
- "Suggest a healthy breakfast using oatmeal"

The heat-map looks like many different failure modes. Drilling in reveals it's essentially **one root cause repeated** across two failure clusters:

| Cluster | Transition | Count | Root cause |
|---------|-----------|-------|-----------|
| A | `PlanToolCalls → GenRecipeArgs` | 10 | Agent can't translate dietary query into structured recipe search args (schema translation failure) |
| B | `GetCustomerProfile → GetRecipes` + `GenCustomerArgs → GetRecipes` | 17 | Recipe DB returns empty for dietary-restriction queries (corpus coverage failure) |

**Two different owners, two different fixes:**

| Failure | Fix | Owner |
|---------|-----|-------|
| GenRecipeArgs can't translate dietary queries | Improve prompt / output schema for argument generation | ML/Prompt engineer |
| GetRecipes returns empty for dietary queries | Add gluten-free, vegetarian, oatmeal recipes to corpus | Content/Data team |

### What the user actually experiences (unfixed)

**Cluster A**: Agent understood the question, planned to search, then silently failed to construct the search query. User gets: *"I'm having trouble finding recipes right now. Could you tell me more about your preferences?"* — a deflection. User rephrases, same failure repeats. Zero value delivered, user churns.

**Cluster B**: Agent ran the full pipeline — fetched user profile, built the search — then DB returned empty. User gets: *"I couldn't find any gluten-free recipes right now. Try again later!"* — worse than Cluster A because the agent did more work and still failed. "Try again later" destroys trust.

**The compounding problem**: Both failures are completely silent. No error code, no alert, no ticket. The agent responds politely and moves on. At 1M users/day, you don't know it's happening unless you have an eval pipeline running.

### PM learnings from HW5

**1. The heat-map is a prioritization tool, not just a diagnostic**
Top 3 cells = 27/96 failures (28%). Fix two root causes, eliminate more than a quarter of all failures. That's how you write an engineering spec with evidence.

**2. Narrow corpus + fragile schema is a platform risk, not a feature bug**
Same 3 queries caused 27 failures across different pipeline paths. The failure is systemic — a gap between what users ask and what the system handles. You escalate this differently than a single-component bug: *"our dietary-restriction query coverage is zero — this is a product gap, not a code bug."*

**3. Silent failures are more dangerous than crashes**
A crash shows up in error logs immediately. A silent failure — agent responds politely but incorrectly — only shows up in your eval pipeline, churn data, or user research. Uptime monitoring tells you nothing about silent failures. This is why HW3's LLM-as-judge and HW5's transition analysis exist as separate disciplines.

**4. Evaluation is a product feature, not a post-launch activity**
Without HW3 + HW5, you'd have zero visibility into any of this at scale. The eval pipeline *is* the instrumentation layer. The PM who builds eval infrastructure before launch is playing a different game than the PM who ships first and measures later.

**The one-sentence PM takeaway**: *The heat-map turned an invisible, recurring, user-facing failure into a ranked, actionable engineering backlog with clear ownership — that's the entire value of building an eval pipeline.*

### What "fix the prompt / schema" actually means (not asking users to change)

When the fix says "improve the prompt or schema for GenRecipeArgs" — this has nothing to do with the user. The user's query is fine. The fix is entirely internal.

`GenRecipeArgs` is an internal agent step whose job is to take the user's natural language and convert it into a structured API call for the recipe database:

```json
{ "dietary_restriction": "gluten-free", "meal_type": "dinner", "servings": 4 }
```

The LLM is doing this conversion and failing. Three internal fixes — none touch the user:

**Fix 1 — Better system prompt for GenRecipeArgs**
The internal prompt driving this step is too vague ("extract recipe search parameters"). Replace with explicit field-by-field instructions: *"Extract the following fields. If a field is not mentioned, use null. Never return an error — always return a valid JSON object even with partial data."*

**Fix 2 — Constrained output schema**
Use structured outputs (OpenAI `response_format`, Pydantic validation) to force the LLM to return a valid object or retry — it can never return an error string. The user never sees this layer.

**Fix 3 — Fallback / graceful degradation**
If `GenRecipeArgs` fails, instead of propagating the error, fall back to passing the raw user query directly to the recipe DB as a keyword search. User gets a slightly less personalized result but always gets an answer. This eliminates the "try again later" response entirely.

**The restaurant analogy**: The customer (user) says "I'd like something gluten-free for four." The internal translator's job is to convert that into the kitchen's order ticket format. The customer spoke clearly. The translator is failing to fill out the ticket. You fix the translator's training (prompt), the ticket format (schema), or add a backup translator (fallback) — you never ask the customer to speak differently.

**Status**: Complete

---

## Optional HW — (Not yet started)

**Directory**: `homeworks/optional/`

---

## End-of-Course GitHub Cleanup Checklist

When the course is done, do this before making the repo public:

### Step 1 — Delete noise files
```bash
# Runtime logs
rm uvicorn.log uvicorn_no_reload.log
rm "curl command.txt"
rm .!67432!.env
rm ai-evals-project.code-workspace

# Auto-generated run results (not meaningful)
rm results/results_*.csv
rm homeworks/hw2/results_20250518_215844.csv

# Intermediate batch files
rm homeworks/hw3/data/my_raw_traces_batch_*.csv

# Binary index (regeneratable)
rm homeworks/hw4/data/my_bm25_index.pkl

# macOS metadata
find . -name ".DS_Store" -delete
```

### Step 2 — Decide on lesson files
The `lesson-4/`, `lesson-7/`, `lesson-8/` directories are course demo files, not your work. Options:
- **Keep**: Shows the full course context
- **Delete**: Cleaner portfolio focused on your HW work

### Step 3 — Write a new root README.md
Replace the course README with your own that tells the story:
- What this project is (AI evals course on Recipe Bot)
- The arc: HW2 (broad discovery) → HW3 (automated eval) → HW4 (retrieval eval)
- Key results table
- How to run each component

### Step 4 — Add a `.gitignore` entry for secrets
Verify `.env` is already in `.gitignore` (it is). Double-check before pushing.

### Step 5 — Final commit
```bash
git add homeworks/ MY_PORTFOLIO_TRACKER.md README.md
git commit -m "Add HW2-HW4 solutions with full evaluation pipeline"
git push
```

---

## The Story Arc (for your GitHub README / interviews)

> **HW2**: Ran Recipe Bot on 100 queries. Found ~47% pass rate. Identified 4 failure modes through manual open coding. Problem: this was informal — no statistical rigor, no automation.
>
> **HW3**: Built an automated LLM-as-judge pipeline. Manually labeled 241 traces as ground truth. Engineered a judge prompt (iterated on dev set). Calibrated judge: TPR 82.2%, TNR 88.9%. Ran judge on 439 new traces. Used `judgy` to correct for judge bias: **62.6% pass rate, 95% CI [53%, 73%]**. Now we have a repeatable, statistically rigorous measurement.
>
> **HW4**: Evaluated the retrieval layer of Recipe Bot. Built a BM25 index over 200 recipes. Generated 193 synthetic queries via 2-step LLM pipeline. Baseline: Recall@5 81.3%. Added LLM query rewrite agent — keywords strategy lifted Recall@5 to **91.2% (+9.9pp)** with only 2 regressions out of 193 queries.

## How Production RAG Actually Works (context for GitHub readers)

Most tutorials show naive RAG: `User query → Retriever → LLM → Answer`. Real products add layers:

```
Production RAG:
User query → Query Rewriter → Retriever → Reranker → LLM → Answer
```

Each layer handles a specific failure mode:
- **Query Rewriter**: fixes lexical mismatch (user says "rise", recipe says "proof") — we built this, measured +9.9pp
- **Retriever**: finds candidate documents — we built BM25 baseline
- **Reranker**: re-scores top-20 with a smarter model — estimated +5-10pp, not built
- **LLM**: answers only from retrieved context, not memory — Recipe Bot

The query rewrite happens **invisibly** — the user types a conversational question, the system silently converts it to search keywords, retrieves the right recipe, and answers with grounded facts. The user just sees a good answer.

**Why this matters beyond metrics**: for a dietary-sensitive product, retrieving the wrong recipe and answering from it is a product safety issue. The 10pp improvement in Recall@5 (81% → 91%) means ~18 fewer wrong-recipe answers per 193 queries. At 1M users/day, that's tens of thousands of potentially incorrect dietary answers prevented daily.

**The strategic unlock**: once you have a grounded retrieval layer, the corpus becomes a product lever you can operate independently of the model — add recipes without retraining, audit which recipe answered any question, A/B test recipe versions, identify gaps from failure logs. That's the difference between a chatbot and a knowledge system.
