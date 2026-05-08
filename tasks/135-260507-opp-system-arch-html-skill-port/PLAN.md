# PLAN: system-architecture-html 스킬 OPAL 통합 + 트윈 빌드 비교

> 작성일: 2026-05-07 (초안) / 2026-05-08 (결정 변경)
> 입력: TASK.md
> 출력: PLAN.md

---

## 🚨 결정 변경 (2026-05-08, 캡틴 지시) — 본문 Override

> 본 박스의 내용은 §1~§5 본문보다 **우선 적용**한다. 본문과 충돌하는 모든 항목은 이 박스를 따른다.

### 변경 사유

캡틴 지시: **"OPAL pilot과 무관한 일반 스킬"**로 만든다. `skills/`(standalone 그룹)에 있는 다른 일반 도구 스킬(`html-mockup`, `ui-designer`, `erd-modeler`, `wireframe-builder`, `web-to-markdown`, `api-analyzer`, `interview`)과 동일 카테고리·관리 패턴으로 통합.

### 핵심 변경 매트릭스

| 항목 | 변경 전 (본문) | 변경 후 (Override) |
|------|---------------|-------------------|
| 폴더 위치 | `community-skills/anthropics/system-architecture-html/` | **`skills/system-architecture-html/`** |
| 현재 폴더 위치 (캡틴 수동 이동 결과) | `skills/system-architecture-html/`(원위치) | **`community-skills/anthropics/system-architecture-html/`** (Step 1에서 `skills/`로 되돌림) |
| 레지스트리 SSOT | `opal/core/references/community-skills-registry.json` | **`opal/core/references/opal-skills-registry.json`** |
| 레지스트리 그룹 | `groups.anthropics` | **`groups.standalone`** |
| 등록 항목 name | `anthropics/system-architecture-html` | **`system-architecture-html`** |
| 등록 항목 paths | `["~/.opal/community-skills/anthropics/system-architecture-html/SKILL.md"]` | **`["{project}/.opal/skills/system-architecture-html/SKILL.md"]`** (standalone 다른 항목 패턴 — `D-4` `groups.standalone`의 7개 기존 항목 모두 동일 형식) |
| 등록 항목 alias / triggers / description | 변경 없음 | 변경 없음 |
| SKILL.md frontmatter `license: Proprietary` | 보존 | **보존** (출처 정보 유지 — 위치 이동만으로 라이선스 정보 유실 없음) |

### 영향 받는 본문 섹션 (Override 적용)

- §1 참조 문서 (`D-4`: `community-skills-registry.json` → `opal-skills-registry.json`)
- §1 관련 파일 (`community-skills/anthropics/...` → `skills/...`)
- §1 영향 범위 (이동 방향 반전)
- §2.2 N-1~N-5 (신규 생성 경로 — `community-skills/anthropics/...` → `skills/...`)
- §2.2 M-1 (레지스트리 파일 경로)
- §2.2 X-1 (삭제 대상 — `skills/...` → `community-skills/anthropics/...`)
- §2.4 M-1 (레지스트리 등록 항목 — name / paths / 그룹 모두 변경)
- §2.4 M-2 (위치 — `community-skills/anthropics/...SKILL.md` → `skills/...SKILL.md`. 5종 변경 a~e 사양은 그대로 적용)
- §3 Step 1 (이전 방향 반전)
- §3 Step 2 (레지스트리 파일·그룹 변경)
- §3 Step 3 (검증 대상 레지스트리 파일·그룹 변경)
- §4 R-1 / R-2 체크리스트 (대응 경로/파일 변경)
- §5 R-T1~R-T8 리스크 (등록 위치 관련 항목)

### 영향 없는 본문 섹션 (그대로 유지)

- §2.1 ai-framework 시스템 아키텍처 분석 (A/B 두 회차의 공통 입력 — 6레이어 18노드)
- §2.3 구현 순서 (순서·Phase 그룹핑은 동일, 대상만 변경)
- §2.4 M-2 OPAL 호환 5종 변경 a~e 사양 (SKILL.md 변경 항목 그대로)
- §3 Step 4~6 (A 산출 / SKILL.md 수정 / B 산출)
- §3 Step 7 (R-7 메모리 규칙 검증)
- 트윈 빌드 입력 동일성·순서 강제·B visible 흔적 제약

### Step 1 (Override) — 폴더 되돌리기

```bash
# 현 상태: community-skills/anthropics/system-architecture-html/ (캡틴 수동 이동 결과)
# 목표: skills/system-architecture-html/ (standalone 위치)

git mv community-skills/anthropics/system-architecture-html/SKILL.md skills/system-architecture-html/SKILL.md
mkdir -p skills/system-architecture-html/references
git mv community-skills/anthropics/system-architecture-html/references/{template.html,design-system.md,copywriting.md,examples.md} skills/system-architecture-html/references/
rmdir community-skills/anthropics/system-architecture-html/references community-skills/anthropics/system-architecture-html
```

**AC**:
- `community-skills/anthropics/system-architecture-html/` 부재
- `skills/system-architecture-html/SKILL.md` 존재
- `skills/system-architecture-html/references/` 안에 4개 파일 존재
- 파일 내용 무변경 (체크섬 일치 — 작업 시작 시점 측정값 대비)

### Step 2 (Override) — 레지스트리 등록 항목

대상: `opal/core/references/opal-skills-registry.json` `groups.standalone` 배열 끝에 다음 객체 1건 삽입.

```json
{
  "name": "system-architecture-html",
  "alias": "html-sa",
  "description": "시스템 아키텍처 다이어그램 HTML 생성 — 다층 구조, 색상 코드, 빌드 우선순위 배지",
  "triggers": [
    "^html-sa$",
    "^system-architecture-html$",
    "(?i)(시스템\\s*아키텍처\\s*HTML|아키텍처\\s*다이어그램\\s*HTML)",
    "(?i)(architecture\\s*diagram\\s*HTML|system\\s*architecture\\s*HTML)"
  ],
  "paths": ["{project}/.opal/skills/system-architecture-html/SKILL.md"]
}
```

**AC**:
- JSON 파싱 통과
- `groups.standalone` 배열 길이 7 → 8 (기존 7개 무수정 + 1건 추가)
- name·alias·triggers·paths 정확 일치
- 다른 그룹(`opal-pilot`, `op-dev`, `op-task`, `op-sdd`, `opal`) 무수정

### Step 3 (Override) — 등록 검증 2단

(α) **소스 직접 파싱 검증** (R-7 무위반):
```bash
python3 -c "
import json
d = json.load(open('opal/core/references/opal-skills-registry.json'))
items = [x for x in d['groups']['standalone'] if x['name'] == 'system-architecture-html']
assert len(items) == 1, f'expected 1, got {len(items)}'
it = items[0]
assert it['alias'] == 'html-sa'
assert len(it['triggers']) >= 4
assert it['paths'] == ['{project}/.opal/skills/system-architecture-html/SKILL.md']
print('alpha-pass')
"
```

(β) **`~/.opal/` 배포본 매칭 호출** (정보 제공용 — fail 판정 안 함):
```bash
node ~/.opal/tools/skill-registry/skill-registry.js validate
node ~/.opal/tools/skill-registry/skill-registry.js match "//html-sa"
```

> ai-framework 소스 갱신은 `~/.opal/`에 동기화되지 않으므로 (β)는 미매칭이 정상. EXECUTE.md에 결과만 기록한다.

### 변경 이유 — 짧게

