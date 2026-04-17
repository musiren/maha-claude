# maha-claude

Claude 기반 다계층 자동화 시스템

## 웹 클라이언트 UI

![Web Client UI](docs/images/web-ui.png)

> `python3 client/web_main.py` → `http://localhost:3000`

## 아키텍처

시스템은 3개의 독립 계층으로 구성됩니다:

| 계층 | 설명 | 참조 문서 |
|---|---|---|
| **Client** | Windows 터미널 클라이언트 (UI 전용) | `client/CLAUDE.md` |
| **Gateway** | FastAPI + 세션 매니저 | `gateway/CLAUDE.md` |
| **Orchestrator** | 에이전트 실행 엔진 | `orchestrator/CLAUDE.md` |

## 워크플로우

### 시스템 전체 구조

```mermaid
graph TD
    User["👤 사용자<br/>(터미널)"]

    subgraph CLIENT["클라이언트 계층"]
        C["client/main.py<br/>─────────────<br/>• 로그인 / 로그아웃<br/>• 세션 관리<br/>• /COMMAND 입력<br/>• SSE 스트림 출력<br/>• 승인 처리"]
    end

    subgraph GATEWAY["게이트웨이 계층  :8000"]
        G["gateway/main.py<br/>─────────────────<br/>• JWT 인증<br/>• 세션 저장소 (Redis)<br/>• 요청 라우팅<br/>• SSE 프록시"]
    end

    subgraph ORCHESTRATOR["오케스트레이터 계층  :9000"]
        E["engine.py<br/>────────────<br/>• 명령어 파싱<br/>• Tool 선택<br/>• 정책 검사<br/>• 승인 흐름"]
        subgraph TOOLS["Tools"]
            T1["/echo"]
            T2["/help"]
            T3["/status"]
            T4["/run-tests<br/>⚠️ 승인 필요"]
            T5["..."]
        end
        E --> T1 & T2 & T3 & T4 & T5
    end

    User -- "입력" --> C
    C -- "POST /auth/login<br/>POST /session/start<br/>POST /command<br/>POST /command/approve" --> G
    G -- "POST /run<br/>POST /approve<br/>GET /commands" --> E
    E -. "SSE 스트림" .-> G
    G -. "SSE 스트림" .-> C
    C -. "출력" .-> User
```

### 명령어 실행 흐름

```mermaid
sequenceDiagram
    actor 사용자
    participant C as 클라이언트
    participant G as 게이트웨이
    participant O as 오케스트레이터

    사용자->>C: /echo 안녕하세요
    C->>G: POST /command<br/>{session_id, command}
    G->>O: POST /run<br/>{session_id, command, username}

    O-->>G: data: {"type":"text","content":"안녕하세요"}
    O-->>G: data: [DONE]
    G-->>C: SSE 스트림
    C-->>사용자: 안녕하세요
```

### 승인 흐름

```mermaid
sequenceDiagram
    actor 사용자
    participant C as 클라이언트
    participant G as 게이트웨이
    participant O as 오케스트레이터

    사용자->>C: /run-tests
    C->>G: POST /command
    G->>O: POST /run

    O-->>G: data: {"type":"approval","approval_id":"xxx"}
    G-->>C: SSE 스트림
    C-->>사용자: [승인 필요] 계속하시겠습니까? [y/N]

    사용자->>C: y
    C->>G: POST /command/approve<br/>{approval_id, approved: true}
    G->>O: POST /approve<br/>{approval_id, approved: true}

    O-->>G: data: {"type":"text","content":"테스트 결과..."}
    O-->>G: data: [DONE]
    G-->>C: SSE 스트림
    C-->>사용자: 테스트 결과 출력
```

### 새 슬래시 커맨드 추가 방법

