# HW4 Analysis: Recipe Bot Retrieval Evaluation

## What We Built

We extended Recipe Bot with a **BM25 retrieval layer** — a keyword-based search engine that finds relevant recipes from a corpus of 200 processed Food.com recipes. The goal: when a user asks a specific technical cooking question (exact temperatures, timing, technique), the system retrieves the correct source recipe before generating an answer.

This is the retrieval step of a **RAG (Retrieval-Augmented Generation)** architecture. If retrieval fails, even a perfect LLM cannot recover — it will hallucinate or give vague answers. So retrieval quality is a platform multiplier.

---

## Pipeline

```
processed_recipes.json (200 recipes)
        │
        ├──► BM25 index (my_bm25_index.pkl)
        │    - 5,779 unique tokens
        │    - avg 517 tokens per recipe
        │    - word rarity (IDF) + frequency (TF) scoring
        │
        ├──► my_generate_queries.py (2 LLM calls per recipe via llm-exec)
        │    - Call 1: extract salient technical fact from recipe
        │    - Call 2: generate realistic user query about that fact
        │    → 193 queries saved to my_synthetic_queries.json
        │
        └──► my_evaluate_retrieval.py (no LLM — pure BM25 + math)
             - For each query: BM25 scores all 200 recipes
             - Check: is source_recipe_id in top 1/3/5/10?
             → my_retrieval_evaluation_own_queries.json
```

---

## Results

| Metric | Our queries (193) | Reference queries (200) |
|--------|------------------|------------------------|
| **Recall@1** | **63.2%** | 53.5% |
| **Recall@3** | **77.2%** | 68.0% |
| **Recall@5** | **81.3%** | 73.0% |
| **Recall@10** | **86.5%** | 81.0% |
| **MRR** | **0.704** | 0.623 |
| Target found (any rank) | 167/193 (86.5%) | 162/200 (81.0%) |
| Complete misses | 26/193 (13.5%) | 38/200 (19.0%) |

Our queries outperformed the reference on every metric. The gap (+9.7 pp on Recall@1, +8.3 pp on Recall@5) is because our `salient_fact` extraction prompt produced more concrete, specific terms (exact temperatures, ingredient names, technique words) that BM25 can anchor on via keyword overlap.

**Query length vs performance:**

| Query length | n | Recall@5 | MRR |
|---|---|---|---|
| Short (≤15 words) | 18 | 83.3% | 0.718 |
| Medium (16-25 words) | 143 | 79.7% | 0.684 |
| Long (>25 words) | 32 | **87.5%** | **0.788** |

Longer queries perform better — they contain more specific terms for BM25 to match on, reducing ambiguity.

---

## What Works Well

**Specific, rare-term queries** are where BM25 excels. When a query contains a word that appears in only 1-2 recipes, BM25 correctly surfaces that recipe at rank 1.

Examples of successful retrievals:
- "How long to simmer chicken broth for dumplings?" → `amazing hungarian chicken paprikash with dumplings` (rank 1) — the word `dumplings` is rare in the corpus (IDF ~4.9), making it a strong signal.
- "How long to brown chicken thighs for paella and steep saffron?" → `al andalus paella` (rank 1) — `paella` and `saffron` are rare terms.
- "Baking time and temperature for honey brown tuiles?" → `almond tuiles` (rank 1) — `tuiles` appears in only one recipe.

**Pattern:** BM25 succeeds when the query contains at least one **rare, dish-specific term** (ingredient name, dish name, or unusual technique) that uniquely identifies the target recipe.

---

## Failure Analysis

**26 complete misses** (target not in top 10). Four overlapping failure modes:

### Failure Mode 1: Generic bread recipes dominate — 17/26 (65%)

Three short recipes (`5 minute artisan bread`, `amish friendship bread`, `100 whole wheat bread`) appear in the top 3 results for the majority of failures. These short docs with common baking words (`dough`, `knead`, `bake`, `flour`, `rise`) are over-ranked by BM25 because their brevity inflates their term frequency scores.

Example:
```
Query:  "After kneading for the full 10 minutes, does the dough really need to rise for over two hours?"
Target: alton brown s overnight cinnamon rolls
Got:    #1 100 whole wheat bread, #2 a new england holiday bread, #3 5 minute artisan bread
```

### Failure Mode 2: High competition in baking domain — 16/26 (62%)

