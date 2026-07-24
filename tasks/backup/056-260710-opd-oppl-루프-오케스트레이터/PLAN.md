# PLAN: opal-pilot-project-loop(oppl) 루프 기반 오케스트레이터 신설

> 작성일: 2026-07-10 | 입력: TASK.md, ANALYSIS.md, SPEC.html(설계 확정 SSOT), REQUEST-DRAFT.md
> 모드: Multi-Feature | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

oppd와 목적(규모 있는 프로젝트의 완전한 완수)은 같으나 **선형 Phase가 아닌 종료조건 있는 2-루프 수렴 구조**(설계 수렴 루프 / 실행 수렴 루프)로 구동하는 루프 기반 오케스트레이터 `opal-pilot-project-loop`(alias `oppl`)를 신설한다 (→ D-1 §00, §01). 검증은 **Evaluator(구현 전 명세 심판) + test-agent(구현 후 동작 검증)** 로 2원화하고 (→ D-1 §04), **3-SSOT tool-gated JSON**(backlog.json/state.json/test-scenario.json)으로 축을 분리한다 (→ D-1 §02, §08). 신규 자산은 **에이전트 1개 + 스킬 1개 + 도구 1개 + 참조 4종**이며 나머지는 기존 컴포넌트 재사용(주입+상속)한다 (→ D-1 §06; [MUST] D-2 §명확화 제약①).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | backlog-tool 신규 도구 (backlog.json SSOT) | TASK 목표·범위, 제약③ (→ D-1 §08 도구 신규) | P0 | 없음 |
| F-002 | test-tool `scenario-*` 확장 (test-scenario.json SSOT) | TASK 범위, 제약③ (→ D-1 §08 도구 확장) | P0 | 없음 |
| F-003 | state-tool 소폭 확장 (`oppl` skill enum + 루프 회전) | TASK 완료기준①, SPEC 재사용 (→ D-1 §08 state-tool) | P0 | 없음 |
| F-004 | opal-evaluator-agent 전담 평가 에이전트 (패턴 B) | TASK 제약①④, 결정6 (→ D-1 §06) | P0 | 없음 |
| F-005 | oppl `references/` 참조 가이드 4종 | TASK 범위 (→ D-1 §07, §03, §04) | P0 | 없음 |
| F-006 | oppl `SKILL.md` 오케스트레이터 (2-루프 엔진) | TASK 목표, 결정1·2·5·10 (→ D-1 §03, §07) | P0 | F-001~F-005 |
| F-007 | 레지스트리 등록 (skills-registry + agents.md) | TASK 완료기준① (→ D-3 §3.1) | P0 | F-004, F-006 |
| F-008 | install-mac.sh 배포 반영 | TASK 완료기준①, 제약⑥ (→ D-2 §명확화 제약⑥) | P0 | F-001, F-004, F-006 |
| F-009 | docs/ 갱신 (PROJECT.md · ARCHITECTURE.md) | TASK 완료기준①, 문서 정합 (→ D-5, D-6) | P1 | F-006, F-007 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 backlog-tool ─┐
F-002 test scenario-* ┤
F-003 state-tool ext ─┼─→ F-006 oppl SKILL ─┬─→ F-007 레지스트리 ─┐
F-004 evaluator-agent ┤                      │                     ├─→ F-009 docs/
F-005 references 4종 ─┘                      └─→ F-008 install ────┘
   (F-001~F-005 상호 독립 · 병렬)          (F-004·F-006도 F-007/F-008 입력)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. 근거 인용: citation-rules.md §2·§3.2 (→ D-20).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-003 state-tool `--skill` enum | oppl 미등록 시 `state-tool init --skill oppl` 거부 → 오케스트레이터 STATE 초기화 불가 → 진입 자체 실패 | P0 | L2 (실제 init 호출) | S-020 |
