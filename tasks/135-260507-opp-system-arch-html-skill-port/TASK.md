# TASK: system-architecture-html 스킬 OPAL 통합 + 트윈 빌드 비교

> 작성일: 2026-05-07 | 작업 유형: 신규+개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 — "system-architecture-html 추가 검증 + 커뮤니티 스킬 이용 프로젝트 아키텍처 HTML 생성 + 내가 만든 스킬 수정 비교"
> 출력: TASK.md

## 작업 목표

사용자가 추가한 `skills/system-architecture-html/` 스킬을 OPAL 커뮤니티 스킬로 정식 등록(alias `html-sa`)하고, **원본 그대로의 스킬로 1차 HTML**과 **OPAL 호환 수정 스킬로 2차 HTML**을 동일 프로젝트(ai-framework)에 대해 산출하여 사용자가 직접 비교 검토할 수 있도록 두 산출물을 제공한다.

## 배경

캡틴이 외부 출처(Anthropic Claude.ai 공식 Skills 형식)에서 가져온 `system-architecture-html` 스킬을 `skills/`에 추가했지만, 다음 이유로 현재 OPAL 시스템에서 호출 불가능한 상태다:

- 스킬 레지스트리(`opal/core/references/opal-skills-registry.json`, `community-skills-registry.json`) 미등록
- alias `html-sa` 부여 안 됨, 트리거 패턴 없음
- 출력 경로(`/mnt/user-data/outputs/...`)와 `present_files` 도구 호출이 Claude.ai 가상 환경 전용이라 Claude Code 로컬에서 동작 불가
- "프로젝트 자동 스캔 → 아키텍처 추출" 흐름 부재 (`html-mockup`이 가진 §0 호출 환경 / Step 1 환경 감지 / Step 2 컨텍스트 흡수 패턴 없음)

원본 스킬의 결과물 품질이 어느 정도인지, OPAL 호환 수정으로 어떤 차이가 발생하는지 비교 검토하기 위해 동일 프로젝트(ai-framework) 입력으로 두 버전을 모두 산출한다.

## 배경 분석 (대화에서 도출)

세션 초반 진단 결과:

| 항목 | 현재 상태 | 표준 |
|------|---------|------|
| 위치 | `skills/system-architecture-html/` (OPAL 자체 스킬 폴더) | `community-skills/anthropics/system-architecture-html/` (외부 출처) |
| 레지스트리 등록 | ❌ 미등록 | `community-skills-registry.json` `groups.anthropics`에 항목 추가 필요 |
| alias | 없음 | `html-sa` |
| 트리거 패턴 | 없음 (description의 키워드만 존재) | `^html-sa$`, `^system-architecture-html$`, 한국어 정규식 |
| 출력 경로 | `/mnt/user-data/outputs/<name>_architecture.html` | cwd 기반 또는 태스크 폴더 산출물 경로 |
| 발표 도구 | `present_files` (Claude.ai 전용) | 일반 파일 저장 + 경로 안내 |
| 환경 감지 | 없음 | `html-mockup` 패턴(§0/§1/§2) 차용 |

매칭 테스트 결과: `node ~/.opal/tools/skill-registry/skill-registry.js match "html-sa 호출"` → `{found: false}` 확인.

## 확정된 설계 방향 (대화에서 합의)

> **2026-05-08 결정 변경 (캡틴 지시)**: 본 절의 §1·§2를 아래 Override가 대체한다 (이전 합의는 PLAN.md `🚨 결정 변경` 박스 §변경 매트릭스에 보존).
>
> **Override §1 (스킬 위치)**: `skills/system-architecture-html/` (standalone 그룹). 캡틴 수동으로 community-skills/anthropics/에 위치한 폴더를 standalone 위치로 되돌린다. 사유: "OPAL pilot과 무관한 일반 스킬"로 만들고 다른 일반 도구 스킬(html-mockup, ui-designer, erd-modeler 등)과 동일 카테고리·관리 패턴 적용.
>
> **Override §2 (레지스트리 등록 위치)**: `opal/core/references/opal-skills-registry.json` `groups.standalone` 배열에 추가. 등록 항목 name=`system-architecture-html`, paths=`["{project}/.opal/skills/system-architecture-html/SKILL.md"]` (standalone 다른 7개 항목과 동일 형식).

1. **스킬 위치**: `skills/system-architecture-html/` → `community-skills/anthropics/system-architecture-html/`로 이전 (외부 출처 = 커뮤니티 스킬 표준). ~~[Override됨]~~
2. **레지스트리 등록 위치**: `opal/core/references/community-skills-registry.json`의 `groups.anthropics` 배열에 추가. ~~[Override됨]~~
3. **alias**: `html-sa`.
4. **트윈 빌드 절차**:
   - 1차(원본): 이전 직후의 스킬 그대로 실행 → `outputs/A_original.html`
   - 2차(OPAL 호환): SKILL.md를 OPAL 호환으로 수정 → `outputs/B_opal_revised.html`