The corpus contains 30+ baking/dough recipes that all share the same vocabulary. BM25 cannot distinguish between them when a query uses only generic baking terms without a unique anchor.

### Failure Mode 3: Query lacks unique anchor term — 14/26 (54%)

Queries under 20 words with no dish-specific term give BM25 nothing to differentiate on. "How long do I mix on low and then medium-high, and what is the bake time at 350?" could describe any cake recipe.

### Failure Mode 4: Numbers present but not unique — 13/26 (50%)

Even queries with specific numbers like "375°F", "2 hours", "150 degrees" fail because those exact numbers appear across many recipes. BM25 treats `375` as just another token — it cannot understand that `375 + cheesecake + 2 hours` is a unique combination.

Example:
```
Query:  "What if after the 30 minutes at 375 and two hours at 250, the center still isn't 150 degrees?"
Target: absolutely the best new york cheesecake gluten free
Got:    #1 10 calorie chocolate miracle noodle cookies, #2 3 step fall off the bone ribs, #3 all butter pie crust
```

---

## How I Would Build an Agent Around This Retriever

In production at scale (e.g. Recipe Bot serving 1M users), I would layer the following on top of BM25:

**1. Query Rewrite Agent (immediate win)**
Before BM25, an LLM rewrites the user's natural language query into a retrieval-optimized form:
- User: "how do I get my dough to rise properly before baking?"
- Rewritten: "overnight cinnamon rolls dough rise 2 hours knead 10 minutes"

This adds dish-specific terms that BM25 can anchor on, directly addressing Failure Modes 3 and 4.

**2. Hybrid Retrieval (medium-term)**
Combine BM25 (lexical) with a dense vector retriever (semantic). BM25 handles exact term matches; dense retrieval handles paraphrases and synonyms ("broil" ↔ "high-heat roast"). A simple linear combination (BM25 score + cosine similarity) typically lifts Recall@5 by 10-15%.

**3. Corpus-level fixes (quick wins)**
- Downweight or deduplicate generic short recipes that dominate results (the "5 minute artisan bread" problem)
- Add recipe-specific metadata fields (cuisine type, primary technique) as boosted search fields

**4. Feedback loop (long-term)**
Log queries where users click past rank 3 or reformulate their query — those are retrieval failures. Use them to retrain the query rewriter and identify corpus gaps.

---

## Part 3: Query Rewrite Agent Results

We ran three LLM rewrite strategies on all 193 queries before BM25 retrieval and compared against baseline.

| Strategy | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |
|----------|----------|----------|----------|-----------|-----|
| **Baseline** | 63.2% | 77.2% | 81.3% | 86.5% | 0.704 |
| **keywords** | **69.9%** | **86.5%** | **91.2%** | **93.8%** | **0.785** |
| rewrite | 60.6% | 77.7% | 83.4% | 90.7% | 0.705 |
| expand | 55.4% | 68.9% | 74.6% | 86.5% | 0.641 |

**Best strategy: `keywords`**
- Recall@5: 81.3% → **91.2%** (+9.9 pp)
- MRR: 0.704 → **0.785** (+0.081)
- **16 previously-missed queries rescued**
- Only 2 previously-found queries degraded

### Why `keywords` won

The keywords strategy strips the query down to bare search terms:
- Original: *"After kneading for the full 10 minutes, does the dough really need to rise for over two hours?"*
- Keywords: `knead dough rise overnight cinnamon rolls`

This removes conversational noise (`after`, `really`, `does`) and lets BM25 focus on the rare, meaningful tokens. The `rewrite` strategy tried to be too clever — rephrasing sometimes introduced new words that didn't match recipe text. The `expand` strategy added too many synonyms, diluting the score of rare terms.

### Why `expand` hurt performance

Adding synonyms backfired. BM25 weights rare terms highly — if you add common synonyms (`bake`, `oven`, `cook`) to a query that already has a rare term (`tuiles`), you dilute the rare term's contribution. Expand strategy dropped Recall@5 by 6.7 pp vs baseline.

### Key insight

Query rewriting is most valuable when the original query is **conversational and noisy**. Our queries already contained specific terms (from the 2-step LLM generation process), so the marginal gain came from stripping noise, not from adding new information.

---

## Ideas for Improving Retrieval Performance

