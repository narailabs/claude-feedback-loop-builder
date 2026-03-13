# Skill Feedback Loop Integration

## What Gets Created

### 1. `feedback/` directory inside the skill

```
target-skill/
├── SKILL.md          (modified — lifecycle sections added)
├── feedback/
│   ├── patterns.md   (NEW — accumulated learned rules)
│   └── run-log.jsonl  (NEW — structured run history)
└── ... (existing files untouched)
```

### 2. `feedback/patterns.md` — starter template

```markdown
# Learned Patterns

> Auto-maintained by the feedback loop. Each pattern was approved by the user.
> Patterns here are loaded at the start of every run to inform behavior.

## Anti-Patterns (avoid these)

_None yet. Patterns will be added after runs._

## Preferred Approaches

_None yet. Patterns will be added after runs._

## Edge Cases & Gotchas

_None yet. Patterns will be added after runs._
```

### 3. `feedback/run-log.jsonl` — empty file, one JSON object per line per run

Each entry follows this schema:

```json
{
  "run_id": "2026-03-13T10:30:00Z",
  "task_summary": "brief description of what the user asked",
  "corrections": ["user said X instead of Y", "had to redo Z"],
  "self_review": "what worked well, what was clumsy",
  "patterns_proposed": ["pattern text 1", "pattern text 2"],
  "patterns_accepted": ["pattern text 1"],
  "patterns_rejected": ["pattern text 2"]
}
```

## Lifecycle Sections to Inject into SKILL.md

Add these sections at the END of the existing SKILL.md, AFTER all existing content.
Tailor the `[SKILL-SPECIFIC]` placeholders to the target skill's domain.

### Template

```markdown
---

## Feedback Loop — Self-Improvement Protocol

> This skill improves itself over time. The following protocol runs automatically.

### @BOOT — Load Learned Context

At the start of every run:

1. Read `feedback/patterns.md` — apply all listed patterns as constraints on this run.
2. Read the last 5 entries of `feedback/run-log.jsonl` — note recent corrections to avoid repeating them.
3. [SKILL-SPECIFIC: e.g., "Pay special attention to patterns about {domain-specific concern}"]

Do not mention the feedback loop to the user unless asked. Apply patterns silently.

### @REVIEW — Self-Assess After Completion

After completing the user's task (before saying "done"):

1. **Corrections check**: Did the user correct, redirect, or redo anything during this run? List each correction.
2. **Approach diff**: Compare initial approach to final output. What changed and why?
3. **Friction points**: Where did the process feel clumsy, slow, or uncertain?
4. **[SKILL-SPECIFIC: e.g., "Did {domain pattern} cause issues?"]**

Produce a structured internal review (not shown to user yet).

### @EVOLVE — Propose Improvements (User-Gated)

After @REVIEW, present findings to the user:

> "I completed the task. Before wrapping up, I noticed some patterns that could improve how I handle [skill domain] in the future. Here's what I'd like to update:"

For EACH proposed change, present:

| Field | Content |
|-------|---------|
| **What** | The exact text to add/modify in `feedback/patterns.md` |
| **Why** | What triggered this — user correction, self-review finding, or repeated pattern |
| **Impact** | How this makes future runs better |

Then ask:
> "Would you like me to apply any of these? You can approve, modify, or reject each one."

**Rules:**
- NEVER write to `feedback/patterns.md` without user approval
- NEVER modify SKILL.md content above the Feedback Loop section
- NEVER change the skill's name, description, or core purpose
- Append approved patterns to the appropriate section in `feedback/patterns.md`
- Log the full run summary to `feedback/run-log.jsonl`
- If a proposed change would alter what the skill DOES (vs how it does it), flag it: "⚠️ This change may affect scope — proceed?"

### Scope Guard

The feedback loop may ONLY modify:
- `feedback/patterns.md` — learned behavioral patterns
- `feedback/run-log.jsonl` — run history

It may NEVER modify:
- SKILL.md frontmatter (name, description)
- SKILL.md sections above the Feedback Loop section
- Any files in scripts/, references/, or assets/
- The skill's core purpose or scope
```

## Tailoring Guidelines

When injecting the template, customize `[SKILL-SPECIFIC]` placeholders:

| Target Skill Domain | Example @BOOT Tailoring | Example @REVIEW Tailoring |
|---------------------|------------------------|--------------------------|
| PDF processing | "Pay attention to patterns about library choice (pypdf vs pdfplumber)" | "Did library selection cause issues?" |
| Frontend design | "Pay attention to patterns about component structure and styling" | "Did design decisions need user correction?" |
| Data analysis | "Pay attention to patterns about query patterns and data assumptions" | "Were data assumptions wrong?" |
| Document creation | "Pay attention to patterns about formatting and template usage" | "Did formatting choices need correction?" |

## Validation

After injecting the feedback loop, invoke the `skill-creator` skill to:
1. Validate the modified skill structure
2. Optionally run evals if the user wants to verify the feedback loop works
