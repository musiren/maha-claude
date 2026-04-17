# CLAUDE.md (Platform Controller)

## 1. 목적
이 문서는 전체 시스템의 동작을 정의하는 상위 규약이며,
각 계층의 상세 동작은 개별 CLAUDE.md를 참조한다.

이 문서는 모든 하위 CLAUDE.md보다 우선하는 전역 규칙을 정의한다.

---

## 2. 구성 요소 및 참조 문서

본 시스템은 다음 3개의 독립 계층으로 구성되며,
각 계층은 별도의 CLAUDE.md를 가진다.

### 2.1 Windows Terminal Client
참조: `/client/CLAUDE.md`

### 2.2 FastAPI + Session Manager
참조: `/gateway/CLAUDE.md`

### 2.3 Agent Orchestrator
참조: `/orchestrator/CLAUDE.md`

---

## 3. 문서 간 관계 규칙

### 3.1 역할 분리 원칙
각 CLAUDE.md는 자신의 계층에 대해서만 정의한다.

- Client CLAUDE.md → UI 및 사용자 인터페이스
- Gateway CLAUDE.md → 인증, 세션, 라우팅
- Orchestrator CLAUDE.md → 실행 판단 및 흐름 제어

### 3.2 중복 정의 금지
- 동일한 규칙을 여러 CLAUDE.md에 중복 정의하지 않는다
- 공통 규칙은 이 문서에만 정의한다

### 3.3 충돌 해결 규칙
규칙 충돌 시 우선순위는 다음과 같다:

1. Platform CLAUDE.md (이 문서)
2. 각 계층 CLAUDE.md
3. 코드 구현

---

## 4. 전체 시스템 설계 원칙

### 4.1 중앙 실행 원칙
- 모든 실행은 서버에서 수행된다
- 클라이언트는 실행 로직을 가지지 않는다

### 4.2 책임 분리 원칙
- 각 계층은 자신의 책임만 수행한다
- 타 계층의 역할을 침범하지 않는다

### 4.3 Tool 기반 실행 원칙
- 모든 외부 시스템 접근은 Tool 계층을 통해 수행한다
- 직접 호출 금지

---

## 5. 계층 간 인터페이스 규칙

### 5.1 Client → Gateway
- HTTP 또는 WebSocket 기반 통신
- 인증 토큰 포함 필수

### 5.2 Gateway → Orchestrator
- 세션 컨텍스트 포함 전달
- 사용자 식별 정보 포함

### 5.3 Orchestrator → Tool
- 명확한 인터페이스 기반 호출
- 직접 외부 API 호출 금지

---

## 6. 데이터 흐름 규칙

1. 사용자 입력은 Client에서 수집
2. Gateway에서 인증 및 세션 검증
3. Orchestrator에서 의도 해석
4. Tool 호출로 실행
5. 결과 요약 후 사용자에게 반환

---

## 7. 보안 규칙 (전역)

### 7.1 접근 제어
- 모든 요청은 인증 필수
- 사용자별 세션 격리

### 7.2 실행 제한
- 임의 코드 실행 금지
- Shell 접근 금지
- 외부 인터넷 업로드 금지

---

## 8. 승인 정책 (전역)

다음 작업은 반드시 승인 필요:

- 테스트 실행
- 스크립트 변경
- 대량 작업

각 세부 규칙은 Orchestrator CLAUDE.md에서 정의한다.

---

## 9. Tool 계층 규칙

### 9.1 Tool 정의 위치
- Tool은 Orchestrator 계층에서 정의된다
- 구현은 Python 모듈로 수행

### 9.2 Tool 사용 규칙
- 모든 외부 시스템 접근은 Tool을 통해 수행
- 직접 접근 금지

---

## 10. 세션 관리 규칙

- 모든 요청은 세션 기반
- 세션은 Gateway에서 관리
- Orchestrator는 세션을 참조만 한다

---

## 11. 로그 및 관측성

- 모든 요청은 추적 가능해야 한다
- Tool 호출은 반드시 기록한다
- 사용자 행동 로그는 최소화한다

---

## 12. 확장 전략

### 12.1 초기 단계
- 단일 서버 구조
- in-process tool 사용

### 12.2 확장 단계
- Tool을 MCP 서버로 분리 가능
- Gateway 수평 확장

---

## 13. 금지사항 (전역)

다음은 모든 계층에서 금지된다:

- 계층 간 역할 침범
- 승인 없는 실행
- 내부 API 직접 노출
- 사용자 임의 코드 실행

---

## 14. 개발 규칙

- 모든 기능은 Tool 단위로 추가
- 정책은 중앙에서 관리
- 계층 간 의존성 최소화

---

## 15. 운영 원칙

- 변경은 서버 중심으로 수행
- 사용자 환경 변경 최소화
- 장애 시 영향 범위 최소화

---

## 16. 요약

이 문서는 시스템 전체의 동작을 정의하며,
각 세부 구현은 다음 문서를 따른다:

- Client → `/client/CLAUDE.md`
- Gateway → `/gateway/CLAUDE.md`
- Orchestrator → `/orchestrator/CLAUDE.md`

각 계층은 독립적으로 동작하지만,
이 문서의 규칙을 반드시 따른다.

---

## 17. 개발 환경 설정 규칙

### 17.1 최초 설정

저장소를 클론한 후 반드시 실행한다:

```bash
bash setup.sh
```

또는 수동으로:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/commit-msg
pip install -r client/requirements-dev.txt
```

### 17.2 커밋 메시지 규칙 (Linux Kernel Format)

모든 커밋 메시지는 Linux 커널 형식을 따른다:

- **제목줄**: 최대 72자, 마침표 없음, 명령형 현재 시제
- **형식**: `subsystem: 간략한 설명` (예: `client: add login timeout`)
- **본문**: 제목 다음 빈 줄, 각 줄 최대 72자
- **공백**: 줄 끝 공백 금지

허용되는 subsystem 접두어: `client`, `gateway`, `orchestrator`,
`ci`, `docs`, `test`, `build`

### 17.3 커밋 전 테스트

- 커밋 전 pytest가 자동으로 실행된다 (pre-commit hook)
- 테스트 파일이 없으면 경고만 출력하고 커밋 허용
- 테스트가 존재하고 실패하면 커밋 차단

### 17.4 커밋/Push 전 확인

- `git commit` 실행 전 반드시 사용자에게 확인을 받는다
  - 커밋할 파일 목록(변경 요약)과 커밋 메시지를 사용자에게 알린다
  - 사용자가 명시적으로 승인해야 커밋 진행
- `git push` 실행 전 반드시 사용자에게 확인을 받는다
  - Push할 브랜치, 리모트, 커밋 수를 사용자에게 알린다
  - 사용자가 명시적으로 승인해야 push 진행

---

## 18. PR 워크플로우 규칙

PR 생성 요청을 받으면 반드시 다음 순서를 따른다:

1. **NEWS** 파일에 변경 이력 항목 추가 (vYYYYMMDD 형식)
2. **README.md** 에 추가/변경된 기능 반영
3. 위 변경사항을 커밋
4. PR 생성

---

## 19. UI 스크린샷 규칙

`client/web/index.html` 이 변경되면 반드시 다음을 수행한다:

1. PIL로 최신 UI 스크린샷을 생성하여 `docs/images/web-ui.png` 에 저장
2. README.md 의 스크린샷 이미지가 최신 상태인지 확인
3. 변경사항을 커밋에 포함