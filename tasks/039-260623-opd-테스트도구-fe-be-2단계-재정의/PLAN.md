# PLAN: 테스트 수행 도구 체계 — FE/BE 2단계(단위·통합) 재정의 + 신규 test-tool

> 작성일: 2026-06-23 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

테스트 도구 체계를 **단위(EXECUTE)/통합(TEST) 2단계**로 재정의하고, 산문 지시 대신 신규 `test-tool`(결정론적 집행기, 4서브명령 resolve/check/unit/integration)이 `test-tools.yaml`을 읽어 단계별 도구를 실행·판정한다. test-tool은 state-tool/cmux-tool 패턴(run.sh 디스패처 + Python/lib 구현 + JSON 출력 + 에러코드 카탈로그)을 답습하는 **얇은 래퍼**이며, E2E는 cmux-tool 호출→에러코드 소비로 cmux 1순위→playwright 폴백을 집행한다. test-tools.yaml/schema 2단계 재구조화 + 6문서 배선 + dtp-* 고아 참조(7줄) 현행화로 R-2(레지스트리 고아화)를 근본 해소한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | test-tools.yaml/schema 2단계 재구조화 + FE/BE 매트릭스 + dtp-* 현행화 | R1, R2 | P0 | 없음 |
| F-002 | test-tool RED-first 테스트 작성 (작성자) | R7 | P0 | F-001 |
| F-003 | test-tool 신규 빌드 — run.sh 디스패처 + Python 4서브명령 (GREEN, 구현자) | R7, R2 | P0 | F-001, F-002 |
| F-004 | test-scenario-guide.md 배선 — 도구 결정 SSOT 통합 + 2단계 명명 + E2E 우선순위 | R3, R6, R8 | P0 | F-001, F-003 |
| F-005 | opal-test-agent/AGENT.md + test-engineer.md 배선 — 2단계 체계·도구 매핑·E2E 순서 교정 | R4, R6, R8 | P0 | F-001, F-003 |
| F-006 | verification-loop-guide.md 배선 — L1~L4 ↔ 2단계 명명 정합 (재라벨링·축 분리) | R5 | P0 | 없음 |
| F-007 | 도구 레지스트리 등록 — tools.md + harness §9 | R8 | P1 | F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (yaml/schema + dtp- 현행화) ─┬─ F-002 (RED 테스트) ─ F-003 (test-tool 빌드 GREEN) ─┬─ F-004 (test-scenario-guide)
                                   │                                                      ├─ F-005 (AGENT/persona)
                                   │                                                      └─ F-007 (tools.md/harness §9)
                                   └─ F-004 도구 결정 SSOT(yaml resolve 대상) 참조

F-006 (verification-loop-guide L1~L4 축 분리) ── 독립 (yaml/tool 미의존)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. ANALYSIS R-1~R-6를 H-N 가설로 발전 + 해소안 포함.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-003 `test-tool resolve` | resolution_order(project→global→추론) 해석 오류 → 잘못된 FE/BE×단계 도구셋 JSON 반환 → 다운스트림 시나리오 작성이 엉뚱한 러너 지정 | P0 | L1(단위, resolve JSON 스키마/우선순위) + L2(실 yaml 파일 fixture) | S-1, S-2 |
| H-2 | F-003 `test-tool unit` | lint→build/type→unit 계층 stop-on-fail 계약 위반(중간 실패에도 다음 계층 진행) → FAIL 은폐 → self-confirming | P0 | L1(stop-on-fail 순서/exit code) + L2(의도적 실패 fixture로 정지 확인) | S-3, S-4 |
| H-3 | F-003 `test-tool integration` cmux 에러코드 소비 | cmux-tool 4-gate 에러코드(`not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed`)를 폴백 트리거로, 나머지 5종(`usage`/`invalid_surface`/`goto_failed`/`wait_failed`/`eval_failed`)을 에스컬레이션으로 정확히 분기 못함 → URL/네트워크 오류를 playwright로 우회(헌법 위반) | P0 | L1(에러코드→분기 매핑 단위) + L2(cmux-tool stub 에러코드 주입 통합) | S-5, S-6, S-7 |
| H-4 | F-003 `test-tool integration` mode A | cmux open→navigate→스텝→close(mode A) 격리 계약 위반 → 사용자 기존 surface(B/C) 재사용·미정리 → 사용자 세션 훼손 | P0 | L1(open/close 호출 시퀀스 단위) + L2(실 cmux mode A 1회 라운드트립) | S-8 |
| H-5 | F-003 `test-tool check` | required/optional 게이트 계약 — required 미설치 시 차단·optional 미설치 시 skip 반환 오류 | P1 | L1(check JSON required 플래그/exit) | S-9 |
| H-6 | F-001 test-tools.yaml/schema 2단계 구조 | 기존 1.0 스키마(`unit/e2e/lint/typecheck/format/security` 카테고리)와 2단계(단위/통합) 구조 호환 깨짐 → resolve 파싱 실패 | P1 | L1(스키마 유효성) + L2(template→resolve 왕복) | S-2, S-10 |
| H-7 | F-001 dtp-* 7줄 현행화 | 고아 참조 제거 후 grep 잔존 → R2 미해소(재고아화) | P1 | L1(grep `dtp-agent\|dtp-test` 잔존 0건) | S-11 |
| H-8 | F-004 도구 결정 이중규정 통합 | L107(yaml 참조)과 L131-142(4단계 탐지)를 `test-tool resolve` 단일 SSOT로 통합 시, 4단계 탐지가 도구 내부 폴백으로 흡수되지 않고 외부에 잔존 → SSOT 이중화 재발 | P1 | L1(문서 정합: resolve 호출 단일화 + 4단계=도구 내부 폴백 문구) | S-12 |
| H-9 | F-005 E2E 순서 교정 | AGENT.md L161 `playwright/cmux` 역순이 cmux 1순위로 교정 안됨 → 문서 간 우선순위 모순 잔존 | P1 | L1(문서 정합: 6문서 E2E 순서 일관) | S-13 |
| H-10 | F-006 L1~L4 ↔ 2단계 축 충돌 | verification-loop-guide L1~L4 / test-scenario L1/L2/L3 / 새 단위·통합 2단계가 3축 혼동 → 워커가 L번호를 오해석 | P2 | L1(문서 정합: 3축 매핑 표 1곳 정의) | S-14 |
| H-11 | F-001/F-007 SSOT 한도 복제 | test-tools.yaml/문서에 루프 한도 수치 직접 기재 → harness §1 SSOT 이중화 | P2 | L1(grep: 한도 수치 미복제, 포인터만) | S-15 |

