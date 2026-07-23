# DONE: state-tool `--import-existing` task-step key 유실 결함 수정

> 완료일: 2026-07-23 | 스킬: opds | 모드: agentic | 상태: 완료 (미배포·미커밋)

## 요약

`state-tool init --import-existing`가 기존 task-step key를 전부 유실시키던 FW 결함을 수정했다. 근본 원인은 import 복구 원천을 **key 컬럼이 없는 STATE.md 렌더 표**에 둔 lossy projection이었다. import 파싱으로 얻은 keyless rows에 권위 원천(기존 state.json → pipeline.json 스펙)의 key를 `(stage,item)` 순서 소비 매칭으로 재접합하도록 고쳤다.

## 근본 원인 (확정)

- `cmd_init` import 분기가 rows를 STATE.md 마크다운 표에서 재파싱 (`parse_existing_state_md`) — 렌더 표 컬럼 `| # | 단계 | 항목 | 상태 | 시점 |`에 key 없음.
- 결과 keyless rows → `--force`가 기존 state.json(key 보유) 덮어씀 → `schema_version` "1.1"→"1.0" 강등 → `--task-step` 주소 전면 불능(070 무력화).

## 변경 내용

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | 신규 헬퍼 `_key_source_index`·`_reattach_import_keys` + `cmd_init` import 분기 3단계 재접합 블록(기존 state.json soft-load → pipeline.json 폴백 → keyless+경고). schema 계산 이전 배치로 "1.1" 유지(line 무변경). @header 074 변경이력 추가 |
| `opal/tools/state-tool/tests/test_state_tool.py` | 신규 회귀 클래스 `TestImportPreservesKeys` 5건 (S-a~S-e) |

## 설계 결정 (PLAN §3.2)

- **DEC-1** 매칭축 = `(stage,item)` 순서 소비 — key가 stage 결속·row_id는 import 시 재부여되어 위치 변동적.
- **DEC-2** state.json에 key 전무하고 재접합 후에도 keyless 남을 때만 `--rows-from *.json` 폴백.
- **DEC-3** schema 승격 로직 무변경 — 재접합을 계산 이전 배치해 `any(key)` 자동 True.
- **DEC-4** 덮어쓰기(`save_state_json`) 이전 soft-load(try/except)로 기존 key 원천 확보.
- **DEC-5** 원천 전무 시 keyless + stderr 경고 1줄, stdout 불변(하위호환).

## 검증 결과

- 신규 5건 RED(수정 전 전량 FAIL) → GREEN(수정 후 전량 PASS) 전환 확인.
- 전량 스위트 254 passed + 22 subtests passed, **이번 변경 신규 회귀 0건**.
- 코드품질 `py_compile` PASS, 보안(시크릿 0·I/O 경계·soft-load) PASS.
- RED 게이트 `verify --red-check` 통과, 작성자(opal-test-agent)≠구현자(opal-task-agent) 분리 준수.

## 후속 조치 (미완 — 캡틴 지시 대기)

1. **배포**: `~/.opal/`에 미배포. 라이브 반영 위해 install 재배포 필요 (배포 경계 — 캡틴 배포).
2. **커밋**: 미커밋. 070/071 등 병존 미커밋 건과 함께 커밋 범위 조율 필요.
3. **사이드 이슈**: `TestVerify::test_verify_passes_own_test_scenario_md`가 034 TEST-SCENARIO 절대경로(`AiStudio`/`opal` 오타·대소문자) 하드코딩으로 상시 실패 — 별도 태스크로 정정 권장.
