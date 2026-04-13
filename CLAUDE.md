# CLAUDE.md - maha-claude 자동화 플랜

## 개요
maha-claude는 마크다운 기반의 자동화 프로젝트입니다.

## 작업 규칙

### 커밋 컨벤션
- Linux kernel 커밋 메시지 규칙을 따른다.
  - 제목: `subsystem: 변경 요약` (영문 소문자 시작, 72자 이내)
  - 본문: 변경 이유(why)를 중심으로 작성
  - 제목과 본문 사이 빈 줄 삽입
  - Signed-off-by 라인 포함

### Push 정책
- push 전에 반드시 사용자에게 확인을 받는다.

### PR 생성 시
- main 브랜치로 PR을 생성할 때 `NEWS.md` 파일을 생성/업데이트하여 주요 수정 내용을 기록한다.

## 서브 플랜

| # | 플랜 | 파일 | 설명 |
|---|------|------|------|
| 1 | 테스트 시나리오 스크립트 작성 | [plans/01-test-scenario.md](plans/01-test-scenario.md) | 테스트 시나리오 및 스크립트 설계 |
| 2 | 테스트 수행 | [plans/02-test-execution.md](plans/02-test-execution.md) | 테스트 실행 절차 및 환경 구성 |
| 3 | 결과 확인 | [plans/03-test-results.md](plans/03-test-results.md) | 테스트 결과 검증 및 판정 기준 |
| 4 | 산출물 관리 | [plans/04-deliverables.md](plans/04-deliverables.md) | 산출물 생성, 저장, 관리 방법 |