**해소안 요약**:
- H-1·H-2·H-3·H-4·H-5: F-002 RED-first 테스트가 4서브명령 행위 계약을 실패 테스트로 먼저 못박고(작성자=opal-test-agent red mode), F-003 구현(opal-be-agent)이 GREEN으로 통과시킨다. cmux 분기는 cmux-tool 에러코드 소비(어댑터)로만 — test-tool에 `uname`/`cmux --version` 하드코딩 분기 금지(헌법 플랫폼 독립).
- H-3 정밀: cmux-tool README §에러코드 테이블(`README.md:148-161`)과 dispatch.sh 가드(`dispatch.sh:44-61`)를 SSOT로, 폴백 4종/에스컬레이션 5종 매핑을 test-tool 어댑터에 1:1 반영.
- H-8: test-scenario-guide L131-142 4단계 탐지를 "test-tool resolve 내부 추론 폴백"으로 재기술(외부 중복 제거).
- H-11: 모든 한도는 harness §1 포인터만(`opal-harness.md §1`), verification-loop-guide §7 표는 "정합성 확인용 요약"으로 유지(이미 L530 포인터 선언) — F-006에서 신규 수치 기재 금지.

---

## 2. 기능별 분석

### F-001: test-tools.yaml/schema 2단계 재구조화 + dtp-* 현행화

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `opal/core/references/test-tools-schema.yaml` | 레지스트리 스키마 — dtp-* 5줄 + 1.0 카테고리 구조 | 수정 |
| 환경 | `opal/templates/test-tools.yaml` | 레지스트리 인스턴스 템플릿 — dtp-* 2줄 + TS 단일 스택 | 수정 |

#### 2.1.2 현재 구현
- schema: `version/stack/global/tools/resolution_order/scenario_type_mapping` 6필드 (`test-tools-schema.yaml:9-166`). 카테고리 enum = `unit/e2e/lint/typecheck/format/security` (`:60`). dtp-* 참조 5줄(`:19,20,44,139,150`).
- template: stack=ts/nextjs/node 기본, global=gitleaks, tools={unit:vitest, e2e:playwright, lint:eslint, typecheck:tsc, format:prettier} + Python 주석 예시 (`test-tools.yaml:15-126`). dtp-* 참조 2줄(`:11,27`).
- **결함(ANALYSIS F-1)**: 실 소비자(dtp-*) 부재 = 고아. 단계(단위/통합) 구조·FE/BE 매트릭스 미반영.

#### 2.1.3 영향 범위
- 피영향: `test-tool resolve`(F-003)가 신 구조의 실 소비자가 됨 → 스키마/템플릿 구조가 resolve 파서 계약. `qa-engineer.md:15`(op-dev-test-scenario, op-dev-qa) 참조 경로 유효성 유지 필요(간접, ANALYSIS §3.2).

---

### F-002: test-tool RED-first 테스트 작성 (작성자)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/test-tool/tests/test_test_tool.py` | 4서브명령 행위 계약 RED 테스트 | 신규 |

#### 2.2.2 현재 구현
- 부재(신규 도구). 패턴 참조: state-tool은 단일 `tests/test_state_tool.py`로 RED-first 적용(`opal/tools/state-tool/tests/`).

#### 2.2.3 영향 범위
- [MUST] 작성자(opal-test-agent red mode) ≠ 구현자(opal-be-agent) — self-confirming 고위험(TASK §E "도구가 테스트를 집행"). RED 증거(실패 출력)가 F-003 GREEN 진입 게이트.

---

### F-003: test-tool 신규 빌드 (GREEN, 구현자)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/test-tool/run.sh` | 디스패처 진입점 — .venv python 위임 (state-tool 패턴) | 신규 |
| BE | `opal/tools/test-tool/test_tool.py` | 4서브명령 라우팅 + 에러코드 카탈로그 + JSON 출력 | 신규 |
| BE | `opal/tools/test-tool/lib/resolver.py` | test-tools.yaml resolution_order 해석 | 신규 |
| BE | `opal/tools/test-tool/lib/runner.py` | unit 계층 stop-on-fail 실행 + check 게이트 | 신규 |
| BE | `opal/tools/test-tool/lib/e2e_adapter.py` | cmux-tool 호출→에러코드 소비→playwright 폴백 결정 | 신규 |
| BE | `opal/tools/test-tool/README.md` | 도구 계약 문서 (cmux-tool README 패턴) | 신규 |

> 모듈 분할 권고안: state-tool은 단일 `state_tool.py`(대형), cmux-tool은 `lib/*.sh` 분할. test-tool은 **얇은 래퍼**(헌법 §2)이나 4서브명령 + cmux 어댑터의 응집도를 위해 `lib/` 분할 채택(resolver/runner/e2e_adapter). 단일 파일도 허용 — 구현자가 코드량 보고 최종 결정 가능.

#### 2.3.2 현재 구현
- 부재. 답습 패턴:
  - run.sh 디스패처: `VENV_PYTHON="$HOME/.opal/.venv/bin/python"` 가드 + `exec $VENV_PYTHON $SCRIPT_DIR/*.py "$@"` (`state-tool/run.sh:4-12`). cmux-tool은 bash 디스패처(`run.sh:88-125`)지만 test-tool은 yaml 파싱·계층 실행이 Python 적합 → state-tool형 Python 위임 채택.
  - 에러코드 카탈로그: `ERROR_CODES = {...}` dict 상수 SSOT + 응답 헬퍼(`state_tool.py:68-103`).
  - 서브명령 라우팅: argparse 서브파서(state-tool) 또는 `case "$subcommand"`(cmux-tool dispatch.sh:68).
  - cmux 호출: cmux-tool `run.sh integration`이 아니라 **cmux-tool 자체를 subprocess 호출**하여 JSON 에러코드 소비.

#### 2.3.3 영향 범위
- 피영향: F-004/F-005/F-007 문서가 `test-tool resolve/check/unit/integration` 호출을 배선. test-tool은 1회 실행·판정만 — PASS-or-fix 루프는 오케스트레이터 책임(TASK §D, harness §1 SSOT).

---

### F-004: test-scenario-guide.md 배선

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 도구 결정 이중규정·M 매핑·E2E 순서 | 수정 |

