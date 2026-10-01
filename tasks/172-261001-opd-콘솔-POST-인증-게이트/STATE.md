# STATE: 콘솔 POST 인증 게이트 (Gateway Phase 0)

> 최종 갱신: 2026-10-01 16:25:21
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-10-01 14:39:03 | design-decision(detail): 진입 token 채널을 OPAL_HOME/run/console-entry 0700 디렉터리의 해시명 0600 파일 1회 소비로 구현 | 제안서 §6.2의 사용자 전용 0600 런타임 채널 요구를 서버 협조 없이 CLI·E2E 하네스가 같은 계약으로 충족하며 token 원문은 디스크에 남지 않음(D-9) |
| 2 | 2026-10-01 14:39:03 | design-decision(detail): 구형 Brain spawn 직렬화를 위해 subprocess.run을 Popen+락 밖 communicate로 전환 | 제안서 §8의 비활성화 완료 후 신규 프로세스 0회 요구를 락을 run 전체 구간에 걸지 않고 충족하는 최소 방법이며 기존 어댑터 호출 계약은 보존(D-16, H-1) |
| 3 | 2026-10-01 14:39:04 | design-decision(detail): /api 하위 전부 default-deny(예외 auth 2종), /health에 auth 마커 필드 추가, 구버전 데몬에는 console open이 열지 않고 재기동 안내 | AC-5 GET 점검을 개별 판정 대신 일괄 세션 보호로 닫고, 구버전 무인증 데몬에 token을 발급해도 보호가 없다는 H-4를 막기 위함(D-2, D-11, D-12) |
| 4 | 2026-10-01 14:39:04 | design-decision(detail): test-tool environment.json에 선택 키 session_bootstrap을 추가해 프로젝트가 선언한 훅으로 E2E 인증 세션을 만든다 | AC-6의 같은 진입 token 교환 요구를 도구가 OPAL Console을 직접 알지 않고 충족하며 기존 선택 키 확장 방식과 호환, 키 없는 환경 파일은 동작 불변(D-20) |
| 5 | 2026-10-01 16:09:47 | additional row inserted after row 8: stage=TEST, item=S-16 code-scan @header JSON 이스케이프 4건 수정(주석만), key=test.s_1, new_row_id=9 | additional work entry |
| 6 | 2026-10-01 16:19:15 | additional row inserted after row 9: stage=TEST, item=보안 M1: E2E redaction 키에 csrf_token·entry·browser_entry_fragment·opal_console_session 추가, SECURITY.md 무세션 표면 서술 정정, key=test.item_1, new_row_id=10 | additional work entry |

## 블로커
없음
