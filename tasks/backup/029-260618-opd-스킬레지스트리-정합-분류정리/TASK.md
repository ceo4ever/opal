# TASK: opal/skills 레지스트리 정합 + 분류 정리 + opal-brain 리네임 + validate lint

> 작성일: 2026-06-18 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청 (opal/ 하위 구조 검토 → 분류 정리 태스크 개설)
> 출력: TASK.md

## 작업 목표

`opal/skills`의 SSOT인 `opal-skills-registry.json`이 실제 폴더와 어긋난 드리프트·분류 비일관을 해소하고, 파일럿(`opal-brain`)을 `opal-pilot-*` 네이밍 체계로 정합화하며, 재발 방지를 위한 `validate` 검출 도구를 `skill-registry`에 추가한다.

## 배경

세션 검토 결과 `opal/` 최상위 6분할(agents/bootstrapper/core/skills/templates/tools)은 의미적으로 건전하나, `skills/` 평면 36개를 의미 계층으로 떠받치는 레지스트리가 실제와 어긋나 있다. 평면 레이아웃 자체는 부트스트래퍼·skill-registry의 경로 해석 단순화를 위한 정당한 설계이므로, 문제는 "물리 구조"가 아니라 "의미 계층(레지스트리)의 정합성·일관성"이다.

## 배경 분석 (대화에서 도출)

레지스트리(`opal/core/references/opal-skills-registry.json`) ↔ `opal/skills/` 폴더 교차 검증 결과:

**(1) 드리프트 — 레지스트리 ↔ 디스크 불일치**

| 유형 | 항목 | 근거 |
|------|------|------|
| dangling (레지스트리엔 있으나 폴더 없음) | `op-sdd-tasks` | 레지스트리 `op-sdd` 그룹 / 폴더엔 `op-sdd-action-plan`만 존재 — 리네임 후 미반영 추정 |
| dangling | `opal-orchestrator` | 레지스트리 `opal` 그룹 / 폴더 부재 — 레거시 잔존 추정 |
| 미등록 (폴더엔 있으나 레지스트리 없음) | `op-sdd-action-plan` | `opal/skills/op-sdd-action-plan/` 존재, 레지스트리 누락 |

> `op-sdd-tasks`는 `docs/PROJECT.md` §주요 컴포넌트(SDD)에도 단계 스킬로 기재되어 있어 PROJECT.md 정합도 함께 확인 필요.

**(2) 분류 비일관 — 그룹 오배치 / 네이밍 비대칭**

| 항목 | 현재 | 문제 | 정합 방향(가설) |
|------|------|------|----------------|
| `opal-brain` | `opal` 그룹, 폴더 `opal-brain`, alias `opbr` | 파일럿(4모드 오케스트레이터)인데 `opal-pilot-*` 네이밍·그룹 아님. `op-data`는 `opal-pilot-data-design`+`op-data-*`로 짝지은 것과 비대칭 | `opal-pilot-brain` 리네임 + `opal-pilot` 그룹 + alias `opb` |
| `op-brain-ingest` | `opal` 그룹 | op-* 단계 스킬인데 잡동사니 'opal' 그룹 소속 | 신규 `op-brain` 그룹 (data 패턴과 대칭) |
| `op-spec-validator` | `opal` 그룹 | op-* 단계 스킬(SDD 계열)인데 'opal' 그룹 소속 | `op-sdd` 그룹 |
| `opal-pilot-project-dev` | `opal` 그룹 | 이름은 pilot인데 `opal-pilot` 그룹과 분리됨 | `opal-pilot` 그룹 |

**(3) 비결함 — 변경 제외 확인 항목**

- 최상위 6분할: 건전. 변경 없음.
- `skills/` 물리 평면 유지(하위폴더화 안 함): 경로 해석 단순성 + cascade 위험 회피.
- `op-task-*` ↔ `op-dev-*` 병렬: 범용(opal-pilot-project) vs 코드(opal-pilot-dev) 두 파이프라인의 정당한 분리 — 통합은 별도 사안(제외).

## 확정된 설계 방향 (대화에서 합의)

