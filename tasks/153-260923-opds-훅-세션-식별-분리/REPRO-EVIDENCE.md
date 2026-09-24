# 사전 독립 재현과 인계

## 확인된 사실
- 설치본 ownership_core.resolve_session_id는 OPAL_SESSION_ID → 플랫폼 환경변수 → payload.session_id 순서다.
- session_end_hook은 이 결과로 owned_task_paths를 찾고 release 및 registry close를 실행한다.
- 격리 재현 경로: /private/var/folders/fc/w424kvjn3mxfk6nyzkw_8b740000gn/T/opal-lease-review-lv7invh6
- 임시 .opal/AGENT.md와 task-ownership.json에 임시 태스크만 가리키도록 설정하고, 설치본 lease.claim/session_registry.register로 부모 레코드를 만들었다. subprocess env의 OPAL_PROJECT_ROOT를 임시 루트로 고정했다. 실제 부모 세션 환경은 출력하거나 변경하지 않았다.
- 실제 실행 바이너리: /Users/iskang/.local/bin/claude

| 인자 배열 | 부모 OPAL_SESSION_ID | 종료 코드 | lease | registry |
|---|---|---|---|---|
| mcp get context7 | review-parent-get | 0 | released | closed |
| mcp list | review-parent-list | 0 | released | closed |
| mcp get context7 | 제거 | 0 | active | active |
| mcp get opal-review-nonexistent | review-parent-inherited | 1 | active | active |

실험 후 각 임시 lease만 release했다. 이 자료는 사전 관찰이며 정식 RED/GREEN 검증을 대체하지 않는다.

## 사건 인과의 한계
installer 실행 22:55:41~22:56:26, 기존 PM fa968a3c 레지스트리 mtime 22:56:23 및 closed가 일치한다. 원인은 강하게 지지되나 당시 훅 payload가 없어 정확한 개별 호출의 직접 추적은 아니다. PID 25584의 다른 Claude가 task_152 cwd에서 살아 있었고, a5db/405b 세션에 /clear 기록이 있다. f3bd와 PID의 직접 연결은 미확정이다. 서브에이전트 자체가 lease를 탈취했다고 적지 않는다.

## 실행 인계
사용자 최종 승인: `좋아. //opds --agentic --pm --wt`.
합의한 구현: 훅에서는 payload 신원만 사용하고 누락 시 no-op/진단; 일반 CLI는 기존 환경변수 규약 보존. SessionStart/End뿐 아니라 heartbeat, guard, stop 소비자와 테스트 기대값까지 분석한다. 병렬 소유권 원자성 결함은 별도 범위이며 이번 원인으로 섞지 않는다.
기존 task 152와 기존 탭의 lease에는 손대지 않는다. installer를 실사용 HOME에 실행하지 않는다. 임시 배포·명시 훅 설정으로 검증하되 실제 Claude CLI 호출은 유지한다. 기본 브랜치 merge/push/실사용 배포는 이번 승인 범위에 없다.
