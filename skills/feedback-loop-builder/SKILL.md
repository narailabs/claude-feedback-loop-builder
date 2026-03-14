---
name: feedback-loop-builder
description: Retrofit self-improving feedback loops into existing skills or agents. Use when user wants to make a skill or agent learn from its usage and mistakes, improve itself over time, or add adaptive behavior that gets smarter with each run. Supports both skill targets (SKILL.md) and agent targets (CLAUDE.md, AGENTS.md). The feedback loop teaches the skill/agent HOW to work better — not what to work on. Always asks user before committing any changes.
---

# Feedback Loop Builder

Analyze an existing skill or agent, then inject a self-improvement feedback loop that makes it learn from every run — without ever changing its scope.

## Core Concept

Three lifecycle phases get injected into the target:

| Phase | When | What | User Involved? |
|-------|------|------|-----------------|
| **@BOOT** | Start of every run | Load `feedback/patterns.md` + recent run history | No (silent) |
| **@REVIEW** | After task completion | Self-assess: corrections, friction, approach diffs | No (internal) |
| **@EVOLVE** | After review | Propose pattern changes, explain reasoning | **Yes — user approves each change** |

The loop modifies ONLY `feedback/patterns.md` and `feedback/run-log.jsonl`. It never touches the skill/agent's core content, purpose, or scope.

## Workflow

### Step 1: Analyze the Target

Run the analysis script. Accept a **name**, **description**, or **path**:

```bash
# By name (searches installed plugins + ~/src/)
python scripts/analyze_target.py browser-qa
python scripts/analyze_target.py pdf

# By path
python scripts/analyze_target.py ./my-agent-project
python scripts/analyze_target.py /abs/path/to/skill
```

Resolution order:
1. Direct path (if input contains `/` or starts with `.` or `~`)
2. Relative to CWD
3. `~/.claude/plugins/installed_plugins.json` — exact then partial name match
4. `~/src/`, `~/projects/`, `~/dev/` — directory name match (also tries `claude-<name>`, `<name>-skill`, `<name>-agent`)

The script outputs JSON with:
- `type`: `"skill"` or `"agent"`
- `name`, `description`, `sections` (scope boundaries)
- `already_has_feedback_loop`: whether one exists already
- `resolution`: how the target was found (registry, source_dir, path)
- Structure info (scripts/, references/, feedback/ dirs)

If the target already has feedback loop markers, ask the user whether to upgrade or skip.

### Step 2: Understand the Target's Domain

Read the target's main config file (SKILL.md for skills, CLAUDE.md/AGENTS.md for agents). Identify:

1. **What the target does** — its core purpose (this is the scope that must NEVER change)
2. **How it does it** — its workflows, patterns, decision points (this is what the feedback loop improves)
3. **Domain-specific concerns** — what kinds of mistakes or inefficiencies are likely in this domain

Use these to tailor the `[SKILL-SPECIFIC]` and `[AGENT-SPECIFIC]` placeholders in the lifecycle templates.

### Step 3: Create the Feedback Infrastructure

Create the `feedback/` directory inside the target:

```
feedback/
├── patterns.md    — starts with empty sections (Anti-Patterns, Preferred Approaches, Edge Cases)
└── run-log.jsonl   — starts empty
```

See [references/skill-integration.md](references/skill-integration.md) for the exact `patterns.md` starter template.

### Step 4: Inject Lifecycle Sections

Based on target type, load the appropriate template:

- **Skills**: Read [references/skill-integration.md](references/skill-integration.md) for the full template and tailoring guidelines
- **Agents**: Read [references/agent-integration.md](references/agent-integration.md) for the full template and tailoring guidelines

**Tailoring rules:**
- Replace ALL `[SKILL-SPECIFIC]` / `[AGENT-SPECIFIC]` placeholders with real, domain-relevant content
- The @BOOT focus should match what typically goes wrong in this domain
- The @REVIEW checklist should probe for the target's common failure modes
- The @EVOLVE proposal format stays unchanged (What/Why/Impact table)

**Injection rules:**
- Add lifecycle sections at the END of the existing file, after all current content
- Separate with a horizontal rule (`---`)
- NEVER modify existing content above the injection point

### Step 5: Present Changes to User

**CRITICAL — Do not write anything without this step.**

Before writing anything, show the user:

1. **What files will be created** (`feedback/patterns.md`, `feedback/run-log.jsonl`)
2. **What will be added to SKILL.md or agent config** (the tailored lifecycle sections — show the full text)
3. **Why each placeholder was replaced the way it was**
4. **Scope confirmation**: "The feedback loop will only modify files inside `feedback/`. Your skill/agent's core behavior is untouched."

Ask: *"Does this look right? Want to modify anything before I apply it?"*

Only proceed after explicit user approval.

### Step 6: Validate

**For skills:**
Invoke the `skill-creator` skill to validate the modified skill structure. If the user wants, run evals to verify the feedback loop triggers correctly.

**For agents:**
Spawn an **Opus agent** (model: opus) to review the injection. The agent should:
1. Verify lifecycle sections are correctly placed and don't break existing behavior
2. Confirm scope guard rules are sound
3. Simulate a dry-run @BOOT → @REVIEW → @EVOLVE cycle
4. Report any issues

See [references/agent-integration.md](references/agent-integration.md) for the Opus agent validation prompt template.

### Step 7: Confirm with User

Show the user a summary:
- ✅ Files created
- ✅ Sections injected
- ✅ Validation results
- 📋 How the feedback loop will work on next run

## Scope Guard Rules

The feedback loop improves HOW the skill/agent works, never WHAT it does:

| ✅ Allowed | ❌ Forbidden |
|-----------|-------------|
| Add pattern: "prefer library X over Y for this case" | Change skill name or description |
| Add pattern: "check for edge case Z before proceeding" | Add new capabilities |
| Add anti-pattern: "don't assume format W" | Remove existing functionality |
| Refine approach ordering | Modify frontmatter |
| Note user preferences for style/approach | Alter files outside `feedback/` |

If @EVOLVE produces a suggestion that would change scope, it must flag:
> "⚠️ This change may affect what the skill/agent does, not just how. Proceed?"

## Example: Retrofitting a PDF Skill

**Target analysis** reveals: skill processes PDFs, uses pypdf/pdfplumber, has scripts for extraction and form filling.

**Tailored @BOOT**:
> "Pay special attention to patterns about library choice (pypdf vs pdfplumber vs reportlab) and PDF structure assumptions."

**Tailored @REVIEW**:
> "Did library selection cause issues? Were PDF structure assumptions wrong (e.g., assuming all pages same size)?"

**After 3 runs**, `feedback/patterns.md` might contain:

```markdown
## Anti-Patterns
- Do NOT use pypdf for text extraction on scanned PDFs — always use pdfplumber with OCR fallback
- Do NOT assume PDF forms are AcroForm — check for XFA forms first

## Preferred Approaches
- When merging PDFs with different page sizes, normalize to the first document's page size
- For form filling, always run extract_form_field_info.py first to discover field names

## Edge Cases
- Password-protected PDFs: try empty string password before asking user
- PDFs with embedded fonts may render differently — warn user about font substitution
```

Each pattern was proposed by @EVOLVE with What/Why/Impact, and approved by the user.
