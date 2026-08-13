# DONE: state-tool STATE.md "다음 액션" 자동 파생

> 완료일: 2026-07-23 | 스킬: opd (--agentic) | 모드: agentic
> 상태: 완료·미커밋·미배포후속(캡틴 배포/커밋) — install 재배포는 EXECUTE Step 7에서 이미 1회 실행됨

## 1. 목표 달성 요약

STATE.md `## 다음 액션`이 `init` 이후 갱신되지 않아 태스크 내내 첫 단계 값에 고정되던 결함을, `advance`/`mark` 시 파이프라인 프론티어(첫 미완료 행)에서 **자동 파생**하도록 해소했다. `state.json`에 `next_action` 필드를 신설해 렌더 SSOT로 삼았다.

- **핵심 발견**: 이는 단순 버그가 아니라 `state-template.md:34`가 "다음 액션은 PM 수동 갱신(state-tool 범위 밖)"으로 명문화한 **의도적 설계의 반전**이었다. 따라서 설계문서 갱신 + 기존 테스트 2건 반전을 스코프에 포함했다.
- **실증(dogfooding)**: 배포된 새 도구로 이 태스크 자신의 STATE.md에서 결함 재현·해소를 확인 — `ANALYSIS 단계 진입`(stale) → `TEST 작업 진입` → `CLOSE DONE.md 생성 진입`으로 실시간 추적.

## 2. 요구사항 달성 (R-1~R-6)

| # | 요구사항 | 상태 | 근거 |
|---|---------|------|------|
| R-1 | state.json `next_action` 필드 + init 영속화 + 스키마 등록 | ✅ | `cmd_init` 딕셔너리 기록, schema `properties` optional 등록(`required` 미포함), state.json:176 실증 |
| R-2 | advance/mark 자동 파생 | ✅ | `_derive_next_action`(프론티어 스캔 + `_COMPLETE_STATUSES` 재사용), cmd_advance/cmd_mark 통합 |
| R-3 | STATE.md 렌더 반영 | ✅ | `update_next_action_section`(첫 줄 정규식 치환), state.json↔STATE.md 정합 |
| R-4 | `--next-action` 오버라이드 | ✅ | init 유지 + advance/mark 신설(per-transition 비지속) |
| R-5 | 테스트 (RED-first) | ✅ | 신규 `TestNextActionAutoDerive` 9건 RED→GREEN, `TestFreeTextPreservation` 2건 반전, 회귀 249 pass |
| R-6 | 문서·배포 | ✅ | state-template.md 설계 반전, README/@header/변경이력(072), install 재배포·diff 0 |

## 3. 미확정 사항 확정 (M-1~M-3)

- **M-1 파생 포맷·치환 범위**: **첫 줄만 정규식 치환**(`(^## 다음 액션\n)([^\n]*)`) — 하위 PM 자유 기재 라인 보존. 포맷 = 프론티어 행 상태별 `"{stage} {item} 진입/진행 중/블로커 해소"`.
- **M-2 전체 완료 표현**: `"태스크 완료"` (`_derive_next_action` 루프 미스 시 반환).
- **M-3 오버라이드 지속성**: **per-transition 비지속** — 다음 전이 시 `--next-action` 미지정이면 자동 파생 복귀. state.json `next_action`은 "마지막 write 값" 렌더 미러(지속 정책 아님).

## 4. 변경 파일 (7건)

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | `_derive_next_action`·`update_next_action_section` 신규, `sync_state_md(next_action=None)`, cmd_init/advance/mark 통합, argparse `--next-action`(adv/mark), @header 072 |
| `opal/tools/state-tool/schema/state.schema.json` | `next_action` properties(oneOf string/null) 추가, `required` 불변 |
| `opal/tools/state-tool/tests/test_state_tool.py` | 신규 `TestNextActionAutoDerive`(9), `TestFreeTextPreservation` 2건 반전 |
| `opal/tools/state-tool/README.md` | init/advance/mark 문서 + 변경이력 v1.6 |
| `opal/core/references/harness/state-template.md` | 설계 반전(34/40/82) + 변경이력 v1.6 |
| `opal/core/references/harness/task-process.md` | `--next-action` 계약 보강 v1.5 |
| `opal/skills/op-task/SKILL.md` | `--next-action` 계약 보강 v2.2 |

> 배포: `opal/tools/` → `~/.opal/tools/` install 재실행 완료, 소스-배포본 diff 0. `~/.opal/` 직접 편집 없음(배포 경계 준수).

## 5. 검증 결과

- **회귀**: 250 tests / 249 pass — 유일 실패는 무관·사전 존재 결함(`TestVerify.test_verify_passes_own_test_scenario_md`, 이동된 `tasks/backup/034-...` 경로). 072 무관.
- **RED-first**: `TestNextActionAutoDerive` 9건 파생 전 RED(exit 1, 8 fail) → 구현 후 GREEN(OK) 전환 로그 확인. 작성자(opal-test-agent red) ≠ 구현자(op-dev-execute) 분리.
- **코드품질**: py_compile Pass, ruff 신규 위반 0(기존 부채 14건은 072 범위 밖).
- **보안**: 하드코딩 시크릿 0, 정규식 섹션 경계 보호(`[^\n]*`).
- **컨벤션**: GC-CONVENTION-2026-07-23-1222.md — Critical/High 0.
- **하위호환**: `next_action` 없는 구버전 state.json 무손상(forward-guard 테스트 통과), 기존 `init --next-action` 동작 불변, 070 task-step key 체계 무접촉.

## 6. 산출물

- TASK.md / ANALYSIS.md / PLAN.md / TEST-SCENARIO.md / AGENTIC-LOG.md / GC-CONVENTION-2026-07-23-1222.md / DONE.md(본 문서)

## 7. 후속 (캡틴 지시 대기)

- **커밋**: 미커밋 — 캡틴 지시 시 수행 (070·071도 미커밋 상태, 070은 install 재배포 후속 잔존).
- **배포**: install은 이 태스크에서 1회 실행됨(라이브 반영). 070의 `--row` deprecated 라이브 잔존 등 기존 배포 후속과 함께 캡틴 판단.
