#!/usr/bin/env python3
"""
Analyze a target skill or agent to determine its type, structure,
and readiness for feedback loop integration.

Usage:
    python analyze_target.py <name-or-path>

Accepts:
    - A skill/plugin name: "browser-qa", "pdf", "frontend-design"
    - A path: "./my-skill", "/abs/path/to/agent-project"
    - A fuzzy description: "my PDF skill", "the browser testing agent"

Resolves names by searching:
    1. ~/.claude/plugins/installed_plugins.json (installed skills)
    2. Common source directories (~/src/, ~/projects/)
    3. Current working directory

Output: JSON report with target metadata.
"""

import json
import os
import re
import sys
from pathlib import Path

PLUGINS_REGISTRY = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'
PLUGINS_CACHE = Path.home() / '.claude' / 'plugins' / 'cache'
SOURCE_DIRS = [Path.home() / 'src', Path.home() / 'projects', Path.home() / 'dev']


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


def find_skill_dir(base_path):
    """Find the actual skill directory within an install path.

    Skills may be at:
      - base/.claude/skills/<name>/SKILL.md
      - base/skills/<name>/SKILL.md
      - base/SKILL.md
    """
    # Direct SKILL.md
    if (base_path / 'SKILL.md').is_file():
        return base_path

    # .claude/skills/<name>/
    claude_skills = base_path / '.claude' / 'skills'
    if claude_skills.is_dir():
        for child in claude_skills.iterdir():
            if child.is_dir() and (child / 'SKILL.md').is_file():
                return child

    # skills/<name>/
    skills_dir = base_path / 'skills'
    if skills_dir.is_dir():
        for child in skills_dir.iterdir():
            if child.is_dir() and (child / 'SKILL.md').is_file():
                return child

    return None


def find_agent_dir(base_path):
    """Find agent config in a directory."""
    for config in ['CLAUDE.md', 'AGENTS.md', 'agent.md']:
        if (base_path / config).is_file():
            return base_path, config
    return None, None


def scan_sub_skills(install_path, query_lower):
    """Scan a multi-skill package for sub-skills matching the query.

    Multi-skill packages (like document-skills) contain multiple skills under
    skills/<name>/ or .claude/skills/<name>/. This finds sub-skills by name.
    """
    matches = []
    for skills_parent in [install_path / 'skills', install_path / '.claude' / 'skills']:
        if not skills_parent.is_dir():
            continue
        for child in skills_parent.iterdir():
            if not child.is_dir():
                continue
            child_name = child.name.lower()
            if (child_name == query_lower
                    or query_lower in child_name
                    or child_name in query_lower):
                if (child / 'SKILL.md').is_file():
                    matches.append(child)
    return matches


def resolve_from_registry(query):
    """Search installed_plugins.json for a matching skill by name.

    Searches both top-level plugin names and sub-skills within packages.
    """
    if not PLUGINS_REGISTRY.is_file():
        return []

    try:
        registry = json.loads(PLUGINS_REGISTRY.read_text())
    except (json.JSONDecodeError, OSError):
        return []

    plugins = registry.get('plugins', registry)
    if not isinstance(plugins, dict):
        return []

    matches = []
    query_lower = query.lower().strip()

    for key, entries in plugins.items():
        # key format: "skill-name@marketplace"
        plugin_name = key.split('@')[0].lower()

        # Exact match on top-level name
        if plugin_name == query_lower:
            for entry in entries:
                matches.insert(0, {'key': key, 'name': plugin_name, 'match': 'exact', **entry})
            continue

        # Partial/fuzzy match on top-level name
        if query_lower in plugin_name or plugin_name in query_lower:
            for entry in entries:
                matches.append({'key': key, 'name': plugin_name, 'match': 'partial', **entry})
            continue

        # Scan sub-skills within multi-skill packages
        for entry in entries:
            install_path = Path(entry.get('installPath', ''))
            if install_path.is_dir():
                sub_matches = scan_sub_skills(install_path, query_lower)
                for sub_path in sub_matches:
                    matches.append({
                        'key': key,
                        'name': sub_path.name.lower(),
                        'match': 'sub_skill',
                        'sub_skill_path': str(sub_path),
                        **entry,
                    })

    return matches


