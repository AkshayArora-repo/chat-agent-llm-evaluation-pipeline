# Recipe Bot Evaluation: From Broad Discovery to Narrow Measurement

A single narrative connecting HW2 (broad first), ground truth labeling, judge calibration, and the final big-trace run.

---

## 1. HW2: Go broad first

**What we did:** Ran Recipe Bot on **synthetic queries** (diverse constraints: time, skill, ingredients, diet), manually reviewed **100 traces**, and built a **failure-mode taxonomy**.

**Result:** **47% Pass, 53% Fail** on that sample.

**Main failure modes you found:**
- **User Constraint Ignored** (32% of failures) — e.g. user asked for “challenging,” bot gave simple.
- **LLM Service Blocked** (16% of failures) — risk screening false positives.
- Others: unclear language, incomplete structure, missing personalization.

**PM takeaway:** Broad evaluation answered “where does it break?” and “what to fix first?” — not a single quality number, but a **prioritized list of failure modes**. Dietary issues showed up as one dimension among many.

---

## 2. HW3: Pick one dimension and build ground truth

**Decision:** Narrow to **one** criterion — **dietary adherence** (does the recipe actually match the user’s stated restriction?). Same Recipe Bot, same system prompt; we’re now measuring this one thing in a repeatable way.

**What we did:**
- Generated **241 traces** from 60 dietary queries (our Recipe Bot, `dietary_queries.csv`).
- **Pre-labeled** with an LLM, then **human-reviewed** every label → **ground truth**.
- **Label distribution:** 161 PASS, 80 FAIL (~67% / 33%).

**PM takeaway:** Ground truth is **human-verified** on a subset. That subset is the only place we “know” the right answer; everything else we’ll infer with a judge and statistics.

---

## 3. Train / Dev / Test: Judge development and calibration

**Split (stratified):**
- **Train** (36): few-shot examples for the judge prompt (no metrics).
- **Dev** (96): iterate on prompt and policy until judge behavior is acceptable.
- **Test** (109): **locked** evaluation — no more changes; this set gives our **TPR/TNR** for the judge.

**Judge iteration on Dev:**
- First version: very strict (e.g. “ambiguous ingredient = FAIL”) → **TPR 0.69, TNR 1.0** (many false negatives).
- We softened policy (e.g. “default version” test for ambiguous ingredients) → **TPR 0.83, TNR 0.97**.
- We **locked** the prompt and did **not** tune on Test.

**Final judge performance on Test (the numbers we use for correction):**
- **TPR = 0.82** (when the recipe is truly PASS, judge says PASS 82% of the time).
- **TNR = 0.89** (when the recipe is truly FAIL, judge says FAIL 89% of the time).
- **Balanced accuracy = 0.86.**

**PM takeaway:** The judge is a **measurement tool**. We calibrated it on dev, then measured its accuracy on test. Those TPR/TNR numbers tell us how much to trust (and correct) the judge when we run it on **new** data where we have no labels.

---

## 4. New raw “big” traces: Scale and correct

**What we did:**
- Generated **439 new traces** (same 60 dietary queries, 9 runs each, our Recipe Bot; 101 calls failed due to rate limits / risk screening, so we have 439 successful).
- **No human labels** on these 439 — that’s the “production-like” setting: we only have judge predictions.
- Ran our **locked judge** on all 439 → **raw observed success rate = 55.6%** (judge said PASS 55.6% of the time).
- Used **judgy** with Test-set TPR/TNR to **correct for judge bias** → **corrected success rate = 62.6%**, **95% CI [53.0%, 72.8%]**.

**Why correction?** The judge is slightly strict (TPR &lt; TNR), so it flags some truly compliant recipes as FAIL. Judgy uses the known TPR/TNR to estimate what the **true** pass rate would be if we had labels; the +7 pp correction is consistent with that.

**PM takeaway:** On **new** data, we don’t have labels. We only have judge predictions. The **corrected 62.6% [53–73%]** is our best estimate of Recipe Bot’s **actual dietary compliance** on this distribution of queries, with uncertainty expressed as a confidence interval.

---

## 5. How it all fits together

| Stage | Question we answered | Output |
|-------|----------------------|--------|
| **HW2 (broad)** | Where does Recipe Bot fail, and how? | Taxonomy: constraint ignored, LLM blocked, etc.; 47% pass on 100 traces. |
| **HW3 labels** | What is “right” for dietary adherence on a subset? | 241 traces, human-reviewed → 161 PASS, 80 FAIL (ground truth). |
| **Train/Dev/Test** | Is our judge a good measuring tool? | Locked judge: TPR 0.82, TNR 0.89 on **held-out test** (109 traces). |
| **Big unlabeled run** | What is Recipe Bot’s dietary compliance at scale? | 439 traces, judge only → **corrected 62.6% [53–73%]** (judgy). |

**Single story:**  
We went **broad** (HW2) to find failure modes and prioritize. We went **narrow** (HW3) on **dietary adherence**: built **ground truth**, trained and calibrated an **LLM-as-judge** on train/dev/test, then ran that judge on **new raw traces** and used **judgy** to turn judge predictions into an **estimate of true compliance** with a confidence interval. So: **discovery (HW2) → definition and calibration (labels + dev/test) → scaled measurement (big traces + judgy)**.

**PM bottom line:**  
- **HW2** = “What’s broken?” (47% pass in that broad sample; taxonomy drives roadmap).  
- **Ground truth** = “What does ‘correct’ mean?” for one criterion (diet), on 241 traces.  
- **Dev/Test** = “Is our judge reliable?” (TPR/TNR locked on test).  
- **Big traces** = “How does the bot perform on new data?” → **~63% dietary compliance [53–73%]** — one number, with uncertainty, you can use for goals, risk, and iteration.
