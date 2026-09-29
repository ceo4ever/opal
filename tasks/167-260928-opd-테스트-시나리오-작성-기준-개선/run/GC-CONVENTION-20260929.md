# GC CONVENTION REPORT — 20260929

## 1. 헤더

- 실행 일시: 2026-09-29 (범위: `git diff 61b6a25..HEAD` 변경분만)
- 범위: `partial` (지정 target_files 19개 중 존재·이탈 없음 확인, 변경분만 검사)
- 대상 파일: 19개 (opal/tools/test-tool/lib/scenario.py, opal/tools/test-tool/lib/e2e_contract.py, opal/tools/test-tool/schema/test-scenario.schema.json, opal/tools/test-tool/tests/test_scenario.py, opal/tools/test-tool/README.md, opal/tools/state-tool/state_tool.py, opal/tools/state-tool/schema/state.schema.json, opal/tools/state-tool/tests/test_design_gate.py, opal/tools/state-tool/tests/test_mode_transition_contract.py, opal/tools/state-tool/tests/test_state_tool_mode_contracts.py, opal/skills/op-dev-test-scenario/references/test-scenario-guide.md, opal/skills/op-scenario-gate/SKILL.md, opal/skills/op-scenario-gate/README.md, opal/agents/opal-evaluator-agent/AGENT.md, opal/agents/opal-test-agent/AGENT.md, opal/core/references/harness/scenario-gate.md, opal/core/references/harness/design-gate.md, opal/core/references/harness/test-cycle.md, docs/PROJECT.md)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 적용. 병행 참조: `.opal/AGENT.md` §금지사항, `opal/core/references/opal-doc-standard.md` §5
- APPLY 수행 여부: N (read-only 진단)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 1 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 1 |
| 파일별 상위 | `opal/tools/test-tool/lib/scenario.py` (1건), `opal/tools/state-tool/state_tool.py` (1건, 정보용·baseline 지속) |
| 카테고리별 빈도 | 죽은 코드(1 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (트리거 미발동 — 빈도 N<3, 새 카테고리 없음) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (1건)

- [ ] GC-001 [opal/tools/test-tool/lib/scenario.py:1217] 미사용·오도 상수 `_GATE_HISTORY_NAME`
  - 카테고리: 죽은 코드
  - 위반 기준: 프레임워크 인접 코드 관측 (`docs/CONVENTIONS.md`에 죽은 코드 직접 규칙 없음 — 인접 패턴상 미사용 상수는 정리 대상)
  - 설명: `_GATE_HISTORY_NAME = ".scenario-coverage-input.json"`가 이번 변경(167)에서 새로 추가됐으나 파일 전체에서 참조되지 않는다(`grep -n "_GATE_HISTORY_NAME"` 결과 정의 1건뿐). 실제 게이트 이력 파일 경로는 별도 함수 `_gate_history_path()`가 리터럴 `".scenario-gate-history.json"`으로 반환하며, 이 상수의 이름(`GATE_HISTORY`)과 값(`coverage-input.json`)이 서로 불일치해 읽는 사람에게 혼동을 준다.
  - 해결 방안: 상수를 제거하거나, 의도가 `.scenario-coverage-input.json` 파일명 상수라면 이름을 `_COVERAGE_INPUT_NAME` 등으로 정정하고 `_build_sdlc_v2_coverage_payload`/`cmd_scenario_coverage_build`의 하드코딩 리터럴(`".scenario-coverage-input.json"`, 최소 2곳)을 이 상수로 교체해 SSOT화한다.
  - 자동 수정: N (의도 확인 필요 — 단순 삭제 vs 리팩터 통합 중 선택)
  - 참조: TBD — Python 미사용 변수 관례(pyflakes F841류에 준함, 모듈 레벨 상수라 정적 툴이 기본 잡지 않음)

### Info (1건)

- [ ] GC-002 [opal/tools/state-tool/state_tool.py:9-10] `@header.description` 단일 필드 누적 서술 지속
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal/core/references/opal-doc-standard.md` §5 — "수기 누적 이력 절을 만들지 않는다", `.opal/AGENT.md` §금지사항 "수기 누적 이력 생성 금지")
  - 설명: 이번 변경은 기존에 이미 극단적으로 길게 누적되어 있던 `state_tool.py`의 `@header.description` 한 줄 문자열 끝에 "167 advisory 응답 게이트: ..." 문장을 추가로 이어 붙였다. §5가 금지하는 것은 별도 "변경이력/Changelog" **절**이며 이 파일은 히스토리 섹션이 아니라 description 한 필드에 태스크 번호별 서술을 계속 누적하는 방식이라, 문언상 §5 위반으로 단정하기는 어렵다. 다만 실질은 "현재 사실만 기재"라는 `header-standard.md` §2.1 취지와 계속 멀어지는 방향이며, 코드베이스 자체가 `code-scan validate`의 `header_history` 비차단 경고로 이 패턴을 이미 관측 대상으로 삼고 있다(state_tool.py 상단 주석에 명시).
  - 해결 방안: 이번 태스크 범위에서 강제할 사안은 아니나(baseline에서 이미 형성된 패턴), 다음 리팩터 시 description을 "현재 동작 요약" 중심으로 재작성하고 태스크별 근거는 `code-scan target` 판정에 따라 인라인 주석 또는 code-map으로 분리하는 정리를 제안한다.
  - 자동 수정: N
  - 참조: `opal/core/references/opal-doc-standard.md` §5, `opal/core/references/header-standard.md` §2.1/§7

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동(Critical/High 0건, 동일 fingerprint 3파일 이상 없음, 새 카테고리 없음).

---

## 5. 문서 작성 유도 (해당 시)

- `docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 참고 — 검사 범위와 baseline 구분

- 판정 기준: `git diff 61b6a25..HEAD`(태스크 167 시작 전 main 대비)로 산출된 변경 파일·라인만 대상으로 했다. `state_tool.py`의 거대 단일 description 필드는 baseline에 이미 존재하던 구조이므로 Info로만 기록하고 blocking 사유로 계산하지 않았다.
- `@header` 갱신(task 목록에 `167` 추가, exports 갱신)은 각 변경 파일에서 확인했고 정상 반영됐다(`scenario.py`, `test_scenario.py`, `test_design_gate.py`, `state_tool.py` 등).
- Python 구문 검증(`py_compile`)은 변경된 3개 실행 모듈(`scenario.py`, `e2e_contract.py`, `state_tool.py`) 모두 통과했다.
- trailing whitespace·디버그 print 등 기계적 위반은 diff 추가 라인에서 발견되지 않았다.
- schema(`state.schema.json`, `test-scenario.schema.json`) 변경은 기존 필드 패턴(선택 필드 + description)과 정합했다.
- 문서류(`scenario-gate.md`, `design-gate.md`, `test-cycle.md`, `AGENT.md`, `SKILL.md`, `README.md`, `test-scenario-guide.md`, `docs/PROJECT.md`)는 한국어 본문, 별도 이력 절 없음, 기존 포인터 규약(SSOT 위임) 준수를 확인했다.