#### 2.4.2 현재 구현
- L107: "도구: `.opal/test-tools.yaml` 또는 프로젝트 설정에서 결정". L131-142: Step 4-a [MUST] 4단계 탐지(CONVENTIONS→스택문서→설정파일→글로브). **이중규정**(ANALYSIS F-2).
- L72/L83: E2E `cmux browser / playwright / cypress` 순서 불명(ANALYSIS F-3).

#### 2.4.3 영향 범위
- 호출자: `op-dev-test-scenario/SKILL.md`, `qa-engineer.md:15`. AGENT.md M2 표기와 동일 방향 필수.

---

### F-005: opal-test-agent/AGENT.md + test-engineer.md 배선

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 에이전트 | `opal/agents/opal-test-agent/AGENT.md` | 4모드(be/fe/e2e/red) + M2 처리 + E2E 순서 | 수정 |
| 에이전트 | `opal/agents/opal-test-agent/personas/test-engineer.md` | FE/BE 집중영역 + 코드품질 기준(도구명 없는 의무) | 수정 |

#### 2.5.2 현재 구현
- AGENT.md L161: M2 처리 "playwright/cmux 도구 환경 확인 후 실행" — **역순**(ANALYSIS F-3). 4모드 체계는 2단계 명명 미반영.
- test-engineer.md L31-35: FE 접근성(WCAG) "도구명 없음". L47-53: 린트/타입/포맷 기준이 단위(EXECUTE)인지 재검(TEST)인지 위상 불명(ANALYSIS F-4 델타).

#### 2.5.3 영향 범위
- test-scenario-guide E2E 우선순위와 동일 방향 필수. test-tools.yaml에 접근성 도구 등록 연동(F-001).

---

### F-006: verification-loop-guide.md 배선

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | L1~L4 계층 + harness §1 SSOT 포인터 | 수정 |

#### 2.6.2 현재 구현
- §2 계층 표(L52-58): L1 lint/L2 build/L3a unit/L3b E2E/L4 QA. §7(L513-530): harness §1 포인터 + "정합성 확인용" 요약 표.
- **R-1 충돌**: L1~L4(검증 계층) ≠ test-scenario L1/L2/L3(검증 깊이) ≠ 새 단위/통합 2단계(파이프라인 단계). 3축이 동일 "L번호"로 혼동.

#### 2.6.3 영향 범위
- harness §1 포인터 참조 유지 필수(H-11). §7 표는 이미 L530 포인터 선언 — 수치 신규 기재 금지.

---

### F-007: 도구 레지스트리 등록

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/tools.md` | OPAL 도구 인벤토리 | 수정 |
| 문서 | `opal/core/references/opal-harness.md` | §9 등록 도구 표 | 수정 |

#### 2.7.2 현재 구현
- tools.md: state-tool/brain-tool/cmux-tool 등 등록(§cmux-tool `:292-313`). test-tool 미등록.
- harness §9 표(L240-245): xlsx/state/brain-tool 3행. test-tool 미등록.

#### 2.7.3 영향 범위
- 등록만(인벤토리). test-tool 트리거 조건·실행 경로·소스 경로·의존성 기재(cmux-tool 항목 포맷 답습).

---

## 3. 기능별 설계

### F-001: test-tools.yaml/schema 2단계 재구조화

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/test-tools-schema.yaml` | 환경 | dtp-* 5줄(`:19,20,44,139,150`)→`op-dev-test-scenario`/`opal-test-agent`/`test-tool` 교체. `tiers` 신규 최상위 필드(단위/통합) + 각 tier에 FE/BE×카테고리 매트릭스 + `scope`(fe/be) | (→ D-1 §F-1), `test-tools-schema.yaml:138-166` |
| 2 | `opal/templates/test-tools.yaml` | 환경 | dtp-* 2줄(`:11,27`) 교체. `tiers: {unit, integration}` 구조 — unit={lint,typecheck,unit} / integration={api_db, e2e, supervisor}. FE/BE 도구 매트릭스(확정 B). 접근성 도구 1종(H-12 결정) | (→ D-2), TASK §B |

#### 3.1.2 데이터 모델 설계 (test-tools.yaml 2단계 스키마)

> [MUST] `.opal/AGENT.md`: ~/.opal/ 직접편집 금지 — 소스 `opal/templates/test-tools.yaml` 수정. install 재배포는 캡틴 직접(TASK §제외).

신규 `tiers` 구조 (확정 B 매트릭스 반영):

```yaml
version: "2.0"   # 1.0 → 2.0 (2단계 구조 도입)
stack: { language, framework, runtime }  # 기존 유지
global:          # 기존 유지 — gitleaks(security, required:true, 단계 무관 즉시차단)
  - name: gitleaks ...
tiers:
  unit:          # 단계1 — EXECUTE 자가검증 (수행: 구현 워커)
    fe:
      lint:     [{ name: eslint, check, install, required: true }]
      typecheck:[{ name: tsc, check: "npx tsc --noEmit", required: true }]
      unit:     [{ name: vitest, ... }]   # + RTL
      a11y:     [{ name: <H-12 결정>, required: false }]   # FE 접근성 (R-3)
    be:
      lint:     [{ name: ruff(py)/eslint(ts) }]
      typecheck:[{ name: mypy|pyright(py)/tsc(ts) }]
      unit:     [{ name: pytest(py)/vitest(ts) }]
  integration:   # 단계2 — TEST (수행: opal-test-agent + [SUPERVISOR])
    be:
      api_db:   [{ name: pytest, deps: [httpx], real_db: true }]  # mock 금지
    fe: {}      # FE 통합 단위는 E2E로 흡수
    e2e:        # FE/BE 공통 — cmux 1순위 → playwright 폴백
      - { name: cmux, priority: 1, via: cmux-tool }
      - { name: playwright, priority: 2, fallback: true }
    supervisor: # 캡틴 수동 [SUPERVISOR]
      - { name: captain-manual }
resolution_order:   # 기존 3단계 유지, 소비자명만 현행화
  1: "{project}/.opal/test-tools.yaml"
  2: "~/.opal/templates/test-tools.yaml"
  3: "package.json / pyproject.toml 추론 — test-tool resolve 내부 폴백"
```

- **dtp-* 교체 문구**: `dtp-agent의 Step 1-b` → `test-tool resolve의 스택 추론`, `dtp-test가 항상 실행` → `test-tool check가 게이트` (→ D-1 §F-1).
- **[MUST] 헌법 §4 mock 금지**: `integration.be.api_db.real_db: true`, mock 금지 주석 유지(TASK §제약 ④).

---

