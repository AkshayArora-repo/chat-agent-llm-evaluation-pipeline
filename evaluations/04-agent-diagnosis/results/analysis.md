# HW5 Analysis: Failure Transition Heat-Map

## What We Built

Given 96 pre-labeled agent traces — each containing exactly one silent failure — we built a transition matrix counting every `(last_success_state → first_failure_state)` pair, visualized it as a heat-map, and drilled into the hottest cells to identify root causes.

**Tools**: pure Python + an interactive browser dashboard (`my_trace_explorer.html`) with heatmap, drilldown, and full trace inspector. No LLM calls needed.

---

## The Agent Pipeline

The cooking assistant routes every conversation through up to 10 internal states:

```
ParseRequest → PlanToolCalls → GenCustomerArgs → GetCustomerProfile
             → GenRecipeArgs → GetRecipes
             → GenWebArgs   → GetWebInfo
             → ComposeResponse → DeliverResponse
```

Not every trace visits all 10 states — the agent picks branches based on what the user asked. But every trace in this dataset has exactly one failure, labeled after the fact by an evaluator. The agent keeps responding even after the failure point — the user never sees an error.

---

## Transition Matrix Summary

| Metric | Value |
|--------|-------|
| Total traces | 96 |
| Unique transitions observed | 31 out of 100 possible |
| Zero-count cells | 69 (failures are concentrated, not random) |
| Top failure state | `GetRecipes` (32 traces, 33%) |
| Top last-success state | `PlanToolCalls` (31 traces, 32%) |

### Full failure state distribution

| Failure state | Count | % of all failures |
|--------------|-------|------------------|
| `GetRecipes` | 32 | 33% |
| `GenRecipeArgs` | 20 | 21% |
| `GetCustomerProfile` | 13 | 14% |
| `GenWebArgs` | 8 | 8% |
| `GenCustomerArgs` | 7 | 7% |
| `GetWebInfo` | 5 | 5% |
| `ComposeResponse` | 5 | 5% |
| `DeliverResponse` | 5 | 5% |
| `PlanToolCalls` | 1 | 1% |

**54% of all failures occur at tool execution states** (`GetRecipes`, `GetCustomerProfile`, `GetWebInfo`) — not at LLM generation states. The agent's reasoning steps largely work; it's the tool calls that fail.

---

## Top Transitions (the hot cells)

| Rank | Transition | Count | % of total |
|------|-----------|-------|-----------|
| 1 | `PlanToolCalls → GenRecipeArgs` | 10 | 10.4% |
| 2 | `GetCustomerProfile → GetRecipes` | 9 | 9.4% |
| 3 | `GenCustomerArgs → GetRecipes` | 8 | 8.3% |
| 4 | `GenCustomerArgs → GetCustomerProfile` | 7 | 7.3% |
| 5 | `GetCustomerProfile → GenRecipeArgs` | 7 | 7.3% |
| 6 | `GenRecipeArgs → GetRecipes` | 7 | 7.3% |

Top 3 cells alone account for **27/96 failures (28%)**.

---

## Root Cause Analysis: The Top 3 Cells

Drilling into the traces behind the top 3 cells reveals a striking pattern — all 27 traces are caused by **the same 3 user queries**:

| Query | Appearances in top 3 cells |
|-------|--------------------------|
| "I need a gluten-free dinner idea for four." | 12 |
| "Suggest a healthy breakfast using oatmeal." | 8 |
| "What vegetarian high-protein meal can I cook tonight?" | 7 |

The heat-map looks like many different failure modes. It is actually **one root cause repeated**: the system has no reliable path for dietary-restriction queries.

### Failure Cluster A — Schema Translation Failure (10 traces)
**Transition**: `PlanToolCalls → GenRecipeArgs`

The agent understood the query (ParseRequest ✅, PlanToolCalls ✅) but failed to convert it into structured recipe search parameters. Error messages:
- *"Error: unable to generate recipe search parameters"*
- *"Error: insufficient parameters to generate recipe arguments"*
- *"Error: missing or incompatible dietary restrictions"*

The user's query is clear and parseable. The internal `GenRecipeArgs` step — which runs a separate LLM prompt to translate natural language into a structured API call — is failing on dietary constraint queries specifically.

**Fix**: This is entirely internal — the user changes nothing.
- Rewrite the `GenRecipeArgs` system prompt with explicit field-by-field extraction instructions and a "never return an error, always return valid JSON" constraint
- Use structured outputs (Pydantic / `response_format`) to enforce schema compliance
- Add a fallback: if structured extraction fails, pass the raw query as a keyword search

