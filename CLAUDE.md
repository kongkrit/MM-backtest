# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What this is

This is a **Claude Code template repository** — a starting point for new projects, not an application itself. It currently contains only configuration and licensing files. When this template is used for a real project, expect application code to be added alongside the files below.

## Repository layout

- `.claude/settings.json` — Claude Code settings committed for the project (`model: opus`, `effortLevel: xhigh`). Personal overrides go in `.claude/settings.local.json` (gitignored), never in the committed file.
- `.claude/commands/wrapup.md` — the `/wrapup` slash command: writes a session handoff to `PROGRESS.md`, then stages and commits.
- `PROGRESS.md` — session handoff created/updated by `/wrapup`; printed into context at session start by the `SessionStart` hook in `.claude/settings.json`. Absent until the first `/wrapup`.
- `.gitignore` — ignores OS cruft, Python/Node build artifacts, and editor files.
- `.gitattributes` — enforces LF line endings and marks binary file types. Keep new text/binary file types consistent with the existing entries.
- `LICENSE` — the project license.
- `README.md` — human-facing overview of the template.

## Conventions

- Line endings are LF across the repo (enforced by `.gitattributes`). Do not introduce CRLF.
- When adding a new language or toolchain, extend `.gitignore` and `.gitattributes` rather than creating parallel ignore files.
- Respect the project [LICENSE](LICENSE) when adding dependencies.

## Development environment

- Target OS is **Debian 13 (trixie)**; `docker` is already installed. Base tooling is installed via `apt` — `git`, `gh`, `python3`, `python3-venv`, `python3-pip`, `python3-dev`, `build-essential`, `curl`, `jq` (see the [README](README.md#development-setup-debian) for the full command).
- **You may install additional system tools yourself.** If a task needs a CLI or library that isn't present, run `sudo apt install -y <package>` (update the index first with `sudo apt update` if a package isn't found). Prefer `apt` for system-level tooling; keep Python dependencies in the project venv (below), not in system packages. After installing something the project will keep relying on, record it in the [README](README.md#development-setup-debian) so the dependency is discoverable.
- **Debian 13 is externally managed (PEP 668): never run a system-wide `pip install`.** Create and use a per-project virtual environment instead:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt   # or: pip install -e ".[dev]"
  ```
- `node`/`npm` and the .NET SDK are not used; serve static content with `python3 -m http.server`. Multi-arch Docker builds need a one-time QEMU + buildx setup (see README).

## Notes

- As the template grows into a real project, update this file with build, test, and run commands so they are discoverable.
