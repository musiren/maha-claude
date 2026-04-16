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