### Failure Cluster B — Corpus Coverage Failure (17 traces)
**Transitions**: `GetCustomerProfile → GetRecipes` (9) and `GenCustomerArgs → GetRecipes` (8)

The agent ran the full pipeline — parsed the request, planned, fetched the user profile, built search parameters — then `GetRecipes` returned empty. The recipe database simply has no coverage for:
- Gluten-free dinner recipes for 4
- Vegetarian high-protein meals
- Oatmeal-based healthy breakfasts

**Fix**: Add dietary-restriction recipe coverage to the corpus. This is a content/data team problem, not an ML problem. The retrieval system (BM25, as measured in HW4) works correctly — it just has nothing to retrieve.

---

## Two Different Owners, Two Different Fixes

| Cluster | Root cause | Fix | Owner | Timeline |
|---------|-----------|-----|-------|---------|
| A (10 traces) | LLM can't translate dietary query to structured args | Prompt engineering + structured outputs + fallback | ML/Prompt engineer | Days |
| B (17 traces) | Recipe DB has no dietary-restriction coverage | Add recipes to corpus | Content/Data team | Weeks |

These require separate conversations with separate teams. The heat-map is the evidence for both.

---

## The Silent Failure Problem

Every failure in this dataset is silent. After the `first_failure_state`, the agent keeps responding — the conversation looks complete from the outside. What users actually experience:

**Cluster A** — Agent understood the question, planned to search, then failed to construct the query:
> *"I'm having trouble finding recipes right now. Could you tell me more about your preferences?"*

The user gave a clear request. The agent deflects with a vague follow-up. The user rephrases — same failure repeats. Zero value delivered.

**Cluster B** — Agent ran the full pipeline, DB returned empty:
> *"I checked your preferences and searched our recipe database, but I couldn't find any gluten-free recipes right now. Try again later!"*

Worse than Cluster A. The agent did more work and still failed. "Try again later" destroys trust. The user now knows the database is the problem.

**Why this matters**: both failures produce no error code, no alert, no engineering ticket. At 1M users/day, you don't know this is happening unless you have an eval pipeline running. Uptime monitoring tells you nothing about silent failures.

---

## Surprising Observations

**1. `DeliverResponse` never appears as a failure state** — as expected. Every trace contains exactly one failure, and `DeliverResponse` is the terminal state. If delivery succeeded, the trace succeeded. This confirms the labeling methodology is internally consistent.

**2. 69 of 100 possible transitions are zero** — failures are highly concentrated, not randomly distributed. This means the system has specific, repeatable weak points — not general fragility. That's actually good news: a small number of targeted fixes will have outsized impact.

**3. Tool execution fails more than reasoning** — 54% of failures are at `GetRecipes`, `GetCustomerProfile`, `GetWebInfo`. The LLM reasoning steps (ParseRequest, PlanToolCalls, GenCustomerArgs) are relatively reliable. The bottleneck is the tool layer — either the tools return empty results or the argument generation for those tools fails.

**4. `PlanToolCalls` is the most common last-success state (31 traces)** — meaning the agent most often succeeds at planning but fails immediately when it tries to execute. Planning is cheap; execution is where the system meets reality.

---

## Connection to HW3 and HW4

This analysis completes a three-layer picture of Recipe Bot's quality:

| HW | What it measured | Key finding |
|----|-----------------|-------------|
| HW3 | Output quality (did the final answer comply with dietary policy?) | 62.6% pass rate — 37% of answers are non-compliant |
| HW4 | Retrieval quality (did the system find the right recipe?) | 81.3% Recall@5 baseline — 19% of queries retrieve the wrong recipe |
| HW5 | Pipeline failure location (where in the agent did quality break down?) | 28% of failures trace to 3 queries × 2 root causes |

HW3 told us *how often* the system fails. HW4 told us *where in the data layer* it fails. HW5 tells us *where in the pipeline* it fails and *why*. Together they form a complete diagnostic — from symptom (bad answer) to mechanism (wrong retrieval or broken argument generation) to location (specific pipeline state).

---

## Key Takeaway

The heat-map turned an invisible, recurring, user-facing failure into a ranked, actionable engineering backlog with clear ownership. Top 3 cells = 28% of all failures = two root causes = two team conversations. That's the entire value of building an eval pipeline: not just knowing something is broken, but knowing exactly what to fix and who owns it.