OPAL 호환 수정(M-2)으로 `/mnt/user-data/outputs/` / `present_files`를 제거하면 SKILL.md가 사실상 `html-mockup`과 동급 OPAL 표준 형식이 된다. "외부 출처" 라벨이 형식적 분류에 그치므로, 다른 일반 도구 스킬(html-mockup 등)과 동일한 standalone 카테고리에 두는 것이 발견성·일관성·관리 부담 측면 모두 유리. 출처 정보는 SKILL.md frontmatter `license: Proprietary`로 보존.

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | system-architecture-html 원본 SKILL.md | `skills/system-architecture-html/SKILL.md` | R-4 1차 산출 기준 + R-5 수정 출발점 |
| D-2 | 소스 | system-architecture-html 원본 references | `skills/system-architecture-html/references/{template.html,design-system.md,copywriting.md,examples.md}` | R-1 이전 대상 4파일 |
| D-3 | 소스 | html-mockup SKILL.md | `skills/html-mockup/SKILL.md` | OPAL 호환 §0 호출 환경 / Step 1 환경 감지 / Step 2 컨텍스트 흡수 패턴 차용 |
| D-4 | 설계 | 커뮤니티 스킬 레지스트리 SSOT | `opal/core/references/community-skills-registry.json` | R-2 등록 대상 |
| D-5 | 설계 | OPAL 스킬 레지스트리 도구 | `~/.opal/tools/skill-registry/skill-registry.js` | R-3 등록 검증 도구 (소스 코드 분석으로 동작 범위 확인) |
| D-6 | 기획 | 배포 경계 메모리 | `~/.claude_platform_mkt/projects/-Volumes-Data-AIStudio-workspace-ai-framework/memory/feedback_deploy_boundary.md` | R-7 메모리 규칙 (`~/.opal/` 직접 수정 금지) |
| D-7 | 설계 | 프로젝트 정의 SSOT | `docs/PROJECT.md` | §2.1 ai-framework 시스템 아키텍처 분석의 폴더 구조 + 프로젝트 원칙 근거 |
| D-8 | 설계 | 시스템 아키텍처 SSOT | `docs/ARCHITECTURE.md` | §2.1 ai-framework 시스템 아키텍처 분석의 컴포넌트 관계 + 배포 모델 근거 |
| D-9 | 설계 | TASK.md (본 태스크) | `tasks/135-260507-opp-system-arch-html-skill-port/TASK.md` | R-1~R-7 + AC |
| D-10 | 설계 | 인용 규칙 | `~/.opal/references/harness/citation-rules.md` | PLAN.md 근거 제시 형식 (필수 하네스) |

> 인용 형식: `~/.opal/references/harness/citation-rules.md` §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부`.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `skills/system-architecture-html/SKILL.md` | 외부 출처 스킬 본체 (이전 대상) | ✅ 이전 + R-5 수정 | `D-1` 1-116 |
| `skills/system-architecture-html/references/template.html` | HTML 보일러플레이트 (제너레이터) | ✅ 이전(보존) | `D-2` 13882B |
| `skills/system-architecture-html/references/design-system.md` | 디자인 시스템 가이드 | ✅ 이전(보존) | `D-2` 7072B |
| `skills/system-architecture-html/references/copywriting.md` | 카피라이팅 가이드 | ✅ 이전(보존) | `D-2` 5881B |
| `skills/system-architecture-html/references/examples.md` | 예시 아키텍처 2종 | ✅ 이전(보존) | `D-2` 4959B |
| `community-skills/anthropics/system-architecture-html/` | 이전 후 새 위치 | ✅ 신규 생성 | `D-7` §폴더 구조맵 — `community-skills/`=외부 조직 제공 스킬 |
| `opal/core/references/community-skills-registry.json` | 커뮤니티 스킬 레지스트리 | ✅ 항목 1건 추가 | `D-4` `groups.anthropics` 배열 |
| `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` | 1차 산출(원본 스킬 결과) | ✅ 신규 생성 | `D-9` R-4 |
| `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` | 2차 산출(수정 스킬 결과) | ✅ 신규 생성 | `D-9` R-6 |
| `~/.opal/tools/skill-registry/skill-registry.js` | 레지스트리 검증 도구 | ❌ 무수정 (분석만) | `D-5` 34-42 (`getReferencesDir()`) |
| `~/.opal/community-skills/anthropics/system-architecture-html/SKILL.md` | 배포본 (R-7로 미수정) | ❌ 본 태스크에서 미생성 | `D-6` |

> 근거: `파일:N-M` 포맷. 없으면 `-`.

### 현재 상태

1. **외부 출처 스킬 위치**: `skills/system-architecture-html/`에 SKILL.md 1개 + `references/` 4개 파일이 존재한다 (`Bash ls` 결과로 확인). 이 위치는 OPAL 자체 스킬 폴더(`docs/PROJECT.md` §폴더 구조맵: "`skills/` = 독립 스킬 소스, 파이프라인 없이 단독 사용하는 스킬")이므로 외부 조직 제공 스킬 표준 위치(`community-skills/`)와 어긋난다.
2. **레지스트리 미등록**: `community-skills-registry.json`의 `groups.anthropics` 배열(18개 항목)에 `system-architecture-html` 항목 없음 (`D-4` 직접 grep 확인).
3. **원본 SKILL.md 비호환 요소** (`D-1` 80-82행):
   - `Save to /mnt/user-data/outputs/<system_name>_architecture.html` — Claude.ai 가상 머신 전용 경로, Claude Code 로컬 환경에서 미존재
   - `Use present_files to surface it to the user` — Claude.ai 전용 도구, Claude Code 미지원
4. **OPAL 환경 감지 패턴 부재**: 원본 SKILL.md에는 `html-mockup/SKILL.md` §0 호출 환경 / §1 Step 1 환경 감지 / §1 Step 2 컨텍스트 흡수 패턴(`D-3` 17-53행)이 없다.
5. **트리거 부재**: 원본 SKILL.md frontmatter `description`에 영문 키워드만 존재 — 정규식 트리거 패턴이 레지스트리에서도 없으므로 `//html-sa` 호출 시 매칭 실패.
6. **검증 도구 동작 범위** (핵심 발견 — `D-5` 34-42행):
   - `getReferencesDir()`는 `~/.opal/references/opal-skills-registry.json`이 존재하면 무조건 `~/.opal/references/`만 본다. ai-framework 소스 레지스트리(`opal/core/references/community-skills-registry.json`)는 직접 참조하지 않는다.
   - `--registry`, `--source` 같은 경로 오버라이드 플래그는 존재하지 않는다 (CLI 라우터 257-308행 확인).
   - 결과: 본 태스크에서 ai-framework 소스만 갱신하면 `node skill-registry.js match "//html-sa"`는 ai-framework 소스를 못 읽고 `found: false`를 반환한다.
7. **배포 경계 메모리** (`D-6`): `~/.opal/` 배포 파일 직접 편집 금지. 따라서 R-3 검증을 위해 `~/.opal/community-skills-registry.json`을 임시 갱신하는 우회는 금지된다.

### 영향 범위

- **이동 1건**: `skills/system-architecture-html/` → `community-skills/anthropics/system-architecture-html/` (5개 파일).
- **수정 1건**: `opal/core/references/community-skills-registry.json` (`groups.anthropics` 배열 끝에 1개 항목 추가, 기존 18개 항목 무수정).
- **수정 1건**: 이전된 `community-skills/anthropics/system-architecture-html/SKILL.md` (frontmatter + Process Step 변경).
- **신규 2건**: `outputs/A_original.html`, `outputs/B_opal_revised.html`.
- **무수정 영역**: `~/.opal/`, `references/` 4파일 내용, 다른 레지스트리 항목, `docs/`, `opal/skills/`.

---

## 2. 구현 계획

### 2.1 ai-framework 시스템 아키텍처 분석 (A/B 두 회차의 공통 입력)

