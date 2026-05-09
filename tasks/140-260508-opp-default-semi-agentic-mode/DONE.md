# DONE: --semi-agentic 모드 도입 + 전체 pilot 기본 모드 변경 (140)

- 시작: 2026-05-08 23:51
- 완료: 2026-05-09 12:16
- 본 태스크 모드: `interactive` (메타 작업 안전성 우선)
- 도입 모드: `semi-agentic` (3-way 모드 체계 신규 기본)

## 작업 목표 (TASK.md 인용)

OPAL 하네스에 세 번째 모드 `semi-agentic`을 신설하고 전체 pilot 7종(opp/opd/opds/opdw/oppd/opsdd/opwt)의 기본 모드로 채택. PLAN-equivalent까지는 사용자 검토(interactive 동작), EXECUTE-equivalent 진입 후부터 PM 자율 통과(agentic 동작), CLOSE 진입은 사용자 승인 필수(공통 게이트). 기존 interactive 동작은 `--interactive` 플래그로 명시 호출 가능.

## 핵심 결정 사항 (D-DEC-1 ~ D-DEC-7)

| # | 항목 | 채택안 |
|---|------|-------|
| **D-DEC-1** | oppd Phase 경계 | **Phase 2 WBS 사용자 확정 행** = 모드 경계. Phase 3 액션 실행은 자율 |
| **D-DEC-2** | opsdd Phase 경계 | **Phase 3 DESIGN 사용자 Gate** = 모드 경계. EXECUTE-LOOP/VERIFY는 자율 |
| **D-DEC-3** | 하네스 파일 구조 | `opal-harness-semi-agentic.md` **신규 파일 신설** (모듈 표 행 추가) |
| **D-DEC-4** | 호환성 | 기존 진행 중 태스크는 mode 그대로 유지 (소급 변경 없음) |
| **D-DEC-5** | state-tool 식별 로직 | `MODE_BOUNDARY_STAGES`(8 stage) 상수 기반 stage 필드 직접 판별 + 신규 에러 `semi_agentic_pre_execute_auto_pass_denied` |
| **D-DEC-5b** | CLOSE 게이트 명명 | 기존 `agentic_close_gate_requires_user` 코드 유지 + 메시지 텍스트 갱신 + 조건 `mode in ("agentic","semi-agentic")` 확장 |
| **D-DEC-6** | 플래그 체계 | `--interactive` / `--semi-agentic`(기본) / `--agentic` 3-way + 다중 플래그 충돌은 `mode_flag_conflict` 에러 |
| **D-DEC-7** | AGENTIC-LOG 시점 | agentic = TASK 시작 / **semi-agentic = EXECUTE-equivalent 첫 행 advance 시점** |

## 변경 문서 목록 (총 25개 변경)

### 신규 (3개)

| 파일 | 역할 |
|------|------|
| `opal/core/references/opal-harness-semi-agentic.md` | semi-agentic 모드 SSOT (9개 섹션 — 모드 정의 / 활성화 / 모드 경계 7 pilot / PLAN까지 동작 / EXECUTE 이후 동작 / CLOSE 게이트 / AGENTIC-LOG 시점 / 차이 표 / 유지 규칙) |
| `.opal/memory/preferences_default_semi_agentic.md` | 캡틴 작업 패턴 메모리 — semi-agentic 기본 채택 근거 + D-DEC-1~D-DEC-7 링크 |
| `tasks/140-260508-opp-default-semi-agentic-mode/` | 태스크 산출물 (TASK / PLAN / QA-PLAN / QA-EXECUTE / GC-CONVENTION / DONE / STATE / state.json) |

