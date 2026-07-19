# PLAN: oppl 계약 접합면 검증 강화 — 표면 인벤토리·커버리지·전수 conformance·충실도 게이트·여정 스모크

> 작성일: 2026-07-18 | 입력: TASK.md (R-0~R-8), ANALYSIS.md (변경지점·리스크 R-A~R-H·미해결 질문 6건)
> 모드: Multi-Feature (기능 10개) | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

oppl의 완료 판정이 "테스트가 어떤 충실도(사용자 실제 접촉 방식과 같은가)로 실행됐는지"를 반영하지 못해 목·비브라우저·서버 미기동 GREEN이 모두 "verified"로 집계되는 근본 갭을 봉쇄한다. **증거 충실도(Evidence Fidelity) 원칙**을 검증 규범으로 명문화하고, 계약 표면(surface) 전수 커버리지와 함께 **도구 거부(exit code + error 필드)로 집행**한다 — 열거된 결함(auth·CORS·envelope)뿐 아니라 미열거 결함 클래스까지 구조적으로 재발 불가능하게 만든다.

### 1.2 참조 문서 핵심 제약 (PLAN 설계에 직접 영향 — [MUST] 인용)

- [MUST] `opal/skills/opal-pilot-project-loop/SKILL.md` §44: "세 SSOT는 서로 참조하지 않는다(축 분리)." — R-3/R-4 교차 판정 로직 소유 위치의 상위 제약 (→ M-2).
- [MUST] `~/.opal/PRINCIPLES.md` Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." — R-2/R-3/R-4/R-5는 반드시 도구 거부로 집행 (→ F-003~006).
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`)에서 수행한다." — 전 Step은 소스만 수정, install은 범위 외.
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm`(KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함." — R-7 집행 근거.
- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 = English." — 신규 필드는 `covers`/`fidelity`/`required_fidelity`/`surface_ref` 영문 스네이크.
- [MUST] `opal/tools/backlog-tool/backlog_tool.py:14`: "표준 라이브러리만 import (신규 패키지 도입 금지, T-11 원칙 준용)." — surfaces IR을 JSON으로 확정한 근거 (→ M-1). PyYAML은 test-tool `resolve` 한정 사용.

### 1.3 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 성격 | 우선순위 | 의존 |
|------|--------|-------------|------|---------|------|
| F-001 | 증거 충실도 원칙·검증 규범 명문화 | R-0 | 문서 | P0 | 없음 |
| F-002 | 표면 인벤토리 규칙 + surfaces IR 확정 | R-1 | 문서(+IR 스펙) | P0 | 없음 |
| F-003 | backlog-tool `covers` 필드 | R-2 | 도구 | P0 | F-002 |
| F-004 | 커버리지 게이트 (`coverage-check`) | R-3 | 도구 | P0 | F-002, F-003 |
| F-005 | 충실도 필드 + 게이트 (`scenario-fidelity-check`) | R-5 | 도구 | P0 | F-001 |
| F-006 | conformance 전수 판정 + 실 API 실행 규범 | R-4 | 도구+문서 | P0 | F-002, F-005 |
| F-007 | 여정 스모크 게이트 | R-6 | 문서 | P1 | F-001 |
| F-008 | 워킹 스켈레톤 최우선 태스크 의무 | R-8 | 문서(+판정항목) | P1 | F-002 |
| F-009 | Evaluator·루프 액션 에이전트 AGENT.md 확장 | R-1·R-5·R-8 집행 | 에이전트 | P0 | F-002, F-005, F-008 |
| F-010 | 변경이력·상호 참조 정합 | R-7 | 문서 | P1 | 전체 |

### 1.4 기능 의존 그래프 (ASCII)

```
F-001 ─┬────────────────────→ F-005 ──────────────┐
       └→(F-007)                                   ├→ F-006 ─┐
F-002 ─┬→ F-003 → F-004 ──────────────────────────┘         │
       ├→ F-008 ───────────────┐                            │
       └→(F-006 표면 분모)       └→ F-009 ←── F-005          │
F-007 (독립 문서)                                            │
                                          전체 완료 ─────────┴→ F-010
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력. 게이트 거부 경로 실증(에러 코드 실관찰)과 회귀 0을 반드시 가설화한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-004 `coverage-check` 거부 경로 | 미커버 표면 존재 시 `ok:false`+`surface_uncovered` exit 1 반환 계약 | P0 | L1(단위)+게이트 실관찰 | S-covers-uncovered |
| H-2 | F-004 통합 태스크 게이트 | parallel_group 존재 + area=통합 태스크 부재 시 `integration_task_missing` exit 1 | P0 | L1+게이트 실관찰 | S-integration-missing |
| H-3 | F-005 `scenario-fidelity-check` 거부 | 실제 충실도 < 요구 충실도 시나리오 존재 시 `fidelity_unmet` 전용 exit code | P0 | L1+게이트 실관찰 | S-fidelity-unmet |
| H-4 | F-006 `scenario-conformance` 거부 | 표면 1개라도 통과 conformance 시나리오 부재 시 `surface_unverified` all_green:false | P0 | L1+게이트 실관찰 | S-surface-unverified |
| H-5 | F-003 `covers` 하위 호환 | `--covers` 미지정 기존 add-task 호출이 그대로 동작(covers 없이 append) | P0 | L1 회귀 | S-covers-omitted-compat |
| H-6 | F-005 fidelity 하위 호환 | `required_fidelity`/`fidelity` 미지정 기존 test-scenario.json이 mock 기본값으로 로드·통과(회귀 0) | P0 | L1 회귀 | S-fidelity-default-mock |
| H-7 | F-004/F-006 축 분리 | backlog-tool이 test-scenario.json을, test-tool이 backlog.json을 파싱하지 않음(Grep 무검출 유지) | P1 | L1 정적 검사 | S-axis-separation |
| H-8 | F-003·F-005 스키마 additive | schema `required`/`additionalProperties:false` 갱신 후 기존 9/9·TestCase 회귀 0 | P0 | L1 전 테스트 스위트 | S-tool-regression-zero |
| H-9 | F-006 CORS 결정론 규범 | origin 선언 시 conformance가 Origin+preflight(OPTIONS) 헤더를 계약과 대조하는 규범이 verification.md에 명시 | P1 | L3(문서 정합) | S-cors-norm |
| H-10 | F-002 surfaces IR 단일 인터페이스 | 게이트 도구가 surfaces.json(JSON) 단일 구조만 소비(YAML/markdown 파서 분기 없음) | P1 | L1 정적 검사 | S-single-interface |
| H-11 | F-009 fidelity 요구 주입 (R-G) | 루프 액션 에이전트가 T2 test-agent에 요구 충실도 미주입 시 mock 시나리오만으로 게이트 통과하는 사각지대 | P1 | L3(프롬프트 정합) | S-fidelity-injection |

---

## 2. 기능별 분석

> ANALYSIS.md 존재 → F-NNN별 간략 작성 (ANALYSIS §1 관련 파일·§4 핵심 발견·§7 미해결 질문 참조).

### F-001: 증거 충실도 원칙·검증 규범 명문화

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | 검증 3-tier+2원화 가이드 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 검증 2원화 절 | 수정 |

#### 2.1.2 현재 구현
`verification.md`는 §2 결정론/루브릭/사람 3-tier와 §3 2원화만 규정하며 "충실도" 개념이 없다 (→ D-3 §2.1·§3). §2.1 "계약 conformance" 행은 "스키마·시그니처 일치"만 요구하고 분모(전 표면)·실행 환경(목 vs 실 서버) 개념이 없다 (`verification.md:38`).

#### 2.1.3 영향 범위
F-005(충실도 게이트)·F-006(conformance)·F-007(여정 스모크)이 이 규범을 집행 근거로 인용한다. R-0 AC: "R-5의 도구 게이트가 이 규범을 집행 근거로 인용한다."

### F-002: 표면 인벤토리 규칙 + surfaces IR 확정

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-project-loop/references/contract.md` | CONTRACT 거버넌스 §2.1 경계·§2.2 기계검증절 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D4 CONTRACT 작성 절 | 수정 |

#### 2.2.2 현재 구현
`contract.md` §2.1은 스키마·시그니처·경계 3파트만 규정, §2.2 기계검증절은 "결정론 검증 가능 항목을 모은 절"이라는 서술만 있고 표면 전수 나열 의무·auth·origin 규칙이 없다 (→ D-2 §2.1·§2.2). 순수 마크다운이라 JSON/YAML 블록이 없다(ANALYSIS §4-2).

#### 2.2.3 영향 범위
F-003(`--covers <surface-id>`)의 surface-id 정의역, F-004(커버리지 게이트)의 분모, F-006(conformance)의 표면 분모가 모두 이 IR에 의존한다(ANALYSIS §5 R-C 순서 의존성 — F-002 선행 필수).

### F-003: backlog-tool `covers` 필드

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/backlog-tool/backlog_tool.py` | add-task/update-task argparse·본문 | 수정 |
| 환경 | `opal/tools/backlog-tool/schema/backlog.schema.json` | tasks[] 스키마 | 수정 |
| 문서 | `opal/tools/backlog-tool/README.md` | 옵션·필드 문서 | 수정 |
| 도구 | `opal/tools/backlog-tool/tests/test_backlog_tool.py` | 단위 테스트 | 수정 |

#### 2.3.2 현재 구현
`add-task`는 `cmd_add_task`에서 new_task dict를 조립(`backlog_tool.py:335-347`), argparse는 `p_add`(`:597-607`). `update-task`는 `_UPDATE_TASK_FIELDS` 튜플(`:432`)로 갱신 대상을 화이트리스트한다. `render_backlog_table`(`:200-215`)이 BACKLOG.md 표 컬럼을 구성한다. 스키마는 `additionalProperties:false` + `required` 배열(`backlog.schema.json:44-49`).

#### 2.3.3 영향 범위
`covers`는 optional additive 필드 — `update-task`의 `_UPDATE_TASK_FIELDS`, schema `required`(추가 안 함 — optional), render 표 컬럼에 영향. ANALYSIS §4-4: additive 패턴(update-task 056 ADD-3)이 회귀 0 선례.

### F-004: 커버리지 게이트 (`coverage-check`)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/backlog-tool/backlog_tool.py` | 신규 서브명령 `coverage-check` | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D5/D7/L✓ 게이트 호출 | 수정 |
| 문서 | `opal/tools/backlog-tool/README.md` | 서브명령·에러코드 | 수정 |
| 도구 | `opal/tools/backlog-tool/tests/test_backlog_tool.py` | 단위 테스트 | 수정 |

#### 2.4.2 현재 구현
`ERROR_CODES` 딕셔너리(`backlog_tool.py:42-54`)가 에러 SSOT, `err()` 헬퍼(`:68-82`)가 `{ok:false,command,error,message}` 단일라인 JSON + exit code 반환. 읽기 전용 서브명령(`select-next`·`done-check`)은 `load_backlog_json`(비락)만 사용(`:363-385`, `:512-526`). backlog.json 전체에 `test-scenario`/`scenario` 토큰 미등장(ANALYSIS §1.3 Grep 무검출) — 축 분리가 코드 수준 유지.

#### 2.4.3 영향 범위
`coverage-check`는 backlog.json(자기 SSOT) + surfaces.json(CONTRACT 도메인 IR)만 읽는다 — test-scenario.json 미접촉으로 축 분리 정신 유지(→ M-2). 읽기 전용이므로 fcntl 락 불필요(ANALYSIS §1.2).

### F-005: 충실도 필드 + 게이트 (`scenario-fidelity-check`)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/test-tool/lib/scenario.py` | fidelity 필드·게이트 핸들러 | 수정 |
| 환경 | `opal/tools/test-tool/schema/test-scenario.schema.json` | scenarios[] 스키마 | 수정 |
| 문서 | `opal/tools/test-tool/README.md` | 필드·서브명령·에러코드 | 수정 |
| 도구 | `opal/tools/test-tool/tests/test_scenario.py` | 단위 테스트 | 수정 |

#### 2.5.2 현재 구현
`_normalize_scenario`(`scenario.py:109-131`)가 spec존/result존 필드를 정규화하며 `red_confirmed`를 항상 false 강제. `scenario-mark`(`:217-246`)가 result존(result/evidence/marked_at) 기록. `SCENARIO_ERROR_CODES`(`:53-59`)가 exit 8~12 전용 카탈로그. `scenario-lock`(`:187-214`)은 **전 시나리오 red_confirmed==true 전부-게이트** — ANALYSIS §4-3/R-B: task:061 혼합 트랙 붕괴 선례.

#### 2.5.3 영향 범위
`required_fidelity`(spec존)/`fidelity`(result존)는 additive. 스키마 참조용(런타임 미검증)이라 기존 파일 로드 무파손이나, 게이트 로직이 `.get(...,"mock")` 방어 기본값을 쓰지 않으면 R-E(기존 프로젝트 즉시 붕괴). `scenario-fidelity-check`는 **시나리오별 부분 게이트** — `scenario-lock` 전부-게이트를 물려받지 않는다(→ M-3).

### F-006: conformance 전수 판정 + 실 API 실행 규범

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/test-tool/lib/scenario.py` | 신규 `scenario-conformance` + `surface_ref` | 수정 |
| 환경 | `opal/tools/test-tool/schema/test-scenario.schema.json` | scenarios[] `surface_ref` | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §2.1 conformance 분모·실행방식·CORS | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | L✓ 종료 판정 | 수정 |
| 문서 | `opal/tools/test-tool/README.md` | 서브명령·에러코드 | 수정 |
| 도구 | `opal/tools/test-tool/tests/test_scenario.py` | 단위 테스트 | 수정 |

#### 2.6.2 현재 구현
`scenario-status`(`scenario.py:285-307`)가 total/red_confirmed/passed/failed 집계. `_load_spec`(`:95-101`)가 test-scenario.json 로드. L✓ 종료 판정(`SKILL.md:270-274`)은 `backlog-tool done-check`의 all_done(태스크 축)만 판정.

#### 2.6.3 영향 범위
`scenario-conformance`는 surfaces.json(분모, 읽기 전용) + 자기 test-scenario.json(result존, `surface_ref` 라벨)만 읽는다 — backlog.json 미접촉으로 축 분리 유지(→ M-2, R-A 해소). L✓ 종료는 PM이 3개 도구 불리언(done-check.all_done ∧ scenario-conformance.all_surfaces_green ∧ 회귀 0)을 AND(loop-control.md §5 도구 결과 기반 판정).

### F-007: 여정 스모크 게이트

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | 여정 스모크 게이트 절 | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §2.1 E2E(L3b) 실행 환경 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | L✓ 회귀 | 수정 |

#### 2.7.2 현재 구현
`journey-flow.md`는 USER_JOURNEY를 Loop 1 D5 분해 입력으로만 소비(§3), Loop 2/L✓ 재실행 의무 없음. §2 트리거(user-facing 여부)가 조건부 설계 선례. verification.md §2.1 E2E(L3b) 행에 실행 환경(실 브라우저) 명시 없음.

#### 2.7.3 영향 범위
비 user-facing 스킵 조건·기록 위치(VERIFICATION.md, D-3 §5.2)를 명시해야 기존 인프라/라이브러리 프로젝트 무영향.

### F-008: 워킹 스켈레톤 최우선 태스크 의무

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D5·병렬 실행 절 | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | 스켈레톤 게이트 메커니즘 | 수정 |
| 에이전트 | `opal/agents/opal-evaluator-agent/AGENT.md` | 판정 항목(F-009에서 처리) | 수정 |

#### 2.8.2 현재 구현
`SKILL.md:206` D5 백로그 생성은 슬라이스 분해만 규정, "실행 스켈레톤 최우선" 규칙 없음. `SKILL.md:490-495` 병렬 실행 절에 통합 태스크는 prose 권고.

#### 2.8.3 영향 범위
스켈레톤 존재 판정은 구조적 탐지가 취약(어느 태스크가 스켈레톤인지 도구가 알기 어려움)하므로 Evaluator 판정 항목(D6)으로 집행 — 문서 성격(→ M-4 R-8 결정). 커버리지 게이트가 스켈레톤 표면 커버를 간접 보강.

### F-009: Evaluator·루프 액션 에이전트 AGENT.md 확장

#### 2.9.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-evaluator-agent/AGENT.md` | Base 루브릭 판정 항목 | 수정 |
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | fidelity 요구 주입·게이트 호출 | 수정 |

#### 2.9.2 현재 구현
Evaluator Base 루브릭 6차원(`AGENT.md:42-49`)에 표면 완전성·auth·origin·스켈레톤 항목 없음. 루프 액션 에이전트 컨텍스트 재주입 표(`opal-loop-action-agent/AGENT.md:109-118`)에 fidelity 요구·surfaces_path 없음, 3-SSOT 호출 규칙(`:313-317`)은 test-tool scenario-*만 허용.

#### 2.9.3 영향 범위
R-F(Evaluator prose 집행은 TASK가 문서 성격으로 확정) / R-G(루프 액션 에이전트 미주입 시 mock 통과 사각지대). 신규 scenario-fidelity-check/scenario-conformance는 test-tool scenario-* 계열이라 루프 액션 에이전트 3-SSOT 경계 불변(추가 허용 불필요).

### F-010: 변경이력·상호 참조 정합

#### 2.10.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | 변경된 스킬·참조·도구 README·AGENT.md 전체 | 변경이력 표 069 행 | 수정 |
| 문서 | `docs/PROJECT.md` | 컴포넌트 설명 정합 | 수정(PM 직접) |

#### 2.10.2 현재 구현
각 문서에 "## 변경이력" 표 존재(contract.md·verification.md·journey-flow.md·loop-control.md·README·AGENT.md). PROJECT.md Project Loop 표에 backlog-tool "6서브명령"(구식) 기재(`PROJECT.md:108`) — done-check/coverage-check 반영 필요.

#### 2.10.3 영향 범위
배포 시 install-mac.sh가 스킬 변경이력을 strip(ANALYSIS §6)하므로 소스에 반드시 기록. docs/는 install 대상 아님.

---

## 3. 기능별 설계

> 각 설계 결정 뒤 인라인 인용. 신규 필드·시그니처·에러코드는 [MUST] 포맷.

### 3.0 핵심 의사결정 (M-1~M-6 — ANALYSIS §7 미해결 6건 확정)

#### M-1. 표면 인벤토리 SSOT 형식 — **구조화 단일 인터페이스 `surfaces.json`(JSON) 확정**

ANALYSIS §7 "조건부 이원화 + 구조화 단일 인터페이스" 제안을 **채택**한다 (→ D-A §7 표면 인벤토리 형식 대안 비교).

- **작성 SSOT(조건부 이원화)**: API 프로젝트는 OpenAPI(YAML) spec을 1순위 작성 원천으로 삼고(캡틴 지시 정합), 비-API 프로젝트(CLI/라이브러리/배치)는 표면 목록을 직접 작성한다. 이 분기는 **CONTRACT 작성 단계(D4, Planner)에 격리**된다.
- **게이트 소비 인터페이스(단일·파서 분기 없음)**: 커버리지·conformance 게이트 도구는 **오직 `surfaces.json`(구조화 JSON 중간 표현) 하나만** 소비한다. OpenAPI→surfaces 변환(securitySchemes→auth 포함)·비-API 직접 작성은 모두 D4에서 완료되어 surfaces.json으로 수렴한다. 도구는 YAML/markdown을 파싱하지 않는다 (H-10).
- **JSON 채택 근거**: backlog-tool은 표준 라이브러리 전용([MUST] `backlog_tool.py:14`)이라 YAML 파서(PyYAML) 도입이 금지되며, 마크다운 표 파서는 결합도 취약(→ D-A §5 R-D). JSON은 stdlib `json`으로 견고 파싱 — 신규 패키지 0.
- **surfaces.json 위치·소유**: CONTRACT 도메인 산출물(3-SSOT 밖, ANALYSIS §8)로 oppl 프로젝트 루트 `tasks/{NNN}-oppl-{프로젝트명}/surfaces.json`. CONTRACT.md §2.2 기계검증절이 이를 기계가독 표현으로 참조한다. 두 게이트 도구가 읽되 3-SSOT 일원이 아니므로 축 분리 위반이 아니다 ([MUST] `SKILL.md` §44 — 세 SSOT는 backlog/state/test-scenario 한정).

surfaces.json 구조 (contract.md에 스펙 명문):
```json
{
  "schema_version": "1.0",
  "origins": { "dev": ["http://localhost:5173"], "prod": ["https://app.example.com"] },
  "surfaces": [
    { "id": "auth-login", "resource": "POST /auth/login", "auth": "none",
      "request_shape": "{email,password}", "response_shape": "{token,user}", "kind": "http" }
  ]
}
```
- `auth`: `required|none` (인증 표면=로그인 자체도 등재, R-1). `origins`: 웹 클라이언트 존재 시만(nullable) — 경계절 CORS 근거.

#### M-2. R-3/R-4 교차 판정 로직 소유 위치 — **축별 분리, backlog-tool 외부 집계(ANALYSIS §8 권고 채택)**

3-SSOT 축 분리 정신("각 도구는 자기 SSOT만 소유") 유지를 위해 R-3와 R-4를 **다른 SSOT 소유 도구에 분리 배치**한다.

- **R-3 커버리지 게이트 → backlog-tool `coverage-check`**: backlog.json(자기 SSOT) + surfaces.json(CONTRACT 도메인, 읽기 전용)만 읽는다. `surface_uncovered`/`integration_task_missing` 거부. **test-scenario.json 미접촉** → 축 분리 유지.
- **R-4 conformance 전수 판정 → test-tool `scenario-conformance`**: surfaces.json(분모, 읽기 전용) + 자기 test-scenario.json(result존)만 읽는다. **backlog.json 미접촉** (ANALYSIS §8: "집행 지점을 backlog-tool 외부"). `all_surfaces_green` + `surface_unverified` 거부.
- **L✓ 종료 판정 = PM 불리언 AND**: PM(오케스트레이터)이 `done-check.all_done`(태스크 축) ∧ `scenario-conformance.all_surfaces_green`(표면 축) ∧ 회귀 0을 조합한다. 각 조건은 개별 도구 거부로 tool-gated이며, PM의 불리언 AND는 기존 "done-check + 회귀 0"과 동일한 정당한 오케스트레이터 제어흐름(loop-control.md §5). **어느 도구도 타 도구 SSOT를 파싱하지 않는다** (H-7, R-A 해소).

#### M-3. fidelity 게이트 구조 — **required_fidelity(요구)/fidelity(실제) 분리 + 시나리오별 부분 게이트**

task:061 재발 사례(전부-아니면-전무 게이트가 혼합 트랙에서 붕괴 — → D-B 재발 사례)를 회피한다. brain 페이지 `red_required` 패턴을 fidelity에 유비 적용(→ D-B "정제된 후속 제안").

- **필드 2종 분리**: `required_fidelity`(spec존, 작성 시 결정 — 시나리오가 반드시 검증돼야 할 충실도) / `fidelity`(result존, scenario-mark 시 기록 — 실제 검증된 충실도). 사다리 순서 `mock(0) < real-http(1) < real-usage(2)`.
- **부분 게이트(시나리오별)**: `scenario-fidelity-check`는 각 시나리오에 대해 `result==pass AND fidelity(실제) >= required_fidelity(요구)`를 판정한다. mock으로 충분한 시나리오와 real-usage 요구 시나리오가 하나의 test-scenario.json에 공존한다 — **전부-게이트를 물려받지 않는다**(R-B 해소). `scenario-lock`(RED-first)과 **통합하지 않고 독립 서브명령**으로 분리(RED 게이트와 fidelity 게이트 직교).

#### M-4. AGENT.md 변경 범위 — **두 AGENT.md 모두 변경(범위 명시)**

- **opal-evaluator-agent: 변경** — Phase 1 Base 루브릭에 판정 항목 추가: ⑦표면 완전성(surfaces.json ↔ PRD/TRD/여정 대비 누락, Likert) ⑧auth 필드 완전성(전 표면 auth 선언, binary) ⑨origin 선언(웹 클라이언트 프로젝트, binary) ⑩워킹 스켈레톤 태스크 존재·구성(R-8, binary). R-1/R-8이 "문서 성격"으로 확정(TASK 확정 방향 표, R-F)되어 Evaluator prose 집행이 정당.
- **opal-loop-action-agent: 변경** — 컨텍스트 재주입 표에 `요구 충실도`(area 매핑: BE 표면=real-http↑, 사용자 접촉 표면·여정=real-usage) + `surfaces_path`를 추가하여 T1 생성자·T2 test-agent(mode:red)에 주입(R-G 사각지대 봉쇄, H-11). T4a에 `scenario-fidelity-check`/`scenario-conformance` 호출 + `fidelity_unmet`을 재작업/blocked 트리거로 편입. **3-SSOT 호출 규칙 불변**(신규 서브명령이 test-tool scenario-* 계열).

#### M-5. fidelity 하위 호환 기본값 — **미지정 시 `mock` (요구·실제 양쪽)**

- `required_fidelity` 미지정 → `mock`(기존 시나리오는 mock만 요구 — 소급하여 엄격해지지 않음).
- `fidelity`(실제) 미지정 → `mock`(충실도 미기록 결과는 목 수준으로 간주 — 보수적).
- 순효과: 기존 test-scenario.json(양 필드 부재) → `mock >= mock` → conformant → **회귀 0**(R-E 해소). 게이트 로직은 반드시 `.get("required_fidelity","mock")`/`.get("fidelity","mock")` 방어 접근을 사용한다. surfaces.json 부재 → `scenario-conformance`는 `applicable:false`로 스킵(기존 프로젝트 무영향, journey-flow 조건부 트리거 선례).

#### M-6. 신규 게이트 에러의 loop-control.md §7 분류 — **전부 "복구가능"에 편입**

`surface_uncovered`·`integration_task_missing`·`fidelity_unmet`·`surface_unverified`를 loop-control.md §7 **복구가능(recoverable)** 행에 추가한다(기존 `red_not_confirmed`와 동렬). 근거: 완결성·충실도 갭으로 재작업(add-task / 더 높은 충실도 재검증)으로 해결 가능하며 계약/설계를 부정하지 않는다. blocked로의 전환은 기존 무진전(§4)·반복 상한(§2) 경로로만 발생(예: 스켈레톤 부재로 real-usage 반복 불가 시 no-progress → blocked). §7에 이 편입을 명시한다.

### F-001 설계

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `references/verification.md` | 가이드 | §1 신규 "증거 충실도 사다리"(mock<real-http<real-usage 정의·BE/FE 매핑·표준 실행법) + "사용자 접촉 표면/여정은 real-usage PASS≥1 없이 done 불인정" 규칙 | (→ D-3 §2·§3) |
| 2 | `SKILL.md` | 오케스트레이터 | 검증 2원화 절에 충실도 규범 인라인 참조 1줄 | `SKILL.md:383` |

#### 3.1.2 설계
verification.md §1 신설 — 충실도 3단계 (→ D-3):
- `mock`: 목 상대 테스트 코드(단위 수준). `real-http`: 실 서버 기동 + 계약 spec 기반 실 HTTP 전수 conformance(스웨거/OpenAPI 방식, auth 토큰 체인 포함). `real-usage`: 실 브라우저(cmux browser 우선/playwright 폴백) E2E — 실 진입점·실 데이터 흐름.
- BE 매핑: 단위=테스트 코드 / 통합=spec 기반 실 HTTP. FE 매핑: 단위=목 허용 컴포넌트 테스트 / 통합=실 브라우저×실 BE.
- [MUST] 규범 원문(verification.md에 명문): "완료(done)의 최종 증거는 사용자가 실제 접촉하는 방식과 같은 충실도에서 관찰된 것만 인정한다. 사용자 접촉 표면·여정은 real-usage PASS ≥1 없이 done을 인정하지 않는다."
- [MUST] conformance 실행 주체 명시: oppl 프레임워크 도구는 규범·게이트만 정의하며, 실 HTTP 호출·브라우저 E2E "실행"의 주체는 대상 프로젝트의 test-agent다(프레임워크 도구가 HTTP를 직접 구현하지 않음).

#### 3.1.3 환경 변경 / 3.1.4 배치·마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-0 AC | 산출물 검사 | verification.md §1에 충실도 3단계 정의·단계별 표준 실행법·real-usage done 규칙이 존재 |
| TS-002 | R-0 AC | 산출물 검사 | R-5 게이트 절이 이 규범을 집행 근거로 인용 |

### F-002 설계

#### 3.2.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `references/contract.md` | 가이드 | §2.2에 표면 인벤토리 필수 규칙 + surfaces.json 구조 스펙(id·resource·auth·request/response_shape) + §2.1 경계절에 허용 origin 선언 의무 | (→ D-2 §2.1·§2.2) |
| 2 | `SKILL.md` | 오케스트레이터 | D4 디스패치 프롬프트에 "surfaces.json 생성(auth 포함) + origin 선언" 요구 | `SKILL.md:204` |

#### 3.2.2 설계
- [MUST] contract.md §2.2 원문: "CONTRACT.md 기계검증절은 기계가독 표면 인벤토리(`surfaces.json`)를 필수 포함한다 — 각 표면은 `id`·`resource`·`auth(required|none)`·요청/응답 형태를 선언하며, 인증 표면(로그인) 자체도 표면으로 등재한다."
- [MUST] contract.md §2.1 경계절 원문: "웹 클라이언트가 존재하는 프로젝트는 허용 origin(개발·운영)을 경계절에 선언한다(`surfaces.json` `origins`) — CORS 결정론 검사의 계약 근거."
- surfaces.json 구조는 M-1 참조. API 프로젝트는 OpenAPI(YAML)에서 파생, 비-API는 직접 작성 — 분기는 D4에 격리.
- 게이트 도구가 소비하는 인터페이스는 surfaces.json 단일(파서 분기 없음, H-10).

#### 3.2.3 환경 / 3.2.4 배치
해당 없음(신규 외부 패키지 0).

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-1 AC | 산출물 검사 | contract.md §2.2에 표면 인벤토리 필수 규칙·형식(auth 포함), §2.1에 origin 선언 규칙 존재 |
| TS-011 | R-1 AC | 산출물 검사 | SKILL.md D4가 surfaces.json+origin을 요구 |

### F-003 설계

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `backlog_tool.py` | 도구 | `p_add`/`p_upd`에 `--covers <json-array>` 추가, `cmd_add_task`/`cmd_update_task`에 covers 파싱·기록, `_UPDATE_TASK_FIELDS`에 covers 추가, `render_backlog_table`에 covers 컬럼 | `backlog_tool.py:335,432,200,597,622` |
| 2 | `schema/backlog.schema.json` | 환경 | tasks[].properties에 `covers`(array of string, optional) 추가, schema_version 1.0→1.1 | `backlog.schema.json:50,9` |
| 3 | `README.md` | 문서 | add-task/update-task covers 옵션 문서 | `README.md:55,122` |
| 4 | `tests/test_backlog_tool.py` | 도구 | covers 기록·미지정 회귀 테스트 | `test_backlog_tool.py:136` |

#### 3.3.2 API·데이터 모델 설계
- [MUST] 신규 필드: `covers` — 태스크가 커버하는 표면 id 배열. `add-task --covers '["auth-login","agents"]'`.
- new_task dict에 `"covers": covers or []` 추가(`cmd_add_task`). JSON 파싱 실패 → 기존 `acceptance_invalid_json` 재사용 or 신규 `covers_invalid_json`. **결정**: 신규 `covers_invalid_json` 추가(에러 명확성). 미지정 → `[]`(하위 호환, H-5).
- `update-task`: `_UPDATE_TASK_FIELDS`에 `"covers"` 추가 — tool-gated 갱신 경로.
- `render_backlog_table`: "커버 표면" 컬럼 추가(`", ".join(covers) or "-"`). BACKLOG.md 미러 렌더(R-2 AC).
- schema: `covers`는 optional(required 배열에 추가 안 함 → 기존 파일 무파손). schema_version const "1.0"→"1.1"(신규 필드 추가 시 상향 규정, `backlog.schema.json:9`). 단 런타임 미검증이라 기존 파일 로드 무영향. init 시 생성되는 schema_version도 "1.1"로 상향할지: **기존 backlog.json은 "1.0" 유지하여 로드 무파손**, 신규 init만 "1.1"(cmd_init dict `schema_version` 값 갱신).

#### 3.3.3 환경 / 3.3.4 배치
run.sh는 argparse 위임(`exec ... "$@"`)이라 신규 옵션 자동 인식 — 별도 wrapper·chmod 불필요(ANALYSIS §5·§6).

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R-2 AC | 기능 테스트 | `add-task --covers '["s1"]'` → backlog.json tasks[].covers==["s1"] + BACKLOG.md에 렌더 |
| TS-021 | R-2 AC | 회귀 테스트 | `--covers` 미지정 add-task → covers==[] 기록·정상 동작(H-5) |
| TS-022 | R-2 AC | 기능 테스트 | `update-task --covers '["s2"]'` → covers 갱신 |
| TS-023 | R-2 AC | 회귀 테스트 | 기존 9 TestCase 전부 pass(회귀 0, H-8) |

### F-004 설계

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `backlog_tool.py` | 도구 | 신규 `cmd_coverage_check` + `p_cov` 서브파서, ERROR_CODES에 신규 3종 | `backlog_tool.py:42,510,635` |
| 2 | `SKILL.md` | 오케스트레이터 | D5/D7에 coverage-check 게이트 호출, L✓에 표면 축 조합 | `SKILL.md:206,227,270` |
| 3 | `README.md` | 문서 | coverage-check 서브명령·에러코드 표 | `README.md:33,189` |
| 4 | `tests/test_backlog_tool.py` | 도구 | 미커버·통합부재·전커버 통과 테스트 | `test_backlog_tool.py:136` |

#### 3.4.2 API·시그니처 설계
- [MUST] 신규 서브명령: `coverage-check <task-path> --surfaces <surfaces.json 경로>` (읽기 전용, fcntl 락 없음).
- `def cmd_coverage_check(args)`: `load_backlog_json`(비락) + surfaces.json을 `json.load`로 로드(파일 부재 → `surfaces_file_not_found` exit 1).
  - 커버 집합 = ∪ tasks[].covers. 표면 집합 = surfaces[].id.
  - `uncovered = 표면집합 - 커버집합`. 비어있지 않으면 `err("coverage-check","surface_uncovered", uncovered=[...])` exit 1.
  - parallel_group이 하나라도 존재하고 area=="통합" 태스크가 없으면 `err(...,"integration_task_missing", groups=[...])` exit 1.
  - 전 표면 커버 + (통합 필요 시)통합 존재 → `ok("coverage-check", all_covered=True, surface_count=N)`.
- [MUST] ERROR_CODES 신규 3종(딕셔너리 추가, exit 1): `surface_uncovered`("미커버 표면 존재: {uncovered}"), `integration_task_missing`("parallel-group 존재하나 통합 태스크(area=통합) 부재: {groups}"), `surfaces_file_not_found`("surfaces.json 부재: {path}").
- **축 분리 준수**: 함수 본문에 `test-scenario`/`scenario` 토큰 미도입(H-7).

#### 3.4.3 환경 / 3.4.4 배치
argparse 위임 — install 무변경.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-3 AC | 기능 테스트 | 미커버 표면 상태 → `ok:false`+`surface_uncovered` exit 1 실관찰(H-1) |
| TS-031 | R-3 AC | 기능 테스트 | parallel_group 존재+통합 태스크 부재 → `integration_task_missing` exit 1(H-2) |
| TS-032 | R-3 AC | 기능 테스트 | 전 표면 커버+통합 존재 → `all_covered:true` exit 0 |
| TS-033 | R-3 AC | 보안/정적 | coverage-check 함수에 test-scenario 파싱 없음(축 분리, H-7) |

### F-005 설계

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `lib/scenario.py` | 도구 | `_normalize_scenario`에 required_fidelity/fidelity 기본값, `scenario-mark`에 `--fidelity`, 신규 `cmd_scenario_fidelity_check`+서브파서, `SCENARIO_ERROR_CODES`+`FIDELITY_ORDER` | `scenario.py:53,109,217,314` |
| 2 | `schema/test-scenario.schema.json` | 환경 | scenarios[]에 `required_fidelity`/`fidelity` enum 추가 | `test-scenario.schema.json:34,54` |
| 3 | `README.md` | 문서 | fidelity 필드·scenario-fidelity-check·에러코드 | `README.md:142,239` |
| 4 | `tests/test_scenario.py` | 도구 | fidelity 게이트·기본값 회귀 테스트 | `test_scenario.py:1` |

#### 3.5.2 데이터 모델·시그니처 설계
- [MUST] 필드 사다리: `FIDELITY_ORDER = {"mock":0, "real-http":1, "real-usage":2}` (scenario.py 상수).
- [MUST] `required_fidelity`(spec존): `_normalize_scenario`에서 `raw.get("required_fidelity","mock")`, 알 수 없는 값 → "mock" 강등 + warning(관대 기본값, R-E/M-5). scenario-init 시 결정(locked 이전 고정 — spec존, ANALYSIS §1.2 spec/result 분리).
- [MUST] `fidelity`(result존): `scenario-mark --fidelity <mock|real-http|real-usage>`(argparse choices) → target["fidelity"] 기록. 미지정 → "mock"(M-5).
- [MUST] 신규 서브명령: `scenario-fidelity-check --task-path <PATH>` — **시나리오별 부분 게이트**:
  - 각 시나리오에 대해 `req = s.get("required_fidelity","mock")`, `act = s.get("fidelity","mock")`, `res = s.get("result")`.
  - unmet = [s.id for s if not(res=="pass" and FIDELITY_ORDER[act] >= FIDELITY_ORDER[req])].
  - unmet 비어있지 않으면 `_error("fidelity_unmet","scenario-fidelity-check",13, detail=unmet)`.
  - 통과 → `{ok:true, all_met:true, total, met}`.
- [MUST] `SCENARIO_ERROR_CODES` 신규: `fidelity_unmet`(exit 13, "요구 충실도 미달 시나리오 존재: {unmet}"). 기존 8~12과 충돌 없음(격리 원칙, `scenario.py:29-31`).
- 스키마: `required_fidelity`/`fidelity` enum `["mock","real-http","real-usage"]`. **required 배열에 추가하지 않음**(optional → 기존 파일 무파손, H-6). `additionalProperties:false`라 신규 필드는 properties에 등록 필요(등록만 하면 기존 파일 로드 무영향 — 런타임 미검증).

#### 3.5.3 환경 / 3.5.4 배치
run.sh argparse 위임 — install 무변경.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R-5 AC | 기능 테스트 | required_fidelity=real-usage, fidelity=mock,result=pass → `fidelity_unmet` exit 13(H-3) |
| TS-051 | R-5 AC | 기능 테스트 | required=real-http, fidelity=real-http,result=pass → all_met exit 0 |
| TS-052 | R-5 AC | 기능 테스트 | 혼합 트랙(mock-요구 + real-usage-요구) 각자 충족 → 통과(부분 게이트, R-B) |
| TS-053 | R-5 AC | 회귀 테스트 | fidelity 미지정 기존 test-scenario.json → mock>=mock → 통과(H-6) |
| TS-054 | R-5 AC | 회귀 테스트 | 기존 scenario-* 테스트 전부 pass(H-8) |

### F-006 설계

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `lib/scenario.py` | 도구 | `_normalize_scenario`에 `surface_ref`, 신규 `cmd_scenario_conformance`+서브파서, 에러코드 2종 | `scenario.py:109,285,314` |
| 2 | `schema/test-scenario.schema.json` | 환경 | scenarios[]에 `surface_ref`(nullable string) | `test-scenario.schema.json:34` |
| 3 | `references/verification.md` | 가이드 | §2.1 계약 conformance 행에 분모(표면 전수)·실행방식(실 서버·실 HTTP·auth 토큰 체인)·CORS 검사 명시 | (→ D-3 §2.1) |
| 4 | `SKILL.md` | 오케스트레이터 | L✓ 종료 판정에 scenario-conformance 조합 | `SKILL.md:270` |
| 5 | `README.md` | 문서 | scenario-conformance·에러코드 | `README.md:239` |
| 6 | `tests/test_scenario.py` | 도구 | conformance 미검증·전green·surfaces부재 스킵 테스트 | `test_scenario.py:1` |

#### 3.6.2 시그니처·규범 설계
- [MUST] `surface_ref`(spec존, nullable): 시나리오가 검증하는 표면 id. `_normalize_scenario`에서 `raw.get("surface_ref")`.
- [MUST] 신규 서브명령: `scenario-conformance --task-path <PATH> --surfaces <surfaces.json>`:
  - surfaces.json 부재 → `{ok:true, applicable:false}` exit 0 (스킵 — 기존 프로젝트·비-API 무영향, M-5).
  - 각 표면 s.id에 대해: 통과 조건 = ∃ 시나리오 with `surface_ref==s.id AND result=="pass" AND fidelity >= (s.auth=="required"? real-http : 요구충실도)`. auth 표면은 real-http↑ 강제(R-4b auth 토큰 체인 — 규범은 verification.md, 게이트는 fidelity>=real-http로 근사).
  - unverified = 통과 조건 미충족 표면. 비어있으면 `{ok:true, all_surfaces_green:true, surface_count}`; 아니면 `_error("surface_unverified","scenario-conformance",14, detail=unverified)` (all_surfaces_green:false).
- [MUST] 에러코드: `surface_unverified`(14), `surfaces_file_not_found`(15) — 기존 8~13과 충돌 없음.
- [MUST] verification.md §2.1 계약 conformance 행 원문: "분모=표면 인벤토리(surfaces.json) 전수. 실행 방식=실 서버 기동+실 HTTP로 응답 형태를 계약과 대조하며, `auth:required` 표면은 실 로그인 토큰 체인(로그인→토큰→Authorization 헤더)으로 호출해야 결과 인정(목·핸들러 단위 테스트 대체 불인정). origin 선언 시 표면 전수에 Origin 헤더 요청 + preflight(OPTIONS)를 보내 `Access-Control-Allow-*`를 계약과 대조(CORS 결정론 검사)."
- **축 분리**: scenario-conformance 본문에 backlog.json/`backlog` 토큰 미도입(H-7).

#### 3.6.3 환경 / 3.6.4 배치
argparse 위임 — install 무변경. HTTP 호출·CORS 실행은 대상 프로젝트 test-agent 소관(프레임워크 도구 미구현 — TASK 유의사항).

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | R-4 AC | 기능 테스트 | 표면 1개 결과 미기록 → `surface_unverified`+all_surfaces_green:false(H-4) |
| TS-061 | R-4 AC | 기능 테스트 | 전 표면 통과 conformance → all_surfaces_green:true |
| TS-062 | R-4 AC | 회귀 테스트 | surfaces.json 부재 → applicable:false 스킵(기존 프로젝트 무영향) |
| TS-063 | R-4 AC | 산출물 검사 | verification.md §2.1에 분모·실행방식·auth 체인·CORS 검사 명시(H-9) |

### F-007 설계

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `references/journey-flow.md` | 가이드 | 신규 "여정 스모크 게이트" 절 — L✓ 회귀에 첫 접촉 경로(로그인→핵심1기능) 실 브라우저 E2E 1회 의무·스킵 조건·기록 위치 | `journey-flow.md:80` |
| 2 | `references/verification.md` | 가이드 | §2.1 E2E(L3b) 행에 "실행 환경=실 브라우저(cmux-tool 우선/playwright 폴백)" 명시 | (→ D-3 §2.1) |
| 3 | `SKILL.md` | 오케스트레이터 | L✓ 회귀에 여정 스모크 게이트 참조 | `SKILL.md:270` |

#### 3.7.2 규범 설계
- [MUST] journey-flow.md 원문: "user-facing 프로젝트는 L✓ 회귀에 USER_JOURNEY 첫 접촉 경로(예: 로그인→핵심 1기능)를 실 브라우저(cmux-tool 우선/playwright 폴백)로 실환경 E2E 1회 실행한다 — CORS·쿠키·리다이렉트 등 브라우저 계층 결함의 최종 안전망. 비 user-facing(인프라/라이브러리/CLI 내부)은 스킵하고 근거를 STATE.md/VERIFICATION.md에 1줄 기록. 결과는 VERIFICATION.md에 결과 계약(대상/결과/사유/시점)으로 기록."
- 스킵 조건·트리거는 journey-flow.md §2(user-facing 여부) 재사용.

#### 3.7.3 환경 / 3.7.4 배치
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-070 | R-6 AC | 산출물 검사 | journey-flow.md에 여정 스모크 의무·실 브라우저 요건·스킵 조건·기록 위치(VERIFICATION.md) 존재 |
| TS-071 | R-6 AC | 산출물 검사 | verification.md §2.1 E2E(L3b) 행에 실 브라우저 실행 환경 명시 |

### F-008 설계

#### 3.8.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `SKILL.md` | 오케스트레이터 | D5에 "실행 스켈레톤 최우선(P0 의존 루트) 태스크 의무"(구성 4항) + 병렬 실행 절 통합 태스크를 게이트 연결 | `SKILL.md:206,490` |
| 2 | `references/verification.md` | 가이드 | 스켈레톤 게이트 메커니즘(D6 Evaluator 판정 항목 + 커버리지 게이트 간접 보강) 명시 | (→ D-3) |

#### 3.8.2 규범 설계
- [MUST] SKILL.md D5 원문: "D5 백로그의 의존 루트(P0) 태스크로 '실행 스켈레톤' 슬라이스를 의무화한다 — 구성: (a) BE 서버 기동+스웨거(OpenAPI) UI 노출(surfaces.json 연동), (b) FE dev 서버 기동, (c) 실 브라우저(cmux browser)에서 FE→BE 실 호출 1개 관통, (d) auth 표면 존재 시 로그인 관통. 이후 전 태스크의 real-http/real-usage 검증이 이 환경 위에서 실행된다(목 개발의 '실 BE 부재' 사유 원천 제거)."
- **게이트 메커니즘 결정(M-4/R-8)**: 스켈레톤 존재·구성 판정은 **D6 Evaluator 판정 항목**(F-009 ⑩)으로 집행한다 — 구조적 탐지(어느 태스크가 스켈레톤인지)가 취약하여 backlog-tool 전용 게이트를 두지 않는다. 커버리지 게이트(F-004)가 스켈레톤 표면 커버를 간접 보강. R-8 AC "스켈레톤 없는 백로그가 D6 fail" 충족.

#### 3.8.3 환경 / 3.8.4 배치
해당 없음.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-080 | R-8 AC | 산출물 검사 | SKILL.md D5에 스켈레톤 태스크 의무·구성 4항 존재 |
| TS-081 | R-8 AC | 산출물 검사 | D6 Evaluator 판정 항목에 "스켈레톤 태스크 부재/구성 미달"(F-009) 포함 |

### F-009 설계

#### 3.9.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal-evaluator-agent/AGENT.md` | 에이전트 | Phase1 Base 루브릭에 표면완전성·auth·origin·스켈레톤 판정 항목 4종 추가, target_artifacts에 surfaces.json | `AGENT.md:42-49,28` |
| 2 | `opal-loop-action-agent/AGENT.md` | 에이전트 | 컨텍스트 재주입 표에 요구 충실도·surfaces_path, T4a에 fidelity/conformance 게이트 호출, blocked 트리거에 fidelity_unmet | `AGENT.md:109-118,144-147,299-309` |

#### 3.9.2 설계
- [MUST] opal-evaluator-agent Base 루브릭 추가(→ D-9 §Phase1): ⑦표면 완전성(surfaces.json ↔ PRD/TRD/여정 누락, Likert ≥4) ⑧auth 필드 완전성(전 표면 auth 선언, binary) ⑨origin 선언(웹 클라이언트, binary) ⑩워킹 스켈레톤 태스크(존재·구성 4항, binary). target_artifacts 예시에 `surfaces.json` 추가.
- [MUST] opal-loop-action-agent(→ D-10): 컨텍스트 재주입 표에 `요구 충실도`(area→충실도 매핑: be/공통 표면=real-http↑, fe·인터랙션·여정=real-usage) + `surfaces_path` 행 추가 — T1·T2에 주입(R-G 사각지대 봉쇄, H-11). §파이프라인 흐름 5(T4a)에 `scenario-fidelity-check`/`scenario-conformance` 호출 추가, `fidelity_unmet`을 재작업 트리거·상한 초과 시 blocked(M-6). 3-SSOT 호출 규칙 불변(test-tool scenario-* 계열).

#### 3.9.3 환경 / 3.9.4 배치
install-mac.sh 어댑터가 AGENT.md 내용을 그대로 소비(ANALYSIS §6) — 어댑터 로직 무변경.

#### 3.9.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-090 | R-1/R-8 AC | 산출물 검사 | Evaluator AGENT.md에 표면·auth·origin·스켈레톤 판정 항목 존재 |
| TS-091 | R-5 AC | 산출물 검사 | 루프 액션 에이전트 AGENT.md에 요구 충실도 주입·T4a 게이트 호출·fidelity_unmet 트리거 존재(H-11) |

### F-010 설계

#### 3.10.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | 변경 문서·도구·에이전트 전체 | 문서 | 각 "## 변경이력" 표에 069 행(KST+태스크번호) | [MUST] CONVENTIONS §변경이력 |
| 2 | `references/loop-control.md` | 가이드 | §7 복구가능 행에 신규 게이트 에러 4종 추가(M-6) | `loop-control.md:104` |
| 3 | `docs/PROJECT.md` | 문서 | Project Loop 표 backlog-tool 서브명령 수·설명 정합 | `PROJECT.md:108` |

#### 3.10.2 설계
- [MUST] loop-control.md §7 복구가능 행에 `surface_uncovered`·`integration_task_missing`·`fidelity_unmet`·`surface_unverified` 추가(M-6): "완결성·충실도 갭 — 재작업(add-task/더 높은 충실도 재검증)으로 해결, 계약/설계 부정 아님. blocked 전환은 §4 무진전·§2 상한 경로."
- 변경이력 069 행 대상: contract.md·verification.md·journey-flow.md·loop-control.md·SKILL.md(변경이력 있으면)·backlog-tool README·test-tool README·evaluator AGENT.md·loop-action AGENT.md. backlog.schema.json/test-scenario.schema.json은 description 필드로 069 반영.
- PROJECT.md는 docs/(install 대상 아님) — PM 직접 갱신.

#### 3.10.3 환경 / 3.10.4 배치
해당 없음.

#### 3.10.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-100 | R-7 AC | 산출물 검사 | changed_files 중 변경이력 표 보유 문서 전부에 069 행 존재 |
| TS-101 | R-7 AC | 산출물 검사 | loop-control.md §7에 신규 게이트 에러 4종 분류 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (규범·IR 토대) | F-001, F-002 | 1, 2 | opal-task-agent | 병렬 가능 | 독립 문서(verification.md vs contract.md) |
| 2 (backlog 도구) | F-003, F-004 | 3, 4, 5 | opal-task-agent | 순차 | 동일 backlog_tool.py — 순차 필수 |
| 3 (test 도구) | F-005, F-006 | 6, 7, 8 | opal-task-agent | 순차 | 동일 scenario.py — 순차 필수 |
| 4 (문서 규범) | F-006(doc), F-007, F-008 | 9, 10, 11 | opal-task-agent | 부분 병렬 | SKILL.md·verification.md 편집 조정 필요 |
| 5 (에이전트) | F-009 | 12, 13 | opal-task-agent | 병렬 가능 | evaluator vs loop-action 독립 파일 |
| 6 (정합·이력) | F-010 | 14, 15, 16 | opal-task-agent / PM | 순차 | 전체 완료 후 |

> **전문 에이전트 매핑**: 전 Step이 Framework 영역(`opal/tools`·`opal/skills`·`opal/agents` — Python/Markdown) → **opal-task-agent**(docs/PROJECT.md §프로젝트 구성 "Framework → opal-task-agent"). FE/BE/DB 코드 없음. docs/PROJECT.md 갱신만 PM 직접.

### 4.2 실행 체크리스트

> 총 16개 Step | Phase 6개 | 실행 모드: 복잡

#### Step 1: verification.md 충실도 사다리·규범 명문화 (F-001)
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/verification.md`
- **작업 내용**: §1 신규 절(충실도 3단계 mock<real-http<real-usage 정의·BE/FE 매핑·표준 실행법·real-usage done 규범, 3.1.2). SKILL.md 검증 2원화 절에 인라인 참조 1줄 추가.
- **완료 기준**: TS-001/TS-002 — §1에 3단계 정의·실행법·done 규칙 존재, R-5가 인용할 규범 원천 확립
- **테스트**: TS-001, TS-002
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: contract.md 표면 인벤토리·auth·origin + surfaces IR 스펙 (F-002)
- [x] 완료 (SKILL.md D4 부분은 Step 11로 재배치 — 이 Step은 contract.md만 완료)
- **소속 기능**: F-002
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/contract.md`, `opal/skills/opal-pilot-project-loop/SKILL.md`(D4)
- **작업 내용**: §2.2 표면 인벤토리 필수 규칙 + surfaces.json 구조 스펙(id·resource·auth·shape·origins) + §2.1 origin 선언 의무(3.2.2). SKILL.md D4 프롬프트에 surfaces.json+origin 요구 추가.
- **완료 기준**: TS-010/TS-011 — §2.2 규칙·형식(auth 포함), §2.1 origin 규칙, D4 요구 존재
- **테스트**: TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 3: backlog-tool covers 필드 구현 (F-003)
- [x] 완료
- **소속 기능**: F-003
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/backlog-tool/backlog_tool.py`, `opal/tools/backlog-tool/schema/backlog.schema.json`
- **작업 내용**: add-task/update-task `--covers` 추가, cmd_add_task/cmd_update_task covers 파싱·기록, `_UPDATE_TASK_FIELDS`·`render_backlog_table` 컬럼, `covers_invalid_json` 에러코드, schema covers optional + 신규 init schema_version 1.1 (3.3.2).
- **완료 기준**: TS-020~TS-022 — covers 기록·렌더·update, 미지정 하위호환
- **테스트**: TS-020, TS-021, TS-022
- **실행 방법**: sub-agent
- **의존**: Step 2 (surface-id 정의역 확정)

#### Step 4: backlog-tool coverage-check 게이트 구현 (F-004)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/backlog-tool/backlog_tool.py`
- **작업 내용**: `cmd_coverage_check`+`p_cov` 서브파서, ERROR_CODES 신규 3종(surface_uncovered/integration_task_missing/surfaces_file_not_found), 읽기 전용(락 없음), 축 분리(test-scenario 미접촉) (3.4.2).
- **완료 기준**: TS-030~TS-033 — 미커버·통합부재 거부 실관찰, 전커버 통과, 축 분리
- **테스트**: TS-030, TS-031, TS-032, TS-033
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: backlog-tool 테스트·README (F-003·F-004)
- [x] 완료
- **소속 기능**: F-003, F-004
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/backlog-tool/tests/test_backlog_tool.py`, `opal/tools/backlog-tool/README.md`
- **작업 내용**: covers·coverage-check 신규 TestCase 추가, README에 옵션·서브명령·에러코드 표 갱신. 기존 9 TestCase 회귀 0 확인.
- **완료 기준**: TS-023, TS-033 — 신규 테스트 통과 + 기존 전부 pass(회귀 0)
- **테스트**: TS-023, TS-033, `bash opal/tools/backlog-tool/run.sh` 스위트
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: test-tool fidelity 필드·게이트 구현 (F-005)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/test-tool/lib/scenario.py`, `opal/tools/test-tool/schema/test-scenario.schema.json`
- **작업 내용**: `FIDELITY_ORDER`, `_normalize_scenario`에 required_fidelity/fidelity 기본값(mock, `.get` 방어), scenario-mark `--fidelity`, `cmd_scenario_fidelity_check`(부분 게이트)+서브파서, `fidelity_unmet`(13), 스키마 enum optional (3.5.2).
- **완료 기준**: TS-050~TS-053 — 미달 거부(exit13), 혼합 트랙 부분 통과, 미지정 mock 하위호환
- **테스트**: TS-050, TS-051, TS-052, TS-053
- **실행 방법**: sub-agent
- **의존**: Step 1 (충실도 규범)

#### Step 7: test-tool scenario-conformance 구현 (F-006)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/test-tool/lib/scenario.py`, `opal/tools/test-tool/schema/test-scenario.schema.json`
- **작업 내용**: `_normalize_scenario`에 surface_ref, `cmd_scenario_conformance`(surfaces.json 분모+result존, auth 표면 real-http↑, surfaces 부재 시 applicable:false 스킵)+서브파서, 에러코드 surface_unverified(14)/surfaces_file_not_found(15), 축 분리(backlog 미접촉) (3.6.2).
- **완료 기준**: TS-060~TS-062 — 미검증 표면 거부, 전green 통과, surfaces 부재 스킵
- **테스트**: TS-060, TS-061, TS-062
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: test-tool 테스트·README (F-005·F-006)
- [x] 완료
- **소속 기능**: F-005, F-006
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/test-tool/tests/test_scenario.py`, `opal/tools/test-tool/README.md`
- **작업 내용**: fidelity·conformance 신규 TestCase, README 필드·서브명령·에러코드(13~15) 갱신. 기존 test_scenario.py 회귀 0 확인.
- **완료 기준**: TS-054, TS-062 — 신규 통과 + 기존 전부 pass(회귀 0)
- **테스트**: TS-054, `bash opal/tools/test-tool/run.sh` scenario 스위트
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: verification.md conformance 분모·실행방식·CORS + E2E 실 브라우저 (F-006·F-007)
- [ ] 완료
- **소속 기능**: F-006, F-007
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/verification.md`
- **작업 내용**: §2.1 계약 conformance 행에 분모(표면 전수)·실행방식(실 서버·실 HTTP·auth 토큰 체인)·CORS 검사(3.6.2). §2.1 E2E(L3b) 행에 실 브라우저(cmux/playwright) 실행 환경(3.7.2).
- **완료 기준**: TS-063, TS-071 — conformance 실행 규범·CORS·E2E 실 브라우저 명시
- **테스트**: TS-063, TS-071
- **실행 방법**: sub-agent
- **의존**: Step 1 (동일 파일 §1과 편집 조정)

#### Step 10: journey-flow.md 여정 스모크 게이트 (F-007)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/journey-flow.md`
- **작업 내용**: 여정 스모크 게이트 절 신설 — 첫 접촉 경로 실 브라우저 E2E 1회 의무·스킵 조건·기록 위치(VERIFICATION.md) (3.7.2).
- **완료 기준**: TS-070 — 의무·실 브라우저 요건·스킵·기록 위치 존재
- **테스트**: TS-070
- **실행 방법**: sub-agent
- **의존**: 없음(독립 문서)

#### Step 11: SKILL.md D5 스켈레톤·L✓ 게이트 조합·병렬 통합 태스크 (F-004·F-006·F-007·F-008)
- [x] 완료
- **소속 기능**: F-008 (주), F-004·F-006·F-007 (L✓/D5/병렬 게이트 연결)
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: D5에 스켈레톤 최우선 태스크 의무(구성 4항, 3.8.2) + coverage-check 게이트 호출. D7/L✓에 coverage-check + scenario-conformance + 여정 스모크 조합(M-2 불리언 AND). 병렬 실행 절 통합 태스크를 coverage-check 게이트에 연결.
- **완료 기준**: TS-080 — D5 스켈레톤 의무·L✓ 표면 축·D5 커버리지 게이트 호출 존재
- **테스트**: TS-080
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 4, Step 7 (게이트 시그니처 확정 후)

#### Step 12: opal-evaluator-agent 판정 항목 확장 (F-009)
- [x] 완료
- **소속 기능**: F-009
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-evaluator-agent/AGENT.md`
- **작업 내용**: Phase1 Base 루브릭에 표면완전성·auth·origin·스켈레톤 판정 4항 추가, target_artifacts에 surfaces.json (3.9.2).
- **완료 기준**: TS-090, TS-081 — 판정 항목 4종 존재
- **테스트**: TS-090, TS-081
- **실행 방법**: sub-agent
- **의존**: Step 2, Step 11

#### Step 13: opal-loop-action-agent fidelity 주입·게이트 호출 (F-009)
- [x] 완료
- **소속 기능**: F-009
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-loop-action-agent/AGENT.md`
- **작업 내용**: 컨텍스트 재주입 표에 요구 충실도·surfaces_path, T4a에 scenario-fidelity-check/scenario-conformance 호출, blocked 트리거에 fidelity_unmet (3.9.2, R-G/H-11).
- **완료 기준**: TS-091 — 주입·게이트 호출·트리거 존재
- **테스트**: TS-091
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 7
- **[MUST]**: `~/.opal/` 직접 편집 금지 — 소스(`opal/agents/`)만 수정.

#### Step 14: loop-control.md §7 신규 게이트 에러 분류 (F-010·M-6)
- [x] 완료
- **소속 기능**: F-010
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/references/loop-control.md`
- **작업 내용**: §7 복구가능 행에 신규 게이트 에러 4종 추가(M-6, 3.10.2).
- **완료 기준**: TS-101 — 4종 복구가능 분류 존재
- **테스트**: TS-101
- **실행 방법**: sub-agent
- **의존**: Step 4, Step 6, Step 7

#### Step 15: 변경이력 069 행 일괄 + 상호 참조 정합 (F-010·R-7)
- [x] 완료
- **소속 기능**: F-010
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: contract.md·verification.md·journey-flow.md·loop-control.md·SKILL.md·backlog-tool README·test-tool README·evaluator AGENT.md·loop-action AGENT.md·양 schema description
- **작업 내용**: 각 변경이력 표에 069 행(KST+069), SKILL.md 내 신규 서브명령/게이트 상호 참조 정합 검토.
- **완료 기준**: TS-100 — 변경이력 표 보유 문서 전부에 069 행
- **테스트**: TS-100
- **실행 방법**: sub-agent
- **의존**: Step 1~14 완료 후

#### Step 16: docs/PROJECT.md 정합 갱신 (docs/ 갱신 — PM 직접)
- [ ] 완료
- **소속 기능**: F-010
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: Project Loop 표 backlog-tool 서브명령 수(coverage-check 반영)·test-tool scenario-* 설명 정합, 변경이력 069 행(ANALYSIS §3.2). 새 패턴 도입(표면 인벤토리·충실도 게이트) — CONVENTIONS.md 갱신 필요 여부 검토.
- **완료 기준**: PROJECT.md가 신규 서브명령·게이트를 반영
- **테스트**: 산출물 검사
- **실행 방법**: direct (PM)
- **의존**: Step 15
- **docs/ 갱신 Step 근거**: 새 도구 서브명령·새 패턴 도입 → PROJECT.md(+CONVENTIONS.md 검토) 갱신 (plan-guide §4.2 docs 자동 생성 규칙).

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일(verification.md vs contract.md), 독립 기능 |
| Step 3 → Step 4 → Step 5 | 동일 backlog_tool.py 순차 수정(파일 충돌 방지) |
| Step 6 → Step 7 → Step 8 | 동일 scenario.py 순차 수정 |
| Step 9 ← Step 1 | 동일 verification.md — §1(Step1)과 §2.1(Step9) 편집 조정, 순차 안전 |
| Step 10 독립 | journey-flow.md 단독 |
| Step 11 ← Step 2·4·7 | 게이트 시그니처 확정 후 SKILL 호출 반영 |
| Step 12 ∥ Step 13 | 독립 AGENT.md 파일 |
| Step 15 → Step 16 | 소스 변경이력 완료 후 docs/ 정합 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 충실도 사다리·done 규범 명문 | TS-001,002 | verification.md §1 존재 |
| F-002 | 표면 인벤토리·auth·origin 규칙 | TS-010,011 | contract.md §2.1/§2.2 + D4 |
| F-003 | covers 기록·렌더·하위호환 | TS-020~023 | covers 기록 + 미지정 정상 |
| F-004 | 커버리지 게이트 거부 실관찰 | TS-030~033 | surface_uncovered/integration_task_missing exit 1 |
| F-005 | 충실도 게이트 부분 판정 | TS-050~054 | fidelity_unmet exit 13 + 혼합 트랙 + mock 하위호환 |
| F-006 | conformance 전수 판정 | TS-060~063 | surface_unverified + surfaces 부재 스킵 + 실행규범 |
| F-007 | 여정 스모크 게이트 규범 | TS-070,071 | journey-flow + verification E2E 실 브라우저 |
| F-008 | 스켈레톤 태스크 의무 | TS-080,081 | D5 의무 + D6 판정 항목 |
| F-009 | Evaluator·루프 액션 확장 | TS-090,091 | 판정 항목 + fidelity 주입 |
| F-010 | 변경이력·§7 분류·정합 | TS-100,101 | 069 행 + §7 4종 |

### 5.2 회귀 테스트
- [ ] backlog-tool 기존 9 TestCase 전부 pass (covers/coverage-check 추가 후, H-8)
- [ ] test-tool scenario 기존 TestCase 전부 pass (fidelity/conformance 추가 후, H-8)
- [ ] `--covers` 미지정 add-task / fidelity 미지정 test-scenario.json 무파손 (H-5·H-6)
- [ ] 기존 exit code 대역(backlog 0~2, scenario 0~12) 충돌 없음 (신규 backlog surface_* = exit 1, scenario 13~15)

### 5.3 코드/문서 품질
- [ ] 표준 라이브러리만 import (신규 패키지 0 — surfaces IR = JSON)
- [ ] 축 분리 유지: backlog_tool.py에 test-scenario 토큰 무, scenario.py에 backlog 토큰 무 (H-7)
- [ ] 신규 필드 영문 스네이크(covers/fidelity/required_fidelity/surface_ref)
- [ ] 변경이력 069 행 (KST+태스크번호) — 변경 문서 전체

### 5.4 보안
- [ ] surfaces.json/test-scenario.json 로드 시 하드코딩 시크릿·토큰 없음
- [ ] 게이트 도구 읽기 전용 — 파일 쓰기 부작용 없음(coverage-check·conformance·fidelity-check)
- [ ] `--dangerously-skip-permissions` 미사용(루프 액션 에이전트 allowlist 원칙 불변)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 16개 | 복잡 |
| 변경 파일 수 | 15개(소스) + docs/PROJECT.md | 복잡 |
| 모듈 범위 | 다중(2 도구 + 4 참조 + SKILL + 2 에이전트 + docs) | 복잡 |
| 작업 유형 | 대규모 개선(도구 게이트 신설 + 규범 명문화) | 복잡 |
| 외부 의존성 | 없음(stdlib, 신규 패키지 0) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **그룹핑(파일 충돌 방지)**: backlog_tool.py 계열(Step 3·4·5)은 동일 파일이라 단일 에이전트 순차. scenario.py 계열(Step 6·7·8)도 단일 에이전트 순차. verification.md(Step 1·9)는 편집 조정 순차.
- **배치 실행 순서**:
  - Batch 1: Step 1(F-001), Step 2(F-002), Step 10(F-007 journey) — 병렬(독립 문서)
  - Batch 2: Step 3→4→5(backlog) ∥ Step 6→7→8(test-tool) — 두 도구 체인 병렬, 체인 내부 순차
  - Batch 3: Step 9(verification §2.1), Step 11(SKILL), Step 12·13(agents) — Batch 2 게이트 시그니처 확정 후
  - Batch 4: Step 14(loop-control), Step 15(변경이력) → Step 16(PROJECT.md, PM)

### C-2. 스킬 요구사항
- 기존 스킬로 충분 — 신규 스킬 갭 없음. 각 워커는 op-dev-execute(구현)·문서 편집 지침을 인라인 수신.
- 도구 테스트는 `unittest` 표준 러너(ANALYSIS §1.4) — 신규 러너 도입 없음.

### C-3. 도구 요구사항
- CLI: `bash opal/tools/backlog-tool/run.sh`, `bash opal/tools/test-tool/run.sh`(개발 중 소스 경로 직접 호출).
- MCP/패키지: 없음. surfaces IR은 stdlib `json`. PyYAML 미도입(backlog-tool stdlib 전용 불변).
- install-mac.sh: 무변경(argparse 서브명령 자동 포함, 신규 .sh 없음 → chmod 라인 불필요 — ANALYSIS §6). 배포는 CLOSE 후 별도 승인(범위 외).

### C-4. 테스트 전략
- **기능 테스트**: backlog-tool `tests/test_backlog_tool.py`(covers·coverage-check TestCase), test-tool `tests/test_scenario.py`(fidelity·conformance TestCase). 게이트 거부 경로는 exit code + error 필드 실관찰(H-1~H-4).
- **회귀 테스트**: 두 도구 기존 스위트 전부 pass(회귀 0). `bash run.sh` 스모크로 신규 서브명령 exit code 확인.
- **문서 산출물 검사**: 참조 문서·AGENT.md·SKILL.md의 규범/판정 항목/게이트 호출 존재 확인(TS 산출물 검사).
- **실행 주체 유의**: conformance "실행"(실 HTTP·CORS·브라우저 E2E)은 대상 프로젝트 test-agent 소관 — 본 태스크는 프레임워크 규범·게이트 도구만 검증한다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Python 3 stdlib(argparse/json/fcntl/pathlib), unittest | op-dev-execute |
| 문서 | Markdown (SKILL·references·README·AGENT) | op-dev-execute |
| 데이터 | JSON(backlog/test-scenario/surfaces), JSON Schema Draft-07(참조용) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | 미사용 — 신규 외부 라이브러리 확정 없음(OpenAPI 생태계 도구 미도입, surfaces IR=stdlib JSON). ANALYSIS §2 조사 보류 유지 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D4/D5/D7/L✓/병렬/T2 개정 대상, §44 축 분리 원칙 |
| D-2 | 설계 | CONTRACT 가이드 | `opal/skills/opal-pilot-project-loop/references/contract.md` | §2.1/§2.2 표면 인벤토리·origin |
| D-3 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | §1 충실도·§2.1 conformance 분모·실행방식 |
| D-4 | 설계 | 여정·플로우 가이드 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | 여정 스모크 게이트·조건부 트리거 선례 |
| D-5 | 소스 | backlog-tool | `opal/tools/backlog-tool/backlog_tool.py`·`schema`·`README`·`tests` | covers·coverage-check 구현 |
| D-6 | 소스 | test-tool scenario | `opal/tools/test-tool/lib/scenario.py`·`schema`·`README`·`tests` | fidelity·conformance 구현 |
| D-7 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | Enforce-don't-advise 집행 근거 |
| D-8 | 설계 | loop-control | `opal/skills/opal-pilot-project-loop/references/loop-control.md` §7 | 신규 게이트 에러 분류(M-6) |
| D-9 | 설계 | Evaluator 정의 | `opal/agents/opal-evaluator-agent/AGENT.md` | 판정 항목 확장(M-4) |
| D-10 | 설계 | 루프 액션 에이전트 정의 | `opal/agents/opal-loop-action-agent/AGENT.md` | fidelity 주입·게이트 호출(M-4) |
| D-11 | 설계 | citation-rules | `opal/core/references/harness/citation-rules.md` §0/§2 | 근거 인용 규칙 |
| D-12 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` | 배포 경계·변경이력·언어·도구 우선 [MUST] |
| D-13 | 설계 | brain 3-SSOT 축 분리 | `.opal/brain/pages/concept/oppl-3-ssot-tool-gated-separation.md` | 축 분리 적용 범위(M-2) |
| D-14 | 설계 | brain scenario-red 갭 | `.opal/brain/pages/concept/oppl-scenario-red-confirmed-gap.md` | 혼합 트랙·required 분리 패턴(M-3) |
| D-A | 설계 | ANALYSIS.md §7 | `tasks/069-260718-opd-oppl-계약검증강화/ANALYSIS.md` | 미해결 질문·표면 형식 대안 비교 |
| D-B | 설계 | ANALYSIS.md §8 | `tasks/069-260718-opd-oppl-계약검증강화/ANALYSIS.md` §8 | 축 분리 관점 R-4 집행 지점 권고 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1. 유형: 기획/설계/소스/외부.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-A | 3-SSOT 축 분리 정신과 R-3/R-4 교차 판정 긴장 | F-004, F-006 | 높음 | M-2 — R-3=backlog-tool(surfaces만), R-4=test-tool(surfaces만), L✓=PM 불리언 AND. 어느 도구도 타 SSOT 미파싱(H-7) |
| R-B | fidelity 게이트가 전부-게이트 물려받아 task:061 재발 | F-005 | 높음 | M-3 — required_fidelity/fidelity 분리 + 시나리오별 부분 게이트 |
| R-C | 표면 인벤토리 SSOT 미확정 시 covers 정의역 붕 뜸 | F-002, F-003 | 중간 | 순서 의존 — Step 2(F-002) 선행 후 Step 3(F-003) |
| R-D | 마크다운 파서 결합도 취약 | F-002, F-004 | 중간 | M-1 — surfaces.json(JSON) 단일 인터페이스, 마크다운/YAML 파서 미도입(H-10) |
| R-E | fidelity/covers 미지정 기존 데이터 붕괴 | F-003, F-005, F-006 | 높음 | M-5 — 미지정=mock 기본값 `.get` 방어, surfaces 부재 시 conformance 스킵. 회귀 0(H-5·H-6) |
| R-F | Evaluator 확장이 prose 집행(도구 게이트 아님) | F-009 | 낮음 | TASK가 R-1/R-8을 문서 성격으로 확정 — Evaluator 판정 정당(M-4) |
| R-G | 루프 액션 에이전트 fidelity 미주입 시 mock 통과 사각지대 | F-009 | 중간 | M-4 — 요구 충실도·surfaces_path 주입 + T4a 게이트 호출(H-11) |
| R-H | 신규 게이트 에러 loop-control §7 미분류 | F-010 | 낮음 | M-6 — 복구가능 4종 편입 |
| R-T1 | 용어 정합 — "표면(surface)" ↔ "surface-id" ↔ surfaces.json id 일관성 | F-002~006 | 중간 | 전 산출물에서 `surface`/`surface_ref`/`covers` 식별자 통일. 불일치 발견 시 decision_required 에스컬레이션(citation-rules §7.5) |
