# DONE: 부트스트랩 이벤트 하네스 경량화

## 결과

- 세션 부트를 `session.disabled`, `session.worker`, `session.assistant`, `session.project` 이벤트로 분할함.
- PM·파일럿·단계·워커는 해당 이벤트에서 최신 문서 전문을 로드하고 receipt와 SHA-256를 검증함.
- `bootstrap: off`와 `[WORKER]` 전역 부트 스킵은 OPAL 문서 0건으로 구분함.
- 프로젝트 인지 비서는 PM을 활성화하지 않고 최대 3개·1KB 이하 메모리 부트 브리프만 사용함.
- `opal-harness.md`를 호환 인덱스로 축소하고 Guards·Modes·Worktree·Capability·PM activation 규칙을 owner 문서로 분리함.
- `opal-doc-standard.md §5`를 이력·버전 관리 SSOT로 적용해 수기 누적 이력 절을 제거함.

## 실측

| 상태 | 변경 전 | 변경 후 | 감소율 |
|---|---:|---:|---:|
| 일반 비서 | 41,703 B | 9,374 B | 77.52% |
| 프로젝트 인지 비서 | 119,644 B | 9,744 B | 91.86% |

- 모든 부트 payload는 30KB 이하임.
- 메모리 부트 브리프는 370 bytes, 활성 메모리 1개, history 0개임.

## 검증

- S1–S12: 12 pass / 0 fail / 0 blocked, RED 3/3 보존.
- event-loader 8/8, memory-tool 188/188, opal-agent 27/27, state-tool 420 pass(3 skip).
- 이벤트 14개, 파일럿 10개, 워커 15개 static-check 위반 0건.
- code-scan 변경 코드 11/11 covered, coverage 100%, newly_uncovered 0건.
- 컨벤션 진단 69파일, Critical/High/Medium/Low/Info 전부 0건.
- macOS 설치 exit 0, source↔`~/.opal` 핵심 15경로 SHA-256 parity 통과.

## 산출물

- [TASK.md](TASK.md), [PLAN.md](PLAN.md), [TEST-SCENARIO.md](TEST-SCENARIO.md), [TEST.md](TEST.md)
- [GC-CONVENTION-2026-09-09T19-28-00.md](GC-CONVENTION-2026-09-09T19-28-00.md)
- [events.json](../../opal/core/references/events.json)
- [opal-harness.md](../../opal/core/references/opal-harness.md)
- [opal-doc-standard.md](../../opal/core/references/opal-doc-standard.md)
- 프레임워크 개선 제안: `~/.opal/fw-inbox/20260910-095209-*-worktree-워커-변경-경계-자동-차단.md`
- 프레임워크 개선 제안: `~/.opal/fw-inbox/20260910-095209-*-install-Console-scan-범위-시간-제한.md`

## 한계·운영 상태

- 현재 환경에 `pwsh`가 없어 Windows는 정적 parity만 확인함.
- 선택적 Console scan이 장기 I/O 대기로 정체해 비필수 하위 프로세스를 종료했으며, 설치 부모는 exit 0으로 완료됨.
- worktree `feat/OP-TASK-113`은 머지 대기 상태이며 커밋·merge·worktree 제거는 수행하지 않음.
