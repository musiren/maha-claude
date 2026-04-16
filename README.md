# maha-claude

A multi-layer automation system powered by Claude.

## Architecture

The system consists of three independent layers:

| Layer | Description | Reference |
|---|---|---|
| **Client** | Windows Terminal Client (Thin UI) | `skills/client/CLAUDE.md` |
| **Gateway** | FastAPI + Session Manager | `skills/gateway/CLAUDE.md` |
| **Orchestrator** | Agent Orchestrator | `skills/orchestrator/CLAUDE.md` |

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd maha-claude

# 2. One-time setup (git hooks + dependencies)
bash setup.sh

# 3. Run the terminal client
GATEWAY_URL=http://localhost:8000 python3 client/main.py
```

## Client

The terminal client (`client/main.py`) connects to the Gateway and provides:

- Login / authentication (token stored in memory only)
- Session start / end
- Command input with streaming response output
- Approval request handling

**Environment Variables:**

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_URL` | `http://localhost:8000` | Gateway server address |
| `SESSION_TIMEOUT` | `3600` | Session timeout in seconds |

## Development

### Requirements

```bash
pip install -r client/requirements-dev.txt
```

### Running Tests

```bash
pytest client/tests/ -v
```

### Commit Message Format (Linux Kernel Style)

```
subsystem: brief description (max 72 chars, no trailing period)

Optional body explaining what and why.
Lines wrapped at 72 characters.
```

Allowed subsystem prefixes: `client`, `gateway`, `orchestrator`, `ci`, `docs`, `test`, `build`

### Git Hooks

Activated automatically via `setup.sh`:

- **pre-commit**: Runs pytest — commit is blocked if any test fails
- **commit-msg**: Validates Linux kernel commit message format

## Changelog

See [NEWS](NEWS) for release notes.
