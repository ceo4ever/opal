# ANALYSIS: opal/skills 레지스트리 정합 + 분류 정리 + opal-brain 리네임 + validate lint

> 작성일: 2026-06-18
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 정합·재그룹 대상 SSOT |
| D-2 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | validate 확장 설계 근거, 기존 구현 패턴 |
| D-3 | 설계 | PROJECT.md | `docs/PROJECT.md` | op-sdd-tasks 기재, opal-brain 약어 정합 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·컴포넌트 체계·변경이력 규칙 |
| D-5 | 설계 | install-mac.sh | `scripts/install-mac.sh` | 스킬 배포 cascade 분석 |
| D-6 | 설계 | opal-brain SKILL.md | `opal/skills/opal-brain/SKILL.md` | frontmatter alias·trigger 현황 |
| D-7 | 설계 | opal-brain-design.md | `docs/proposals/opal-brain-design.md` | opal-brain 설계 이력·과거 리네임 결정 근거 |
| D-8 | 설계 | AGENT.md (core) | `opal/core/AGENT.md` | opal-brain/opbr 글로벌 참조 |
| D-9 | 설계 | op-sdd-action-plan SKILL.md | `opal/skills/op-sdd-action-plan/SKILL.md` | 미등록 스킬 내용·dispatched_by 확인 |
| D-10 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | opal-orchestrator 잔존 기재 확인 |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 의무 수준(ANALYSIS §4 필수) |
| D-12 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | domain 필드 "opal-brain" 사용 여부 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/opal-skills-registry.json` | 스킬 SSOT 레지스트리 | 필수 | `:670-684` (opal-brain), `:305-313` (op-sdd-tasks), `:619-628` (opal-orchestrator) |
| `opal/skills/opal-brain/SKILL.md` | opal-brain 스킬 정의 | 필수 (리네임 대상) | `:2,7,9,10` (name/alias/trigger) |
| `opal/skills/opal-brain/references/brain-schema.md` | brain 스키마 설명 | 내부 참조 갱신 | `:4,108` |
| `opal/skills/op-brain-ingest/SKILL.md` | CLOSE ingest 워커 | 내부 참조 갱신 | `:51,55` (opal-brain 명시 참조) |
| `opal/core/AGENT.md` | 글로벌 PM 컨텍스트 | 필수 | `:39,194,203,213,231,247,446,447` (opal-brain/opbr 다수 참조) |
| `opal/core/references/opal-harness.md` | 하네스 참조 | 확인 후 갱신 | `:241` (opbr 언급) |
| `docs/PROJECT.md` | 프로젝트 SSOT 문서 | 필수 | `:79,83` (opal-brain/opbr), `:61` (op-sdd-tasks) |
| `docs/proposals/opal-brain-design.md` | brain 설계 SSOT | 변경이력 보존 | 과거 이력 문서 (변경 금지) |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 필수 | `:126,328` (opal-orchestrator 잔존) |
| `README.md` | 공개 소개 문서 | 필수 | `:43,65,307,662,670-673` (opbr 다수) |
| `opal/tools/brain-tool/brain_tool.py` | brain-tool CLI | 변경 불필요 | `:5` ("domain": "opal-brain" — 도메인 분류 태그, 스킬명과 물리 연결 없음) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | brain-tool 단위 테스트 | 변경 불필요 | `:1209,1238` (domain 태그 테스트 — 스킬 리네임과 무관) |
| `opal/tools/skill-registry/skill-registry.js` | skill-registry CLI | 필수 (R4 확장) | `:277-392` (validate 함수 현황) |
| `scripts/install-mac.sh` | macOS 설치 스크립트 | 변경 불필요 | `:923-934` (폴더 동적 순회 배포 — 하드코딩 없음) |

### 1.2 아키텍처 패턴

- **스킬 그룹 체계**: `opal-skills-registry.json`의 `groups` 필드에 그룹별 배열로 스킬을 관리. 현행 최상위 그룹: `opal-pilot`, `op-dev`, `op-sdd`, `op-data`, `op-task`, `standalone`, `opal` (`opal/core/references/opal-skills-registry.json:3-5`)
- **paths 치환 규칙**: `{project}` → `process.cwd()`, `~` → `os.homedir()`. `validate()`에서 적용 (`opal/tools/skill-registry/skill-registry.js:375-378`)
- **스킬 물리 위치 2원화**:
  - `opal/skills/` — opal-pilot-*/op-*/opal-* 등 OPAL 전용 스킬
  - `skills/` (top-level) — standalone 그룹의 독립 스킬(api-analyzer, interview 등)
  - 레지스트리 paths는 모두 동일 형식 (`{project}/.opal/skills/` 또는 `~/.opal/skills/`)
- **install 배포 방식**: `scripts/install-mac.sh:923-934`는 `opal/skills/*/` 폴더 전체를 동적으로 순회하여 배포. **개별 스킬명 하드코딩 없음** → 폴더 리네임만으로 배포 cascade 자동 완성. 스크립트 소스 수정 불필요.
- **validate 현재 구현**: `validate()` 함수(`opal/tools/skill-registry/skill-registry.js:277-392`)가 **이미 존재**하며, `no SKILL.md found at any path`를 **warning(exit 0)**으로만 처리 (`:379`). R4는 이를 **error(exit 1)**로 격상 + **unregistered 역방향 감지** 추가 요구. → R4는 "신설"이 아니라 **"확장"**이다.

### 1.3 의존성 맵

```
opal-skills-registry.json (SSOT)
  ├─ skill-registry.js (loadJsonFile()로 로드)
  ├─ opal/core/AGENT.md (Lazy 트리거 //opbr 조건 참조)
  ├─ docs/PROJECT.md (컴포넌트 테이블 직접 참조)
  ├─ docs/ARCHITECTURE.md (스킬 목록 직접 참조)
  └─ README.md (공개 문서 직접 참조)

opal/skills/opal-brain/ (리네임 대상 폴더)
  ├─ op-brain-ingest/SKILL.md (내부 opal-brain //opbr 참조)
  ├─ opal/core/AGENT.md (섹션 헤딩 "opal-brain 활용 규칙")
  └─ docs/proposals/opal-brain-design.md (설계 이력 — 보존)
```

### 1.4 테스트 현황

- `opal/tools/skill-registry/` — **단위 테스트 파일 없음** (skill-registry.js 단독)
- `opal/tools/brain-tool/tests/test_brain_tool.py` — Python 단위 테스트 존재. `"domain": "opal-brain"` 값 하드코딩 검증 (`test_brain_tool.py:1209,1238`) — 리네임 불필요(도메인 태그)
- R4 AC: validate 단위 테스트 신규 생성 필요

---

## 2. 외부 조사 결과

해당 없음 (모든 분석 대상이 프로젝트 내부 파일).

---

## 3. 영향 범위

### 3.1 직접 영향

| 대상 | 변경 유형 |
|------|----------|
| `opal/core/references/opal-skills-registry.json` | JSON 수정 — opal-brain→opal-pilot-brain, alias opbr→opb, 그룹 재배치 4건, dangling 2건 제거, 미등록 1건 등록 |
| `opal/skills/opal-brain/` 폴더 | 폴더 리네임 → `opal-pilot-brain/` |
| `opal/skills/opal-brain/SKILL.md` (리네임 후) | name/alias/triggers 수정 |
| `opal/core/AGENT.md` | opal-brain→opal-pilot-brain, //opbr→//opb (7개 이상 라인) |
| `docs/PROJECT.md` | opal-brain→opal-pilot-brain, opbr→opb, op-sdd-tasks 행 삭제 |
| `README.md` | opbr 섹션·커맨드 갱신 (5개 이상 라인) |
| `opal/tools/skill-registry/skill-registry.js` | R4 validate 확장: dangling error 격상 + unregistered 역방향 감지 |
| `opal/skills/op-brain-ingest/SKILL.md` | 내부 opal-brain/opbr 참조 갱신 |
| `docs/ARCHITECTURE.md` | opal-orchestrator 잔존 행 제거 |

### 3.2 간접 영향

| 대상 | 영향 | 결론 |
|------|------|------|
| `~/.opal/skills/opal-brain/` (배포본) | install 재실행 후 자동 opal-pilot-brain으로 갱신 | install-mac.sh 재배포로 자동 처리 |
| `opal/tools/brain-tool/brain_tool.py` | `domain: "opal-brain"` — brain 페이지 분류 태그 | 변경 불필요 (스킬명과 물리 연결 없음) |
| `docs/proposals/opal-brain-design.md` | 과거 설계 이력 | 변경 금지 (②보존 대상) |
| `opal/bootstrapper/` (4개 파일) | opal-brain 직접 언급 0건 (grep 확인) | 변경 불필요 |
| `scripts/install.ps1`, `install.sh` | opal-brain 직접 언급 0건 | 변경 불필요 |

### 3.3 영향 범위 요약

- [x] 설정/환경변수 변경 — 레지스트리 JSON 구조 변경
- [x] 빌드/배포 파이프라인 변경 — install 재실행 필요 (폴더 리네임 cascade)
- [ ] DB 스키마 변경 — 해당 없음
- [ ] API 인터페이스 변경 — 해당 없음

---

## 4. 핵심 발견 사항

### 4.1 opal-brain 전역 참조 인벤토리

grep 전수 검색 결과 (범위: `opal/`, `scripts/`, `docs/`, `README.md`. `tasks/` 및 `~/.opal/` 제외):

| 경로 | 줄번호 | 내용 요약 | 분류 |
|------|--------|----------|------|
| `opal/core/references/opal-skills-registry.json` | 670-684 | `"name": "opal-brain"`, `"alias": "opbr"`, triggers, paths | ① 리네임 대상 |
| `opal/skills/opal-brain/SKILL.md` | 2, 5, 7, 9, 10, 41 | frontmatter name/alias/trigger, 모드 설명 내 참조 | ① 리네임 대상 |
| `opal/skills/opal-brain/references/brain-schema.md` | 4, 108 | "opal-brain 스킬 운용자", [[opal-brain-skill]] 링크 | ① 리네임 대상 |
| `opal/skills/op-brain-ingest/SKILL.md` | 51, 55 | `opal-brain //opbr ingest`, `//opbr init` 참조 | ① 리네임 대상 |
| `opal/core/AGENT.md` | 39, 194, 203, 213, 231, 247, 446, 447 | opal-brain 활용 규칙 섹션, //opbr ask/ingest | ① 리네임 대상 |
| `opal/core/references/opal-harness.md` | 241 | `//opbr` 언급 (brain-tool 트리거 설명) | ① 리네임 대상 |
| `docs/PROJECT.md` | 79, 83 | opal-brain 컴포넌트 표, opbr alias, `//opbr init` | ① 리네임 대상 |
| `docs/proposals/opal-brain-design.md` | 5, 172-173, 186-189, 197-215, 236-239, 286, 309, 369, 387, 400, 413, 427, 431, 456, 458 | 과거 설계 이력·결정 근거·구현 식별자 정의 | ② 보존 (설계 이력 문서) |
| `opal/tools/brain-tool/brain_tool.py` | 5 | `"domain": "opal-brain"` — brain 페이지 도메인 태그 | ② 보존 (스킬명과 물리 연결 없음) |
| `opal/tools/brain-tool/templates/schema-template.md` | 4, 196-197 | 변경이력 언급 | ② 보존 (변경이력) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | 5, 690, 1209, 1237-1238 | `"domain": "opal-brain"` 테스트 값 | ② 보존 (brain 도메인 태그, 스킬 리네임 무관) |
| `README.md` | 43, 65, 307, 662, 670-673 | `//opbr` 커맨드 예시, `opbr — 프로젝트 브레인` 섹션 | ① 리네임 대상 |

**① 리네임 대상 파일: 9개** (registry JSON, opal-brain/SKILL.md, brain-schema.md, op-brain-ingest/SKILL.md, opal/core/AGENT.md, opal-harness.md, docs/PROJECT.md, README.md, 폴더명)

> op-brain-ingest는 리네임 대상 아님 — 스킬명 유지, 그룹 이동(op-brain 신규 그룹)만, SKILL.md 내 문자열만 갱신.

### 4.2 alias opbr→opb 충돌 검사

레지스트리 전수 확인 결과 현행 alias 22개:
`opp`, `opd`, `opds`, `opdw`, `opwt`, `opsdd`, `opgc`, `opdd`, `wfb`, `uid`, `wtm`, `erm`, `mockup`, `html-sa`, `onb`, `start`, `opi`, `oppd`, `osc`, `oac`, `osm`, `opbr`

**`opb` alias는 어떤 스킬에도 등록되지 않음. 충돌 없음.** (`opal-pilot-brain=opb`는 `opal-pilot-data-design=opdd`, `opal-pilot-dev=opd`, `opal-pilot-sdd=opsdd`, `opal-pilot-gc=opgc` 패턴과 정합)

### 4.3 dangling 2건 추적 — M2 판정

#### op-sdd-tasks

- **git 이력**: commit `a940318` (feat(093), 2026-04-07) — opsdd 7→5단계 파이프라인 축소 시 op-sdd-tasks 물리 삭제. 기능은 op-sdd-plan(SPEC-PLAN)으로 통합.
- **op-sdd-action-plan과의 관계**: op-sdd-action-plan은 "SDD ACT 전용 경량 PLAN" (`opal/skills/op-sdd-action-plan/SKILL.md:2-10`) — 다른 역할. **리네임 매핑 아님.**
- **PROJECT.md 정합**: `docs/PROJECT.md:61`에 op-sdd-tasks 잔존 — 함께 제거 필요
- **권고**: **레지스트리에서 제거 + PROJECT.md 행 삭제**

#### opal-orchestrator

- **git 이력**: commit `45d2118` (chore(086), 2026-04-05) — "opal-orchestrator 스킬 삭제 — opal-pm.md로 완전 대체". `opal/core/AGENT.md` 변경이력 기록.
- **현재 잔존**: `opal/core/references/opal-skills-registry.json:619-628`, `docs/ARCHITECTURE.md:126,328`
- **권고**: **레지스트리에서 제거 + ARCHITECTURE.md 해당 행 제거**

### 4.4 op-sdd-action-plan 미등록 분석

- **SKILL.md**: name=`op-sdd-action-plan`, version=1.0.0, alias 없음 (`opal/skills/op-sdd-action-plan/SKILL.md:2-12`)
- **dispatched_by**: `opal-sdd-action-agent` (`opal/agents/opal-sdd-action-agent/AGENT.md:40,73,263`)
- **레지스트리 등록 제안 스키마** (op-sdd 그룹 기존 패턴 준수):

```json
{
  "name": "op-sdd-action-plan",
  "alias": null,
  "description": "SDD ACT 전용 경량 PLAN 스킬 — SPEC.md + SPEC-PLAN.md + TEST-SCENARIOS.md + ACT 정의 기반 구현 청사진 작성",
  "triggers": ["^op-sdd-action-plan$"],
  "paths": [
    "{project}/.opal/skills/op-sdd-action-plan/SKILL.md",
    "~/.opal/skills/op-sdd-action-plan/SKILL.md"
  ],
  "stage": "PLAN(ACT)",
  "dispatched_by": ["opal-sdd-action-agent"]
}
```

그룹: `op-sdd` (SDD 계열 단계 스킬이므로). 단, 등록 전 op-sdd 그룹의 실제 항목 스키마 필드(stage/dispatched_by 유무)를 그대로 따른다.

### 4.5 skill-registry.js 구조 분석 — R4 validate 설계 근거

**(a) 로드 방식**: `getReferencesDir()`(`opal/tools/skill-registry/skill-registry.js:55-63`) — 배포 후 `~/.opal/references/`, 소스 환경 `opal/core/references/` 순 탐색.

**(b) validate 현재 구현**: 이미 존재 (`skill-registry.js:277-392`, 디스패치 `case 'validate':` `:438-439`). `no SKILL.md found at any path` → **warning(exit 0)** (`:379`). R4 요구: **error(exit 1)로 격상 + unregistered 역방향 감지 추가**.

**(c) standalone vs opal/skills 위치 구분**:

레지스트리 paths는 모두 `~/.opal/skills/` 형태로 동일. unregistered 감지는 소스 레포 기준 2개 폴더 스캔 필요:

```js
const srcDirs = [
  path.resolve(cwd, 'opal', 'skills'),  // opal-pilot-*, op-*, opal-*
  path.resolve(cwd, 'skills'),           // standalone (api-analyzer 등)
];
```

소스 환경 판별: `getReferencesDir()`이 `opal/core/references/` 반환 시 = 소스 환경 → unregistered 스캔 활성화. 배포 환경에서는 false positive 방지를 위해 비활성 (또는 `--source-mode` 플래그).

**(d) R4 실질 구현 범위**:
1. `no SKILL.md found` warning → error 격상 (`skill-registry.js:379`)
2. `validateUnregistered(srcDirs, registeredNames)` 신규 함수 (소스 환경 전용)
3. 단위 테스트: dangling exit 1, clean exit 0, unregistered exit 1 케이스

**(e) 테스트 현황**: `opal/tools/skill-registry/` — 단위 테스트 없음. R4에서 신규 생성.

### 4.6 install cascade 지점

`scripts/install-mac.sh:923-934`: 폴더를 동적으로 순회하여 `$skill_name`을 basename으로 읽어 배포. **opal-brain 직접 하드코딩 없음. 폴더 리네임만으로 배포 자동 완성.**

`scripts/install.ps1`, `scripts/install.sh`, `opal/bootstrapper/` — opal-brain/opbr 직접 참조 0건 (grep 확인). 수정 불필요.

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | cascade 누락: `opal/core/AGENT.md`의 //opbr 참조 7개 이상 — 모두 갱신 필수 | 높음 | `opal/core/AGENT.md:39,213,231` |
| R-2 | backward-compat M1: //opbr → //opb 완전 교체 시 기존 사용자 매칭 실패 | 중간 | `opal/skills/opal-brain/SKILL.md:9`, TASK.md §M1 |
| R-3 | validate false positive: unregistered 감지 시 standalone(`skills/` top-level)과 `opal/skills/`를 모두 체크해야 함. `opal/skills/` 만 체크 시 standalone 폴더 오판 | 중간 | 레지스트리 standalone 그룹 (§4.5) |
| R-4 | ARCHITECTURE.md 잔존: 레지스트리에서 opal-orchestrator 제거 후에도 ARCHITECTURE.md에 잔존 | 낮음 | `docs/ARCHITECTURE.md:126,328` |
| R-5 | brain_tool.py domain 값 오인: `"domain": "opal-brain"` 을 스킬 리네임 연동 항목으로 오해할 수 있음 | 낮음 | `opal/tools/brain-tool/brain_tool.py:5` |
| R-6 | validate 소스/배포 환경 구분: unregistered 감지는 소스 환경 전용. 배포 환경에서 실행 시 false positive 위험 | 중간 | `skill-registry.js:55-63` |
| R-7 | 용어 일관성: AGENT.md Lazy 트리거 조건 `//opbr` → `//opb` 갱신 필요. `citation-rules.md §7` 영역 간 용어 일관성 점검 항목 | 중간 | `opal/core/AGENT.md:39`, `citation-rules.md §7.2` |

---

## M1 권고: opbr backward-compat alias

**권고: 과도기적 trigger 유지.** 레지스트리 alias 표시값은 `opb`로 변경하되, SKILL.md triggers와 레지스트리 triggers에 `"^opbr$"`, `"^opal-brain$"` 패턴을 한시 유지(backward-compat)하여 기존 머슬메모리를 보호한다. 제거 일정은 PLAN 단계에서 명시.

## M2 권고: dangling 2건 처리

| 스킬 | 판정 | 처리 방향 |
|------|------|----------|
| `op-sdd-tasks` | 제거 | 레지스트리 삭제 + `docs/PROJECT.md:61` 행 삭제 (commit a940318 근거) |
| `opal-orchestrator` | 제거 | 레지스트리 삭제 + `docs/ARCHITECTURE.md:126,328` 행 삭제 (commit 45d2118 근거) |
