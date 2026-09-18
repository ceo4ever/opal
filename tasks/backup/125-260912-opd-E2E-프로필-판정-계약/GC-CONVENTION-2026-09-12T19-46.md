# GC CONVENTION REPORT — 2026-09-12T19-46

## 1. 헤더

- 실행 일시: 시작 기준 2026-09-12 19:44:00 KST / 최종 산출 2026-09-12 19:49:57 KST / 실제 경과 5분 57초
- 산출물 timestamp: `2026-09-12T19-46` (호출자 지정)
- 범위: `all` / 대상 파일 24개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md`, `docs/PROJECT.md`, `opal/core/references/header-standard.md`, `opal/core/references/opal-doc-standard.md`
- 비교 기준: `git show HEAD:<file>` + 현재 diff + initial `GC-CONVENTION-2026-09-12T19-22.md`
- APPLY 수행 여부: N (read-only 진단)
- 검사 실행 상태: `pass` — 24/24 파일 검사, missing capability 없음
- 태스크 회귀 판정: **PASS** — introduced/regressed blocking finding 0건
- 저장소 잔존 finding: 10건. 모두 HEAD에 동일하게 존재하고 현재 diff가 위반 줄/계약을 건드리지 않아 이 태스크의 회귀 게이트에서만 scoped suppression 처리했다. 위반 자체의 T0 `blocking` disposition은 유지한다.

---

## 2. 요약 지표

| 지표 | 값 |
|---|---|
| 현재 잔존 이슈 | 10 |
| 현재 잔존 심각도 | Critical 0 / High 1 / Medium 3 / Low 6 / Info 0 |
| introduced/regressed 심각도 | Critical 0 / High 0 / Medium 0 / Low 0 / Info 0 |
| pre-existing 심각도 | Critical 0 / High 1 / Medium 3 / Low 6 / Info 0 |
| blocking regressions | **0** |
| initial 해소 | 8건 (`GC-011`~`GC-018`) |
| `GC-009` 보정 결과 | 수기 이력 위반은 pre-existing으로 잔존하나, 이번 diff가 이력 행을 갱신하던 회귀는 해소 |
| 자동 수정 가능(잔존) | 8 |
| 수동 조치 필요(잔존) | 2 |
| 문서 업데이트 제안 | 0 — 적용 규칙이 이미 T0 문서에 존재 |

`PASS`는 이번 태스크가 새로 만들거나 악화한 규약 위반의 게이트 판정이다. 아래 잔존 finding은 저장소 전체 규약 관점에서 여전히 유효하며, suppression scope 밖에서는 blocking이다.

---

## 3. initial correction 재검사

| initial finding | 최신 판정 | 근거 |
|---|---|---|
| `GC-011` | resolved | `tests/test_e2e_contract.py`의 비표준 `@header.track` 제거. `code-scan validate`의 `header_history=0` |
| `GC-012` | resolved | `tests/test_test_tool.py`의 비표준 `@header.track` 제거. `code-scan validate`의 `header_history=0` |
| `GC-013` | resolved | `lib/e2e_adapter.py:10`의 `depends`에 직접 import `lib.e2e_contract` 반영 |
| `GC-014` | resolved | `lib/scenario.py:22`의 `depends`에 직접 import `lib.e2e_contract` 반영 |
| `GC-015` | resolved | `test_tool.py:6-15`의 description/depends가 scenario 라우팅과 `lib.e2e_contract`, `lib.scenario`를 반영 |
| `GC-016` | resolved | `tests/test_scenario.py:7-31`의 description/scenarios/exports를 현재 테스트 집합에 맞췄고, 정적 AST 대조에서 미등재 Test class 0건 |
| `GC-017` | resolved | `tests/test_test_tool.py:7-17`이 현재 회귀 테스트 역할을 기술하고, 비표준 track·FAIL 예상·수기 변경이력 제거 |
| `GC-018` | resolved | `tests/test_e2e_contract.py:22-24`가 현존 production owner를 전제로 한 현재형 회귀 보호 설명으로 교체 |

`GC-009`는 `verification.md:201`의 수기 `## 변경이력` 자체가 HEAD부터 존재하므로 finding은 잔존한다. 다만 최신 `git diff --unified=0`은 30행과 72행만 변경하며 201행 이력 절이나 행을 수정하지 않으므로 initial의 task-introduced 악화는 해소됐다.

