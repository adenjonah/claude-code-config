# Obsidian Knowledge Base

## Purpose

Personal knowledge management vault. Contains project notes, technical learning, reference material, and daily logs.

## Structure

- `projects/` - Per-project notes, architecture decisions, meeting notes (mirrors ~/dev/ project names)
- `learning/` - Technical notes organized by topic
- `reference/` - Cheat sheets, patterns, quick-reference docs
- `daily/` - Daily notes (YYYY-MM-DD.md format)
- `templates/` - Obsidian templates for new notes

## Conventions

- File names: lowercase-kebab-case.md
- Links: Use Obsidian [[wikilinks]] for internal links
- Tags: #project/<name>, #topic/<name>, #type/decision, #type/reference

## Error Logging

- **Error log**: `reference/claude-errors.md`
- **Policy**: Log EVERY error immediately to that file (quick one-liner is fine). Don't filter. Patterns emerge over time.
- Review periodically to add prevention rules to CLAUDE.md or hooks.
- Each machine's `MEMORY.md` should also reference this file path.

## When Claude Should Reference This Vault

- Before starting work on a project, check `projects/<name>/` for context and past decisions
- When asked about past decisions or rationale, search here first
- When capturing new decisions or learnings, create notes here
