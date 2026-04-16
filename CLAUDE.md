# CLAUDE.md (Platform Level)

## 1. 목적
이 시스템은 사용자 터미널 기반으로 테스트 스크립트 작성 및 실행을 지원하는
중앙집중형 Agent 플랫폼이다.

모든 실행 로직은 서버에서 통제되며, 사용자는 내부 동작을 알 필요가 없다.

---

## 2. 전체 아키텍처

본 시스템은 다음 3계층으로 구성된다.

1. Windows Terminal Client
2. FastAPI + Session Manager (Gateway)
3. Agent Orchestrator (Core Execution Engine)

각 계층은 명확히 분리되며, 역할을 침범하지 않는다.

---

## 3. 핵심 설계 원칙

### 3.1 중앙 통제
- 모든 실행은 서버에서 수행된다
- 클라이언트는 절대 실행 로직을 가지지 않는다

### 3.2 책임 분리
- Client: 입력/출력
- Gateway: 인증/세션/라우팅
- Orchestrator: 판단/실행 제어

### 3.3 Tool 기반 실행
- 모든 실제 작업은 Tool 계층을 통해 수행된다
- 직접 외부 시스템 호출 금지

### 3.4 변경 가능성 최소화
- 사용자 환경은 변경하지 않는다
- 서버에서 일괄 업데이트

---

## 4. 데이터 흐름

1. 사용자 입력 (Terminal)
2. Gateway 인증 및 세션 확인
3. Orchestrator로 전달
4. Orchestrator가 Tool 선택
5. Tool 실행 (Jenkins / DB / Git / Bench API)
6. 결과 요약 후 사용자에게 반환

---

## 5. 계층별 책임

### 5.1 Windows Terminal Client
- 사용자 입력 처리
- 결과 표시
- 세션 유지

절대 수행 금지:
- 테스트 실행
- Jenkins 호출
- Git 접근
- DB 접근

---

### 5.2 FastAPI + Session Manager
- 인증 및 세션 관리
- 요청 라우팅
- 사용자별 격리

절대 수행 금지:
- 비즈니스 로직 실행
- 테스트 수행
- Tool 호출

---

### 5.3 Agent Orchestrator
- 사용자 의도 해석
- Tool 선택
- 실행 흐름 제어
- 결과 요약

---

## 6. Tool 계층 규칙

### 6.1 기본 원칙
- 모든 외부 시스템은 Tool로 추상화한다
- Tool은 Python 모듈 형태로 구현한다

### 6.2 예시 Tool
- create_test_script
- update_test_script
- run_test
- get_test_history
- summarize_results

### 6.3 금지사항
- Orchestrator에서 직접 Jenkins 호출 금지
- Orchestrator에서 직접 DB 접근 금지

---

## 7. 세션 관리

- 모든 요청은 세션 기반으로 처리된다
- 세션은 Redis에 저장된다
- 사용자 간 데이터는 완전히 격리된다

세션 구성:
- user_id
- session_id
- workspace
- context

---

## 8. 보안 정책

### 8.1 접근 제어
- 모든 요청은 인증 필수
- 권한 기반 Tool 실행

### 8.2 데이터 보호
- 민감 정보 로그 금지
- 외부 네트워크 접근 제한

### 8.3 실행 제한
- 임의 코드 실행 금지
- Shell 접근 금지

---

## 9. 승인 정책

다음 작업은 반드시 승인 필요:

- 테스트 실행 (run_test)
- 스크립트 변경 (update_test_script)
- 대량 작업 수행

승인 없이 자동 실행 금지

---

## 10. 에러 처리

- Tool 실패 시 재시도
- 실패 원인 분석 후 사용자에게 요약 제공
- 시스템