---

## 4. 잔존 finding — pre-existing baseline

모든 항목의 suppression은 `task-introduced regression gate only` 범위다.

### Critical (0건)

없음.

### High (1건, pre-existing 1)

- [~] `GC-001` [`opal/agents/opal-loop-action-agent/AGENT.md:55`] 핵심 에이전트가 Claude 전용 디스패치 분기를 소유함
  - 카테고리: 플랫폼 분기 격리
  - 위반 기준: 프로젝트 T0 `docs/CONVENTIONS.md` §플랫폼 분기 격리
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: 현재 55, 78, 93, 272-273행의 claude 채널·`--provider claude` 계약은 HEAD 같은 행에도 동일하다. 현재 diff의 이 파일 hunk는 348행과 356행뿐이다.
  - 해결 방안: provider 선택·모델 치환·세션·출력 파싱·가용성 분기를 어댑터 계층으로 옮긴다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §플랫폼 분기 격리

### Medium (3건, pre-existing 3)

- [~] `GC-002` [`opal/skills/opal-pilot-dev/SKILL.md:81`] 공통 Dev 스킬이 `CLAUDE.md` 폴백을 고정함
  - 위반 기준: 프로젝트 T0 `docs/CONVENTIONS.md` §플랫폼 분기 격리
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: 현재 81, 110, 188행과 HEAD의 동일 행이 일치한다. 현재 diff hunk는 219행뿐이다.
  - 해결 방안: 플랫폼 중립 프로젝트 문서 선택 계약을 사용한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §플랫폼 분기 격리

- [~] `GC-003` [`opal/skills/opal-pilot-dev-short/SKILL.md:1`] 스킬 frontmatter에 `triggers`와 `version`이 없음
  - 위반 기준: 프로젝트 T0 `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: 현재와 HEAD frontmatter는 동일하게 `name`, `description`만 가진다. 현재 diff hunk는 140행뿐이다.
  - 해결 방안: 소비 계약에 맞는 `triggers`, `version`을 추가한다.
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter

- [~] `GC-004` [`opal/skills/opal-pilot-dev/SKILL.md:1`] canonical Dev 스킬 frontmatter에 `triggers`와 `version`이 없음
  - 위반 기준: 프로젝트 T0 `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: 현재와 HEAD frontmatter는 동일하게 `name`, `description`만 가진다. 현재 diff hunk는 219행뿐이다.
  - 해결 방안: opd/opds 라우팅에 맞는 `triggers`, `version`을 추가한다.
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter

### Low (6건, pre-existing 6)