### 수정 — 하네스 (3개)

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-harness.md` | §2 모듈 구조 표에 semi-agentic 행 + 로딩 규칙 3-way 갱신 (v4.7) |
| `opal/core/references/opal-harness-interactive.md` | 도입부에 semi-agentic 준용 안내 1줄 (v2.6) |
| `opal/core/references/opal-harness-agentic.md` | §1 모드 정의 표 + §7 CLOSE 게이트 + §8 AGENTIC-LOG 시점 분기 (v1.6) |

### 수정 — 부트스트랩/공통 참조 (4개)

| 파일 | 변경 |
|------|------|
| `opal/core/references/harness/state-template.md` | `--mode` choices 3-way + 기본값 안내 + 모드 필드 값 안내 (v1.3) + GC-C002 헤더 형식 보정 (날짜→일시) |
| `opal/core/references/harness/task-process.md` | 4번 항목 모드 필드 3-way 갱신 + state init choices 3-way (v1.2) + GC-C002 헤더 형식 보정 (날짜→일시 / 내용→변경내용) |
| `opal/core/references/harness/skill-commands.md` | 쌍슬래시 커맨드 예시에 `--interactive` / `--agentic` 추가 |
| `opal/core/AGENT.md` | 도메인 지식 표 Agentic Mode 행 3-way 모드 설명 (v2.2) + GC-C001 헤더 형식 보정 (날짜→일시 / 내용→변경내용) |

### 수정 — op-task / pilot 7종 (8개)

| 파일 | 변경 |
|------|------|
| `opal/skills/op-task/SKILL.md` | TASK.md 헤더 모드 필드 3-way + state init choices + 작성 체크리스트 갱신 |
| `opal/skills/opal-pilot-project/SKILL.md` (opp) | Harness 절 3-way + Agentic / Semi-Agentic 모드 절 확장 (v2.9) |
| `opal/skills/opal-pilot-dev/SKILL.md` (opd) | 동일 패턴 (Full Task: TASK→ANALYSIS→PLAN→EXECUTE→TEST→CLOSE) |
| `opal/skills/opal-pilot-dev-short/SKILL.md` (opds) | 동일 패턴 (Short Task) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` (opdw) | 동일 패턴 (WIREFRAME = PLAN-equivalent) |
| `opal/skills/opal-pilot-write-tech/SKILL.md` (opwt) | Agentic / Semi-Agentic 모드 절 신규 추가 (이전엔 미존재) |
| `opal/skills/opal-pilot-project-dev/SKILL.md` (oppd) | Phase 2 WBS 사용자 확정 행 = 모드 경계 명시 (D-DEC-1) |
| `opal/skills/opal-pilot-sdd/SKILL.md` (opsdd) | Phase 3 DESIGN 사용자 Gate = 모드 경계 명시 (D-DEC-2) |

### 수정 — state-tool (2개)

| 파일 | 변경 |
|------|------|
| `opal/tools/state-tool/state_tool.py` | (a) `--mode` choices에 `semi-agentic` 추가 (b) `MODE_BOUNDARY_STAGES` 상수 신설 (8 stage) (c) `cmd_mark`에 `semi_agentic_pre_execute_auto_pass_denied` 검증 추가 (d) `check_close_gate` 조건 `mode in ("agentic","semi-agentic")` 확장 (e) ERROR_CODES에 신규 2종 + 기존 1종 메시지 갱신 (f) `cmd_validate`에 semi-agentic 모드 검증 (g) @header description "3-way 모드 지원" 추가 |
| `opal/tools/state-tool/README.md` | mode choices 3-way + 신규 에러 카탈로그 |

### 수정 — 메모리/설정 (2개)

| 파일 | 변경 |
|------|------|
| `.opal/AGENT.md` | 도메인 지식 표 Agentic Mode 행 갱신 + 확정 기준 표 행 추가 ("PLAN까지 캡틴 검토 / EXECUTE 이후 PM 자율 / CLOSE 진입 캡틴 승인 — 모든 pilot의 기본 작업 패턴") |
| `.opal/MEMORY.md` | 메모리 표에 preferences 행 추가 + 작업 히스토리 행 추가 |

### Step 9 보정 — docs (1개)

| 파일 | 변경 |
|------|------|
| `docs/CONVENTIONS.md` | 161줄 — `(agentic 모드에서도 유지)` → `(agentic/semi-agentic 모드에서도 유지)` 보정. PLAN §3 Step 9 docs 검토 시 발견된 잔여 보정 |

## 검증 결과

### QA Gate (PLAN + EXECUTE)

- **QA-PLAN.md**: 14개 검증 항목 모두 Pass (요구사항 커버 / 의존 순서 / Citation Rules / Guards / 변경이력 / 배포 경계 / state-tool SSOT / Step별 완성도 / 모드 경계 / 롤백 전략 / 모드 분리)
- **QA-EXECUTE.md**: 38개 검증 항목 모두 Pass (기능 22 / 일관성 7 / 품질 6 / 교차 참조 4)

### EXECUTE PM Gate 컨벤션 자동 진단

`GC-CONVENTION-framework-2026-05-09T11-55-43.md` — Critical/High **0건** → PM Gate PASS. 발견된 후속 4건은 EXECUTE 후처리에서 모두 해결:

- **GC-C001 (Medium)** ✅ 처리: `opal/core/AGENT.md` 변경이력 헤더 `날짜/내용` → `일시/변경내용` 보정
- **GC-C002 (Medium)** ✅ 처리: `state-template.md` / `task-process.md` 헤더 동일 보정
- **GC-C003 (Low)** 미해당: `.opal/memory/`는 프로젝트 의존이라 install 대상 아님 (`install-mac.sh:689` opal_home은 사용자 ~/.opal/만 처리)
- **GC-C004 (Low)** 미해당: `header-rules.md`에 @header 변경이력 필드 미정의(옵션) + state-tool README.md에 변경이력 행 별도 보유

### Step 8 install + 6단계 동작 검증

