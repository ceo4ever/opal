# PLAN: 파이프라인 현황판 JSON 분리 + state-tool 도입 (B안)

> 작성일: 2026-05-01 | 보강: 2026-05-01 v2 (G-1~G-15) → v3 (E-1~E-6 EXECUTE 컨텍스트 완결성)
> 입력: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` (v2 — T-1~T-13 / F-1~F-23)
> 출력: PLAN.md (단일 파일)
> 작성 페르소나: generalist-architect (`~/.opal/agents/opal-planning-agent/personas/generalist-architect.md` 부재 시 기본 범용 분석/설계 원칙 적용)
> v2 보강 범위: §2.2 스키마 G-1/G-2/G-3/G-4 정정, §2.11~§2.17 신설(G-5~G-15), §3 Step 1/2/4/7/13/16 정합 갱신, §4 QA 항목 추가, §5 리스크 R-10~R-12 추가
> v3 보강 범위: §2.18 에러 코드 카탈로그 SSOT 신설(E-1), §2.19 명령 인자 종합 매트릭스 신설(E-2), §2.20 행 구성 외부 주입 형식 신설(E-3 — `--rows-spec`/`--rows-from`/`--rows-acts`), §2.21 Step 실패 시 롤백 정책 신설(E-6), §3 Step 7 fallback 보강(E-4), §3 Step 8 표준 교체 매트릭스 보강(E-5), §4 QA 항목 추가, §5 R-12 보강 + R-13 신규

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §3 State 모듈 stub(116-123), §9 OPAL Tools(184-216) 도구 우선 원칙 + 도구 테이블 등록 형식 |
| D-2 | 설계 | harness/state.md | `opal/core/references/harness/state.md` | 갱신 로직 본체(13-32 갱신 이벤트 표 + 갱신 모델 + 수행 순서 강제) |
| D-3 | 설계 | harness/state-template.md | `opal/core/references/harness/state-template.md` | STATE.md 공통 템플릿(13-42) + 행 구성 규칙(44-50) + CLOSE 진입 게이트 |
| D-4 | 설계 | harness/task-process.md | `opal/core/references/harness/task-process.md` | TASK 단계 STATE.md 생성 절차(31 — `[필수] STATE.md를 생성한다`) |
| D-5 | 설계 | harness/pm-review-gate.md | `opal/core/references/harness/pm-review-gate.md` | PM Gate 검토 절차(18-42) — `state validate` 통합 위치 |
| D-6 | 설계 | harness/additional-work.md | `opal/core/references/harness/additional-work.md` | 추가작업 진입 절차(42-50) + CLOSE 재진입 원칙 |
| D-7 | 설계 | opal-harness-interactive.md | `opal/core/references/opal-harness-interactive.md` | QA Gate(33-36) / PM Gate(80-83) 직후 State Gate 갱신 절차 |
| D-8 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` | PM 자율 통과(60-65) + auto-pass 표기 위치 |
| D-9 | 설계 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | STATE.md 도메인 치환값(112-144) — 마이그레이션 표본 |
| D-10 | 소스 | xlsx-tool 래퍼 | `opal/tools/xlsx-tool/run.sh:1-12` | OPAL Tools 패턴 — venv 호출 + JSON 출력 + 미존재 시 stderr JSON |
| D-11 | 소스 | xlsx-tool 본체 | `opal/tools/xlsx-tool/xlsx-tool.py:1-313` | argparse + JSON 응답(`ok`, `command`, `error`) + 종료 코드 |
| D-12 | 설계 | .opal/AGENT.md (프로젝트 PM) | `.opal/AGENT.md` | 개발/배포 경계(54-63), `~/.opal/` 직접 수정 금지 + 매핑(115) |
| D-13 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 §0/§2/§7 |
| D-14 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | PM 검토 게이트 진입 시점 (state validate 통합 검토) |
| D-15 | 외부 | JSON Schema Draft-07 | [JSON Schema 07 release notes](https://json-schema.org/draft-07/json-schema-release-notes.html) | F-3 스키마 표준 |
| D-16 | 소스 | install-mac.sh OPAL Installer | `scripts/install-mac.sh:637-744` | 도구 배포 함수(`install_dir`로 `opal/tools/` → `~/.opal/tools/` 일괄 복사) + playwright-tool 실행 권한 패턴 |
| D-17 | 소스 | tools.md 등록 형식 | `opal/core/references/tools.md:8-65` | xlsx-tool 등록 섹션 — 용도/실행 경로/소스 경로/의존성/커맨드/출력 형식 |
| D-18 | 소스 | opal-pilot-sdd SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md:279-381` | 35행 파이프라인 + ACT 목록 SSOT — 가장 복잡한 케이스 |
| D-19 | 소스 | opal-pilot-project-dev SKILL.md | `opal/skills/opal-pilot-project-dev/SKILL.md:494-540` | STATE.md "관리" 섹션 — Phase별 상태 + 검증 루프 로그 |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/xlsx-tool/run.sh` | OPAL Tools 래퍼 패턴 표본 | 참조만 | `opal/tools/xlsx-tool/run.sh:1-12` |
| `opal/tools/xlsx-tool/xlsx-tool.py` | argparse + JSON 응답 표본 | 참조만 | `opal/tools/xlsx-tool/xlsx-tool.py:26-32, 267-310` |
| `opal/tools/state-tool/` | 신규 도구 본체 | **신규** | - |
| `opal/core/AGENT.md` | OPAL 부트스트랩 | **수정 없음** (STATE 표현 grep 결과 본 태스크 범위 무관 — 모드 전환 표 라인 121-138은 "그냥 해" 시 STATE.md 생성 미적용 규정으로 state-tool 도입과 영향 없음) | `opal/core/AGENT.md:121-138` 검토 결과 |
| `opal/core/references/opal-harness.md` | 공통 하네스 §3/§9 | 수정 | §3(116-123), §9 도구 테이블(211-213) |
| `opal/core/references/opal-harness-interactive.md` | interactive Gate | 수정 | §2(33-36), §3(80-83) |
| `opal/core/references/opal-harness-agentic.md` | agentic 자율 통과 | 수정 | §4 판정(60-65) — auto-pass 표기 |
| `opal/core/references/harness/state.md` | 갱신 로직 본체 ★ | 수정 | 13-32 (갱신 이벤트 표) |
| `opal/core/references/harness/state-template.md` | 템플릿 ★ | 수정 | 9-42 (공통 템플릿) — `[MUST] LLM 직접 작성 금지` 추가 |
| `opal/core/references/harness/task-process.md` | TASK 공통 프로세스 | 수정 | 31 (5번 항목 STATE.md 생성) |
| `opal/core/references/harness/additional-work.md` | 추가작업 | 수정 | 42-50 (진입 절차) |
| `opal/core/references/harness/pm-review-gate.md` | PM 검토 게이트 | 수정 | 18-42 (검토 절차에 `state validate` 추가) |
| `opal/core/references/tools.md` | 도구 등록부 | 수정 | 8-65 (state-tool 섹션 신규) |
| `opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,gc,project,project-dev,sdd,write-tech}/SKILL.md` | 8개 오케스트레이터 | 수정 | 각 파일 "STATE.md 도메인 치환값" 섹션 |
| `opal/skills/op-task/SKILL.md` | TASK 단계 스킬 | 수정 | 186-188 (STATE.md 리마인더) |
| `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 단계 스킬 | **수정 없음** (grep 결과 STATE 갱신 책임 본문 없음 — 113번 라인은 무관한 "빌드/배포 파이프라인" 표현. 영향 없음 확인) | grep `STATE` 0건 |
| `opal/skills/op-dev-execute/references/execute-guide.md` | EXECUTE 가이드 | 수정 | 95, 97, 119 (워커 STATE.md 갱신) |
| `opal/agents/opal-{be,db,fe,plan,task,task-action}-agent/AGENT.md` | 워커 에이전트 | 수정 (1줄 단순 갱신) | 각 파일 행동 규칙 — `STATE.md는 EXECUTE Step 진행 시에만 갱신한다` 1행 |
| `opal/agents/opal-sdd-action-agent/AGENT.md` | SDD 액션 에이전트 | 수정 (1줄 단순 갱신) | 249 (`STATE.md를 갱신하지 않는다`) |
| `opal/agents/opal-task-action-agent/AGENT.md` | oppd 액션 에이전트 | 수정 (1줄 단순 갱신) | 211, 222 |
| `opal/agents/opal-planning-agent/personas/service-planner.md` | 기획 페르소나 | 수정 (1줄 단순 갱신) | 17 (`STATE.md 갱신 금지`) |
| `opal/core/references/harness/parallel-execution.md` | 병렬 실행 가이드 | **단순 참조** (1회 — `AGENTIC-LOG.md 및 STATE.md`에 폴백 기록, state-tool과 무관한 자유 텍스트 영역) | 74 |
| `opal/core/references/harness/qa-standards.md` | QA 표준 | **단순 참조** (1회 — SKILL.md "STATE.md 도메인 치환값" 섹션 명만 인용) | 47 |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | oppd 병렬 가이드 | **실질 갱신** (9회 — STATE.md 갱신 절차 + 머지 이력 + 검증 루프 로그가 반복 등장하므로 state-tool 호출 표기 필요) | 252, 308, 350-354, 383, 429, 437, 487, 523 |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | oppd 검증 루프 | **실질 갱신** (8회 — `STATE.md 검증 루프 로그` 섹션은 자유 텍스트 영역이라 state-tool 범위 밖이지만, "STATE.md 갱신 시점" 표현은 `state mark` 호출로 갱신 필요) | 337, 406, 408, 434, 436, 449, 463, 465 |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | WBS 가이드 | **단순 참조** (2회 — 체크리스트 항목 "STATE.md를 갱신했는가" 표현. 갱신 방법 = state-tool 호출로 1줄 추가만 필요) | 45, 242 |
| `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 로드맵 가이드 | **단순 참조** (2회) | 45, 205 |
| `opal/skills/opal-pilot-project-dev/references/prd-guide.md` | PRD 가이드 | **단순 참조** (1회) | 126 |
| `opal/skills/opal-pilot-project-dev/references/trd-guide.md` | TRD 가이드 | **단순 참조** (1회) | 189 |
| `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | SDD EXECUTE-LOOP | **실질 갱신** (8회 — Group 완료 후, ACT 완료 후 STATE.md 갱신 절차가 반복적으로 표기됨) | 41, 51, 294-307, 398, 406, 413 |
| `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` | SDD SPEC-PLAN | **단순 참조** (3회 — SSOT 원칙 강조이므로 표현 통일만) | 276, 277, 294 |
| `opal/skills/opal-pilot-sdd/references/verify-guide.md` | SDD VERIFY | **단순 참조** (1회 — 의사결정 로그 자유 텍스트 영역 — 본 태스크 범위 밖) | 171 |
| `opal/skills/opal-pilot-gc/references/done-template.md` | gc DONE 템플릿 | **단순 참조** (1회 — 체크리스트 항목, 표현 통일 가능 — 1줄 갱신) | 57 |
| `scripts/install-mac.sh` | 설치 스크립트 | 수정 (또는 변경 없음) | 716-740 — `install_dir "$opal_dir/tools" "$opal_home/tools"`가 일괄 복사이므로 state-tool 디렉토리는 추가 코드 없이 자동 복사. **`run.sh` 실행 권한 부여만 신규 추가 필요** |

### 현재 상태

- **STATE.md 갱신 방식**: 마크다운 표를 LLM이 직접 편집. 강제 검증은 PM Gate 자가 점검에 의존.
- **하네스 §3**: `harness/state.md`(13-32)에 13개 이벤트 × 4컬럼 갱신 의무 표가 정의되어 있고 모든 이벤트에 **[필수]** 강제 표기.
- **OPAL Tools 패턴**: `opal/tools/xlsx-tool/`이 표준 — `run.sh`(bash 래퍼) + `<tool>.py`(argparse+JSON) + `requirements.txt`(공유) 구조. 응답은 `{"ok": bool, "command": str, ...}` 단일 라인 JSON. 종료 코드 `1=error`.
- **install-mac.sh 배포**: `install_dir "$opal_dir/tools" "$opal_home/tools"`(D-16:718)로 `opal/tools/` 디렉토리 전체를 일괄 복사. 새 도구 디렉토리 추가 시 코드 변경 없이 자동 배포. 단, `run.sh` 실행 권한은 도구별로 명시 부여(playwright-tool은 720-725에 명시).
- **8개 오케스트레이터 파이프라인 행 구성**: opp(20행) / opd / opds / opdw / opp / oppd(검증 루프 로그 별도) / opsdd(35행+ACT 목록 동적 삽입) / opwt / opgc — 행 수 차이가 크고 일부는 별도 섹션(ACT 목록, 실행 요약 테이블, 검증 루프 로그)이 추가됨.
- **에이전트 8개 본문**: 모두 "STATE.md는 EXECUTE Step 진행 시에만 갱신한다" 또는 "STATE.md를 갱신하지 않는다"의 **1줄 행동 규칙** — 본문 변경 폭은 작음(영향 범위 정정).

### 영향 범위

#### A. 강 영향 (실질 본문 수정 필요) — 26개

**하네스 — 8개**: `opal-harness.md`(§3+§9), `harness/state.md`, `harness/state-template.md`, `harness/task-process.md`, `harness/pm-review-gate.md`, `harness/additional-work.md`, `opal-harness-interactive.md`, `opal-harness-agentic.md`. (`opal/core/AGENT.md`는 영향 없음으로 정정 → §1.5 참조)

**오케스트레이터 — 8개**: opal-pilot-{dev, dev-short, dev-wireframe, gc, project, project-dev, sdd, write-tech} SKILL.md. 각 "STATE.md 도메인 치환값" 섹션 + 본문의 "STATE.md 갱신" 표현.

**단계 스킬 — 2개** (3개 → 2개로 정정): `op-task/SKILL.md`(186-188), `op-dev-execute/references/execute-guide.md`(95, 97, 119). (`op-dev-analysis/SKILL.md`는 STATE 갱신 책임 본문 0건으로 영향 없음 정정)

**가이드 (실질 갱신) — 3개**: `oppd/references/parallel-execution-guide.md`, `oppd/references/verification-loop-guide.md`, `sdd/references/execute-loop-guide.md`.

**도구 등록부 + 배포 — 2개**: `opal/core/references/tools.md`, `scripts/install-mac.sh`.

**신규 — 1세트**: `opal/tools/state-tool/` (5개 파일 — 본체 / 래퍼 / 스키마 / README / 단위 테스트).

**에이전트 (1줄 단순 갱신) — 8개**: opal-{be,db,fe,plan,task}-agent, opal-sdd-action-agent, opal-task-action-agent (각 AGENT.md 행동 규칙 1행 갱신), opal-planning-agent/personas/service-planner.md.

#### B. 약 영향 (단순 참조 — 표현 1~2줄만 통일) — 9개

`harness/parallel-execution.md`, `harness/qa-standards.md`, `oppd/wbs-guide.md`, `oppd/roadmap-guide.md`, `oppd/prd-guide.md`, `oppd/trd-guide.md`, `sdd/spec-plan-guide.md`, `sdd/verify-guide.md`, `gc/done-template.md`.

> **분류 기준**: 본문에서 "STATE.md 갱신" 절차가 5회 이상 반복 등장하거나 별도 SOP 섹션이 있으면 "실질 갱신". 체크리스트/단일 문장 참조면 "단순 참조" — 이때는 토큰 표기 1줄 갱신만 수행.

#### C. 영향 없음 (확인 완료) — 그대로 보존

`op-task-execute`, `op-task-plan`, `op-task-qa`, `op-dev-plan`, `op-dev-qa`, `op-dev-test-scenario`, `op-dev-todo`, `op-dev-wireframe`, `op-sdd-{action-plan, plan, spec, verify}`, `op-spec-validator`, `opal/core/AGENT.md`, `op-dev-analysis/SKILL.md`.

#### 합계 정정

TASK.md "약 42개" → **PLAN 정정 결과**: 강 영향 26개(신규 1세트 별도) + 약 영향 9개 + 영향 없음 13개 = 추적 대상 **48개** 중 **수정 대상 35개 + 신규 5파일**.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/tools/state-tool/state_tool.py` | 도구 본체 — 9개 서브 명령 구현 (argparse + JSON 응답) | TASK F-1, F-2 (→ D-11 패턴 차용. PLAN v2 §2.11 G-7 / §2.13 G-10에서 7→9 확장) |
| N-2 | `opal/tools/state-tool/run.sh` | bash 래퍼 — `~/.opal/.venv/bin/python` 호출 | TASK F-1 (→ D-10 동일 패턴) |
| N-3 | `opal/tools/state-tool/schema/state.schema.json` | JSON Schema Draft-07 — state.json 검증 | TASK F-3 (→ D-15) |
| N-4 | `opal/tools/state-tool/README.md` | 사용법 문서 — 9개 서브 명령 + 종료 코드 + 에러 코드 | TASK F-1 |
| N-5 | `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 — 9개 명령 × happy path + 주요 에러 (status / gate-pass 시나리오 포함) | TASK F-21 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/harness/state.md` | 갱신 이벤트 표(13-32) 컬럼 "갱신 명령" 추가 + `[MUST] state-tool 호출만 허용` 블록 추가 | TASK F-7 (→ D-2) |
| M-2 | `opal/core/references/harness/state-template.md` | 상단에 `[MUST] LLM 직접 작성 금지 — state init 호출`(F-8) + 마커 형식 명세(T-6) + 본문은 출력 형식 참조용 유지 | TASK F-8 (→ D-3) |
| M-3 | `opal/core/references/harness/task-process.md` | 31번 항목(`[필수] STATE.md를 생성한다`) → `[필수] state-tool init 호출` 표현으로 교체 | TASK F-9 (→ D-4) |
| M-4 | `opal/core/references/harness/pm-review-gate.md` | 검토 절차(18-42)에 신규 항목 "12. state validate 실행 → violations 0건 확인" 추가. violations ≥1이면 PM Gate Fail 처리 | TASK F-10 (→ D-5) |
| M-5 | `opal/core/references/harness/additional-work.md` | 진입 절차(42-50) 1번 ~ 7번에 `state add-row --after N --stage CLOSE --item ...` + `state mark --row ... --done` 호출 명세 | TASK F-11 (→ D-6) |
| M-6 | `opal/core/references/opal-harness-interactive.md` | §2 QA Gate 직후(33-36): `state mark --row N --done` 표기. §3 PM Gate 직후(80-83): `state mark --row N --done`. §3 자가 진단(46-59) 4번에 `state validate` 호출 추가 | TASK F-12 (→ D-7) |
| M-7 | `opal/core/references/opal-harness-agentic.md` | §4 자율 통과(60-65) Pass 시: `state mark --row N --done --auto-pass` 표기. §3 판단 기록 의무에 "agentic auto-pass는 state.json `note`에 자동 기재됨" 추가 | TASK F-12 (→ D-8) |
| M-8 | `opal/core/references/opal-harness.md` | §3 stub(116-123) 본문에 `[MUST] state-tool 호출만 허용` 추가. §9 도구 테이블(211-213)에 `state-tool` 행 추가 (트리거: TASK 단계 시작 / Gate 직후 / 추가작업 진입) | TASK F-13 (→ D-1) |
| M-9 | `opal/core/AGENT.md` | **변경 없음** — grep 결과 STATE 표현이 모두 "그냥 해" 모드 미적용 규정에 한정되어 본 태스크 영향 없음을 확인. PLAN 결정으로 NO-OP 처리 | (정정) |
| M-10~M-17 | `opal/skills/opal-pilot-{dev, dev-short, dev-wireframe, gc, project, project-dev, sdd, write-tech}/SKILL.md` | "STATE.md 도메인 치환값" 섹션은 그대로 유지(행 구성 매핑 SSOT는 SKILL.md). 본문의 "STATE.md 갱신" 표현을 `state-tool` 호출로 교체. `init --skill <약어> --mode <모드>` 호출 위치 명시. | TASK F-15 (→ D-9, D-18, D-19) |
| M-18 | `opal/skills/op-task/SKILL.md` | 186-188 STATE.md 리마인더 → `~/.opal/tools/state-tool/run.sh init {경로} --skill {약어} --mode {모드}` 호출 명시 + `[MUST] state-tool로만 생성` 추가 | TASK F-16 (→ D-4) |
| M-19 | `opal/skills/op-dev-analysis/SKILL.md` | **변경 없음** — STATE 갱신 책임 본문 0건. NO-OP 처리 (영향 범위 정정) | (정정) |
| M-20 | `opal/skills/op-dev-execute/references/execute-guide.md` | 95, 97, 119 → `state mark --row N --done --as-worker` 호출로 교체. `[MUST] 워커는 자기 단계 작업 행만 mark 가능` 추가 | TASK F-16 (→ T-10) |
| M-21~M-28 | `opal/agents/opal-{be,db,fe,plan,task}-agent/AGENT.md` (5개) + `opal-sdd-action-agent/AGENT.md` + `opal-task-action-agent/AGENT.md` + `opal-planning-agent/personas/service-planner.md` (8개) | 각 행동 규칙 1행 갱신 — "STATE.md는 ~로만 갱신한다" → "STATE.md 갱신은 `state-tool` 호출로만 수행하며, 워커는 `--as-worker` 한정. 다른 단계 행은 갱신 금지." | TASK F-17 |
| M-29 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 252, 308, 350-354, 383, 429, 437, 487, 523 → `state mark/advance` 호출로 표기 통일. `STATE.md 갱신 (오케스트레이터만 수행)` → `state-tool 호출 (오케스트레이터만 수행, 머지 이력은 자유 텍스트 영역)` | TASK F-18 |
| M-30 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 337, 436 등 갱신 시점 표기 → `state mark` 호출. **단, "STATE.md 검증 루프 로그" 자유 텍스트 영역은 본 태스크 범위 밖** (TASK 확정 사항 5: 의사결정 로그/블로커는 STATE.md 자유 텍스트 유지) | TASK F-18 |
| M-31 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | 41, 51, 398, 406, 413 → `state mark` 호출 표기. §9 STATE.md ACT 상태 관리(294-307)는 ACT 목록 SSOT가 SKILL.md에 있으므로 표기 통일만 | TASK F-18 |
| M-32~M-39 | 가이드 약 영향 8개 (분류 결과 §1 영향 범위 B 참조) | 1~2줄 표현만 `state-tool` 호출로 통일. 절차 본문은 변경 없음 | TASK F-18 |
| M-40 | `opal/core/references/tools.md` | xlsx-tool 섹션 형식(8-65) 그대로 차용한 `state-tool` 섹션 신규 추가 — 용도/실행 경로/소스 경로/의존성/커맨드 9종(init/show/advance/mark/block/validate/add-row/status/gate-pass)/출력 형식/사용 예시/종료 코드 | TASK F-19 (→ D-17) |
| M-41 | `scripts/install-mac.sh` | 716-740 도구 배포 블록에 `state-tool/run.sh` 실행 권한 부여 코드 추가 (playwright-tool 패턴 동일) | TASK F-20 (→ D-16) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | 본 태스크는 추가/갱신 위주. 기존 자유 텍스트 섹션(의사결정 로그/블로커/다음 액션)은 보존 — TASK 확정 사항 5번 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | state-tool 신규 도구 본체+래퍼+스키마+README 작성 | N-1~N-4 | 중 |
| 2 | 단위 테스트 작성·통과 | N-5 | 중 |
| 3 | 하네스 §3 + §9 갱신 | M-8 | 하 |
| 4 | state.md / state-template.md / task-process.md 갱신 | M-1, M-2, M-3 | 중 |
| 5 | op-task SKILL.md 갱신 | M-18 | 하 |
| 6 | opp(opal-pilot-project) SKILL.md 갱신 | M-14 | 하 |
| 7 | 134 자기 자신 회귀 테스트 (`state init --import-existing` + 진행 검증) | (실행 검증) | 중 |
| 8 | 나머지 7개 pilot SKILL.md 일괄 갱신 (병렬 가능) | M-10~M-17 (M-14 제외) | 하 |
| 9 | 단계 스킬 갱신 | M-20 (op-dev-execute) | 하 |
| 10 | 에이전트 8개 1줄 갱신 (병렬 가능) | M-21~M-28 | 하 |
| 11 | 가이드 (실질 갱신 3개) | M-29, M-30, M-31 | 중 |
| 12 | 가이드 (단순 참조 8개) (병렬 가능) | M-32~M-39 | 하 |
| 13 | pm-review-gate.md / additional-work.md / interactive / agentic 하네스 갱신 | M-4, M-5, M-6, M-7 | 중 |
| 14 | tools.md 등록부 갱신 | M-40 | 하 |
| 15 | install-mac.sh 실행 권한 부여 추가 | M-41 | 하 |
| 16 | 추가 회귀 표본 (F-23) — dummy 태스크 1건 + 모드 2종 검증 | (실행 검증) | 중 |

### 핵심 설계

> 각 결정 뒤 인라인 인용. `[MUST]`는 재해석 방지 토큰.

#### 2.1 state-tool 본체 설계 (N-1)

**필수 인용**:

- [MUST] `opal/.opal/AGENT.md` §확정 기준 #2: "`~/.opal/` 경로 파일을 Edit/Write하지 않는다. 수정 대상은 반드시 소스 경로에서 찾아 수정한다. 매핑: `~/.opal/AGENT.md` → `opal/core/AGENT.md`, `~/.opal/references/` → `opal/core/references/`, `~/.opal/skills/` → `opal/skills/`"
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."
- [MUST] `opal/.opal/AGENT.md` §개발 vs 배포 경계 원칙: 본 태스크는 "개발" 범위. `~/.opal/` 직접 복사·실행 금지. 배포는 캡틴의 별도 지시로 `install-mac.sh` 통해 수행.

**구현 명세**:

- 표준 라이브러리만 import: `json, argparse, pathlib, subprocess, re, sys, datetime` (→ TASK T-11)
- 응답 헬퍼는 xlsx-tool 패턴 차용 — `ok(command, **kwargs)` / `err(command, code, message, violations=None)` (→ D-11 26-32 / TASK T-4)
- 종료 코드 `0=ok / 1=violation,scope_error / 2=internal_error` (→ TASK T-3). xlsx-tool은 1만 사용하지만 본 도구는 권한 위반과 내부 오류를 분리 — 호출자가 분기 처리 가능
- 시점 취득은 `subprocess.run(["node", os.path.expanduser("~/.opal/tools/date/date.js"), "datetime"], capture_output=True, text=True, check=True)`로 구현 (→ TASK T-5). subprocess 호출 실패 시 `err(..., "date_tool_failed")`
- 9개 서브 명령 시그니처: TASK F-2의 7종(`init`, `show`, `advance`, `mark`, `block`, `validate`, `add-row`) + PLAN v2 신규 2종(`status` §2.11 G-7, `gate-pass` §2.13 G-10). TASK 본문은 변경 없이 PLAN이 SSOT (→ TASK F-2 / §2.11 G-7 / §2.13 G-10)
- 워커 권한 검증(T-10)은 `--as-worker --worker-stage <stage>` 명시 인자 방식 채택 — **PLAN 결정**: 환경 변수는 디스패치 컨텍스트에서 누락 위험이 큼, `[WORKER]` 마커는 프롬프트 텍스트일 뿐 도구가 읽을 수 없음. 명시 인자가 가장 안전. 위반 시 `{"ok": false, "error": "worker_scope_violation"}` + exit 1 (→ TASK 미확정 #3)
- 마커(T-6) `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->`로 STATE.md 파이프라인 영역 안전 교체. 마커 손실 시 `init`/`advance`/`mark`/`block`/`add-row` 모두 `marker_missing` 에러로 거부. `show`만 fallback으로 표 영역 추정 출력 (→ TASK T-6)
- 멱등성(T-8): `init`은 state.json 존재 시 `already_initialized` 거부. `--force`로 덮어쓰기. force 사용 시 STATE.md 의사결정 로그 자동 기재 (→ §2.17 트리거 #1, TASK T-8 + 제약 "에스케이프 해치")

#### 2.2 state.json 스키마 (N-3)

JSON Schema Draft-07로 작성 (→ D-15). TASK F-3에 명시된 필드 + **v2 보강(G-1~G-4)**으로 누락 필드와 enum 정의를 보강. 모든 필수 필드를 `required` 처리:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["task_id", "skill", "mode", "schema_version", "created_at", "updated_at", "current_status", "rows"],
  "properties": {
    "task_id": {"type": "string", "pattern": "^[0-9]{3}-[0-9]{6}-[a-z]+-.*$"},
    "skill": {"enum": ["opp", "opd", "opds", "opdw", "opwt", "opgc", "oppd", "opsdd"]},
    "mode": {"enum": ["interactive", "agentic"]},
    "schema_version": {"const": "1.0"},
    "created_at": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$"},
    "updated_at": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$"},
    "current_status": {"enum": ["in_progress", "done", "blocked", "additional_work", "additional_work_done"]},
    "rows": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["row_id", "stage", "item", "status", "status_label", "timestamp"],
        "properties": {
          "row_id": {"type": "integer", "minimum": 1},
          "stage": {
            "enum": [
              "TASK", "ANALYSIS", "PLAN", "EXECUTE", "TEST", "WIREFRAME",
              "QA", "SPEC", "REVIEW", "DESIGN", "VERIFY",
              "SCAN", "CHECK", "REPORT", "WBS", "CLOSE"
            ],
            "description": "8개 opal-pilot SKILL.md '단계 목록' 합집합. 신규 스킬 추가 시 enum 확장 (스키마 v1.1 등)"
          },
          "item": {
            "type": "string",
            "minLength": 1,
            "description": "표준 항목명 또는 산출물명. 예: '작업', 'QA Gate', 'State Gate', 'PM Gate', '사용자 확인', '{파일명} 생성'"
          },
          "status": {"enum": ["pending", "in_progress", "done", "failed", "na"]},
          "status_label": {"enum": ["⬜", "🔄", "✅", "❌", "-"]},
          "timestamp": {
            "oneOf": [
              {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$"},
              {"type": "null"}
            ],
            "description": "행 갱신 시점(KST). pending 행은 null 허용, 그 외 상태는 string 필수"
          },
          "owner": {
            "oneOf": [
              {"enum": ["PM", "worker", "user", "auto"]},
              {"type": "null"}
            ]
          },
          "note": {
            "oneOf": [
              {"type": "string"},
              {"type": "null"}
            ]
          }
        }
      }
    }
  }
}
```

**필드 정합 규칙** (`init`이 강제):
- `status == "pending"` ↔ `timestamp == null` ↔ `status_label == "⬜"`
- `status == "in_progress"` ↔ `timestamp != null` ↔ `status_label == "🔄"`
- `status == "done"` ↔ `timestamp != null` ↔ `status_label == "✅"`
- `status == "failed"` ↔ `status_label == "❌"`
- `status == "na"` ↔ `status_label == "-"`
- enum과 라벨 매핑은 T-2 그대로 (→ TASK T-2). `init`/`advance`/`mark`/`block` 모두 양쪽을 동시 갱신하여 정합성 보장.

##### G-3 stage enum 도출 근거 (8개 SKILL.md grep 결과)

| SKILL.md | 단계 목록 (출처 라인) | 기여 토큰 |
|---------|--------------------|---------|
| `opal/skills/opal-pilot-project/SKILL.md:117` | `TASK / PLAN / EXECUTE / CLOSE` | TASK, PLAN, EXECUTE, CLOSE |
| `opal/skills/opal-pilot-dev/SKILL.md:11` | `TASK → ANALYSIS → PLAN → EXECUTE → TEST → CLOSE` | ANALYSIS, TEST |
| `opal/skills/opal-pilot-dev-short/SKILL.md:207` | `TASK / PLAN / EXECUTE / TEST / CLOSE` | (중복) |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md:132` | `TASK / WIREFRAME / EXECUTE / CLOSE` | WIREFRAME |
| `opal/skills/opal-pilot-write-tech/SKILL.md:240` | `TASK → ANALYSIS → PLAN → EXECUTE → QA → CLOSE` | QA |
| `opal/skills/opal-pilot-sdd/SKILL.md:284` | `TASK / SPEC / REVIEW / DESIGN / EXECUTE-LOOP / VERIFY / CLOSE` | SPEC, REVIEW, DESIGN, VERIFY |
| `opal/skills/opal-pilot-gc/SKILL.md:393` | `SCAN / CHECK / REPORT / CLOSE` | SCAN, CHECK, REPORT |
| `opal/skills/opal-pilot-project-dev/SKILL.md:507` | `Phase: 1-PLAN(PRD/TRD) / 2-WBS / 3-EXECUTE` | WBS |

**합집합 (16종)**: TASK, ANALYSIS, PLAN, EXECUTE, TEST, WIREFRAME, QA, SPEC, REVIEW, DESIGN, VERIFY, SCAN, CHECK, REPORT, WBS, CLOSE.

> **중요 결정**: opsdd "EXECUTE-LOOP"은 enum 토큰 `EXECUTE` 1종으로 통일하고, 각 ACT의 진행은 `item` 필드("ACT 실행 (상세: ACT 목록 참조)")로 구분한다. 하이픈을 enum에 포함시키면 행 단계 이름이 분산되어 일관성을 잃기 때문. opsdd ACT 동적 삽입은 본 태스크 범위 밖이며, 후속 태스크에서 별도 다룬다.

##### G-4 item 필드 표준 항목 상수 (코드 내 하드코딩)

state-tool 코드 내부에 표준 항목명 상수 `STANDARD_ITEMS`를 정의하여 `validate` 명령이 행 순서/패턴 검증에 사용한다 (`item` 필드 자체는 enum이 아닌 자유 string + `minLength: 1`):

```python
# state_tool.py 내 상수
STANDARD_ITEMS = {
    "작업",           # 단계 시작 행 (첫 행)
    "QA Gate",       # QA Gate 행
    "State Gate",    # State Gate 행 (QA 직후/PM 직후 2회)
    "PM Gate",       # PM Gate 행
    "사용자 확인",     # 사용자 확인 행 (단계 마지막)
}
GATE_PATTERN = ["QA Gate", "State Gate", "PM Gate", "State Gate"]  # G-10 gate-pass 검증용
```

**근거**: state-template.md §파이프라인 현황판 행 구성 규칙(44-50)의 일반 단계 행 구성 — `작업` → `{산출물} 생성` → `QA Gate` → `{QA 산출물} 생성` → `State Gate` → `PM Gate` → `State Gate` → `사용자 확인`. 산출물 행은 가변(`PLAN.md 생성` / `ANALYSIS.md 생성` 등)이므로 enum 대신 패턴(`^.+ 생성$`)으로 인식.

`item` 필드는 enum으로 강제하지 않는 이유: 산출물명은 단계마다 다르고(`PLAN.md 생성`, `TEST-SCENARIO.md 생성`, `ACT 실행 (상세: ACT 목록 참조)` 등), enum 강제 시 신규 스킬·산출물 추가가 어려워짐. 대신 `STANDARD_ITEMS`를 통해 정형 행은 식별하고, 그 외는 자유 string 허용.

#### 2.3 모드×스킬별 행 구성 매핑 위치 (TASK 미확정 #2 결정)

**PLAN 결정**: 행 구성 SSOT는 **각 SKILL.md "STATE.md 도메인 치환값" 섹션**에 유지, state-tool은 SKILL.md를 참조하지 **않고** 인자로 받은 행 목록을 그대로 사용한다.

근거:
- 8개 오케스트레이터의 행 구성 차이가 크고(opp 20행 / opsdd 35행+ACT 동적 / oppd 검증 루프 별도), state-tool 내부 하드코딩 시 SKILL.md 변경 시 도구도 같이 갱신해야 함 → 결합도 증가
- `state init`에 `--rows-from <SKILL.md 경로>` 또는 `--rows-json <path>` 또는 `--rows-spec <inline>` 인자를 추가하여 호출자(오케스트레이터)가 행 구성을 주입하도록 설계
- 모드(interactive/agentic) 차이는 행 추가/제거가 아니라 일부 행의 `na` 자동 마킹으로만 구현 — `--mode agentic`이면 "사용자 확인" 행을 자동 `na` 처리 (→ TASK 제약 "모드별 행 구성 차이")

**제약**: 이 결정으로 SKILL.md "STATE.md 도메인 치환값"은 SSOT 유지되며 본 태스크에서는 표현 갱신만 (→ M-10~M-17).

#### 2.4 워커 권한 게이트 검증 방식 (TASK 미확정 #3 결정)

**PLAN 결정**: `--as-worker --worker-stage <stage>` 명시 인자 방식 채택.

근거:
- 환경 변수(`OPAL_WORKER_STAGE`) 방식은 워커 디스패치 시 PM이 매번 환경 주입 — 누락 위험 + 디버깅 어려움
- `[WORKER]` 마커는 프롬프트 텍스트로만 존재하여 Bash 도구가 인식 불가
- 명시 인자: PM이 워커 디스패치 프롬프트에 호출 예시를 함께 주입 → 워커는 자기 단계명을 명시 인자로 전달. 위반 시 즉시 거부

**검증 알고리즘**: state.json의 `rows[]` 중 `stage == --worker-stage` 이고 `item == "작업"`(또는 "Step N/M 진행"의 EXECUTE 행)인 행만 `mark --as-worker`로 갱신 가능. 그 외 시도 시 `worker_scope_violation`.

#### 2.5 134 자기 자신 회귀 테스트 (T-13)

**PLAN 결정**: 회귀 테스트는 EXECUTE 끝에 다음 절차로 수행:

1. `state init --import-existing tasks/134-260501-opp-pipeline-state-tool/` 호출
2. 도구가 기존 STATE.md를 정규식으로 파싱하여 행 목록 추출 (→ TASK 미확정 #7)
3. 파싱 실패(행 정규식 매칭 0건) 시 `import_failed` 에러 + 호출자에게 수동 행 목록 주입 권고
4. 성공 시 state.json 생성 + STATE.md 마커 영역만 자동 렌더 교체
5. `state validate` 실행 → violations 0건 확인
6. 이후 CLOSE 단계까지 `state mark` / `state advance`만으로 진행

**파싱 정확도**: 마크다운 표 정규식 `^\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([⬜🔄✅❌-])\s*\|\s*([^|]*)\s*\|$` (→ TASK 미확정 #7). 본 134 STATE.md의 행 구성으로 검증.

#### 2.6 `state validate` 통합 위치 (TASK F-10)

**PLAN 결정**: `pm-review-gate.md` 검토 절차(D-5) 18-42에 신규 12번 항목으로 추가:

```
12. STATE.md 정합성 자동 검증 (state validate)
   - 실행: `~/.opal/tools/state-tool/run.sh validate tasks/{NNN}-.../`
   - 결과: violations[] 0건이면 Pass, ≥1건이면 PM Gate Fail (재작업)
```

추가로 `opal-harness-interactive.md` §3 PM Gate 자가 진단(46-59)에 신규 6번 항목으로 `state validate` 실행 추가 (→ M-6).

#### 2.7 백업 정책 (TASK 미확정 #4 결정)

**PLAN 결정**: 별도 자동 백업 미도입. 기존 git 커밋이 충분.

근거: 캡틴이 EXECUTE 직전 git status 확인 후 진행하는 워크플로(opal-harness.md §1 Guards)가 이미 백업 역할 수행. 자동 백업은 STATE.md 디렉토리에 추가 파일 노이즈를 발생시킨다. 단, `--force`/`--import-existing` 사용 시는 위험도가 크므로 STATE.md 의사결정 로그에 자동 기재(에스케이프 해치 정책).

#### 2.8 감사 로그 (TASK 미확정 #5 결정)

**PLAN 결정**: 별도 `.audit.log` 파일 미도입. STATE.md 의사결정 로그 자동 기재로 충분.

근거: agentic 모드의 AGENTIC-LOG.md가 이미 PM 판단 추적 역할 수행 (→ D-8 §8). 추가 로그 파일은 SSOT 분산을 야기. `--auto-pass` 사용 시 state.json `note` 필드와 STATE.md 의사결정 로그 양쪽에 기록.

#### 2.9 회귀 테스트 표본 수 (TASK 미확정 #6 결정)

**PLAN 결정**: dummy 태스크 2건 — interactive×opp, agentic×opd. 4종 매트릭스는 과도(opp/opd가 행 구성 대표 케이스 커버).

근거: opp(20행 / 표준 단계) + opd(EXECUTE 단계 + 워커 권한 게이트 트리거) 조합으로 핵심 시나리오 커버. opsdd(35행+ACT 동적)와 oppd(검증 루프)는 본 태스크에서 갱신 후 다음 태스크에서 별도 검증 (캡틴 결정 시).

#### 2.10 단위 테스트 위치 (TASK 미확정 #8 결정)

**PLAN 결정**: `opal/tools/state-tool/tests/test_state_tool.py` 단일 파일. 기존 도구(xlsx-tool, code-scan)에 테스트 디렉토리 컨벤션이 없으므로 본 도구가 첫 표본.

근거: 도구별 자기 완결성 — 다른 도구가 따라 적용하기 쉬움. install-mac.sh의 일괄 복사가 tests/도 함께 복사하지만 런타임 영향 없음(`.venv/bin/python -m unittest`로만 실행).

---

#### 2.11 STATE.md 자동 갱신 범위 (G-5, G-6, G-7, G-8 통합 명세)

`init`/`advance`/`mark`/`block`/`add-row`/`status`/`gate-pass` (이하 "갱신 명령")이 STATE.md를 어떻게 갱신하는지의 SSOT. EXECUTE 워커는 이 절을 그대로 구현한다 (추가 추측 금지).

##### G-5 STATE.md "최종 갱신" 헤더 자동 갱신

- **대상 라인**: STATE.md 1번째 출현하는 `^> 최종 갱신: .*$` 라인 (state-template.md:16)
- **동작**: 모든 갱신 명령은 실행 마지막 단계에서 다음 정규식 치환을 수행:
  - 패턴: `^(> 최종 갱신: ).*$` (멀티라인 모드)
  - 치환: `\1{node ~/.opal/tools/date/date.js datetime 결과}`
  - 첫 매치 1건만 치환 (다중 매치 시 첫 줄만)
- **시점 취득**: `subprocess.run(["node", os.path.expanduser("~/.opal/tools/date/date.js"), "datetime"], capture_output=True, text=True, check=True).stdout.strip()` (→ T-5)
- **state.json `updated_at` 동기화**: 같은 시점 값을 `updated_at`에도 기재 (G-1)
- **실패 정책**: date.js 호출 실패 시 명령 전체가 `{"ok": false, "error": "date_tool_failed"}` 반환, exit 2. STATE.md 변경 없음(원자성)

##### G-6 "현재 상태" 섹션 자동 갱신

- **대상 영역**: STATE.md `## 현재 상태` 헤더 ~ 다음 헤더(`## 파이프라인 현황판` 또는 `<!-- pipeline:start -->`) 사이의 4줄 (state-template.md:18-22)
- **자동 갱신 대상**: `- 진행:` / `- 상태:` 2개 라인 (`- 모드:` / `- 단계:` 2개 라인은 `init`만 작성, 이후 명령은 미변경 — 도메인 SSOT 보존)
- **갱신 매핑** (`opal/core/references/harness/state.md`:13-30 갱신 이벤트 표 그대로 매핑):

| 명령 / 트리거 | `- 진행:` 라인 | `- 상태:` 라인 |
|--------------|--------------|---------------|
| `init` | `{첫 단계명} 단계` (예: `TASK 단계`) | `진행 중` |
| `advance --row N` (단계 시작) | `{rows[N].stage} 단계` | (변경 없음) |
| `mark --row N --done` (일반) | (변경 없음) | (변경 없음) |
| `mark --as-worker --step <N/M>` (EXECUTE Step) | `Step {N/M} 완료` | (변경 없음) |
| `mark --row N --done` (CLOSE 단계 마지막 State Gate) | (변경 없음) | `완료` |
| `add-row --after N` (추가작업 진입) | (변경 없음) | `추가작업중` |
| `status --set additional_work_done` | (변경 없음) | `추가작업완료` |
| `block --row N` | (변경 없음) | `블로커` |

- **CLOSE 마지막 행 식별 알고리즘**: state.json `rows[]` 중 `stage == "CLOSE"`이고 `item == "State Gate"`인 마지막 행. `mark`로 해당 행을 ✅ 처리하면 `current_status`는 `done`, `- 상태:`는 `완료`로 자동 전환
- **EXECUTE Step 진행 표기**: `mark --as-worker --step <N/M>` 명시 인자 추가. 예: `state mark --row 12 --done --as-worker --worker-stage EXECUTE --step 3/8`. 이때 STATE.md `- 진행:` 라인은 `Step 3/8 완료`로 갱신. `--step` 누락 시 `- 진행:` 미변경 (action 기반 행 진행만 갱신)
- **갱신 시 정규식**: `^(- 진행: ).*$` / `^(- 상태: ).*$` 첫 매치 치환

##### G-7 추가작업 진입 시 current_status 전환 트리거 + 8번째 서브 명령 신설

**PLAN 결정**: `state status --set <전환>` 8번째 서브 명령을 신설하여 `current_status` 명시 전환을 처리한다. `add-row`는 자동으로 `current_status` → `additional_work` 전환만 수행하고, 추가작업 완료 후 `done` 상태로의 복귀는 `state status --set additional_work_done`이 수행한다.

- **시그니처**:
  ```
  state status <task-path> --set <in_progress|done|blocked|additional_work|additional_work_done> [--note <text>]
  ```
- **허용 전환** (current_status 전이 그래프, additional-work.md:42-50 진입 절차 그대로):
  - `in_progress → done` (CLOSE 단계 완료 시 자동, 명시 호출도 가능)
  - `done → additional_work` (`add-row` 실행 시 자동, 또는 `status --set additional_work` 명시)
  - `additional_work → additional_work_done` (`status --set additional_work_done` 명시 호출만)
  - `additional_work_done → additional_work` (재추가작업 진입, `add-row` 또는 `status --set`)
  - 어떤 상태 → `blocked` — 두 가지 진입 경로 모두 허용:
    - (a) `block <row>` 명령 호출 시 자동 — 행 단위 ❌ 처리와 함께 current_status도 자동으로 `blocked`로 전환 (행+상태 동시 변경)
    - (b) `status --set blocked` 명시 호출 — current_status만 `blocked`로 변경. 행 단위 ❌ 처리가 함께 필요하면 PM이 별도로 `block <row>`를 추가 호출. 행 ❌ 없는 단순 상태 표기용 (드문 케이스)
  - `blocked → in_progress` 또는 `blocked → done` (블로커 해제 시 `status --set` 명시 호출만)
- **거부 전환**: 위 그래프에 없는 전환은 `{"ok": false, "error": "invalid_status_transition", "from": "<prev>", "to": "<next>"}` + exit 1
- **STATE.md 영향**: G-6 표 매핑대로 `- 상태:` 라인 갱신. 의사결정 로그 자동 기재 (→ §2.17)
- **`add-row`의 자동 전환 로직**: `add-row` 실행 시 `current_status`가 `done`이면 자동으로 `additional_work`로 전환 (G-6 표). 이미 `additional_work`/`in_progress`이면 변경 없음.
- **TASK F-2 정정**: TASK.md F-2의 "7개 서브 명령"은 PLAN에서 **9개**(`init`, `show`, `advance`, `mark`, `block`, `validate`, `add-row`, `status`, `gate-pass`)로 확장된다. TASK.md 본문은 안정화되어 변경하지 않으며, 본 PLAN.md가 SSOT.

##### G-8 state init 신규 생성 시 STATE.md 자유 텍스트 영역 함께 생성

**`state init` 시그니처 (보강)**:

```
state init <task-path>
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd>
  --mode <interactive|agentic>
  [--task-title <text>]               # G-8: STATE.md 1행 제목
  [--next-action <text>]              # G-8: 다음 액션 섹션 초기값
  [--rows-spec <inline-json>]         # §2.3: 행 구성 외부 주입 (JSON 배열)
  [--rows-from <path-to-skill.md>]    # §2.3: SKILL.md 파싱
  [--force]                           # T-8 멱등성 우회
  [--import-existing]                 # T-13 기존 STATE.md 흡수
```

**생성 STATE.md 템플릿** (state-template.md:13-42 그대로 + 도메인 치환):

```markdown
# STATE: {--task-title 또는 task-path 마지막 디렉토리명}

> 최종 갱신: {init 시점 (date.js 결과)}

## 현재 상태
- 모드: {--mode}
- 단계: {SKILL.md "STATE.md 도메인 치환값" 단계 목록 — --rows-from 또는 --rows-spec에서 도출}
- 진행: {첫 단계명} 단계
- 상태: 진행 중

<!-- pipeline:start -->
## 파이프라인 현황판

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음
> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
{rows_spec에서 자동 렌더한 모든 행 — 모두 status="pending", status_label="⬜", timestamp=""}
<!-- pipeline:end -->

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{--next-action 인자 또는 기본값 "PLAN 단계 진입" (TASK 단계가 첫 단계면 "TASK 단계 진행")}
```

- **자유 텍스트 영역 3개 섹션**(`## 의사결정 로그` / `## 블로커` / `## 다음 액션`)을 `init`이 모두 자동 생성. 이후 갱신 명령은 의사결정 로그에만 자동 추가(§2.17), 블로커/다음 액션은 PM이 수동 갱신 (자유 텍스트 영역, state-tool 범위 밖)
- **`--import-existing` 사용 시**: 기존 STATE.md를 Read → 자유 텍스트 3개 섹션은 **그대로 보존** → 마커(`<!-- pipeline:start -->` ~ `<!-- pipeline:end -->`) 영역만 신규 삽입(또는 마커가 이미 있으면 그 영역만 교체). `## 현재 상태` 4줄은 G-6 매핑대로 갱신. 마커 누락 시 마크다운 표 정규식 파싱(§2.5) 결과를 마커로 감싸서 삽입
- **`--task-title` 누락 시 기본값**: task-path 마지막 디렉토리의 `134-260501-opp-pipeline-state-tool` 형식에서 `134` 이후를 사람 가독 형태로 변환은 하지 않고, 디렉토리명 그대로 사용 (변환 규칙 명세 없으면 추측 금지)

---

#### 2.12 추가작업 행 삽입 알고리즘 (G-9)

`state add-row --after <N> --stage <단계명> --item <항목명> [--note <text>]` 동작:

1. **기존 행 식별**: state.json `rows[]`에서 `row_id == N`인 행 위치 식별. 미존재 시 `{"ok": false, "error": "row_not_found", "row_id": N}` + exit 1
2. **신규 행 생성**: 다음 객체를 생성:
   ```json
   {
     "row_id": (다음 단계에서 결정),
     "stage": "<--stage 인자>",
     "item": "<--item 인자>",
     "status": "pending",
     "status_label": "⬜",
     "timestamp": null,
     "owner": null,
     "note": "<--note 인자 또는 null>"
   }
   ```
3. **삽입 위치**: 행 N 직후 위치. Python: `rows.insert(N_index + 1, new_row)`
4. **row_id 재정렬 정책**: 삽입 행 이후 모든 row_id를 1씩 증가. 신규 행의 `row_id = N + 1`, 기존 N+1행은 N+2, 기존 N+2행은 N+3, ... (단조 증가 보장)
5. **stage enum 검증**: `--stage`가 §2.2 G-3 enum에 없으면 `{"ok": false, "error": "invalid_stage_enum", "value": "<stage>"}` + exit 1. 추가작업 진입 시 보통 `--stage CLOSE` 사용 (additional-work.md:46 "CLOSE 단계 재진입")
6. **schema validate 실행**: 변경 후 state.json을 `state.schema.json`에 대해 검증. 위반 시 변경 롤백 + violations 반환
7. **STATE.md 자동 동기화**: 마커 영역(`<!-- pipeline:start -->` ~ `<!-- pipeline:end -->`) 재렌더 — rows[] 전체를 마크다운 표로 다시 출력
8. **current_status 자동 전환**: 현재 `current_status == "done"`이면 `additional_work`로 전환 (G-7). `additional_work`/`in_progress`/`additional_work_done`이면 그대로
   - `additional_work_done`에서 `add-row` 호출 시 자동으로 `additional_work`로 회귀 (재추가작업 진입)
9. **의사결정 로그 자동 기재**: §2.17 트리거 #5에 따라 STATE.md 의사결정 로그 표에 1행 추가
10. **응답**:
    ```json
    {"ok": true, "command": "add-row", "row_id": N+1, "rows_count": <갱신 후 rows[] 길이>, "current_status": "additional_work"}
    ```

**다중 행 삽입**: 단일 호출은 단일 행만 삽입한다. 여러 행 추가 시 `state add-row` 명령을 순차 호출 (`--after N` → 다음은 `--after N+1` 사용). 단일 호출에 `--items "<json-array>"` 등의 일괄 인자는 도입하지 않음(범위 외).

**검증 통합**: `state validate`는 삽입 후 행 순서 정합성(앞 행 ✅ 후 ⬜의 정합성, 추가작업 행이 CLOSE 재진입 패턴인지)을 함께 검사한다.

---

#### 2.13 Gate 통과 일괄 처리 (G-10)

일반 단계의 Gate 흐름은 4행 연속 갱신: `QA Gate(N)` → `State Gate(N+1)` → `PM Gate(N+2)` → `State Gate(N+3)` (state-template.md:46 "일반 단계" 행 구성 규칙). PM이 매번 `mark` 4번 호출은 비효율 + 누락 위험.

**`state gate-pass` 9번째 서브 명령 신설**:

```
state gate-pass <task-path> --start <N> [--note <text>]
```

**동작**:

1. **시작 행 검증**: `rows[start_row_index].item == "QA Gate"`이고 `rows[start_row_index].status in {"pending", "in_progress"}`인지 확인. 미충족 시 `{"ok": false, "error": "gate_pattern_mismatch", "expected": "QA Gate at row N", "found": "<item>"}` + exit 1
2. **연속 4행 패턴 검증**: `rows[N], rows[N+1], rows[N+2], rows[N+3]`의 `item` 필드가 정확히 `["QA Gate", "State Gate", "PM Gate", "State Gate"]`인지 확인 (§2.2 G-4 `GATE_PATTERN` 상수와 일치). 1개라도 다르면 동일 에러
3. **stage 일관성**: 4개 행이 모두 동일 `stage`인지 확인 (혼합 단계 거부). 다르면 `{"ok": false, "error": "gate_stage_mixed"}` + exit 1
4. **순차 ✅ 처리**: 각 행에 대해 `mark --row {row_id} --done` 동등 처리. timestamp는 4행 모두 동일 시점(date.js 1회 호출 결과 재사용 — 타임스탬프 정합성)
5. **STATE.md 의사결정 로그 자동 기재**: `Gate Pass: rows {N}~{N+3}, stage={stage}, note=<--note 또는 빈 문자열>` 1행 추가 (§2.17 트리거 #6)
6. **응답**:
    ```json
    {"ok": true, "command": "gate-pass", "rows_passed": [N, N+1, N+2, N+3], "stage": "<stage>", "timestamp": "<KST>"}
    ```

**적용 범위 제한**: opp(20행 표준)/opd/opd-short/opdw/opwt 같은 표준 단계 행 구성에서만 사용. opsdd/oppd처럼 비표준 행 구성에서는 `mark` 개별 호출 권장 (R-10 참조).

**TASK F-2 정정**: TASK.md F-2의 "7개 서브 명령"은 본 PLAN에서 **9개**(`init`, `show`, `advance`, `mark`, `block`, `validate`, `add-row`, `status`(G-7), `gate-pass`(G-10))로 확장. TASK.md 본문은 변경 없이 PLAN이 SSOT.

---

#### 2.14 state show 출력 범위 (G-11)

```
state show <task-path> [--format md|json|full]
```

| `--format` | 출력 내용 | 비고 |
|-----------|----------|------|
| `md` (기본) | 파이프라인 현황판 마크다운 표 + `## 현재 상태` 4줄 요약 | LLM 컨텍스트 토큰 효율 우선 |
| `json` | state.json raw 그대로 | 머신 가독, 후속 도구 파이프 |
| `full` | STATE.md 전체 본문 (자유 텍스트 영역 포함) | 사람 검토용 |

**마커 손실 시 fallback**:

- `--format md`:
  - 헤더에 `# 파이프라인 현황판 (마커 누락 — fallback 출력)` 명시
  - state.json `rows[]`로 표 재구성
  - exit 0 (정상 출력) + stderr에 `warning: pipeline markers missing in STATE.md`
- `--format json`:
  - state.json 정상 출력. 마커 상태 필드 추가:
    ```json
    {"ok": true, "command": "show", "format": "json", "marker_present": false, "data": {...state.json 그대로...}}
    ```
- `--format full`:
  - STATE.md 본문 그대로 출력 + 본문 맨 위에 주석 한 줄 prepend:
    ```markdown
    <!-- WARNING: pipeline markers missing — table region is unrendered. Run `state init --import-existing` to recover. -->
    ```

**state.json 미존재 시**: 모든 format에 대해 `{"ok": false, "error": "state_not_initialized"}` + exit 1. show는 갱신 명령이 아니므로 STATE.md를 변경하지 않는다 (G-5/G-6 자동 갱신 미적용).

---

#### 2.15 사용자 확인 행 처리 (G-12)

캡틴이 "확인" / "승인" / "확인완료" 등의 명시적 발화를 했을 때 PM이 사용자 확인 행을 ✅ 처리하는 방식.

**호출 형식**:

```
~/.opal/tools/state-tool/run.sh mark <task-path> \
  --row <N> --done \
  --owner user \
  --note "캡틴 확인: <발화 또는 요약>"
```

**동작**:

- `--owner user` 명시 시 state.json `rows[N].owner = "user"`로 저장
- `rows[N].note`에 `--note` 인자 그대로 저장 (캡틴 발화 추적)
- timestamp는 date.js 결과로 자동 기재

**`state validate` 검증 추가**:

- 사용자 확인 행(`rows[].item == "사용자 확인"`)에 대해:
  - `status == "done"` ∧ `owner != "user"` ∧ `owner != "auto"` → violations에 `user_confirmation_owner_mismatch` 추가 (`row_id` 포함)
  - `status == "done"` ∧ `owner == "auto"` ∧ `mode != "agentic"` → violations에 `auto_pass_in_interactive_mode` 추가
- agentic 모드에서 사용자 확인 행은 `--auto-pass` 사용:
  ```
  ~/.opal/tools/state-tool/run.sh mark <task-path> \
    --row <N> --done \
    --auto-pass \
    --note "agentic auto-pass: <PM 판단 근거>"
  ```
  - `--auto-pass` 명시 시 `owner = "auto"` 자동 저장. `--owner` 인자와 충돌 시 `{"ok": false, "error": "owner_flag_conflict"}` + exit 1
  - state-template.md:47 "사용자 확인 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트"와 통일: agentic의 사용자 확인 행은 `na`(-)가 아니라 **`auto-pass`로 처리** — 이때 owner=auto, 행은 ✅로 마킹됨. (단, CLOSE 진입 게이트는 §2.16의 별도 정책 적용)

**모드 × owner 매트릭스**:

| 모드 | 사용자 확인 행 처리 | owner 값 | status 값 |
|------|-------------------|---------|----------|
| interactive | 캡틴 발화 후 PM이 mark | `user` | `done` |
| agentic (CLOSE 진입 외) | PM이 auto-pass | `auto` | `done` |
| agentic (CLOSE 진입 행) | 사용자 발화 필수 (§2.16) | `user` | `done` |

---

#### 2.16 CLOSE 진입 게이트 자동 검증 (G-13)

state-template.md:52 "CLOSE 진입 게이트: 사용자의 확인된 지시가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다."를 도구가 강제한다.

**검증 알고리즘**:

1. **트리거**: `mark` 또는 `advance` 명령으로 `rows[N]`을 갱신하려 할 때 `rows[N].stage == "CLOSE"`이고 해당 행이 CLOSE 단계 첫 행(즉 `rows[N-1].stage != "CLOSE"`)인지 확인
2. **이전 단계 마지막 사용자 확인 행 식별**: `rows[N-1]`부터 역순으로 스캔하여 `item == "사용자 확인"`인 첫 행을 찾는다 (`prev_user_row`)
3. **검증 조건**:
   - `prev_user_row`가 존재해야 한다. 미존재 시: `{"ok": false, "error": "close_gate_violation", "violation_detail": "no preceding user confirmation row found"}` + exit 1
   - `prev_user_row.status == "done"`이어야 한다
   - `prev_user_row.owner == "user"`이어야 한다 (auto-pass 거부)
4. **위반 응답**:
   ```json
   {
     "ok": false,
     "error": "close_gate_violation",
     "violation_detail": "user confirmation row {prev_user_row.row_id} is not done with owner=user (status={prev.status}, owner={prev.owner})",
     "exit": 1
   }
   ```
5. **agentic 모드 거부 정책 (PLAN 결정)**:
   - agentic 모드에서도 CLOSE 진입 행 mark에 `--auto-pass`는 거부된다. 거부 응답:
     ```json
     {"ok": false, "error": "agentic_close_gate_requires_user", "row_id": N}
     ```
   - 근거: state-template.md:52 "이 규칙은 agentic 모드에서도 유지된다"
   - **운영 절차**: agentic 모드라도 CLOSE 진입 직전에 PM은 캡틴에게 보고 후 사용자 발화("확인"/"승인")를 받아 prev_user_row를 `--owner user`로 mark한 뒤 CLOSE 첫 행을 진행

6. **강제 우회**: `--force` 사용 시 검증 스킵. 단 STATE.md 의사결정 로그에 자동 기재 (§2.17 트리거 #8)

**적용 범위**:

- CLOSE 단계의 **첫 행**(stage 전환 행)에만 적용. CLOSE 단계 내부의 후속 행(예: `DONE.md 생성`, `State Gate`)은 일반 행 순서 강제만 적용 (§2.5/§2.6)

---

#### 2.17 의사결정 로그 자동 기재 트리거 (G-14, G-15)

**SSOT 표** — 8개 트리거가 STATE.md `## 의사결정 로그` 섹션에 행을 추가한다. §2.1 본문 표현("force flag used at row 0")은 이 표를 참조하는 것으로 단순화한다.

| # | 트리거 | 의사결정 로그 자동 기재 내용 (`결정` / `근거` 컬럼) | state.json 영향 |
|---|--------|----------------------------------------------|---------------|
| 1 | `init --force` 사용 | 결정: `force flag used at init` / 근거: `--note 인자 (필수)` | (없음) |
| 2 | `mark --auto-pass` 사용 | 결정: `agentic auto-pass at row {N}, item={item}` / 근거: `--note 인자 또는 "agentic mode"` | `rows[N].note = "agentic auto-pass: <--note>"` |
| 3 | `mark --force` (스코프 위반 우회) | 결정: `worker_scope_force at row {N}, requested_stage={requested}, actual_stage={actual}` / 근거: `--note 인자 (필수)` | `rows[N].note = "scope_force: <--note>"` |
| 4 | `status --set <전환>` | 결정: `current_status changed: {prev} → {next}` / 근거: `--note 인자 또는 "(none)"` | `current_status` 변경 |
| 5 | `add-row --after N` | 결정: `additional row inserted after row {N}: stage={stage}, item={item}, new_row_id={N+1}` / 근거: `--note 인자 또는 "additional work entry"` | `rows[]`에 신규 행 추가 |
| 6 | `gate-pass --start N` | 결정: `Gate Pass: rows {N}~{N+3}, stage={stage}` / 근거: `--note 인자 또는 "(none)"` | 4행 모두 `done` |
| 7 | `block --row N` | (자동 기재 안 함 — 블로커 섹션은 PM 별도 작성. 단 row.note는 기재) | `rows[N].note = "block: <--reason>"` |
| 8 | CLOSE 진입 게이트 `--force` 우회 | 결정: `close_gate_force at row {N}, prev_user_row_id={prev.row_id}, user_confirmation_missing` / 근거: `--note 인자 (필수)` | (없음) |
| 9 | Step 실패 + `status --set blocked` (§2.21.3 — v3 보강) | 결정: `Step {N} failed, current_status → blocked` / 근거: `--note "Step {N} failed: {reason}, rollback: {scope}"` | `current_status = blocked` |

**기재 동작 명세**:

- **위치**: STATE.md `## 의사결정 로그` 섹션의 표 마지막 행 다음에 1행 추가 (마커 영역 외부, 자유 텍스트 영역의 표)
- **표 형식**: `| # | 시점 | 결정 | 근거 |` 컬럼 그대로 (state-template.md:33-35)
- **`#` 컬럼**: 기존 표의 마지막 # + 1 (자동 증가). 표가 비어 있으면 1부터
- **`시점` 컬럼**: `node date.js datetime` 결과 (KST `YYYY-MM-DD HH:mm`)
- **`결정` / `근거` 컬럼**: 위 표의 명세 그대로
- **`--note` 필수 트리거**: 트리거 #1, #3, #8은 `--note` 인자 미제공 시 명령 자체를 거부 (`{"ok": false, "error": "note_required_for_force"}` + exit 1)
- **삽입 알고리즘** (정규식):
  ```python
  # STATE.md 본문에서 "## 의사결정 로그" 헤더 이후 표를 찾아 마지막 행 다음에 삽입
  pattern = r"(## 의사결정 로그\n\| # \| 시점 \| 결정 \| 근거 \|\n\|[-\| ]+\|\n)((?:\| .+ \|\n)*)"
  # 매치된 group(2)의 끝에 신규 행 1줄 추가
  ```
- **마커 영역 외부 보장**: `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->` 사이에는 절대 기재하지 않음 (마커 영역은 행 표 SSOT 전용)

**§2.1 단순화**: §2.1의 "force flag used at row 0 — reason: <text>" 문구는 본 §2.17 트리거 #1의 명세로 대체됨. §2.1은 이 표를 참조하는 형태로 유지.

---

#### 2.18 에러 코드 카탈로그 (SSOT — E-1 보강)

**목적**: §2.1~§2.17에 분산된 에러 코드를 1개 표로 통합. EXECUTE 워커가 코드 구현 시 본 표가 단일 진실 공급원이며, README.md / 단위 테스트 / 도구 응답 모두 본 카탈로그를 따른다.

**사용 규약**:
- 에러 코드는 영어 snake_case (`worker_scope_violation` 등)
- 응답 형식: `{"ok": false, "command": "<command>", "error": "<code>", ...추가 필드}` 단일 라인 JSON
- 종료 코드 컬럼: 0=ok / 1=violation,scope,validation / 2=internal,subprocess (T-3)
- "발생 명령" 컬럼이 다중일 때는 콤마 구분
- 모든 코드는 §2.x 인용을 가진다 (인용 0건이면 카탈로그 등재 불가)

| # | 에러 코드 | 발생 명령 | 종료 코드 | 의미 | 트리거 조건 | 인용 |
|---|---------|---------|---------|------|----------|------|
| 1 | `worker_scope_violation` | mark | 1 | 워커가 자기 단계 외 행 갱신 시도 | `mark --as-worker --worker-stage X`인데 `rows[N].stage != X` 또는 `item != "작업"`(EXECUTE Step 행 외) | §2.1, §2.4 |
| 2 | `marker_missing` | init(--import-existing 외), advance, mark, block, add-row | 1 | STATE.md `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->` 마커 누락 | 갱신 명령이 마커 영역을 찾지 못함. show만 fallback 출력으로 우회 (§2.14) | §2.1, T-6 |
| 3 | `already_initialized` | init | 1 | state.json이 이미 존재 | `state init` 호출 시 `<task-path>/state.json` 존재. `--force` 사용 시 우회 | §2.1, §2.17 트리거 #1, T-8 |
| 4 | `date_tool_failed` | init, advance, mark, block, add-row, status, gate-pass | 2 | `node ~/.opal/tools/date/date.js datetime` 호출 실패 | subprocess.run 비-0 종료 또는 stdout 비어있음. STATE.md 변경 없음(원자성) | §2.1, §2.11 G-5 |
| 5 | `import_failed` | init --import-existing | 1 | 기존 STATE.md 파싱 실패 | 마크다운 표 정규식 매칭 0건 또는 마커 누락 + 표 영역 추정 실패 | §2.5, T-13 |
| 6 | `invalid_status_transition` | status, (block의 자동 전환은 항상 허용) | 1 | current_status 전이 그래프(§2.11 G-7) 위반 | 예: `done → in_progress`(허용 안 됨) | §2.11 G-7 |
| 7 | `row_not_found` | mark, advance, block, add-row | 1 | `--row N` 또는 `--after N`의 N에 해당하는 행이 state.json에 없음 | `rows[]` 중 `row_id == N`인 객체 미존재 | §2.12 G-9 |
| 8 | `invalid_stage_enum` | add-row | 1 | `--stage` 인자가 §2.2 G-3 enum 16종에 없음 | 예: `--stage FOO` | §2.12 G-9 |
| 9 | `gate_pattern_mismatch` | gate-pass | 1 | `--start N`이 `QA Gate`로 시작하지 않거나 4행 패턴이 `[QA Gate, State Gate, PM Gate, State Gate]` 아님 | §2.13 G-10 시작 행 검증 / 연속 4행 검증 위반 | §2.13 G-10, R-10 |
| 10 | `gate_stage_mixed` | gate-pass | 1 | 4행이 동일 stage가 아님 | 예: 행 N=PLAN, N+1=EXECUTE | §2.13 G-10, R-10 |
| 11 | `state_not_initialized` | show, advance, mark, block, validate, add-row, status, gate-pass | 1 | state.json 미존재 | `<task-path>/state.json` 파일 없음 | §2.14 G-11 |
| 12 | `user_confirmation_owner_mismatch` | validate(검출만), mark(직접 발생 X) | 1 | 사용자 확인 행이 `done`인데 `owner != user` 그리고 `owner != auto` | validate가 violations에 추가 | §2.15 G-12 |
| 13 | `owner_flag_conflict` | mark | 1 | `--owner`와 `--auto-pass` 동시 사용 | 두 인자가 함께 지정됨 | §2.15 G-12 |
| 14 | `auto_pass_in_interactive_mode` | validate(검출만) | 1 | interactive 모드에서 사용자 확인 행이 `owner == auto`로 ✅ | mode==interactive ∧ row.owner==auto ∧ row.status==done | §2.15 G-12 |
| 15 | `close_gate_violation` | mark, advance | 1 | CLOSE 단계 첫 행 갱신 시 직전 단계 사용자 확인 행이 `owner != user` 또는 `status != done` 또는 미존재 | §2.16 G-13 검증 알고리즘 위반 | §2.16 G-13 |
| 16 | `agentic_close_gate_requires_user` | mark | 1 | agentic 모드 CLOSE 첫 행에 `--auto-pass` 사용 | mode==agentic ∧ rows[N].stage==CLOSE ∧ CLOSE 첫 행 ∧ `--auto-pass` 명시 | §2.16 G-13 |
| 17 | `note_required_for_force` | init --force, mark --force, mark CLOSE 첫 행 --force | 1 | `--force` 사용 시 `--note` 미제공 | 트리거 #1/#3/#8(§2.17)에서 `--note` 누락 | §2.17 트리거 #1/#3/#8, R-11 |
| 18 | `rows_spec_invalid_json` | init --rows-spec | 1 | `--rows-spec` 인자가 유효한 JSON 배열 아님 | json.loads 실패 또는 최상위가 배열 아님 | §2.20.1 (E-3 신규) |
| 19 | `skill_md_parse_error` | init --rows-from | 1 | `--rows-from` SKILL.md에서 행 0건 추출 또는 헤더 미발견 | §2.20.2 정규식 절차 단계 2/3/5 실패 | §2.20.2 (E-3 신규) |
| 20 | `task_path_not_found` | 모든 명령 | 1 | `<task-path>` 디렉토리 자체가 존재하지 않음 | pathlib `Path(task_path).is_dir() == False` | §2.18 (신규 — 모든 명령 공통 사전 검증) |
| 21 | `worker_stage_required` | mark | 1 | `--as-worker` 사용 시 `--worker-stage` 미지정 | argparse 단계에서 검출 | §2.4, §2.19 (init 인자 매트릭스) |
| 22 | `rows_input_conflict` | init | 1 | `--rows-spec`과 `--rows-from`이 동시 사용됨 | 두 인자 모두 지정 (배타) | §2.19, §2.20 |
| 23 | `rows_acts_not_implemented` | init --rows-acts | 2 | `--rows-acts` 인자 사용 — 본 태스크에선 시그니처만 정의, 동작 미구현 (R-13) | argparse가 `--rows-acts` 인자 발견 시 즉시 거부 응답 | §2.20.3, R-13 |

**누락 0건 검증 (PLAN.md grep)**:
- §2.1~§2.17에서 `error":` 또는 `에러` 토큰을 grep한 결과 17개 코드 모두 본 카탈로그에 등재됨
- 추가로 발견된 누락 코드 6건(`rows_spec_invalid_json`, `skill_md_parse_error`, `task_path_not_found`, `worker_stage_required`, `rows_input_conflict`, `rows_acts_not_implemented`) 등재 — §2.19/§2.20 신설로 식별
- 합계 **23종**

**EXECUTE 워커 구현 가이드**:
- `state_tool.py` 상단에 `ERROR_CODES` 상수 dict 정의 (코드 → 메시지 템플릿 매핑)
- 응답 헬퍼 `err(command, code, **fields)`가 본 카탈로그를 단일 진실 공급원으로 참조
- 단위 테스트(N-5)는 23종 코드 각각에 대해 최소 1개 케이스 작성 — happy path 외 23 케이스
- README.md(N-4) "에러 코드" 섹션은 본 표를 그대로 복사하여 사용자 가독 형태로 게재

---

#### 2.19 명령 인자 종합 매트릭스 (SSOT — E-2 보강)

**목적**: 9개 명령 × 모든 인자/플래그를 1개 표로 통합. argparse 구현 시 본 표가 SSOT. EXECUTE 워커가 별도 추측 없이 인자 정의를 그대로 코드에 옮길 수 있다.

**규약**:
- 인자 컬럼: long form만 표기 (short form 미도입 — TASK 미명시 + xlsx-tool도 long만 사용)
- 타입 컬럼: `string`/`int`/`flag`/`enum(...)` /`path`/`inline-json`
- 충돌 관계: 다른 인자와 동시 사용 불가하거나 함께 사용 필수인 경우 명시 + 위반 시 발생할 §2.18 에러 코드 인용

##### 2.19.1 `state init`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 (위반 시) | 인용 |
|------|---------|------|--------|-----------|---------------------|------|
| `<task-path>` (positional) | 필수 | path | - | 디렉토리 존재 필수 | task_path_not_found | §2.11 G-8 |
| `--skill` | 필수 | enum(opp/opd/opds/opdw/opwt/opgc/oppd/opsdd) | - | - | argparse choices error | §2.11 G-8 |
| `--mode` | 필수 | enum(interactive/agentic) | - | - | argparse choices error | §2.11 G-8 |
| `--task-title` | 선택 | string | (`<task-path>` 마지막 디렉토리명) | - | - | §2.11 G-8 |
| `--next-action` | 선택 | string | "PLAN 단계 진입" (또는 첫 단계가 TASK면 "TASK 단계 진행") | - | - | §2.11 G-8 |
| `--rows-spec` | 선택 | inline-json (배열) | - | `--rows-from`과 배타 | rows_input_conflict / rows_spec_invalid_json | §2.20.1 |
| `--rows-from` | 선택 | path | - | `--rows-spec`과 배타 | rows_input_conflict / skill_md_parse_error | §2.20.2 |
| `--rows-acts` | 선택 | inline-json | - | opsdd 전용. 본 태스크 범위 밖 (시그니처만) | (미구현 — exit 2 internal_error) | §2.20.3, R-13 |
| `--force` | 선택 | flag | false | `--note` 종속 (force 사용 시 필수) | already_initialized 우회 / note_required_for_force | §2.17 트리거 #1, T-8 |
| `--note` | 선택 (force 사용 시 필수) | string | null | - | note_required_for_force | §2.17 트리거 #1 |
| `--import-existing` | 선택 | flag | false | `--rows-spec`/`--rows-from`과 호환(보강 — fallback 시 함께 사용 가능) | import_failed | §2.5, T-13, E-4 |

##### 2.19.2 `state show`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.14 G-11 |
| `--format` | 선택 | enum(md/json/full) | "md" | - | argparse choices error | §2.14 G-11 |

##### 2.19.3 `state advance`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | T-7 |
| `--row` | 필수 | int | - | - | row_not_found, marker_missing, close_gate_violation, date_tool_failed | T-7, §2.16 |
| `--note` | 선택 | string | null | - | (없음 — 자유 텍스트 메모, state.json `rows[N].note`에 저장) | TASK F-2, §2.17 |

##### 2.19.4 `state mark`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | T-7 |
| `--row` | 필수 | int | - | - | row_not_found | T-7 |
| `--done` | 필수 | flag | - | - | (다른 status 전이는 본 도구 미지원) | T-7 |
| `--note` | 선택 (force 사용 시 필수) | string | null | `--force` 사용 시 필수 | note_required_for_force | §2.17 |
| `--as-worker` | 선택 | flag | false | `--worker-stage` 종속(없으면 worker_stage_required) | worker_scope_violation, worker_stage_required | T-10, §2.4 |
| `--worker-stage` | `--as-worker` 시 필수 | enum(stage 16종) | - | `--as-worker` 없이 사용 금지 | worker_stage_required | T-10, §2.2 G-3 |
| `--step` | 선택 (EXECUTE Step 진행 시) | string `N/M` 형식 | - | `--as-worker` 종속 권장 | (형식 위반 시 internal_error 2) | §2.11 G-6 |
| `--owner` | 선택 | enum(PM/worker/user/auto) | "PM"(default) | `--auto-pass`와 배타 | owner_flag_conflict | §2.15 G-12 |
| `--auto-pass` | 선택 | flag | false | `--owner`와 배타. agentic 모드 + CLOSE 첫 행 거부 | owner_flag_conflict, agentic_close_gate_requires_user | §2.17 트리거 #2, §2.16 G-13 |
| `--force` | 선택 | flag | false | `--note` 종속 | note_required_for_force, close_gate_violation 우회 | §2.17 트리거 #3, §2.17 트리거 #8 |

##### 2.19.5 `state block`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.1 |
| `--row` | 필수 | int | - | - | row_not_found | §2.1 |
| `--reason` | 필수 | string | - | - | (미제공 시 argparse error) | §2.17 트리거 #7 |

##### 2.19.6 `state validate`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.6, F-10 |

응답 형식: `{"ok": true|false, "command": "validate", "violations": [...], "violations_count": N}`. violations 배열 항목은 `{"code": "<§2.18 카탈로그 코드>", "row_id": N|null, "detail": "..."}` 객체. 0건이면 ok=true, ≥1이면 ok=false + exit 1.

##### 2.19.7 `state add-row`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.12 G-9 |
| `--after` | 필수 | int | - | - | row_not_found | §2.12 G-9 |
| `--stage` | 필수 | enum(stage 16종) | - | - | invalid_stage_enum | §2.12 G-9 |
| `--item` | 필수 | string (minLength 1) | - | - | (미제공 시 argparse error) | §2.12 G-9 |
| `--note` | 선택 | string | null | - | - | §2.17 트리거 #5 |

##### 2.19.8 `state status`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.11 G-7 |
| `--set` | 필수 | enum(in_progress/done/blocked/additional_work/additional_work_done) | - | - | invalid_status_transition | §2.11 G-7 |
| `--note` | 선택 | string | null | - | - | §2.17 트리거 #4 |

##### 2.19.9 `state gate-pass`

| 인자 | 필수/선택 | 타입 | 기본값 | 충돌 / 종속 | 에러 코드 | 인용 |
|------|---------|------|--------|-----------|---------|------|
| `<task-path>` | 필수 | path | - | - | task_path_not_found, state_not_initialized | §2.13 G-10 |
| `--start` | 필수 | int | - | - | row_not_found, gate_pattern_mismatch, gate_stage_mixed | §2.13 G-10 |
| `--note` | 선택 | string | null | - | - | §2.17 트리거 #6 |

##### 2.19.10 충돌/종속 매트릭스 요약

| # | 관계 유형 | 인자 A | 인자 B | 명령 | 위반 에러 코드 |
|---|---------|--------|--------|------|--------------|
| C-1 | 배타(XOR) | `--rows-spec` | `--rows-from` | init | rows_input_conflict |
| C-2 | 배타(XOR) | `--owner` | `--auto-pass` | mark | owner_flag_conflict |
| C-3 | 종속(A → B 필수) | `--as-worker` | `--worker-stage` | mark | worker_stage_required |
| C-4 | 종속(A → B 필수) | `--force` | `--note` | init, mark | note_required_for_force |
| C-5 | 종속(A → B 권장) | `--step` | `--as-worker` | mark | (권장이며 강제 거부 아님) |
| C-6 | 모드 제약 | `--auto-pass` + CLOSE 첫 행 | mode==agentic | mark | agentic_close_gate_requires_user |

**EXECUTE 워커 구현 가이드**:
- argparse 서브파서 9개를 `<command>` positional 다음에 정의
- 각 서브파서는 위 표의 인자 그대로 등록
- 종속/배타 검증은 argparse `mutually_exclusive_group` 활용 가능 (C-1, C-2). 그 외 종속(C-3, C-4)은 argparse 후 명시 검증 분기로 처리

---

#### 2.20 행 구성 외부 주입 형식 (SSOT — E-3 보강)

`state init`은 SKILL.md "STATE.md 도메인 치환값" 섹션의 행 목록을 도구가 직접 읽지 않고(§2.3 결정), 호출자(오케스트레이터/PM)가 외부에서 주입한다. 본 절은 주입 형식 2종(`--rows-spec` inline JSON / `--rows-from` SKILL.md 파싱) + 1종 시그니처 정의(`--rows-acts` opsdd ACT 동적, 미구현)의 명세.

##### 2.20.1 `--rows-spec <inline-json>` (PM/오케스트레이터 주입)

**입력 형식** — JSON 배열, 각 항목은 객체:

```json
[
  {"stage": "TASK", "item": "작업"},
  {"stage": "TASK", "item": "TASK.md 생성"},
  {"stage": "TASK", "item": "사용자 확인"},
  {"stage": "PLAN", "item": "작업"},
  {"stage": "PLAN", "item": "PLAN.md 생성"},
  {"stage": "PLAN", "item": "QA Gate"},
  {"stage": "PLAN", "item": "QA-PLAN.md 생성"},
  {"stage": "PLAN", "item": "State Gate"},
  {"stage": "PLAN", "item": "PM Gate"},
  {"stage": "PLAN", "item": "State Gate"},
  {"stage": "PLAN", "item": "사용자 확인"},
  {"stage": "EXECUTE", "item": "작업"},
  {"stage": "EXECUTE", "item": "QA Gate"},
  {"stage": "EXECUTE", "item": "QA-EXECUTE.md 생성"},
  {"stage": "EXECUTE", "item": "State Gate"},
  {"stage": "EXECUTE", "item": "PM Gate"},
  {"stage": "EXECUTE", "item": "State Gate"},
  {"stage": "EXECUTE", "item": "사용자 확인"},
  {"stage": "CLOSE", "item": "DONE.md 생성"},
  {"stage": "CLOSE", "item": "State Gate"}
]
```

(opp 표본 20행 — `opal/skills/opal-pilot-project/SKILL.md:122-143` 그대로)

**필드 명세**:

| 필드 | 필수/선택 | 타입 | 검증 | 인용 |
|------|---------|------|------|------|
| `stage` | 필수 | string | §2.2 G-3 enum 16종 (TASK/ANALYSIS/PLAN/EXECUTE/TEST/WIREFRAME/QA/SPEC/REVIEW/DESIGN/VERIFY/SCAN/CHECK/REPORT/WBS/CLOSE) | §2.2 G-3 |
| `item` | 필수 | string | minLength 1 | §2.2 G-4 |
| `owner_default` | 선택 | string | enum(PM/worker/user/auto). 누락 시 "PM" | §2.15 G-12 |

**`init` 시 자동 처리** (모든 행 공통):
- `row_id` = 1부터 배열 순서대로 증가 (1-based)
- `status` = `pending`
- `status_label` = `⬜`
- `timestamp` = `null`
- `note` = `null`
- `owner` = `owner_default` 또는 PM(기본)

**agentic 모드 자동 마킹** (`--mode agentic` + 본 입력 형식 공통):
- `item == "사용자 확인"` 행 중 **CLOSE 단계가 아닌 행**은 자동으로:
  - `status = "na"`, `status_label = "-"`, `owner = "auto"`, `note = "agentic auto-na at init"`
- **CLOSE 단계 사용자 확인 행은 `pending`(⬜) 그대로 유지** (§2.16 G-13 — CLOSE 진입 게이트는 사용자 발화 필수)
- 이 자동 마킹 규칙은 §2.20.2도 동일 적용

**파싱 실패 응답**:
```json
{"ok": false, "command": "init", "error": "rows_spec_invalid_json", "detail": "<json.JSONDecodeError 메시지 또는 'top-level not array'>"}
```
exit 1.

**파싱 알고리즘**:
1. `argparse`로 `--rows-spec` 문자열 수신
2. `json.loads(<인자>)` 호출 → `JSONDecodeError` 시 위 응답
3. 결과가 list 아니면 위 응답
4. 각 항목 검증: dict 타입 / `stage`·`item` 키 존재 / `stage` ∈ enum / `item` minLength 1
5. 검증 실패 시 `rows_spec_invalid_json` + `detail` 필드에 어떤 항목/필드가 위반인지 명시
6. 모두 통과 시 행 객체 배열 생성

##### 2.20.2 `--rows-from <path-to-skill.md>` (SKILL.md 자동 파싱)

8개 opal-pilot-* SKILL.md의 "STATE.md 도메인 치환값" 섹션 마크다운 표를 정규식으로 파싱.

**파싱 절차 (확정 정규식)**:

1. **파일 Read**: `Path(<--rows-from 인자>).read_text(encoding="utf-8")`
2. **헤더 패턴 매칭**: 정규식 `^(##|###|####)\s+.*STATE\.md\s*도메인\s*치환값.*$` (멀티라인 모드)
   - 매치 0건 시: `{"ok": false, "command": "init", "error": "skill_md_parse_error", "path": "<path>", "reason": "header not found"}` + exit 1
3. **섹션 본문 추출**: 매치 위치부터 다음 같은 레벨 또는 상위 레벨 헤더 직전까지
4. **첫 번째 마크다운 표 식별**: 본문 내 `^\| # \| 단계 \| 항목 \| 상태 \| 시점 \|` 또는 `^\| # \| Phase \| 항목 \| 상태 \| 시점 \|` 헤더 라인 매칭
   - 헤더 매치 0건 시: `skill_md_parse_error`, `reason: "table header not found"` + exit 1
5. **데이터 행 추출**: 헤더 + 구분선(`|---|...`) 다음부터 빈 줄 또는 코드 블록 종료(```` ``` ````) 또는 다음 헤더(`^#`) 직전까지
6. **각 행 파싱 정규식**:
   ```
   ^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([⬜🔄✅❌\-])\s*\|.*?\|\s*$
   ```
   - 캡처 그룹: (1) row_id (2) stage (3) item (4) status_label
   - 시점 컬럼은 무시(파싱 후 모두 `null`로 초기화)
7. **추출 행 수가 0이면**: `skill_md_parse_error`, `reason: "no rows found"` + exit 1
8. **status_label → status 매핑** (T-2):
   - ⬜ → pending
   - 🔄 → in_progress
   - ✅ → done
   - ❌ → failed
   - "-" → na
9. **stage 검증**: 추출된 stage 값이 §2.2 G-3 enum 16종에 없으면 `invalid_stage_enum` + 정확한 위반 위치 detail
10. **agentic 자동 마킹**: §2.20.1과 동일 규칙 적용 (CLOSE 사용자 확인 행 제외)

**8개 SKILL.md 파싱 표본 검증 결과** (Step 7/16 회귀 시 검증):

| SKILL.md | 표 위치 (라인) | 행 수 | 비고 |
|---------|------------|-------|------|
| opal-pilot-project | 122-143 | 20 | opp 표준 — Step 7 회귀 표본 |
| opal-pilot-dev | (해당 섹션 내 표) | 24~ | EXECUTE Step 행 가변 |
| opal-pilot-dev-short | (해당 섹션 내) | ~17 | TASK→PLAN→EXECUTE→TEST→CLOSE 단순 |
| opal-pilot-dev-wireframe | (해당 섹션 내) | ~14 | WIREFRAME 단계 |
| opal-pilot-write-tech | (해당 섹션 내) | ~22 | QA 단계 추가 |
| opal-pilot-gc | (해당 섹션 내) | ~14 | SCAN/CHECK/REPORT |
| opal-pilot-project-dev | (해당 섹션 내) | ~30 | Phase 컬럼 변형 — 헤더 정규식이 "Phase" 토큰도 매칭해야 함(절차 4 정규식) |
| opal-pilot-sdd | 305-345 | 35+ | EXECUTE-LOOP의 ACT 행은 단일 "ACT 실행 (상세: ACT 목록 참조)" 행으로 합쳐짐. ACT 동적 삽입은 §2.20.3 미구현 |

**Step 16 회귀 시**: opp(20행) + opd(opal-pilot-dev) 2개 SKILL.md에 대해 `--rows-from` 호출하여 추출 행 수 / 정합성 / agentic 자동 마킹 모두 검증.

##### 2.20.3 `--rows-acts <inline-json>` (opsdd ACT 동적 — 시그니처만 정의, 본 태스크 범위 밖)

opsdd 35행+ACT 동적 삽입 처리는 본 태스크 범위 밖이며, 별도 후속 태스크에서 진행한다 (R-13 추가).

**시그니처 정의만 (구현 X)**:
```
state init <task-path> --skill opsdd --mode <mode> --rows-from <skill.md> --rows-acts '<json>'
```

본 태스크에서 `--rows-acts` 인자가 명시되면 도구는 다음 응답을 반환하고 종료한다:
```json
{"ok": false, "command": "init", "error": "rows_acts_not_implemented", "note": "opsdd ACT dynamic injection is out of scope for task 134. Track at R-13."}
```
exit 2 (internal_error — 미구현이므로 추후 구현 시 안전하게 동작 변경 가능).

**향후 구현 시 (별도 태스크) 예상 동작**:
- `--rows-acts`는 `[{"act_id": "ACT-1", "label": "...", "ts_count": N}, ...]` 형식
- `--rows-from`이 추출한 행 중 EXECUTE 단계의 "ACT 실행" 행을 ACT 개수만큼 확장 삽입
- 본 태스크는 opp/opd 표본만 검증 — opsdd 35행+ACT는 후속

---

#### 2.21 Step 실패 시 롤백 정책 (E-6 보강)

**목적**: EXECUTE 중 16개 Step 중 어느 하나가 실패할 때 PM이 어떤 범위로 롤백하고 어떻게 재시작/에스컬레이션할지의 SSOT.

**전제**: opal-harness.md §1 Guards 사전 점검(EXECUTE 진입 직전 git status 클린)이 만족되어 EXECUTE 워커가 변경한 파일만 git checkout 대상이 된다. 본 태스크는 "개발" 범위이므로 `~/.opal/`에 직접 배포된 파일은 변경하지 않으며 모든 롤백은 소스 경로(`opal/`, `scripts/`, `tasks/134-.../`)에 한정된다 ([MUST] D-12 §개발 vs 배포 경계).

##### 2.21.1 Step별 롤백 범위 매트릭스

| 실패한 Step | 롤백 범위 | 처리 방식 | 캡틴 에스컬레이션 |
|------------|---------|---------|---------------|
| Step 1 (도구 본체 + 래퍼 + 스키마 + README) | `opal/tools/state-tool/` 전체 | 디렉토리 삭제 또는 `git clean -fd opal/tools/state-tool/` | 즉시 — 설계 결함 가능성 (캡틴 결정 필요) |
| Step 2 (단위 테스트) | `opal/tools/state-tool/tests/` | `git checkout opal/tools/state-tool/tests/` | 1회 재시도 후 에스컬레이션 (테스트 케이스 갭 의심) |
| Step 3 (하네스 §3+§9) | `opal/core/references/opal-harness.md` | `git checkout opal/core/references/opal-harness.md` | 1회 재시도 후 에스컬레이션 |
| Step 4 (state.md / state-template.md / task-process.md) | 3개 파일 | `git checkout opal/core/references/harness/state.md opal/core/references/harness/state-template.md opal/core/references/harness/task-process.md` | 1회 재시도 후 에스컬레이션 |
| Step 5 (op-task SKILL.md) | `opal/skills/op-task/SKILL.md` | `git checkout opal/skills/op-task/SKILL.md` | 1회 재시도 후 에스컬레이션 |
| Step 6 (opp SKILL.md) | `opal/skills/opal-pilot-project/SKILL.md` | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 7 (134 자기 자신 회귀) | `tasks/134-.../state.json` 삭제 + `tasks/134-.../STATE.md` git checkout | E-4 fallback 절차 우선 (3.1 → 3.2 → 3.3) | E-4 3.3 (수동 정정)도 실패 시 즉시 — 도구 import 정확도 결함 |
| Step 8 (7개 pilot 일괄) | 실패한 pilot SKILL.md만 | 실패한 pilot만 `git checkout`, 성공한 6개는 유지 | 실패 pilot 1회 재시도 후 에스컬레이션 |
| Step 9 (op-dev-execute 가이드) | `opal/skills/op-dev-execute/references/execute-guide.md` | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 10 (에이전트 8개) | 실패한 AGENT.md만 | 실패한 파일만 `git checkout`, 성공한 것은 유지 | 1회 재시도 후 에스컬레이션 |
| Step 11 (가이드 실질 갱신 3개) | 실패한 가이드 파일만 | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 12 (가이드 단순 참조 8개) | 실패한 가이드 파일만 | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 13 (하네스 4개 — pm-review-gate / additional-work / interactive / agentic) | 4개 파일 모두 | `git checkout` 4개 파일 | 1회 재시도 후 에스컬레이션 |
| Step 14 (tools.md) | `opal/core/references/tools.md` | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 15 (install-mac.sh) | `scripts/install-mac.sh` | `git checkout` | 1회 재시도 후 에스컬레이션 |
| Step 16 (dummy 회귀) | dummy 태스크 폴더(`/tmp/test-dummy-*`)만 삭제 | `rm -rf /tmp/test-dummy-*` 또는 `tasks/dummy-*/` | 즉시 — 회귀 실패는 본체 결함 가능성 (Step 1~15 결함 의심) |

##### 2.21.2 의존 관계 보존 원칙

- **이전 Step ✅ + 현재 Step 실패** 시: 이전 Step 변경은 유지(롤백 안 함). 현재 Step 변경만 git checkout
- **단**, Step 실패가 이전 Step의 결함 때문임이 명백한 경우 — 예: Step 5에서 op-task SKILL.md 갱신 후 Step 7 회귀 실패 → op-task SKILL.md의 state init 호출 시그니처가 도구 시그니처와 불일치한 것이 원인 — PM이 캡틴에게 보고 후 결정 (이전 Step 회귀 가능)
- git checkout 대상은 EXECUTE 워커가 변경한 파일만이며, EXECUTE 진입 직전 git status가 클린 상태(opal-harness.md §1 Guards 사전 점검)이므로 변경 파일은 `git status`로 식별 가능

##### 2.21.3 부분 진행 상태 추적

- EXECUTE 중 Step N 실패 시 다음 절차:
  1. PM이 `state block --row N --reason "Step {N} failed: <원인 요약>"` 호출 → 134 STATE.md 행 N → ❌
  2. PM이 STATE.md 블로커 섹션에 자유 텍스트로 실패 원인 + 롤백 결과 + 재시도 계획 작성 (state-tool 범위 밖, 자유 텍스트 영역)
  3. state.json `current_status` → `blocked` 자동 전환 (block 명령의 자동 효과 — §2.11 G-7)
  4. 캡틴이 재시작 결정 시 PM이 `state status --set in_progress --note "재시작: <근거>"` 호출 → §2.17 트리거 #4 자동 기재
  5. 롤백 후 다시 Step N부터 진행
- §2.17 트리거 표 #9 추가 (보강) — `Step 실패 + status --set blocked` 시 의사결정 로그 자동 기재 내용:
  - 결정: `Step {N} failed, current_status → blocked`
  - 근거: `--note "Step {N} failed: {reason}, rollback: {scope}"`

##### 2.21.4 캡틴 즉시 에스컬레이션 트리거

다음 케이스는 1회 재시도 없이 즉시 캡틴에게 보고:

- Step 1 실패 (도구 본체) — 설계 결함 가능
- Step 7 실패 후 E-4 fallback 3.3(수동 정정)도 실패 — 도구 import 정확도 결함
- Step 16 실패 — 본체(Step 1~15) 결함 가능
- 동일 Step 2회 연속 실패 — 1회 재시도 후 다시 실패 시
- `git checkout` 자체가 실패 (예: 파일 권한 / 머지 충돌) — 환경 결함

**EXECUTE 워커 구현 가이드**:
- 본 §2.21이 EXECUTE 절차의 일부 — 워커는 Step 진행 중 실패 감지 시 본 매트릭스를 그대로 따른다
- 캡틴 에스컬레이션은 PM이 보고 형식으로 수행 — 워커는 PM에게 실패 보고만 (직접 캡틴 호출 X)

---

## 3. 실행 체크리스트

> 총 16개 Step | Phase 9개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1, 2 | 순차 | Step 2(테스트)는 Step 1(본체) 의존 |
| 2 | 3, 4 | 순차 | Step 4는 Step 3 의존 |
| 3 | 5 | 순차 | Step 4 의존 |
| 4 | 6 | 순차 | Step 5 의존 |
| 5 | 7 | 순차 | Step 6 의존 — 회귀 게이트 |
| 6 | 8, 9, 10 | 병렬 | 서로 독립 (다른 파일 그룹) |
| 7 | 11, 12 | 병렬 | 가이드 그룹 — 다른 파일 |
| 8 | 13, 14, 15 | 순차 | 13 후 14, 15는 병렬 가능하나 작은 양이라 순차로 처리 |
| 9 | 16 | 순차 | 모든 갱신 완료 후 최종 회귀 |

### Step 1: state-tool 본체 + 래퍼 + 스키마 + README 작성

- [ ] 완료
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/run.sh`, `opal/tools/state-tool/schema/state.schema.json`, `opal/tools/state-tool/README.md`
- **작업 내용**:
  1. `run.sh` 작성 (xlsx-tool 패턴 그대로 차용 — D-10:1-12)
  2. `state_tool.py` **9개** 서브 명령(`init`, `show`, `advance`, `mark`, `block`, `validate`, `add-row`, `status`(G-7), `gate-pass`(G-10)) 구현
     - `init`: §2.11 G-8 시그니처 + STATE.md 자유 텍스트 영역 자동 생성
     - `advance`/`mark`: §2.11 G-5/G-6 자동 갱신(최종 갱신 헤더 + `## 현재 상태` 4줄) 포함. `mark --as-worker --step <N/M>`은 EXECUTE Step 진행 표기
     - `block`: §2.17 트리거 #7 (row.note 기재만, 의사결정 로그 미기재)
     - `add-row`: §2.12 G-9 알고리즘 (row_id 재정렬 + current_status 자동 전환)
     - `status`(신규): §2.11 G-7 시그니처 + 전이 그래프 검증
     - `gate-pass`(신규): §2.13 G-10 4행 일괄 처리
     - `mark`/`advance`가 CLOSE 첫 행을 갱신할 때 §2.16 G-13 검증 자동 호출
     - 사용자 확인 행 갱신 시 §2.15 G-12 owner 처리
     - 모든 갱신 명령에 §2.17 의사결정 로그 자동 기재 분기
     - 표준 항목 상수 `STANDARD_ITEMS` / `GATE_PATTERN` (§2.2 G-4) 코드 내 정의
  3. JSON Schema Draft-07 작성 (§2.2 G-1/G-2/G-3 보강 — `created_at`/`updated_at`/`stage` enum / `timestamp` 패턴)
  4. README.md 작성 — **9개** 명령 시그니처 + 종료 코드 + 에러 코드 + 사용 예시 (`status` / `gate-pass` 포함). §2.11~§2.17 SSOT 링크 명시
- **완료 기준**:
  - 9개 명령 `--help` 모두 응답
  - 모든 응답이 단일 라인 JSON
  - 종료 코드가 T-3(0/1/2) 규약 준수
  - 마커(T-6) 있는 STATE.md에 대한 `init`이 정상 동작 — 자유 텍스트 3개 섹션(§2.11 G-8) 함께 생성
  - state.json schema에 `created_at`/`updated_at`/`stage` enum/`timestamp` 패턴 모두 강제 검증
- **테스트**: 수동 호출 — `bash opal/tools/state-tool/run.sh init /tmp/test-task --skill opp --mode interactive --task-title "테스트" --next-action "PLAN 진입" --rows-spec '[{"stage":"TASK","item":"작업"}]'` 실행하여 state.json + STATE.md(자유 텍스트 영역 포함) 생성 확인. **단, 본 태스크는 "개발" 범위이므로 `~/.opal/`에 직접 배포 금지** ([MUST] D-12 §개발 vs 배포 경계). 검증은 소스 경로 `opal/tools/state-tool/run.sh` 직접 호출로 수행
- **의존**: 없음

### Step 2: 단위 테스트 작성·통과

- [ ] 완료
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: **9개** 서브 명령 × happy path + 주요 에러 시나리오:
  - 기본: 권한 위반, 순서 위반, 마커 손실, 멱등성 위반, 워커 스코프 위반, `--force` 우회, `--import-existing` 파싱
  - **§2.11 G-5**: STATE.md "최종 갱신" 헤더 자동 갱신 — 모든 갱신 명령 후 1번째 줄이 date.js 결과로 교체됨
  - **§2.11 G-6**: `## 현재 상태` 4줄 자동 갱신 — `advance`(`- 진행:` 갱신), `mark` CLOSE 마지막 행(`- 상태: 완료`), `add-row`(`- 상태: 추가작업중`), `block`(`- 상태: 블로커`)
  - **§2.11 G-7**: `state status --set` 8개 전이 케이스 — happy path × 5(허용 전환) + 거부 × 3(invalid_status_transition)
  - **§2.11 G-8**: `state init`이 자유 텍스트 3개 섹션(`## 의사결정 로그` 빈 표 / `## 블로커` "없음" / `## 다음 액션`)을 정확히 생성
  - **§2.12 G-9**: `add-row` row_id 재정렬 검증 — N+1 이후 모든 row_id가 +1 됨, schema validate 통과, current_status 자동 전환
  - **§2.13 G-10**: `gate-pass` happy path(4행 일괄 ✅) + `gate_pattern_mismatch` 거부 + `gate_stage_mixed` 거부
  - **§2.14 G-11**: `state show --format md|json|full` 3종 + 마커 손실 fallback 3종(헤더 명시/marker_present 필드/주석 prepend)
  - **§2.15 G-12**: 사용자 확인 행을 `--owner user` 없이 mark 시 `validate`가 `user_confirmation_owner_mismatch` 반환. `--auto-pass` 명시 시 owner=auto 자동 저장. interactive 모드에서 owner=auto 행이 ✅이면 `auto_pass_in_interactive_mode`
  - **§2.16 G-13**: CLOSE 첫 행 mark 시 prev_user_row 미통과 → `close_gate_violation`. agentic 모드 + `--auto-pass`로 CLOSE 첫 행 시도 → `agentic_close_gate_requires_user`. `--force` 우회 시 의사결정 로그 자동 기재
  - **§2.17 G-14/G-15**: 8개 트리거 각각에 대해 STATE.md 의사결정 로그 표에 정확히 1행씩 추가됨. 트리거 #1/#3/#8은 `--note` 미제공 시 `note_required_for_force` 거부
  - **자유 텍스트 영역 보존**: `init` 후 `mark`/`advance`/`block`/`add-row` 호출 시 의사결정 로그(§2.17 자동 기재 외부) / 블로커 섹션 / 다음 액션 섹션 본문이 변경 0건
- **완료 기준**: `python3 -m unittest opal/tools/state-tool/tests/test_state_tool.py` 0 fail, 0 error. 테스트 케이스 수 최소 40건 (9개 명령 × happy + 보강 시나리오 31종 = 40+)
- **테스트**: 위 명령 실행 결과 확인
- **의존**: Step 1

### Step 3: 하네스 §3 + §9 갱신 (`opal-harness.md`)

- [ ] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §3 stub(116-123)에 `[MUST] state-tool 호출만 허용` 추가. §9 도구 테이블(211-213)에 `state-tool` 행 추가
- **완료 기준**: grep으로 `state-tool` 토큰이 §3 / §9 양쪽에 출현 확인
- **테스트**: `grep -n state-tool opal/core/references/opal-harness.md`
- **의존**: Step 2 (도구 동작 검증 후 갱신)

### Step 4: state.md / state-template.md / task-process.md 갱신

- [ ] 완료
- **파일**: `opal/core/references/harness/state.md`, `opal/core/references/harness/state-template.md`, `opal/core/references/harness/task-process.md`
- **작업 내용**:
  - state.md(13-32) — 갱신 이벤트 표에 `갱신 명령` 컬럼 추가 + `[MUST] state-tool 호출만 허용` 블록. **§2.11 G-6 매핑 그대로 표기** (각 이벤트 → state-tool 명령 + STATE.md `## 현재 상태` 4줄 자동 갱신 규칙). EXECUTE Step 행은 `mark --as-worker --step <N/M>` 표기
  - state-template.md(상단) — `[MUST] LLM 직접 작성 금지 — state init 호출` + 마커 형식 명세. **§2.11 G-8 자유 텍스트 3개 섹션(`## 의사결정 로그` / `## 블로커` / `## 다음 액션`) 자동 생성 명세 추가** (state-template.md:33-41 영역). `--task-title` / `--next-action` 인자 표기
  - task-process.md(31번 항목) — `[필수] state init` 호출 표현으로 교체. `--task-title` / `--next-action` 인자 명시
- **완료 기준**: 3개 파일에서 state-tool 호출 표현이 일관(예: 모두 `~/.opal/tools/state-tool/run.sh ...` 절대 경로 사용). state.md 갱신 이벤트 표가 §2.11 G-6 매핑과 일관, state-template.md가 §2.11 G-8 자유 텍스트 영역 자동 생성 명세 포함
- **테스트**: grep + 본문 정독 + state.md 표 ↔ §2.11 G-6 표 ↔ state-template.md ↔ §2.11 G-8 일관성 교차 검증
- **의존**: Step 3

### Step 5: op-task SKILL.md 갱신

- [ ] 완료
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: 186-188 STATE.md 리마인더 → `state init` 호출 명시 + `[MUST] state-tool로만 생성` 추가
- **완료 기준**: 본문에 `state init` 토큰 출현
- **테스트**: grep
- **의존**: Step 4

### Step 6: opp(opal-pilot-project) SKILL.md 갱신

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: 본문 "STATE.md 갱신" 표현을 `state-tool` 호출로 교체. 112-144 "STATE.md 도메인 치환값"의 행 목록은 SSOT로 유지. agentic 활성화(163) 부근에 auto-pass 표기 추가
- **완료 기준**: 본문에서 LLM 직접 갱신 표현이 0건, state-tool 호출 표현이 출현
- **테스트**: grep `STATE\.md` → 모두 state-tool 호출 컨텍스트 확인
- **의존**: Step 5

### Step 7: 134 자기 자신 회귀 테스트

- [ ] 완료
- **파일**: `tasks/134-260501-opp-pipeline-state-tool/STATE.md` + state.json (신규)
- **작업 내용** (E-4 보강 — fallback 절차 포함):
  1. `bash opal/tools/state-tool/run.sh init tasks/134-260501-opp-pipeline-state-tool/ --skill opp --mode interactive --import-existing` 실행
  2. **성공 시**: state.json 생성 + STATE.md 마커 영역 교체 확인 + 자유 텍스트 영역(의사결정 로그 / 블로커 / 다음 액션) 보존 확인 (§2.11 G-8 import 정책) → Step 7 정상 완료
  3. **실패 시 fallback 절차** (`import_failed` 반환 — §2.18 카탈로그 5번):
     - **3.1**: PM이 STATE.md 표를 정독하여 행 목록을 §2.20.1 형식 JSON 배열로 수동 변환 (134의 경우 opp 표준 20행 — `opal/skills/opal-pilot-project/SKILL.md:122-143` 그대로)
     - **3.2**: `bash opal/tools/state-tool/run.sh init tasks/134-260501-opp-pipeline-state-tool/ --skill opp --mode interactive --rows-spec '<수동 변환 JSON 배열>' --import-existing --force --note "fallback: import-existing parsing failed at first attempt"` 재시도. `--rows-spec`이 우선 적용되어 행 구성을 강제 주입하면서, `--import-existing`은 자유 텍스트 영역 보존 역할만 수행
     - **3.3**: 그래도 실패 시 PM이 STATE.md를 수동 정정(마커 삽입 / 표 재구성) + state.json을 §2.2 스키마대로 수동 작성 (rare case) → `state validate` violations 0건 확인. 3.3도 실패 시 캡틴 즉시 에스컬레이션(§2.21.4)
  4. `state validate` violations 0건 확인
  5. 이후 진행 시 `state mark` / `state advance` / `state gate-pass`만 사용 (직접 마크다운 편집 금지 — [MUST])
  6. **§2.15 G-12 사용자 확인 행 갱신 검증**: 본 134 STATE.md의 사용자 확인 행(현 STATE.md 행 3 `TASK 사용자 확인`, 행 11 `PLAN 사용자 확인`, 행 18 `EXECUTE 사용자 확인`)을 `mark --owner user --note "캡틴 확인: ..."` 호출로 갱신했을 때 owner=user 저장 + validate에서 `user_confirmation_owner_mismatch` 0건 확인
  7. **§2.16 G-13 CLOSE 진입 게이트 검증**: 행 18(EXECUTE 사용자 확인)이 ✅ + owner=user인 상태에서만 행 19(CLOSE DONE.md 생성) mark 가능. 행 18을 `--auto-pass` 또는 owner≠user로 ✅ 처리한 상태에서 행 19 mark 시도 시 `close_gate_violation` 발생 확인
- **완료 기준**: violations 0건 + state.json 20개 행 모두 정확히 임포트(opp 표준 20행 행 구성, opal-pilot-project SKILL.md:122-143) + STATE.md 의사결정 로그/블로커/다음 액션 영역 보존 + 사용자 확인 행 owner=user 정합 + CLOSE 진입 게이트 정상 차단. **fallback 시나리오까지 포함하여**: 의도적 깨진 STATE.md(마커 누락 또는 표 깨짐) 표본으로 import-existing 호출 → import_failed 트리거 → 3.2 재시도 절차로 정상 복구되는지 검증 (Step 16 dummy 회귀에 추가 검증)
- **테스트**: 수동 검증 — state.json `rows[]` 길이 = 20 (기존 STATE.md 표 행 수와 일치). G-12/G-13 시나리오 양쪽 별도 검증. fallback 시나리오는 Step 16에서 dummy 표본으로 추가 검증
- **의존**: Step 6

### Step 8: 나머지 7개 pilot SKILL.md 일괄 갱신 (병렬 가능)

- [ ] 완료
- **파일**: `opal-pilot-{dev, dev-short, dev-wireframe, gc, project-dev, sdd, write-tech}/SKILL.md` (opp 제외 7개)
- **작업 내용** (E-5 보강 — 표준 교체 패턴 매트릭스 적용): 본문 "STATE.md 갱신" 표현을 아래 표준 매트릭스 8개 패턴 그대로 일관 적용. "STATE.md 도메인 치환값"은 SSOT 유지. 각 파일별 특이사항 — sdd는 ACT 목록 SSOT 보존(D-18), oppd는 검증 루프 로그 자유 텍스트 유지

  **표준 교체 패턴 매트릭스 (E-5)**:

  | # | Before (옛 마크다운 표현) | After (state-tool 호출) | 근거 |
  |---|----------------------|--------------------|------|
  | P-1 | "PM이 STATE.md 행 N을 ✅로 갱신" | "PM이 `~/.opal/tools/state-tool/run.sh mark <task-path> --row N --done` 호출" | T-7 mark, §2.19.4 |
  | P-2 | "STATE.md 파이프라인 현황판 테이블에서 QA Gate 행 → ✅" 또는 "Gate 4행 ✅로 갱신" | "PM이 `state mark --row N --done` 호출. **Gate 4행은 `state gate-pass --start N` 1회 호출로 일괄 처리 가능**(opp/opd 등 표준 행 구성 한정)" | §2.13 G-10, §2.19.9, R-10 |
  | P-3 | "단계 시작 시 작업 행을 🔄로 갱신" | "PM이 `state advance --row N` 호출" | T-7 advance, §2.19.3 |
  | P-4 | "워커가 EXECUTE Step 진행 시 갱신" 또는 "EXECUTE Step N 완료 시 STATE.md 갱신" | "워커가 `state mark --row N --done --as-worker --worker-stage EXECUTE --step <N/M>` 호출" | T-10, §2.11 G-6, §2.19.4 |
  | P-5 | "사용자 확인 시 행을 ✅로 갱신" | "PM이 `state mark --row N --done --owner user --note '캡틴 확인: ...'` 호출" | §2.15 G-12, §2.19.4 |
  | P-6 | "추가작업 행 추가" 또는 "CLOSE 단계 재진입 시 행 추가" | "PM이 `state add-row --after N --stage CLOSE --item '...'` 호출 — current_status 자동 `additional_work` 전환. 추가작업 종료 시 `state status --set additional_work_done`" | §2.12 G-9, §2.11 G-7, §2.19.7, §2.19.8 |
  | P-7 | "블로커 발생 시 행 ❌" | "PM이 `state block --row N --reason '...'` 호출. STATE.md 블로커 섹션 자유 텍스트는 PM 별도 작성(state-tool 범위 밖)" | §2.1, §2.19.5 |
  | P-8 | "agentic 자율 통과" 또는 "agentic 모드에서 PM 판단으로 통과" | "PM이 `state mark --row N --done --auto-pass --note '<판단 근거>'` 호출 — `note`에 'agentic auto-pass: <근거>' 자동 기재. **단, CLOSE 첫 행은 `--auto-pass` 거부**(`agentic_close_gate_requires_user`) — 캡틴 발화 후 `--owner user`로 처리" | §2.17 트리거 #2, §2.16 G-13, §2.19.4 |

  **7개 pilot별 적용 행 수 예상 (참고용)**:

  | pilot | 적용 패턴 (예상) | 비고 |
  |-------|--------------|------|
  | opal-pilot-dev (opd) | P-1, P-2, P-3, P-4(EXECUTE Step), P-5, P-7, P-8 | EXECUTE Step 행 가변 |
  | opal-pilot-dev-short (opds) | P-1, P-2, P-3, P-5, P-7, P-8 | 단순 |
  | opal-pilot-dev-wireframe (opdw) | P-1, P-2, P-3, P-5, P-7, P-8 | WIREFRAME 단계 |
  | opal-pilot-gc (opgc) | P-1, P-2, P-3, P-5, P-7 | SCAN/CHECK/REPORT |
  | opal-pilot-project-dev (oppd) | P-1, P-2(주의 — 비표준 행 구성), P-3, P-4, P-5, P-6(추가작업 빈번), P-7, P-8. **검증 루프 로그는 자유 텍스트 유지** | 비표준 단계 — `gate-pass` 사용 제한(R-10) |
  | opal-pilot-sdd (opsdd) | P-1, P-3, P-4(ACT 진행), P-5, P-7, P-8. **ACT 목록 SSOT 보존, gate-pass 사용 제한** | 35행+ACT, gate_pattern_mismatch 거부 (R-10) |
  | opal-pilot-write-tech (opwt) | P-1, P-2, P-3, P-5, P-7, P-8 | QA 단계 추가 |

- **완료 기준**: 7개 pilot SKILL.md에서 위 매트릭스 8개 패턴 모두 일관 적용 — `grep -n "STATE.md 갱신\|STATE.md 행" opal/skills/opal-pilot-{dev,dev-short,dev-wireframe,gc,project-dev,sdd,write-tech}/SKILL.md` 결과 옛 표현이 0건이며, `grep -n "state mark\|state advance\|state gate-pass\|state add-row\|state status\|state block" ...` 결과 새 표현이 7개 파일 모두에 출현
- **테스트**: 각 파일 grep + 본문 일관성 검증 (E-5 매트릭스 8개 패턴이 각 pilot의 기존 표현과 1:1 대응되었는지 교차 확인)
- **의존**: Step 7 (정상 동작 확인 후 일괄 진행)

### Step 9: 단계 스킬 갱신 (op-dev-execute)

- [ ] 완료
- **파일**: `opal/skills/op-dev-execute/references/execute-guide.md`
- **작업 내용**: 95, 97, 119 → `state mark --row N --done --as-worker` 호출. `[MUST] 워커는 자기 단계 작업 행만 mark 가능` 추가
- **완료 기준**: grep으로 state mark + --as-worker 토큰 확인
- **테스트**: grep
- **의존**: Step 7 (병렬 그룹)

### Step 10: 에이전트 8개 1줄 갱신 (병렬 가능)

- [ ] 완료
- **파일**: `opal/agents/opal-{be,db,fe,plan,task}-agent/AGENT.md`, `opal/agents/opal-sdd-action-agent/AGENT.md`, `opal/agents/opal-task-action-agent/AGENT.md`, `opal/agents/opal-planning-agent/personas/service-planner.md`
- **작업 내용**: 각 행동 규칙 1행 갱신 — "STATE.md는 ~로만 갱신한다" → "STATE.md 갱신은 `~/.opal/tools/state-tool/run.sh ...` 호출로만 수행. 워커는 `--as-worker --worker-stage <자기단계>` 한정. 다른 단계 행 시도 시 도구가 거부."
- **완료 기준**: 8개 파일 모두 갱신된 표현 출현
- **테스트**: grep
- **의존**: Step 7 (병렬 그룹)

### Step 11: 가이드 (실질 갱신 3개)

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md`, `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`, `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
- **작업 내용**: §1 영향 범위 분류 결과대로 `state mark/advance/add-row` 호출 표기 통일. **자유 텍스트 영역(검증 루프 로그/머지 이력/의사결정 로그)은 본 태스크 범위 밖이므로 보존** (TASK 확정 사항 5)
- **완료 기준**: 3개 파일에서 state-tool 호출 표현이 일관 출현, 자유 텍스트 영역은 변경 0줄
- **테스트**: grep + diff 확인
- **의존**: Step 8

### Step 12: 가이드 (단순 참조 8개)

- [ ] 완료
- **파일**: `harness/parallel-execution.md`, `harness/qa-standards.md`, `oppd/wbs-guide.md`, `oppd/roadmap-guide.md`, `oppd/prd-guide.md`, `oppd/trd-guide.md`, `sdd/spec-plan-guide.md`, `sdd/verify-guide.md`, `gc/done-template.md`
- **작업 내용**: 1~2줄 표현 통일만. 절차 본문 변경 0줄
- **완료 기준**: grep으로 LLM 직접 STATE 갱신 표현 0건 (state-tool 호출 표현으로 통일)
- **테스트**: grep
- **의존**: Step 8 (Step 11과 병렬 가능)

### Step 13: pm-review-gate.md / additional-work.md / interactive / agentic 하네스 갱신

- [ ] 완료
- **파일**: `opal/core/references/harness/pm-review-gate.md`, `opal/core/references/harness/additional-work.md`, `opal/core/references/opal-harness-interactive.md`, `opal/core/references/opal-harness-agentic.md`
- **작업 내용**:
  - pm-review-gate.md 검토 절차에 12번 항목 `state validate` 추가. **§2.13 G-10 `gate-pass` 호출 표기 추가** — Gate 4행(QA Gate / State Gate / PM Gate / State Gate) 통과 시 PM이 `state gate-pass --start <N>` 1회 호출 (mark 4번 호출의 표준 단축형). 자가 진단에 "최근 24시간 의사결정 로그에 force 사용 0건 확인"(R-11 대응) 추가
  - additional-work.md 진입 절차에 `state add-row` / `state mark` 호출 추가. **§2.11 G-7 `status --set additional_work_done` 표기 추가** (진입 절차 7번 — `추가작업중 → 추가작업완료` 전환은 `state status --set additional_work_done` 호출). 진입 절차 1번도 자동 전환이지만 명시 호출 옵션으로 `state status --set additional_work` 표기 가능
  - opal-harness-interactive.md §2(33-36), §3(80-83) `state mark` 호출 표기. 자가 진단(46-59)에 `state validate` 6번 항목 추가. **§2.13 gate-pass 호출 권장 표기**
  - opal-harness-agentic.md §4(60-65) `--auto-pass` 표기. **§2.16 G-13 추가**: "CLOSE 진입은 사용자 확인 필수, --auto-pass 거부됨. PM은 CLOSE 진입 직전 캡틴 보고 후 사용자 발화를 받아 prev_user_row를 `--owner user`로 mark한다." (M-7 갱신, R-12 대응)
  - **§2.16 G-13 도구 자동 검증 명시**: pm-review-gate.md / opal-harness-interactive.md / opal-harness-agentic.md 양쪽에 "CLOSE 첫 행 mark 시 prev_user_row 자동 검증 — 미통과 시 도구가 거부 (close_gate_violation / agentic_close_gate_requires_user)" 명시
- **완료 기준**: 4개 파일에서 state-tool 호출 표현 출현. `gate-pass` 표기 출현(M-4/M-6). `--auto-pass` 거부 정책(M-7) 명시. CLOSE 진입 자동 검증 표기 출현(M-4/M-6/M-7)
- **테스트**: grep `gate-pass` / `auto-pass` / `close_gate` 토큰 출현 확인
- **의존**: Step 11, 12

### Step 14: tools.md 등록부 갱신

- [ ] 완료
- **파일**: `opal/core/references/tools.md`
- **작업 내용**: xlsx-tool 섹션(8-65) 형식 차용한 `state-tool` 섹션 신규 추가 — 용도/실행 경로/소스 경로/의존성/커맨드 9종(init/show/advance/mark/block/validate/add-row/status/gate-pass)/출력 형식/사용 예시/종료 코드. 변경이력에 v1.3 행 추가
- **완료 기준**: tools.md에 state-tool 섹션 추가, 형식이 xlsx-tool과 일관
- **테스트**: 본문 정독 + 섹션 헤더 일관성 확인
- **의존**: Step 13

### Step 15: install-mac.sh 실행 권한 부여 추가

- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 716-740 도구 배포 블록의 playwright-tool 실행 권한 부여(720-725) 패턴을 차용하여 `state-tool/run.sh`에 동일 처리 추가. 디렉토리 자체는 `install_dir "$opal_dir/tools" "$opal_home/tools"`(718)로 자동 복사
- **완료 기준**: install-mac.sh에 `state-tool run.sh 실행 권한 설정` 메시지 출력 코드 추가
- **테스트**: bash -n으로 syntax 체크
- **의존**: Step 14

### Step 16: 추가 회귀 표본 (F-23) — dummy 태스크 2건

- [ ] 완료
- **파일**: 임시 dummy 태스크 폴더 (테스트 후 삭제)
- **작업 내용**: dummy 태스크 2건 생성 — (1) interactive×opp 20행, (2) agentic×opd 24행. 각각 `state init` → 진행 → `state validate` violations 0건 확인
  - **§2.16 G-13 CLOSE 진입 게이트 시나리오 추가**:
    - (1) interactive×opp: 행 18(EXECUTE 사용자 확인) `--owner user`로 mark → 행 19(CLOSE DONE.md 생성) mark 정상 통과. owner≠user로 mark 시 행 19에서 `close_gate_violation` 거부 → `--force` 우회 시 의사결정 로그 자동 기재 검증 (§2.17 트리거 #8)
    - (2) agentic×opd: 사용자 확인 행을 `--auto-pass`로 ✅ 처리 가능하지만, **CLOSE 진입 행만은** `--auto-pass`가 거부되어 `agentic_close_gate_requires_user` 에러 검증. 캡틴 발화 후 `--owner user`로 mark → CLOSE 진입 가능
  - **§2.13 G-10 gate-pass 검증**: opp의 PLAN Gate 4행(행 6~9)에 `gate-pass --start 6` 호출 → 4행 일괄 ✅, 의사결정 로그 1행 추가 확인. 비표준 행 구성(opsdd 35행)에는 `gate-pass` 호출 시 `gate_pattern_mismatch` 거부(R-10 대응)
  - **§2.11 G-7 status 시나리오**: dummy 태스크 (1) 완료 후 `add-row --after 19 --stage CLOSE --item "추가 검증"` → current_status 자동 `additional_work` 전환 → 신규 행 ✅ 처리 → `status --set additional_work_done` → STATE.md `- 상태:` 갱신 검증
- **완료 기준**: 2건 모두 violations 0건. 워커 권한 게이트(`--as-worker`) 거부 케이스 + CLOSE 진입 게이트(close_gate_violation, agentic_close_gate_requires_user, --force 우회) 3종 + gate-pass happy/거부 2종 + status 전이 시나리오 3종 모두 검증 통과
- **테스트**: 수동 검증 + state.json 직접 정독 + STATE.md 의사결정 로그 정독
- **의존**: Step 15

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] `state init` happy path — task-path + skill + mode + --rows-spec 정상 처리, state.json + STATE.md 마커 영역 양쪽 생성
- [ ] `state init` 멱등성 — 기존 state.json 존재 시 `already_initialized` 거부 (T-8)
- [ ] `state init --force` — 덮어쓰기 + STATE.md 의사결정 로그 자동 기재
- [ ] `state init --import-existing` — 134 자기 자신 STATE.md 파싱 후 모든 행이 정확히 임포트됨
- [ ] `state show --format md` — 마크다운 표 출력 형식이 STATE.md 본문과 일치
- [ ] `state show --format json` — state.json raw 그대로 출력
- [ ] `state advance` — ⬜→🔄 전환만 허용, ✅→🔄 시도 시 거부 (T-7)
- [ ] `state mark --done` — ⬜/🔄→✅ 전환 허용, 다른 전이 거부 (T-7)
- [ ] `state mark --as-worker --worker-stage <자기단계>` — 자기 단계 "작업" 행만 허용
- [ ] `state mark --as-worker --worker-stage PLAN` 워커가 EXECUTE 행 시도 → `worker_scope_violation` (T-10)
- [ ] `state mark --auto-pass` — `note` 필드에 "agentic auto-pass" 자동 기재 (T-9)
- [ ] `state block` — any→❌ 전환, STATE.md 블로커 섹션은 자유 텍스트 보존
- [ ] `state validate` happy path — violations 빈 배열 반환
- [ ] `state validate` 행 순서 위반 검출 — 앞 행 미완료에서 다음 행 ✅ 시 violations 출력
- [ ] `state validate` 모드 일치 검출 — agentic 모드에서 사용자 확인 행이 ✅인 경우 검출
- [ ] `state validate` 마커 손상 검출 — `<!-- pipeline:start -->` 누락 시 violations 출력
- [ ] `state validate` 스키마 위반 검출 — state.json 필수 필드 누락 시 violations 출력
- [ ] `state add-row --after N --stage CLOSE --item ...` — 추가작업 행 정상 삽입, **row_id 재정렬** 검증 (삽입 행 이후 모든 row_id +1, §2.12 G-9). current_status 자동 `additional_work` 전환 (§2.11 G-7)
- [ ] 종료 코드 정합성 — happy path = 0, 권한/순서 위반 = 1, 내부 오류 = 2 (T-3)
- [ ] **§2.11 G-7** `state status --set additional_work` happy path — current_status 정상 전환 + STATE.md `- 상태: 추가작업중` 갱신 + 의사결정 로그 1행 자동 기재 (§2.17 트리거 #4)
- [ ] **§2.11 G-7** `state status --set additional_work_done` happy path — `additional_work → additional_work_done` 정상 전환 + `- 상태: 추가작업완료` 갱신
- [ ] **§2.11 G-7** `state status --set` 거부 케이스 — `done → in_progress` 등 invalid 전환 시 `invalid_status_transition` + exit 1
- [ ] **§2.13 G-10** `state gate-pass --start <N>` happy path — 4행(QA Gate / State Gate / PM Gate / State Gate) 일괄 ✅ + 의사결정 로그 1행 자동 기재 (§2.17 트리거 #6)
- [ ] **§2.13 G-10** `gate-pass` Gate 패턴 불일치 거부 — 행 N의 item이 `QA Gate`가 아니거나 4행 패턴이 다를 때 `gate_pattern_mismatch` 반환
- [ ] **§2.13 G-10** `gate-pass` stage 혼합 거부 — 4행이 동일 stage가 아니면 `gate_stage_mixed` 반환
- [ ] **§2.14 G-11** `state show --format full` 출력에 자유 텍스트 영역(`## 의사결정 로그` / `## 블로커` / `## 다음 액션`) 모두 포함 확인
- [ ] **§2.14 G-11** 마커 손실 시 fallback 검증 — `--format md`는 헤더에 "(마커 누락 — fallback 출력)" 명시, `--format json`은 `marker_present: false` 필드 추가, `--format full`은 본문 맨 위에 warning 주석 prepend
- [ ] **§2.15 G-12** 사용자 확인 행을 `--owner user` 없이 mark 시 `validate`가 `user_confirmation_owner_mismatch` violations 반환
- [ ] **§2.15 G-12** interactive 모드에서 사용자 확인 행이 owner=auto로 ✅ 처리되면 `auto_pass_in_interactive_mode` violations
- [ ] **§2.15 G-12** `--owner` 와 `--auto-pass` 동시 사용 시 `owner_flag_conflict` 거부
- [ ] **§2.16 G-13** CLOSE 진입 게이트 — 직전 단계 사용자 확인 미통과(prev_user_row.owner != "user") 상태에서 CLOSE 첫 행 mark 시도 → `close_gate_violation` 반환
- [ ] **§2.16 G-13** agentic 모드 CLOSE 진입 게이트 — `--auto-pass`로는 CLOSE 첫 행 mark 거부 (`agentic_close_gate_requires_user`)
- [ ] **§2.16 G-13** CLOSE 진입 게이트 `--force` 우회 시 `--note` 인자 미제공 거부 (`note_required_for_force`)
- [ ] **§2.16 G-13** CLOSE 진입 게이트 `--force` 우회 시 의사결정 로그 자동 기재 (§2.17 트리거 #8)
- [ ] **§2.17 의사결정 로그 자동 기재** — 8개 트리거(#1~#8) 각각에 대해 STATE.md `## 의사결정 로그` 표에 정확히 1행씩 추가됨. 트리거 #7(block)은 row.note만 기재, 의사결정 로그 미기재
- [ ] **§2.17 의사결정 로그 자동 기재** — 트리거 #1(`init --force`), #3(`mark --force`), #8(close_gate `--force`)은 `--note` 미제공 시 명령 거부

#### v3 보강 — E-1~E-6 검증 (신규)

- [ ] **§2.18 에러 코드 카탈로그(E-1)** — 22종 코드 모두 §2.x 인용 정확. `state_tool.py`의 `ERROR_CODES` 상수에 22종 모두 정의됨. 단위 테스트(N-5)가 22종 코드 각각에 대해 최소 1개 케이스를 포함 (cross-ref grep 검증)
- [ ] **§2.18 에러 카탈로그 누락 0건 검증** — `grep -nE '"error":\s*"' opal/tools/state-tool/state_tool.py` 결과의 모든 코드가 §2.18 표에 등재됨. 거꾸로 §2.18 표의 모든 코드가 코드에 등장
- [ ] **§2.19 명령 인자 매트릭스(E-2)** — 9개 명령 × 모든 인자가 §2.19 표에 빠짐없이 등재. argparse 정의가 §2.19와 1:1 일치(`--help` 출력으로 교차 검증)
- [ ] **§2.19.10 충돌/종속 매트릭스** — C-1~C-6 케이스 모두 단위 테스트로 검증 — 위반 시 §2.18 카탈로그의 해당 에러 코드 정확 반환
- [ ] **§2.20.1 `--rows-spec` 입력 형식(E-3)** — opp 표준 20행 JSON 배열 주입 시 정상 파싱 + agentic 모드 자동 마킹(CLOSE 외 사용자 확인 행 → na, CLOSE 사용자 확인 행 → pending 유지) 정확 동작
- [ ] **§2.20.1 `--rows-spec` 파싱 에러 케이스** — 잘못된 JSON / 배열 아님 / 객체 필드 누락(stage 또는 item) / stage enum 위반 / item minLength 0 — 5종 케이스 각각 `rows_spec_invalid_json` 또는 `invalid_stage_enum` 반환
- [ ] **§2.20.2 `--rows-from` SKILL.md 파싱(E-3)** — opp(20행) + opd 양쪽 SKILL.md를 정상 파싱 + 추출 행 수 정합. opsdd처럼 35행+ACT가 있는 경우도 EXECUTE-LOOP의 ACT 행은 단일 "ACT 실행" 행으로 합쳐져 추출됨(§2.20.2 표 참조)
- [ ] **§2.20.2 `--rows-from` 에러 케이스** — 헤더 누락 / 표 헤더 누락 / 데이터 행 0건 — 3종 케이스 각각 `skill_md_parse_error` 반환 + `reason` 필드에 정확한 사유 기재
- [ ] **§2.20.3 `--rows-acts` 시그니처만(R-13)** — 본 태스크에서 인자 명시 시 `rows_acts_not_implemented` 에러 + exit 2 반환 (향후 별도 태스크에서 구현)
- [ ] **§2.21 Step 롤백 정책(E-6)** — 16개 Step별 롤백 시나리오가 git 작업과 정합 (개발 범위만 영향, ~/.opal/ 직접 미터치). Step 1/Step 7/Step 16의 즉시 에스컬레이션 트리거(§2.21.4) 명세대로 동작
- [ ] **§3 Step 7 fallback(E-4)** — 의도적으로 깨진 STATE.md(마커 누락 또는 표 깨짐) 표본으로 import-existing 호출 → `import_failed` 트리거 → 3.2 fallback(`--rows-spec --import-existing --force --note`) 절차 정상 복구 (Step 16 dummy 회귀 시 검증)
- [ ] **§3 Step 8 표준 매트릭스(E-5)** — 7개 pilot SKILL.md에서 8개 패턴(P-1~P-8) 일관 적용. 옛 표현(`STATE.md 갱신`/`STATE.md 행`) grep 결과 0건. 새 표현(`state mark`/`state advance`/`state gate-pass` 등) grep 결과 7개 파일 모두 출현

### 일관성 테스트

- [ ] state.json `status` enum과 `status_label` 매핑 — 모든 행의 두 필드가 T-2 매핑(`pending`↔⬜, `in_progress`↔🔄, `done`↔✅, `failed`↔❌, `na`↔-) 정확
- [ ] 마커 안전성(T-6) — STATE.md의 의사결정 로그/블로커/다음 액션 영역이 mark/advance/block 후에도 변경 0건
- [ ] 행 순서 강제(T-7) 동작 — `advance`는 ⬜만, `mark`는 ⬜/🔄만, `block`은 any 허용
- [ ] 워커 권한 게이트(T-10) — `--as-worker` 없이 다른 단계 행 mark 시 무제한 허용 (PM 모드), `--as-worker` 있으면 자기 단계 한정
- [ ] 시점 형식(T-5) — 모든 timestamp가 `node ~/.opal/tools/date/date.js datetime` 결과와 동일 KST 포맷
- [ ] 호출 형식 통일(T-12) — `~/.opal/tools/state-tool/run.sh <command> ...` 형태가 모든 갱신 본문에서 일관 사용
- [ ] 8개 SKILL.md "STATE.md 도메인 치환값" 섹션 SSOT 보존 — 행 구성 매핑이 SKILL.md에만 존재, state-tool 내부 하드코딩 없음
- [ ] 영역 간 용어 일관성(citation-rules.md §7) — `state-tool`(도구명), `state.json`(파일명), `state init/show/advance/mark/block/validate/add-row/status/gate-pass`(9개 서브 명령) 토큰이 TASK / PLAN / 갱신된 본문에서 일관. 갱신된 본문에서 옛 7개 명령만 표기된 곳이 0건 (status/gate-pass 누락 0건)
- [ ] 자유 텍스트 영역 보존 — STATE.md "의사결정 로그", "블로커", "다음 액션" 섹션 + oppd "검증 루프 로그", "머지 이력" 섹션이 본 태스크 범위 밖으로 보존됨
- [ ] **§2.11 G-5 자동 갱신** — 모든 갱신 명령(init/advance/mark/block/add-row/status/gate-pass) 실행 후 STATE.md 첫 출현 `> 최종 갱신: ...` 라인이 date.js 결과(KST `YYYY-MM-DD HH:mm`)로 자동 교체되며, state.json `updated_at`도 동일 값으로 동기화 (date.js 1회 호출 결과 재사용으로 정합)
- [ ] **§2.11 G-6 자동 갱신** — `## 현재 상태` 4줄 중 `- 진행:` / `- 상태:` 라인이 G-6 매핑 표대로 자동 갱신. `- 모드:` / `- 단계:` 라인은 init만 작성, 이후 명령은 미변경(도메인 SSOT 보존)
- [ ] **§2.11 G-8 자유 텍스트 영역 보존(보강 검증)** — `init` 후 `mark` / `advance` / `block` / `add-row` 호출 시 자유 텍스트 3개 섹션(`## 의사결정 로그` 자동 기재 1행 외 / `## 블로커` / `## 다음 액션`) 본문이 변경 0건. 단 §2.17 자동 기재 트리거 발동 시 `## 의사결정 로그` 표에 1행 추가만 허용

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수 (도구명/JSON 필드명/서브 명령은 영어, 설명은 한국어)
- [ ] kebab-case 파일/폴더 네이밍 — `state-tool`, `state.schema.json`, `test_state_tool.py` (Python은 snake_case 허용)
- [ ] YAML frontmatter 없음 — 본 태스크 산출물은 도구이며 SKILL.md 아니므로 frontmatter 불필요
- [ ] 갱신된 본문이 새 호출 형식을 일관되게 사용 — F-7~F-19 대상 35개 파일 grep으로 0건 누락 확인
- [ ] [MUST] 토큰 사용 일관성 — `state.md` / `state-template.md` / `op-task/SKILL.md` 3곳에 `[MUST] state-tool 호출만 허용` 또는 `[MUST] LLM 직접 작성 금지` 표기
- [ ] tools.md 등록 형식이 xlsx-tool 섹션과 동일 구조 (용도/실행 경로/소스 경로/의존성/커맨드/출력 형식/사용 예시)
- [ ] install-mac.sh 변경이 기존 도구 배포 패턴(playwright-tool 720-725)과 일관

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | `state init --import-existing` 정규식 파싱이 모든 기존 STATE.md를 처리하지 못함 (TASK 미확정 #7) | 134 회귀 테스트 실패 → 마이그레이션 차단 | 본 134 STATE.md로만 1차 검증. 실패 시 `import_failed` 반환 + 호출자에게 수동 행 목록 주입 권고. 레거시 호환 정책상 ~133은 소급 변경하지 않으므로 영향 제한적 |
| R-2 | 8개 SKILL.md "STATE.md 도메인 치환값" SSOT 결정(§2.3)이 향후 행 추가 요구를 받을 때 결합도 발생 | 행 추가 시 SKILL.md + state-tool 양쪽 변경 | `--rows-spec` 인자가 외부 주입 방식이므로 도구 변경 없이 SKILL.md만 수정하면 됨. 향후 모드별 차이가 커지면 별도 태스크로 재설계 |
| R-3 | 워커 권한 게이트(--worker-stage 명시 인자, §2.4) 도입으로 PM이 워커 디스패치 프롬프트에 호출 예시를 매번 주입해야 함 | 디스패치 프롬프트 길이 증가 | 8개 오케스트레이터 SKILL.md(M-10~M-17)에 워커 호출 예시를 표준 블록으로 삽입하여 PM이 복사·주입만 하면 되도록 함 |
| R-4 | 마커(T-6) `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->`가 사용자 직접 편집 시 손상 가능 | mark/advance/block 모두 거부 → 진행 차단 | `init --force`로 복구 가능. show 명령은 fallback으로 표 추정 출력 → 사용자가 재초기화 가능 (T-6) |
| R-5 | 영역 간 용어 일관성 (citation-rules.md §7) — `state-tool`/`state.json`/서브 명령 토큰이 35개 파일에 분산되어 누락 위험 | 갱신 누락 시 LLM이 옛 형태로 STATE.md 직접 편집 시도 → 마커 손실 | Step 13 완료 후 전체 grep 검증 (`grep -rn "STATE.md 갱신" opal/core opal/skills opal/agents` → state-tool 호출 컨텍스트가 아닌 매치 0건 목표). PM Gate에서도 동일 검증 |
| R-6 | TASK.md 미확정 9건 중 PLAN에서 자체 결정 8건 — 캡틴 결정이 필요한 항목 잔여 | 의사결정 권한 위임 발생 가능성 | §2.3~§2.10에 결정 근거 명시. 캡틴 검토 후 이의 시 재결정 (decision_required로 에스컬레이션 — 본 PLAN 제출 시 빈 배열 반환) |
| R-7 | install-mac.sh 변경이 기존 배포 흐름에 영향을 줄 가능성 | 배포 시 권한 미부여로 도구 호출 실패 | playwright-tool 패턴(D-16:720-725) 그대로 차용 — 검증된 패턴이므로 위험 낮음. bash -n 문법 검증 필수 |
| R-8 | "약 영향 9개 가이드" 단순 참조 갱신이 누락될 위험 | 가이드 본문에서 LLM이 옛 형태 STATE.md 직접 갱신 시도 | Step 12에서 9개 파일 일괄 grep → 모두 state-tool 토큰으로 통일 후 PM Gate 재검증 |
| R-9 | 본 태스크가 "개발 범위"이므로 `~/.opal/`에 직접 적용 금지 ([MUST] D-12) | EXECUTE 검증 시 `~/.opal/tools/state-tool/`에 도구가 없어 수동 호출 불가 | 검증은 소스 경로 직접 호출 — `bash opal/tools/state-tool/run.sh ...` (래퍼 스크립트가 venv를 절대 경로로 호출하므로 동작 가능). 배포는 캡틴의 `install-mac.sh` 실행 후에만 |
| R-10 | `gate-pass --start N`은 4행 패턴(`QA Gate / State Gate / PM Gate / State Gate`)을 가정 — opsdd(35행+ACT 동적) / oppd(검증 루프 별도) 등 비표준 행 구성에서는 미동작 | opsdd/oppd 단계 종료 시 PM이 일괄 갱신 단축형을 사용 못함 → mark 4번 호출 누락 위험 | 비표준 행 구성은 `gate-pass` 호출 시 `gate_pattern_mismatch` / `gate_stage_mixed` 명시 거부 (§2.13, §2.18 카탈로그 #9/#10). 해당 SKILL.md(M-15 oppd `opal-pilot-project-dev`, M-16 opsdd `opal-pilot-sdd`)에 "비표준 행 구성은 mark 개별 호출 필수" 표준 블록 추가 (Step 8 매트릭스의 P-2 비고 — E-5). PM Gate 자가 진단에 "opsdd/oppd 단계는 mark 4회 호출 누락 0건 확인" 추가 |
| R-11 | `--force`로 검증 우회 시 사후 추적만 가능 (의사결정 로그 자동 기재 §2.17 트리거 #1/#3/#8) — 우회 남발 시 안정성 저하 | 마커 손상/CLOSE 게이트 강제 우회/스코프 위반 우회가 누적될 위험 | `--note` 인자 강제(미제공 시 `note_required_for_force` 거부 — §2.18 카탈로그 #17) + PM Gate 자가 진단에 "최근 24시간 의사결정 로그에 force 사용 0건 확인" 항목 추가 (Step 13 pm-review-gate.md 갱신). 누적 발생 시 별도 태스크로 우회 제한 정책 재설계 |
| R-12 | agentic 모드에서도 CLOSE 진입 게이트는 사용자 발화 필수 (§2.16 G-13) — agentic 자율성 일부 제한 | agentic 모드 PM이 자율 통과 시도 시 `agentic_close_gate_requires_user` 거부로 워크플로 중단 가능 | opal-harness-agentic.md M-7에 "CLOSE 진입은 사용자 발화 필수, --auto-pass 거부" 명시 (Step 13 갱신). PM은 CLOSE 진입 직전 캡틴 보고 후 사용자 발화를 받아 prev_user_row를 `--owner user`로 mark. 운영 문서에 "agentic 모드는 CLOSE 진입을 위한 1회 보고 의무" 표준 절차 추가 |
| R-13 | opsdd 35행+ACT 동적 행 처리는 본 태스크 범위 밖 (`--rows-acts` 시그니처만 정의 — §2.20.3) | opsdd 태스크는 본 태스크 도구 도입 직후에 사용 불가 — `state init --rows-acts` 호출 시 `rows_acts_not_implemented` + exit 2. opsdd 사용자가 임시로 `--rows-spec`으로 ACT 행을 inline 주입해야 함 | 본 태스크는 opp/opd 표본만으로 검증 (R-1과 별개). opsdd ACT 동적 처리는 별도 후속 태스크로 진행. 후속 태스크 진행 전까지 opsdd SKILL.md(M-16)에 "ACT 동적 행은 `--rows-spec`으로 inline 주입" 임시 가이드 추가. 시그니처 호환성은 본 태스크에서 보장(`--rows-acts` 인자 자체는 argparse에 등록되어 있어, 후속 태스크에서 동작 변경만 추가) |

### 영역 간 용어 일관성 검토 결과 (citation-rules.md §7)

PLAN/TASK 간 토큰 일치 확인:

- 도구명: `state-tool` (TASK §확정 / §F-1 / §F-19, PLAN 전체) — 일관 ✅
- 파일명: `state.json` (TASK §F-3, PLAN §2.2 / §3 Step 1) — 일관 ✅
- 서브 명령: `init / show / advance / mark / block / validate / add-row / status / gate-pass` (TASK §F-2 7개 → PLAN v2에서 9개로 확장 — `status`(G-7) / `gate-pass`(G-10) 신설. PLAN §2.11/§2.13이 SSOT, TASK 본문은 변경 없음) — 일관 ✅
- 종료 코드: `0=ok / 1=violation,scope_error / 2=internal_error` (TASK T-3, PLAN §2.1, §2.18 카탈로그 종료 코드 컬럼) — 일관 ✅
- 마커: `<!-- pipeline:start -->` ~ `<!-- pipeline:end -->` (TASK T-6, PLAN §2.1 / §3 Step 1, §2.18 #2 marker_missing) — 일관 ✅
- 워커 인자: `--as-worker --worker-stage <stage>` (PLAN 결정 §2.4, TASK 미확정 #3 → 결정, §2.19.4 / §2.19.10 C-3) — 일관 ✅
- 에러 코드 카탈로그: 22종(§2.18) — 인자 매트릭스(§2.19) / 입력 형식(§2.20) / 롤백 정책(§2.21)이 모두 §2.18 카탈로그 인용 — 일관 ✅
- 외부 주입 인자: `--rows-spec` / `--rows-from` / `--rows-acts` (§2.19.1 init 매트릭스 / §2.20 세부 명세) — 일관 ✅
- 충돌 관계 토큰: C-1~C-6(§2.19.10) — §2.18 카탈로그 #13/#17/#21/#22와 정확히 매핑 — 일관 ✅

영역 간 불일치 검출 0건. `decision_required` 에스컬레이션 불필요.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-01 | 최초 작성 — TASK v2 기반. 영향 범위 정정(48개 추적 / 35개 수정 / 5파일 신규) + TASK 미확정 9건 중 8건 PLAN 결정 + 1건 회귀 검증 시 결정 |
| v2 | 2026-05-01 | PM Gate Pass 후 사용자 검토에서 식별된 갭 15건(G-1~G-15) 정정. §2.2 스키마 보강(`created_at`/`updated_at`/`timestamp`/`note` + stage enum 8 SKILL.md 도출 + STANDARD_ITEMS 상수). §2.11~§2.17 신설(STATE.md 자동 갱신 SSOT / add-row 알고리즘 / gate-pass 일괄 / show 출력 범위 / 사용자 확인 owner 처리 / CLOSE 진입 자동 검증 / 의사결정 로그 자동 기재 8 트리거). 서브 명령 7개 → 9개로 확장(`status`(G-7), `gate-pass`(G-10) 신설). §3 Step 1/2/4/7/13/16 정합 갱신. §4 QA 항목 추가(G-7~G-15 시나리오 14건). §5 R-10/R-11/R-12 추가. TASK.md 본문은 변경 없음(PLAN이 SSOT). |
| v3 | 2026-05-01 | EXECUTE 진입 전 PM 자가 검토에서 식별된 갭 6건(E-1~E-6) 정정. §2.18 에러 카탈로그 SSOT(17~22종 통합 — 기존 17종 + 신규 5종 식별). §2.19 명령 인자 매트릭스(9 명령 × 모든 인자 + 충돌/종속 매트릭스 C-1~C-6). §2.20 `--rows-spec`/`--rows-from` 입력 형식 + SKILL.md 파싱 정규식 + agentic 자동 마킹 규칙 + `--rows-acts` 시그니처 정의. §2.21 Step 16개별 롤백 정책 + 의존 보존 + 즉시 에스컬레이션 트리거. Step 7 `--import-existing` 실패 fallback 절차(3.1~3.3) 보강. Step 8 7개 pilot 표준 교체 패턴 매트릭스 8개(P-1~P-8) + pilot별 적용 행 수. §4 v3 보강 QA 항목 12건 추가. §5 R-13 신규(opsdd ACT 동적 미구현). 영역 간 용어 일관성에 §2.18~§2.21 참조 추가. EXECUTE 워커가 §2.18~§2.21만 보고도 추측 없이 구현 가능한 수준으로 완결성 확보. TASK.md 본문은 변경 없음(PLAN이 SSOT). |