### F-002: test-tool RED-first 테스트 작성

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/test-tool/tests/test_test_tool.py` | BE | 4서브명령 행위 계약 RED 테스트 | TASK §E self-confirming → RED-first |

#### 3.2.2 테스트 설계 (RED — 미구현 실패 상태)

> [MUST] 작성자(opal-test-agent red mode) ≠ 구현자(opal-be-agent). RED 증거(exit≠0)가 GREEN 게이트. 공개 인터페이스(run.sh exit code/JSON)로만 검증 — 내부 결합 금지(test-scenario-guide Step 4-c `:152-156`).

| 테스트 함수 | 대상 서브명령 | 계약 (관찰 가능 행위) | 가설 |
|------------|-------------|---------------------|------|
| `test_resolve_returns_tier_toolset_json` | resolve | exit 0 + JSON에 `tiers.unit.fe/be`, `tiers.integration.e2e` 키 존재 | H-1 |
| `test_resolve_order_project_over_global` | resolve | project yaml fixture가 global보다 우선 | H-1 |
| `test_resolve_infer_fallback_when_no_yaml` | resolve | yaml 부재 시 pyproject.toml/package.json 추론 폴백 | H-1, H-8 |
| `test_unit_stop_on_fail_lint_blocks_build` | unit | 의도적 lint 실패 fixture → build/unit 미실행 + exit≠0 | H-2 |
| `test_unit_layer_order_lint_build_unit` | unit | JSON 증거에 lint→build→unit 순서 기록 | H-2 |
| `test_unit_no_watch_mode` | unit | 실행 명령에 watch 플래그 없음(단발) | H-2 (verification-loop §2 R-4) |
| `test_check_required_blocks_optional_skips` | check | required 미설치=차단(exit≠0), optional 미설치=skip(exit 0) | H-5 |
| `test_integration_cmux_fallback_4codes` | integration | cmux-tool stub이 `not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed` 반환 시 playwright 폴백 | H-3 |
| `test_integration_cmux_escalate_5codes` | integration | `usage`/`invalid_surface`/`goto_failed`/`wait_failed`/`eval_failed` 반환 시 폴백 금지·에스컬레이션 | H-3 |
| `test_integration_mode_a_open_close` | integration | cmux-tool 호출 시퀀스 open→navigate→...→close(mode A) | H-4 |
| `test_error_codes_in_catalog` | 공통 | 모든 error 값이 ERROR_CODES 카탈로그 키 | H-3 |

---

### F-003: test-tool 신규 빌드 (GREEN)

#### 3.3.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/test-tool/run.sh` | BE | .venv python 위임 디스패처 | `state-tool/run.sh:4-12` |
| 2 | `opal/tools/test-tool/test_tool.py` | BE | argparse 서브파서 + ERROR_CODES + JSON 응답 헬퍼 | `state_tool.py:68-103` |
| 3 | `opal/tools/test-tool/lib/resolver.py` | BE | resolution_order 해석 | (→ §3.1.2) |
| 4 | `opal/tools/test-tool/lib/runner.py` | BE | unit stop-on-fail + check 게이트 | TASK §E |
| 5 | `opal/tools/test-tool/lib/e2e_adapter.py` | BE | cmux-tool 호출→에러코드 소비 | TASK §E-1 |
| 6 | `opal/tools/test-tool/README.md` | BE | 계약 문서 | `cmux-tool/README.md` 패턴 |

#### 3.3.2 API 설계 (4서브명령 계약)

> [MUST] 헌법 §2 Simplicity First: 러너(pytest/vitest/cmux) 재구현 금지 — yaml 해석→명령 실행→JSON 증거 반환하는 얇은 래퍼.
> [MUST] 헌법 플랫폼 독립: cmux 분기는 cmux-tool 에러코드 소비(어댑터)로만. `uname`/`cmux --version` 하드코딩 분기 금지(TASK §제약 ①, §E-1).

**run.sh 디스패처** (`state-tool/run.sh:4-12` 패턴):
```bash
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ ! -x "$VENV_PYTHON" ]] && echo '{"ok":false,"error":"venv_missing"}' >&2 && exit 1
exec "$VENV_PYTHON" "$SCRIPT_DIR/test_tool.py" "$@"
```

**서브명령 시그니처 / 출력 JSON / 종료코드**:

| 서브명령 | 입력 인자 | 출력 JSON (핵심 필드) | 종료코드 |
|---------|----------|---------------------|---------|
| `resolve` | `[--stack py\|ts] [--project-root PATH]` | `{ok, command, tiers:{unit:{fe,be}, integration:{e2e,api_db,supervisor}}, source, stack}` | 0 / `yaml_parse_failed`(2) / `no_runner`(3) |
| `check` | `[--category C] [--tier unit\|integration] [--project-root PATH]` | `{ok, command, results:[{name, installed:bool, required:bool}], blocked:bool}` | 0 / `required_missing`(4) |
| `unit` | `[--scope fe\|be] [--changed-files ...] [--project-root PATH]` | `{ok, command, layers:[{name:lint\|build\|unit, status:pass\|fail\|skip, stdout, exit}], stopped_at}` | 0(all pass) / `layer_failed`(5) |
| `integration` | `[--scope fe\|be] [--url URL] [--project-root PATH]` | `{ok, command, e2e:{driver:cmux\|playwright, fallback_reason, status}, api_db:{status}, escalate:bool}` | 0 / `e2e_failed`(6) / `escalation`(7) |

- **stop-on-fail (unit)**: lint→build/type→unit 순서, 한 계층 fail 시 다음 미실행 + `stopped_at` 기록(H-2). 단발 실행(watch 금지 — verification-loop §2 [MUST] `:60`).
- **루프 한도 비보유**: test-tool은 1회 실행·판정만. 재시도 루프는 오케스트레이터(TASK §D). 한도 수치는 `opal-harness.md §1` 포인터만, README에 복제 금지(H-11).

#### 3.3.3 e2e_adapter cmux 에러코드 소비 계약 (TASK §E-1 [MUST])

> [MUST] `opal/tools/cmux-tool/lib/dispatch.sh:44-61`(가드) + `cmux-tool/README.md:148-161`(에러코드 테이블) 소비. test-tool은 cmux-tool을 subprocess 호출하고 JSON `error` 필드로 폴백 결정.

