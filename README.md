# Feedback Loop Builder

Make any Claude skill or agent self-improving. Retrofits a feedback loop that learns from usage and mistakes, getting smarter with every run — without ever changing the skill/agent's scope.

## What It Does

- **Analyzes** your existing skill (SKILL.md) or agent (CLAUDE.md/AGENTS.md) to understand its structure and domain
- **Injects** three lifecycle phases (@BOOT, @REVIEW, @EVOLVE) that run automatically
- **Learns** patterns from user corrections, self-assessment, and repeated mistakes
- **Asks before changing anything** — every proposed improvement is shown to you with What/Why/Impact before being applied
- **Validates** changes using the skill-creator for skills, or an Opus agent review for agents
- **Guards scope** — the feedback loop only modifies `feedback/patterns.md` and `feedback/run-log.jsonl`, never the core behavior

## How It Works

```
Every Run:
  @BOOT → Load learned patterns silently
  [... normal skill/agent work ...]
  @REVIEW → Self-assess: what worked, what didn't, user corrections
  @EVOLVE → Propose improvements → User approves/rejects → Patterns saved
```

After a few runs, your skill/agent accumulates domain-specific wisdom:

```markdown
## Anti-Patterns (avoid these)
- Do NOT use pypdf for text extraction on scanned PDFs — use pdfplumber with OCR fallback

## Preferred Approaches
- When merging PDFs with different page sizes, normalize to first document's page size

## Edge Cases & Gotchas
- Password-protected PDFs: try empty string password before asking user
```

## Prerequisites

1. [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed
2. An existing skill or agent to retrofit

## Install

### Option 1: From the Narai Marketplace (recommended)

```
/plugin marketplace add narailabs/narai-claude-plugins
/plugin install feedback-loop-builder@narai
```

### Option 2: Install plugin directly from GitHub

```
/plugin install narailabs/claude-feedback-loop-builder
```

### Option 3: Manual install

```bash
mkdir -p .claude/skills/feedback-loop-builder
curl -o .claude/skills/feedback-loop-builder/SKILL.md \
  https://raw.githubusercontent.com/narailabs/claude-feedback-loop-builder/main/skills/feedback-loop-builder/SKILL.md
```

## Usage

```
# Retrofit a skill
/feedback-loop-builder path/to/my-skill

# Retrofit an agent
/feedback-loop-builder path/to/my-agent-project
```

The skill will:
1. Analyze the target and detect whether it's a skill or agent
2. Read the target's config to understand its domain
3. Create `feedback/` infrastructure (patterns.md + run-log.jsonl)
4. Show you the tailored lifecycle sections before injecting
5. Ask for your approval before writing anything
6. Validate the result

## Supports

| Target Type | Config File | Detection |
|-------------|-------------|-----------|
| Skill | SKILL.md | Automatic |
| Agent | CLAUDE.md | Automatic |
| Agent | AGENTS.md | Automatic |
| Agent | agent.md | Automatic |

## License

MIT
