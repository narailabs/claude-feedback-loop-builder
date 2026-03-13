#!/usr/bin/env python3
"""
Analyze a target skill or agent to determine its type, structure,
and readiness for feedback loop integration.

Usage:
    python analyze_target.py <path>

Output: JSON report with target metadata.
"""

import json
import os
import re
import sys
from pathlib import Path


def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            fm[key.strip()] = val.strip()
    return fm


def detect_scope_markers(content):
    """Extract section headers as scope boundaries."""
    headers = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
    return headers


def check_existing_feedback_loop(content):
    """Check if target already has feedback loop sections."""
    markers = ['@BOOT', '@REVIEW', '@EVOLVE', 'feedback/patterns.md', 'feedback/run-log.jsonl']
    found = [m for m in markers if m in content]
    return found


def analyze_skill(path):
    """Analyze a skill target."""
    skill_md = path / 'SKILL.md'
    content = skill_md.read_text()
    frontmatter = extract_yaml_frontmatter(content)
    sections = detect_scope_markers(content)
    existing = check_existing_feedback_loop(content)

    # Detect bundled resources
    has_scripts = (path / 'scripts').is_dir()
    has_references = (path / 'references').is_dir()
    has_assets = (path / 'assets').is_dir()
    has_feedback = (path / 'feedback').is_dir()

    return {
        'type': 'skill',
        'path': str(path),
        'name': frontmatter.get('name', 'unknown'),
        'description': frontmatter.get('description', ''),
        'sections': sections,
        'has_scripts': has_scripts,
        'has_references': has_references,
        'has_assets': has_assets,
        'has_feedback_dir': has_feedback,
        'existing_feedback_markers': existing,
        'already_has_feedback_loop': len(existing) >= 3,
        'skill_md_lines': len(content.split('\n')),
    }


def analyze_agent(path, config_file):
    """Analyze an agent target."""
    config_path = path / config_file
    content = config_path.read_text()
    sections = detect_scope_markers(content)
    existing = check_existing_feedback_loop(content)
    has_feedback = (path / 'feedback').is_dir()

    # Try to extract agent name/purpose from first heading or content
    name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    agent_name = name_match.group(1) if name_match else config_file

    return {
        'type': 'agent',
        'path': str(path),
        'config_file': config_file,
        'name': agent_name,
        'sections': sections,
        'has_feedback_dir': has_feedback,
        'existing_feedback_markers': existing,
        'already_has_feedback_loop': len(existing) >= 3,
        'config_lines': len(content.split('\n')),
    }


def analyze(target_path):
    """Detect target type and return analysis report."""
    path = Path(target_path).resolve()

    if not path.exists():
        return {'error': f'Path does not exist: {path}'}

    # Detect type
    skill_md = path / 'SKILL.md'
    claude_md = path / 'CLAUDE.md'
    agents_md = path / 'AGENTS.md'
    agent_md = path / 'agent.md'

    if skill_md.is_file():
        return analyze_skill(path)
    elif claude_md.is_file():
        return analyze_agent(path, 'CLAUDE.md')
    elif agents_md.is_file():
        return analyze_agent(path, 'AGENTS.md')
    elif agent_md.is_file():
        return analyze_agent(path, 'agent.md')
    else:
        # Check if the path itself is a file
        if path.is_file() and path.suffix == '.md':
            return analyze_agent(path.parent, path.name)
        return {
            'error': f'No SKILL.md, CLAUDE.md, AGENTS.md, or agent.md found at: {path}',
            'hint': 'Provide the path to a skill directory or agent config directory.',
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_target.py <path-to-skill-or-agent>")
        print("\nDetects whether the target is a skill or agent and extracts metadata.")
        sys.exit(1)

    result = analyze(sys.argv[1])
    print(json.dumps(result, indent=2))

    if 'error' in result:
        sys.exit(1)
    if result.get('already_has_feedback_loop'):
        print("\n⚠️  Target already has feedback loop markers. Review before re-injecting.", file=sys.stderr)


if __name__ == "__main__":
    main()