| H-2 | F-002 `scenario-lock` 동결 게이트 | RED(실패) 미확인 상태에서 lock 허용 시 self-confirming 테스트로 T2→G 게이트 무력화 (→ D-1 §03 RED-first) | P0 | L1 단위 + L2 통합 | S-011 |
| H-3 | F-001 backlog.json 동시 쓰기 | 태스크 간 병렬 실행 중 backlog.json 원자성 미보장 → 상태 유실/손상 (→ D-1 §03 병렬 실행) | P1 | L1 단위 + L2 (동시성) | S-001b |
| H-4 | F-004 evaluator readonly 계약 | Evaluator가 소스/산출물 mutate 시 "생성자=평가자" 헌법 위반 ([MUST] D-1 §00; D-2 제약④) | P0 | L1 (tools 화이트리스트) + L2 (changed_files 검사) | S-030 |
| H-5 | F-001/F-002 결과 계약 (JSON) | 서브명령 출력이 단일라인 JSON·에러코드·exit code 계약 위반 시 오케스트레이터 파싱 실패 (→ D-8 종료코드, D-11 에러코드) | P1 | L1 단위 (JSON 파싱·exit 검증) | S-007 |
| H-6 | F-001/F-002 tool-gated 축 분리 | BACKLOG.md/STATE.md 손편집 허용 시 double-truth ([MUST] D-7 §State 관리; D-1 §02) | P1 | L2 (렌더 산출물 vs JSON 정합) | S-006 |
| H-7 | F-006 oppl 루프 종료조건 | 반복상한·예산·무진전 가드 부재 시 무한 루프/비용 폭주 (→ D-1 §07) | P0 | L3 (드라이런 무진전 시나리오) | S-055 |
| H-8 | F-006 3-way 모드 승계 | semi-agentic 경계(EXECUTE 이전 auto-pass 금지) 미승계 시 사용자 게이트 우회 (→ D-8 오류 #24; D-16 모드절) | P0 | L2 (state-tool validate) | S-051 |
| H-9 | F-006/F-004 검증 2원화 순서 | Evaluator(구현 전)와 test-agent(구현 후) 순서 뒤바뀌면 명세 리뷰 게이트 무력화 (→ D-1 §04, §06) | P1 | L3 (드라이런 파이프라인 순서 evidence) | S-090 |
| H-10 | F-007 skills-registry 트리거 | `oppl` 트리거 정규식 충돌/누락 시 `//oppl` 미발동 또는 오발동 (→ D-17 triggers; D-1 §08 alias 충돌 없음) | P1 | L1 (skill-registry validate) | S-060 |
| H-11 | F-008 install 배포 경계 | run.sh 실행권한 누락 시 배포본에서 backlog-tool 미동작 (→ D-19 L1114-1171 chmod) | P1 | L2 (배포 후 실행) | S-071 |
| H-12 | F-005/F-006 용어 일관성 | `BACKLOG.md`(백로그) ↔ 태스크 `PLAN.md`(미시설계) 명칭 혼동 (→ D-4 §4 명칭 충돌 주의; D-1 결정3 확정) | P2 | L1 (문서 용어 grep) | S-041 |

> H-1·H-2·H-4·H-7·H-8은 P0 — TEST-SCENARIO에서 L2/L3 의무 시나리오로 승격 권고.

---

## 2. 기능별 분석

### F-001: backlog-tool 신규 도구

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/backlog-tool/run.sh` | .venv python 래퍼 (state-tool run.sh 패턴) | 신규 |
| 도구 | `opal/tools/backlog-tool/backlog_tool.py` | backlog.json SSOT 관리 CLI | 신규 |
| 도구 | `opal/tools/backlog-tool/schema/backlog.schema.json` | JSON Schema Draft-07 | 신규 |
| 도구 | `opal/tools/backlog-tool/README.md` | 서브명령·에러코드·스키마 문서 | 신규 |

#### 2.1.2 현재 구현
기존 `state-tool`이 동일 아키텍처의 선례다: `run.sh`가 `~/.opal/.venv/bin/python`으로 `*_tool.py`를 exec하고 venv 부재 시 `{"ok":false,...}` + exit 1 (→ D-9:7-12). `state_tool.py`는 단일 파일 모놀리식으로 `set_defaults(func=cmd_x)` 디스패치(→ D-10:1788-1933), 단일라인 JSON 헬퍼 `ok()/err()` (→ D-10:121-139), KST 타임스탬프는 `~/.opal/tools/date/date.js` subprocess (→ D-10:145-161), state.json load/save (→ D-10:174-201), 마크다운 미러 렌더 `render_pipeline_table`/`replace_pipeline_section` (→ D-10:240-268). 에러코드는 `ERROR_CODES` dict SSOT (→ D-10:68-115). backlog-tool은 이 패턴을 그대로 복제한다.

#### 2.1.3 영향 범위
- **피호출자**: `~/.opal/tools/date/date.js` (KST 시점). 신규 도구는 date.js에만 의존.
- **호출자**: F-006 oppl SKILL의 D5(백로그 생성)·L0(태스크 선택)·L∞(관찰)·L✓(종료 판정) 단계.
- backlog.json은 state.json/test-scenario.json과 **축 분리** — 상호 참조 없음 ([MUST] D-2 §명확화 제약③).

---

### F-002: test-tool `scenario-*` 확장

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/test-tool/test_tool.py` | `_build_parser`·`dispatch` dict에 scenario-* 4종 추가 | 수정 |
| 도구 | `opal/tools/test-tool/lib/scenario.py` | scenario-* 핸들러 (spec존/result존 관리) | 신규 |
| 도구 | `opal/tools/test-tool/schema/test-scenario.schema.json` | test-scenario.json JSON Schema | 신규 |
| 도구 | `opal/tools/test-tool/README.md` | scenario-* 4서브명령 문서 + 변경이력 | 수정 |

#### 2.2.2 현재 구현
`test_tool.py`는 `lib/` 모듈 분리형(resolver/runner/e2e_adapter, → D-12:37-39)이며 argparse subparsers + `dispatch` dict 라우팅(→ D-12:196-249). 단일라인 JSON 헬퍼 `_respond(data, exit_code)`(→ D-12:60-63)·`_error(error_key, detail, command)`(→ D-12:66-76), 에러코드 catalog `ERROR_CODES`(→ D-12:46-54). 현재 4서브명령(resolve/check/unit/integration)은 **1회 실행·판정만** 수행하고 루프 한도는 오케스트레이터 책임 ([MUST] D-11 §개요). date.js 미사용. scenario-*는 신규 `lib/scenario.py`로 격리한다.

#### 2.2.3 영향 범위
- 기존 4서브명령 로직 불변 (신규 서브명령만 추가) → 회귀 위험 최소.
- **호출자**: F-006 oppl SKILL의 T2(테스트 시나리오 RED-first)·T4a(동작 검증 결과 기록).
- test-scenario.json은 backlog/state와 축 분리 — 검증 스펙+결과 전담 (→ D-1 §02).

---

### F-003: state-tool 소폭 확장

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/state-tool/state_tool.py` | `--skill` argparse choices에 `oppl` 추가 | 수정 |
| 도구 | `opal/tools/state-tool/schema/state.schema.json` | `skill` enum에 `oppl` 추가 | 수정 |
| 도구 | `opal/tools/state-tool/README.md` | init `--skill` 문서 + 변경이력 | 수정 |

#### 2.3.2 현재 구현
`state_tool.py`의 init 서브파서가 `--skill` 화이트리스트를 강제한다: `choices=["opp","opd","opds","opdw","opwt","opgc","oppd","opsdd"]` (→ D-10:1816-1817). 스키마도 동일 enum을 가진다 (→ D-10 schema:15). **`oppl` 미포함** — 오케스트레이터의 `state-tool init --skill oppl` 호출이 argparse 단계에서 거부된다 (H-1). 루프 회전 추적은 SPEC이 "소폭 확장"으로 명시 (→ D-1 §08 state-tool 행).

#### 2.3.3 영향 범위
- 2줄 enum 확장 + 스키마 1줄 → 기존 8개 스킬 동작 불변 (추가만).
- 루프 회전 필드: state.json은 스키마 `additionalProperties` 여부에 따라 자유 필드(예: `loop_meta`)를 rows 외부에 둘 수 있는지 확인 필요 (설계 시 결정 — 최소 침습 우선, in-file SSOT 행 테이블로 루프 태스크를 표현하는 opsdd 방식을 1차 채택 → D-16:343-373).

---

### F-004: opal-evaluator-agent 전담 평가 에이전트

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-evaluator-agent/AGENT.md` | 명세 심판 verdict-only 에이전트 | 신규 |

#### 2.4.2 현재 구현
선례는 `opal-convention-checker`(→ D-13)·`opal-security-checker`(→ D-14) — 둘 다 **패턴 B**: `tools: [Read, Grep, Glob, Bash]` readonly, `[WORKER]` 마커 시 부트스트랩 스킵, 외부 기준 문서(CONVENTIONS.md / OWASP Base + SECURITY.md)를 Read하여 자기완결 보고서 생성, **진단 전담 — 소스 파일 수정 금지**, `changed_files`에 보고서만 포함, 커밋 금지 (→ D-13:205-215, D-14:185-194). security-checker는 "Base 원칙 + 프로젝트 문서 병합" 구조(→ D-14:34-72)로, Evaluator의 "SPEC §4 루브릭 Base + CONTRACT.md 루브릭절 병합" 요구와 정확히 대응한다.

#### 2.4.3 영향 범위
- 신규 에이전트 1개 — TASK 제약① "Evaluator 외 신규 에이전트 금지"의 유일 허용분 ([MUST] D-2 §명확화 제약①).
- **호출자**: F-006 oppl SKILL의 D6(설계 산출물 검토)·G(태스크 명세 리뷰 게이트, 구현 전)·drift 재콜백.
- 헌법: 생성자≠평가자 → Evaluator는 Executor/Planner와 분리 ([MUST] D-1 §04 "평가자 ≠ 생성자").

---

### F-005: oppl `references/` 참조 가이드 4종

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 참조 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | 종료조건·무진전·예산·에러처리·컨텍스트 관리 | 신규 |
| 참조 | `opal/skills/opal-pilot-project-loop/references/contract.md` | CONTRACT.md 작성 규칙 + 거버넌스(오너십 계층) | 신규 |
| 참조 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | USER_JOURNEY/USER_FLOW Mermaid 작성 규칙(조건부) | 신규 |
| 참조 | `opal/skills/opal-pilot-project-loop/references/verification.md` | 검증 3-tier·Evaluator 콜백·산출물 기록 규칙 | 신규 |

#### 2.5.2 현재 구현
기존 오케스트레이터는 phase별 상세를 `references/*.md`로 분리하고 SKILL 본문에서 인라인 참조한다 — oppd `references/wbs-guide.md`·`verification-loop-guide.md`·`parallel-execution-guide.md`(→ D-15:277-279), opsdd `references/execute-loop-guide.md`(→ D-16:254). 4종 가이드는 SPEC의 §07(루프 제어)·§05(CONTRACT 거버넌스)·§02 note(UX 산출물)·§04(검증 3-tier)를 각각 상세화한다 (→ D-1).

#### 2.5.3 영향 범위
- SKILL 본문 슬림화 — 상세는 가이드로 위임. F-006 SKILL이 4종을 인라인 참조.

---

### F-006: oppl `SKILL.md` 오케스트레이터

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 2-루프 수렴 엔진 본문 | 신규 |

#### 2.6.2 현재 구현
oppd·opsdd가 골격 선례. 공통 `## Harness` 블록(모드 문자열 + base-harness fallback `>` 라인 + `[MUST]` 4-라인 sub-harness selector + `[MUST]` citation-rules + `mode_flag_conflict`)(→ D-15:22-33, D-16:21-32), 공통 `## Agentic / Semi-Agentic 모드` 절 레이아웃(default→boundary→explicit-table→flow→CLOSE gate→AGENTIC-LOG)(→ D-15:718-779, D-16:413-507), 공통 변경이력 3열 `| 버전 | 날짜 | 변경내용 |` + `(NNN)` 규약(→ D-16:511-534). 루프 오케스트레이터의 최근접 템플릿은 **opsdd EXECUTE-LOOP**(→ D-16:198-254): in-file SSOT 행 테이블(→ D-16:343-373) + `[R-13]` 동적 `add-row`로 루프 반복 행(ACT) 표현 + `opal-sdd-action-agent` 단일 디스패치 + 재시도 루프(unit/integration 최대 3회, L2 build 2회 후 에스컬레이션).

#### 2.6.3 영향 범위
- 신규 스킬 — 기존 오케스트레이터 불변(oppd 병행 유지, deprecate는 검증 후 → D-1 결정4).
- **디스패치 대상**: opal-planning-agent/opal-plan-agent(설계 루프), be/fe/db-agent·opal-task-action-agent(태스크 생성자), opal-evaluator-agent(명세 심판), opal-test-agent + conv/sec-checker(동작 검증) (→ D-1 §06).
- **도구 호출**: state-tool(state.json)·backlog-tool(backlog.json)·test-tool scenario-*(test-scenario.json).

---

### F-007: 레지스트리 등록

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | `opal-pilot` 그룹에 oppl 엔트리 + version bump + changelog | 수정 |
| 레지스트리 | `opal/core/references/agents.md` | opal-evaluator-agent 섹션 + 매핑 테이블 행 + 변경이력 | 수정 |

#### 2.7.2 현재 구현
skills-registry는 그룹별 배열 — 각 엔트리 `{name, alias, description, triggers[], paths[], (domain/pipeline)}` (→ D-17:6-147). oppd 엔트리(→ D-17:134-147)가 동렬 계열 선례. `changelog[]` 배열 + `version` 필드 존재 (→ D-17:724-763). agents.md는 checker 섹션(→ D-18:48-70)·전문 에이전트 매핑 테이블(→ D-18:137-151)·변경이력(→ D-18:333-346) 구조.

#### 2.7.3 영향 범위
- skill-registry 도구가 이 JSON을 트리거 SSOT로 소비 — 트리거 정규식 유효성 필수 (H-10).
- 매핑 테이블에 evaluator 행 추가 시 F-006 SKILL이 이를 주입받아 디스패치.

---

### F-008: install-mac.sh 배포 반영

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `scripts/install-mac.sh` | backlog-tool run.sh 실행권한 chmod 블록 추가 | 수정 |

#### 2.8.2 현재 구현
skills(`opal/skills/*/` 루프 → D-19:1058-1069)·agents(`opal/agents/*/` 루프 → D-19:1076-1085)·tools(`install_dir` 통째 복사 → D-19:1109-1112)는 **디렉토리 구동** — 신규 자산은 디렉토리 존재만으로 자동 배포되며 이름 배열 편집 불요. 단, 도구별 `chmod +x run.sh`는 명시적 if-블록(루프 아님, → D-19:1114-1171)에 나열 — playwright/state/brain/cmux/tool-scan/memory/git-sync만 포함하고 **test-tool은 git 실행비트에 의존**. 플랫폼 어댑터도 `~/.opal/agents/*/` 루프(→ D-19:640-703, install_codex_agents 706-814)라 evaluator 자동 반영.

#### 2.8.3 영향 범위
- 최소 침습: backlog-tool `run.sh`를 git 755로 커밋 + install L1114-1171에 chmod 블록 1개 추가(배포본 실행비트 보증, H-11).
- oppl 스킬·evaluator 에이전트는 install 코드 편집 불요(디렉토리 자동 배포). "install 반영" 검증은 배포 후 존재·실행 확인으로 수행.

---

## 3. 기능별 설계

### F-001: backlog-tool 신규 도구

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/backlog-tool/run.sh` | 도구 | .venv python 래퍼 | (→ D-9:1-12) |
| 2 | `opal/tools/backlog-tool/backlog_tool.py` | 도구 | backlog.json CLI (6서브명령) | (→ D-1 §08) |
| 3 | `opal/tools/backlog-tool/schema/backlog.schema.json` | 도구 | JSON Schema Draft-07 | (→ D-10 schema 패턴) |
| 4 | `opal/tools/backlog-tool/README.md` | 도구 | 문서 (state-tool README 패턴) | (→ D-8) |

#### 3.1.2 API·데이터 모델 설계

**run.sh** (state-tool 복제 → D-9:1-12):
```bash
#!/bin/bash
# @header: shell script — 적용 대상 아님 (header-rules.md §적용 대상 확장자 참조)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -x "$VENV_PYTHON" ]] || { echo '{"ok":false,"error":"venv_missing",...}' >&2; exit 1; }
exec "$VENV_PYTHON" "$SCRIPT_DIR/backlog_tool.py" "$@"
```
> [MUST] `docs/CONVENTIONS.md` §도구 우선 원칙: "파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구(`~/.opal/tools/`)를 우선 검토한다." → backlog-tool은 state-tool 패턴을 재사용한다 (→ D-7:190-192).

**backlog.json 스키마** (top-level, → D-10:706-715 state.json 형태 준용):
- `schema_version` "1.0" · `project_title` · `mode` (interactive|semi-agentic|agentic) · `created_at` · `updated_at` · `goal` (목표 요약 — 종료 판정 기준) · `tasks[]`
- `tasks[]` 각 항목: `id` (`T{NN}`) · `title` · `slice` (얇은 수직 슬라이스 설명) · `acceptance_criteria[]` (수용기준) · `area` (fe|be|db|공통|통합) · `priority` (P0|P1|P2) · `depends[]` (선행 task id) · `status` (pending|in_progress|done|blocked) · `parallel_group` (병렬 그룹 id, nullable) · `created_at` · `done_at`

> [MUST] `docs/CONVENTIONS.md` §State 관리: "마크다운 표 직접 편집 금지" — 동일 원칙을 backlog.json에 적용: BACKLOG.md는 도구가 렌더한 미러이며 손편집 금지 (→ D-7:184; D-1 §02 note "손편집 금지").

**6 서브명령** (→ D-1 §08 도구 신규 행 "init/add-task/select-next/mark/done-check/show"):
| 서브명령 | 시그니처 | 동작 | 결과(JSON) |
|---------|---------|------|-----------|
| `init` | `init <task-path> --project-title <t> --mode <m> [--goal <g>] [--force]` | backlog.json + BACKLOG.md 생성(멱등) | `{ok, command:"init", task_path, created_at}` |
| `add-task` | `add-task <task-path> --id <T> --title <t> --slice <s> --acceptance <json[]> --area <a> --priority <p> [--depends <ids>] [--parallel-group <g>]` | tasks[] 추가 + BACKLOG.md 재렌더 | `{ok, task_id, tasks_count}` |
| `select-next` | `select-next <task-path>` | depends 충족 + priority 최상위 pending 태스크 반환 (없으면 null) | `{ok, next_task_id, task}` |
| `mark` | `mark <task-path> --id <T> --status <s> [--note <n>]` | 상태 전이 + done 시 done_at 기록 | `{ok, task_id, status}` |
| `done-check` | `done-check <task-path>` | 모든 태스크 done + 회귀 0 판정 → 종료조건 충족 여부 | `{ok, all_done, remaining[], done_count, total}` |
| `show` | `show <task-path> [--format md|json]` | BACKLOG.md 렌더 또는 backlog.json raw | `{ok, ...}` 또는 md |

- KST 타임스탬프: `~/.opal/tools/date/date.js` subprocess (→ D-10:145-161), 실패 시 `date_tool_failed` exit 2.
- 헬퍼: `ok(command, **kw)` / `err(command, code, message, exit_code)` — 단일라인 JSON, `ensure_ascii=False` (→ D-10:121-139).
- BACKLOG.md 렌더: `## 백로그` 마커 구간(`<!-- backlog:start -->`~`<!-- backlog:end -->`)에 태스크 표 렌더 (→ D-10:240-268 render/replace 패턴).

#### 3.1.3 에러 코드 (state-tool 패턴 → D-8 카탈로그)
`ERROR_CODES` dict SSOT: `already_initialized`(1) · `backlog_not_initialized`(1) · `task_id_exists`(1) · `task_not_found`(1) · `invalid_status_transition`(1) · `dependency_not_found`(1) · `acceptance_invalid_json`(1) · `date_tool_failed`(2) · `task_path_not_found`(1). exit: 0 성공 / 1 검증·위반 / 2 내부오류 (→ D-8 종료코드).

#### 3.1.4 환경 변경
해당 없음 (표준 라이브러리 + date.js만 사용 → D-8 의존성).

#### 3.1.5 배치/마이그레이션
해당 없음.

#### 3.1.6 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | init | 기능 테스트 | init 후 backlog.json + BACKLOG.md 생성, 재실행 시 `already_initialized` exit 1 |
| TS-002 | add-task | 기능 테스트 | add-task 후 tasks[] 1건, BACKLOG.md 표에 반영 |
| TS-003 | select-next | 기능 테스트 | depends 미충족 태스크는 스킵, priority 순 pending 반환 |
| TS-004 | mark | 기능 테스트 | 유효 전이 성공, 무효 전이 `invalid_status_transition` |
| TS-005 | done-check | 기능 테스트 | 전 태스크 done 시 `all_done:true`, 잔여 시 `remaining[]` |
| TS-006 | show/tool-gated | 통합 테스트 | BACKLOG.md는 JSON 미러와 정합 (손편집 방지, H-6) |
| TS-007 | 결과 계약 | 기능 테스트 | 전 서브명령 단일라인 JSON + 규정 exit code (H-5) |
| TS-001b | 동시 쓰기 | 통합 테스트 | 병렬 mark 시 backlog.json 무손상 (H-3) |

---

### F-002: test-tool `scenario-*` 확장

#### 3.2.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/test-tool/lib/scenario.py` | 도구 | scenario-* 핸들러 (spec/result 존) | (→ D-1 §08 도구 확장) |
| 2 | `opal/tools/test-tool/schema/test-scenario.schema.json` | 도구 | test-scenario.json Schema | (→ D-10 schema 패턴) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/test-tool/test_tool.py` | 도구 | `_build_parser` subparser 4종 + `dispatch` dict 키 추가 | (→ D-12:196-249) |
| 2 | `opal/tools/test-tool/README.md` | 도구 | scenario-* 문서 + 변경이력 행 | (→ D-11:195-199) |

#### 3.2.2 API·데이터 모델 설계

**test-scenario.json 스키마** (spec존 + result존 분리, → D-1 §03 T2/T4a):
- `schema_version` · `task_id` · `locked` (bool — RED 확인 후 동결) · `created_at` · `locked_at` · `scenarios[]`
- `scenarios[]` 각 항목: `id` (`S{NNN}`) · `acceptance_ref` (수용기준/계약 참조) · `type` (unit|integration|contract|regression|e2e) · `expected` (기대결과) · **spec존**: `red_confirmed` (bool) · **result존**: `result` (pass|fail|null) · `evidence` · `marked_at`

**4 서브명령** (→ D-1 §08 "init/lock/mark/status (RED-first·spec 동결 게이트)"):
| 서브명령 | 시그니처 | 동작 | 결과(JSON) |
|---------|---------|------|-----------|
| `scenario-init` | `scenario-init --task-path <p> [--scenarios <json[]>]` | test-scenario.json 생성 (spec존, locked=false) | `{ok, command, scenarios_count}` |
| `scenario-lock` | `scenario-lock --task-path <p>` | 전 시나리오 `red_confirmed==true`일 때만 locked=true. 미충족 시 거부 | `{ok, locked}` / `err: red_not_confirmed` |
| `scenario-mark` | `scenario-mark --task-path <p> --id <S> --result <pass\|fail> [--evidence <e>]` | result존 기록 (locked 후에만) | `{ok, scenario_id, result}` |
| `scenario-status` | `scenario-status --task-path <p>` | spec/result 요약 (RED 확인·통과율) | `{ok, locked, total, red_confirmed, passed, failed}` |

> [MUST] RED-first 동결 게이트 (H-2): `scenario-lock`은 모든 시나리오가 `red_confirmed==true`(구현 전 실패 확인)일 때만 통과한다 — self-confirming 방지 (→ D-1 §03 "RED-first", §04 "구현 전"). 미확인 시 `red_not_confirmed` exit 1. `scenario-mark --result`는 `locked==true` 이후에만 허용(`scenario_not_locked` exit 1).

- JSON 헬퍼 `_respond`/`_error` 재사용 (→ D-12:60-76). 신규 에러코드 `ERROR_CODES`에 추가: `red_not_confirmed`(8) · `scenario_not_locked`(9) · `scenario_not_initialized`(10) · `scenario_spec_invalid_json`(11). 기존 4서브명령 exit code(2~7)와 충돌 없이 8~ 배정.
- **[MUST] 기존 4서브명령 로직 불변** — scenario-*는 `lib/scenario.py`로 격리하여 resolver/runner/e2e_adapter 미간섭 (→ D-12:37-39; 회귀 방지).

#### 3.2.3 환경 변경
해당 없음 (PyYAML 등 기존 의존 → D-11 의존).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | scenario-init | 기능 테스트 | test-scenario.json 생성, locked=false |
| TS-011 | scenario-lock RED 게이트 | 기능 테스트 | red_confirmed 미충족 시 `red_not_confirmed` exit 1 (H-2) |
| TS-012 | scenario-mark | 기능 테스트 | locked 후 result존 기록, locked 전 `scenario_not_locked` |
| TS-013 | scenario-status | 기능 테스트 | 통과율·RED 확인 수 정확 |
| TS-014 | 회귀 | 회귀 테스트 | 기존 resolve/check/unit/integration 동작 불변 |

---

### F-003: state-tool 소폭 확장

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | 도구 | `--skill` choices에 `"oppl"` 추가 | (→ D-10:1816-1817) |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 도구 | `skill` enum에 `"oppl"` 추가 | (→ D-10 schema:15) |
| 3 | `opal/tools/state-tool/README.md` | 도구 | init `--skill` 목록 + 변경이력 | (→ D-8:38-45) |

#### 3.3.2 API·데이터 모델 설계
- `p_init.add_argument("--skill", ... choices=[...,"oppl"])` — 기존 8종에 `oppl` 추가 (→ D-10:1816-1817).
- schema `"skill": {"enum": [..., "oppl"]}` (→ D-10 schema:15).
- **루프 회전 추적**: 최소 침습 원칙 — 1차 채택안은 **in-file SSOT 행 테이블 + `[R-13]` add-row 동적 행**으로 루프 태스크를 표현(opsdd 방식 → D-16:336-373). state.json 스키마에 신규 필드를 추가하지 않는다(스키마 안정성 우선). 루프 회전 수 등 메타가 필요하면 `add-row`/`status` 노트로 기록. → 설계 결정: 스키마 무변경 (H-1과 독립).

> [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다" — state-tool enum 확장은 플랫폼 중립 (→ D-7:205-208).

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | --skill oppl | 통합 테스트 | `state-tool init --skill oppl --mode semi-agentic` 성공 (H-1) |
| TS-021 | schema enum | 산출물 검사 | state.schema.json에 oppl 포함, validate 통과 |
| TS-022 | 회귀 | 회귀 테스트 | 기존 8개 스킬 init 동작 불변 |

---

### F-004: opal-evaluator-agent

#### 3.4.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/agents/opal-evaluator-agent/AGENT.md` | 에이전트 | 명세 심판 verdict-only | (→ D-14 패턴 B) |

#### 3.4.2 설계 (checker 패턴 B 준용 → D-13, D-14)

**frontmatter** (→ D-14:1-10):
```yaml
name: opal-evaluator-agent
description: |
  계약·설계 루브릭 심판 전담 에이전트. SPEC §4 루브릭 Base + CONTRACT.md 루브릭절을 기준으로
  구현 전 명세(PLAN/USER_FLOW/test-scenario+계약)를 판정한다. verdict-only·mutate 금지·readonly.
  oppl 태스크 파이프라인 G(명세 리뷰) 게이트 및 설계 루프 D6에서 디스패치.
model: advanced
icon: "⚖️"
tools: [Read, Grep, Glob, Bash]
```
> [MUST] `docs/CONVENTIONS.md` §YAML Frontmatter: 에이전트는 `model`·`icon` 필드를 가진다 (→ D-7:74-89).
> [MUST] D-1 §04: "평가자 ≠ 생성자 — 생성 모델과 다른(강한) 모델로 평가. Evaluator ≠ Executor/Planner." → `model: advanced` (강한 모델) + readonly tools. (D-2 §명확화 제약④ 헌법 준수).

**입력 명세** (→ D-13:22-31 패턴):
| 파라미터 | 필수 | 설명 |
|---------|------|------|
| task_folder | O | 태스크 폴더 경로 |
| phase | O | `design-review`(D6) / `spec-review`(G, 구현 전) / `drift-recheck` |
| target_artifacts | O | 판정 대상 (PLAN.md / USER_FLOW.md / test-scenario.json / PRD·TRD·CONTRACT) |
| contract_path | O | `CONTRACT.md` (루브릭절 기준 원천 — CONVENTIONS.md를 conv-checker가 읽듯) |
| timestamp | O | 보고서 파일명용 |
| project_root | O | 프로젝트 루트 |

**실행 프로세스** (security-checker Base+문서 병합 구조 → D-14:34-72):
- Phase 1: SPEC §4 루브릭 Base 로드 (계약 완전성/일관성/설계 정합/drift/컨벤션 정신/아키텍처 적합, Likert 1–5, 통과선 ≥4 — → D-1 §04 루브릭 표).
- Phase 2: `CONTRACT.md` 존재 시 루브릭절 병합 (없으면 Base만 + 안내). 기계검증절은 test-tool/checker 소관이므로 Evaluator는 **루브릭절만** 판정.
- Phase 3: target_artifacts 순회 판정 → 차원별 Likert + drift binary(yes/no).
- Phase 4: 결과 계약 산출 — `{item, result(PASS|FAIL / Likert), reason, suggestion}` (→ D-1 §06 card "산출: {item, result, reason, suggestion}").
- Phase 5: 자기완결 보고서 생성 — 기존 리포트 준용, 명세리뷰는 `QA-SPEC.md`, 없으면 태스크 폴더 `VERIFICATION.md` (→ D-1 §03 T-G 산출, §09 결과계약 {대상·PASS/FAIL·사유·시점}).
- Phase 6: 결과 반환 JSON — `changed_files`에 보고서만 (소스 미수정).

**결과 반환** (→ D-13:181-191):
```json
{"artifact_path": "{task_folder}/QA-SPEC.md", "summary": "...", "status": "completed|blocked",
 "verdict": "pass|fail", "blockers": [], "changed_files": ["QA-SPEC.md"]}
```

**행동 규칙** (→ D-14:185-194):
1. `[WORKER]` 마커 시 부트스트랩 스킵.
2. **verdict-only · mutate 금지** — 소스/산출물 수정 금지, tools는 Read/Grep/Glob/Bash만 (H-4).
3. **커밋 금지.**
4. drift 판정 = binary yes/no; yes면 §5 거버넌스 에스컬레이션(PM/통합게이트/사용자) — Evaluator는 판정만, 반영은 PM (→ D-1 §05).
5. 기준 원천은 CONTRACT.md 루브릭절 (내장 루브릭은 SPEC §4 Base만; 프로젝트 계약 우선).

> [MUST] D-2 §명확화 제약④: "헌법 준수(생성자≠평가자, enforce-don't-advise, done=verified)." → Evaluator는 구현 전 명세를 심판하는 독립 게이트이며 생성자와 분리된다.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | verdict-only | 산출물 검사 | changed_files에 보고서만, 소스 미변경 (H-4) |
| TS-031 | CONTRACT 루브릭 로드 | 통합 테스트 | CONTRACT.md 루브릭절 기준 판정, 부재 시 Base+안내 |
| TS-032 | 결과 계약 | 산출물 검사 | `{item, result, reason, suggestion}` + verdict 반환 |
| TS-033 | [WORKER] 스킵 | 통합 테스트 | 부트스트랩 스킵 후 즉시 Phase 1 |
| TS-034 | drift binary | 기능 테스트 | drift yes/no 판정 + 거버넌스 에스컬레이션 안내 |

---

### F-005: oppl `references/` 4종

#### 3.5.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `.../references/loop-control.md` | 참조 | 종료조건·안전 가드 상세 | (→ D-1 §07) |
| 2 | `.../references/contract.md` | 참조 | CONTRACT 작성·거버넌스 | (→ D-1 §04 D4, §05) |
| 3 | `.../references/journey-flow.md` | 참조 | UX 산출물 Mermaid 규칙 | (→ D-1 §02 note, §03 D1.5/T1) |
| 4 | `.../references/verification.md` | 참조 | 검증 3-tier·기록 규칙 | (→ D-1 §04, §03 note) |

> 경로 접두: `opal/skills/opal-pilot-project-loop/references/`

#### 3.5.2 설계 (각 가이드 필수 섹션)
- **loop-control.md**: 반복 상한(루프별 hard cap) · 토큰/비용 예산 · 무진전 감지 · 목표 달성 체크(수용 테스트 기반) · 경로 분리(성공/실패/에스컬레이션) · 에러 처리(복구가능 vs 하드블로커) · 컨텍스트 관리(압축 작업기억) · 사람 게이트(비가역 행동 전) (→ D-1 §07 표 전 항목).
- **contract.md**: CONTRACT.md 1급 산출물 구조(인터페이스 계약 = 스키마·시그니처·경계 + **기계검증절 + 루브릭절**) · 작성=Planner/리뷰=Evaluator/반영=PM · 변경 거버넌스 오너십 계층 4단계(무변경→PM자율 / 내부조정→PM자율 / 인터페이스변경→통합게이트 / 외부노출→사용자) (→ D-1 §04 D4, §05 표).
- **journey-flow.md**: USER_JOURNEY.md(Loop1 거시 — 단계·행동·시스템 반응) / USER_FLOW.md(Loop2 미시 — 분기·상태·에러경로) · Mermaid `flowchart`/`sequenceDiagram` · **user-facing 프로젝트만 트리거**(인프라·라이브러리·CLI 내부 스킵) · Flow는 인터랙션 슬라이스만(순수 API/BE는 계약 테스트 대체) (→ D-1 §02 note "* UX 산출물").
- **verification.md**: 검증 3-tier 위계(① 결정론 code → ② 루브릭 LLM → ③ 사람) · 검증 2원화(Evaluator 구현 전 / test-agent 구현 후, 통과 후 conv/sec-checker, drift 시만 Evaluator 재콜백) · 산출물 자동 생성·기록(GC-*/QA-*/test-scenario.json/DONE, 없으면 VERIFICATION.md) · 결과 계약 {대상·PASS/FAIL·사유·시점} (→ D-1 §04, §03 note 2종).

#### 3.5.3 환경/3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | 4종 존재·섹션 | 산출물 검사 | 4개 가이드 각 필수 섹션 포함, SKILL 참조와 정합 |
| TS-041 | 용어 일관성 | 산출물 검사 | BACKLOG.md ↔ 태스크 PLAN.md 명칭 구분 준수 (H-12) |

---

### F-006: oppl `SKILL.md`

#### 3.6.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | 2-루프 수렴 엔진 | (→ D-1 §03) |

#### 3.6.2 설계

**frontmatter** (→ D-15:1-15, D-16:1-14):
```yaml
name: opal-pilot-project-loop
description: |
  루프 기반 프로젝트 오케스트레이터 — 요청 분석→계획→목표 충족까지 반복(2-루프 수렴).
  ... (트리거 키워드 포함)
triggers:
  - "^opal-pilot-project-loop$"
  - "^oppl$"
  - "(?i)(루프\\s*오케스트레이터|수렴\\s*루프|프로젝트\\s*루프)"
version: 1.0.0
```

**본문 섹션 스켈레톤** (oppd/opsdd 골격 준용):
1. `## Harness` — 모드 문자열 `Project Loop (설계 루프 → 실행 루프)` + base-harness fallback `>` 라인 + `[MUST]` 4-라인 sub-harness selector(interactive/agentic/semi-agentic + `mode_flag_conflict`) + `[MUST]` citation-rules (→ D-15:22-33, D-16:21-32). **[MUST] 3-way 모드 그대로 승계** (D-2 §명확화 제약②, D-1 결정5).
2. `## 계층 · 핵심 개념` — 프로젝트 > 태스크(슬라이스) > 단계, 3-SSOT tool-gated (→ D-1 §02).
3. `## 사전 조건 체크` (→ D-15:44).
4. `## 폴더 구조` — 아래 3.6.3.
5. `## STATE.md 초기 생성` — `state-tool init --skill oppl --mode <m> --rows-from opal/skills/opal-pilot-project-loop/SKILL.md` (→ D-16:330-332; F-003이 oppl enum 선행). in-file SSOT 행 테이블 + `[R-13]` 동적 add-row (→ D-16:336-373).
6. `## Loop 1 — 설계 수렴 루프` — D1 인터뷰 → D1.5 여정*(조건부) → D2 PRD → D3 TRD → D4 CONTRACT → D5 백로그(backlog-tool init/add-task) → D6 Evaluator 검토(디스패치) → D7 사용자 확정 게이트 (→ D-1 §03 Loop1 표). 종료조건: 4요소 잠김 + 미해결 0.
7. `## Loop 2 — 실행 수렴 루프` — L0 선택(backlog-tool select-next) → 태스크 파이프라인 → L∞ 관찰(backlog-tool mark/add-task) → L✓ 종료판정(backlog-tool done-check) (→ D-1 §03 Loop2 바깥 루프 표). 종료조건: 전 수용기준 GREEN + 회귀 0.
8. `## 태스크 내부 파이프라인` — T1 명세·설계(PLAN.md·USER_FLOW*) → T2 테스트시나리오(test-tool scenario-init, RED-first) → **G 명세 리뷰 게이트(Evaluator, 구현 전)** → T3 구현 → T4a 테스트(test-agent, 구현 후) → T4b 규칙검사(conv/sec-checker, 변경파일) → T5 마무리(DONE.md) (→ D-1 §03 태스크 내부 파이프라인 표).
9. `## 디스패치 (하이브리드 C)` — 생성자(도메인 resolve, T1~T3) + Evaluator 별도, 태스크당 ~3회, 저위험 슬라이스 인라인 경량화, drift 시만 Evaluator 재콜백 (→ D-1 §03 note, §08 결정1). 디스패치 idiom은 opsdd EXECUTE-LOOP의 action-agent 서술형 + `[WORKER]` 프롬프트 (→ D-16:198-254).
10. `## 검증 2원화` — Evaluator(명세 심판, 구현 전) / test-agent(동작 검증, 구현 후) → verification.md 참조 (→ D-1 §04).
11. `## 루프 제어` — loop-control.md 참조, 종료조건 5종(반복상한·예산·무진전·목표체크·사람게이트) (→ D-1 §07).
12. `## CONTRACT 거버넌스` — contract.md 참조 (→ D-1 §05).
13. `## Agentic / Semi-Agentic 모드` — 승계 절(default semi-agentic→boundary→explicit-table→flow→CLOSE gate→AGENTIC-LOG) (→ D-15:718-779, D-16:413-507).
14. `## 산출물 · 기록 규칙` — 자동 생성, 기존 리포트 준용, 없으면 VERIFICATION.md, 결과계약 (→ D-1 §03 note).
15. `## 병렬 실행` — 태스크 간 기본(worktree), 계약 고정 시 태스크 내 FE/BE, 병렬 그룹마다 통합 태스크 필수, STATE는 PM 단독 갱신 (→ D-1 §03 병렬 note).
16. `## DONE.md / CLOSE` — 사용자 승인 게이트 후 docs/ 승격 + brain-ingest 훅 (→ D-16:279-317).
17. `## 스킬 탐색 경로` / `## 프로젝트 메모리 동기화` (→ D-15:685-717).
18. `## 변경이력` — `| 버전 | 날짜 | 변경내용 |`, `v1.0 | 2026-07-10 | 초기 작성 (056)` (→ D-16:511-534, D-7:96-104).

> [MUST] `docs/CONVENTIONS.md` §디스패치 의무: "오케스트레이터 SKILL.md에서 '워커 디스패치'로 정의된 단계는 반드시 서브에이전트를 디스패치한다. PM이 직접 실행으로 대체하지 않는다." → D6·G·T1~T4는 디스패치 단계 (→ D-7:165-168).
> [MUST] `docs/CONVENTIONS.md` §State 관리: STATE.md 행 상태 변경은 state-tool 서브명령으로만 (→ D-7:182-186).
> [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: SKILL 본문에 플랫폼 조건문 금지 (→ D-7:205-208; D-2 §.opal/AGENT.md 금지사항).

#### 3.6.3 폴더 구조 (산출물 레이아웃, → D-4 §7 조정 · D-1 §02·명칭 결정3)
```
tasks/{NNN}-oppl-{프로젝트명}/
├── TASK.md · STATE.md
├── BACKLOG.md            (backlog-tool 렌더 미러 — 손편집 금지)
├── backlog.json          (backlog-tool SSOT)
├── PRD.md · TRD.md · CONTRACT.md · USER_JOURNEY.md*   (설계 루프 산출 → 확정 후 docs/ 승격)
├── DONE.md
└── tasks/
    └── T{NN}-{태스크명}/  { PLAN.md, USER_FLOW.md*, test-scenario.json, QA-SPEC.md, DONE.md, (VERIFICATION.md) }
```

#### 3.6.4 환경/배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | frontmatter·triggers | 산출물 검사 | name/description/triggers/version 정상, oppl 트리거 포함 |
| TS-051 | harness 3-way 승계 | 산출물 검사 | Harness 블록 + Agentic/Semi 절, semi-agentic 기본 (H-8) |
| TS-052 | STATE init 호출 | 산출물 검사 | `--skill oppl --rows-from ...` 명시 |
| TS-053 | 2-루프 구조 | 산출물 검사 | Loop1(D1~D7)·Loop2(L0~L✓)·태스크 파이프라인(T1~T5+G) 섹션 존재 |
| TS-054 | 디스패치 하이브리드 C | 산출물 검사 | 생성자+Evaluator ~3회, 검증 2원화 순서(구현 전/후) 명시 (H-9) |
| TS-055 | 루프 종료조건 | 산출물 검사 | 반복상한·예산·무진전·목표체크·사람게이트 5종 (H-7) |
| TS-056 | references 링크 | 산출물 검사 | 4종 가이드 인라인 참조 정합 |

---

### F-007: 레지스트리 등록

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | opal-pilot 그룹 oppl 엔트리 + version bump + changelog | (→ D-17:134-147, 724-763) |
| 2 | `opal/core/references/agents.md` | 레지스트리 | evaluator 섹션 + 매핑 테이블 행 + 변경이력 | (→ D-18:48-70, 137-151, 333-346) |

#### 3.7.2 설계
**skills-registry oppl 엔트리** (oppd 형태 준용 → D-17:134-147):
```json
{
  "name": "opal-pilot-project-loop", "alias": "oppl",
  "description": "루프 기반 프로젝트 오케스트레이터 (2-루프 수렴: 설계 루프 → 실행 루프, 종료조건 제어)",
  "triggers": ["^opal-pilot-project-loop$", "^oppl$", "(?i)(루프\\s*오케스트레이터|수렴\\s*루프|프로젝트\\s*루프)"],
  "paths": ["{project}/.opal/skills/opal-pilot-project-loop/SKILL.md", "~/.opal/skills/opal-pilot-project-loop/SKILL.md"],
  "domain": "dev", "pipeline": "설계 루프(인터뷰→PRD→TRD→CONTRACT→BACKLOG) → 실행 루프(태스크 반복)"
}
```
- `version` 3.7.0 → 3.8.0 bump + `changelog[]` 최상단 엔트리 추가 (→ D-17:724-733).
- **[MUST] alias `oppl` 충돌 없음** 확인 (D-1 §08 결정2 확정; H-10) — 기존 opp/oppd/opsdd와 정규식 비충돌.

**agents.md evaluator 등록** (checker 섹션 형태 → D-18:48-70):
- `### opal-evaluator-agent` 섹션: 역할/호출시점/단계(명세 리뷰 — oppl G·D6)/영역(평가)/model(advanced)/자체 로드 문서(SPEC §4 Base + CONTRACT.md 루브릭절)/입력/출력(QA-SPEC.md·VERIFICATION.md)/에이전트 경로.
- 전문 에이전트 매핑 테이블에 행 추가 (→ D-18:141-151): `| opal-evaluator-agent | 명세 리뷰 (oppl G/D6) | 평가 | advanced | SPEC §4 루브릭 Base, CONTRACT.md 루브릭절 |`.
- 변경이력 행 추가: `| v2.0 | 2026-07-10 HH:mm KST | opal-evaluator-agent 신규 등록 + 매핑 테이블 행 (056) |`.

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 YYYY-MM-DD HH:mm (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함" (→ D-7:194-198).

#### 3.7.3 환경/배치
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | oppl 엔트리·트리거 | 산출물 검사 | JSON 유효, 트리거 정규식 컴파일 성공, alias 충돌 없음 (H-10) |
| TS-061 | skill-registry validate | 통합 테스트 | skill-registry validate 통과 (dangling·드리프트 0) |
| TS-062 | evaluator 등록 | 산출물 검사 | agents.md 섹션 + 매핑 행 + 변경이력 정합 |

---

### F-008: install-mac.sh 배포 반영

#### 3.8.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 환경 | backlog-tool run.sh chmod +x 블록 추가 (L1114-1171 구간) | (→ D-19:1114-1171) |

#### 3.8.2 설계
- skills/agents/tools는 디렉토리 구동 자동 배포 — oppl 스킬·evaluator 에이전트·backlog-tool 디렉토리는 **install 코드 편집 없이** 배포됨 (→ D-19:1058-1112). 플랫폼 어댑터도 `~/.opal/agents/*/` 루프로 evaluator 자동 반영 (→ D-19:640-814).
- **필요 편집**: 도구별 chmod if-블록(→ D-19:1114-1171)에 backlog-tool `run.sh` 실행권한 부여 1블록 추가 (state-tool L1122 패턴 준용). 또는 `run.sh`를 git 755로 커밋 (F-001 Step에서 보증) — **두 방법 병행 권고**로 배포본 실행 확실성 확보 (H-11).

> [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행하고 install-mac.sh로 재배포한다." (→ D-7:200-203; D-2 §명확화 제약⑥).
> [MUST] `.opal/AGENT.md` 금지사항: "하드코딩된 플랫폼 분기 추가 금지 — 어댑터 계층(install·plugin)에서만" — chmod 블록은 어댑터 계층(install)이므로 허용, SKILL/AGENT 본문 아님 (→ D-2 §.opal/AGENT.md).

#### 3.8.3 환경/배치
- 배포 검증: `./scripts/install-mac.sh` 실행 후 `~/.opal/tools/backlog-tool/run.sh`(실행가능)·`~/.opal/agents/opal-evaluator-agent/AGENT.md`·`~/.opal/skills/opal-pilot-project-loop/SKILL.md` 존재 확인 + `~/.claude/agents/opal-evaluator-agent.md` 어댑터 생성 확인.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-070 | 배포 존재 | 통합 테스트 | install 후 oppl/evaluator/backlog-tool 3자산 + 어댑터 배포 확인 |
| TS-071 | run.sh 실행권한 | 통합 테스트 | 배포된 backlog-tool run.sh 실행 가능 (H-11) |

---

### F-009: docs/ 갱신

#### 3.9.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `docs/PROJECT.md` | 문서 | 주요 컴포넌트 표에 oppl 파이프라인 섹션/행 + 변경이력 | (→ D-5:53-98, 134-142) |
| 2 | `docs/ARCHITECTURE.md` | 문서 | 서브에이전트 목록·오케스트레이터 표·전문 에이전트 표에 evaluator/oppl + 변경이력 | (→ D-6:41-51, 106-167, 379-386) |

#### 3.9.2 설계
- PROJECT.md: 오케스트레이터 컴포넌트로 oppl(alias) 등록, 변경이력 행 `| 2026-07-10 | oppl 루프 오케스트레이터 + opal-evaluator-agent + backlog-tool 신설 (056) |` (→ D-5:134-142).
- ARCHITECTURE.md: 서브에이전트 목록(→ D-6:41-51)·오케스트레이터 표(→ D-6:106-114)·전문 에이전트 표(→ D-6:160-167)에 evaluator·oppl 추가 + 변경이력 (→ D-6:379-386).
- **agent: PM 직접** (docs/ 갱신 Step 규칙).

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: docs/ 변경 시 변경이력 행 추가 (→ D-7:194-198).

#### 3.9.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-080 | PROJECT.md | 산출물 검사 | oppl 컴포넌트 등록 + 변경이력 행 |
| TS-081 | ARCHITECTURE.md | 산출물 검사 | evaluator·oppl 표 반영 + 변경이력 행 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002, F-003 (도구 3종) | 1, 2, 3 | opal-task-agent | 병렬 가능 | 독립 도구 디렉토리 |
| 1 | F-004 (evaluator) | 4 | opal-task-agent | 병렬 가능 | 독립 에이전트 파일 |
| 1 | F-005 (references) | 5 | opal-task-agent | 병렬 가능 | 독립 문서 4종 |
| 2 | F-006 (oppl SKILL) | 6 | opal-task-agent | 순차 | F-001~F-005 완료 후 (참조·도구·에이전트 확정) |
| 3 | F-007 (레지스트리) | 7, 8 | opal-task-agent | 순차 | F-004·F-006 완료 후 |
| 3 | F-008 (install) | 9 | opal-task-agent | 순차 | F-001·F-004·F-006 완료 후 |
| 4 | 도구 단위/통합 TEST | 10, 11, 12 | opal-test-agent | 순차 | 구현 완료 후 (완료기준②) |
| 5 | oppl 드라이런 E2E | 13 | opal-test-agent | 순차 | 전체 배포 후 (완료기준③) |
| 6 | F-009 (docs/) | 14, 15 | PM 직접 | 순차 | 검증 통과 후 |

### 4.2 실행 체크리스트

> 총 15개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: backlog-tool 신규 구현 (run.sh + backlog_tool.py + schema + README)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/backlog-tool/{run.sh, backlog_tool.py, schema/backlog.schema.json, README.md}`
- **작업 내용**: state-tool 패턴 복제 — run.sh(.venv exec, git 755), 6서브명령(init/add-task/select-next/mark/done-check/show), ok/err 단일라인 JSON 헬퍼, date.js 타임스탬프, backlog.json 스키마(§3.1.2), BACKLOG.md 마커 렌더, ERROR_CODES SSOT
- **완료 기준**: TS-001~007 GREEN, `run.sh`가 exec 가능, JSON 계약·exit code 준수
- **테스트**: TS-001~007, TS-001b
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: test-tool scenario-* 확장 (lib/scenario.py + test_tool.py 라우팅 + schema + README)
- [x] 완료
- **소속 기능**: F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/test-tool/{lib/scenario.py, test_tool.py, schema/test-scenario.schema.json, README.md}`
- **작업 내용**: `_build_parser`에 scenario-init/lock/mark/status 4 subparser + dispatch dict 키 추가, lib/scenario.py 핸들러(spec존/result존), RED-first 동결 게이트(§3.2.2), 에러코드 8~11 추가. **기존 4서브명령 불변**
- **완료 기준**: TS-010~013 GREEN + TS-014 회귀 통과 (기존 resolve/check/unit/integration 불변)
- **테스트**: TS-010~014
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: state-tool oppl enum 확장 (state_tool.py + schema + README)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/state-tool/{state_tool.py, schema/state.schema.json, README.md}`
- **작업 내용**: `--skill` choices(L1817)에 `"oppl"` 추가, schema enum(L15)에 `"oppl"` 추가, README init 목록 갱신 + 변경이력. state.json 스키마 신규 필드 없음(루프 행은 in-file add-row로 표현)
- **완료 기준**: TS-020~021 GREEN, TS-022 회귀 (기존 8스킬 불변)
- **테스트**: TS-020~022
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: opal-evaluator-agent 신규 작성 (AGENT.md)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-evaluator-agent/AGENT.md`
- **작업 내용**: checker 패턴 B — frontmatter(model: advanced, tools readonly, icon), 입력 명세, 6-Phase 실행 프로세스(SPEC §4 루브릭 Base + CONTRACT.md 루브릭절 병합), 결과 계약 {item,result,reason,suggestion}+verdict, 행동 규칙(verdict-only/mutate 금지/커밋 금지), 변경이력
- **완료 기준**: TS-030~034 산출물 검사 통과, tools에 Edit/Write 없음 (readonly)
- **테스트**: TS-030~034
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 5: oppl references/ 4종 작성 (loop-control·contract·journey-flow·verification)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 참조
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/{loop-control,contract,journey-flow,verification}.md`
- **작업 내용**: §3.5.2의 각 가이드 필수 섹션 작성, BACKLOG.md↔PLAN.md 명칭 구분 준수, 각 문서 변경이력
- **완료 기준**: TS-040~041 산출물 검사 통과
- **테스트**: TS-040, TS-041
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 6: oppl SKILL.md 작성 (2-루프 엔진 본문)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: §3.6.2 18개 섹션 스켈레톤 — Harness 3-way 승계, STATE init(--skill oppl), Loop1(D1~D7)/Loop2(L0~L✓)/태스크 파이프라인(T1~T5+G), 디스패치 하이브리드 C, 검증 2원화, 루프 제어 5종, CONTRACT 거버넌스, 폴더 구조(§3.6.3), references 4종 인라인 참조, 변경이력
- **완료 기준**: TS-050~056 산출물 검사 통과, 디스패치 의무·State 관리·플랫폼 분기 [MUST] 준수
- **테스트**: TS-050~056
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3, 4, 5

#### Step 7: opal-skills-registry.json oppl 등록
- [x] 완료
- **소속 기능**: F-007
- **영역**: 레지스트리
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: opal-pilot 그룹에 oppl 엔트리(§3.7.2), version 3.8.0 bump, changelog 엔트리 추가
- **완료 기준**: TS-060~061 GREEN (JSON 유효, 트리거 컴파일, skill-registry validate 통과)
- **테스트**: TS-060, TS-061
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: agents.md evaluator 등록 + 매핑 테이블 행
- [x] 완료
- **소속 기능**: F-007
- **영역**: 레지스트리
- **agent**: opal-task-agent
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: `### opal-evaluator-agent` 섹션 + 전문 에이전트 매핑 테이블 행 + 변경이력 행(§3.7.2)
- **완료 기준**: TS-062 산출물 검사 통과
- **테스트**: TS-062
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 9: install-mac.sh backlog-tool chmod 블록 추가
- [x] 완료
- **소속 기능**: F-008
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 도구별 chmod if-블록(L1114-1171)에 backlog-tool run.sh 실행권한 부여 1블록 추가(state-tool 패턴). 스킬/에이전트/도구 자동 배포는 편집 불요(디렉토리 구동)
- **완료 기준**: 스크립트 문법 유효(`bash -n`), chmod 블록 정합
- **테스트**: TS-070·TS-071 (Step 12에서 배포 검증)
- **실행 방법**: sub-agent
- **의존**: Step 1, 4, 6

#### Step 10: 신규/확장 도구 단위 테스트 (backlog-tool + scenario-* + state-tool)
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (테스트 스크립트/명령 — 태스크 폴더 하위)
- **작업 내용**: backlog-tool 6서브명령·test-tool scenario-* 4서브명령·state-tool oppl init 단위 테스트 실행, JSON·exit code·RED 게이트·전이 검증
- **완료 기준**: 완료기준② — 단위 테스트 GREEN (TS-001~007, 010~013, 020~021)
- **테스트**: TS-001~007, TS-010~013, TS-020~021
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3

#### Step 11: 회귀 테스트 (test-tool 기존 4서브명령 + state-tool 기존 8스킬)
- [ ] 완료
- **소속 기능**: F-002, F-003
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (기존 도구 스위트)
- **작업 내용**: test-tool resolve/check/unit/integration 불변 확인, state-tool 기존 스킬 init 불변 확인
- **완료 기준**: TS-014·TS-022 GREEN (회귀 0)
- **테스트**: TS-014, TS-022
- **실행 방법**: sub-agent
- **의존**: Step 2, 3

#### Step 12: install 배포 + 통합 검증
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 환경
- **agent**: opal-test-agent
- **파일**: `~/.opal/` 배포본 (검증 대상)
- **작업 내용**: `./scripts/install-mac.sh` 실행 후 oppl 스킬·evaluator 에이전트·backlog-tool 배포 + 어댑터 생성 + run.sh 실행권한 확인
- **완료 기준**: TS-070~071 GREEN, 완료기준① 배포 반영
- **테스트**: TS-070, TS-071
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 13: oppl 드라이런 E2E (설계 루프 → 실행 루프 1태스크)
- [ ] 완료
- **소속 기능**: F-006 (전 기능 통합)
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (드라이런 태스크 폴더 + evidence)
- **작업 내용**: oppl 최소 1회 드라이런 — 설계 루프(인터뷰~CONTRACT~BACKLOG, Evaluator D6) → 실행 루프 1태스크(T1~T5, G 명세 리뷰 게이트, 검증 2원화 순서) 완주. 3-SSOT 갱신·검증 순서·종료 판정 evidence 수집
- **완료 기준**: 완료기준③ — 드라이런 1회 동작 검증 evidence, 검증 2원화 순서(구현 전 Evaluator → 구현 후 test-agent) 확인 (TS-090)
- **테스트**: TS-090 (H-7·H-9 검증)
- **실행 방법**: sub-agent
- **의존**: Step 12

#### Step 14: docs/PROJECT.md 갱신
- [ ] 완료
- **소속 기능**: F-009
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: oppl 오케스트레이터 컴포넌트 등록 + 변경이력 행(§3.9.2)
- **완료 기준**: TS-080 산출물 검사 통과
- **테스트**: TS-080
- **실행 방법**: direct
- **의존**: Step 6, 7

#### Step 15: docs/ARCHITECTURE.md 갱신
- [ ] 완료
- **소속 기능**: F-009
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: 서브에이전트 목록·오케스트레이터 표·전문 에이전트 표에 evaluator·oppl 추가 + 변경이력 행(§3.9.2)
- **완료 기준**: TS-081 산출물 검사 통과
- **테스트**: TS-081
- **실행 방법**: direct
- **의존**: Step 6, 8

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ 2 ∥ 3 ∥ 4 ∥ 5 | 독립 파일/디렉토리, 상호 의존 없음 (도구·에이전트·참조 각기 독립 축) |
| Step 1~5 → Step 6 | oppl SKILL이 도구 호출·evaluator 디스패치·references 인라인 참조를 확정 후 기술 |
| Step 4 → Step 8 | agents.md evaluator 등록은 에이전트 파일 확정 후 |
| Step 6 → Step 7 | skills-registry oppl 엔트리는 SKILL 경로·트리거 확정 후 |
| Step 1·4·6 → Step 9 | install chmod는 backlog-tool run.sh 존재 전제 |
| Step 1·2·3 → Step 10 | 단위 테스트는 구현 완료 후 |
| Step 9 → Step 12 | 배포 검증은 install 스크립트 확정 후 |
| Step 12 → Step 13 | 드라이런은 전체 배포 완료 후 (E2E) |
| Step 6·7·8 → Step 14·15 | docs 갱신은 스킬·레지스트리 확정 후 (PM 직접) |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | backlog-tool 6서브명령 + JSON 계약 + tool-gated | TS-001~007, TS-001b | 전 서브명령 GREEN, BACKLOG.md=JSON 미러, exit code 규정 |
| F-002 | scenario-* 4서브명령 + RED-first 동결 + 회귀 | TS-010~014 | RED 게이트 동작, 기존 4서브명령 불변 |
| F-003 | state-tool oppl enum + 회귀 | TS-020~022 | `--skill oppl` 수용, 기존 8스킬 불변 |
| F-004 | evaluator verdict-only + 결과 계약 | TS-030~034 | 소스 미변경, {item,result,reason,suggestion}+verdict |
| F-005 | references 4종 섹션·용어 | TS-040~041 | 필수 섹션 완비, 명칭 구분 준수 |
| F-006 | oppl SKILL 2-루프·3-way·디스패치·종료조건 | TS-050~056 | 전 산출물 검사 통과 |
| F-007 | 레지스트리 oppl·evaluator 등록 | TS-060~062 | JSON 유효·validate 통과·매핑 정합 |
| F-008 | install 배포 반영 | TS-070~071 | 3자산+어댑터 배포, run.sh 실행권한 |
| F-009 | docs/ 갱신 | TS-080~081 | 컴포넌트·에이전트 표 반영 + 변경이력 |

### 5.2 회귀 테스트
- [ ] test-tool 기존 4서브명령(resolve/check/unit/integration) 동작 불변 (TS-014)
- [ ] state-tool 기존 8스킬 init·전 서브명령 동작 불변 (TS-022)
- [ ] 기존 오케스트레이터(oppd/opsdd/opd) 미변경 — 병행 유지 (D-1 결정4)

### 5.3 코드/문서 품질
- [ ] 신규/변경 스킬·에이전트·참조·README에 변경이력 행 추가 (KST 일시 + 태스크 번호 056) — [MUST] D-7:194-198
- [ ] run.sh @header 규칙 준수 (shell script 적용 대상 아님 주석) — [MUST] D-7:170-174
- [ ] 프로젝트 컨벤션(파일 구조·YAML frontmatter·네이밍) 준수 — D-7:51-104
- [ ] SPEC 확정 결정 무변경 준수 (설계 이탈 없음) — [MUST] D-1 §00

### 5.4 보안
- [ ] backlog_tool.py·scenario.py에 하드코딩된 토큰/시크릿 없음
- [ ] 도구가 표준 라이브러리 + date.js만 사용 (임의 subprocess·네트워크 없음)
- [ ] evaluator tools 화이트리스트 readonly (Edit/Write/커밋 없음) — H-4
- [ ] backlog.json/test-scenario.json 경로 조작(path traversal) 방지 — task-path 검증

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 15개 | 복잡 |
| 변경 파일 수 | 20+개 (신규 도구·에이전트·스킬·참조 4 + 수정 6) | 복잡 |
| 모듈 범위 | 다중 (도구·에이전트·스킬·레지스트리·install·docs) | 복잡 |
| 작업 유형 | 신규 개발 (오케스트레이터 + 도구 + 에이전트) | 복잡 |
| 외부 의존성 | 신규 도구(backlog-tool)·신규 에이전트·신규 스킬 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬 — 독립 빌딩블록):
  ├─ A1: opal-task-agent → Step 1 (backlog-tool)
  ├─ A2: opal-task-agent → Step 2 (test-tool scenario-*)
  ├─ A3: opal-task-agent → Step 3 (state-tool ext)
  ├─ A4: opal-task-agent → Step 4 (evaluator AGENT.md)
  └─ A5: opal-task-agent → Step 5 (references 4종)
Batch 2 (순차 — 통합):
  └─ A6: opal-task-agent → Step 6 (oppl SKILL)   [A1~A5 완료 후]
Batch 3 (병렬 — 등록/배포):
  ├─ A7: opal-task-agent → Step 7 (skills-registry) [A6 후]
  ├─ A8: opal-task-agent → Step 8 (agents.md)        [A4 후]
  └─ A9: opal-task-agent → Step 9 (install)          [A1·A4·A6 후]
Batch 4 (순차 — 검증):
  ├─ A10: opal-test-agent → Step 10 단위 · Step 11 회귀 [A1~A3 후]
  ├─ A11: opal-test-agent → Step 12 배포 검증          [A9 후]
  └─ A12: opal-test-agent → Step 13 드라이런 E2E        [A11 후]
Batch 5 (순차 — 문서, PM 직접):
  └─ Step 14·15 (docs/) [A6·A7·A8 후]
```
> 파일 충돌 방지: 동일 파일 수정 Step 없음(각 Step 파일 배타적). test-tool 수정(Step 2)과 state-tool 수정(Step 3)은 별도 디렉토리 — 병렬 안전.

### C-2. 스킬 요구사항
- 각 Step 워커는 해당 단계 스킬을 Read하지 않고 **본 PLAN.md의 Step 작업 내용 + §3 설계**를 직접 구현 지침으로 사용(도구·에이전트·문서 작성 태스크). 신규 스킬 갭 없음 — oppl SKILL 자체가 산출물.
- 참조 패턴: state-tool README(도구), convention/security-checker AGENT.md(에이전트), oppd/opsdd SKILL.md(오케스트레이터).

### C-3. 도구 요구사항
- CLI: `~/.opal/tools/date/date.js`(신규 도구 타임스탬프), `~/.opal/.venv/bin/python`(도구 실행), `skill-registry`(레지스트리 validate).
- MCP: 없음 (Framework 문서·Bash·Python 태스크).
- 패키지: 표준 라이브러리 + PyYAML(test-tool 기존) — 신규 설치 없음.

### C-4. 테스트 전략 (opal-test-agent)
- **단위**(Step 10): backlog-tool·scenario-*·state-tool 서브명령별 JSON/exit/전이/RED 게이트 검증. `bash run.sh <cmd>` 직접 호출 → JSON 파싱 assert.
- **회귀**(Step 11): 기존 test-tool 4서브명령·state-tool 8스킬 스모크.
- **통합 배포**(Step 12): install 실행 → 배포 파일 존재·실행권한·어댑터 assert.
- **E2E 드라이런**(Step 13): oppl 설계 루프→실행 루프 1태스크 완주, 3-SSOT 갱신·검증 2원화 순서·종료 판정 evidence.
- 코드 품질: `bash -n scripts/install-mac.sh`(문법), python `-m py_compile`(도구).
- 보안: 하드코딩 시크릿 스캔, evaluator tools readonly 확인.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python 3.8+ (표준 라이브러리), Bash 래퍼 | state-tool/test-tool 패턴 |
| 오케스트레이터·에이전트·참조 | Markdown, YAML frontmatter | oppd/opsdd/checker 선례 |
| 레지스트리 | JSON (skills-registry), Markdown (agents.md) | - |
| 배포 | Bash (install-mac.sh) | 디렉토리 구동 + chmod 블록 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | Framework 문서·Bash·Python 태스크 — 외부 라이브러리 API 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | SPEC (확정본) | `tasks/056-260710-opd-oppl-루프-오케스트레이터/SPEC.html` | 워크플로우·에이전트·검증·3-SSOT·루프제어 확정 SSOT |
| D-2 | 설계 | TASK.md | `tasks/056-260710-opd-oppl-루프-오케스트레이터/TASK.md` | 명확화 4요소·제약·완료기준 |
| D-3 | 설계 | ANALYSIS.md | `tasks/056-260710-opd-oppl-루프-오케스트레이터/ANALYSIS.md` | 기존 컴포넌트 분석·영향 범위 |
| D-4 | 설계 | REQUEST-DRAFT.md | `tasks/056-260710-opd-oppl-루프-오케스트레이터/REQUEST-DRAFT.md` | 폴더 구조·명칭 충돌 정리·에이전트 구성표 |
| D-5 | 기획 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 구성·컴포넌트 표·네이밍 |
| D-6 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 서브에이전트·오케스트레이터·배포 모델 |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 구현 규칙(Guards/@header/State/배포경계/플랫폼분기/변경이력) |
| D-8 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | 도구 서브명령·에러코드·종료코드 패턴 |
| D-9 | 소스 | state-tool run.sh | `opal/tools/state-tool/run.sh` | .venv python 래퍼 패턴 |
| D-10 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 디스패치·JSON 헬퍼·date.js·스키마·마크다운 렌더 (`:1816-1817` skill enum) |
| D-11 | 소스 | test-tool README | `opal/tools/test-tool/README.md` | 서브명령·에러코드·1회 실행 계약 |
| D-12 | 소스 | test_tool.py | `opal/tools/test-tool/test_tool.py` | argparse+dict 디스패치(`:196-249`)·JSON 헬퍼(`:60-76`)·lib 모듈 |
| D-13 | 소스 | opal-convention-checker AGENT.md | `opal/agents/opal-convention-checker/AGENT.md` | checker 패턴 B (readonly·자기완결 보고서) |
| D-14 | 소스 | opal-security-checker AGENT.md | `opal/agents/opal-security-checker/AGENT.md` | Base+문서 병합·verdict·진단 전담 |
| D-15 | 소스 | oppd SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md` | 오케스트레이터 골격·Harness·모드 절 |
| D-16 | 소스 | opsdd SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md` | EXECUTE-LOOP(`:198-254`)·in-file SSOT 행 테이블(`:343-373`)·STATE init |
| D-17 | 소스 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 엔트리·트리거·changelog 형식 (`:134-147` oppd 선례) |
| D-18 | 소스 | agents.md | `opal/core/references/agents.md` | 에이전트 섹션·매핑 테이블·변경이력 (`:137-151`) |
| D-19 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 디렉토리 배포 루프(`:1058-1112`)·chmod 블록(`:1114-1171`)·어댑터 |
| D-20 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 규칙·MUST 토큰·decision_required |

> 인용 형식: citation-rules.md §3.1 (→ D-20). 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | state-tool `--skill` enum에 oppl 미포함 (H-1) | F-003 | P0 — 오케스트레이터 진입 실패 | Step 3에서 enum+schema 확장 선행, TS-020 L2 의무 |
| R-2 | scenario-lock RED 미확인 동결 (H-2) | F-002 | P0 — self-confirming | RED-first 게이트 강제(§3.2.2), TS-011 L1+L2 의무 |
| R-3 | evaluator mutate 위반 (H-4) | F-004 | P0 — 헌법 위반 | tools readonly 화이트리스트, changed_files 보고서만, TS-030 검증 |
| R-4 | 루프 종료조건 가드 부재 (H-7) | F-006 | P0 — 무한루프/비용 | loop-control.md 5종 가드, 드라이런 무진전 시나리오 TS-055/S-055 |
| R-5 | 검증 2원화 순서 역전 (H-9) | F-006, F-004 | P1 — 게이트 무력화 | 파이프라인에 G(구현 전)→T4a(구현 후) 명시, 드라이런 evidence TS-090 |
| R-6 | 명칭 혼동 BACKLOG.md ↔ 태스크 PLAN.md (H-12, 용어 일관성 §7.1) | F-005, F-006 | P2 | 확정 명칭(D-1 결정3) 준수, references·SKILL 용어 grep TS-041 |
| R-7 | install 실행권한 누락 (H-11) | F-008, F-001 | P1 | run.sh git 755 + chmod 블록 병행, TS-071 |
| R-8 | 기존 도구 회귀 | F-002, F-003 | P1 | scenario-* 격리(lib/scenario.py), enum 추가만, TS-014·TS-022 회귀 |

> **용어 일관성 검토 결과 (citation-rules.md §7)**: `BACKLOG.md`(프로젝트 백로그) ↔ 태스크별 `PLAN.md`(미시 설계)는 REQUEST-DRAFT.md §4에서 명칭 충돌로 식별되었고 SPEC 결정3에서 별개 명칭으로 확정 완료 (→ D-4 §4, D-1 §08 결정3). decision_required 에스컬레이션 불요(설계 루프에서 잠금). 신규 용어 불일치 추가 검출 없음.
