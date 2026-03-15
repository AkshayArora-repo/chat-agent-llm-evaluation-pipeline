# Failure Mode Taxonomy — Recipe Bot Error Analysis

## Summary

- **Total traces analyzed:** 100
- **Pass:** 47 (47%)
- **Fail:** 53 (53%)

---

## Unclear Language and Instructions

**Definition:** The bot uses jargon, vague descriptions, or overly complex phrasing that a busy home cook or novice would struggle to understand.

**Frequency:** 3 out of 100 traces (3%)

**Examples from traces:**

- **SYN001** — Query: "easy halal turkish recipe with pantry stuff"
  - Note: language not simple. words like saute aromatic.

- **SYN020** — Query: "Challenge me! 💪 I want to make a cool, high-protein Korean dish. I need to use up ground turkey, cottage cheese, and som"
  - Note: optional add on instructions not clear,seens like a bunch things were suggested which would confuse the user. 

- **SYN026** — Query: "low fodmap recipe under an hour using pantry staples, nothing mexican, intermediate skill"
  - Note: instructions on how much to heat broth, and what to do with it till the dish is being made not clear. same thing with roast rice, what does that mean ?
---

## User Constraint Ignored

**Definition:** The bot does not follow the user's stated constraints around time, dietary restrictions, or cooking skill level, including defaulting to simple recipes when users explicitly request complex or advanced dishes.

**Frequency:** 32 out of 100 traces (32%)

**Examples from traces:**

- **SYN005** — Query: "any easyto-make halal turkish meals from pantry staples?"
  - Note: suggesting have recipe everytime 

- **SYN007** — Query: "hey i need a keto recipe that takes like 30-60 mins. i have to use avocado sardines and pork rinds. im not a beginner so"
  - Note: ttime preference not followed by bot 

- **SYN010** — Query: "Help me find an intermediate keto recipe for tonight I have about 45 minutes to an hour. Must use sardines avocado and p"
  - Note: user suggested time not followed , also are bread crums keto ??
---

## Incomplete Recipe Structure

**Definition:** The bot produces a recipe where ingredients mentioned in the steps are missing from the ingredients list, or where non-standard equipment is used without being called out.

**Frequency:** 2 out of 100 traces (2%)

**Examples from traces:**

- **SYN002** — Query: "Simple turkidh halal food i can make? using what i have"
  - Note: did not ask what ingredients user have 

- **SYN018** — Query: "I have Ground Turkey, KIMCHI, and cottage cheese and want to make something high-protien and Korean inspired. I'm an oka"
  - Note: ingidients usedin steps were not mentoined under ingredietns secition
---

## Missing Personalization

**Definition:** The bot does not attempt to understand the user's situation or gives the same generic response regardless of the query context.

**Frequency:** 2 out of 100 traces (2%)

**Examples from traces:**

- **SYN002** — Query: "Simple turkidh halal food i can make? using what i have"
  - Note: did not ask what ingredients user have 

- **SYN005** — Query: "any easyto-make halal turkish meals from pantry staples?"
  - Note: suggesting have recipe everytime 
---

## LLM Service Blocked Response

**Definition:** The LLM infrastructure blocked the bot's response due to a false positive in the risk screening filter, resulting in the user receiving an error instead of a recipe.

**Frequency:** 16 out of 100 traces (16%)

**Examples from traces:**

- **SYN004** — Query: "looking for low effort   halal turkish recipes   i can make with basic ingredients"
  - Note: LLM service error - risk screening blocked response (profanity filter false positive on recipe content)

- **SYN022** — Query: "Whats a LOW EFFORT meal i can make that is low FODMAP and takes between 30 and 60 mins"
  - Note: LLM service error - risk screening blocked response (profanity filter false positive on recipe content)

- **SYN023** — Query: "show me a simple low fodmap receipe that takes less than an hour plz 🙏"
  - Note: LLM service error - risk screening blocked response (profanity filter false positive on recipe content)

---

## Distribution Chart

```
User Constraint Ignored:          ████████████████████████████████ (32)
LLM Service Blocked:              ████████████████ (16)
Unclear Language & Instructions:  ███ (3)
Incomplete Recipe Structure:      ██ (2)
Missing Personalization:          ██ (2)
```

## Key Insight

The dominant failure mode is **User Constraint Ignored** (32 traces, 60% of all failures). Most of these are cases where users explicitly asked for complex, advanced, or challenging recipes, but the bot defaulted to simple and quick alternatives. This is a direct conflict in the system prompt which instructs the bot to "prioritize clarity, simplicity, and speed" — causing it to override explicit user requests for complexity. This is a product design issue, not a model quality issue.

The second largest failure mode is **LLM Service Blocked** (16 traces, 30% of all failures) — Intuit's risk screening filter incorrectly flagging normal recipe content as profanity. This is a platform reliability issue that requires coordination with the llm-exec team.