```python
# e2e_adapter.py — 폴백 결정 (어댑터 격리)
FALLBACK_CODES   = {"not_in_cmux", "cmux_not_installed", "surface_parse_failed", "open_failed"}  # → playwright
ESCALATE_CODES   = {"usage", "invalid_surface", "goto_failed", "wait_failed", "eval_failed"}      # → 에스컬레이션(폴백 금지)
# cmux-tool 호출: bash ~/.opal/tools/cmux-tool/run.sh open <url> → JSON.error 검사
#   error in FALLBACK_CODES → playwright 경로 (phase2)
#   error in ESCALATE_CODES → {ok:false, escalate:true} 반환 (URL/네트워크/명령 오류 우회 금지)
```

**mode A 실행 흐름** (TASK §E-2 [MUST] — 격리 신규 surface):
```
cmux-tool open <SUT_URL>  → surface 획득 (신규)
  → navigate → click/fill/wait/eval(시나리오 스텝 단언)
  → 증거 캡처(snapshot/eval)
  → cmux-tool은 mode A에서 자체 close (dispatch.sh:543 A) tab close)
```
- **[MUST] mode B/C(사용자 surface 재사용) 금지** — `--surface` 미전달로 강제(TASK §E-2). 사용자 세션 비훼손.
- **SUT 경계 권고안**: test-tool은 **앱 가동 전제 검사만** 수행(기동 책임 비보유). `integration` 진입 시 `--url`로 받은 SUT(dev서버/localhost)에 cmux open 시도 → `open_failed`/`wait_failed`면 "SUT 미가동" 에스컬레이션. **근거**: 헌법 §2(단순성) — 앱 기동(포트 관리·프로세스 라이프사이클)은 도구 책임 경계 밖, 오케스트레이터/캡틴이 SUT 가동 후 호출. 이를 README·integration 출력 `escalate` 사유에 명시.

#### 3.3.4 환경 변경
- 신규 도구 디렉토리 `opal/tools/test-tool/`. install 재배포로 `~/.opal/tools/test-tool/`에 반영(캡틴 직접 — TASK §제외). 추가 패키지 없음(yaml 파싱은 .venv PyYAML 가정 — 부재 시 stdlib 폴백 또는 의존성 명시는 구현자 판단).

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | 완료기준② R7 | 기능 | `resolve`가 yaml 읽어 tiers JSON 반환 (실 소비자=R-2 해소) |
| TS-002 | 완료기준① R7 | 기능 | `unit` lint→build→unit stop-on-fail, JSON 증거 |
| TS-003 | 완료기준③ R7 | 통합 | `integration` cmux→playwright 폴백 4코드 + 에스컬레이션 5코드 |
| TS-004 | 완료기준① R7 | 기능 | `check` required 차단/optional skip |
| TS-005 | 완료기준① R7 | 회귀 | RED 테스트 전체 GREEN 전환 |

---

### F-004: test-scenario-guide.md 배선

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `test-scenario-guide.md` | 가이드 | L107 도구 결정→`test-tool resolve` 단일 호출. L131-142 4단계 탐지→"resolve 내부 추론 폴백"으로 재기술. L72/L83 E2E cmux 1순위 명시. 2단계 명명(단위=EXECUTE/통합=TEST) 매핑 추가 | (→ D-3 §F-2,F-3), TASK §B,C |

#### 3.4.2 설계 (R-2/R-3 해소)
- **도구 결정 SSOT 통합(R-2 해소, H-8)**: L107을 "도구: `test-tool resolve` 출력의 해당 tier×scope 도구셋"으로 재기술. Step 4-a(L131-142) 4단계 탐지는 "[MUST] `test-tool resolve` 호출 → 내부에서 resolution_order(project→global→추론) 집행. 4단계 탐지는 resolve 내부 추론 폴백으로 흡수됨"으로 변경. → 외부 중복 제거, 단일 SSOT.
- **2단계 명명 매핑 표 추가**: `단위=EXECUTE(lint+build+unit, 구현 워커)` / `통합=TEST(E2E+실DB+[SUPERVISOR], opal-test-agent)`.
- **E2E 우선순위(R-6)**: L72/L83 `cmux 1순위 → playwright 폴백 (cmux 미가용=폴백, 플랫폼 가드 자연 흡수)` 명시. [MUST] 인용.
- **[MUST] 변경이력 행 추가**(태스크 039, KST). mock 금지 룰 유지.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | 완료기준⑤ R3,R8 | 산출물 검사 | L107·L131-142가 `test-tool resolve` 단일 SSOT, 4단계=내부 폴백 |
| TS-007 | 완료기준⑤ R6 | 산출물 검사 | E2E cmux 1순위→playwright 명시 |

---