5. **비교 검토**: 사용자가 직접 수행 (별도 비교 보고서 산출 불필요).
6. **수정 범위(OPAL 호환)**:
   - 출력 경로 → 태스크 폴더 또는 cwd 기반으로 변경
   - `present_files` 호출 제거 → 파일 저장 + 경로 안내로 대체
   - §0 "호출 환경" 섹션 추가 (`//html-sa` 명시, 모드 무관 호출 가능 여부 명시)
   - Step 1 "환경 감지" / Step 2 "컨텍스트 흡수" 추가 (대화 + 프로젝트 양방향 컨텍스트 흡수)
   - 트리거 description에 한국어 정규식 패턴 보강
7. **배포(`~/.opal/`)**: 본 태스크에서는 ai-framework 소스만 갱신. `~/.opal/`로의 배포는 별도 배포 스크립트(또는 후속 태스크)로 처리. 메모리 규칙 "배포 소스 직접 수정 금지" 준수.

## 요구사항

- [x] **R-1 (스킬 위치 정착)** [Override됨 — 2026-05-08]: 무엇을 = `community-skills/anthropics/system-architecture-html/` 디렉토리 전체를 `skills/system-architecture-html/`(standalone 위치)로 되돌리기 / 어디에 = ai-framework 저장소 소스 / 왜 = OPAL pilot과 무관한 일반 도구 스킬로 정착 (다른 standalone 7개 스킬과 동일 카테고리) / **AC** = 되돌리기 후 `community-skills/anthropics/system-architecture-html/` 부재 + `skills/system-architecture-html/SKILL.md` 존재 + `references/` 4개 파일(template.html / design-system.md / copywriting.md / examples.md) 모두 보존 (체크섬/파일 수 일치) — **PLAN 명세 완료** (`PLAN.md 🚨 결정 변경 §Step 1 + §3 Step 1`), EXECUTE에서 실제 이동 및 검증
- [x] **R-2 (레지스트리 등록)** [Override됨 — 2026-05-08]: 무엇을 = `opal-skills-registry.json` `groups.standalone` 배열 끝에 항목 추가 / 어디에 = `opal/core/references/opal-skills-registry.json` / 왜 = `//html-sa` 호출 가능화 + standalone 일반 스킬로 등록 / **AC** = JSON 파싱 통과 + `groups.standalone` 배열 길이 7→8 + 항목에 `name: "system-architecture-html"`, `alias: "html-sa"`, `triggers` 배열에 최소 4개 패턴(`^html-sa$`, `^system-architecture-html$`, 한국어 "시스템\\s*아키텍처\\s*HTML" 정규식, 영어 "architecture\\s*diagram\\s*HTML" 정규식) + `paths`에 `{project}/.opal/skills/system-architecture-html/SKILL.md` 포함 (standalone 다른 7개 항목 동일 형식) — **PLAN 명세 완료** (`PLAN.md 🚨 결정 변경 §Step 2`), EXECUTE에서 실제 등록 및 검증
- [x] **R-3 (등록 검증)**: 무엇을 = 매칭 동작 확인 / 어디에 = ai-framework 레지스트리 + `~/.opal/` 배포본 / 왜 = 등록 누락 방지(확정 방향 §3) / **AC** = ai-framework 레지스트리에 대해 `node ~/.opal/tools/skill-registry/skill-registry.js --registry ./opal/core/references/community-skills-registry.json match "//html-sa"` 또는 동등 호출이 `found: true` 반환 (배포 메커니즘 확인 후 호출 형식 PLAN에서 결정) — **PLAN 명세 완료** (`PLAN.md §2.4 R-3 + §3 Step 3` / `QA-PLAN.md` §5), EXECUTE에서 실제 검증
- [x] **R-4 (1차 산출물 — 원본 스킬)**: 무엇을 = 이전 직후 원본 SKILL.md를 그대로 따라 ai-framework 프로젝트 시스템 아키텍처를 HTML로 생성 / 어디에 = `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` / 왜 = 원본 스킬 결과 비교 기준선(확정 방향 §4) / **AC** = 단일 자기완결 HTML 파일 + 브라우저에서 외부 의존(Google Fonts 외) 없이 렌더링 + ai-framework 실제 구성(`opal/`, `skills/`, `community-skills/`, `agents/`, `tasks/`, `tools` 디렉토리 + opal-pilot 오케스트레이터 / op-task 스킬 / community-skills 외부 출처 등)이 다이어그램 노드로 표현됨 — **PLAN 명세 완료** (`PLAN.md §2.1 + §2.4 N-6 + §3 Step 4` / `QA-PLAN.md` §5), EXECUTE에서 실제 생성 및 검증
- [x] **R-5 (스킬 OPAL 호환 수정)**: 무엇을 = 이전된 SKILL.md를 OPAL 호환으로 수정 / 어디에 = `community-skills/anthropics/system-architecture-html/SKILL.md` / 왜 = Claude Code 로컬 동작 + OPAL 환경 감지 패턴 적용(확정 방향 §6) / **AC** = (a) 출력 경로 `/mnt/user-data/outputs/...` 제거되고 cwd/태스크 폴더 기반으로 변경됨 + (b) `present_files` 호출 제거 + (c) §0 "호출 환경" 섹션 존재(`//html-sa` 명시) + (d) Step 1 "환경 감지" / Step 2 "컨텍스트 흡수" 절 신설(`html-mockup` SKILL.md §0~§1 패턴 차용) + (e) frontmatter `description`에 한국어 트리거 키워드("시스템 아키텍처 HTML", "아키텍처 다이어그램 HTML" 등) 명시 — **PLAN 명세 완료** (`PLAN.md §2.4 M-2 + §3 Step 5` / `QA-PLAN.md` §5), EXECUTE에서 실제 수정 및 검증
- [x] **R-6 (2차 산출물 — 수정 스킬)**: 무엇을 = 수정된 SKILL.md를 따라 동일 프로젝트(ai-framework) 시스템 아키텍처 HTML 재생성 / 어디에 = `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` / 왜 = OPAL 호환 수정 결과 비교(확정 방향 §4) / **AC** = 단일 자기완결 HTML + 브라우저 정상 렌더링 + R-4와 동일 프로젝트 입력에 대한 산출 + 수정으로 추가된 환경 감지/컨텍스트 흡수 로직이 산출 과정에 반영됨(예: ai-framework의 `docs/`, `.opal/MEMORY.md` 등을 컨텍스트로 활용한 흔적이 노드 설명/메타에 보임) — **PLAN 명세 완료** (`PLAN.md §2.4 N-7 + §3 Step 6` / `QA-PLAN.md` §5), EXECUTE에서 실제 생성 및 검증
- [x] **R-7 (메모리 규칙 준수)**: 무엇을 = 모든 변경은 ai-framework 소스에만 적용 / 어디에 = 작업 전체 / 왜 = 메모리 `feedback_deploy_boundary.md` "`~/.opal/` 배포 파일 직접 편집 금지" / **AC** = 본 태스크 내 어떤 단계에서도 `~/.opal/` 하위 파일을 직접 Edit/Write하지 않았음 (Bash `find ~/.opal -newer <task-start-marker>` 등으로 검증 가능) — **PLAN 명세 완료** (`PLAN.md §3 Step 7 + §5` / `QA-PLAN.md` §5), EXECUTE에서 실제 검증

