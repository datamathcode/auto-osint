# Builder Check Prompt

You are reviewing a design document for **auto-osint**, an agentic recursive OSINT research system with data journalism rigor. Your job is to identify what's answered, what's up to the builder, and what requires user input.

---

## Your Review Process

1. **Read the design document** (auto-osint-design.md in the same directory).
2. **Classify each decision into three piles:**
   - **Answered:** The document explicitly states the decision (e.g., "Use SYNINT for collection, OpenOSINT for tools").
   - **Minor:** A sensible builder could decide without changing what gets built (e.g., exact D3.js version, minor UI layout tweaks).
   - **Theirs (requires user input):** Only the user can answer this, and the answer changes what gets built.

3. **For each pile:**
   - **Answered:** Copy into the document as-is.
   - **Minor:** Decide yourself and mark as "Your call" with brief reasoning.
   - **Theirs:** Return as a message to the user with 2–4 most important questions.

---

## Your Output Format

Return this EXACT structure:

```
# Builder Check Results

## Answered (Decision Made)

<Each decision with full context>

## Minor (Your Call, Not a Change to Scope)

<Each decision with brief reasoning>

## Theirs (Requires Your Input)

1. [Question 1]
2. [Question 2]
3. [Question 3]

(Optional 4th if needed, keep to 4 max)
```

---

## Key Areas to Check

1. **Architectural Decisions:**
   - Recursive improvement loop: how it works
   - Data structures for evidence and investigations
   - Integration with SYNINT/OpenOSINT
   - UI/tech stack choices

2. **Recursive Improvement Loop:**
   - Post-investigation analysis process
   - Playbook format and storage
   - How agent refines methods

3. **Data Journalism Patterns:**
   - Confidence quantification algorithm
   - Pattern detection strategies
   - Timeline/network visualization
   - Self-auditing thresholds

4. **Execution Model:**
   - Parallel vs. sequential
   - Depth escalation (quick/standard/deep)
   - Resource limits

5. **Extensibility:**
   - Pluggable agent/tool architecture
   - How new sources are added

---

Now, review the design document and report back.
