# Agent Failure Diagnosis: Where Quality Silently Degrades

Given 96 pre-labeled agent traces, each containing exactly one silent failure, built a transition matrix showing where the agent succeeds last and fails first across 10 internal pipeline states. Visualized it as a heatmap and drilled into the hottest cells to identify root causes.

## The Key Insight

**The agent keeps talking after it fails.** After the failure point, the assistant continues responding and the conversation looks complete from the outside. The user gets a polite deflection ("try again later!") instead of an error. No crash, no alert, no ticket.

This is why uptime monitoring tells you nothing about AI product quality. You need an eval pipeline to see these failures.

## The Heatmap

![Failure Transition Heatmap](results/failure_transition_heatmap.png)

The top 3 cells account for **27 of 96 failures (28%)**. Drilling in reveals all 27 traces come from the same 3 user queries:
- "I need a gluten-free dinner idea for four"
- "What vegetarian high-protein meal can I cook tonight?"
- "Suggest a healthy breakfast using oatmeal"

The heatmap looks like many different failure modes. It's actually **one root cause repeated**: the system has no reliable path for dietary-restriction queries.

## Root Cause Analysis

Two distinct failure clusters with different owners and different fixes:

| Cluster | Transition | Count | Root Cause | Owner |
|---------|-----------|-------|-----------|-------|
| A | PlanToolCalls → GenRecipeArgs | 10 | Agent can't translate dietary query into structured search args | ML/Prompt engineer |
| B | GetCustomerProfile → GetRecipes + GenCustomerArgs → GetRecipes | 17 | Recipe DB returns empty for dietary queries | Content/Data team |

**Cluster A**: The agent understood the question and planned to search, then silently failed to construct the search query. The user gets a deflection. They rephrase, same failure repeats. Zero value delivered.

**Cluster B**: The agent ran the full pipeline (fetched user profile, built the search), then the DB returned empty. Worse than Cluster A because the agent did more work and still failed. "Try again later" destroys trust.

## What I Learned

1. **The heatmap is a prioritization tool.** Top 3 cells = 28% of failures. Fix two root causes, eliminate more than a quarter of all failures. That's how you write an engineering spec with evidence.

2. **Silent failures are more dangerous than crashes.** A crash shows up in error logs. A polite wrong answer only shows up in your eval pipeline, churn data, or user research.

3. **54% of failures occur at tool execution states** (GetRecipes, GetCustomerProfile, GetWebInfo), not at LLM generation states. The agent's reasoning largely works; it's the tool calls that fail.

## Files

| File | Description |
|------|------------|
| `results/failure_transition_heatmap.png` | Heatmap visualization |
| `results/trace_explorer.html` | Interactive browser dashboard with heatmap, drilldown, and trace inspector (open in browser, no server needed) |
| `results/analysis.md` | Full write-up with failure analysis and PM learnings |
| `data/labeled_traces.json` | 96 pre-labeled agent traces |