## 제약 조건

- 메모리 `feedback_deploy_boundary.md` 준수 — `~/.opal/` 배포 파일 직접 편집 금지
- 커밋은 사용자가 명시 요청 시에만 수행 (하네스 §1 Guards)
- HTML 산출물은 외부 자산 의존 최소화 (Google Fonts 정도 허용 — 원본 스킬 표준)
- 스킬 SKILL.md frontmatter `name` 필드는 이전 후에도 `system-architecture-html` 유지 (alias만 `html-sa` 추가)
- ai-framework 레지스트리는 `opal/core/references/community-skills-registry.json`이 SSOT — `~/.opal/references/` 동기화는 본 태스크 범위 외(별도 배포 절차)

## 기술 스택

- 본 태스크는 코드 빌드/실행을 수반하지 않는 문서·스킬·산출물 작업 (opp 도메인)
- 산출물은 정적 HTML (외부 의존: Google Fonts만 허용)
- 검증 도구: `node ~/.opal/tools/skill-registry/skill-registry.js`, `~/.opal/tools/state-tool/run.sh`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | system-architecture-html 원본 SKILL.md | `skills/system-architecture-html/SKILL.md` (이전 후 `community-skills/anthropics/...`) | 1차 산출 기준 + 수정 출발점 |
| D-2 | 소스 | html-mockup SKILL.md | `skills/html-mockup/SKILL.md` | OPAL 호환 §0 호출 환경 / Step 1 환경 감지 / Step 2 컨텍스트 흡수 패턴 차용 |
| D-3 | 설계 | 커뮤니티 스킬 레지스트리 | `opal/core/references/community-skills-registry.json` | R-2 등록 대상 SSOT |
| D-4 | 설계 | OPAL 스킬 레지스트리 도구 | `~/.opal/tools/skill-registry/skill-registry.js` | R-3 등록 검증 도구 |
| D-5 | 설계 | OPAL Pilot 표준 | `~/.opal/references/opal-pm.md`, `opal-harness.md`, `opal-harness-interactive.md` | opp 파이프라인 + Gates |
| D-6 | 설계 | TASK 공통 프로세스 | `~/.opal/references/harness/task-process.md` | TASK.md 형식 + 채번 + state init |
| D-7 | 기획 | 프로젝트 메모리 | `.opal/MEMORY.md`, `memory/feedback_deploy_boundary.md` | 배포 소스 직접 수정 금지 규칙 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
