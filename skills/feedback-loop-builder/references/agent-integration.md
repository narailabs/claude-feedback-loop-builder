# Agent Feedback Loop Integration

Agents are defined by config files (CLAUDE.md, AGENTS.md, agent.md, or similar).
The integration pattern is similar to skills but adapted for agent contexts.

## What Gets Created

### 1. `feedback/` directory alongside the agent config

```
agent-project/
├── CLAUDE.md          (modified — lifecycle sections added)
├── feedback/
│   ├── patterns.md    (NEW — accumulated learned rules)
│   └── run-log.jsonl   (NEW — structured run history)
└── ... (existing files untouched)
```

### 2. Same `feedback/patterns.md` and `feedback/run-log.jsonl` as skills

See skill-integration.md for the file templates — they are identical.

## Lifecycle Sections to Inject into Agent Config

Add at the END of the agent's config file, AFTER all existing content.

### Template

```markdown
---

## Feedback Loop — Self-Improvement Protocol

> This agent improves itself over time. The following protocol runs automatically.

### @BOOT — Load Learned Context

At the start of every session:

1. Read `feedback/patterns.md` — apply all listed patterns as constraints.
2. Read the last 5 entries of `feedback/run-log.jsonl` — note recent corrections.
3. [AGENT-SPECIFIC: e.g., "Pay special attention to patterns about {agent's domain}"]

Apply patterns silently. Do not mention the feedback loop unless asked.

### @REVIEW — Self-Assess After Completion

After completing the user's request (before saying "done"):

1. **Corrections check**: Did the user correct, redirect, or redo anything? List each.
2. **Approach diff**: Compare initial approach vs final output.
3. **Friction points**: Where was the process clumsy or uncertain?
4. **[AGENT-SPECIFIC: e.g., "Did {domain concern} cause issues?"]**

Produce a structured internal review.

### @EVOLVE — Propose Improvements (User-Gated)

After @REVIEW, present findings:

> "Before wrapping up, I noticed some patterns that could improve how I handle [agent domain] in the future:"

For EACH proposed change, present:

| Field | Content |
|-------|---------|
| **What** | The exact text to add/modify in `feedback/patterns.md` |
| **Why** | What triggered this — user correction, self-review, or repeated pattern |
| **Impact** | How this makes future runs better |

Ask: "Would you like me to apply any of these? You can approve, modify, or reject each one."

**Rules:**
- NEVER write to `feedback/patterns.md` without user approval
- NEVER modify agent config content above the Feedback Loop section
- NEVER change the agent's core purpose or identity
- Append approved patterns to `feedback/patterns.md`
- Log run summary to `feedback/run-log.jsonl`
- If a proposed change would alter what the agent DOES (vs how), flag it: "⚠️ Scope change — proceed?"

### Scope Guard

May ONLY modify:
- `feedback/patterns.md`
- `feedback/run-log.jsonl`

May NEVER modify:
- Agent config sections above the Feedback Loop
- The agent's core purpose, tools, or identity
- Other project files
```

## Tailoring for Agent Types

| Agent Type | @BOOT Focus | @REVIEW Focus |
|------------|-------------|---------------|
| Code agent | "Patterns about architecture decisions and coding style" | "Did architecture or style choices need correction?" |
| Research agent | "Patterns about source selection and synthesis approach" | "Were sources appropriate? Did synthesis need redoing?" |
| DevOps agent | "Patterns about deployment strategies and error handling" | "Did deployment steps fail or need manual intervention?" |
| Writing agent | "Patterns about tone, structure, and audience fit" | "Did tone or structure need user correction?" |

## Validation

After injecting the feedback loop into an agent, spawn an **Opus agent** to:

1. **Review the injection**: Verify lifecycle sections are correctly placed and don't break existing agent behavior
2. **Check scope guard**: Confirm the feedback loop can only modify feedback/ files
3. **Dry-run test**: Simulate a @BOOT → @REVIEW → @EVOLVE cycle to verify the flow makes sense for this specific agent
4. **Run evals** (if user wants): Test the agent with sample prompts to verify the feedback loop triggers correctly

### Opus Agent Validation Prompt Template

```
Review the feedback loop that was just added to the agent at [PATH].

1. Read the agent config file and verify:
   - The Feedback Loop section is at the END, after all existing content
   - @BOOT, @REVIEW, @EVOLVE sections are present and correctly structured
   - Scope guard rules are clear and correct
   - [AGENT-SPECIFIC] placeholders have been replaced with real content

2. Check that no existing agent behavior was altered

3. Simulate a dry run:
   - What would @BOOT load?
   - After a hypothetical task, what would @REVIEW capture?
   - What kind of pattern would @EVOLVE propose?

4. Report any issues or improvements needed
```