| Idea | Measured lift | Effort |
|------|--------------|--------|
| **Keywords rewrite agent** | **+9.9% Recall@5** (measured) | Low |
| Downweight short generic docs | +3-7% Recall@5 (estimated) | Low |
| Hybrid BM25 + dense retrieval | +10-20% Recall@5 (estimated) | Medium |
| Better query generation (require unique anchor) | +5-10% Recall@5 (estimated) | Low |
| Reranker (cross-encoder) on top-20 | +5-10% Recall@1 (estimated) | Medium |

---

## Key Takeaway

BM25 baseline: **Recall@5 81.3%**, MRR 0.704. With a simple keywords rewrite agent: **Recall@5 91.2%**, MRR 0.785 — a +9.9 pp improvement with minimal engineering effort.

The failure mode is well-understood: BM25 breaks when queries are noisy/conversational and when the corpus has many near-duplicate documents (the "5 minute artisan bread" problem). The fix is not to replace BM25 but to strip query noise first (keywords strategy), then layer semantic retrieval for the remaining hard cases. That combination would likely push Recall@5 above 95% and make Recipe Bot's factual answers reliably grounded in real recipe data.

---

## How This Works in a Real Product

**Query rewrite is completely invisible to the user.** Here is what actually happens end-to-end when someone uses Recipe Bot:

```
User types:
"I'm trying to make something for my lactose-intolerant friend,
 does your lemon tart recipe use real butter?"

         ↓
┌─────────────────────┐
│  Query Rewrite LLM  │  ← ~200ms, invisible to user
└─────────────────────┘
         ↓
 "lemon tart dairy free butter substitute lactose"
         ↓
┌─────────────────────┐
│   BM25 Retriever    │  ← finds top-5 recipes
└─────────────────────┘
         ↓
 [lemon tart recipe, dairy-free tart, ...]
         ↓
┌─────────────────────┐
│   Recipe Bot LLM    │  ← answers using retrieved context
└─────────────────────┘
         ↓
"Yes, this recipe uses butter. Here's a dairy-free version
 using coconut oil..."
```

The user asked a conversational question. The system silently converted it to search keywords, retrieved the right recipe, and answered with grounded facts. The user just sees a good answer.

### Naive RAG vs. Production RAG

Most tutorials show the naive version. Real products are different:

```
Naive RAG:       User query → Retriever → LLM → Answer
                 (breaks on conversational queries)

Production RAG:  User query → Query Rewriter → Retriever → Reranker → LLM → Answer
                 (each layer handles a specific failure mode)
```

| Layer | What it fixes | What we built |
|-------|--------------|---------------|
| Query Rewriter | Lexical mismatch — user says "rise" but recipe says "proof" | ✅ keywords strategy (+9.9pp) |
| Retriever | Finds candidate documents | ✅ BM25 baseline |
| Reranker | Re-scores top-20 with a smarter model | Not built (estimated +5-10pp) |
| LLM | Answers only from retrieved context | Recipe Bot (existing) |

### Why this matters for dietary safety

For a dietary-sensitive product, retrieval failure is not just a bad metric — it has real consequences:

| Without rewrite | With rewrite |
|----------------|-------------|
| Recall@5: 81.3% | Recall@5: 91.2% |
| ~35 queries retrieve wrong recipe | ~17 queries retrieve wrong recipe |
| Bot answers from wrong recipe or memory | Bot answers from correct recipe |
| User gets incorrect dietary information | User gets correct dietary information |

A user asking "is this recipe safe for my nut allergy?" getting an answer based on the wrong retrieved recipe is a product safety issue, not just a quality issue.

### The strategic unlock: corpus as a product lever

Before RAG: Recipe Bot answers from model memory — hallucination risk, stale knowledge, no auditability.

After RAG + rewrite: Recipe Bot answers from a grounded corpus — measurable accuracy, updatable without retraining, fully auditable.

The corpus becomes a **product lever** you can operate independently of the model:
- Add new recipes without touching the model or redeploying
- A/B test different recipe versions and measure retrieval impact
- Audit exactly which recipe was used to answer any question (traceability)
- Swap BM25 for dense retrieval later without changing anything else
- Identify corpus gaps from retrieval failure logs

This is the difference between a chatbot and a knowledge system. The evaluation work in this homework is what makes that distinction measurable.
