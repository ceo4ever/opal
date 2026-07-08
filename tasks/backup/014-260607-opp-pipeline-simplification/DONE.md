# DONE 014 — 파이프라인 간소화 (QA 통합 + 단계 축소 + 경량 트랙)

> 완료: 2026-06-08 07:31 KST | 모드: semi-agentic | 스킬: opp

## 목적

캡틴 #2 문제("작업이 단계 많고 왕복이 길어 느림") 해결. 파이프라인 단계·게이트·왕복을 줄여 속도를 개선하되, 동작 검증(TEST) 실효성은 유지·강화.

## 결과 요약

| Phase | 산출물 | 커밋 |
|-------|--------|------|
| P1 | state-tool **stage-transition guard** 신설 (단계 건너뛰기 차단을 행→도구로 이전) | `29a3a09` |
| P2 | opds STATE **19→10행** 재구성 (파일럿 레퍼런스) | `8c4267d` |
| P3 | **QA→PM Gate 통합** — 문서 QA를 PM Gate가 흡수(검증원칙 4종+self-check), QA 에이전트 디스패치/재소환 제거. 6파일 | `073c4c4` |
| P4 | **전 pilot STATE 재구성 + 정합** — 7 pilot 행 축소(opd 28→15, opsdd 35→24 등) + state_tool.py gate-pass deprecate + 공유문서 22종 정합. 32파일 | `1915535` |
| P5 | **L2 경량 트랙 공식화** — "그냥 해/직접 수행"에 L2 명칭+진입 기준+동작검증 가드+PM 자동제안 | (이 커밋) |

## AC 충족

- [x] QA Gate 단계 제거 + PM Gate가 요구사항 누락·오해 검토 + self-check 흡수 (P3)
- [x] opds STATE 행 19→10 (산출물 행 흡수 + State Gate 중복 제거) (P2)
- [x] 모든 pilot 트랙 일관 적용 — opd/opds/opp/opdw/opwt/oppd/opsdd/gc (P4)
- [x] interactive 하네스 ↔ opds QA Gate 모순 해소 (P3)
- [x] L2 경량 트랙 진입 기준 정의 (P5)
- [x] TEST-SCENARIO·TEST·verify 불변 확인 — 전 Phase 동작검증 가드 (M-5)

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| M-A | State Gate 별도 행 전면 제거 + 단계 건너뛰기 차단을 state-tool guard로 이전 | 행(advisory)→도구(deterministic). 행↓ + 강제↑ |
| M-1 | 문서 QA를 PM Gate로 통합 (QA Gate 단계 제거) | QA 워커 실사용 2개뿐, PM Gate가 문서검증 흡수 |
| gate-pass | deprecate(레거시 retain) | 4행 패턴(QA/State Gate) 소멸로 존재 이유 상실. 하위호환 위해 명령은 유지 |
| L2 | "그냥 해"를 L2로 공식화 (신 트랙 미신설) | PLAN 정의가 "그냥 해"와 동일. 헌법 §2 단순성 |

## 검증 (헌법 §4 동작 증거)

- state-tool 테스트 **158 passed** (149 베이스라인 + 9 신규, 회귀 0)
- 8 pilot 표 내 State/QA Gate 행 **0** / gate-pass 실호출 **0** / 신정책 위반 **0**
- 전 pilot `init --rows-from` 파싱 OK: opd 15 / opds 10 / opdw 9 / opp 9 / opwt 10 / opgc 7 / opsdd 24
- 추가 발견·수정: state_tool.py cmd_mark CLOSE 판정 항목명 비의존화(잠재버그), opsdd `--rows-from` 파싱 기존버그

## 잔여 / 후속

- **install 재실행 필요** — 모든 변경이 소스(`opal/`)에 있고 배포본(`~/.opal/`)은 구버전. 캡틴이 별도 진행(b 선택)
- 잔여 미해결 이슈: 없음
