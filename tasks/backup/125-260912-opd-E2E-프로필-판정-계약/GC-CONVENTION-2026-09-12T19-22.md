# GC CONVENTION REPORT — 2026-09-12T19-22

## 1. 헤더

- 실행 일시: 시작 2026-09-12 19:24 / 완료 2026-09-12 19:29 / 소요 5분
- 범위: `all` / 대상 파일 24개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 및 그 포인터인 `header-standard.md`, `opal-doc-standard.md`
- baseline: `none` — 현재 finding 18건 전부 `new`
- APPLY 수행 여부: N (read-only 진단)
- 검사 실행 상태: `pass` — 24/24 파일 검사, missing capability 없음
- 규약 판정: **FAIL** — blocking finding 16건

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 18 |
| 심각도 분포 | Critical 0 / High 1 / Medium 6 / Low 9 / Info 2 |
| 집행 수준 | Blocking 16 / Advisory 0 / Informational 2 |
| 자동 수정 가능 | 14 |
| 수동 조치 필요 | 4 |
| 파일별 상위 Top 5 | `opal-pilot-dev/SKILL.md` (2) / `test_e2e_contract.py` (2) / `test_test_tool.py` (2) / 그 외 12개 파일 (각 1) |
| 카테고리별 빈도 | 문서/헤더 메타데이터 8 / 수기 이력 6 / 플랫폼 분기 격리 2 / frontmatter 2 |
| Critical/High 수 | 1 |
| 문서 업데이트 제안 수 | 0 — 필요한 규칙은 이미 T0 문서에 존재 |

독립 정적 관측은 모두 실행 가능했다. Python 8개 구문 컴파일, YAML 2개와 AGENT/SKILL frontmatter 7개 파싱, JSON schema 파싱 및 Draft-07 meta-schema 검증은 통과했다. `code-scan target`은 Python 8개 모두 `write_to=inline`, `reason=header_source_inline`을 반환했으며, 신규 `e2e_contract.py`에도 정상 인라인 헤더가 존재한다. 호출자가 제공한 전체 source suite `78 tests pass`는 재실행하거나 재판정하지 않았다.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (1건)

- [ ] GC-001 [`opal/agents/opal-loop-action-agent/AGENT.md:55`] 핵심 에이전트가 Claude 전용 디스패치 분기를 소유함
  - 카테고리: 플랫폼 분기 격리
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §플랫폼 분기 격리), T0/blocking
  - 설명: 본문이 claude headless 채널, `--provider claude`, claude 컬럼 모델 치환, claude 전용 출력·session-id/resume, provider별 가용성 표를 직접 소유한다(55, 78, 93, 118, 194-195, 211-214, 271-275, 298-306).
  - 영향: 어댑터 밖 핵심 로직이 플랫폼에 결합되어 다른 플랫폼에서 동일 행동 계약을 보장할 수 없다.
  - 해결 방안: provider 선택·모델 치환·세션·출력 파싱·가용성 분기를 `opal-agent` 어댑터로 옮기고 AGENT 본문은 provider-neutral 계약만 유지한다.
  - 검증: AGENT 본문에 provider별 조건이나 플랫폼 고정 토큰이 남지 않고 어댑터만 분기를 소유하는지 확인한다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §플랫폼 분기 격리

### Medium (6건)

- [ ] GC-002 [`opal/skills/opal-pilot-dev/SKILL.md:81`] 공통 Dev 스킬이 `CLAUDE.md` 폴백을 고정함
  - 카테고리: 플랫폼 분기 격리
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §플랫폼 분기 격리), T0/blocking
  - 설명: ANALYSIS/PLAN/EXECUTE 템플릿의 프로젝트 컨텍스트 폴백이 `CLAUDE.md`로 고정되어 있다(81, 110, 188).
  - 해결 방안: 플랫폼 중립 문서 선택 계약을 사용하고 플랫폼 파일명 매핑은 부트스트래퍼/어댑터에 둔다.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §플랫폼 분기 격리

- [ ] GC-003 [`opal/skills/opal-pilot-dev-short/SKILL.md:1`] 스킬 frontmatter에 `triggers`와 `version`이 없음
  - 카테고리: 문서화/frontmatter
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter), T0/blocking
  - 설명: YAML은 정상 파싱되지만 `name`, `description`만 존재한다(1-9).
  - 해결 방안: 현재 라우팅 계약에 맞는 `triggers`와 소비되는 `version`을 추가한다.
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter

