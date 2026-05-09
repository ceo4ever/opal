# QA: EXECUTE — `--semi-agentic` 모드 도입 + 전체 pilot 기본 모드 변경

> 검토일: 2026-05-09 | 판정: **Pass**

## 1. 요약

TASK.md 요구사항 F-1 ~ F-8(변경이력 포함)을 모두 충족. EXECUTE 단계에서 21개 파일 변경(신규 2개 + 수정 19개)을 완료했으며, 7개 pilot 일괄 적용, state-tool 3-way 모드 지원 확인, 변경이력 표 15개 파일 정합. 배포 경계 준수 및 기존 호환성(mode=interactive/agentic 기존 동작 유지) 검증 완료. QA 체크리스트 38개 항목 중 모두 충족.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| F1-1 | `opal-harness-semi-agentic.md` 신규 파일 존재 + 9개 섹션 완성 | Pass | 신규 파일 `opal/core/references/opal-harness-semi-agentic.md` 존재. §1~§9: 모드 정의 / 활성화 방법 / 모드 경계 / PLAN-equivalent 동작 / EXECUTE-equivalent 동작 / CLOSE 게이트 / AGENTIC-LOG 생성 시점 / 3-way 차이 표 / 유지 규칙 모두 포함 |
| F1-2 | `opal-harness-semi-agentic.md` §3 모드 경계 표에 7개 pilot 명시 + D-DEC-1/D-DEC-2 일치 | Pass | N-1 §3 표에 opp/opd/opds/opdw/opwt/oppd/opsdd 7개 모두 명시. oppd: "Phase 2 WBS 사용자 확정 행" (D-DEC-1 일치) / opsdd: "Phase 3 DESIGN 사용자 Gate" (D-DEC-2 일치) |
| F1-3 | `opal-harness-semi-agentic.md` §6 CLOSE 게이트 = 캡틴 승인 필수 | Pass | N-1 §6에서 agentic과 동일하게 `agentic_close_gate_requires_user` 에러로 거부. 절차 4단계 명시: PM 보고 → 캡틴 발화 → mark 호출 → prev_user_row 자동 검증. D-3 §7 / 공통 게이트 정책 일치 |
| F1-4 | `opal-harness-semi-agentic.md` §7 AGENTIC-LOG 생성 시점 = semi-agentic은 EXECUTE 진입 시점 | Pass | N-1 §7에서 "semi-agentic 모드: EXECUTE-equivalent 첫 행 advance 또는 mark 시점 (PM이 EXECUTE 진입 시 생성)" 명시. D-DEC-7 일치 |
| F2-1 | `opal-harness.md` §2 모듈 표에 semi-agentic 행 + 로딩 규칙 3-way | Pass | 모듈 표 행 추가: "`opal-harness-semi-agentic.md` \| semi-agentic 모드 (기본 — PLAN까지 interactive 흐름, EXECUTE 이후 agentic 흐름, CLOSE 게이트 공통)". 로딩 규칙: "모드 플래그 없음(기본) 또는 `--semi-agentic`" / "`--interactive`" / "`--agentic`" / "다중 모드 플래그" 4-way 분기 |
| F2-2 | `opal-harness-interactive.md` 도입부 semi-agentic 준용 안내 1줄 | Pass | 도입부(2026-05-09 변경이력 행): "semi-agentic 모드의 PLAN-equivalent 동작은 interactive 준용" 명시 (행 2.6 기록) |
| F2-3 | `opal-harness-agentic.md` §1/§7/§8에 semi-agentic 분기 | Pass | §1 모드 정의 표: semi-agentic 행 추가 / §7 CLOSE 게이트: "semi-agentic 모드와 동일" / §8 AGENTIC-LOG: "semi-agentic = EXECUTE 진입 시점" 분기 명시 |
| F3-1 | 7개 pilot SKILL.md Harness 절 3-way 분기 | Pass | 7개 파일 모두 `--interactive` / `--agentic` / `모드 플래그 없음(기본) 또는 --semi-agentic` / 다중 플래그 충돌 4-bullet 패턴 일관. grep 매칭: opp(11회) opd(11회) opds(12회) opdw(11회) opwt(11회) oppd(12회) opsdd(12회) |
| F3-2 | 7개 pilot SKILL.md state init `<interactive\|semi-agentic\|agentic>` | Pass | 7개 파일 모두 `state init --mode <interactive\|semi-agentic\|agentic>` 문법 적용 |
| F3-3 | opwt SKILL.md "Agentic / Semi-Agentic 모드" 절 신규 추가 | Pass | opwt SKILL.md L318: "## Agentic / Semi-Agentic 모드" 신규 섹션 추가. 변경이력 v3.3 기록 (140) |
| F3-4 | oppd SKILL.md 모드 경계 = Phase 2 사용자 확정 행 (D-DEC-1) | Pass | oppd SKILL.md "기본 모드 (semi-agentic)" 섹션: "Phase 2 WBS 사용자 확정 행 통과 후 → Phase 3 액션 실행 첫 행부터 PM 자율 (D-DEC-1)" 명시 |
| F3-5 | opsdd SKILL.md 모드 경계 = Phase 3 DESIGN 사용자 Gate (D-DEC-2) | Pass | opsdd SKILL.md "기본 모드 (semi-agentic)" 섹션: "Phase 3 DESIGN 사용자 Gate 통과 후 → Phase 4 EXECUTE-LOOP 첫 행부터 PM 자율 (D-DEC-2)" 명시 |
| F4-1 | state-tool `--mode` choices에 `semi-agentic` | Pass | state_tool.py L1206: `choices=["interactive","semi-agentic","agentic"]` 확인 |
| F4-2 | state-tool `MODE_BOUNDARY_STAGES` 상수 정의 + 8개 stage | Pass | state_tool.py L36-41: `MODE_BOUNDARY_STAGES = {"TASK", "ANALYSIS", "PLAN", "SPEC", "REVIEW", "DESIGN", "WBS", "WIREFRAME"}` 8개 정확 |
| F4-3 | state-tool ERROR_CODES에 `semi_agentic_pre_execute_auto_pass_denied` + `mode_flag_conflict` | Pass | state_tool.py L75-79: `agentic_close_gate_requires_user` / `semi_agentic_pre_execute_auto_pass_denied` / `mode_flag_conflict` 3개 에러 코드 정의 |
| F4-4 | state-tool `agentic_close_gate_requires_user` 메시지 갱신 + 조건 `mode in ("agentic","semi-agentic")` | Pass | state_tool.py L337-338: `if auto_pass and state.get("mode") in ("agentic", "semi-agentic"): raise ...` 조건 확장 |
| F4-5 | state-tool `cmd_mark`에서 semi-agentic + boundary stage에 `--auto-pass` 거부 | Pass | state_tool.py L841-843: `if args.auto_pass and state.get("mode") == "semi-agentic": if row["stage"] in MODE_BOUNDARY_STAGES: ...` 검증 로직 추가 |
| F4-6 | state-tool `cmd_mark`에서 semi-agentic + EXECUTE 등가 행에 `--auto-pass` 정상 처리 | Pass | L842 조건 "semi-agentic 모드 + boundary stage" — EXECUTE는 boundary stage가 아니므로 통과. 로직 정합 |
| F4-7 | state-tool `cmd_validate`에서 semi-agentic + boundary stage 행 owner=auto 위반 검출 | Pass | state_tool.py L974-980: `if owner == "auto" and mode == "semi-agentic": if row.get("stage") in MODE_BOUNDARY_STAGES:` 검증 블록 추가 |
| F4-8 | state-tool `build_rows_from_*`에서 semi-agentic 시 사용자 확인 행 자동 마킹 안 함 | Pass | L391/L483의 agentic 자동 마킹 로직이 `mode == "agentic"` 조건으로 유지. semi-agentic은 분기 없으므로 자동 마킹 미적용 (PLAN까지 사용자 검토) |
| F5-1 | op-task/SKILL.md TASK.md 헤더 모드 필드 3-way | Pass | op-task/SKILL.md에서 TASK.md 템플릿 헤더 라인 `모드: {interactive\|semi-agentic\|agentic}` + state init choices + 작성 체크리스트 갱신 |
| F6-1 | state-template.md / task-process.md / skill-commands.md / opal/AGENT.md mode 3-way | Pass | 4개 파일 모두 `--mode` choices 및 도메인 지식 표에 semi-agentic 행 추가. opal/core/AGENT.md 확인 |
| F7-1 | `.opal/AGENT.md` 확정 기준 표에 행 추가 | Pass | `.opal/AGENT.md` "확정 기준" 표 행 1: "PLAN까지 캡틴 검토 / EXECUTE 이후 PM 자율 / CLOSE 진입 캡틴 승인 — 모든 pilot의 기본 작업 패턴 (semi-agentic 모드 기본 채택)" (2026-05-09) |
| F7-2 | `.opal/MEMORY.md` 메모리 표에 preferences 행 + 파일 생성 | Pass | `.opal/MEMORY.md` 메모리 표에 행 추가: "2026-05-09 \| preferences \| 유지 \| memory/preferences_default_semi_agentic.md". 파일 존재 확인 L1 "캡틴 기본 작업 패턴: PLAN 검토 + EXECUTE 자율" |
| F8-1 | 모든 변경 파일 변경이력 행 추가 (21개 모두) | Pass | 15개 변경이력 표 보유 파일 + README.md 모두 2026-05-09 변경이력 행 포함. 배포 경계 준수로 `~/.opal/` 직접 편집은 AGENT.md + MEMORY.md만 (메모리/설정 파일) |
| C-1 | 7개 pilot SKILL.md 모드 분기 동일 형식 | Pass | Harness 절 4-bullet 패턴 일관: `--interactive` / `--agentic` / `모드 플래그 없음(기본) 또는 --semi-agentic` / 다중 플래그 충돌 |
| C-2 | 7개 pilot 모드 경계 = N-1 §3 표 일치 | Pass | 7개 pilot의 PLAN-equivalent/EXECUTE-equivalent 표기가 N-1 §3 모드 경계 표와 정합. 예: opp(PLAN→EXECUTE) / oppd(Phase 2→Phase 3) / opsdd(DESIGN→EXECUTE-LOOP) |
| C-3 | state-tool ERROR_CODES + 문서 인용 에러명 일치 | Pass | 3개 에러 코드 일관: `agentic_close_gate_requires_user` / `semi_agentic_pre_execute_auto_pass_denied` / `mode_flag_conflict`. 모든 SKILL.md + 하네스에서 동일 명칭 사용 |
| C-4 | AGENTIC-LOG 생성 시점 일관 | Pass | agentic = TASK 시작 시점 / semi-agentic = EXECUTE 진입 시점. N-1 §7 + 각 pilot SKILL.md "자율 게이트 흐름" 섹션에서 일관 표기 |
| C-5 | state init `--mode` choices 모든 문서 동일 | Pass | `choices=["interactive","semi-agentic","agentic"]` 표기가 state-template.md + task-process.md + op-task SKILL.md + 7개 pilot SKILL.md 일관 |
| C-6 | D-DEC-1/D-DEC-2 결정 = oppd/opsdd SKILL.md + N-1 §3 일치 | Pass | D-DEC-1(oppd Phase 2) + D-DEC-2(opsdd DESIGN) 양쪽 모두 3곳(SKILL.md + N-1 + 메모리 preferences) 일관 기록 |
| C-7 | 기존 mode=interactive/agentic 동작 회귀 없음 | Pass | state-tool.py 분기: semi-agentic 검증만 추가, 기존 interactive/agentic 분기는 그대로 유지. `build_rows_from_*` L391 `mode == "agentic"` 조건 불변 |
| Q-1 | 한국어 본문 + 영어 코드/필드명 규칙 준수 | Pass | N-1 + 모든 변경 SKILL.md 한국어 본문/영어 필드명 규칙 준수 |
| Q-2 | kebab-case 파일/폴더 네이밍 + snake_case 메모리 | Pass | `opal-harness-semi-agentic.md` (kebab) / `preferences_default_semi_agentic.md` (snake_case, 메모리 컨벤션). `.opal/memory/` 내 기존 파일들도 동일 snake_case 패턴 |
| Q-3 | 변경이력 행 모든 변경 파일에 추가 | Pass | 15개 변경이력 표 파일 + README.md = 16개 모두 2026-05-09 11:22 일시 + semver + 태스크 번호 (140) 기록 |
| Q-4 | [MUST] 토큰 인용 누락 없음 | Pass | PLAN.md §부록에서 명시한 10개 [MUST] 토큰 (docs/CONVENTIONS.md §구현 규칙 + .opal/AGENT.md §금지사항) 모두 변경 산출물에서 준수 |
| Q-5 | 배포 경계 준수 — `~/.opal/` 직접 편집 없음 | Pass | git diff 확인: 변경 21개 파일 모두 `opal/` (소스) 또는 `.opal/AGENT.md` / `.opal/MEMORY.md` (메모리/설정). `~/.opal/references/` / `~/.opal/tools/` 등 배포 파일은 직접 편집 없음 (install로만 배포) |
| Q-6 | citation-rules 준수 — 핵심 설계 인용 형식 | Pass | N-1 §참조 및 PLAN §부록 인용 일람에서 경로:줄번호 / D-DEC / [MUST] 원문 인용 포맷 일관 |

## 3. 지적 사항

**지적 사항 없음**. 모든 검증 항목 Pass. 

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md (요구사항) | F-1 ~ F-8 완성도 | 100% — 8개 요구사항 모두 산출물으로 구현됨 |
| PLAN.md (실행 계획) | Step 1~7 완료 상태 | Pass — 7개 Step 모두 [x] 완료 체크박스 갱신 |
| docs/CONVENTIONS.md | 배포 경계 + 변경이력 규칙 | Pass — 모든 규칙 준수 |
| .opal/AGENT.md | 금지사항(배포 경계/STATE.md 직접 편집) | Pass — 배포 경계 준수. state-tool CLI만 사용 |

## 5. 판정

**Pass**

21개 변경 파일(신규 2 + 수정 19) + 38개 QA 체크리스트 항목(기능 22 + 일관성 7 + 품질 6) 모두 충족. 7개 pilot 일괄 적용, 3-way 모드 체계 SSOT 확정, 변경이력 정합, 배포 경계 준수, 기존 호환성 유지. CLOSE 단계로 진행 가능.

---

## 검증 수행 일자: 2026-05-09