def resolve_from_source_dirs(query):
    """Search common source directories for matching projects."""
    matches = []
    query_lower = query.lower().strip()

    for src_dir in SOURCE_DIRS:
        if not src_dir.is_dir():
            continue
        for child in src_dir.iterdir():
            if not child.is_dir():
                continue
            name = child.name.lower()
            # Match: exact name, name contains query, or "claude-<query>"
            if (name == query_lower
                    or query_lower in name
                    or name == f'claude-{query_lower}'
                    or name == f'{query_lower}-skill'
                    or name == f'{query_lower}-agent'):
                matches.append(child)

    return matches


def resolve_target(query):
    """Resolve a name, description, or path to a target directory.

    Returns: (path, resolution_info) or (None, error_info)
    """
    # 1. If it looks like a path (contains / or . or ~), try as path first
    if '/' in query or query.startswith('.') or query.startswith('~'):
        path = Path(os.path.expanduser(query)).resolve()
        if path.exists():
            return path, {'resolved_via': 'path', 'original': query}

    # 2. Check if it's a direct path from CWD
    cwd_path = Path.cwd() / query
    if cwd_path.exists():
        return cwd_path, {'resolved_via': 'cwd_path', 'original': query}

    # 3. Search installed plugins registry
    registry_matches = resolve_from_registry(query)
    if registry_matches:
        best = registry_matches[0]

        # Sub-skill match: direct path to sub-skill already resolved
        if best['match'] == 'sub_skill' and 'sub_skill_path' in best:
            sub_path = Path(best['sub_skill_path'])
            if sub_path.exists():
                return sub_path, {
                    'resolved_via': 'registry',
                    'plugin_key': best['key'],
                    'install_path': best.get('installPath', ''),
                    'match_type': 'sub_skill',
                    'sub_skill_name': best['name'],
                    'version': best.get('version', 'unknown'),
                    'original': query,
                }

        install_path = Path(best['installPath'])
        if install_path.exists():
            # Find the actual skill dir within the install path
            skill_dir = find_skill_dir(install_path)
            if skill_dir:
                return skill_dir, {
                    'resolved_via': 'registry',
                    'plugin_key': best['key'],
                    'install_path': str(install_path),
                    'match_type': best['match'],
                    'version': best.get('version', 'unknown'),
                    'original': query,
                }
            # Maybe it's an agent
            agent_dir, config = find_agent_dir(install_path)
            if agent_dir:
                return agent_dir, {
                    'resolved_via': 'registry',
                    'plugin_key': best['key'],
                    'install_path': str(install_path),
                    'match_type': best['match'],
                    'config_file': config,
                    'original': query,
                }

    # 4. Search source directories
    source_matches = resolve_from_source_dirs(query)
    for match_path in source_matches:
        # Check for skill
        skill_dir = find_skill_dir(match_path)
        if skill_dir:
            return skill_dir, {
                'resolved_via': 'source_dir',
                'project_path': str(match_path),
                'original': query,
            }
        # Check for agent
        agent_dir, config = find_agent_dir(match_path)
        if agent_dir:
            return agent_dir, {
                'resolved_via': 'source_dir',
                'project_path': str(match_path),
                'config_file': config,
                'original': query,
            }

    # 5. Nothing found
    search_locations = ['~/.claude/plugins/installed_plugins.json']
    search_locations += [str(d) for d in SOURCE_DIRS if d.is_dir()]
    return None, {
        'error': f'Could not resolve "{query}" to a skill or agent',
        'searched': search_locations,
        'hint': 'Try: a skill name ("browser-qa"), a path ("./my-skill"), or install the skill first.',
        'original': query,
    }


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
            'hint': 'Provide a skill name or path to a skill/agent directory.',
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_target.py <name-or-path>")
        print("\nAccepts a skill/agent name, path, or description.")
        print("Examples:")
        print("  analyze_target.py browser-qa")
        print("  analyze_target.py pdf")
        print("  analyze_target.py ./my-agent-project")
        print("  analyze_target.py /abs/path/to/skill")
        sys.exit(1)

    query = ' '.join(sys.argv[1:])

    # Try to resolve the target (name → path)
    resolved_path, resolution_info = resolve_target(query)

    if resolved_path is None:
        print(json.dumps(resolution_info, indent=2))
        sys.exit(1)

    # Analyze the resolved path
    result = analyze(str(resolved_path))
    result['resolution'] = resolution_info
    print(json.dumps(result, indent=2))

    if 'error' in result:
        sys.exit(1)
    if result.get('already_has_feedback_loop'):
        print("\n⚠️  Target already has feedback loop markers. Review before re-injecting.", file=sys.stderr)


if __name__ == "__main__":
    main()
