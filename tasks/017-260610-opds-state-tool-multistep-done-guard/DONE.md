# DONE: state-tool 다중 Step EXECUTE 행 조기 done 가드

> 완료일: 2026-06-10 | 스킬: opds (semi-agentic) | 태스크: 017 (016 후속)

## 요약

016 EXECUTE에서 발생한 **STATE 행 조기 done 사고**의 근본 원인(state-tool 도구 갭)을 차단했다. `mark`가 `--step N/M`에서 **N<M인데 `--done`을 받으면 행을 done으로 닫던** 문제를, N<M이면 `in_progress` 유지(+진행률 영속화), N==M에서만 done으로 수정했다. 016에서 도입한 **RED-first 트랙을 자기적용**하여 검증했다.

## 확정 설계 (캡틴 결정)

| # | 결정 |
|---|------|
| C-1 | `--step N/M` N<M + `--done` → done 안 함, **in_progress 유지** (진행률만 기록) |
| C-2 | N==M에서만 done |
| C-5 | 진행률 `step:"N/M"` **state.json 영속화** + 조기 close 3층 가드(①행done ②단계전환 ③CLOSE) |

**핵심 통찰**: ②단계전환·③CLOSE 가드는 **신규 코드 불필요**. `in_progress`가 `_COMPLETE_STATUSES`에 없으므로, N<M 행을 in_progress로 유지하면 기존 `stage_transition_violation` guard가 다음 단계·CLOSE 진입을 자동 차단한다(TS-003/004로 실증).

## 산출물 (변경 2파일)

- `opal/tools/state-tool/state_tool.py` — `_parse_step` 헬퍼 + `cmd_mark` N/M 분기(in_progress 유지/done) + `is_close_last`에 `status=="done"` 가드 + `ok` status 정확화 + @header 017
- `opal/tools/state-tool/tests/test_state_tool.py` — `TestMultiStepDoneGuard` 7케이스(TS-001~005,007,008)

## 동작검증 (헌법 §4 — 실제 실행 증거)

| 항목 | 결과 |
|------|------|
| RED (구현 전) | `Ran 172 tests, FAILED (failures=5)` exit 1 — TS-001/002/003/004/008 |
| GREEN (구현 후) | **`Ran 172 tests OK`, exit 0** (기존 165 + 신규 7) |
| 회귀 | `test_error_codes_count`==30 유지, 신규 ERROR_CODE 0 |
| 하위 호환 | `--step` 미지정/비정형 → 기존 즉시 done (TS-005/007) |

RED-first 자기적용: 작성자(RED 워커) ≠ 구현자(GREEN PM 직접).

## 후속 조치 (필수)

1. **install 재배포 — 016 + 017 일괄**: 두 태스크 변경분(`state_tool.py`/`test`/`red-first.md`/스킬·에이전트·참조 다수)이 `~/.opal/`로 배포돼야 실제 활성화. 배포 후 smoke(`mark ... --step 1/2` → in_progress 확인) 1회.
2. **커밋 분리**: 016+017 변경분만, 워킹트리의 무관한 미커밋 변경(ppt-builder 등)과 격리.

## 특이사항

- semi-agentic 모드. EXECUTE 이후 PM 자율, CLOSE 진입 캡틴 승인("확인").
- verify mock 오탐(설명 문장의 `MagicMock`/`@patch` 리터럴 자기검출) → 016과 동일 패턴, 표현 수정으로 해소.
- install(Step 4)은 환경 변경이라 EXECUTE 자율 실행 대신 CLOSE 후 캡틴 승인 일괄로 분리.
