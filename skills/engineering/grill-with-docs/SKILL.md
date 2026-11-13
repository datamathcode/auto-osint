---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
disable-model-invocation: true
---

When reviewing or validating a design document, ADR, or glossary:

## Step 1: Load grilling skill

Call `skill_view("grilling")` and read its full instructions. Grilling is a design-tree method: every decision branches into sub-decisions you haven't resolved yet. Build questions that expose unclear assumptions.

## Step 2: Load domain-modeling skill

Call `skill_view("domain-modeling")` and read its full instructions. Domain modeling is the active discipline: challenge terms, sharpen fuzzy language, update the glossary as decisions crystallize.

## Step 3: Work design tree in rounds

- **Frontier:** Decisions whose prerequisites are settled — you can ask these now without guessing.
- **Format:** Number questions, give recommended answers, wait for user input before next round.
- **Facts:** Dispatch sub-agents for facts you need to look up; ask decisions to the user.
- **Progression:** As answers come in, recompute frontier and ask next round until no frontier remains.

## Step 4: Capture decisions immediately

- Update glossary as terms get resolved (domain-modeling skill).
- Offer ADRs sparingly (domain-modeling skill): hard to reverse, surprising without context, result of a real trade-off.

## Step 5: Complete

Stop when frontier is empty: every branch visited, nothing assumed silently. Do not proceed to implementation until user confirms shared understanding.