> **[PLAN 게이트 중 정정 — 2026-06-18]** 초기에 "opal-brain → opal-pilot-brain 리네임 + opbr→opb"로 합의했으나, PLAN 게이트에서 캡틴이 "pilot은 단계 파이프라인+워커 지휘 오케스트레이터에 붙는 접두사인데 opal-brain도 그런가?"를 제기. 실제 `opal/skills/opal-brain/SKILL.md` 검증 결과 **opal-brain은 pilot이 아님**(독립 4모드 라우터 + brain-tool 직접 호출, 워커 디스패치·STATE·단계 파이프라인 없음 — `:21` "단일 pilot 구조"는 "오케스트레이터+단계스킬로 미분할"의 느슨한 표기). → **리네임 철회 확정.**

1. **opal-brain 리네임 철회** (캡틴 확정). 폴더·name·alias(`opbr`)·triggers 전부 **불변**. opal-brain은 operator(직접 실행) 스킬로서 `opal` 그룹(onboarding/start/project-init/skill-creator 등 operator 묶음)에 잔류.
2. **실제 정리 = 오기재 교정** (캡틴 확정). `docs/PROJECT.md`가 opal-brain을 "오케스트레이터 / Pilot"로 오기재한 것을 operator 성격에 맞게 교정. (alias 변경·cascade 없음)
3. **재발 방지 lint = `skill-registry validate` 확장** (캡틴 확정). ANALYSIS 결과 validate 함수는 이미 존재(`skill-registry.js:277-392`) → "신설"이 아니라 dangling warning→error 격상 + unregistered 역방향 감지 추가 + 단위 테스트.

## 명확화 결과

> TASK 4요소를 잠근다. 미잠금 시 PLAN 진입이 state-tool `verify --clarification-check`로 거부된다 (PRINCIPLES §1 집행).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 레지스트리 드리프트·분류 비일관 해소 + `opal-brain` 오기재(Pilot) 교정 + `skill-registry validate` 확장 | - | `opal-skills-registry.json` 현행, `opal/skills/` 폴더 |
| 범위 | **포함**: 레지스트리 JSON 드리프트 해소(R1)·그룹 재배치(R2), `docs/PROJECT.md` opal-brain "오케스트레이터/Pilot" 오기재 교정(R3), validate 확장+테스트(R4). **제외**: opal-brain 리네임·alias 변경·전역 cascade(리네임 철회 확정), 최상위 6분할 변경, skills 하위폴더화, op-task/op-dev 파이프라인 통합 | - (M1/M2 해소됨 — M1: 리네임 철회로 무효, M2: dangling 2건 모두 제거로 확정) | 캡틴 확정(확정 방향 §1~3, PLAN 게이트 정정) |
| 제약 | 배포 경계(`~/.opal/` 직접 편집 금지, 프로젝트 소스 수정 후 install 재배포) / 플랫폼 분기 어댑터 격리 / 부트·배포 무결성 / 변경이력 행 추가 | - | `.opal/AGENT.md` §금지사항, PRINCIPLES Core Stance |
| 완료기준 | ① `skill-registry validate` exit 0 (드리프트 0건: dangling·unregistered 모두 0) ② R1/R2 정합: dangling 2건·미등록 1건 해소, 그룹 3건 재배치 (jq/grep 확인) ③ `docs/PROJECT.md`에서 opal-brain의 "오케스트레이터/Pilot" 표기 교정 ④ validate 단위 테스트 PASS | - | - |

## 요구사항

- [ ] **R1 — 레지스트리 드리프트 해소**: dangling 2건(`op-sdd-tasks`·`opal-orchestrator`) 처리(리네임 매핑 또는 제거, ANALYSIS 판정) + 미등록 1건(`op-sdd-action-plan`) 등록.
  - 어디에: `opal/core/references/opal-skills-registry.json`, `docs/PROJECT.md`(op-sdd-tasks 기재 정합)
  - 왜: SSOT가 실제와 어긋나면 `//` 커맨드 매칭·디스패치 라우팅이 오작동 (확정 방향 §3, 배경 분석 (1))
  - AC: `node skill-registry.js validate` 실행 시 dangling·unregistered 0건 리포트.