- [ ] GC-004 [`opal/skills/opal-pilot-dev/SKILL.md:1`] canonical Dev 스킬 frontmatter에 `triggers`와 `version`이 없음
  - 카테고리: 문서화/frontmatter
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter), T0/blocking
  - 설명: YAML은 정상 파싱되지만 `name`, `description`만 존재한다(1-7).
  - 해결 방안: opd/opds 라우팅을 나타내는 `triggers`와 소비되는 `version`을 추가한다.
  - 자동 수정: Y
  - 참조: `docs/CONVENTIONS.md` §파일 구조 > YAML Frontmatter

- [ ] GC-016 [`opal/tools/test-tool/tests/test_scenario.py:9`] 테스트 헤더와 RED 설명이 현재 파일과 불일치함
  - 카테고리: @header 메타데이터 drift
  - 위반 기준: 프로젝트(`header-standard.md` §2.1, §4.1), T0/blocking
  - 설명: `exports`가 현재 coverage-build 및 T125 V2 클래스 4개(1219, 1262, 1311, 1389)를 누락하고, 본문 여러 곳(31-43, 478, 647)은 이미 구현된 기능을 미구현/자연 RED라고 서술한다.
  - 해결 방안: 헤더의 exports/scenarios를 현재 테스트 집합에 맞추고 과거 RED 설명을 현재 회귀 보호 설명으로 교체한다.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §2.1, §4.1

- [ ] GC-017 [`opal/tools/test-tool/tests/test_test_tool.py:7`] 헤더가 전체 테스트를 미구현·FAIL 예상으로 서술함
  - 카테고리: @header 메타데이터 drift
  - 위반 기준: 프로젝트(`header-standard.md` §2.1), T0/blocking
  - 설명: header와 본문은 전부 RED 실패 예정이라고 서술하지만(7, 398, 894), 호출자 제공 증거는 전체 source suite 78 tests pass다. 수기 이력도 본문에 남아 있다(21-27).
  - 해결 방안: 과거 RED/미구현 설명을 현재 회귀 테스트 역할로 교체하고 이력은 git/tasks에 맡긴다.
  - 자동 수정: N
  - 참조: `opal/core/references/header-standard.md` §2.1

- [ ] GC-018 [`opal/tools/test-tool/tests/test_e2e_contract.py:22`] 신규 계약 테스트 docstring이 production owner 부재·전부 RED라고 서술함
  - 카테고리: stale documentation
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §3), T0/blocking
  - 설명: `lib/e2e_contract.py`가 현재 존재하고 호출자 제공 증거가 78 tests pass인데도 22-24행은 반대 상태를 현재형으로 기록한다.
  - 해결 방안: 도입 당시 RED 설명을 제거하고 현재 E2E contract 회귀 보호 역할로 교체한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §3

### Low (9건)