### F-005: opal-test-agent/AGENT.md + test-engineer.md 배선

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal-test-agent/AGENT.md` | 에이전트 | L161 `playwright/cmux`→`cmux 1순위→playwright 폴백` 역전. M2 처리를 `test-tool integration` 호출로 배선. 2단계 체계 반영 | (→ D-4 §F-3), TASK §C |
| 2 | `test-engineer.md` | 에이전트 | L31-35 FE 접근성에 도구 매핑(H-12). L47-53 lint/type 위상=단위(EXECUTE) 명시, TEST 중복 제거 규율 | (→ D-5 §F-4) |

#### 3.5.2 설계 (R-4 해소)
- **E2E 순서 교정(R-6, H-9)**: AGENT.md L161 `cmux 1순위 → playwright 폴백`. M2 처리: "`test-tool integration --scope fe|be`을 호출하여 cmux→playwright 폴백·실DB를 집행. 도구가 폴백/에스컬레이션을 JSON으로 반환".
- **2단계 체계(R-4)**: 단위=EXECUTE(구현 워커 자가, lint+build+unit) / 통합=TEST(opal-test-agent, E2E+실DB+[SUPERVISOR]). PASS-or-fix 루프 한도는 harness §1 포인터(H-11).
- **도구명 없는 의무 해소(R-3, H-12)**: test-engineer.md FE 접근성(WCAG)에 **jest-axe** 매핑(택1 결정 — H-12 §아래). BE 실DB에 pytest+httpx+실DB 매핑.
- **lint 위상 재정의(F-4 델타)**: lint/build/type = 단위(EXECUTE 귀속). TEST 단계는 EXECUTE 완료 전제이므로 lint 재검 생략(또는 회귀 가드로만). 명시.
- **[MUST] 변경이력 행 추가**(039, KST).

> **H-12 결정 — FE 접근성 도구 택1 (R-3, 과설계 금지·1기본값)**: **jest-axe** 채택. 근거: ① vitest+RTL(확정 B FE unit) 환경에 jest-axe(axe-core 래퍼)가 동일 테스트 러너 내 통합 — 별도 러너 불요. ② lighthouse는 풀 페이지 감사(E2E/성능 영역)로 단위 단계 부적합·무거움(헌법 §2). ③ test-tools.yaml `tiers.unit.fe.a11y`에 jest-axe 1종 등록(required:false). axe-core 직접/lighthouse는 미채택(주석 비활성 보존 가능).

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음 (jest-axe는 test-tools.yaml 등록 — F-001 연동).

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | 완료기준⑤ R4,R6 | 산출물 검사 | AGENT.md L161 cmux 1순위 + M2=test-tool integration 호출 |
| TS-009 | 완료기준⑤ R4 | 산출물 검사 | test-engineer.md 접근성=jest-axe, lint=단위 위상 명시 |

---

### F-006: verification-loop-guide.md 배선

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `verification-loop-guide.md` | 가이드 | §1 개요/§2 계층 표에 "L1~L4(검증계층) ≠ 단위/통합(파이프라인 단계) ≠ L1/L2/L3(검증깊이) — 별도 축" 주석 추가. 3축 매핑 표 1곳 정의 | (→ D-6 §R-1), TASK §R5 |

#### 3.6.2 설계 (R-1/R-5 해소)
- **3축 매핑 표(R-1, H-10)** 1곳 정의:

| 축 | 명명 | 정의 |
|----|------|------|
| 검증 계층 (verification-loop) | L1/L2/L3a/L3b/L4 | lint/build/unit/E2E/QA — 실행 비용 순서 |
| 검증 깊이 (test-scenario) | L1/L2/L3 | 기능단위/프로세스통합/사용자협업 |
| 파이프라인 단계 (캡틴 2단계) | 단위/통합 | 단위=EXECUTE(L1+L2계층+L1깊이) / 통합=TEST(L3b계층+L2/L3깊이) |

- **배선 권고(기존 축 활용)**: 새 명명 강제 도입 대신 "단위=EXECUTE 묶음 / 통합=TEST 묶음"을 기존 L계층에 배선(TASK §M-6 권장). L3a/L3b 명칭 유지.
- **[MUST] R-5 한도 복제 금지(H-11)**: §7 표는 "정합성 확인용"으로 유지(이미 L530 포인터 선언). 신규 수치 기재 금지. F-5 판정 = 위반 아님(포인터 선언 존재).
- **[MUST] 변경이력 행 추가**(039, KST).

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | 완료기준⑤ R5 | 산출물 검사 | 3축 매핑 표 존재 + L계층 ≠ 2단계 명시 |
| TS-011 | 완료기준 제약⑤ | 산출물 검사 | §7 한도 수치 신규 복제 없음, harness §1 포인터 유지 |

---

### F-007: 도구 레지스트리 등록

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `tools.md` | 문서 | `## test-tool` 섹션 신규 — 용도/실행경로/소스경로/의존성/트리거/커맨드(4종) | `tools.md:292-313` cmux-tool 포맷 |
| 2 | `opal-harness.md` | 문서 | §9 등록 도구 표(L240-245)에 test-tool 1행 추가 | `opal-harness.md:240-245` |

#### 3.7.2 설계
- tools.md test-tool 항목: 실행경로 `bash ~/.opal/tools/test-tool/run.sh`, 소스 `opal/tools/test-tool/`, 의존 `.venv python + PyYAML + cmux-tool(E2E)`, 트리거 "테스트 단계 진입(EXECUTE 단위/TEST 통합)".
- harness §9 행: `| test-tool | 테스트 단계별 도구 결정론적 집행 — 4서브명령 resolve/check/unit/integration | EXECUTE/TEST 단계 진입 시 |`.
- **[MUST] 변경이력 행 추가**(039, KST) — tools.md/harness 모두.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | 완료기준⑦ R8 | 산출물 검사 | tools.md + harness §9에 test-tool 등록 |
| TS-013 | 완료기준⑥ R2 | 산출물 검사 | `grep -rn "dtp-agent\|dtp-test" opal/` 잔존 0건 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-be-agent | F-006과 병렬 가능 | yaml/schema 기반 확정 |
| 1 | F-006 | 6 | opal-task-agent | F-001과 병렬 | 도구/yaml 미의존 (독립) |
| 2 | F-002 | 2 | opal-test-agent(red) | 순차 | F-001 후 RED 작성 |
| 3 | F-003 | 3 | opal-be-agent | 순차 | F-002 RED 증거 후 GREEN |
| 4 | F-004, F-005, F-007 | 4,5,7 | opal-task-agent | 3개 병렬 | F-003 후 문서 배선 (독립 파일) |
| 5 | docs/ 갱신 판단 | 8 | PM 직접 | 순차 | §4.4 참조 |

### 4.2 실행 체크리스트
> 총 8개 Step | Phase 5개 | 실행 모드: 복잡

