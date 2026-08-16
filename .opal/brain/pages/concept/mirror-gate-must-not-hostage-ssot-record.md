---
type: concept
title: 미러 게이트가 SSOT 기록을 인질로 잡지 않는다 — fail-open 저널 쓰기 경계
tags:
- state-tool
- ssot
- mirror
- fail-open
- defensive-design
- task-094
sources:
- task:094
related:
- state-tool
- state-md-journal-redefinition
- green-tests-do-not-imply-contract-conformance
- silent-render-failure-deterministic-gate
- degraded-execution-with-explicit-gap
created: '2026-08-16'
updated: '2026-08-16'
status: draft
---
## 개요

표시용 미러(STATE.md)의 결손·손상이 원본 기록(`state.json` 갱신, 의사결정 로그 기재)까지 막아서는 안 된다는 설계 원칙이다. 저널 쓰기는 실패해도 파이프라인을 막지 않되(fail-open), 그 실패 자체는 조용히 사라지지 않고 응답에 표면화돼야 한다.

## 결정 배경 (WHY)

- **미러가 SSOT를 인질로 잡던 구조**: STATE.md에 마커(`<!-- pipeline:start/end -->`)가 없으면 `advance`/`mark`/`block`/`add-row` 자체를 거부하는 `marker_missing` 게이트가 있었다. 이는 역방향 의존이다 — 표시용 미러의 상태(마커 존재 여부)가 원본 기록(`state.json`)의 갱신 가능 여부를 좌우했다. STATE.md를 삭제하거나 임의 편집한 정상적인 상황에서도 파이프라인 진행 자체가 막히는 결과를 낳았다(근거: task:094 TASK.md R-3, 배경 분석 (3)).
- 더 심각한 문제는 이 게이트가 **의사결정 로그 기재보다 먼저** `sys.exit`할 수 있었다는 점이다 — 마커 검사가 최우선으로 실행되면 `append_decision_log` 호출 자체가 도달하지 못해, `--force --note`로 남기려던 의사결정 근거까지 함께 증발할 위험이 있었다.
- **fail-open의 경계 설계**: 저널(STATE.md) 쓰기가 실패하는 경우(권한 제거, 디스크 오류 등)를 어떻게 다룰지가 별도 설계 문제였다. 두 가지 실패 모드가 대칭적으로 나쁘다 — ① 저널 쓰기 실패를 이유로 파이프라인 자체를 멈추면(과잉 방어) `state.json`은 이미 갱신됐는데 명령이 실패로 반환되는 모순이 생긴다. ② 반대로 실패를 완전히 삼키면(과소 방어) `--force --note`로 남기려던 의사결정 근거가 조용히 증발하는데 호출자는 그 사실조차 모른다(근거: task:094 PLAN.md 리스크 가설 H-2).

## 결정 내용

- **`marker_missing` 게이트 완전 제거**: 상태 변경 명령(`advance`/`mark`/`block`/`add-row`)은 STATE.md의 존재·마커 여부와 무관하게 항상 성공한다. STATE.md가 삭제됐거나 손상됐어도 `state.json` 갱신과 의사결정 로그 기재는 독립적으로 진행된다(근거: task:094 TASK.md R-3 AC(a)).
- **저널 쓰기는 fail-open이지만 실패는 표면화한다**: `sync_state_md`는 어떤 경로에서도 `err()`/`sys.exit()`를 호출하지 않는다. I/O 예외(권한 없음 등)가 발생하면 명령 자체는 `ok:true`로 성공 반환하되, stdout 응답에 `journal_warning`(예외 종류·기재하려던 의사결정·근거 원문 포함) 필드를 실어 호출자가 "저널에는 안 남았지만 이런 결정이 있었다"를 알 수 있게 한다(근거: task:094 코드 `sync_state_md` 문서 주석, PLAN.md H-2 대응 S-3).
- **순서 보증**: `state.json` 저장(`save_state_json`)이 저널 쓰기보다 먼저 완료된다. 저널 쓰기가 실패해도 "일어난 일이 기록되지 않는" 상태만 발생하고, "일어나지 않은 일이 기록된" 역방향 불일치는 발생하지 않는다(근거: task:094 PLAN.md H-3).
- **실환경 결함 발견**: 배포본 실증 과정에서, `journal_warning.reason`이 예외 메시지를 원문 그대로(경로 절삭 없이) 노출해 태스크 절대경로·홈 디렉토리 경로가 유출되는 결함이 발견됐다 — PLAN §5.4가 이미 요구했던 경로 절삭이 코드에 구현돼 있지 않았고, 이를 검증하는 테스트도 없었다(근거: task:094 DONE.md §8(1)). `_redact_path_like()`를 신설해 `/` 또는 홈 경로로 시작하는 토큰만 `os.path.basename`으로 치환하고, 예외 타입명·파일명(`STATE.md` 등)은 진단 가치를 위해 보존하도록 수정했다.

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — `marker_missing` 에러 코드 제거, `sync_state_md`/`append_decision_log`/`ensure_journal_skeleton` 재작성.
- **일반화 가능한 설계 원칙**: 미러·표시 계층에 게이트를 걸 때는 반드시 "그 게이트가 원본 SSOT 기록 경로보다 먼저 실행되는가"를 점검해야 한다. 원본 기록이 미러 상태에 의존하면, 미러가 SSOT를 인질로 잡는 구조가 재발한다. 이 원칙은 state-tool에 국한되지 않고 표시/영속 계층이 분리된 모든 도구 설계에 적용 가능하다.
- **일반화 가능한 fail-open 경계**: "실패해도 멈추지 않아야 하는 부수 효과(로깅·미러 갱신)"는 예외를 삼키되 그 사실을 응답 필드로 표면화해야 한다 — 침묵도 안 되고 차단도 안 된다는 두 극단 사이의 설계다.
- **문서에만 있고 코드·테스트로 이어지지 않은 요구사항은 자동 검증이 못 잡는다**: `journal_warning` 경로 절삭 결함이 대표 사례다. pytest 344건이 전부 GREEN인 상태에서도, 실배포본을 직접 실행하는 실환경 검증과 컨벤션 진단(`@header` JSON 무효 2건)이 별도로 결함을 검출했다(근거: task:094 DONE.md §8(1) — task:092의 동일 교훈이 재현).

## 관련 페이지

- [[state-tool]]
- [[state-md-journal-redefinition]]
- [[green-tests-do-not-imply-contract-conformance]]
- [[silent-render-failure-deterministic-gate]]
- [[degraded-execution-with-explicit-gap]]
