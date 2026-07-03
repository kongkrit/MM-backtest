# Claude Code Template

A starter repository preconfigured for working with [Claude Code](https://claude.com/claude-code). Use it as a base for new projects so the Claude Code setup, ignore rules, and line-ending normalization are in place from the first commit.

## What's included

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Claude Code settings — `model: opus`, `effortLevel: xhigh`. |
| `.claude/settings.json` (hook) | `SessionStart` hook that prints `PROGRESS.md` into context at startup. |
| `.claude/commands/wrapup.md` | `/wrapup` — write a session handoff to `PROGRESS.md`, then commit. |
| `.gitignore` | Ignores OS cruft, Python/Node build artifacts, and editor files. |
| `.gitattributes` | Normalizes line endings to LF and marks binary file types. |
| `LICENSE` | Project license. |

## Usage

1. Use this repo as a GitHub template (**Use this template**) or clone it.
2. Remove these template files you don't need and start building your project.
3. Adjust `.claude/settings.json` to taste — see the Claude Code [settings docs](https://docs.claude.com/en/docs/claude-code/settings).

Personal settings that should not be committed belong in `.claude/settings.local.json`, which is already gitignored.

## Development setup (Debian)

Targets **Debian 13 (trixie)**. `docker` is assumed already installed.

Install the base toolchain:

```bash
sudo apt install -y git gh python3 python3-venv python3-pip python3-dev build-essential curl jq
```

| Package | Purpose |
|---|---|
| `git` | Version control. |
| `gh` | GitHub CLI — clone, push, PRs, releases. |
| `python3` | Interpreter. |
| `python3-venv` | Virtual environments — required on Debian 13 (see below). |
| `python3-pip` | Installs Python dependencies (most ship as prebuilt wheels). |
| `python3-dev` | C headers for dependencies built from source. |
| `build-essential` | C/C++ compiler + make, for the same source builds. |
| `curl` | Fetching files and data over HTTP. |
| `jq` | Command-line JSON processor — query and transform JSON output. |

### Installing more tools

This environment has passwordless `sudo`, and Claude Code is allowed to install extra system tooling when a task needs it:

```bash
sudo apt update                 # refresh the package index if a package isn't found
sudo apt install -y <package>   # e.g. ripgrep, sqlite3, imagemagick
```

Use `apt` for system-level tools and CLIs. Keep Python dependencies in the project virtual environment (below) rather than installing them as system packages. If a newly installed tool becomes a lasting dependency, add it to the base toolchain list above so it's reproducible.

### Python: Debian 13 is externally managed (PEP 668)

A system-wide `pip install` is blocked. Use a virtual environment per project:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt      # or: pip install -e ".[dev]"
```

Optional: `sudo apt install -y pipx`, then `pipx install .` to install a packaged CLI tool without managing a venv by hand.

### Docker multi-arch builds (one-time, optional)

Building multi-arch images (`linux/amd64` + `linux/arm64`) needs QEMU emulation plus a `docker-container` buildx builder:

```bash
docker run --privileged --rm tonistiigi/binfmt --install all
docker buildx create --name multiarch --driver docker-container --bootstrap --use
```

The first line registers QEMU so the host can emulate the non-native architecture (`--install all` is host-agnostic); the second creates and activates the builder reused by later `docker buildx build`. On Apple Silicon + OrbStack, cross-arch emulation is built in, so only the `buildx create` line is needed.

### Not required

- **node / npm** — not used; serve static content with `python3 -m http.server`.
- **.NET SDK** — no .NET projects.

## License

See [LICENSE](LICENSE).