- [ ] **R2 — 분류 그룹 재배치**: `op-spec-validator`→`op-sdd`, `op-brain-ingest`→신규 `op-brain` 그룹, `opal-pilot-project-dev`→`opal-pilot` 그룹으로 이동.
  - 어디에: `opal-skills-registry.json` groups
  - 왜: op-* 단계 스킬과 pilot이 잡동사니 'opal' 그룹에 오배치됨 (배경 분석 (2))
  - AC: 4개 항목이 각 정합 그룹에 배치되고, 'opal' 그룹엔 부트/init/메타작성 스킬만 잔존.
- [ ] **R3 — opal-brain 오기재(Pilot) 교정** (리네임 철회): opal-brain은 pilot이 아니라 operator 스킬(4모드 라우터+brain-tool 직접 호출, 워커 디스패치·STATE·단계 파이프라인 없음). 폴더·name·alias(`opbr`)·triggers·전역 참조 **전부 불변**. `docs/PROJECT.md`가 opal-brain을 "오케스트레이터 / …Pilot"로 분류한 오기재만 operator 성격에 맞게 교정.
  - 어디에: `docs/PROJECT.md`(opal-brain 컴포넌트 표 §주요 컴포넌트(Project Brain)의 유형 표기)
  - 왜: opal-brain은 pilot 정의(단계 파이프라인 분해+워커 지휘)를 충족하지 않음 — `opal/skills/opal-brain/SKILL.md` 검증 (확정 방향 §1·§2)
  - AC: `docs/PROJECT.md`에서 opal-brain의 유형이 "오케스트레이터/Pilot"이 아닌 operator(직접 실행 multi-mode) 성격으로 기재됨. opal-brain 폴더·alias·triggers·전역 참조는 변경 0건(grep으로 불변 확인).
- [ ] **R4 — skill-registry validate 확장** (신설 아님): `skill-registry.js:277-392`의 기존 `validate()`를 확장 — (a) `no SKILL.md found` warning→error 격상(`:379`), (b) unregistered 역방향 감지 신규(`opal/skills/`+top-level `skills/` 양쪽 스캔, **소스 환경 전용**), (c) 단위 테스트 신규.
  - 어디에: `opal/tools/skill-registry/skill-registry.js` + `opal/tools/skill-registry/tests/test-validate.js`(신규)
  - 왜: 이번 드리프트의 근본 재발 방지 (확정 방향 §3)
  - AC: dangling/unregistered가 있으면 항목 리포트+exit 1, 정합 시 exit 0. standalone(top-level skills) 오판 0건, 배포 환경 false positive 0건. 단위 테스트로 케이스 검증.

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 수정 금지. 프로젝트 소스(`opal/`, `scripts/`, `docs/`) 수정 후 install로 재배포.
- **플랫폼 분기 격리**: install-mac.sh / windows.ps1 등 어댑터 계층에서만 플랫폼 차이 처리. 로직에 하드코딩 분기 추가 금지.
- **부트·배포 무결성**: 리네임 cascade 누락 시 부트스트랩/`//` 커맨드/배포가 깨지므로 ANALYSIS에서 참조 전수 식별 필수.
- **변경이력**: 수정한 스킬·참조 문서·레지스트리에 변경이력/버전 행 추가 (KST 일시 + 태스크 029).
- **STATE.md**: `state-tool`로만 행 변경. 마크다운 직접 편집 금지.

## 기술 스택

- Node.js (skill-registry.js, date.js)
- Markdown / JSON (레지스트리·문서·부트스트래퍼)
- Bash (install-mac.sh), PowerShell (windows.ps1)
- Python (state-tool, brain-tool — 직접 변경 대상 아님)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 정합·재그룹 대상 SSOT |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | validate 신설 대상 |
| D-3 | 설계 | PROJECT.md | `docs/PROJECT.md` | op-sdd-tasks 기재 정합, 컴포넌트 테이블 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·변경이력 규칙 |
| D-5 | 설계 | install-mac.sh | `scripts/install-mac.sh` | opal-brain 배포 경로 cascade |
| D-6 | 설계 | 부트스트래퍼/references | `opal/bootstrapper/`, `opal/core/references/` | //opbr·opal-brain 언급 갱신 |