#### Step 1: test-tools.yaml/schema 2단계 재구조화 + dtp-* 현행화
- [x] 완료
- **소속 기능**: F-001
- **영역**: 환경
- **agent**: opal-be-agent
- **파일**: `opal/core/references/test-tools-schema.yaml`, `opal/templates/test-tools.yaml`
- **작업 내용**: §3.1.2 `tiers` 구조(unit/integration) + FE/BE 매트릭스(확정 B) + jest-axe(a11y) 등록. dtp-* 7줄(schema 5/template 2) → test-tool/op-dev-test-scenario/opal-test-agent 교체. version 2.0. mock 금지 주석 유지. 변경이력 행 추가
- **완료 기준**: tiers 구조 존재 + `grep dtp- ` 해당 2파일 0건 + resolve 파서가 읽을 수 있는 유효 YAML
- **테스트**: TS-013 (grep 0건), F-003 resolve가 소비
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: test-tool RED-first 테스트 작성
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: opal-test-agent (test_mode=red)
- **파일**: `opal/tools/test-tool/tests/test_test_tool.py`
- **작업 내용**: §3.2.2 11개 테스트 함수 — 4서브명령 행위 계약(resolve/check/unit/integration), cmux 폴백 4종/에스컬레이션 5종, mode A open/close, stop-on-fail. 공개 인터페이스(run.sh exit/JSON)로만 검증. 실행하여 RED(exit≠0) 증거 확보·기록
- **완료 기준**: 테스트 실행 시 전부 FAIL(미구현) + RED 증거 기록. [MUST] 작성자≠구현자
- **테스트**: RED 증거가 Step 3 GREEN 게이트
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: test-tool 신규 빌드 (GREEN)
- [x] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/test-tool/run.sh`, `test_tool.py`, `lib/resolver.py`, `lib/runner.py`, `lib/e2e_adapter.py`, `README.md`
- **작업 내용**: §3.3 run.sh 디스패처(state-tool 패턴) + 4서브명령 + ERROR_CODES 카탈로그 + JSON 출력. resolve(resolution_order), unit(stop-on-fail 단발), check(required 게이트), integration(cmux-tool 에러코드 소비→폴백/에스컬레이션, mode A). 얇은 래퍼(러너 재구현 금지). cmux 하드코딩 분기 금지. 한도 수치 비복제(harness §1 포인터)
- **완료 기준**: Step 2 RED 테스트 전부 GREEN + 4서브명령 JSON 반환 동작
- **테스트**: TS-001~005
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 4: test-scenario-guide.md 배선
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- **작업 내용**: §3.4.2 L107·L131-142 `test-tool resolve` 단일 SSOT 통합(4단계=내부 폴백). L72/L83 E2E cmux 1순위 명시. 2단계 명명 매핑. 변경이력 행
- **완료 기준**: resolve 단일 호출 + E2E 순서 명시 + 이중규정 제거
- **테스트**: TS-006, TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 5: opal-test-agent/AGENT.md + test-engineer.md 배선
- [x] 완료
- **소속 기능**: F-005
- **영역**: 에이전트
- **agent**: opal-task-agent
- **파일**: `opal/agents/opal-test-agent/AGENT.md`, `opal/agents/opal-test-agent/personas/test-engineer.md`
- **작업 내용**: §3.5.2 L161 cmux 1순위 역전 + M2=`test-tool integration` 호출 배선. 2단계 체계. 접근성=jest-axe(H-12). lint 위상=단위(EXECUTE). 변경이력 행
- **완료 기준**: E2E 순서 교정 + 도구 매핑 + 2단계 반영
- **테스트**: TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 6: verification-loop-guide.md 배선
- [x] 완료
- **소속 기능**: F-006
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
- **작업 내용**: §3.6.2 3축 매핑 표(검증계층/검증깊이/파이프라인 단계) 1곳 정의 + L계층 ≠ 2단계 주석. §7 한도 수치 신규 복제 금지(harness §1 포인터 유지). 변경이력 행
- **완료 기준**: 3축 매핑 표 존재 + 한도 수치 미복제
- **테스트**: TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: 없음 (F-001/F-003 미의존 — Phase 1 병렬)

#### Step 7: 도구 레지스트리 등록 (tools.md + harness §9)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md`, `opal/core/references/opal-harness.md`
- **작업 내용**: §3.7.2 tools.md `## test-tool` 섹션(cmux-tool 포맷) + harness §9 표 1행. 변경이력 행(양쪽)
- **완료 기준**: 양 파일에 test-tool 등록
- **테스트**: TS-012
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 8: docs/ 갱신 필요 여부 판단
- [ ] 완료
- **소속 기능**: 공통
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/` (해당 시)
- **작업 내용**: 이 태스크는 OPAL 프레임워크 소스(`opal/`) 대상 — 프로젝트 `docs/`(PROJECT/ARCHITECTURE/CONVENTIONS/FRONTEND/BACKEND)는 영향 없음 확인(ANALYSIS §3.3: DB/API/환경 변경 없음). 갱신 불요 시 "해당 없음" 기록
- **완료 기준**: docs/ 영향 판단 완료
- **테스트**: -
- **실행 방법**: direct
- **의존**: Step 1~7

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 6 | F-001(yaml)와 F-006(verification-loop)은 독립 파일·미의존 |
| Step 1 → Step 2 | RED 테스트가 yaml tiers 구조 계약 참조 |
| Step 2 → Step 3 | RED-first — RED 증거가 GREEN 진입 게이트(작성자≠구현자) |
| Step 3 → Step 4,5,7 | 문서 배선이 test-tool 호출 인터페이스 확정에 의존 |
| Step 4 ∥ Step 5 ∥ Step 7 | 독립 파일, 동일 호출 계약 참조(읽기) — 병렬 가능 |

### 4.4 docs/ 갱신 Step 판단
- 대상: 프로젝트 `docs/`. 본 태스크는 `opal/` 프레임워크 소스 변경(스킬/에이전트/레퍼런스/도구/YAML)이며 ANALYSIS §3.3에서 DB/API/환경/배포 변경 없음 확정. → 프로젝트 docs/ 갱신 불요(Step 8에서 최종 확인). 프레임워크 문서(test-scenario-guide/AGENT/persona/verification-loop/tools.md/harness)는 F-004~F-007 자체가 갱신 대상.

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | tiers 2단계 구조 + dtp- 0건 | TS-013 | `grep dtp-` 2파일 0건 + 유효 YAML |
| F-002 | RED 증거 확보 | (RED) | 11개 테스트 전부 FAIL + 증거 기록 + 작성자≠구현자 |
| F-003 | 4서브명령 동작 + RED→GREEN | TS-001~005 | resolve/check/unit/integration JSON 반환 + RED 테스트 GREEN |
| F-004 | 도구 결정 단일 SSOT + E2E 순서 | TS-006,007 | resolve 단일 호출, cmux 1순위 |
| F-005 | E2E 순서 교정 + 도구 매핑 | TS-008,009 | cmux 1순위, jest-axe, lint=단위 |
| F-006 | 3축 매핑 + 한도 미복제 | TS-010,011 | 매핑 표 존재, harness §1 포인터 |
| F-007 | 레지스트리 등록 | TS-012 | tools.md + harness §9 등록 |

### 5.2 회귀 테스트
- [ ] test-tool RED 테스트 전체 GREEN 전환(F-003 후)
- [ ] test-tools.yaml 참조 파일(qa-engineer.md ×2) 참조 경로 유효성 유지
- [ ] 6문서 E2E 우선순위 일관(cmux 1순위) — 문서 간 모순 0건

### 5.3 코드/문서 품질
- [ ] 변경 7파일(+신규 도구) 변경이력 행 추가 (KST + 039)
- [ ] test-tool run.sh/Python @header 작성(code-scan 대상 — header-rules)
- [ ] 루프 한도 수치 미복제(harness §1 포인터만) — H-11
- [ ] cmux 하드코딩 분기 0건(`uname`/`cmux --version`) — 헌법 플랫폼 독립

### 5.4 보안
- [ ] test-tool 코드에 하드코딩 시크릿/토큰 없음
- [x] gitleaks(global, security) 등록 유지 — test-tools.yaml
- [x] mock 금지 룰 유지(integration.api_db.real_db) — 헌법 §4

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 13개(신규 7 + 수정 6) | 복잡 |
| 모듈 범위 | 다중 (도구/스키마/스킬/에이전트/레퍼런스) | 복잡 |
| 작업 유형 | 신규 도구 빌드 + 6문서 배선 | 복잡 |
| 외부 의존성 | 신규 도구(test-tool) + cmux-tool 소비 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1 (병렬): [opal-be-agent: Step1 F-001] ∥ [opal-task-agent: Step6 F-006]
Batch 2:        [opal-test-agent red: Step2 F-002]            (Step1 완료 후)
Batch 3:        [opal-be-agent: Step3 F-003 GREEN]            (Step2 RED 증거 후)
Batch 4 (병렬): [opal-task-agent: Step4] ∥ [Step5] ∥ [Step7]  (Step3 후)
Batch 5:        [PM: Step8 docs/ 판단]
```
- **파일 충돌 방지**: Step1(yaml ×2)와 Step3(test-tool)은 다른 파일. Step4/5/7 독립 파일 → 병렬 안전.
- **작성자≠구현자 강제**: Step2(opal-test-agent) ≠ Step3(opal-be-agent) — self-confirming 차단.