- [ ] GC-005 [`opal/core/references/tools.md:1157`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: 실행 reference 문서가 이력 SSOT를 git/tasks와 중복한다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-006 [`opal/skills/op-dev-test-scenario/references/test-scenario-guide.md:92`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: 실행 guide가 이력 SSOT를 git/tasks와 중복한다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-007 [`opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:582`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: 실행 guide가 이력 SSOT를 git/tasks와 중복한다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-008 [`opal/skills/opal-pilot-project-loop/references/journey-flow.md:103`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: reference 문서가 이력 SSOT를 git/tasks와 중복한다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-009 [`opal/skills/opal-pilot-project-loop/references/verification.md:201`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: reference 문서가 이력 SSOT를 중복하며 이번 변경도 기존 이력 행을 갱신했다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-010 [`opal/tools/test-tool/README.md:439`] 수기 누적 `## 변경이력` 절
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal-doc-standard.md` §5), T0/blocking
  - 설명: 도구 README가 이력 SSOT를 git/tasks와 중복한다.
  - 해결 방안: 변경이력 절 전체를 제거한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/opal-doc-standard.md` §5

- [ ] GC-013 [`opal/tools/test-tool/lib/e2e_adapter.py:10`] `@header.depends`가 신규 공통 계약 import를 누락함
  - 카테고리: @header 메타데이터 drift
  - 위반 기준: 프로젝트(`header-standard.md` §2 depends), T0/blocking
  - 설명: 헤더는 cmux-tool만 선언하지만 `lib.e2e_contract`를 직접 import한다(31).
  - 해결 방안: 현재 모듈 의존성을 depends에 추가한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/header-standard.md` §2, §4.2

- [ ] GC-014 [`opal/tools/test-tool/lib/scenario.py:23`] `@header.depends: []`가 신규 공통 계약 import와 모순됨
  - 카테고리: @header 메타데이터 drift
  - 위반 기준: 프로젝트(`header-standard.md` §2 depends), T0/blocking
  - 설명: 코드가 `lib.e2e_contract`의 9개 심볼을 import한다(80-89).
  - 해결 방안: 현재 모듈 의존성을 depends에 추가한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/header-standard.md` §2, §4.2

- [ ] GC-015 [`opal/tools/test-tool/test_tool.py:6`] CLI 헤더 설명·의존 목록이 현재 라우팅을 누락함
  - 카테고리: @header 메타데이터 drift
  - 위반 기준: 프로젝트(`header-standard.md` §2 description/depends), T0/blocking
  - 설명: description은 4서브명령만 기술하고 depends는 직접 import하는 `lib.e2e_contract`, `lib.scenario`를 누락한다(40-41).
  - 해결 방안: 4개 기본 명령과 scenario-* 라우팅을 현재 역할로 기술하고 두 의존성을 반영한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/header-standard.md` §2, §4.2

### Info (2건)

- [ ] GC-011 [`opal/tools/test-tool/tests/test_e2e_contract.py:9`] 표준 밖 `@header.track` 필드
  - 카테고리: @header 미선언 필드
  - 위반 기준: 실행 설정(`code-scan validate`의 `header_history/undeclared_field`), T0/informational
  - 설명: 도구가 해당 경고를 반환했지만 전체 validate는 `ok=true`였다. 도구 판정을 비차단으로 그대로 보존했다.
  - 해결 방안: 소비자가 없으면 제거하고, 실제 계약이면 표준 소유 절차로 명시한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/header-standard.md` §2

- [ ] GC-012 [`opal/tools/test-tool/tests/test_test_tool.py:9`] 표준 밖 `@header.track` 필드
  - 카테고리: @header 미선언 필드
  - 위반 기준: 실행 설정(`code-scan validate`의 `header_history/undeclared_field`), T0/informational
  - 설명: 도구가 해당 경고를 반환했지만 전체 validate는 `ok=true`였다. 도구 판정을 비차단으로 그대로 보존했다.
  - 해결 방안: 소비자가 없으면 제거하고, 실제 계약이면 표준 소유 절차로 명시한다.
  - 자동 수정: Y
  - 참조: `opal/core/references/header-standard.md` §2

---

## 4. 문서 업데이트 제안

동일 fingerprint `0d65ac1342cb42bc`의 수기 이력 위반이 3개 파일에서 관측되어 빈도 트리거는 발생했다. 그러나 금지 규칙이 이미 `docs/CONVENTIONS.md`의 포인터와 `opal-doc-standard.md` §5에 존재하므로 중복 규칙 추가를 제안하지 않는다. 이번 결과는 규칙 문서 갱신이 아니라 기존 규칙 적용 대상으로 분류한다.

새 카테고리 트리거는 없다. 플랫폼 격리, frontmatter, 문서 이력, header 현재 사실 규칙 모두 기존 T0 기준에 포함된다.

---

## 5. 검사 범위와 증거

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

### 활성 카테고리

- 네이밍/파일 구조: 대상 경로 및 파일명 규약, AGENT/SKILL frontmatter
- 들여쓰기/파일 형식: diff whitespace, EOF LF, YAML/JSON/Python 파싱
- 문서화: 수기 이력, 현재 사실, @header 필드·기록 위치·레이어·의존성
- 플랫폼/배포 경계: 핵심 로직의 플랫폼 분기 및 `~/.opal` 직접 수정 지시 여부

### 비활성 카테고리

- 죽은 코드, 미사용 import, import 정렬, 일반 코드 품질: 프로젝트 T0 formatter/linter 설정이 없고 이번 검사에 해당 규칙을 강제하는 설정도 없어 위반으로 생성하지 않았다.
- 보안: 별도 security checker 관할이다.

### 실행 증거

- `event-loader verify --event worker.dispatch`: `ok=true`, 문서 4개 검증
- 대상 검증: 24/24 존재, 24/24 `project_root` 내부
- `git diff --check`: 출력 없음
- Python 8개 `py_compile`: pass (`PYTHONPYCACHEPREFIX`는 `/tmp` 사용)
- PyYAML 6.0.3: AGENT/SKILL frontmatter 7개, YAML 대상 2개 parse pass
- JSON parse 및 `Draft7Validator.check_schema`: pass
- `code-scan target`: Python 8개 모두 `inline/header_source_inline`
- `code-scan validate --json`: `ok=true`, `exports_not_found=0`, 대상 파일 경고 2건은 `header_history/undeclared_field`
- 호출자 제공 source suite: 78 tests pass — 재실행·재분류하지 않음

### 결측·블로커

- missing_capabilities: 없음
- blockers: 없음
- 검사 실행 자체는 완전하며, blocking finding 16건 때문에 규약 판정만 FAIL이다.
