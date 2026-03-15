# The AI Evals Playbook
### Everything I Learned Building Evaluation Systems for LLM Applications

> **What this is**: A comprehensive reference for AI evaluation — from first principles through production systems. Built from hands-on work across 5 homework assignments in Shreyas & Hamel's AI Evals course, where I systematically evaluated a Recipe Bot chatbot. Every concept here is grounded in something I actually built, measured, or debugged.
>
> **How to use it**: Read end-to-end for the full narrative, or jump to any chapter. Part II is the technical core. Part III is the systems thinking layer. Part IV is the quick-reference for panel discussions.

---

# Table of Contents

- [Part I — Foundations](#part-i--foundations)
  - [Chapter 1: Why Evaluation Matters](#chapter-1-why-evaluation-matters)
  - [Chapter 2: The Course Arc — How It All Fits Together](#chapter-2-the-course-arc--how-it-all-fits-together)
- [Part II — The Evaluation Journey (Homework Deep-Dives)](#part-ii--the-evaluation-journey-homework-deep-dives)
  - [Chapter 3: Establishing a Baseline (HW1)](#chapter-3-establishing-a-baseline-hw1)
  - [Chapter 4: Broad Discovery — Finding Where Things Break (HW2)](#chapter-4-broad-discovery--finding-where-things-break-hw2)
  - [Chapter 5: Narrow Measurement — The LLM-as-Judge Pipeline (HW3)](#chapter-5-narrow-measurement--the-llm-as-judge-pipeline-hw3)
  - [Chapter 6: Component Evaluation — Retrieval & RAG (HW4)](#chapter-6-component-evaluation--retrieval--rag-hw4)
  - [Chapter 7: Pipeline Diagnostics — Where Quality Silently Degrades (HW5)](#chapter-7-pipeline-diagnostics--where-quality-silently-degrades-hw5)
- [Part III — Building Agentic Applications: Architecture, Evals & System Design](#part-iii--building-agentic-applications-architecture-evals--system-design)
  - [Chapter 8: Anatomy of an Agentic Application](#chapter-8-anatomy-of-an-agentic-application)
  - [Chapter 9: The Eval-Driven Development Loop](#chapter-9-the-eval-driven-development-loop)
  - [Chapter 10: System Design Thinking at Every Layer](#chapter-10-system-design-thinking-at-every-layer)
  - [Chapter 11: Production Patterns — Cascades, Observability & Cost](#chapter-11-production-patterns--cascades-observability--cost)
- [Part IV — Synthesis & Quick Reference](#part-iv--synthesis--quick-reference)
  - [Chapter 12: Cross-Cutting Learnings](#chapter-12-cross-cutting-learnings)
  - [Chapter 13: Technical Concepts Glossary](#chapter-13-technical-concepts-glossary)
  - [Chapter 14: The PM & Leadership Perspective](#chapter-14-the-pm--leadership-perspective)
  - [Chapter 15: Panel Discussion Cheat Sheet](#chapter-15-panel-discussion-cheat-sheet)

---

# Part I — Foundations

## Chapter 1: Why Evaluation Matters

### The Core Problem

LLM applications don't crash — they degrade silently. A traditional software bug throws an exception, triggers an alert, and shows up in your error dashboard. An LLM failure looks like a polite, confident, wrong answer. The user gets a response. It just happens to be incorrect, incomplete, or hallucinated.

This is the fundamental challenge that makes AI evaluation a discipline unto itself:

**You cannot tell if an LLM application is working by looking at whether it responds.** You need a separate system — an evaluation pipeline — to measure whether the responses are *good*.

### What Evaluation Actually Is

Evaluation is not testing. Testing asks "does the code run?" Evaluation asks "does the output meet a quality bar?" In traditional software, the output is deterministic — same input, same output. In LLM applications, the output is stochastic — same input, different output every time. This means:

1. **You can't write unit tests** in the traditional sense. There's no expected output to assert against.
2. **You need statistical measurement.** One run tells you nothing. You need hundreds of runs to establish a distribution.
3. **You need a definition of "good."** Quality is subjective and domain-specific. Someone has to decide what PASS and FAIL mean for your application.
4. **You need a judge.** Since you can't hard-code assertions, you need something (human or LLM) to assess quality at scale.
5. **You need to measure the judge.** The judge itself is imperfect. You need to know *how* imperfect and correct for it.

This is the evaluation stack. Each layer depends on the one below it:

```
┌─────────────────────────────────────┐
│   Corrected Measurement + CI        │  ← What you report to stakeholders
├─────────────────────────────────────┤
│   Judge Calibration (TPR/TNR)       │  ← How much to trust the judge
├─────────────────────────────────────┤
│   LLM-as-Judge                      │  ← Automated quality assessment
├─────────────────────────────────────┤
│   Ground Truth Labels               │  ← Human-verified "right answers"
├─────────────────────────────────────┤
│   Failure Mode Taxonomy             │  ← What "bad" looks like
├─────────────────────────────────────┤
│   Traces (System Under Evaluation)  │  ← Raw data from the application
└─────────────────────────────────────┘
```

### The Two Modes of Evaluation

Everything in this playbook maps to one of two modes:

| Mode | Question | Method | Output |
|------|----------|--------|--------|
| **Broad discovery** | "Where does it break?" | Manual review, open/axial coding | Failure mode taxonomy |
| **Narrow measurement** | "How often does it break on dimension X?" | LLM-as-judge + statistical correction | Corrected pass rate + confidence interval |

You always start broad to find what matters, then go narrow to measure it precisely. This is the fundamental rhythm of evaluation work.

### Why "Vibes-Based" Evaluation Fails

Before this course, the typical approach to evaluating an LLM app was:

1. Try a few queries manually
2. "Looks good to me"
3. Ship it
4. Wait for user complaints

This fails because:
- **Small samples lie.** 10 manual tests might all pass even if the true pass rate is 60%.
- **Confirmation bias.** You test the cases you expect to work.
- **No repeatability.** You can't measure improvement if you don't have a baseline.
- **No coverage.** Edge cases (dietary restrictions, ambiguous queries, contradictory requests) are where LLMs fail most — and they're the cases you're least likely to test manually.

The entire course is about replacing vibes with measurement.

---

## Chapter 2: The Course Arc — How It All Fits Together

### The Progressive Zoom

Each homework zooms into a different layer of the system, and each builds on what came before:

```
HW1: "Does it respond?"          → Baseline (yes, it responds)
HW2: "Where does it break?"      → Taxonomy (5 failure modes, 47% pass)
HW3: "How often does it break?"  → Measurement (62.6% dietary compliance [53-73%])
HW4: "Why does retrieval break?" → Component eval (Recall@5: 81% → 91% with rewrite)
HW5: "Where in the pipeline?"    → Diagnostics (28% of failures → 2 root causes)
```

### The Three-Layer Diagnostic

By the end, you have a complete picture:

| Layer | HW | Question | Finding |
|-------|-----|----------|---------|
| **Output quality** | HW3 | Did the final answer comply? | 62.6% pass rate — 37% non-compliant |
| **Data layer** | HW4 | Did retrieval find the right recipe? | 81.3% Recall@5 — 19% wrong recipe |
| **Pipeline location** | HW5 | Where did quality silently degrade? | 28% of failures → 2 root causes, 2 owners |

HW3 tells you *how often* it fails. HW4 tells you *where in the data layer* it fails. HW5 tells you *where in the pipeline* it fails and *why*. Together: symptom → mechanism → location.

### The Application Under Evaluation: Recipe Bot

Throughout the course, we evaluated a **Recipe Bot** — a conversational cooking assistant built on:

- **Backend**: FastAPI + LLM (GPT-4o-mini via LiteLLM or llm-exec)
- **System prompt**: Friendly cooking assistant that prioritizes clarity, simplicity, speed
- **Output format**: Structured recipes with Title, Summary, Yield, Time, Ingredients, Steps, Tips, Optional Add-ons
- **Closing**: "Was this helpful? Want it quicker, cheaper, or tailored to your diet?"

The system prompt itself created an interesting tension: it instructed the bot to "prioritize clarity, simplicity, and speed" — which caused it to override explicit user requests for complex recipes. This became the #1 failure mode in HW2 (32% of failures). A product design issue, not a model quality issue.

---

# Part II — The Evaluation Journey (Homework Deep-Dives)

## Chapter 3: Establishing a Baseline (HW1)

### What We Did

- Wrote an effective system prompt for Recipe Bot in `backend/utils.py`
- Expanded the test query dataset in `data/sample_queries.csv` with 10+ diverse queries
- Ran `scripts/bulk_test.py` to generate baseline traces

### The System Prompt

The system prompt is the foundation of LLM application behavior. Recipe Bot's prompt defined:

1. **Role & objective**: Friendly cooking assistant
2. **Response rules**: Always provide ingredient lists with precise measurements, always include step-by-step instructions
3. **Safety clause**: Decline unsafe/unethical requests politely
4. **LLM agency boundaries**: Can suggest variations/substitutions, can creatively combine known recipes
5. **Output formatting**: Markdown structure with required sections (Title, Summary, Yield, Time, Ingredients, Steps, Tips, Add-ons)

**Key insight**: The system prompt is not just instructions — it's the product specification. Every behavioral expectation lives here. And every conflict in the prompt creates a failure mode. The instruction to "prioritize simplicity" conflicted with users requesting complex recipes — and that conflict drove 32% of all failures.

### Query Design

Good evaluation starts with diverse, realistic queries. The queries I added covered:

- **Cuisines**: Italian, Thai, Turkish, Korean
- **Dietary restrictions**: Vegan, gluten-free, keto, halal, low-FODMAP
- **Constraints**: Time limits, skill levels, available ingredients
- **Ambiguity**: Vague requests, contradictory preferences
- **Edge cases**: Emoji-heavy queries, typos, slang

**Why this matters**: If you only test happy-path queries ("Give me a pasta recipe"), you'll never find the failure modes that matter. Dietary restriction queries are where Recipe Bot breaks most — and they're also where incorrect answers have real consequences.

### System Design Thinking: The Baseline Layer

At the baseline layer, the system is simple:

```
User Query → LLM (with system prompt) → Response
```

There's no retrieval, no tools, no pipeline. Just prompt-in, text-out. The system design decisions at this layer are:

1. **Model selection**: GPT-4o-mini (cost vs. quality tradeoff)
2. **System prompt design**: What behavior to encode
3. **Output format**: Structured markdown for consistency
4. **Query interface**: FastAPI backend + HTML frontend

**What you can evaluate here**: Only the end-to-end output quality. You can ask "is this response good?" but you can't yet ask "why is it bad?" because there are no internal components to inspect. That's what the later homeworks add.

---

## Chapter 4: Broad Discovery — Finding Where Things Break (HW2)

### The Method: Open Coding → Axial Coding

This is a qualitative research methodology borrowed from social science. The idea is to look at data without preconceived categories and let patterns emerge.

**Open coding** (first pass):
- Read each trace
- Write freeform notes about what you observe
- No categories yet — just observations

Example open codes from my analysis:
- "language not simple. words like saute aromatic" (SYN001)
- "time preference not followed by bot" (SYN007)
- "are bread crumbs keto??" (SYN010)
- "LLM service error - risk screening blocked response" (SYN004)

**Axial coding** (second pass):
- Group open codes into broader categories
- Define each category with a clear title, definition, and examples
- Count frequencies

This two-pass approach prevents you from seeing only what you expect to see. If you start with categories ("I bet it fails on dietary restrictions"), you'll find those failures and miss others. Open coding forces you to look at the data first.

### My Failure Mode Taxonomy

From 100 traces (47 PASS, 53 FAIL):

| Failure Mode | Count | % of Failures | Definition |
|---|---|---|---|
| **User Constraint Ignored** | 32 | 60% | Bot doesn't follow stated constraints (time, diet, skill). Defaults to simple when complex requested. |
| **LLM Service Blocked** | 16 | 30% | Risk screening filter false positives blocking legitimate recipe content |
| **Unclear Language** | 3 | 6% | Jargon, vague descriptions, overly complex phrasing |
| **Incomplete Recipe** | 2 | 4% | Ingredients in steps missing from ingredients list |
| **Missing Personalization** | 2 | 4% | Generic responses; doesn't engage with user's specific situation |

```
User Constraint Ignored:     ████████████████████████████████ (32)
LLM Service Blocked:         ████████████████ (16)
Unclear Language:             ███ (3)
Incomplete Recipe:            ██ (2)
Missing Personalization:      ██ (2)
```

### Key Discoveries

**1. The #1 failure is a product design issue, not a model issue.**

"User Constraint Ignored" (32 traces, 60% of failures) is caused by a conflict in the system prompt. The prompt says "prioritize clarity, simplicity, and speed" — so when a user asks for a challenging, complex recipe, the bot overrides their request and gives something simple. The model is doing exactly what it was told. The instructions are wrong.

**Fix**: Rewrite the system prompt to say "match the user's stated complexity preference" instead of always defaulting to simple.

**2. Platform reliability issues are separate from application quality.**

"LLM Service Blocked" (16 traces) was caused by Intuit's risk screening filter incorrectly flagging normal recipe content as profanity. This is not a Recipe Bot problem — it's an infrastructure problem that requires coordination with the llm-exec team. Evaluation surfaces these issues; fixing them requires organizational awareness.

**3. Broad evaluation creates a roadmap.**

The taxonomy directly tells you what to fix first:
1. Fix system prompt conflict (32 failures)
2. Escalate risk screening false positives (16 failures)
3. Improve language clarity (3 failures)
4. Ensure ingredient completeness (2 failures)

This is not a quality score — it's an engineering backlog with evidence.

### When to Use Broad vs. Narrow Evaluation

| Dimension | Broad (HW2) | Narrow (HW3+) |
|-----------|-------------|----------------|
| **Goal** | Discover failure modes | Measure one precisely |
| **Sample size** | ~100 traces | 200+ labeled, 400+ unlabeled |
| **Method** | Manual review, open/axial coding | LLM-as-judge + statistical correction |
| **Output** | Taxonomy + frequencies | Pass rate + confidence interval |
| **Scalability** | Manual only (~100 traces max) | Automated (thousands of traces) |
| **When to use** | Start of project, new feature, major change | Ongoing measurement, regression detection |

**Rule of thumb**: Go broad when you don't know what's broken. Go narrow when you know what to measure.

### System Design Thinking: Adding Observability

At this layer, we're adding the first observability layer to the system:

```
User Query → LLM → Response
                       ↓
              Trace Logger → CSV
                       ↓
              Human Reviewer → Taxonomy
```

The system design insight is that **the application itself doesn't change**. We're building a parallel measurement system that observes the application's behavior. This is the beginning of the evaluation infrastructure pattern: the eval pipeline runs alongside the product pipeline, not inside it.

**What you can evaluate here**: Failure mode categories and their relative frequencies. You can answer "what kinds of failures exist?" but not yet "how often does failure X happen with statistical confidence?"

---

## Chapter 5: Narrow Measurement — The LLM-as-Judge Pipeline (HW3)

This is the technical core of the course. Everything in HW3 is a building block you'll reuse in every eval project.

### The Decision: What to Measure

From HW2's taxonomy, we chose **dietary adherence** as the narrow criterion: "When a user requests a recipe with specific dietary restrictions, does the bot provide a recipe that actually meets those restrictions?"

Why this criterion:
- **Clear definition**: Dietary rules are objective (vegan = no animal products)
- **High stakes**: Wrong dietary information has real consequences
- **Common failure**: Showed up frequently in HW2
- **Measurable**: Binary PASS/FAIL, not a subjective quality score

**Key principle**: Pick one dimension. Measure it well. Don't try to evaluate everything at once. A precise measurement of one thing is worth more than a vague assessment of everything.

### Step 1: Generate Traces

**Script**: `homeworks/hw3/scripts/my_generate_traces.py`

```python
# Core approach:
# - Load 60 dietary edge-case queries from dietary_queries.csv
# - Run each query through Recipe Bot multiple times (5 traces per query)
# - Use ThreadPoolExecutor with 8 workers for parallel execution
# - Save successful traces to my_raw_traces.csv

TRACES_PER_QUERY = 5  # Multiple runs capture stochastic variation
```

**Why multiple runs per query?** LLM outputs are stochastic. The same query might produce a compliant recipe on one run and a non-compliant one on the next. Running 5 times per query captures this variance.

**Why our own traces, not the reference?** The reference traces were generated with a potentially different model/system prompt. Using our own ensures we're measuring *our* Recipe Bot's actual behavior.

**Result**: 439 successful traces from 60 queries (some failed due to rate limits/risk screening).

### Step 2: Build Ground Truth

**Script**: `homeworks/hw3/scripts/my_label_data.py`

Ground truth is the single most important asset in an evaluation pipeline. It's the only place where you "know" the right answer. Everything downstream — judge calibration, bias correction, confidence intervals — depends on the quality of your labels.

**Approach: LLM pre-labeling + human review**

```python
LABELING_PROMPT = """You are an expert nutritionist and dietary compliance specialist.
Your task is to evaluate whether a Recipe Bot response properly adheres to
a user's specified dietary restriction..."""

# Output per trace:
# - label: PASS or FAIL
# - reasoning: Detailed explanation
# - confidence: HIGH / MEDIUM / LOW
```

The LLM pre-labels traces to speed up human review. But — and this is critical — **every label was human-reviewed**. The LLM gets you 80% of the way; the human catches the 20% the LLM gets wrong.

**Result**: 241 human-verified labels (161 PASS, 80 FAIL — 67% / 33%)

**Why not just use LLM labels as ground truth?** Because the LLM has systematic biases. If you use LLM labels as ground truth and then use an LLM judge, you're measuring agreement between two LLMs — not actual quality. Ground truth must be human-verified.

### Step 3: Split the Data

**Script**: `homeworks/hw3/scripts/my_split_data.py`

```python
# Stratified splits preserving PASS/FAIL ratios:
# Train:  36 traces (15%) → Few-shot examples for judge prompt
# Dev:    96 traces (40%) → Iterate on judge prompt
# Test:  109 traces (45%) → Final, locked evaluation

train_test_split(data, test_size=0.85, stratify=labels, random_state=42)
# Then split remainder into dev (40/85) and test (45/85)
```

**Why three splits?**

| Split | Purpose | Rules |
|-------|---------|-------|
| **Train** | Select few-shot examples for the judge prompt | Never compute metrics on this |
| **Dev** | Iterate on judge prompt until performance is acceptable | Look at this as much as you want |
| **Test** | Final, unbiased measurement of judge quality | **Never look at this until you're done iterating** |

**Why stratified?** Each split must contain both PASS and FAIL examples in similar proportions. If dev is 90% PASS and test is 50% PASS, your dev metrics won't predict test performance.

**The cardinal sin of evaluation**: Tuning on your test set. If you look at test-set errors and adjust your judge prompt to fix them, your test metrics are no longer unbiased. The test set is your "sealed envelope" — open it once, report the number, done.

### Step 4: Engineer the Judge Prompt

**File**: `homeworks/hw3/results/my_judge_prompt.txt`

The judge prompt is a 500-line document that turns an LLM into a dietary compliance evaluator. Key components:

**1. Role definition:**
```
You are an expert nutritionist and dietary compliance specialist.
Your task is to evaluate whether a Recipe Bot response properly
adheres to a user's specified dietary restriction.
```

**2. Dietary restriction definitions (16 categories):**
```
- Vegan: No animal products (meat, dairy, eggs, honey, etc.)
- Vegetarian: No meat or fish, but dairy and eggs are allowed
- Gluten-free: No wheat, barley, rye, or other gluten-containing grains
- Keto: Very low carb (typically <20g net carbs), high fat, moderate protein
- Raw vegan: Vegan foods not heated above 118°F (48°C)
... (16 total)
```

**3. Policy rules (the heart of the prompt):**

These are the rules I iterated on during dev-set evaluation:

```
POLICY RULES:
1. OPTIONAL NON-COMPLIANT INGREDIENTS = FAIL
   If the recipe suggests a non-compliant ingredient as "optional,"
   in "Tips," or in "Add-ons," it is still a FAIL.

2. AMBIGUOUS INGREDIENTS: Apply the "default version" test.
   Ask: "Is the most common, default version of this ingredient
   non-compliant?"
   - If YES → FAIL (e.g., generic "granola" often contains honey)
   - If NO → PASS (e.g., canned tomatoes are just tomatoes + salt)
   - Key question: "Would a typical shopper grabbing the most common
     brand off the shelf get a compliant version?"

3. JUDGE AGAINST THE DIETARY RESTRICTION FIELD, NOT USER CAVEATS.
   If user says "I'm vegan but I want honey," still evaluate
   against "vegan."

4. COOKING METHOD VIOLATIONS = FAIL
   For raw vegan: any instruction heating above 118°F is a FAIL.

5. NON-COMPLIANT SUBSTITUTION SUGGESTIONS = FAIL

6. CASUAL PHRASING = STRICT EVALUATION
   "keto-ish" or "gluten-light" → evaluate against strict definition.
```

**4. Few-shot examples (10 examples from train set):**

Each example includes the full query, dietary restriction, recipe response, detailed reasoning citing specific policy rules, and the final label. Examples cover:
- Vegetarian recipe with optional ground beef → FAIL (Rule 1)
- Halal recipe with Parmesan → FAIL (Rule 2, animal rennet)
- Raw vegan soup with "blend until steaming" → FAIL (Rule 4)
- Sugar-free recipe with brown sugar → FAIL (obvious violation)
- Vegan recipe with generic granola → FAIL (Rule 2, honey)
- Vegan chocolate cake with maple syrup → PASS (all plant-based)
- Diabetic-friendly cake with almond flour → PASS
- Nut-free cookies with allergy note → PASS

**The iteration story:**

| Version | Change | Dev TPR | Dev TNR | Problem |
|---------|--------|---------|---------|---------|
| v1 | Very strict: "ambiguous ingredient = FAIL" | 0.69 | 1.00 | Too many false negatives — flagging compliant recipes |
| v2 | Added "default version" test for ambiguous ingredients | 0.83 | 0.97 | Balanced — judge now asks "would a shopper get a compliant version?" |

The key iteration was **Policy Rule 2**. In v1, any ingredient that *could* be non-compliant was marked FAIL. This flagged things like "canned tomatoes" (because some brands add sugar) and "pizza sauce" (because some contain cheese). The "default version" test fixed this: if the most common version at a typical grocery store is compliant, it's PASS.

### Step 5: Calibrate the Judge

**Script**: `homeworks/hw3/scripts/my_evaluate_judge.py`

Run the judge on the test set (109 traces) to measure its accuracy:

```
Test Set Performance:
┌──────────────────────┬────────┐
│ Metric               │ Value  │
├──────────────────────┼────────┤
│ True Positive Rate   │ 82.2%  │  ← When truly PASS, judge says PASS 82% of the time
│ True Negative Rate   │ 88.9%  │  ← When truly FAIL, judge says FAIL 89% of the time
│ Balanced Accuracy    │ 85.5%  │  ← (TPR + TNR) / 2
└──────────────────────┴────────┘

Confusion Matrix:
                    Predicted PASS  Predicted FAIL
Actual PASS (73)         60              13          ← 13 false negatives (FN)
Actual FAIL (36)          4              32          ← 4 false positives (FP)
```

**Understanding TPR and TNR:**

- **TPR = 82.2%** (True Positive Rate / Sensitivity / Recall): Of recipes that are *truly compliant*, the judge correctly identifies 82.2% as PASS. It misses 17.8% — these are **false negatives** (judge says FAIL when it's actually PASS).

- **TNR = 88.9%** (True Negative Rate / Specificity): Of recipes that are *truly non-compliant*, the judge correctly identifies 88.9% as FAIL. It misses 11.1% — these are **false positives** (judge says PASS when it's actually FAIL).

**The bias**: TPR < TNR means the judge has a **false-negative bias** — it's slightly too strict, flagging some compliant recipes as non-compliant. This means the raw pass rate from the judge will *underestimate* the true pass rate. This is important for the next step.

**Error analysis (what the judge gets wrong):**

False negatives (13 cases — judge said FAIL, actually PASS):
- Judge being too strict on ambiguous ingredients even after the "default version" rule
- Overthinking edge cases that are clearly fine

False positives (4 cases — judge said PASS, actually FAIL):
- Missing subtle violations buried in Tips/Add-ons sections
- Not catching cooking method violations in raw vegan recipes

**False positives are more dangerous than false negatives.** A false negative is annoying (underestimates quality). A false positive is dangerous (misses a real dietary violation). For safety-critical applications, you want TNR as high as possible — our 88.9% is good but not perfect.

### Step 6: Measure at Scale with Bias Correction

**Script**: `homeworks/hw3/scripts/my_run_full_evaluation.py`

Now we run the locked judge on 439 *new*, *unlabeled* traces and correct for the known bias:

```python
# Step 1: Run judge on all 439 traces
# → Raw observed pass rate: 55.6%

# Step 2: Correct for judge bias using judgy library
from judgy import estimate_success_rate

result = estimate_success_rate(
    judge_labels=predictions,       # Judge's PASS/FAIL on 439 traces
    test_labels=test_ground_truth,  # Human labels on 109 test traces
    test_predictions=test_preds     # Judge predictions on same 109 test traces
)
# → Corrected pass rate: 62.6%
# → 95% CI: [53.0%, 72.8%]
```

**How judgy works:**

The math is elegant. If you know the judge's TPR and TNR from calibration, you can solve for the true pass rate:

```
observed_pass_rate = TPR × true_pass_rate + (1 - TNR) × (1 - true_pass_rate)

Rearranging:
true_pass_rate = (observed_pass_rate - (1 - TNR)) / (TPR - (1 - TNR))
               = (0.556 - 0.111) / (0.822 - 0.111)
               = 0.445 / 0.711
               ≈ 0.626
```

The judge observed 55.6% pass rate, but we know it has false-negative bias (TPR 82.2% < TNR 88.9%). So some of those "FAILs" are actually PASSes. Judgy corrects upward by +7 percentage points to 62.6%.

**The confidence interval**: [53.0%, 72.8%] — a 20-point spread. This reflects:
1. **Sample size uncertainty**: 439 traces gives limited precision
2. **Judge calibration uncertainty**: TPR/TNR are estimated from 109 test traces
3. **Stochastic variation**: Different runs would give different results

To tighten the CI to ±5 pp, you'd need ~1000+ traces. To get ±2 pp, you'd need ~5000+.

### The Complete HW3 Pipeline

```
dietary_queries.csv (60 queries)
        │
        ▼
my_generate_traces.py ──→ my_raw_traces.csv (241 traces, small batch)
        │                  my_raw_traces_big.csv (439 traces, large batch)
        ▼
my_label_data.py ──→ my_labeled_traces.csv (241 human-verified labels)
        │
        ▼
my_split_data.py ──→ my_train_set.csv (36)
        │              my_dev_set.csv (96)
        │              my_test_set.csv (109)
        ▼
[Manual prompt engineering using train examples + dev metrics]
        │
        ▼
my_evaluate_judge.py ──→ my_judge_performance_dev.json (iterate)
        │                  my_judge_performance_test.json (final: TPR 82.2%, TNR 88.9%)
        │                  my_judgy_test_data.json (for bias correction)
        ▼
my_run_full_evaluation.py ──→ my_final_evaluation.json
                                Raw: 55.6%
                                Corrected: 62.6% [53.0%, 72.8%]
```

### What This Means in Plain English

Recipe Bot correctly adheres to dietary restrictions about 63% of the time (our best estimate). We're 95% confident the true rate is between 53% and 73%. That means roughly 1 in 3 dietary-restriction recipes contains a violation — a real product risk for a cooking assistant.

### System Design Thinking: The Measurement Layer

At this layer, we've built a parallel measurement system:

```
                    ┌──────────────────────┐
User Query ───────→ │    Recipe Bot LLM     │ ───→ Response to User
                    └──────────────────────┘
                              │
                         [Trace logged]
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Ground Truth Labels  │ ← Human-verified (241)
                    └──────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │   LLM Judge (locked)  │ ← Calibrated on test set
                    └──────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │  Judgy Correction     │ ← Corrects for judge bias
                    └──────────────────────┘
                              │
                              ▼
                    62.6% [53%, 73%]  ← Reportable number
```

The product pipeline (top) and the evaluation pipeline (bottom) are completely decoupled. The eval pipeline doesn't change the product — it just measures it. This separation is a key architectural principle: **evaluation is infrastructure, not a feature**.

---

## Chapter 6: Component Evaluation — Retrieval & RAG (HW4)

### Why Component-Level Evaluation

HW3 measured the end-to-end output: "Is the response good?" But when the response is bad, you don't know *why*. Is it because the LLM is bad? Because it retrieved the wrong recipe? Because the query was ambiguous?

Component-level evaluation breaks the system into pieces and measures each one. In a RAG (Retrieval-Augmented Generation) system, the critical component is **retrieval** — finding the right document before the LLM generates an answer.

**The retrieval bottleneck**: If retrieval fails, the LLM is answering based on the wrong context. Even a perfect LLM cannot give a correct answer about Recipe A if it was given Recipe B. Retrieval quality is a *multiplier* on output quality — fix retrieval and everything downstream improves.

### BM25: How Keyword Search Works

BM25 (Best Matching 25) is a classical information retrieval algorithm. It's the backbone of most search engines before the deep learning era, and it's still competitive for many use cases.

**Core idea**: Score documents by how well their words match the query, weighted by word rarity.

**Two key components:**

1. **TF (Term Frequency)**: How often does the query word appear in this document? More occurrences → higher score. But with diminishing returns — the 10th occurrence matters less than the 1st.

2. **IDF (Inverse Document Frequency)**: How rare is this word across all documents? Rare words are more informative. "dumplings" (appears in 2 recipes) is a much stronger signal than "cook" (appears in all 200 recipes).

```
BM25 score = Σ  IDF(word) × TF(word, document) × (k1 + 1)
             ─────────────────────────────────────────────────
             TF(word, document) + k1 × (1 - b + b × |D|/avgdl)

Where:
- k1 ≈ 1.5 (TF saturation parameter)
- b ≈ 0.75 (document length normalization)
- |D| = document length, avgdl = average document length
```

**Why BM25 works well for recipes**: Recipe text contains specific, rare terms (ingredient names, dish names, techniques). When a query contains "tuiles" or "saffron" or "dumplings," BM25 finds the right recipe because those words are rare and discriminative.

**Where BM25 fails**: When queries use conversational language ("How do I get my dough to rise properly?") instead of recipe-specific terms. The query words ("dough," "rise") appear in 30+ recipes, so BM25 can't distinguish between them.

### Synthetic Query Generation: The 2-Step Approach

**Script**: `homeworks/hw4/scripts/my_generate_queries.py`

Generating good test queries is itself a craft. Bad queries test nothing; good queries reveal failure modes.

**The 2-step salient fact extraction:**

```
Step 1: Extract salient fact from recipe
────────────────────────────────────────
Prompt: "Read this recipe and identify 1-2 distinctive,
retrievable technical facts. Target: temperatures, cooking times,
marinating durations, appliance settings, dough resting times,
internal temps, mixing techniques. Facts must be hard to guess
and involve precise numbers or named techniques."

Recipe: "Amazing Hungarian Chicken Paprikash with Dumplings"
→ Salient fact: "Simmer chicken in paprika sauce for 25 minutes
   before adding dumplings"

Step 2: Generate realistic user query about that fact
────────────────────────────────────────
Prompt: "Generate one natural, conversational question a home cook
might ask. Sound like a real person, not a textbook. Focus on the
salient fact. Don't mention the recipe name."

→ Query: "How long should I simmer chicken broth for dumplings?"
```

**Why 2 steps instead of 1?** A single-step prompt ("Generate a query for this recipe") produces generic questions like "How do I make this?" The 2-step approach forces specificity: first extract the *most distinctive detail*, then ask about *that specific detail*. This produces queries that have a unique answer — exactly what you want for retrieval evaluation.

**Result**: 193 synthetic queries, each paired with the source recipe ID (ground truth for retrieval evaluation).

### Information Retrieval Metrics

Four metrics you need to know:

**Recall@k**: "What fraction of queries had the target recipe in the top k results?"

```
Recall@1:  Target is the #1 result           → 63.2%
Recall@3:  Target is in top 3 results        → 77.2%
Recall@5:  Target is in top 5 results        → 81.3%
Recall@10: Target is in top 10 results       → 86.5%
```

Recall@5 is the most commonly reported metric. It means: "If I show the user the top 5 recipes, is the right one among them?" 81.3% means 1 in 5 queries retrieves the wrong set of recipes.

**MRR (Mean Reciprocal Rank)**: "On average, how high does the target recipe rank?"

```
MRR = average of (1 / rank) for all queries where target was found

If target is rank 1: 1/1 = 1.0
If target is rank 3: 1/3 = 0.33
If target not found: 0

Our MRR: 0.704 → target is typically between rank 1 and rank 2
```

MRR cares about *where* in the results the target appears, not just whether it appears. High Recall@5 + low MRR means the target is being found but at rank 4-5, not rank 1.

### Baseline Results and Failure Analysis

| Metric | Our Queries (193) | Reference Queries (200) |
|--------|-------------------|------------------------|
| Recall@1 | **63.2%** | 53.5% |
| Recall@5 | **81.3%** | 73.0% |
| MRR | **0.704** | 0.623 |

Our queries outperformed the reference on every metric (+8-10 pp). Why? Our salient-fact extraction produced more concrete, specific terms that BM25 can anchor on.

**Query length vs. performance:**

| Length | n | Recall@5 | MRR |
|--------|---|----------|-----|
| Short (≤15 words) | 18 | 83.3% | 0.718 |
| Medium (16-25) | 143 | 79.7% | 0.684 |
| Long (>25 words) | 32 | **87.5%** | **0.788** |

Longer queries perform better — more words means more chances for a rare, discriminative term to appear.

**26 complete misses — four overlapping failure modes:**

**1. Generic bread recipes dominate (65% of misses)**
Three short recipes (`5 minute artisan bread`, `amish friendship bread`, `100 whole wheat bread`) appear in the top 3 for most failures. Short docs with common baking words (`dough`, `knead`, `bake`, `flour`) get inflated BM25 scores because term frequency is proportionally higher in short documents.

**2. High competition in baking domain (62%)**
30+ baking/dough recipes share the same vocabulary. BM25 cannot distinguish between them when the query uses only generic baking terms.

**3. Query lacks unique anchor term (54%)**
"How long do I mix on low and then medium-high, and what is the bake time at 350?" — could describe any cake recipe. No rare word to anchor on.

**4. Numbers present but not unique (50%)**
"375°F, 2 hours" appear across many recipes. BM25 treats numbers as regular tokens — it can't understand that `375 + cheesecake + 2 hours` is a unique combination.

### Query Rewrite Agent: Three Strategies

**Script**: `homeworks/hw4/scripts/my_evaluate_retrieval_with_agent.py`

The insight: if BM25 fails on conversational queries, transform the query before searching.

**Strategy 1 — Keywords: Strip to core search terms**
```
Original: "After kneading for the full 10 minutes, does the dough
           really need to rise for over two hours?"
Keywords: "knead dough rise overnight cinnamon rolls"
```
Remove conversational noise. Keep only terms that appear in recipe text.

**Strategy 2 — Rewrite: Rephrase for search effectiveness**
```
Original: "After kneading for the full 10 minutes..."
Rewrite:  "overnight cinnamon rolls knead 10 minutes dough rise
           2 hours baking"
```
More aggressive transformation. Infer the dish name if possible.

**Strategy 3 — Expand: Add synonyms and related terms**
```
Original: "After kneading for the full 10 minutes..."
Expand:   "knead fold dough bread rise proof ferment overnight
           cinnamon rolls baking oven yeast"
```
Add synonyms (`rise` → `proof`, `ferment`), related equipment, related ingredients.

### Results: Why Keywords Won

| Strategy | Recall@5 | MRR | Queries Rescued | Queries Degraded |
|----------|----------|-----|-----------------|------------------|
| Baseline | 81.3% | 0.704 | — | — |
| **Keywords** | **91.2%** | **0.785** | **16** | **2** |
| Rewrite | 83.4% | 0.705 | — | — |
| Expand | 74.6% | 0.641 | — | — |

**Keywords won by a landslide**: +9.9 pp on Recall@5, rescued 16 previously-missed queries, only 2 regressions.

**Why keywords won**: Our queries already contained specific terms (from the 2-step generation). The gain came from *removing noise*, not adding information. Stripping conversational filler ("After," "really," "does," "need to") lets BM25 focus on the rare, meaningful tokens.

**Why expand HURT performance** (-6.7 pp vs baseline): Adding synonyms *dilutes* rare-term scores. BM25 weights rarity highly. If you add common words (`bake`, `oven`, `cook`) to a query that contains a rare word (`tuiles`), the rare word's contribution to the score drops. More is literally worse for keyword search.

**Why rewrite was neutral**: Rephrasing sometimes introduced new words that didn't match recipe text. "Proof" instead of "rise" — technically correct, but the recipe text says "rise," not "proof." BM25 is literal; it doesn't understand synonyms.

**The insight**: For BM25 (lexical search), the optimal query strategy is *subtractive*, not *additive*. Remove noise; don't add information. This flips with semantic/dense retrieval, where expansion helps because the embedding model understands synonyms.

### Naive RAG vs. Production RAG

Most tutorials show:
```
Naive RAG:       User query → Retriever → LLM → Answer
                 (breaks on conversational queries)
```

Real products:
```
Production RAG:  User query → Query Rewriter → Retriever → Reranker → LLM → Answer
                 (each layer handles a specific failure mode)
```

| Layer | What it fixes | What we built | Measured impact |
|-------|--------------|---------------|-----------------|
| **Query Rewriter** | Lexical mismatch (user says "rise", recipe says "proof") | Keywords strategy | +9.9 pp Recall@5 |
| **Retriever** | Finds candidate documents | BM25 baseline | 81.3% Recall@5 |
| **Reranker** | Re-scores top-20 with a cross-encoder model | Not built | Estimated +5-10 pp |
| **LLM** | Answers from retrieved context, not memory | Recipe Bot | Existing |

The query rewrite happens **invisibly** — the user types a conversational question, the system silently converts it to search keywords, retrieves the right recipe, and answers with grounded facts. The user just sees a good answer.

### The Strategic Unlock: Corpus as Product Lever

Before RAG: Recipe Bot answers from model memory → hallucination risk, stale knowledge, no auditability.

After RAG + rewrite: Recipe Bot answers from a grounded corpus → measurable accuracy, updatable without retraining, fully auditable.

The corpus becomes a **product lever** you can operate independently of the model:
- Add new recipes without touching the model or redeploying
- A/B test different recipe versions and measure retrieval impact
- Audit exactly which recipe was used to answer any question (traceability)
- Swap BM25 for dense retrieval later without changing anything else
- Identify corpus gaps from retrieval failure logs

This is the difference between a chatbot and a knowledge system.

### System Design Thinking: The Data Layer

At this layer, the system architecture expands:

```
User Query
    │
    ▼
┌─────────────────┐
│  Query Rewriter  │  ← LLM call (~200ms)
│  (keywords)      │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  BM25 Retriever  │  ← Keyword search over 200 recipes
│  (rank_bm25)     │
└─────────────────┘
    │
    ▼
 Top-5 recipes
    │
    ▼
┌─────────────────┐
│  Recipe Bot LLM  │  ← Answers from retrieved context
└─────────────────┘
    │
    ▼
  Response
```

The evaluation architecture for this layer is:

```
193 synthetic queries (with known source_recipe_id)
    │
    ▼
BM25 retriever → top-k results
    │
    ▼
Check: is source_recipe_id in top-k?
    │
    ▼
Recall@k, MRR metrics
```

**Key design decision**: Evaluation of retrieval is *much simpler* than evaluation of generation. You have a known right answer (source recipe ID), so it's a deterministic check — no LLM judge needed. This is why component evaluation is powerful: some components have clean, measurable outputs even when the end-to-end system doesn't.

---

## Chapter 7: Pipeline Diagnostics — Where Quality Silently Degrades (HW5)

### The Problem: Silent Failures

A traditional software crash throws an exception. You see it in logs. You get paged. You fix it.

An LLM agent failure is different. The agent encounters a problem at step 6 of a 10-step pipeline — and then **keeps going**. It generates a polite, complete-looking response. The user gets an answer. It's just wrong.

```
The restaurant analogy:

Traditional crash: Kitchen burns the sauce → fire alarm → everyone knows
Silent failure:    Kitchen burns the sauce → dish still goes out → customer gets burnt sauce
                   → no alarm, no ticket, no alert
                   → the waiter smiled and served it confidently
```

This is why you need pipeline diagnostics. End-to-end evaluation (HW3) tells you the dish has burnt sauce. Component evaluation (HW4) tells you the sauce is burned. Pipeline diagnostics (HW5) tells you *which station burned it and why*.

### The Agent Pipeline: 10 States

Recipe Bot's agent has 10 internal states:

```
1. ParseRequest      → LLM interprets the user's message
2. PlanToolCalls     → LLM decides which tools to invoke
3. GenCustomerArgs   → LLM constructs arguments for customer DB
4. GetCustomerProfile→ Execute customer-profile tool
5. GenRecipeArgs     → LLM constructs arguments for recipe DB
6. GetRecipes        → Execute recipe-search tool
7. GenWebArgs        → LLM constructs arguments for web search
8. GetWebInfo        → Execute web-search tool
9. ComposeResponse   → LLM drafts the final answer
10. DeliverResponse  → Agent sends the answer
```

Not every trace visits all 10 states — the agent picks branches based on the query. But every trace in the HW5 dataset has exactly one failure, labeled with:
- `last_success_state`: The last state that worked correctly
- `first_failure_state`: The first state where quality degraded

### The Transition Matrix

Each trace gives you one directed edge: `(last_success → first_failure)`. Count all edges across 96 traces → build a 10×10 matrix → visualize as heatmap.

```
                    ┌─ first_failure_state ─┐
                    Parse Plan GenCA GetCP GenRA GetR GenWA GetWI Comp Deliv
┌─ last_success ─┐
│ ParseRequest    │
│ PlanToolCalls   │        •     3          10    5    3
│ GenCustomerArgs │                    7          8
│ GetCustomerProf │              7                9
│ GenRecipeArgs   │                               7
│ GetRecipes      │                                    2    2    3    2
│ GenWebArgs      │                                         3
│ GetWebInfo      │                                              2    3
│ ComposeResponse │                                                   0
│ DeliverResponse │
└─────────────────┘
```

Key observations:
- **69 of 100 possible transitions are zero** → failures are concentrated, not random
- **Top failure state**: `GetRecipes` (32 traces, 33%)
- **Top last-success state**: `PlanToolCalls` (31 traces, 32%)
- **54% of failures at tool execution states** (GetRecipes, GetCustomerProfile, GetWebInfo)
- **46% at LLM generation states** (GenRecipeArgs, GenCustomerArgs, etc.)

### Root Cause Analysis: The Top 3 Cells

The top 3 transitions account for **27 of 96 failures (28%)**:

| Rank | Transition | Count |
|------|-----------|-------|
| 1 | PlanToolCalls → GenRecipeArgs | 10 (10.4%) |
| 2 | GetCustomerProfile → GetRecipes | 9 (9.4%) |
| 3 | GenCustomerArgs → GetRecipes | 8 (8.3%) |

**The surprise**: All 27 traces trace back to **the same 3 user queries**:
- "I need a gluten-free dinner idea for four"
- "What vegetarian high-protein meal can I cook tonight?"
- "Suggest a healthy breakfast using oatmeal"

The heatmap looks like many different failure modes. Drilling in reveals it's **one root cause repeated** across two failure clusters:

### Cluster A: Schema Translation Failure (10 traces)

**Transition**: `PlanToolCalls → GenRecipeArgs`

The agent understood the query (ParseRequest ✅, PlanToolCalls ✅) but failed to convert it into structured recipe search parameters.

```
What should happen:
  User: "I need a gluten-free dinner idea for four"
    → GenRecipeArgs should produce:
      { "dietary_restriction": "gluten-free",
        "meal_type": "dinner",
        "servings": 4 }

What actually happens:
  → GenRecipeArgs returns: "Error: unable to generate recipe search parameters"
```

**Root cause**: The internal LLM prompt driving GenRecipeArgs is too vague. It can't translate dietary constraint queries into the structured schema.

**Fix** (three options, all internal — user changes nothing):
1. **Better prompt**: Explicit field-by-field extraction instructions
2. **Structured outputs**: Use Pydantic/response_format to force valid JSON
3. **Fallback**: If structured extraction fails, pass raw query as keyword search

**Owner**: ML/Prompt engineer. **Timeline**: Days.

### Cluster B: Corpus Coverage Failure (17 traces)

**Transitions**: `GetCustomerProfile → GetRecipes` (9) + `GenCustomerArgs → GetRecipes` (8)

The agent did everything right — parsed the request, planned, fetched the profile, built search parameters. Then `GetRecipes` returned empty. The recipe database has zero coverage for gluten-free dinners, vegetarian high-protein meals, and oatmeal breakfasts.

**Root cause**: The corpus doesn't contain dietary-restriction recipes. The retrieval system works (as measured in HW4); it just has nothing to retrieve.

**Fix**: Add dietary-restriction recipes to the corpus.

**Owner**: Content/Data team. **Timeline**: Weeks.

### What Users Actually Experience

**Cluster A** — Agent deflects:
> *"I'm having trouble finding recipes right now. Could you tell me more about your preferences?"*

The user gave a clear request. The agent asks them to rephrase. They rephrase. Same failure. Zero value delivered.

**Cluster B** — Agent admits defeat:
> *"I couldn't find any gluten-free recipes right now. Try again later!"*

Worse than Cluster A. The agent did more work and still failed. "Try again later" destroys trust — the user now knows the system can't help with dietary restrictions.

**Both failures are completely silent.** No error code. No alert. No engineering ticket. At 1M users/day, you don't know this is happening unless you have an eval pipeline running.

### The Compounding Insight

HW3, HW4, and HW5 now form a complete diagnostic:

| Layer | What we measured | Finding | Action |
|-------|-----------------|---------|--------|
| **HW3** (output) | Dietary compliance of final answers | 62.6% — 37% non-compliant | "We have a problem" |
| **HW4** (data) | Retrieval accuracy | 81.3% Recall@5 — 19% wrong recipe | "Retrieval needs query rewrite" |
| **HW5** (pipeline) | Where failures occur | 28% → 2 root causes, 2 owners | "Fix GenRecipeArgs prompt + add recipes" |

From symptom (bad answer) to mechanism (wrong retrieval) to location (GenRecipeArgs or empty corpus) to owner (ML engineer or content team). That's the full diagnostic chain.

### System Design Thinking: The Diagnostic Layer

At this layer, the architecture includes full pipeline instrumentation:

```
User Query
    │
    ▼
┌───────────────┐
│ ParseRequest  │ ← state logged
└───────────────┘
    │
    ▼
┌───────────────┐
│ PlanToolCalls │ ← state logged, last_success tracked
└───────────────┘
    │
    ├──→ GenCustomerArgs → GetCustomerProfile
    │
    ├──→ GenRecipeArgs → GetRecipes          ← failure detected here
    │
    ├──→ GenWebArgs → GetWebInfo
    │
    ▼
┌────────────────┐
│ ComposeResponse│ ← agent continues despite upstream failure
└────────────────┘
    │
    ▼
┌────────────────┐
│ DeliverResponse│ ← user gets a response (but it's wrong)
└────────────────┘
```

The key insight is that **the agent doesn't stop when a step fails**. It keeps going, generating a response that looks complete. The only way to know a step failed is to instrument every state transition and compare against expected behavior.

This is the argument for **observability as a first-class concern** in agent architecture. You need:
1. **State logging**: Record which states were visited and their outcomes
2. **Transition tracking**: Record (last_success, first_failure) pairs
3. **Aggregation**: Build transition matrices over many traces
4. **Visualization**: Heatmaps for pattern detection
5. **Drilldown**: Ability to inspect individual traces behind each cell

---

# Part III — Building Agentic Applications: Architecture, Evals & System Design

## Chapter 8: Anatomy of an Agentic Application

### What Makes an Application "Agentic"

An agentic application is one where the LLM makes decisions about *what to do next*, not just *what to say*. Recipe Bot in HW5 is a clear example — it decides which tools to call, in what order, with what arguments, based on the user's query.

The key architectural components:

```
┌─────────────────────────────────────────────────────────────┐
│                     AGENT LOOP                               │
│                                                              │
│  ┌───────────┐    ┌──────────┐    ┌──────────────────┐      │
│  │  Planner   │───→│ Executor  │───→│ Response Builder  │     │
│  │ (LLM call) │    │ (tools)   │    │ (LLM call)        │     │
│  └───────────┘    └──────────┘    └──────────────────┘      │
│       ↑                │                    │                │
│       │           [tool results]            │                │
│       └─────────── feedback loop ───────────┘                │
│                                                              │
│  Tools:                                                      │
│  ├── Customer DB (GetCustomerProfile)                        │
│  ├── Recipe DB (GetRecipes)                                  │
│  ├── Web Search (GetWebInfo)                                 │
│  └── [any other API/tool]                                    │
│                                                              │
│  Context:                                                    │
│  ├── System prompt (behavioral rules)                        │
│  ├── Conversation history                                    │
│  ├── Retrieved documents (RAG)                               │
│  └── Tool results from current turn                          │
└─────────────────────────────────────────────────────────────┘
```

### The Three Types of LLM Calls in an Agent

Not all LLM calls are equal. Understanding their distinct roles is crucial for evaluation:

**1. Reasoning calls** (ParseRequest, PlanToolCalls)
- **Purpose**: Understand intent, decide what to do
- **Quality metric**: Does the plan make sense for the query?
- **Failure mode**: Misunderstanding the request, wrong tool selection
- **Eval approach**: Check plan against expected tool set for query type

**2. Argument generation calls** (GenCustomerArgs, GenRecipeArgs, GenWebArgs)
- **Purpose**: Translate natural language into structured API arguments
- **Quality metric**: Does the JSON match the expected schema? Are fields correct?
- **Failure mode**: Schema translation failure (Cluster A in HW5)
- **Eval approach**: Validate output against schema, check field values

**3. Synthesis calls** (ComposeResponse)
- **Purpose**: Combine tool results into a coherent answer
- **Quality metric**: Is the answer accurate, complete, well-formatted?
- **Failure mode**: Hallucination, missing information, format violations
- **Eval approach**: LLM-as-judge on final output (HW3)

Each type has different failure modes, different eval strategies, and different owners when things go wrong.

### Tool Integration Patterns

Tools are the bridge between the LLM's reasoning and the real world. Three patterns:

**Pattern 1: Direct API call**
```
LLM generates args → Call API → Return results
Example: GetCustomerProfile, GetRecipes
Failure mode: Empty results, API errors, wrong arguments
```

**Pattern 2: RAG retrieval**
```
LLM rewrites query → BM25/vector search → Return top-k docs
Example: GetRecipes (with RAG layer from HW4)
Failure mode: Wrong documents retrieved, query mismatch
```

**Pattern 3: Multi-step tool chain**
```
LLM plans → Tool A results → LLM re-plans → Tool B results → ...
Example: Fetch profile → use profile to constrain recipe search
Failure mode: Error propagation — Tool A failure corrupts Tool B inputs
```

### Error Propagation in Agent Pipelines

The most insidious pattern in agentic applications is **error propagation** — a failure at step N corrupts all subsequent steps, but the agent keeps going and delivers a confident-looking response.

```
Step 1: ParseRequest ✅ "User wants gluten-free dinner for 4"
Step 2: PlanToolCalls ✅ "I'll search recipes with dietary filter"
Step 3: GenRecipeArgs ❌ Returns error (can't generate structured args)
Step 4: GetRecipes    ❌ Receives bad args → returns empty
Step 5: ComposeResponse "I couldn't find recipes. Try again later!"  ← looks polite
Step 6: DeliverResponse ✅ User gets the response

From outside: Agent responded! Ship it!
From inside: Steps 3-5 all failed, user got zero value
```

This is exactly what HW5's transition matrix captures. The last_success/first_failure pair tells you where the propagation chain begins.

---

## Chapter 9: The Eval-Driven Development Loop

### The Loop

Building AI applications well means building evaluation *first*, not after:

```
┌─────────────────────────────────────────────┐
│                                             │
│  1. Define what "good" looks like           │
│     (failure mode taxonomy, quality criteria)│
│                                             │
│  2. Build ground truth                      │
│     (human-label a sample)                  │
│                                             │
│  3. Build automated measurement             │
│     (LLM-as-judge, calibrated on test set)  │
│                                             │
│  4. Measure baseline                        │
│     (current performance with CI)           │
│                                             │
│  5. Make a change                           │
│     (new prompt, new model, new retrieval)  │
│                                             │
│  6. Measure again                           │
│     (same judge, same queries)              │
│                                             │
│  7. Compare with statistical rigor          │
│     (did performance change significantly?) │
│                                             │
│  8. Iterate → go to step 5                  │
│                                             │
└─────────────────────────────────────────────┘
```

**The key insight**: Steps 1-4 are the *investment*. Once you have a calibrated eval pipeline, steps 5-7 are fast and repeatable. Every future change can be measured against the same baseline. Without this investment, every change is a leap of faith.

### What to Evaluate at Each Stage of Development

| Development stage | What to evaluate | Method |
|-------------------|-----------------|--------|
| **Prompt engineering** | Does the output match quality criteria? | LLM-as-judge on end-to-end output |
| **Adding RAG** | Does retrieval find the right documents? | Recall@k, MRR on synthetic queries |
| **Adding tools** | Do tool calls succeed? Are arguments valid? | Schema validation, success rate |
| **Agent pipeline** | Where do failures occur? | Transition matrix, state-level metrics |
| **Model swap** | Does quality change? | A/B comparison with same eval pipeline |
| **Prompt iteration** | Does the change help or hurt? | Before/after measurement with CI |
| **Production monitoring** | Is quality stable over time? | Continuous eval on sampled traffic |

### The Ground Truth Bottleneck

Ground truth is always the bottleneck. You need human-verified labels, and humans are slow and expensive.

**Strategies to manage the bottleneck:**

1. **LLM pre-labeling + human review** (what I did in HW3): Use an LLM to generate initial labels, then have humans correct them. Gets you 80% accuracy automatically; humans focus on the 20% the LLM gets wrong.

2. **Active learning**: Label the traces the judge is most uncertain about. This maximizes the information gained per human label.

3. **Stratified sampling**: Don't label randomly. Ensure you cover all important subgroups (query types, dietary restrictions, failure modes).

4. **Start small, scale later**: 100-200 high-quality labels is enough to calibrate a judge. You don't need 10,000 labels on day one.

---

## Chapter 10: System Design Thinking at Every Layer

### Layer 1: Single LLM Call (HW1 Baseline)

```
Architecture:  User → LLM → Response
Eval:          Manual review ("does it look good?")
Failure modes: Bad prompt, model limitations
Fix surface:   System prompt only
```

**Design considerations:**
- Model selection (capability vs. cost vs. latency)
- System prompt design (explicit rules, output format, safety guardrails)
- Temperature setting (creativity vs. consistency)
- Token limits (response length, context window)

**What you can measure**: End-to-end output quality only. When something goes wrong, the only lever is the prompt.

### Layer 2: LLM + Evaluation (HW2-HW3)

```
Architecture:  User → LLM → Response
               [Trace] → [Labels] → [Judge] → [Judgy] → Measurement
Eval:          Automated LLM-as-judge with bias correction
Failure modes: Everything from Layer 1, plus judge calibration drift
Fix surface:   System prompt, judge prompt, labeling criteria
```

**Design considerations:**
- How to generate diverse, representative traces
- How to build and maintain ground truth labels
- How to split data for unbiased evaluation
- How to handle judge bias and uncertainty
- How to set quality thresholds and alert on regression

**The eval infrastructure becomes its own system** with its own maintenance burden. The judge prompt needs updating when the product changes. Ground truth labels go stale. The judgy calibration needs refreshing.

### Layer 3: LLM + Retrieval (HW4 RAG)

```
Architecture:  User → [Query Rewriter] → Retriever → LLM → Response
Eval:          Retrieval metrics (Recall@k, MRR) + end-to-end judge
Failure modes: Query mismatch, corpus gaps, wrong document retrieved
Fix surface:   Query rewriter, retrieval algorithm, corpus content, LLM prompt
```

**Design considerations:**
- Retrieval algorithm (BM25 vs. dense vs. hybrid)
- Query preprocessing (rewrite, expand, keywords)
- Corpus management (content updates, deduplication, metadata)
- Result ranking (top-k selection, reranking)
- Chunk size and overlap for document splitting

**The critical design tradeoff**: BM25 is fast, cheap, and interpretable but fails on paraphrases. Dense retrieval handles paraphrases but is slower, more expensive, and harder to debug. Hybrid combines both but adds complexity.

**Production RAG stack:**
```
User query
    │
    ├── Query understanding (intent classification)
    ├── Query rewriting (for search optimization)
    │
    ├── BM25 retrieval (top-50 candidates)
    ├── Dense retrieval (top-50 candidates)
    │
    ├── Fusion (combine and deduplicate)
    ├── Reranking (cross-encoder on top-20)
    │
    ├── Context assembly (format for LLM)
    └── Generation (LLM answers from context)
```

Each component is independently evaluable:
- Query rewriter: Did it improve retrieval? (HW4 measured this)
- Retriever: Recall@k, MRR
- Reranker: NDCG, position improvement
- Generator: End-to-end quality (HW3 judge)

### Layer 4: Full Agent Pipeline (HW5)

```
Architecture:  User → [Parse] → [Plan] → [Tool calls] → [Compose] → Response
Eval:          State-level transition matrix + end-to-end judge
Failure modes: Silent failures at any state, error propagation
Fix surface:   Per-state prompts, tool implementations, fallback logic, corpus
```

**Design considerations:**
- State machine design (what states, what transitions)
- Error handling strategy (fail fast vs. graceful degradation)
- Fallback chains (what to do when a tool fails)
- Observability (logging every state transition)
- Timeout and retry policies per tool
- Context management (what information flows between states)

**The graceful degradation principle:**

```
If GenRecipeArgs fails:
  Option A (current): Return error → "Try again later" → user churns
  Option B (better):  Fall back to keyword search with raw query
  Option C (best):    Fall back to keyword search + tell user
                      "I found some general recipes; let me know
                      if you need something more specific"
```

Option C preserves user trust even when the system partially fails. The user gets *something* (a general recipe) instead of *nothing* ("try again later"). Designing these fallback chains is a critical part of agent architecture.

### Layer 5: Multi-Agent Systems (Beyond the Course)

```
Architecture:  Orchestrator → [Agent A] → [Agent B] → [Agent C] → Response
               Each agent has its own tools, state, and evaluation criteria
```

**Design considerations:**
- Agent routing (which agent handles which queries)
- Inter-agent communication (what context is shared)
- Cascade vs. parallel execution
- Per-agent evaluation + end-to-end evaluation
- Cost management (each agent = LLM calls = cost)

**The evaluation challenge scales multiplicatively**: With N agents, you need N component evals + 1 end-to-end eval + N×(N-1) interaction evals. This is why eval infrastructure must be built early — retrofitting it into a multi-agent system is orders of magnitude harder.

---

## Chapter 11: Production Patterns — Cascades, Observability & Cost

### Model Cascades: The Cost-Accuracy Tradeoff (Lesson 8)

Not every query needs the most expensive model. A model cascade routes easy queries to a cheap model and hard queries to an expensive one:

```
User query
    │
    ▼
┌────────────────────┐
│ Cheap "Proxy" Model │  (e.g., GPT-4o-mini)
│ + confidence score  │
└────────────────────┘
    │
    ├── High confidence → Use proxy answer (cheap)
    │
    └── Low confidence → Escalate to...
                         ┌──────────────────────┐
                         │ Expensive "Oracle"     │  (e.g., GPT-4o)
                         │ Model                  │
                         └──────────────────────┘
                              │
                              └── Use oracle answer (expensive but accurate)
```

**How to build it:**

1. Run proxy model on labeled test data → get predictions + confidence scores
2. Find confidence threshold that maintains target accuracy (e.g., 99%)
3. In production: queries above threshold use proxy; queries below escalate to oracle
4. **Measure**: Oracle usage rate (what % gets escalated) = your cost savings

**Key metrics:**
- **Target accuracy**: Minimum acceptable quality (e.g., 99%)
- **Oracle usage rate**: % of queries sent to expensive model
- **Cost savings**: (1 - oracle_rate) × (proxy_cost / oracle_cost)

**The connection to evals**: Model cascades require a *confidence score* — and a way to validate that the confidence score is calibrated. This is another application of the TPR/TNR framework from HW3: you need to know how often the proxy's "high confidence" is actually correct.

### Observability: Phoenix & OpenTelemetry (Optional HW)

Production LLM applications need the same observability as traditional services — but with LLM-specific dimensions:

**What to instrument:**
- **Every LLM call**: Model, tokens in/out, latency, cost, response
- **Every tool call**: Tool name, arguments, result, latency, success/failure
- **Every state transition**: Agent state, timestamps, outcomes
- **Every session**: User ID, session ID, conversation history

**Arize Phoenix** provides this observability layer:

```python
# Instrumentation with OpenTelemetry + Phoenix
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from phoenix.otel import register

tracer_provider = register(project_name="recipe-bot")
LiteLLMInstrumentor().instrument(tracer_provider=tracer_provider)

# Now every LiteLLM call is automatically traced:
# - Input/output tokens and content
# - Model name and parameters
# - Latency and cost
# - Session grouping
```

**Why this matters for evals**: Observability gives you the *raw material* for evaluation. Without traces, you can't build transition matrices (HW5). Without token counts, you can't optimize cost (cascades). Without session grouping, you can't track conversation-level quality.

**The monitoring loop:**
```
Production traffic → Trace collection → Sample evaluation
    ↓                                        ↓
 Alert if quality drops          Update eval pipeline if needed
```

### Cost Management in LLM Applications

LLM costs scale linearly with usage. Every LLM call costs money. In an agentic application with multiple LLM calls per user query, costs compound:

```
Recipe Bot cost per query:
├── ParseRequest (LLM call)         ~$0.001
├── PlanToolCalls (LLM call)        ~$0.001
├── GenCustomerArgs (LLM call)      ~$0.001
├── GenRecipeArgs (LLM call)        ~$0.001
├── ComposeResponse (LLM call)      ~$0.002
├── Query Rewrite (LLM call)        ~$0.001
└── Total per query:                ~$0.007

At 1M queries/day = ~$7,000/day = ~$210,000/month
```

**Cost reduction strategies:**
1. **Model cascade**: Route 70% of queries to cheap model → 70% cost reduction
2. **Caching**: Same query → same response (if deterministic enough)
3. **Prompt optimization**: Shorter prompts = fewer input tokens
4. **Batch processing**: Aggregate eval runs during off-peak hours
5. **Query rewriting**: A single rewrite call saves multiple retry calls

**The eval cost**: Your evaluation pipeline also costs money. Running an LLM judge on 439 traces at ~$0.005 per judgment = ~$2.20. Running it on 10,000 traces = ~$50. This is cheap compared to the product cost, but it's not free — factor it into your budget.

---

# Part IV — Synthesis & Quick Reference

## Chapter 12: Cross-Cutting Learnings

These are the big lessons that span all five homeworks and apply to any AI evaluation project:

### 1. Evaluation is Hierarchical

Start broad to find priorities. Go narrow to measure one thing precisely. Zoom into mechanism to understand why.

```
Broad (HW2)     → "Where does it break?"     → Taxonomy
Narrow (HW3)    → "How often, statistically?" → Pass rate + CI
Component (HW4) → "Which component?"          → Retrieval metrics
Pipeline (HW5)  → "Which step, which owner?"  → Transition matrix
```

Each level answers a different question. You need all four levels for a complete diagnostic.

### 2. Ground Truth is the Constraint

Every measurement downstream depends on the quality of your labels. The LLM judge is only as good as the test set it's calibrated on. The bias correction is only valid if the test labels are correct. This is why I human-reviewed every single label in HW3 — that 241-label dataset is the foundation of everything.

**Implication**: Invest disproportionately in labeling quality. 200 perfect labels beat 2,000 noisy labels.

### 3. Silent Failures are More Dangerous Than Crashes

A crash shows up in error logs immediately. A silent failure — agent responds politely but incorrectly — only shows up in your eval pipeline, churn data, or user research.

```
Crash:          Error log → Alert → Fix → Done (minutes to hours)
Silent failure: No log → No alert → Users churn → Maybe noticed
                in quarterly review → Maybe fixed (weeks to months)
```

Uptime monitoring tells you nothing about silent failures. This is the entire reason evaluation infrastructure exists.

### 4. Query Quality Drives Everything

In HW4, our 2-step salient fact extraction produced queries that outperformed the reference set by 8-10 pp on every metric. The quality of your test queries determines the quality of your evaluation.

**Bad queries**: "How do I make pasta?" (too generic, doesn't test anything)
**Good queries**: "How long should I simmer the paprika sauce before adding dumplings?" (specific, targets one recipe, uses rare terms)

### 5. Less is More for Lexical Search

The `expand` strategy hurt BM25 performance by 6.7 pp. Adding synonyms dilutes rare-term scores. For BM25 (and any TF-IDF-based system), the optimal query is *minimal and specific* — strip noise, keep rare terms.

This principle reverses for semantic search, where expansion helps. Know your retrieval algorithm before choosing a query strategy.

### 6. Small Targeted Fixes Have Outsized Impact

HW5 showed 28% of all failures trace to just 2 root causes affecting 3 queries. Fix those 2 issues (GenRecipeArgs prompt + corpus coverage) and you eliminate more than a quarter of all failures. This is the Pareto principle in action — most failures come from a small number of root causes.

### 7. Evaluation is Infrastructure, Not a Feature

The eval pipeline runs alongside the product pipeline. It doesn't change user experience. It doesn't add features. It just measures. But without it, you're flying blind. The PM who builds eval infrastructure before launch is playing a different game than the PM who ships first and measures later.

### 8. Uncertainty is Not Optional

62.6% sounds precise. [53%, 73%] tells you the truth — we're pretty sure it's between 53% and 73%, but we don't know exactly where. Reporting a point estimate without a confidence interval is misleading. Always include uncertainty.

---

## Chapter 13: Technical Concepts Glossary

### Evaluation Concepts

**Open Coding**: First-pass qualitative analysis where you read traces and write freeform observations without preconceived categories. Used in HW2 to discover failure patterns.

**Axial Coding**: Second-pass analysis where you group open codes into structured categories with clear definitions. Produces the failure mode taxonomy.

**Ground Truth**: Human-verified labels that define the "right answer" for evaluation. The foundation of all automated measurement. In HW3: 241 traces labeled PASS/FAIL by a human.

**LLM-as-Judge**: Using an LLM to evaluate the output of another LLM. The judge has a specialized prompt with criteria, policy rules, and few-shot examples. Must be calibrated against ground truth.

**TPR (True Positive Rate)**: Of all truly PASS items, what fraction does the judge correctly identify as PASS? Also called sensitivity or recall. Our judge: 82.2%.

**TNR (True Negative Rate)**: Of all truly FAIL items, what fraction does the judge correctly identify as FAIL? Also called specificity. Our judge: 88.9%.

**Balanced Accuracy**: (TPR + TNR) / 2. A single number summarizing judge quality that accounts for class imbalance. Our judge: 85.5%.

**False Positive (FP)**: Judge says PASS but it's actually FAIL. Dangerous — misses a real violation.

**False Negative (FN)**: Judge says FAIL but it's actually PASS. Annoying — underestimates quality.

**Judgy**: A Python library that corrects for known judge bias. Uses TPR/TNR from calibration to estimate the true pass rate from observed (biased) judge predictions. Produces a corrected estimate with confidence interval.

**Confidence Interval (CI)**: A range that likely contains the true value. Our 95% CI [53%, 73%] means: if we repeated this entire process 100 times, ~95 of those intervals would contain the true pass rate.

**Train/Dev/Test Split**: Three non-overlapping subsets of labeled data. Train provides few-shot examples. Dev is for iterating on the judge prompt. Test is locked — used once for final calibration, never tuned on.

### Retrieval Concepts

**BM25 (Best Matching 25)**: A keyword-based retrieval algorithm that scores documents by term frequency (TF) and inverse document frequency (IDF). Good for exact term matches; bad for paraphrases.

**TF (Term Frequency)**: How often a word appears in a document. More occurrences → higher score, with diminishing returns.

**IDF (Inverse Document Frequency)**: How rare a word is across all documents. Rare words (like "tuiles") get high IDF; common words (like "cook") get low IDF.

**Recall@k**: Fraction of queries where the target document appears in the top k results. Recall@5 = 81.3% means 81.3% of queries had the right recipe in the top 5.

**MRR (Mean Reciprocal Rank)**: Average of 1/rank across all queries. If the target is usually at rank 1, MRR ≈ 1.0. If usually at rank 3, MRR ≈ 0.33.

**RAG (Retrieval-Augmented Generation)**: Architecture where the LLM answers based on retrieved documents rather than its training data. Reduces hallucination, enables corpus updates without retraining.

**Query Rewriting**: Transforming a user's natural language query into a search-optimized form before retrieval. Three strategies tested: keywords (best for BM25), rewrite (neutral), expand (harmful for BM25).

**Dense Retrieval**: Using neural embeddings to find semantically similar documents. Handles paraphrases ("rise" ↔ "proof") but is slower and harder to debug than BM25.

**Hybrid Retrieval**: Combining BM25 (lexical) + dense (semantic) retrieval with score fusion. Typically outperforms either alone.

**Reranking**: Using a more powerful model (cross-encoder) to re-score the top-k results from retrieval. Improves precision within the candidate set.

### Agent Concepts

**Agent Loop**: The cycle of Plan → Execute → Observe → Re-plan that defines agentic behavior. The LLM decides what to do, executes it (via tools), observes results, and decides what to do next.

**Tool Calling**: The mechanism by which an LLM invokes external functions (APIs, databases, web search) with structured arguments. The LLM generates the arguments; the system executes the call.

**State Machine**: The abstraction of an agent's pipeline as a series of discrete states with transitions. Used in HW5 to build the transition matrix.

**Silent Failure**: When an agent encounters an error but continues generating a response that looks complete. The user gets an answer; it's just wrong. No error code, no alert.

**Error Propagation**: When a failure at step N corrupts all subsequent steps but the agent continues to a final response. The response reflects the upstream error but doesn't indicate it.

**Graceful Degradation**: Design pattern where the system falls back to a simpler but still useful behavior when a component fails. Instead of "try again later," provide a partial answer.

**Transition Matrix**: A matrix counting (last_success_state, first_failure_state) pairs across many traces. Visualized as a heatmap, it shows where in the pipeline failures concentrate.

### Production Concepts

**Model Cascade**: Routing queries to cheap or expensive models based on a confidence threshold. Maintains accuracy while reducing cost.

**Observability**: Instrumenting every LLM call, tool call, and state transition for monitoring, debugging, and evaluation. The raw material for evaluation at scale.

**OpenTelemetry**: A standard protocol for distributed tracing. Used to collect spans (individual operations) and traces (chains of operations) across a system.

---

## Chapter 14: The PM & Leadership Perspective

### Evaluation is a Product Feature

Without evaluation infrastructure, you have zero visibility into quality at scale. The eval pipeline is not a nice-to-have — it's the instrumentation layer that tells you whether your product works.

**The analogy**: A manufacturing plant without quality control sensors. The plant runs, products ship, but you don't know what percentage are defective until customers complain. Evaluation is quality control for AI.

### The Business Case for Eval Investment

| Without eval | With eval |
|---|---|
| Ship first, hope it works | Ship with measured quality and known gaps |
| Learn about failures from user complaints | Learn about failures before users see them |
| Prioritize fixes by gut feeling | Prioritize fixes by data (which failures are most common?) |
| Can't measure improvement after fixes | Before/after comparison with statistical rigor |
| No confidence in quality during handoff | Specific quality numbers with confidence intervals |
| "It works on my machine" | "62.6% dietary compliance [53%, 73%] on 439 traces" |

### How to Talk About Eval Results

**To engineers**: "Our judge has TPR 82.2% and TNR 88.9%. After bias correction, dietary compliance is 62.6% [53%, 73%]. The top 3 failure transitions account for 28% of all failures — two root causes, two teams."

**To PMs**: "Recipe Bot gets dietary restrictions right about 63% of the time. One in three dietary answers is wrong — that's a product safety risk. We know exactly where it breaks and who needs to fix it."

**To executives**: "We can improve dietary compliance from 63% to ~80% by fixing two root causes: a prompt engineering issue (days to fix) and a corpus coverage gap (weeks to fill). The eval infrastructure to measure this cost us 2 weeks to build and now runs automatically."

### The Heatmap as a Prioritization Tool

HW5's transition heatmap is not just a diagnostic — it's a backlog generator:

1. **Top 3 cells = 28% of failures = 2 root causes = 2 team conversations**
2. Each cell maps to a specific owner and fix timeline
3. The heatmap provides the *evidence* for engineering specs

This is how you turn an invisible, recurring, user-facing failure into a ranked, actionable engineering backlog with clear ownership.

### Silent Failures Are an Existential Risk

For safety-sensitive applications (dietary advice, medical information, financial guidance):

- A crash is embarrassing but safe — the user gets no answer
- A silent failure is dangerous — the user gets a *wrong* answer they trust

**At scale**: If Recipe Bot serves 1M queries/day and 37% of dietary answers are non-compliant, that's 370,000 potentially incorrect dietary answers per day. For a user with a severe food allergy, one wrong answer is one too many.

This is why evaluation infrastructure is not optional for any AI application where incorrect outputs have consequences.

---

## Chapter 15: Panel Discussion Cheat Sheet

Quick-reference answers for common questions in panel discussions about AI evaluation.

### "How do you evaluate LLM applications?"

> "You start broad — run 100 traces, manually review them, build a taxonomy of failure modes. Then go narrow — pick the most important dimension, build human-labeled ground truth, engineer an LLM-as-judge, calibrate it on a held-out test set, and run it at scale with statistical correction for judge bias. You end up with a corrected pass rate and confidence interval — a real number you can track over time."

### "What's an LLM-as-judge?"

> "It's using one LLM to evaluate the output of another. You give it criteria, policy rules, and few-shot examples. The key is calibrating it — you run it against human-labeled ground truth to measure its TPR and TNR, then use those numbers to correct for bias when you run it at scale. It's a measurement tool, not ground truth."

### "How do you know if your eval is good?"

> "Two things: balanced accuracy on a held-out test set, and the width of your confidence interval. If your judge has 85% balanced accuracy and your CI is ±10 pp, you know the measurement is useful but not precise. To improve: more ground truth labels, better judge prompt, more traces."

### "How do you evaluate RAG systems?"

> "Separate component eval from end-to-end eval. For retrieval: generate synthetic queries with known answers, measure Recall@k and MRR. For generation: LLM-as-judge on the final output. For the full system: both. We found a keywords query rewrite strategy improved Recall@5 from 81% to 91% — a simple change with outsized impact."

### "What's the biggest mistake people make with AI evaluation?"

> "Three tied for first: (1) Tuning on the test set — if you peek at test errors and adjust, your metrics are no longer unbiased. (2) Not building ground truth — you can't measure what you haven't labeled. (3) Ignoring silent failures — the agent always responds, so uptime monitoring tells you nothing about quality."

### "How do you handle the cost of evaluation?"

> "The eval pipeline itself is cheap — running a judge on 500 traces costs a few dollars. The expensive part is ground truth labeling. LLM pre-labeling + human review gets you 80% of the way. Start with 200 high-quality labels and scale from there. For production monitoring, sample traffic and run continuous eval on the sample."

### "How do you think about agent architecture?"

> "An agent is a loop: plan → execute → observe → re-plan. The key architectural decisions are: what tools does it have, how does it decide which to call, what happens when a tool fails, and how do you observe all of this. Every state transition should be logged. Every tool call should have a fallback. The agent should degrade gracefully — a partial answer beats 'try again later.'"

### "How do you prioritize what to fix?"

> "Build a transition matrix. Count where failures happen. The top cells tell you which root causes affect the most users. In our case, 28% of all failures traced to 2 root causes — one fixable in days (prompt engineering), one in weeks (corpus expansion). That's how you write an engineering spec with evidence."

### "What's the relationship between evals and observability?"

> "Observability gives you the raw material — traces, spans, tool calls, latencies. Evaluation gives you the judgment — was this trace good or bad? You need both. Without observability, you can't evaluate because you have no data. Without evaluation, observability just shows you things happening without telling you if they're happening *well*."

### "How do you think about evaluation for a new AI project?"

> "Day 1: Write the system prompt and run 50-100 queries manually. Week 1: Build a failure taxonomy from manual review. Week 2: Pick one dimension, label 200 traces, build an LLM-as-judge, calibrate it. Week 3: Run the judge at scale, get your baseline number with CI. Now every future change is measurable. This 3-week investment pays dividends for the entire project lifecycle."

### "What surprised you most about this work?"

> "Two things. First, the #1 failure mode was a product design issue — the system prompt told the bot to be simple, which conflicted with users asking for complex recipes. The model was doing exactly what we told it to; the instructions were wrong. Second, in HW5, 28% of failures traced to just 3 user queries. The heatmap looked like many different problems. Drilling in revealed one root cause repeated across different pipeline paths. You can't see this without evaluation infrastructure."

---

# Appendix A: My Recipe Bot Evaluation Results — All Numbers

| Metric | Value | Source |
|--------|-------|--------|
| **HW2: Broad pass rate** | 47% (100 traces) | Manual review |
| **HW2: Top failure mode** | User Constraint Ignored (32/100) | Taxonomy |
| **HW3: Ground truth labels** | 241 (161 PASS, 80 FAIL) | Human-reviewed |
| **HW3: Judge TPR (test)** | 82.2% | 109 test traces |
| **HW3: Judge TNR (test)** | 88.9% | 109 test traces |
| **HW3: Judge balanced accuracy** | 85.5% | (TPR + TNR) / 2 |
| **HW3: Raw pass rate** | 55.6% | Judge on 439 traces |
| **HW3: Corrected pass rate** | 62.6% [53%, 73%] | Judgy correction |
| **HW4: BM25 baseline Recall@5** | 81.3% | 193 queries |
| **HW4: BM25 baseline MRR** | 0.704 | 193 queries |
| **HW4: Keywords rewrite Recall@5** | 91.2% (+9.9 pp) | Same 193 queries |
| **HW4: Keywords rewrite MRR** | 0.785 (+0.081) | Same 193 queries |
| **HW4: Queries rescued** | 16 | Keywords vs baseline |
| **HW4: Queries degraded** | 2 | Keywords vs baseline |
| **HW5: Total traces analyzed** | 96 | Pre-labeled |
| **HW5: Top 3 cells** | 27/96 (28%) | Transition matrix |
| **HW5: Root causes** | 2 (schema translation + corpus coverage) | Drilldown |
| **HW5: Distinct failing queries** | 3 | Behind all 27 traces |

---

# Appendix B: File Index — What I Built

### HW2 — Broad Discovery
| File | Purpose |
|------|---------|
| `homeworks/hw2/my_failure_mode_taxonomy.md` | 5 failure modes with definitions, examples, frequencies |
| `homeworks/hw2/error_analysis.csv` | 100 labeled traces with open/axial codes |

### HW3 — LLM-as-Judge Pipeline
| File | Purpose |
|------|---------|
| `homeworks/hw3/scripts/my_generate_traces.py` | Generate traces via Recipe Bot (parallel, 5 per query) |
| `homeworks/hw3/scripts/my_generate_traces_big.py` | Large batch: 540 traces in 4 parallel batches |
| `homeworks/hw3/scripts/my_label_data.py` | LLM pre-labeling with expert nutritionist prompt |
| `homeworks/hw3/scripts/my_review_labels.py` | Browser UI for human review of labels |
| `homeworks/hw3/scripts/my_split_data.py` | Stratified train/dev/test split |
| `homeworks/hw3/scripts/my_evaluate_judge.py` | Judge evaluation with TPR/TNR, error analysis |
| `homeworks/hw3/scripts/my_review_predictions.py` | Browser UI for inspecting judge predictions |
| `homeworks/hw3/scripts/my_run_full_evaluation.py` | Final evaluation with judgy bias correction |
| `homeworks/hw3/data/my_raw_traces.csv` | 60 initial traces |
| `homeworks/hw3/data/my_raw_traces_big.csv` | 439 traces for full evaluation |
| `homeworks/hw3/data/my_labeled_traces.csv` | 241 human-verified ground truth labels |
| `homeworks/hw3/data/my_train_set.csv` | 36 train traces |
| `homeworks/hw3/data/my_dev_set.csv` | 96 dev traces |
| `homeworks/hw3/data/my_test_set.csv` | 109 test traces |
| `homeworks/hw3/results/my_judge_prompt.txt` | Final 500-line judge prompt with 10 few-shot examples |
| `homeworks/hw3/results/my_judge_performance_dev.json` | Dev metrics (TPR 82.8%, TNR 96.9%) |
| `homeworks/hw3/results/my_judge_performance_test.json` | Test metrics (TPR 82.2%, TNR 88.9%) |
| `homeworks/hw3/results/my_judgy_test_data.json` | Calibration data for judgy |
| `homeworks/hw3/results/my_final_evaluation.json` | Final: 62.6% [53%, 73%] |
| `homeworks/hw3/results/my_evaluation_narrative.md` | Full narrative connecting HW2 → HW3 |

### HW4 — Retrieval Evaluation
| File | Purpose |
|------|---------|
| `homeworks/hw4/scripts/my_generate_queries.py` | 2-step salient fact → query generation (193 queries) |
| `homeworks/hw4/scripts/my_evaluate_retrieval.py` | BM25 evaluation with Recall@k, MRR, failure analysis |
| `homeworks/hw4/scripts/my_evaluate_retrieval_with_agent.py` | 3 query rewrite strategies: keywords, rewrite, expand |
| `homeworks/hw4/data/my_synthetic_queries.json` | 193 synthetic queries with source recipe IDs |
| `homeworks/hw4/results/my_retrieval_evaluation.json` | Reference query results (Recall@5: 73.0%) |
| `homeworks/hw4/results/my_retrieval_evaluation_own_queries.json` | Our query results (Recall@5: 81.3%) |
| `homeworks/hw4/results/my_retrieval_comparison.json` | All 4 strategies compared |
| `homeworks/hw4/results/my_agent_enhanced.json` | Best strategy (keywords) details |
| `homeworks/hw4/results/my_hw4_analysis.md` | Full write-up with failure analysis |

### HW5 — Pipeline Diagnostics
| File | Purpose |
|------|---------|
| `homeworks/hw5/analysis/my_transition_analysis.py` | Transition matrix + analysis |
| `homeworks/hw5/results/my_trace_explorer.html` | Interactive heatmap + drilldown dashboard |
| `homeworks/hw5/results/my_hw5_analysis.md` | Full write-up: root causes, clusters, PM learnings |

---

# Appendix C: The One-Page Summary

If you only have 60 seconds, here's the entire course:

**The problem**: LLM applications fail silently. They always respond. The response is just sometimes wrong.

**The solution**: Build evaluation infrastructure that measures quality automatically, with statistical rigor.

**The method**:
1. Go broad: Manual review → failure taxonomy → prioritize
2. Go narrow: Pick one dimension → label ground truth → build LLM-as-judge → calibrate on test set → run at scale → correct for bias → report with CI
3. Go deep: Evaluate components independently (retrieval, tools) → build transition matrix → find root causes → assign owners

**The numbers from Recipe Bot**:
- 47% broad pass rate (HW2)
- 62.6% dietary compliance [53%, 73%] (HW3)
- 81% → 91% Recall@5 with query rewrite (HW4)
- 28% of failures → 2 root causes → 2 teams (HW5)

**The principle**: Evaluation is not testing. It's not a one-time activity. It's infrastructure that runs alongside your product, measures quality continuously, and turns invisible failures into an actionable engineering backlog.

---

*Built during Shreyas & Hamel's AI Evals Course, 2025. All measurements from my own Recipe Bot evaluation pipeline.*