### C-2. 스킬 요구사항
- 기존 스킬 매칭: op-dev-execute(GREEN 구현), op-dev-test-scenario(RED 작성 맥락). 갭 없음 — 신규 스킬 불요(도구 빌드는 EXECUTE 워커 인라인).

### C-3. 도구 요구사항
- 신규: `test-tool` (본 태스크 산출물). 소비: `cmux-tool`(E2E 어댑터). 런타임: `.venv python` + PyYAML(부재 시 구현자 판단). install 재배포는 캡틴 직접(TASK §제외).

### C-4. 테스트 전략
- RED-first: Step2(opal-test-agent red)가 11개 행위 계약 RED 작성→실행→증거. Step3(opal-be-agent)가 GREEN. 
- 통합/E2E: test-tool 자체의 integration은 cmux-tool stub 에러코드 주입으로 폴백 분기 검증(실 cmux 1회 mode A 라운드트립은 캡틴 환경에서 통합 단계).
- 문서 QA: PM Gate에서 6문서 정합(E2E 순서/2단계 명명/SSOT 단일화) 검토.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 구현 | Python(.venv) + bash run.sh 디스패처 + YAML | trailofbits/modern-python(참조 가능) |
| 문서 배선 | Markdown / YAML | - |
| 소비 도구 | cmux-tool(E2E 어댑터), pytest/vitest/eslint/ruff/tsc/mypy/playwright/gitleaks/jest-axe(규정 대상) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 내부 OPAL 프레임워크 변경 — 외부 라이브러리 조사 불요(ANALYSIS §6.3) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | test-tools-schema.yaml | `opal/core/references/test-tools-schema.yaml` | 스키마·dtp-* 5줄·카테고리 구조 |
| D-2 | 설계 | test-tools.yaml 템플릿 | `opal/templates/test-tools.yaml` | 인스턴스·dtp-* 2줄·TS 스택 |
| D-3 | 설계 | test-scenario-guide.md | `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` | 도구 결정 이중규정 L107/L131-142·E2E 순서 L72/L83 |
| D-4 | 설계 | opal-test-agent AGENT.md | `opal/agents/opal-test-agent/AGENT.md` | M2 처리 L159-163·E2E 순서 L161 |
| D-5 | 설계 | test-engineer.md | `opal/agents/opal-test-agent/personas/test-engineer.md` | 도구명 없는 의무 L31-35·코드품질 L47-53 |
| D-6 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | L1~L4 계층 L52-58·§7 SSOT 포인터 L513-530 |
| D-7 | 설계 | opal-harness.md §1/§9 | `opal/core/references/opal-harness.md` | 루프 한도 SSOT L48-58·도구 등록 §9 L240-245 |
| D-8 | 소스 | state-tool | `opal/tools/state-tool/run.sh:4-12`, `state_tool.py:68-103` | run.sh 디스패처·ERROR_CODES 카탈로그 패턴 |
| D-9 | 소스 | cmux-tool | `opal/tools/cmux-tool/run.sh:88-125`, `lib/dispatch.sh:44-61`, `README.md:148-161` | 서브명령 라우팅·4-gate 가드·에러코드 9종 계약(폴백 4/에스컬레이션 5) |
| D-10 | 소스 | tools.md cmux-tool | `opal/core/references/tools.md:292-313` | 도구 등록 포맷 + cmux macOS 전용 `:297` |
| D-11 | 설계 | op-dev-execute SKILL | `opal/skills/op-dev-execute/SKILL.md:57-66` | Step 3-S 자가점검 L1/L2 범위(R-6) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 3축 명명 충돌(L계층/검증깊이/2단계) | F-006 | 중 | H-10 — 3축 매핑 표 1곳 정의, 기존 축 배선(새 명명 강제 X) |
| R-2 | dtp-* 제거 후 레지스트리 재고아화 | F-001,F-003 | 높음 | H-7 — test-tool resolve가 실 소비자, grep 0건 검증 |
| R-3 | FE 접근성 도구 미결 | F-005 | 중 | H-12 — jest-axe 택1(과설계 금지), test-tools.yaml 등록 |
| R-4 | cmux 플랫폼 가드 부재 | F-003 | 중 | H-3 — cmux-tool 4-gate 에러코드 소비로 자연 흡수(uname 분기 X) |
| R-5 | 루프 한도 수치 복제 | F-001,F-006,F-007 | 낮음 | H-11 — harness §1 포인터만, 수치 신규 기재 금지 |
| R-6 | op-dev-execute Step 3-S 범위(L2 귀속) | F-004,F-005 | 낮음 | **권고: 포인터만**(범위 편입 X). op-dev-execute는 TASK 변경 범위 밖 — Step 3-S L1/L2 자가점검은 "단위(EXECUTE)" 정의와 정합(현행 유지). "통합=TEST" 매핑은 문서 배선에서 포인터로 참조하고, L2 시나리오의 TEST 단계 귀속 이동은 별도 태스크로 PM 에스컬레이션 권고(범위 편입 시 PM 결정). |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 | 초기 작성 — test-tool 빌드 + yaml 2단계 재구조화 + 6문서 배선 PLAN (039). 7기능·8Step·복잡모드·리스크 가설 H-1~H-11·핵심 설계 9건 결정 |
