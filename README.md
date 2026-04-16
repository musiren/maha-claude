# maha-claude

A multi-layer automation system powered by Claude.

## Architecture

The system consists of three independent layers:

| Layer | Description | Reference |
|---|---|---|
| **Client** | Windows Terminal Client (Thin UI) | `skills/client/CLAUDE.md` |
| **Gateway** | FastAPI + Session Manager | `skills/gateway/CLAUDE.md` |
| **Orchestrator** | Agent Orchestrator | `skills/orchestrator/CLAUDE.md` |

## Workflow

### System Overview

```mermaid
graph TD
    User["👤 User<br/>(Terminal)"]

    subgraph CLIENT["Client Layer"]
        C["client/main.py<br/>─────────────<br/>• Login / logout<br/>• Session management<br/>• /COMMAND input<br/>• SSE stream output<br/>• Approval prompt"]
    end

    subgraph GATEWAY["Gateway Layer  :8000"]
        G["gateway/main.py<br/>─────────────────<br/>• JWT authentication<br/>• Session store (Redis)<br/>• Request routing<br/>• SSE proxy"]
    end

    subgraph ORCHESTRATOR["Orchestrator Layer  :9000"]
        E["engine.py<br/>────────────<br/>• Intent parsing<br/>• Tool dispatch<br/>• Policy check<br/>• Approval flow"]
        subgraph TOOLS["Tools"]
            T1["/echo"]
            T2["/help"]
            T3["/status"]
            T4["/run-tests<br/>⚠️ approval"]
            T5["..."]
        end
        E --> T1 & T2 & T3 & T4 & T5
    end

    User -- "input" --> C
    C -- "POST /auth/login<br/>POST /session/start<br/>POST /command<br/>POST /command/approve" --> G
    G -- "POST /run<br/>POST /approve<br/>GET /commands" --> E
    E -. "SSE stream" .-> G
    G -. "SSE stream" .-> C
    C -. "output" .-> User
```

### Command Flow

```mermaid
sequenceDiagram
    actor User
    participant C as Client
    participant G as Gateway
    participant O as Orchestrator

    User->>C: /echo hello
    C->>G: POST /command<br/>{session_id, command}
    G->>O: POST /run<br/>{session_id, command, username}

    O-->>G: data: {"type":"text","content":"hello"}
    O-->>G: data: [DONE]
    G-->>C: SSE stream
    C-->>User: hello
```

### Approval Flow

```mermaid
sequenceDiagram
    actor User
    participant C as Client
    participant G as Gateway
    participant O as Orchestrator

    User->>C: /run-tests
    C->>G: POST /command
    G->>O: POST /run

    O-->>G: data: {"type":"approval","approval_id":"xxx"}
    G-->>C: SSE stream
    C-->>User: [승인 필요] 계속하시겠습니까? [y/N]

    User->>C: y
    C->>G: POST /command/approve<br/>{approval_id, approved: true}
    G->>O: POST /approve<br/>{approval_id, approved: true}

    O-->>G: data: {"type":"text","content":"테스트 결과..."}
    O-->>G: data: [DONE]
    G-->>C: SSE stream
    C-->>User: 테스트 결과 출력
```

### Adding a New Slash Command

```mermaid
flowchart LR
    A["1️⃣  Create<br/>orchestrator/tools/my_tool.py<br/>─────────────────────<br/>class MyTool(BaseTool):<br/>  slash_command = '/my-tool'<br/>  async def execute(...)"]
    B["2️⃣  Register<br/>orchestrator/tools/__init__.py<br/>─────────────────────<br/>ALL_TOOLS = [..., MyTool]"]
    C["✅  Done<br/>─────────────<br/>• /my-tool available<br/>• GET /commands lists it<br/>• Client '/' shows it"]

    A --> B --> C
```

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd maha-claude

# 2. One-time setup (git hooks + dependencies)
bash setup.sh

# 3. Start Gateway (port 8000)
PYTHONPATH=gateway python3 gateway/main.py

# 4. Start Orchestrator (port 9000)
PYTHONPATH=orchestrator python3 orchestrator/main.py

# 5. Run the terminal client
GATEWAY_URL=http://localhost:8000 python3 client/main.py
```

## Client

The terminal client (`client/main.py`) connects to the Gateway and provides:

- Login / authentication (token stored in memory only)
- Session start / end
- `/COMMAND` slash command input with streaming response output
- Approval request handling
- `GET /commands` auto-discovery on session start

**Environment Variables:**

| Variable | Default | Description |
|---|---|---|
| `GATEWAY_URL` | `http://localhost:8000` | Gateway server address |
| `SESSION_TIMEOUT` | `3600` | Session timeout in seconds |

## Slash Commands

| Command | Description | Approval |
|---|---|---|
| `/echo <msg>` | Echo message back | - |
| `/help` | List available commands | - |
| `/status` | Show session info | - |
| `/run-tests [path]` | Run pytest | ✅ Required |

Type `/` alone to show the command list locally.

## Development

### Requirements

```bash
pip install -r client/requirements-dev.txt
pip install -r gateway/requirements.txt
pip install -r orchestrator/requirements.txt
```

### Running Tests

```bash
# All layers
pytest client/tests/ gateway/tests/ orchestrator/tests/ -v

# Per layer (with correct PYTHONPATH)
PYTHONPATH=client     pytest client/tests/
PYTHONPATH=gateway    pytest gateway/tests/
PYTHONPATH=orchestrator pytest orchestrator/tests/
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

- **pre-commit**: Runs pytest per layer — commit blocked if any test fails
- **commit-msg**: Validates Linux kernel commit message format

## Changelog

See [NEWS](NEWS) for release notes.
