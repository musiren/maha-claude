# FastAPI + Session Manager CLAUDE.md

## 1. 목적
API Gateway 및 세션 관리 계층

## 2. 핵심 역할
- 인증 처리
- 세션 관리
- 요청 라우팅
- 로깅

## 3. 설계 원칙
- Stateless API + Stateful Session 분리
- 확장 가능한 구조

## 4. 기능
- 로그인
- 토큰 발급
- 세션 생성
- 세션 종료

## 5. 세션 관리
- Redis 사용
- TTL 설정
- 사용자별 isolation

## 6. 인증
- JWT 기반
- 권한 체크 필수

## 7. 금지사항
- 비즈니스 로직 처리 금지
- 테스트 실행 금지
- DB 직접 변경 최소화

## 8. API 설계
- RESTful 구조
- 명확한 endpoint naming

## 9. 에러 처리
- 표준화된 에러 코드
- 사용자 메시지 분리

## 10. 로깅
- 요청/응답 로그
- 사용자별 트래킹

## 11. 보안
- HTTPS 필수
- 인증 토큰 검증

## 12. 확장성
- 수평 확장 가능
- stateless 유지

## 13. 성능
- 비동기 처리
- 캐싱 활용

## 14. 테스트
- API 테스트 자동화
- 부하 테스트

## 15. 유지보수
- API 버전 관리
- backward compatibility