> 본 절은 R-4·R-6의 "동일 프로젝트 입력" 보장을 위해 PLAN 단계에서 사전 확정한다. EXECUTE Step 4(A 산출) / Step 6(B 산출) 모두 본 절의 노드 사양을 그대로 참조한다.
> 근거: `D-7` §폴더 구조맵 / §주요 컴포넌트 + `D-8` 전체 구조 + 본 PLAN 단계의 `Bash ls` 직접 검증 결과.

**시스템 명칭**: OPAL — Open Protocol for Agentic Links (`D-7` §프로젝트 개요)
**원라이너**: AI 환경에서 IT 프로젝트를 체계적으로 수행하기 위한 범용 AI 개발 프레임워크 (`D-7` 인용문)
**메타 패널 값** (template.html `head .meta` 영역):

- target: AI 에이전트로 IT 프로젝트를 수행하는 개발자/PM
- BM: OSS 프레임워크 (수익 모델 없음 — 표준화 + 재사용성 우선)
- stack: Markdown / YAML / Bash / Node.js (`D-7` 프로젝트 구성)
- timeline: Phase = 아키텍처 안정화 — 멀티 플랫폼 확장 중 (`D-7` §프로젝트 개요)

**레이어 구성 (확정 6레이어)**:

| # | 레이어명 | 태그 (역할) | 노드 (이름 / 배지 / 1줄 설명 / tech chips) |
|---|---------|-----------|-----------------------------------------|
| 1 | Channel / Entry | 사용자 진입점 — CLI 플랫폼 어댑터 계층 | (a) Claude Code [DONE] — 메인 플랫폼, sub-agent + skills 풀 지원 / `Anthropic Claude Code CLI` (b) Cursor [DONE] — `~/.cursor/rules/000-opal-agent.mdc`로 정체성 주입 / `Cursor Rules` (c) Gemini CLI / Antigravity [LATER] — 어댑터 일부 미지원, sub-agent 비호환 / `Google Gemini CLI` |
| 2 | Identity / Bootstrap | 정체성·부트스트랩 — 세션 시작 시 강제 로드 | (a) `~/.opal/AGENT.md` [DONE] — Eager/Lazy 트리거 테이블 + 부트스트래퍼 자동 관리 / `Markdown` (b) `~/.opal/identity.md` [DONE] — YAML frontmatter (이름/소유자/톤/성격) / `YAML` (c) 프로젝트 부트스트래퍼 [DONE] — `CLAUDE.md` / `GEMINI.md` / `.cursor/rules/` 자동 삽입 / `Auto-managed` (d) `{project}/.opal/AGENT.md` [DONE] — PM 역할 활성화 트리거 / `Markdown` |
| 3 | Orchestrator + Stage Skills | Pilot 오케스트레이터 + 단계 스킬 | (a) `opal-pilot-project` (opp) [DONE] — TASK→PLAN→EXECUTE→CLOSE / `Pipeline` (b) `opal-pilot-dev` / `opal-pilot-sdd` / `opal-pilot-gc` [DONE] — dev/sdd/gc 파이프라인 / `Pipeline` (c) op-task / op-task-plan / op-task-execute / op-task-qa [DONE] — opp 단계 스킬 / `Skill` (d) op-dev-* / op-sdd-* [DONE] — dev·sdd 단계 스킬 / `Skill` |
| 4 | Worker Agents | 디스패치 가능한 전문 워커 (12종) | (a) opal-task-agent (범용 PLAN/EXEC) / opal-plan-agent (PLAN 전문) [DONE] / `Sub-agent` (b) opal-fe-agent / opal-be-agent / opal-db-agent / opal-test-agent [DONE] — 도메인 전문 / `Sub-agent` (c) opal-task-qa-agent / opal-security-checker / opal-convention-checker [DONE] — 검증 / `Sub-agent` (d) opal-task-action-agent / opal-sdd-action-agent / opal-planning-agent / wtm-agent [DONE] — 액션·계획·전사 / `Sub-agent` |
| 5 | Tools + Registries | 도구 + 메타데이터 SSOT | (a) state-tool [DONE] — STATE.md 9 서브명령 + 절차 강제력 SSOT / `Python` (b) skill-registry [DONE] — alias/triggers 매칭 + validate / `Node.js` (c) code-scan / xlsx-tool / date / playwright-tool / check-env [DONE] / `Node/Python` (d) opal-skills-registry.json + community-skills-registry.json + agents.md + opal-model-mapping.md [DONE] — 메타 SSOT 4종 / `JSON/MD` |
| 6 | Artifacts + Operations | 산출물·운영 — 태스크 폴더 + 메모리 + 배포 | (a) `tasks/{NNN}-*/` [DONE] — STATE/TASK/PLAN/EXECUTE/CLOSE 산출물 + `outputs/` / `Filesystem` (b) `.opal/MEMORY.md` + `memory/` [DONE] — 카테고리 6종(task/project/architecture/feedback/preferences/issues) / `Markdown` (c) `scripts/install-mac.sh` [DONE] — `~/.opal/` 배포 + 부트스트래퍼 삽입 / `Bash` (d) docs/ARCHITECTURE.md / docs/CONVENTIONS.md / README.md [DONE] — 프로젝트 SSOT / `Markdown` |

**색상 매핑 (template.html `:root` 변수 그대로 사용)**:

| 레이어 | 변수 | HEX |
|--------|------|-----|
| L1 Channel/Entry | `--c-l1` | `#7CA9FF` (블루) |
| L2 Identity | `--c-l2` | `#9C8CFF` (퍼플) |
| L3 Orchestrator | `--c-l3` | `#FF8FA3` (코랄핑크) |
| L4 Workers | `--c-l4` | `#5BD3B0` (민트) |
| L5 Tools | `--c-l5` | `#FFB454` (오렌지) |
| L6 Artifacts | `--c-l6` | `#F7C66B` (옐로) |

**accent**: `#FF5A1F` (template.html 기본값 유지 — 변경 불필요).

**레전드 상태 배지**: `MVP / LATER / DONE` 3종 사용. 본 프로젝트는 안정화 단계이므로 거의 모든 노드가 `DONE`이고, Gemini/Antigravity 일부 어댑터만 `LATER`다.

**로드맵 섹션** (template.html `.roadmap` 영역):

- **Now**: 멀티 플랫폼 어댑터 확장 (Antigravity 정식 지원), 파이프라인 현황판 정합화
- **Next**: opal-pilot-write-tech 정식화, 커뮤니티 스킬 등록 자동화
- **Later**: 비-Anthropic 모델 정식 호환(Sonnet 4.5, Gemini 2.5 등 매핑 검증)

