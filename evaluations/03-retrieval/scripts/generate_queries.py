#!/usr/bin/env python3
"""Generate our own synthetic queries for HW4 retrieval evaluation.

Uses llm-exec (Intuit's LLM service) instead of OpenAI/litellm.
Two LLM calls per recipe:
  1. Extract salient fact  — what specific technical detail lives in this recipe?
  2. Generate query        — what would a real user ask to find that detail?

Output: data/synthetic_queries.json
Each record: { query, salient_fact, source_recipe_id, source_recipe_name, ... }

Usage:
    python scripts/generate_queries.py
    python scripts/generate_queries.py --max 50   # generate fewer for testing
"""

import os
import sys
import json
import time
import argparse
import functools
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import httpx

load_dotenv(override=True)
print = functools.partial(print, flush=True)

# ── llm-exec config ────────────────────────────────────────────────────────────
LLM_EXEC_BASE_URL           = os.environ.get("LLM_EXEC_BASE_URL", "")
LLM_EXEC_MODEL_PATH         = os.environ.get("LLM_EXEC_MODEL_PATH", "")
INTUIT_PRIVATEAUTH_HEADER   = os.environ.get("INTUIT_PRIVATEAUTH_HEADER", "")
INTUIT_EXPERIENCE_ID        = os.environ.get("INTUIT_EXPERIENCE_ID", "")
INTUIT_ORIGINATING_ASSETALIAS = os.environ.get("INTUIT_ORIGINATING_ASSETALIAS", "")

MAX_WORKERS  = 4     # parallel LLM calls
TIMEOUT      = 60.0  # seconds per call


def call_llm(prompt: str) -> Optional[str]:
    """Single LLM call via llm-exec. Returns text or None on failure."""
    url = f"{LLM_EXEC_BASE_URL.rstrip('/')}/v3/{LLM_EXEC_MODEL_PATH}/chat/completions"
    headers = {
        "Authorization": INTUIT_PRIVATEAUTH_HEADER,
        "Content-Type": "application/json",
        "intuit_experience_id": INTUIT_EXPERIENCE_ID,
        "intuit_originating_assetalias": INTUIT_ORIGINATING_ASSETALIAS,
    }
    payload = {"messages": [{"role": "user", "content": prompt}]}
    try:
        resp = httpx.Client(timeout=TIMEOUT).post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise RuntimeError(f"llm-exec {resp.status_code}: {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  [LLM ERROR] {e}")
        return None


# ── Prompt 1: extract salient fact ─────────────────────────────────────────────
SALIENT_FACT_PROMPT = """\
You are analyzing a recipe to identify its most distinctive, retrievable detail.

Find 1-2 specific technical facts from this recipe that:
- Are hard to guess without reading the recipe
- Involve precise numbers (temps, times, weights) or named techniques
- Someone might specifically search for

Focus on: temperatures, cooking times, marinating durations, appliance settings,
dough resting times, internal temps, mixing techniques with timing.

Return only the facts — no preamble.

Recipe:
{recipe_text}

Salient fact(s):"""


# ── Prompt 2: generate user query ──────────────────────────────────────────────
QUERY_PROMPT = """\
A home cook needs help with a specific step. Write ONE natural, conversational question they might type or ask.

Rules:
- Sound like a real person, not a textbook
- Focus on this specific detail: {salient_fact}
- Do NOT mention the recipe name
- Be specific enough that only this recipe's info would fully answer it

Recipe context: {recipe_name} using {top_ingredients}

Examples of good query style:
- "How long should I let my brioche dough rest before shaping?"
- "What internal temp should pork tenderloin reach to be safe but juicy?"
- "How do I know when my caramel is ready — what color should it be?"

Write ONE query only, no quotes:"""


def format_recipe(recipe: Dict[str, Any]) -> str:
    """Flatten recipe into text for LLM consumption."""
    parts = [f"Name: {recipe.get('name', '')}"]
    if recipe.get("description"):
        parts.append(f"Description: {recipe['description'][:300]}")
    if recipe.get("ingredients"):
        parts.append(f"Ingredients: {', '.join(recipe['ingredients'][:10])}")
    if recipe.get("steps"):
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(recipe["steps"][:20]))
        parts.append(f"Steps:\n{steps_text}")
    return "\n".join(parts)


def process_single_recipe(recipe: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Two LLM calls for one recipe:
      call 1 → salient_fact
      call 2 → query
    Returns a query record or None on failure.
    """
    recipe_text = format_recipe(recipe)

    # ── Call 1: salient fact ────────────────────────────────────────────────
    fact_prompt = SALIENT_FACT_PROMPT.format(recipe_text=recipe_text)
    salient_fact = call_llm(fact_prompt)
    if not salient_fact or len(salient_fact.strip()) < 10:
        return None

    # ── Call 2: user query ──────────────────────────────────────────────────
    top_ingredients = ", ".join(recipe.get("ingredients", [])[:5])
    query_prompt = QUERY_PROMPT.format(
        salient_fact=salient_fact[:300],
        recipe_name=recipe.get("name", ""),
        top_ingredients=top_ingredients,
    )
    query = call_llm(query_prompt)
    if not query or len(query.strip()) < 10:
        return None

    return {
        "query": query.strip().strip('"'),
        "salient_fact": salient_fact.strip(),
        "source_recipe_id": recipe["id"],
        "source_recipe_name": recipe["name"],
        "ingredients": recipe.get("ingredients", []),
        "cooking_time": recipe.get("minutes", 0),
        "tags": recipe.get("tags", []),
    }


def generate_all(recipes: List[Dict[str, Any]], max_queries: int) -> List[Dict[str, Any]]:
    """Run generation in parallel across recipes."""
    target = recipes[:max_queries]
    total  = len(target)
    results = []
    failed  = 0

    print(f"Generating queries for {total} recipes ({MAX_WORKERS} workers, 2 LLM calls each)...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(process_single_recipe, r): r for r in target}
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                results.append(result)
            else:
                failed += 1
            if i % 10 == 0 or i == total:
                print(f"  [{i}/{total}] generated={len(results)} failed={failed}")

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=200,
                        help="Max queries to generate (default 200)")
    args = parser.parse_args()

    hw4_dir    = Path(__file__).resolve().parent.parent
    data_dir   = hw4_dir / "data"
    output     = data_dir / "synthetic_queries.json"
    recipes_path = data_dir / "processed_recipes.json"

    if not recipes_path.exists():
        print(f"ERROR: {recipes_path} not found. Run process_recipes.py first.")
        sys.exit(1)

    recipes = json.loads(recipes_path.read_text())
    print(f"Loaded {len(recipes)} recipes from {recipes_path.name}")

    start = time.time()
    queries = generate_all(recipes, args.max)
    elapsed = time.time() - start

    if not queries:
        print("ERROR: No queries generated. Check your token in .env")
        sys.exit(1)

    with open(output, "w") as f:
        json.dump(queries, f, indent=2)

    print(f"\nDone in {elapsed:.0f}s")
    print(f"  Generated : {len(queries)} queries")
    print(f"  Failed    : {args.max - len(queries)} recipes")
    print(f"  Saved to  : {output}")

    print("\nSample (first 3):")
    for q in queries[:3]:
        print(f"\n  Recipe : {q['source_recipe_name']}")
        print(f"  Fact   : {q['salient_fact'][:100]}...")
        print(f"  Query  : {q['query']}")


if __name__ == "__main__":
    main()