| # | 검증 항목 | 결과 |
|---|----------|------|
| 1 | `./scripts/install-mac.sh` 메뉴 [1] OPAL 설치 | ✅ skills 30 + agents 13 + 부트스트래퍼 + 어댑터 + opal-cli 배포 |
| 2 | `~/.opal/references/opal-harness-semi-agentic.md` 배포 확인 | ✅ 4904 bytes, 헤더 정상 |
| 3 | `state-tool init --help` mode choices | ✅ `{interactive,semi-agentic,agentic}` |
| 4 | `state init --mode semi-agentic` 정상 동작 | ✅ rows_count: 20 |
| 5 | PLAN 행 (row 4, stage=PLAN) `--auto-pass` | ✅ `semi_agentic_pre_execute_auto_pass_denied` 거부 |
| 6 | EXECUTE 행 (row 12, stage=EXECUTE) `--auto-pass` | ✅ 정상 처리, owner=auto |
| 7 | CLOSE 첫 행 (row 19, stage=CLOSE) `--auto-pass` | ✅ `agentic_close_gate_requires_user` 거부 (메시지 갱신 확인) |

### state validate

`violations: 0` (PLAN State Gate / EXECUTE State Gate / CLOSE 진입 게이트 자동 검증 모두 통과)

## 모드 매트릭스 — 도입 후 최종 상태

| 호출 형식 | 결과 모드 |
|----------|---------|
| `//opp 작업` | `semi-agentic` (기본) |
| `//opp --semi-agentic 작업` | `semi-agentic` (명시) |
| `//opp --interactive 작업` | `interactive` (전 단계 사용자 검토) |
| `//opp --agentic 작업` | `agentic` (TASK부터 모두 자율) |
| `//opp --interactive --agentic 작업` | `mode_flag_conflict` 에러 |

## 모드 경계 표 (pilot 7종)

| pilot | PLAN-equivalent 종료 시점 | EXECUTE-equivalent 시작 시점 |
|-------|--------------------------|----------------------------|
| opp | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opd | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opds | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opdw | WIREFRAME 사용자 확인 행 | EXECUTE 작업 행 |
| opwt | PLAN(간략/진단보고) 사용자 확정 | EXECUTE 작업 행 |
| oppd | Phase 2 WBS 사용자 확정 행 (D-DEC-1) | Phase 3 액션 실행 첫 행 |
| opsdd | Phase 3 DESIGN 사용자 Gate (D-DEC-2) | Phase 4 EXECUTE-LOOP 첫 행 |

## 결함 및 회고

- **워커 보고 부정확**: EXECUTE 워커가 `summary`에 "Steps 5-7 완료"로 보고하고 `changed_files`에 12개만 적었으나 실제로는 Step 1~7 모든 21개 파일이 정상 변경됨. PM 검증(`git status` + grep 매칭)으로 실태 확인 후 진행. 워커가 보고 단계에서 컨텍스트가 압축되어 누락된 것으로 추정.
- **PLAN Step 9 docs 검토 사전 결론 부정확**: PLAN.md §3 Step 9에서 "docs/CONVENTIONS.md §구현 규칙에 모드 체계 직접 언급 없음, 변경 없음"이라고 결론지었으나 실제로는 161줄 1곳에 `(agentic 모드에서도 유지)` 표현이 있어 보정 필요. EXECUTE 후처리에서 발견하여 즉시 수정.
- **변경이력 헤더 표준 분산**: GC 컨벤션 체커가 발견한 헤더 형식(`날짜/내용` vs 표준 `일시/변경내용`) 분산은 본 태스크에서 변경한 3개 파일에서 보정. 그러나 다른 파일에도 동일 분산이 있을 가능성 — 후속 정리 후보.
- **install 비대화형 처리**: `install-mac.sh`가 메뉴 기반 대화형이라 비대화형 자동화에는 `printf "Y\n1\n0\n"` 입력 시퀀스 필요. 첫 입력은 detect_user의 confirm("Y/n"), 다음이 메뉴 선택, 마지막이 종료. 후속에 `--non-interactive` 옵션 또는 함수 직접 호출 진입점 도입 검토 가치.

## 후속 작업 후보 (별도 태스크 제안)

- **R-1**: 타 OPAL 문서들의 변경이력 헤더 형식 일제 정리 (날짜/내용 → 일시/변경내용 표준 통일)
- **R-2**: `install-mac.sh`에 `--non-interactive` / `--target {1|2|3|4}` CLI 옵션 추가 — CI/자동화/AI 에이전트가 install을 안전하게 자동 호출
- **R-3**: `opal-harness-semi-agentic.md`에 사용 사례 섹션 보강 — 실제 사용 후 패턴이 정착되면 가이드 추가

## 다음 단계

본 태스크 완료. **다음 OPAL 작업부터 `semi-agentic`이 기본 모드로 자동 적용**된다. 캡틴이 별도로 `--interactive` 또는 `--agentic`을 명시하지 않으면 모든 pilot이 PLAN-equivalent까지 검토 + EXECUTE-equivalent부터 자율 진행 + CLOSE 진입 캡틴 승인의 흐름을 따른다.