- [~] `GC-005` [`opal/core/references/tools.md:1157`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD 1142행부터 같은 이력 절이 존재한다. 최신 diff의 마지막 hunk는 669행이며 이력 절 내용은 미접촉이다.
  - 해결 방안: 이력 절을 제거하고 git/tasks를 이력 SSOT로 사용한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [~] `GC-006` [`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:92`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD 79행부터 같은 이력 절이 존재하고 현재 diff는 33-45행 추가뿐이다.
  - 해결 방안: 이력 절을 제거한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [~] `GC-007` [`opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:582`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD 578행부터 같은 이력 절이 존재하고 현재 diff hunk는 272-304행에 한정된다.
  - 해결 방안: 이력 절을 제거한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [~] `GC-008` [`opal/skills/opal-pilot-project-loop/references/journey-flow.md:103`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD와 현재 모두 103행에 같은 이력 절이 있고 현재 diff hunk는 89행뿐이다.
  - 해결 방안: 이력 절을 제거한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [~] `GC-009` [`opal/skills/opal-pilot-project-loop/references/verification.md:201`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD와 현재 모두 201행에 같은 이력 절이 있다. 최신 diff는 30행과 72행만 변경하며 initial에서 관측된 이력 행 변경은 더 이상 없다.
  - 해결 방안: 이력 절을 제거한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [~] `GC-010` [`opal/tools/test-tool/README.md:445`] 수기 누적 `## 변경이력` 절
  - 위반 기준: 프로젝트 T0 `opal-doc-standard.md` §5
  - disposition: `blocking`; baseline suppression: active (`task-introduced regression gate only`)
  - 근거: HEAD 419행부터 같은 이력 절이 존재한다. 앞선 문서 추가로 현재 위치만 445행으로 이동했으며 diff는 이력 헤더·행 내용을 수정하지 않는다.
  - 해결 방안: 이력 절을 제거한다. 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

### Info (0건)

없음.

---

## 5. 정적 검사 결과

- event receipt 직접 검증: `ok=true`, 문서 4개 검증
- 대상 검증: 24/24 존재, 24/24 `project_root` 내부, 입력 순서와 `checked_files` 완전 일치
- `git diff --check -- <target_files>`: 출력 없음
- Python AST parse: 8/8 pass
- AGENT/SKILL frontmatter YAML: 7/7 pass
- YAML 대상: 2/2 pass
- JSON parse + `Draft7Validator.check_schema`: pass
- `code-scan target`: Python 8개 모두 `write_to=inline`, `reason=header_source_inline`
- `code-scan validate --changed <8 Python>`: `ok=true`, coverage 8/8, `exports_not_found=0`, `header_history=0`, violations 0
- 독립 header 사실 대조: 선언 export 미존재 0, 누락 Test class 0, 직접 `lib.*` import의 header depends 누락 0
- 플랫폼 분기 격리: 추가된 provider/cmux/playwright 서술과 분기는 E2E contract 설정 또는 `e2e_adapter.py` adapter 경계 안이며, 새 핵심 계층 플랫폼 분기 finding 없음
- 수기 이력 diff: 6개 잔존 절 모두 HEAD 기원. `GC-009`의 initial 변경 행은 최신 diff에서 제거됨
- 호출자가 제공한 전체 source suite 78 tests pass는 재실행하거나 재판정하지 않음

## 6. 검사 범위

### checked_files (입력과 완전 일치)

1. `opal/agents/opal-loop-action-agent/AGENT.md`
2. `opal/agents/opal-task-action-agent/AGENT.md`
3. `opal/agents/opal-test-agent/AGENT.md`
4. `opal/core/references/test-tools-schema.yaml`
5. `opal/core/references/tools.md`
6. `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
7. `opal/skills/opal-pilot-dev-short/SKILL.md`
8. `opal/skills/opal-pilot-dev/SKILL.md`
9. `opal/skills/opal-pilot-project-dev/SKILL.md`
10. `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
11. `opal/skills/opal-pilot-project-loop/SKILL.md`
12. `opal/skills/opal-pilot-project-loop/references/journey-flow.md`
13. `opal/skills/opal-pilot-project-loop/references/verification.md`
14. `opal/templates/test-tools.yaml`
15. `opal/tools/test-tool/README.md`
16. `opal/tools/test-tool/lib/e2e_adapter.py`
17. `opal/tools/test-tool/lib/e2e_contract.py`
18. `opal/tools/test-tool/lib/resolver.py`
19. `opal/tools/test-tool/lib/scenario.py`
20. `opal/tools/test-tool/schema/test-scenario.schema.json`
21. `opal/tools/test-tool/test_tool.py`
22. `opal/tools/test-tool/tests/test_e2e_contract.py`
23. `opal/tools/test-tool/tests/test_scenario.py`
24. `opal/tools/test-tool/tests/test_test_tool.py`

### 결측·블로커

- missing_capabilities: 없음
- blockers: 없음
- 이번 실행 changed_files: 이 보고서와 동명 JSON 2개만 생성. source/test/docs는 수정하지 않음
