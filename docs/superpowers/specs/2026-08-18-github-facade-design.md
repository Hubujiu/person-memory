# Person Memory GitHub Facade Design

Date: 2026-08-18
Status: Approved direction

## Goal

Present Person Memory as a unified, local-first Agent Skill for remembering people with evidence, privacy, and restraint. Hermes remains the currently supported independent-agent integration, not the boundary of the project.

This work changes the GitHub-facing presentation only. Runtime behavior, storage semantics, and command-line interfaces remain unchanged.

## Positioning

Project name: **Person Memory**

Primary tagline:

> A local-first, evidence-backed memory skill for AI agents.

Expanded repository description:

> A local-first, evidence-backed memory skill that helps AI agents remember people with context, privacy, and restraint.

The project should feel human and warm without being framed as a dating tool. Its technical presentation should emphasize auditability, local ownership, conservative extraction, targeted recall, and zero third-party Python dependencies.

## README Information Architecture

`README.md` is the canonical English entry point. `README.zh-CN.md` is a first-class Simplified Chinese edition with the same structure, facts, commands, and safety boundaries. Each file links to the other at the top.

Both editions use this sequence:

1. Hero: name, concise value proposition, language switch, and a small set of meaningful badges.
2. Why Person Memory: the problem and the project's differentiators.
3. How it works: a compact Mermaid data-flow diagram.
4. Core capabilities: evidence-backed memories, conservative extraction, targeted recall, local privacy, and standard-library-only Python.
5. Agent compatibility: the general Agent Skill boundary followed by current Hermes independent-agent support.
6. Five-minute quick start: install, register a person, remember a message, and recall it.
7. Memory principles: stable preference versus temporary state, facts versus inference, and change over time.
8. Privacy and sensitive-data boundaries.
9. Repository structure, testing, FAQ, and license.

Detailed trigger behavior remains in `TRIGGERS.md`; the README links to it instead of duplicating the manual.

## Visual Direction

Use a restrained visual identity combining warm human cues with dependable technical structure:

- soft indigo and violet as primary colors;
- a warm accent for memory nodes;
- an abstract relationship between a person, evidence-backed memory nodes, and local storage;
- good contrast on GitHub light and dark themes;
- readable behavior at narrow README widths.

Create a repository banner for the README and a 1280 by 640 social-preview variant. Keep badges limited to useful signals such as license, Python, zero dependencies, local-first operation, and test status.

## GitHub Metadata

Use these repository Topics:

- `agent-skill`
- `ai-agent`
- `personal-memory`
- `long-term-memory`
- `local-first`
- `privacy-first`
- `evidence-based`
- `sqlite`
- `hermes-agent`
- `python`

Keep the repository slug `person-memory` and use the readable project name `Person Memory` in prose and artwork.

## Language Governance

The English and Chinese READMEs are parallel editions, not literal translations. Explanatory prose should read naturally in each language while preserving identical technical meaning.

Commands, file paths, feature claims, privacy warnings, and compatibility claims must remain synchronized. Use consistent terms for `Agent Skill`, `Person Memory`, and `Hermes independent agent`. Do not add an automated translation framework or a documentation site.

## Deliverables

- rewritten English `README.md`;
- new `README.zh-CN.md`;
- README banner and 1280 by 640 social-preview asset;
- updated GitHub repository description;
- updated GitHub Topics;
- verified links, commands, Mermaid rendering, visual readability, and existing Python tests.

## Non-Goals

- Runtime feature changes.
- New storage or agent-integration abstractions.
- A documentation website.
- Automated translation.
- External social-media or community promotion copy.
- Roadmaps, issue templates, pull-request templates, or release-process expansion.

## Acceptance Criteria

- The first screen explains what Person Memory is, who it serves, and why it is different.
- The default README is English and links clearly to the complete Chinese edition.
- Both README editions have matching technical content and a natural voice.
- The general Agent Skill identity is primary; Hermes support is clear and accurately scoped.
- GitHub description and Topics match the approved positioning.
- Visual assets remain legible on light, dark, desktop, and narrow layouts.
- Markdown links and Mermaid syntax validate.
- The existing Python test suite passes without modification to runtime behavior.