> 본 분석은 PLAN 산출물에 명시되어 EXECUTE Step 4·6에서 동일하게 사용되어야 한다 ([MUST] §2.4 인용 — `~/.opal/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지").

---

### 2.2 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `community-skills/anthropics/system-architecture-html/SKILL.md` | 이전된 스킬 본체 | (→ D-9 R-1) |
| N-2 | `community-skills/anthropics/system-architecture-html/references/template.html` | 이전된 보일러플레이트 | (→ D-9 R-1) |
| N-3 | `community-skills/anthropics/system-architecture-html/references/design-system.md` | 이전된 디자인 시스템 | (→ D-9 R-1) |
| N-4 | `community-skills/anthropics/system-architecture-html/references/copywriting.md` | 이전된 카피라이팅 가이드 | (→ D-9 R-1) |
| N-5 | `community-skills/anthropics/system-architecture-html/references/examples.md` | 이전된 예시 | (→ D-9 R-1) |
| N-6 | `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` | 1차(원본 스킬) HTML | (→ D-9 R-4) |
| N-7 | `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` | 2차(수정 스킬) HTML | (→ D-9 R-6) |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/community-skills-registry.json` | `groups.anthropics` 배열 끝에 항목 1건 추가 (alias `html-sa`, 트리거 4개, paths 1개) | (→ D-9 R-2 AC) |
| M-2 | `community-skills/anthropics/system-architecture-html/SKILL.md` (이전 후) | OPAL 호환 5종 변경 a~e (§2.4 참조) | (→ D-9 R-5 AC) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| X-1 | `skills/system-architecture-html/` 전체 디렉토리 | 이전 대상 — `community-skills/anthropics/`로 이동 후 원위치 잔존 금지 (→ D-9 R-1 AC: "이전 후 `skills/system-architecture-html/` 부재") |

> M-1과 M-2는 동일 회차에 모두 반영하지 않는다. 트윈 빌드 절차상 **M-1만 먼저 적용 → A 산출 → M-2 적용 → B 산출** 순서가 필수다 (§2.3 참조).

### 2.3 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 스킬 디렉토리 이동 (R-1) | N-1~N-5, X-1 | 낮음 (`mv` 또는 `git mv`) |
| 2 | 레지스트리 등록 (R-2) | M-1 | 낮음 (JSON 1행 추가) |
| 3 | 등록 검증 (R-3) | (검증만) | 낮음 (도구 호출 + 직접 파싱) |
| 4 | A 산출 — 원본 스킬 (R-4) | N-6 | 중간 (분석 결과 적용 + 출력 경로 강제 주입) |
| 5 | SKILL.md OPAL 호환 수정 (R-5) | M-2 | 중간 (5종 변경 a~e) |
| 6 | B 산출 — 수정 스킬 (R-6) | N-7 | 중간 (동일 입력 재사용 + 환경 감지/컨텍스트 흡수 흔적 반영) |
| 7 | 최종 점검 (R-7) | (검증만) | 낮음 (`~/.opal/` 무수정 검증 + changed_files 정리) |

> **핵심 의존**: Step 4(A 산출)는 Step 5(M-2 수정) **이전**에 수행해야 한다 — 원본 SKILL.md를 그대로 따른 결과가 비교 기준선이기 때문. Step 5 → Step 6은 순차 의존(같은 파일 SKILL.md 기반).
> [MUST] `~/.opal/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지" — 트윈 빌드의 분석 결과는 §2.1을 그대로 사용하며 회차마다 재추론하지 않는다.

#### Phase 그룹핑

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | 스킬 이전이 모든 후속의 전제 |
| 2 | 2 | 순차 | Step 1 완료 후 새 경로(`~/.opal/community-skills/anthropics/system-architecture-html/SKILL.md`) 기반 paths 등록 |
| 3 | 3 | 순차 | Step 2의 JSON 변경을 검증 |
| 4 | 4 | 순차 | A는 M-2 적용 전 원본 SKILL.md 기반 — Step 5보다 먼저 |
| 5 | 5 | 순차 | A 산출 완료 후 SKILL.md 수정 |
| 6 | 6 | 순차 | M-2 적용 후 B 산출 |
| 7 | 7 | 순차 | 모든 변경 종료 후 최종 점검 |

> 본 태스크는 모든 Step이 순차 의존이므로 병렬 실행 불가. Phase 7개 = Step 7개.

### 2.4 핵심 설계

#### M-1. 레지스트리 등록 항목 (R-2)

`opal/core/references/community-skills-registry.json` `groups.anthropics` 배열의 **마지막 항목** (현재 `anthropics/template`) 뒤에 다음 한 줄 객체를 삽입한다 (→ D-4 7-24 기존 18개 항목 패턴 통일):

```json
{
  "name": "anthropics/system-architecture-html",
  "alias": "html-sa",
  "description": "시스템 아키텍처 다이어그램 HTML 생성 — 다층 구조, 색상 코드, 빌드 우선순위 배지",
  "triggers": [
    "^html-sa$",
    "^system-architecture-html$",
    "(?i)(시스템\\s*아키텍처\\s*HTML|아키텍처\\s*다이어그램\\s*HTML)",
    "(?i)(architecture\\s*diagram\\s*HTML|system\\s*architecture\\s*HTML)"
  ],
  "paths": ["~/.opal/community-skills/anthropics/system-architecture-html/SKILL.md"]
}
```

설계 결정 근거:

- **alias `html-sa`**: 캡틴 합의 (→ D-9 §확정된 설계 방향 §3). 기존 anthropics 항목 18개 중 `alias` 필드를 채운 항목은 없으나, R-2 AC가 명시 요구하므로 `null`이 아닌 `"html-sa"`를 기재한다 (→ D-9 R-2 AC: `alias: "html-sa"`).
- **트리거 4개**: R-2 AC가 "최소 4개 패턴" 명시 — `^html-sa$` (alias 직접), `^system-architecture-html$` (full name), 한국어 정규식, 영어 정규식.
- **`paths`**: `~/.opal/community-skills/...`만 등록한다. `D-5` 34-42 분석 결과 — skill-registry.js는 `~/.opal/references/`만 본다. ai-framework 측 paths를 함께 넣으면 `validate`가 두 항목 중 첫 번째 존재 경로만 검사하므로 의미 없음. `{project}` placeholder도 `getReferencesDir()`가 ai-framework 소스를 안 읽으므로 무용. 따라서 배포 후 사용 시점 기준 단일 경로로 통일.

> [MUST] `~/.opal/references/harness/citation-rules.md` §2.4: "재해석 여지가 있는 금지사항·강제 규칙은 `[MUST]` 접두사 + 원문 인용으로 기재한다." → 본 항목 트리거 4개는 R-2 AC 원문이 정한 최소 요구이므로 추가 가능하나 4개 미만 금지.

#### M-2. SKILL.md OPAL 호환 수정 (R-5) — 5종 변경 a~e

이전 후 `community-skills/anthropics/system-architecture-html/SKILL.md`에 적용한다.

**(a) 출력 경로 변경** (R-5 AC (a))

원본(→ D-1:80-82): `Save to /mnt/user-data/outputs/<system_name>_architecture.html (use snake_case)`

수정 후 사양:

```
- 환경 감지(Step 1) 결과에 따라 저장 경로를 결정한다:
  | 환경 | 저장 경로 |
  | OPAL 태스크 폴더 | `tasks/{NNN}-*/outputs/<system_name>_architecture.html` (cwd가 태스크 폴더면 `outputs/...`) |
  | OPAL 프로젝트 (태스크 외) | `cwd/system-architecture/<system_name>_architecture.html` |
  | 비-OPAL / 사용자 직접 지정 | 인터뷰로 묻거나 cwd 기본값 사용 |
- snake_case 파일명 규칙은 유지한다 (원본 §3 그대로).
```

근거: (→ D-3 §1 Step 1 환경 감지 표 + `D-3` §0 호출 환경 패턴).

**(b) `present_files` 호출 제거** (R-5 AC (b))

원본(→ D-1:81): `Use present_files to surface it to the user`

수정 후 사양:

```
- `present_files` 도구 호출 제거.
- Write 도구로 파일 저장 후, 응답 본문에 절대 경로 1줄 안내:
  "✅ {절대경로} 생성 완료. 브라우저에서 바로 열 수 있습니다."
- 다중 산출이 아니므로 인덱스 페이지 자동 생성은 적용하지 않는다 (html-mockup §6과 다름).
```

근거: (→ D-3 §1 Step 6 보고 형식 차용).

**(c) §0 "호출 환경" 섹션 신설** (R-5 AC (c))

`# System Architecture HTML` 헤더 직후, `## When to use` **앞에** 다음 표 신설:

```markdown
## 0. 호출 환경

| 항목 | 값 |
|------|---|
| 호출 명령 | `//html-sa` 또는 `//system-architecture-html` |
| 별칭 | `html-sa` |
| 호출 가능 모드 | 비서(Assistant) / 태스크(Task) / PM / 오케스트레이터 — 모드 무관 |
| 특이 사항 | OPAL 프로젝트 여부 불문 (비-OPAL cwd에서도 동작 — 출력 경로만 환경 감지 결과에 따라 변동) |
```

근거: (→ D-3:17-25 html-mockup §0 호출 환경 패턴 — alias만 `html-sa`로 치환).

**(d) Step 1 "환경 감지" + Step 2 "컨텍스트 흡수" 신설** (R-5 AC (d))

원본(→ D-1) `## Process`의 기존 3 Step (1. Interview, 2. Draft the HTML, 3. Save and present) 앞에 2 Step을 **삽입**하여 총 5 Step으로 확장:

```markdown
## Process

### 1. 환경 감지 (Environment detection)

| 순서 | 조건 | 판정 |
|------|------|------|
| 1 | cwd에 `.opal/AGENT.md` 존재? | Yes → OPAL 프로젝트 |
| 2 | cwd 또는 상위에 `tasks/{NNN}-*/TASK.md` 패턴 존재? | Yes → 태스크 폴더 |
| 3 | STATE.md 또는 MEMORY.md 존재? | Yes → 세션 컨텍스트 폴백 |
| 4 | 위 모두 없음 | 비-OPAL / 컨텍스트 없음 |

### 2. 컨텍스트 흡수 (Context absorption)

| 환경 | 흡수 자원 | 추출 내용 |
|------|---------|---------|
| OPAL 프로젝트 + 태스크 폴더 | `TASK.md`, `ANALYSIS.md` (있으면), `PLAN.md` (있으면), `docs/PROJECT.md`, `docs/ARCHITECTURE.md` | 시스템 명칭, 레이어 후보, 노드 후보, MVP/LATER 분류 힌트, 기술 스택 |
| OPAL 프로젝트 (태스크 폴더 없음) | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `STATE.md`, `MEMORY.md` | 프로젝트 개요 + 컴포넌트 관계 |
| 비-OPAL | (없음) | 흡수 스킵 → 인터뷰(Step 3)에서 전체 수집 |

추론 가능한 항목(시스템 명칭, 레이어 수, 메타 패널 4종 등)은 인터뷰에서 스킵하고 1줄 통지로 대체:
"`{항목}`은 컨텍스트에서 `{추론값}`으로 자동 결정. 변경하시려면 알려주세요."

### 3. Interview (ONLY if information is missing)
... (원본 유지, 단 Step 2의 추론으로 채워진 항목은 자동 스킵 명시)

### 4. Draft the HTML
... (원본 유지)

### 5. Save and present
- (원본 §3 변경 — (a)(b) 사양 반영)
```

근거: (→ D-3:32-53 html-mockup §1 Step 1·Step 2 패턴 차용. system-architecture-html 도메인 특성상 흡수 자원에 `docs/ARCHITECTURE.md` 추가).

**(e) frontmatter `description` 한국어 트리거 보강** (R-5 AC (e))

원본(→ D-1:3): 영문 description 단일.

수정 후 사양 (frontmatter `description` 필드 끝에 한국어 트리거 키워드 명시 추가):

```yaml
description: |
  Create production-grade system architecture diagrams as standalone HTML files.
  Use this skill whenever the user asks for a system architecture, technical architecture diagram, layered system diagram, software architecture, infrastructure diagram, service blueprint, or AI system architecture as HTML/web format.
  Triggers (한국어): "시스템 아키텍처 HTML", "아키텍처 다이어그램 HTML", "기술 스택 다이어그램 HTML", "시스템 아키텍처를 HTML로 만들어줘".
  Triggers (English): "architecture diagram HTML", "system architecture HTML", "make my architecture into HTML", "tech stack diagram", "infrastructure diagram HTML".
  Output is ALWAYS a single self-contained .html file with no external dependencies (except optionally Google Fonts).
```

> 단순 키워드 추가만으로는 정규식 매칭이 안 된다(레지스트리 trigger가 정규식 매칭의 SSOT). description은 사람용 식별자이며, **실제 매칭은 M-1의 `triggers` 배열로 이루어진다**. R-5 AC는 description 보강만 요구하므로 설계 차이가 있음을 본 PLAN에 명시.

근거: (→ D-9 R-5 AC (e): "한국어 트리거 키워드 명시").

#### N-6. A 산출 (1차 — 원본 스킬) (R-4)

**중요 제약**: A는 **이전 직후, M-2 적용 전**의 SKILL.md를 따라 생성한다 — 비교 기준선 (→ D-9 §확정된 설계 방향 §4).

다만 원본 SKILL.md의 `Save to /mnt/user-data/outputs/...`(→ D-1:80)는 Claude Code 로컬에서 작동 불가하므로 **출력 경로만 강제 주입**한다:

```
저장 경로 강제 주입 규칙:
- 원본 SKILL.md의 §3 Save and present 단계에서 `/mnt/user-data/outputs/<name>_architecture.html` 부분만
  `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html`로 치환.
- `present_files` 도구는 호출하지 않고 Write 도구로 직접 저장 (Claude Code 환경 제약).
- 이외의 §1 Interview / §2 Draft the HTML / Quality bar / Common mistakes는 원본 그대로 따름.
- §2.1 ai-framework 분석 결과(레이어 6개 + 노드 18개 + 색상/배지/로드맵)를 입력으로 사용.
```

[MUST] `~/.opal/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지." — 분석 결과는 §2.1을 그대로 사용하며, A 산출 회차에서 Read를 통해 ai-framework 트리를 재추론하지 않는다.

근거: (→ D-9 R-4 AC: "단일 자기완결 HTML + 외부 의존(Google Fonts 외) 없이 렌더링 + ai-framework 실제 구성이 다이어그램 노드로 표현").

#### N-7. B 산출 (2차 — 수정 스킬) (R-6)

**중요 제약**: B는 M-2 적용 완료 후의 SKILL.md를 따라 생성한다.

```
- 입력 동일성 보장: §2.1 분석 결과를 그대로 입력 (A와 동일 텍스트). 두 산출물의 노드 명칭/배지/tech chips는 동일해야 한다.
- 환경 감지 결과 흔적 반영: 수정된 SKILL.md §1 Step 1 / Step 2 로직이 동작했음을 산출물에 visible하게 표현 — 다음 1가지 이상 적용:
  (i) HTML 메타 패널에 `context: docs/PROJECT.md + docs/ARCHITECTURE.md` 1줄 표기 또는
  (ii) Layer 6 (Artifacts + Operations) 노드 (b) `.opal/MEMORY.md`의 description에 "환경 감지로 자동 흡수됨" 표기 또는
  (iii) HTML 푸터에 `Generated via OPAL skill: anthropics/system-architecture-html (//html-sa) — context absorbed from ai-framework` 1줄.
- 저장 경로: `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` (수정된 SKILL.md §1 Step 1 환경 감지 결과 = OPAL 태스크 폴더 → outputs/ 자동 결정).
```

근거: (→ D-9 R-6 AC: "수정으로 추가된 환경 감지/컨텍스트 흡수 로직이 산출 과정에 반영됨").

#### R-3 검증 명령 (D-5 분석 결과 반영)

skill-registry.js는 `~/.opal/references/`만 본다 (→ D-5:34-42). 본 태스크는 R-7로 `~/.opal/` 직접 수정 금지이므로 다음 **2단 검증**으로 분리한다:

**(α) ai-framework 소스 직접 파싱 검증** (R-2 형식 정합성 + R-3 매칭 가능성 사전 검증):

```bash
# 1) JSON 파싱 무결성
node -e "JSON.parse(require('fs').readFileSync('opal/core/references/community-skills-registry.json'))" && echo "OK: parse"

# 2) 등록 항목 존재 + 트리거 매칭 시뮬레이션 (Node 인라인)
node -e "
const r = JSON.parse(require('fs').readFileSync('opal/core/references/community-skills-registry.json'));
const item = r.groups.anthropics.find(s => s.name === 'anthropics/system-architecture-html');
if (!item) { console.error('FAIL: item not found'); process.exit(1); }
if (item.alias !== 'html-sa') { console.error('FAIL: alias != html-sa'); process.exit(1); }
if (!item.triggers || item.triggers.length < 4) { console.error('FAIL: triggers < 4'); process.exit(1); }
const tests = ['html-sa', 'system-architecture-html', '시스템 아키텍처 HTML로 만들어줘', 'architecture diagram HTML'];
for (const t of tests) {
  const matched = item.triggers.some(p => {
    let pat = p, flags = '';
    if (pat.startsWith('(?i)')) { flags='i'; pat = pat.slice(4); }
    return new RegExp(pat, flags).test(t);
  });
  if (!matched) { console.error('FAIL: no trigger matched:', t); process.exit(1); }
}
console.log('OK: ai-framework registry — alias + triggers + 4 tests pass');
"
```

**(β) skill-registry.js validate (현재 ~/.opal/ 기준)**:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js validate
# 기대: errors = [] (warnings에 path 미존재가 나올 수 있음 — system-architecture-html은 아직 ~/.opal/community-skills/에 배포되지 않으므로 warning은 허용. R-2 AC는 "validate Pass"이므로 errors=[]만 확인).
```

> R-3 AC가 명시한 `node ... match "//html-sa"` 호출은 `~/.opal/`이 본 태스크 범위에서 갱신되지 않으므로 `found: false`가 정상이다. R-3 AC 본문도 "(배포 메커니즘 확인 후 호출 형식 PLAN에서 결정)"로 유연성을 둠. 따라서 본 PLAN에서 검증 명령은 (α) ai-framework 소스 직접 파싱을 R-3의 정식 검증으로 채택하고, skill-registry.js 매칭은 배포 후 후속 태스크에서 수행한다고 명시.

[MUST] `~/.opal/references/harness/citation-rules.md` §2.4 + `D-6`: "`~/.opal/` 배포 파일 직접 편집 금지." — 본 태스크에서 검증을 위해 `~/.opal/community-skills-registry.json`을 임시 수정하는 우회는 금지된다.

근거: (→ D-5 34-42 + D-9 R-3 AC + D-9 R-7).

---

## 3. 실행 체크리스트

> 총 7개 Step | Phase 7개 (모두 순차)
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | 스킬 이전이 모든 후속의 전제 |
> | 2 | 2 | 순차 | 새 paths 기반 등록 |
> | 3 | 3 | 순차 | (α) 직접 파싱 + (β) validate 분리 검증 |
> | 4 | 4 | 순차 | M-2 적용 전 — 원본 기준선 |
> | 5 | 5 | 순차 | A 완료 후 SKILL.md 수정 |
> | 6 | 6 | 순차 | M-2 적용 후 B 산출 |
> | 7 | 7 | 순차 | 최종 점검 — `~/.opal/` 무수정 검증 |

### Step 1: 스킬 디렉토리 이전 (R-1)

- [x] 완료
- **파일**: `skills/system-architecture-html/` → `community-skills/anthropics/system-architecture-html/`
- **작업 내용**:
  1. `mkdir -p community-skills/anthropics/system-architecture-html/references`
  2. `git mv skills/system-architecture-html/SKILL.md community-skills/anthropics/system-architecture-html/SKILL.md`
  3. `git mv skills/system-architecture-html/references/{template.html,design-system.md,copywriting.md,examples.md} community-skills/anthropics/system-architecture-html/references/`
  4. `rmdir skills/system-architecture-html/references skills/system-architecture-html` (빈 디렉토리 정리)
  5. `git mv` 사용 시 git이 rename을 자동 추적 — 별도 add 불필요. `mv` 사용 시 add 필요.
- **완료 기준**:
  - `skills/system-architecture-html/` 부재 (`ls skills/system-architecture-html` → No such file)
  - `community-skills/anthropics/system-architecture-html/SKILL.md` 존재
  - `references/` 4개 파일 모두 존재 (`ls community-skills/anthropics/system-architecture-html/references | wc -l` = 4)
  - 파일 내용 무변경 (체크섬 기준): `shasum -a 256 community-skills/anthropics/system-architecture-html/SKILL.md` 결과를 이전 전 `skills/system-architecture-html/SKILL.md` 체크섬과 비교 (이전 작업 시작 시 기록 후 비교)
- **테스트**: `find community-skills/anthropics/system-architecture-html -type f | wc -l` → `5` (SKILL.md 1 + references 4)
- **의존**: 없음
- **agent**: opal-task-agent

### Step 2: 레지스트리 등록 (R-2)

- [x] 완료
- **파일**: `opal/core/references/community-skills-registry.json`
- **작업 내용**: `groups.anthropics` 배열의 마지막 항목(`anthropics/template`) 뒤에 §2.4 M-1의 객체 1건 추가. JSON 들여쓰기와 따옴표 패턴은 기존 18개 항목과 통일 (한 줄 객체 형식).
- **완료 기준**:
  - `node -e "JSON.parse(require('fs').readFileSync('opal/core/references/community-skills-registry.json'))"` 성공
  - `groups.anthropics` 배열 길이 = 19 (기존 18 + 신규 1)
  - 신규 항목 `name = "anthropics/system-architecture-html"`, `alias = "html-sa"`, `triggers.length >= 4`, `paths` 1개
  - 기존 18개 항목 무수정 (diff에 추가만 표시되어야 함)
- **테스트**: §2.4 R-3 검증 (α)의 인라인 Node 스크립트 실행 — 출력에 `OK: ai-framework registry — alias + triggers + 4 tests pass` 포함
- **의존**: Step 1 (paths가 새 위치를 가리키도록 — 단, paths는 `~/.opal/...`이므로 Step 1 결과와 직접 의존은 없으나, 시점 일관성을 위해 순차 유지)
- **agent**: opal-task-agent

### Step 3: 등록 검증 — 2단 분리 (R-3)

- [x] 완료
- **파일**: (검증 — 파일 변경 없음)
- **작업 내용**:
  1. (α) ai-framework 소스 직접 파싱 — §2.4 "R-3 검증 명령" (α) 블록의 Node 인라인 스크립트 실행 (cwd = ai-framework 루트)
  2. (β) `node ~/.opal/tools/skill-registry/skill-registry.js validate` 실행 후 출력 JSON의 `valid` 필드 확인
- **완료 기준**:
  - (α) `OK: parse` + `OK: ai-framework registry — alias + triggers + 4 tests pass` 모두 출력
  - (β) JSON 출력의 `valid: true` (warnings는 허용 — `system-architecture-html: no SKILL.md found at any path` warning은 ~/.opal/ 배포 전이므로 정상)
  - 두 검증 모두 비-Pass 시 Step 2로 롤백 후 JSON 형식 재점검
- **테스트**: 두 명령의 stdout/stderr 캡처를 EXECUTE 보고에 포함
- **의존**: Step 2
- **agent**: opal-task-agent

### Step 4: A 산출 — 원본 스킬 기반 1차 HTML (R-4)

- [x] 완료
- **파일**: `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` (신규)
- **작업 내용**:
  1. `mkdir -p tasks/135-260507-opp-system-arch-html-skill-port/outputs`
  2. **이전된 원본** SKILL.md (`community-skills/anthropics/system-architecture-html/SKILL.md`)를 그대로 따른다 — M-2 적용 전. §1 Interview는 §2.1 분석 결과로 자동 충족(추가 인터뷰 없음).
  3. `references/template.html`을 시작점으로 §2.1 분석 결과(시스템 명칭/레이어 6/노드/색상/배지/로드맵)를 채운다.
  4. `references/design-system.md` + `copywriting.md`를 따라 카피 톤 유지.
  5. **출력 경로 강제 주입**: 원본 §3의 `/mnt/user-data/outputs/...` → `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html`로 치환. `present_files` 호출 생략 (Write로 직접 저장).
- **완료 기준**:
  - 파일 존재 + 크기 > 8KB
  - HTML 파싱 무결성: `<!DOCTYPE html>` 시작, `</html>` 종료
  - 외부 의존: `<link>` 태그가 Google Fonts (`fonts.googleapis.com`)만 참조
  - 6개 레이어 모두 표현됨 (`grep -c 'class="layer"' A_original.html` ≥ 6 또는 동등 셀렉터)
  - §2.1 노드 명칭이 모두 포함됨 (예: `Claude Code`, `opal-pilot-project`, `state-tool`, `.opal/MEMORY.md` 등 키워드 검색)
  - MVP/LATER/DONE 배지 클래스 존재
- **테스트**: 브라우저로 `file://` 직접 열기 — 콘솔 에러 없음, 6개 레이어 시각적 확인. (검증은 캡틴 비교 검토 단계에서 함께 진행)
- **의존**: Step 1 (이전 완료 후 원본 SKILL.md를 새 경로에서 Read)
- **agent**: opal-task-agent

### Step 5: SKILL.md OPAL 호환 수정 (R-5)

- [x] 완료
- **파일**: `community-skills/anthropics/system-architecture-html/SKILL.md`
- **작업 내용**: §2.4 M-2의 5종 변경 a~e 적용 (Edit 도구 사용 — 원본 보존이 필요한 섹션은 무수정)
  - (a) `## Process` §3 (원래 "Save and present") 본문의 `/mnt/user-data/outputs/...` → 환경 감지 결과 기반 표
  - (b) `Use present_files to surface it to the user` 줄 제거 + 1줄 안내 형식 명시
  - (c) `# System Architecture HTML` 직후 `## 0. 호출 환경` 섹션 신설
  - (d) `## Process` 안에 `### 1. 환경 감지` + `### 2. 컨텍스트 흡수` 신설 — 기존 1/2/3 → 3/4/5로 번호 재정렬
  - (e) frontmatter `description` 한국어 + 영어 트리거 키워드 명시 (description 필드를 multi-line `|`로 변경)
- **완료 기준**:
  - SKILL.md frontmatter 유효 (YAML 파싱 가능): `python3 -c "import yaml; yaml.safe_load(open('community-skills/anthropics/system-architecture-html/SKILL.md').read().split('---')[1])"` 성공
  - frontmatter `name = "system-architecture-html"` 유지 (이전 후에도 무변경 — D-9 §제약 조건)
  - 본문에 `/mnt/user-data/outputs` 문자열 0회 (`grep -c '/mnt/user-data' SKILL.md` = 0)
  - 본문에 `present_files` 문자열 0회
  - 본문에 `## 0. 호출 환경` 헤더 1회 + 표 4행
  - 본문에 `### 1. 환경 감지` + `### 2. 컨텍스트 흡수` 헤더 각 1회 + 각 표 존재
  - description에 "시스템 아키텍처 HTML" 문자열 1회 이상
- **테스트**:
  - `grep -c '## 0. 호출 환경' SKILL.md` = 1
  - `grep -c '### 1. 환경 감지' SKILL.md` = 1
  - `grep -c '### 2. 컨텍스트 흡수' SKILL.md` = 1
  - `grep -c '/mnt/user-data' SKILL.md` = 0
  - `grep -c 'present_files' SKILL.md` = 0
  - `grep -c '시스템 아키텍처 HTML' SKILL.md` ≥ 1
- **의존**: Step 4 (A 산출이 원본 기반이므로 Step 5보다 **반드시 늦게** 적용)
- **agent**: opal-task-agent

### Step 6: B 산출 — 수정 스킬 기반 2차 HTML (R-6)

- [x] 완료
- **파일**: `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` (신규)
- **작업 내용**:
  1. 수정된 SKILL.md (`community-skills/anthropics/system-architecture-html/SKILL.md`)를 따라 새로 생성.
  2. §2.1 분석 결과를 입력으로 그대로 사용 (A와 동일 텍스트). 노드 명칭·배지·tech chips는 A와 일치해야 한다.
  3. 환경 감지 흔적 반영(§2.4 N-7) — (i)/(ii)/(iii) 중 1가지 이상 적용.
  4. 저장 경로는 수정된 SKILL.md §1 Step 1 환경 감지 결과(태스크 폴더 → `outputs/`)로 자동 결정 → `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html`.
- **완료 기준**:
  - 파일 존재 + 크기 > 8KB
  - HTML 파싱 무결성 + Google Fonts만 외부 참조
  - 6개 레이어 + 노드 명칭이 A_original.html과 일치 (diff로 노드 명칭 셋 비교)
  - 환경 감지 흔적 1가지 이상 visible (메타 패널 또는 푸터 또는 노드 description)
  - `grep -c 'system-architecture-html\|//html-sa\|context absorbed' B_opal_revised.html` ≥ 1
- **테스트**: 브라우저로 `file://` 직접 열기 — A와 디자인 일관성 + 환경 감지 흔적 가시 확인
- **의존**: Step 5
- **agent**: opal-task-agent

### Step 7: 최종 점검 (R-7)

- [x] 완료
- **파일**: (검증 — 파일 변경 없음)
- **작업 내용**:
  1. **`~/.opal/` 무수정 검증**: 본 태스크 시작 시점(STATE.md `started_at` 또는 Step 1 직전 시각)을 기준으로 `find ~/.opal -newer <마커파일> -type f -not -path '*/node_modules/*' -not -path '*.git*' 2>/dev/null` 실행 → 결과가 비어있어야 함. 마커 파일이 없으면 본 태스크 폴더의 `STATE.md` 시각을 기준으로 한다.
  2. **changed_files 정리**: `git status --short` 출력을 캡처하여 변경 파일 목록 확인. 예상 항목:
     - `R skills/system-architecture-html/SKILL.md -> community-skills/anthropics/system-architecture-html/SKILL.md`
     - `R skills/system-architecture-html/references/{4개} -> community-skills/anthropics/system-architecture-html/references/{4개}`
     - `M opal/core/references/community-skills-registry.json`
     - `M community-skills/anthropics/system-architecture-html/SKILL.md` (Step 5 수정)
     - `?? tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html`
     - `?? tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html`
  3. **AC 매트릭스 확인**: §4 QA 체크리스트 R-1~R-7 모든 항목이 통과하는지 점검.
- **완료 기준**:
  - `find ~/.opal -newer ...` 결과 비어있음 (R-7 AC)
  - changed_files에 `~/.opal/` 경로 0건
  - QA 체크리스트 R-1~R-7 모두 ✅
- **테스트**: 본 PLAN §4 QA 체크리스트의 각 항목을 순회하며 실제 검증 명령 실행 + 캡처
- **의존**: Step 6
- **agent**: opal-task-agent

---

## 4. QA 체크리스트

### 기능 테스트 (TASK.md R-1~R-7 대응)

#### R-1 (스킬 이전) [Override: community-skills/anthropics/ → skills/]

- [x] `community-skills/anthropics/system-architecture-html/` 디렉토리 부재 (Override 결과: 존재하지 않음 확인)
- [x] `skills/system-architecture-html/SKILL.md` 존재 (Override 목표 위치)
- [x] `skills/system-architecture-html/references/` 안에 4개 파일(`template.html`, `design-system.md`, `copywriting.md`, `examples.md`) 모두 존재
- [x] 이전 전후 파일 체크섬 일치 (shasum 비교 — 5개 파일 모두 일치 확인)

#### R-2 (레지스트리 등록) [Override: opal-skills-registry.json standalone 그룹]

- [x] `opal-skills-registry.json` JSON 파싱 성공 (python3 alpha-pass)
- [x] `groups.standalone` 배열에 `name = "system-architecture-html"` 항목 정확히 1건 존재 (7→8)
- [x] 해당 항목 `alias = "html-sa"`
- [x] 해당 항목 `triggers.length >= 4` + 4개 패턴 모두 유효
- [x] 해당 항목 `paths` = `["{project}/.opal/skills/system-architecture-html/SKILL.md"]`
- [x] 기존 7개 standalone 항목 무수정

#### R-3 (등록 검증)

- [x] (α) opal-skills-registry.json 직접 파싱 — alpha-pass 출력 확인
- [x] (β) `skill-registry.js validate` — `valid: true`, `errors: []` 확인 (β) match "//html-sa" → `found: false` — ~/.opal/ 동기화 전이므로 정상

#### R-4 (1차 산출 — 원본 스킬)

- [x] `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` 존재 (24421 bytes)
- [x] 단일 파일 + 외부 의존: Google Fonts만 (fonts.googleapis.com / fonts.gstatic.com)
- [x] 6개 레이어 모두 표현됨 (`layer layer-l` 6건) + 노드 명칭 존재 확인
- [ ] 브라우저 렌더링 정상 (캡틴 직접 확인 — interactive 모드)

#### R-5 (스킬 OPAL 호환 수정) [Override: skills/system-architecture-html/SKILL.md]

- [x] (a) `/mnt/user-data` 0건 확인
- [x] (b) `present_files` 0건 확인
- [x] (c) `## 0. 호출 환경` 섹션 존재 + `//html-sa` 명시 + 호출 가능 모드 표
- [x] (d) `### 1. 환경 감지` + `### 2. 컨텍스트 흡수` 섹션 존재
- [x] (e) frontmatter description에 "시스템 아키텍처 HTML" + "아키텍처 다이어그램 HTML" 한국어 키워드 명시 (2건)
- [x] frontmatter `name = "system-architecture-html"` 유지 확인

#### R-6 (2차 산출 — 수정 스킬)

- [x] `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` 존재 (25996 bytes)
- [x] 단일 파일 + 외부 의존 Google Fonts만
- [x] R-4와 동일 입력(§2.1 분석) 사용 — 노드 명칭 동일
- [x] 환경 감지 흔적 visible (ctx-banner + 메타 CTX 행 + 푸터 OPAL 스킬 표기 + chip-ctx 마킹 — 3가지 이상)
- [ ] 브라우저 렌더링 정상 (캡틴 직접 확인 — interactive 모드)

#### R-7 (메모리 규칙 준수)

- [x] `find ~/.opal -newer state.json -type f` 결과 0건 확인
- [x] `git status --short`에 `~/.opal/...` 경로 0건 확인
- [x] 모든 Edit/Write 호출이 ai-framework 경로만 사용

### 일관성 테스트

- [x] SKILL.md frontmatter `name = "system-architecture-html"` + 레지스트리 항목 `name = "system-architecture-html"` 일치 (Override 후 standalone 형식)
- [x] 레지스트리 항목 `paths = ["{project}/.opal/skills/system-architecture-html/SKILL.md"]` — standalone 다른 7개 항목 패턴과 동일
- [x] A_original.html과 B_opal_revised.html의 §2.1 노드 명칭 셋 일치 (동일 입력 사용)
- [x] 기존 standalone 항목 7개 무수정

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 (PLAN.md 본문)
- [x] kebab-case 파일/폴더 네이밍 (`skills/system-architecture-html/`)
- [x] YAML frontmatter 유효 (수정 후 SKILL.md — frontmatter 파싱 확인)
- [x] §1 참조 문서 테이블 D-1~D-10 모두 유형/경로/참조 이유 컬럼 채워짐
- [x] §2 핵심 설계 인라인 인용 존재
- [x] [MUST] R-7 메모리 규칙 준수 확인

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | skill-registry.js가 ai-framework 소스를 직접 못 읽음 (`D-5` 34-42) | R-3 AC가 명시한 `match "//html-sa"` 명령이 본 태스크 범위 내에서 `found: false` 반환 → 검증 실패 인상 | §2.4 R-3 검증을 (α) ai-framework 직접 파싱 + (β) validate로 분리. R-3 AC 본문이 "(배포 메커니즘 확인 후 호출 형식 PLAN에서 결정)"로 유연성을 두므로 본 PLAN의 분리 검증을 정식 검증으로 채택. 배포 후 매칭 검증은 후속 태스크로 분리 |
| R-T2 | 원본 SKILL.md의 `/mnt/user-data/outputs/` 강제 사용 | A 산출(Step 4)이 원본을 그대로 따르면 저장 실패 | Step 4 작업 내용 #5에서 "출력 경로만 강제 주입" 규칙 명시. `present_files`도 동일하게 회피 (§2.4 N-6) |
| R-T3 | A/B 입력 동일성 보장 실패 | 두 회차의 노드 셋이 달라 비교 검토 무효 | §2.1 분석 결과를 PLAN에 사전 확정하여 두 회차 모두 동일 입력 사용 강제. Step 6 완료 기준에 "노드 명칭 셋 일치" 검증 포함 |
| R-T4 | `~/.opal/` 임시 동기화 유혹 | R-7 AC 위반 + 메모리 규칙 위반 | §2.4 R-3 검증 명령에 [MUST] D-6 인용으로 차단. Step 7에서 `find ~/.opal -newer` 실측 |
| R-T5 | `git mv` vs `mv` 선택 (Step 1) | `mv` 사용 시 git이 rename으로 인식 안 해 변경 폭이 크게 보임 | EXECUTE 워커가 `git mv` 우선 사용. cwd가 git 워크트리 내부임은 본 PLAN 단계 `gitStatus`로 확인됨 |
| R-T6 | 이전 후 references 파일 내용 손상 | R-1 AC 위반 (체크섬 일치 요구) | Step 1 작업 내용 #2-3에서 이동 직전 5개 파일의 shasum을 기록하고, 이동 직후 새 경로 5개 파일 shasum과 비교. 불일치 시 즉시 롤백 |
| R-T7 | 캡틴 비교 검토 난이도 (interactive 모드) | A/B 두 HTML이 너무 비슷하면 차이가 안 보임 | Step 6 작업 내용 #3에서 환경 감지 흔적을 visible 1가지 이상 강제 (§2.4 N-7 (i)(ii)(iii) 중 택). 두 산출물 파일명도 `A_original` / `B_opal_revised`로 명확히 구분 |
| R-T8 | 영역 간 용어 불일치 (citation-rules §7) | 본 태스크는 단일 영역(공통/Framework)이므로 FE↔BE/ERD↔코드 등 영역 쌍 없음 | 검출 대상 없음 — `decision_required` 페이로드 비어 있음 (`citation-rules.md` §7.5는 결정성 이슈 발생 시만 적용) |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-07 | 초기 작성 — TASK 135 R-1~R-7 대응. §2.1 ai-framework 6레이어 18노드 분석 확정. R-3 검증 (α)+(β) 분리 결정 (skill-registry.js D-5 분석 반영) |