```mermaid
flowchart LR
    A["1️⃣  파일 생성<br/>orchestrator/tools/my_tool.py<br/>─────────────────────<br/>class MyTool(BaseTool):<br/>  slash_command = '/my-tool'<br/>  async def execute(...)"]
    B["2️⃣  등록<br/>orchestrator/tools/__init__.py<br/>─────────────────────<br/>ALL_TOOLS = [..., MyTool]"]
    C["✅  완료<br/>─────────────<br/>• /my-tool 사용 가능<br/>• GET /commands 목록에 표시<br/>• 클라이언트 '/'에 표시"]

    A --> B --> C
```

## 빠른 시작

```bash
# 1. 저장소 클론
git clone <repo-url>
cd maha-claude

# 2. 최초 설정 (git hooks + 의존성 설치)
bash setup.sh

# 3. 게이트웨이 실행 (포트 8000)
PYTHONPATH=gateway python3 gateway/main.py

# 4. 오케스트레이터 실행 (포트 9000)
PYTHONPATH=orchestrator python3 orchestrator/main.py

# 5. 터미널 클라이언트 실행
GATEWAY_URL=http://localhost:8000 python3 client/main.py
```

## 클라이언트

터미널 클라이언트(`client/main.py`)는 게이트웨이에 연결하여 다음 기능을 제공합니다:

- 로그인 / 인증 (토큰은 메모리에만 저장)
- 세션 시작 / 종료
- `/COMMAND` 슬래시 커맨드 입력 및 SSE 스트리밍 출력
- 승인 요청 처리
- 세션 시작 시 `GET /commands`로 명령어 목록 자동 조회

**환경 변수:**

| 변수 | 기본값 | 설명 |
|---|---|---|
| `GATEWAY_URL` | `http://localhost:8000` | 게이트웨이 주소 |
| `SESSION_TIMEOUT` | `3600` | 세션 타임아웃 (초) |

## 슬래시 커맨드

| 커맨드 | 설명 | 승인 |
|---|---|---|
| `/echo <메시지>` | 메시지 그대로 반환 | - |
| `/help` | 사용 가능한 커맨드 목록 표시 | - |
| `/status` | 현재 세션 정보 표시 | - |
| `/run-tests [경로]` | pytest 실행 | ✅ 필요 |

`/` 단독 입력 시 로컬 캐시된 커맨드 목록을 표시합니다.

## 개발

### 의존성 설치

```bash
pip install -r client/requirements-dev.txt
pip install -r gateway/requirements.txt
pip install -r orchestrator/requirements.txt
```

### 테스트 실행

```bash
# 전체 계층
pytest client/tests/ gateway/tests/ orchestrator/tests/ -v

# 계층별 (PYTHONPATH 지정)
PYTHONPATH=client      pytest client/tests/
PYTHONPATH=gateway     pytest gateway/tests/
PYTHONPATH=orchestrator pytest orchestrator/tests/
```

### 커밋 메시지 규칙 (Linux Kernel 형식)

```
subsystem: 간략한 설명 (최대 72자, 마침표 없음)

변경 이유와 내용을 설명하는 본문 (선택)
각 줄 최대 72자
```

허용되는 subsystem 접두어: `client`, `gateway`, `orchestrator`, `ci`, `docs`, `test`, `build`

### Git Hooks

`setup.sh` 실행 시 자동 활성화:

- **pre-commit**: 계층별 pytest 실행 — 테스트 실패 시 커밋 차단
- **commit-msg**: Linux kernel 커밋 메시지 형식 검증

## 배포

systemd 유닛 파일은 `deploy/` 디렉토리에 있습니다:

| 파일 | 설명 |
|---|---|
| `deploy/maha-gateway.service` | 게이트웨이 서비스 (포트 8000) |
| `deploy/maha-orchestrator.service` | 오케스트레이터 서비스 (포트 9000) |

```bash
# 서비스 파일 설치
sudo cp deploy/maha-gateway.service /etc/systemd/system/
sudo cp deploy/maha-orchestrator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable maha-gateway maha-orchestrator
sudo systemctl start maha-gateway maha-orchestrator
```

## 변경 이력

[NEWS](NEWS) 파일을 참조하세요.
