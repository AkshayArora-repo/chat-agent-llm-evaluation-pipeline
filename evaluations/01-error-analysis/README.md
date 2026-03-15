# Error Analysis: Finding Where the Recipe Bot Breaks

Ran the Recipe Bot on 100 synthetic queries spanning dietary restrictions, time constraints, skill levels, and ingredient limitations. Manually reviewed every trace using open and axial coding to build a failure mode taxonomy.

## Key Finding

**~47% pass rate.** More than half the responses had meaningful quality issues, but not all in the same way.

## Failure Mode Taxonomy

Four categories emerged from the data:

| Failure Mode | % of Failures | Example |
|-------------|---------------|---------|
| User constraint ignored | 32% | User asked for "challenging," bot gave a simple recipe |
| LLM service blocked | 16% | Risk screening false positives on safe queries |
| Unclear language | ~26% | Ambiguous phrasing, incomplete instructions |
| Incomplete structure | ~26% | Missing steps, no ingredient quantities |

The full taxonomy with examples is in [failure_mode_taxonomy.md](failure_mode_taxonomy.md).

## Why This Matters

Broad evaluation answers "where does it break?" and "what to fix first?" Not a single quality number, but a **prioritized list of failure modes**. Without this step, you'd automate measurement of the wrong thing.

This analysis directly informed [02-llm-judge](../02-llm-judge/), where we narrowed to one dimension (dietary adherence) and built a repeatable, automated measurement pipeline.

## Files

| File | Description |
|------|------------|
| `failure_mode_taxonomy.md` | Taxonomy of Recipe Bot failure modes with examples |
| `error_analysis.csv` | Labeled error analysis for all 100 traces |
