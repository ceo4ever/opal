# PLAN: html-mockup 일반 스킬 신규 개발

> 작성일: 2026-04-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PROJECT.md | `docs/PROJECT.md` | 폴더 구조맵 §폴더 구조맵 + 네이밍 규칙 §네이밍 규칙 — `skills/` 위치 + kebab-case 근거 |
| D-2 | 설계 | skill-commands.md | `~/.opal/references/harness/skill-commands.md` | `//` 호출 인프라 + 레지스트리 매칭 절차 |
| D-3 | 소스 | op-task SKILL.md | `~/.opal/skills/op-task/SKILL.md` | interview 스킬 연동 패턴 + 탐색 경로 (M-3 결정 근거) |
| D-4 | 설계 | AGENT.md (프로젝트 PM) | `.opal/AGENT.md` | PM 검토 기준 + 금지사항 (배포 행위 금지, ~/.opal/ 직접 수정 금지) |
| D-5 | 외부 | DaisyUI | [DaisyUI](https://daisyui.com/) | 컴포넌트 클래스 라이브러리 (토큰 절약) |
| D-6 | 외부 | Alpine.js | [Alpine.js](https://alpinejs.dev/) | 선언적 인터랙션 |
| D-7 | 외부 | Lucide | [Lucide](https://lucide.dev/) | SVG 아이콘 자동 치환 |
| D-8 | 외부 | Tailwind CDN | [Tailwind CDN](https://tailwindcss.com/docs/installation/play-cdn) | 빌드 없는 유틸리티 CSS |
| D-9 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 시스템 아키텍처 — 스킬 구조 일관성 |
| D-10 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드/문서 컨벤션 |
| D-11 | 설계 | README.md | `README.md` | 프레임워크 공개 소개 — Pilot 개념 / 사용 사례 |
| D-12 | 소스 | skills.md (레지스트리 문서) | `~/.opal/references/skills.md` | 레지스트리 SSOT 명시 + 폴백 데이터 소스 (M-1 조사) |
| D-13 | 소스 | interview SKILL.md | `~/.opal/skills/interview/SKILL.md` | 인터뷰 스킬 표준 인터페이스 (M-3 결정 근거) |
| D-14 | 소스 | install-mac.sh | `scripts/install-mac.sh` | skills/ 배포 패턴 (M-2 조사) |
| D-15 | 소스 | skill-registry.js | `~/.opal/tools/skill-registry/skill-registry.js` | 매칭 알고리즘 + 그룹 평탄화 (M-1 조사) |
| D-16 | 외부 | Pretendard | [Pretendard](https://github.com/orioncactus/pretendard) | 한글 폰트 CDN |
| D-17 | 소스 | opal-skills-registry.json | `opal/core/references/opal-skills-registry.json` | 레지스트리 SSOT (편집 대상, M-1 결론) |
| D-18 | 소스 | api-analyzer SKILL.md | `skills/api-analyzer/SKILL.md` | 표준 standalone 스킬 패턴 (단일 SKILL.md형) |
| D-19 | 소스 | erd-modeler 디렉토리 | `skills/erd-modeler/` | references/ 보조 패턴 (M-4 참고) |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `skills/html-mockup/SKILL.md` | 본 스킬 정의 (신규) | 신규 생성 | 신규 |
| `skills/html-mockup/templates/boilerplate.html` | HTML 보일러플레이트 시드 (신규) | 신규 생성 | 신규 |
| `skills/html-mockup/templates/shared/style.css` | 공통 CSS 시드 (신규) | 신규 생성 | 신규 |
| `skills/html-mockup/templates/shared/main.js` | 공통 JS 시드 (신규) | 신규 생성 | 신규 |
| `skills/html-mockup/templates/index.html.tmpl` | 인덱스 페이지 시드 (신규) | 신규 생성 | 신규 |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 (SSOT) | 수정 — `groups.standalone` 배열에 항목 추가 | `opal/core/references/opal-skills-registry.json:212-255` |
| `scripts/install-mac.sh` | 배포 스크립트 | 변경 불필요 | `scripts/install-mac.sh:438-441` (`install_dir "$FRAMEWORK_ROOT/skills" ...` 일괄 복사) |
| `~/.opal/skills/interview/SKILL.md` | interview 스킬 (재사용 대상) | 변경 없음 (참조만) | `~/.opal/skills/interview/SKILL.md:1-7` |

> 근거: `파일:N-M` 포맷. 변경 없는 파일은 본 PLAN의 가정이 정확한지 검증하기 위한 참조 자원.

### 현재 상태

- **skills/ 디렉토리**: 이미 6개의 standalone 스킬 존재 — `api-analyzer/`, `erd-modeler/`, `interview/`, `ui-designer/`, `web-to-markdown/`, `wireframe-builder/`. `html-mockup/`은 없음.
- **레지스트리 SSOT**: `opal/core/references/opal-skills-registry.json`이 `groups.standalone` 배열을 사용하여 매 standalone 스킬을 등록한다 (`opal/core/references/opal-skills-registry.json:212-255`). 각 항목 형식: `{name, alias, description, triggers[], paths[]}`. `~/.opal/references/skills.md`는 **사람이 읽는 보조 문서**(기술 스택별 추천 매핑)이며 매칭 데이터 소스 아님. (→ D-12, D-15, D-17)
- **배포 스크립트**: `install-mac.sh`는 `install_dir "$FRAMEWORK_ROOT/skills" "$opal_home/skills" "독립 스킬"` 한 줄로 `skills/` 디렉토리 전체를 일괄 복사한다 (`scripts/install-mac.sh:440-441`). 이후 `strip_deploy_md_recursive`로 변경이력 strip. 새 스킬 추가 시 스크립트 변경 없이 자동 배포된다. (→ D-14)
- **interview 스킬**: 표준 인터페이스 — AskUserQuestion 사용, 한 라운드 3~4문 묶음, 2~3라운드 이내 종결 (`~/.opal/skills/interview/SKILL.md:14-19`). op-task가 STEP 2에서 동일한 탐색 경로 우선순위로 호출한다 (`~/.opal/skills/op-task/SKILL.md:36-39`). (→ D-3, D-13)
- **standalone 스킬 구조 패턴**: 단일 SKILL.md형(`api-analyzer/`, `interview/`, `web-to-markdown/`, `wireframe-builder/`) + 보조 파일형(`erd-modeler/references/*.md`, `ui-designer/modes/*.md`). 본 태스크의 보일러플레이트·shared 시드는 **저장 시 `cp` 대상이 되는 정적 자산**이므로 `templates/` 분리가 적합하다. (→ D-18, D-19)
- **레지스트리 매칭**: `matchByAlias`(name 또는 alias 정확 일치) → `matchByTriggers`(정규식 매칭) 순서. 별칭 호출 `//mockup`은 `alias: "mockup"` 한 필드로 충족된다 (`skill-registry.js:67-73`). (→ D-15)

### 영향 범위

- **신규 스킬 추가만 필요** — 기존 스킬·하네스·오케스트레이터에 영향 없음.
- **레지스트리 한 항목 추가** — JSON 파일 한 곳(`opal-skills-registry.json` standalone 배열 끝). 다른 스킬과 충돌 없음 (이름/별칭 유일).
- **배포 스크립트 변경 불필요** — 일괄 복사 패턴(M-2 결론).
- **install-mac.sh 동기화 검증** — 다음 배포 시 `~/.opal/skills/html-mockup/`이 자동 생성되는지 캡틴 확인 필요. 본 태스크에서는 배포하지 않음 (PM 금지사항, → D-4).
- **테스트 영향 범위**: `skill-registry.js validate`가 신규 항목의 path 존재성·triggers 정규식·alias 유일성을 검증한다.

### 기존 standalone 스킬 trigger 충돌 검증 (B-1)

기존 6개 standalone 스킬(api-analyzer, interview, wireframe-builder/wfb, ui-designer/uid, web-to-markdown/wtm, erd-modeler/erm)의 trigger와 본 스킬 trigger 패턴 비교.

**name/alias 충돌**: 없음. `html-mockup` 신규, `mockup` 별칭은 기존 alias(`wfb`/`uid`/`wtm`/`erm`/null/null) 중 어느 것과도 중복 안 됨. (→ `opal/core/references/opal-skills-registry.json:212-255` 조회 결과)

**trigger 정규식 충돌 매트릭스**:

| 본 스킬 토큰 | 기존 잠재 충돌 토큰 | 충돌 여부 | 판단 근거 |
|------------|-----------------|---------|---------|
| `^html-mockup$`, `^mockup$` | `^wireframe-builder$`/`^wfb$` 등 | **없음** | 정확 매칭 — 다른 문자열 |
| `목업` | wireframe-builder `와이어프레임`, ui-designer `UI 만들어` | **없음** | 토큰 다름 |
| `모크업` | (없음) | **없음** | - |
| `HTML\s*화면\s*만들` | wireframe-builder `화면\s*설계`, ui-designer `화면\s*구현` | **없음** | "만들" vs "설계/구현" — 의도 분기 명확 |
| `HTML\s*목업` | (없음) | **없음** | - |

**의미 영역 잠재 모호성 (R-T1 보강)**:
- "**프로토타입 만들어**" — ui-designer에 매칭. 본 스킬은 HTML 키워드 필요 — 매칭 안 됨. 사용자 의도 분기 명확.
- "**목업 만들어**" — 본 스킬에 매칭. ui-designer `프로토타입 만들어`와 도메인은 겹치나 토큰 다름. → 사용자에게는 동일 작업으로 인식될 수 있어 "목업"과 "프로토타입" 의미 차이를 SKILL.md description에 명기 필요(빠른 검토용 정적 HTML = 목업 / 풀 인터랙션 UI = 프로토타입).

**검증 결론**: 정규식·name·alias 모든 차원에서 충돌 없음. 의미 영역 모호성은 SKILL.md description에서 분기 안내로 해소.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `skills/html-mockup/SKILL.md` | 스킬 정의 (YAML frontmatter + 프로세스 + 인터뷰·산출물 규칙) | TASK §요구사항 R-1 ~ R-7, R-11 ~ R-19 |
| N-2 | `skills/html-mockup/templates/boilerplate.html` | HTML 보일러플레이트 표준 (TASK §9 인용) | TASK §요구사항 R-11 |
| N-3 | `skills/html-mockup/templates/shared/style.css` | 공통 스타일 시드 (Pretendard 폰트 매핑 + 자주 쓰는 커스텀) | TASK §확정 §4, §9 |
| N-4 | `skills/html-mockup/templates/shared/main.js` | 공통 인터랙션 시드 (Lucide 초기화, 모달 토글 등 패턴) | TASK §확정 §4 |
| N-5 | `skills/html-mockup/templates/index.html.tmpl` | 다중 화면 인덱스 페이지 보일러플레이트 (DaisyUI card/list) | TASK §요구사항 R-13 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `opal/core/references/opal-skills-registry.json` | `groups.standalone` 배열 끝에 `html-mockup` 항목 추가 — `{name, alias, description, triggers, paths}` | TASK §요구사항 R-8, R-10 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | (없음) | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 보일러플레이트 + shared 시드 + 인덱스 시드 작성 | N-2, N-3, N-4, N-5 | 낮음 (TASK §9 그대로) |
| 2 | SKILL.md 본문 작성 (프로세스·인터뷰·산출물·에러·보고 모두 포함) | N-1 | 높음 (R-1 ~ R-19 통합) |
| 3 | 레지스트리 등록 (standalone 배열에 항목 추가) | M-1 | 낮음 |
| 4 | 검증 — `skill-registry.js validate` + `match "html-mockup"` + `match "mockup"` | (검증 단계) | 낮음 |

> 의존 방향: templates(시드) → SKILL.md(시드 참조) → 레지스트리(SKILL.md 경로 등록) → 검증.

### 핵심 설계

#### M-1 ~ M-4 결정 결과 (현황 조사 결론)

- **M-1 (레지스트리 데이터 소스)**: SSOT는 `opal/core/references/opal-skills-registry.json`. `groups.standalone` 배열에 항목 한 줄 추가. `references/skills.md`는 사람이 읽는 보조 문서로 별도 수정 불필요. (→ D-12, D-15, D-17 / `opal/core/references/opal-skills-registry.json:212-255`)
- **M-2 (install-mac.sh 동기화)**: **변경 불필요**. `install-mac.sh`는 `skills/` 폴더 일괄 복사이므로 신규 디렉토리가 자동 배포된다. (→ D-14 / `scripts/install-mac.sh:440-441`)
- **M-3 (인터뷰 스킬 재사용)**: **재사용**. op-task와 동일하게 path 우선순위 `{project}/.opal/skills/interview/SKILL.md` → `~/.opal/skills/interview/SKILL.md`로 탐색하여 호출. 인라인 재구현은 중복 — 표준화·재사용성 원칙 위반(→ D-1 §프로젝트 원칙). (→ D-3 §STEP 2, D-13)
- **M-4 (templates/ 보조 파일 패턴)**: **별도 templates/ 분리**. 보일러플레이트 HTML(약 25줄), shared CSS/JS는 SKILL.md 인라인 시 토큰 낭비 + 스킬이 스킬 호출마다 동일 텍스트를 추론에 노출. 스킬은 `Read templates/boilerplate.html → Write {저장위치}/{화면}.html` 패턴으로 사용한다. (→ D-19 / `skills/erd-modeler/references/`)

> 본 4개 결정은 PLAN의 모든 후속 단계와 R-1 ~ R-19 매핑의 전제이다.

#### N-1: SKILL.md 구조 (요구사항 → 섹션 매핑)

YAML frontmatter:

```yaml
---
name: html-mockup
description: |
  **CDN 기반 정적 HTML 화면 빠른 생성 스킬**. 태스크 컨텍스트 자동 흡수 + 인터뷰로 화면 1~수개를 생성한다.
  반드시 이 스킬을 사용해야 하는 상황: "화면 만들어줘", "목업 만들어줘", "HTML로 빠르게 보여줘", 와이어프레임 검토용 정적 화면 필요 시.
  필수 입력: 저장 위치 (인터뷰). 보장 출력: HTML 화면 파일 + shared/ + 다중 시 index.html.
---
```

본문 섹션 (TASK 요구사항과의 매핑 보장):

| 섹션 | TASK 요구사항 | 핵심 내용 |
|------|-------------|----------|
| 0. 호출 환경 | R-1 | 일반 스킬, `//html-mockup` / `//mockup` 호출, 비서/태스크/PM 모드 무관 호출 가능 |
| 1. 프로세스 — Step 1 환경 감지 | R-2 | (1) cwd `.opal/AGENT.md` 존재 검사 → OPAL 프로젝트 여부, (2) `tasks/{NNN}-*/TASK.md` 매칭 → 태스크 폴더 여부, (3) STATE.md/MEMORY.md 폴백 |
| 1. 프로세스 — Step 2 컨텍스트 흡수 | R-2 | 감지 결과별 흡수 자원 표 (TASK §확정 §2 그대로 인용) |
| 1. 프로세스 — Step 3 인터뷰 | R-3, R-19 | interview 스킬 호출 (path 우선순위 표 명시) — 부족분만 묻기 + 7단계 + 추론 시 스킵 1줄 통지 |
| 1. 프로세스 — Step 4 입력 자원 | R-17 | 4종 입력 처리 (이미지/Figma/URL/텍스트) |
| 1. 프로세스 — Step 5 산출물 생성 | R-4, R-6, R-11, R-12, R-13 | 보일러플레이트 적용 + 화면명 변환 + 다중 시 index 자동 |
| 1. 프로세스 — Step 6 보고 | R-18 | 단일/다중/수정 분기 |
| 2. 산출물 구조 | R-4 | 트리 명시 + shared/ 분리 + 외부 분리 원칙 |
| 3. 기본 기술 스택 | R-5, R-14 | CDN 4종 + 핀 정책 표 + 대안 2종(Flowbite/Tailwind만) |
| 4. 보일러플레이트 | R-11 | `templates/boilerplate.html` Read → 화면 제목·본문 치환 → Write |
| 5. 파일명 규칙 | R-12 | 영문/한글/혼합 변환 + transliteration + 인터뷰 분기 |
| 6. 인덱스 페이지 | R-13 | 화면 1개 → 안 만듦 / 2개 이상 → DaisyUI card/list |
| 7. 디자인 정책 | R-15 | 반응형 ON 모바일 우선 / 다크모드 OFF 기본 |
| 8. 반복 수정 | R-7 | 같은 파일 덮어쓰기 / CHANGELOG 만들지 않음 |
| 9. 에러 처리 | R-16 | 5종 케이스 표 |

각 섹션 끝에는 인라인 인용 `(→ TASK §확정 §N)` 형식으로 합의 결정의 근거를 표기한다 (→ D-1, citation-rules.md §3.2).

#### N-1 부속 명세 (보강)

##### (a) 인터뷰 7단계 질문 템플릿 (A-1)

각 단계는 interview 스킬을 통해 AskUserQuestion 도구로 사용자에게 묻는다. **한 라운드에 3~4문씩 묶어서 호출** (interview SKILL.md §라운드 규칙 준수). 컨텍스트로 추론 가능한 단계는 묻지 않고 `"{단계}는 컨텍스트에서 {추론값}으로 자동 결정. 변경하시려면 알려주세요."` 1줄 통지로 대체.

| # | 단계 | 질문 | 옵션/형식 | 스킵 조건 |
|---|------|------|----------|---------|
| 1 | 저장 위치 | "HTML 화면을 저장할 위치는?" | multipleChoice: `["현재 태스크 폴더의 mockup/", "현재 cwd 직속 mockup/", "직접 입력"]` (태스크 폴더 감지 시 첫 옵션, 아니면 두 번째가 디폴트) | **스킵 불가 (필수)** |
| 2 | 화면 종류·개수 | "어떤 화면을 몇 개 만들까요? (예: 로그인 / 대시보드 / 설정 — 3개)" | freeText | TASK.md/PLAN.md에서 화면 식별 가능 시 스킵 |
| 3 | 핵심 액션·데이터 | "각 화면에서 보여줄 핵심 액션이나 데이터 예시가 있나요?" | freeText (선택, "없음" 허용) | 컨텍스트에서 ANALYSIS.md/PLAN.md 핵심 설계 추론 가능 시 스킵 |
| 4 | 분리 모드 | "화면 구성 방식은?" | multipleChoice: `["화면별 분리 (기본)", "단일 파일에 섹션으로 묶기"]` | 화면 1개면 자동으로 단일 파일 의미 — 스킵 |
| 5 | UI 라이브러리 | "UI 컴포넌트 라이브러리는?" | multipleChoice: `["DaisyUI (기본 추천)", "Flowbite", "없음 (Tailwind만)"]` | 사전 지시 시 스킵 |
| 6 | 다크모드 | "다크모드 토글이 필요한가요?" | multipleChoice: `["아니오 (기본)", "예 — DaisyUI 테마 토글 사용"]` | 사전 지시 시 스킵 |
| 7 | 입력 자원 | "참고할 와이어프레임 이미지·Figma URL·참고 사이트가 있나요?" | freeText (선택, "없음" 허용) | 호출 시 사전 첨부됨 → 자동 스킵 |

라운드 묶기 권장: **R1**(1~3), **R2**(4~6), **R3**(7). 컨텍스트 자동 흡수가 충분하면 R1만으로 종결 가능.

##### (b) 저장 위치 처리 흐름 (C-1)

저장 위치 결정 후 폴더 처리 의사 코드:

```
if not exists(저장위치):
    if writable(parent(저장위치)):
        mkdir -p 저장위치
    else:
        escalate("권한 없음 — 다른 위치 지정 필요")
elif not is_dir(저장위치):
    escalate("동일 이름의 파일 존재 — 다른 위치 지정 필요")
else:
    # 폴더 존재 → 안의 파일은 R-16 §9 에러 처리 분기로 위임
    use 저장위치
```

##### (c) 반복 수정 감지 로직 (C-2)

같은 호출 안에서 수정 의도 vs 신규 호출에서 동일 파일명 충돌은 다음 규칙으로 구분:

| 시나리오 | 감지 방법 | 처리 |
|---------|---------|------|
| 같은 호출 안 (한 세션 내 같은 화면 수정) | 같은 호출의 인터뷰 컨텍스트에 "수정"/"바꿔"/"고쳐" 키워드 존재 | 자동 덮어쓰기 |
| 다른 호출 (새 세션 또는 새 //html-mockup 호출) — 파일명 충돌 | 저장 위치에 이미 같은 파일명 존재 + 인터뷰 컨텍스트에 수정 키워드 없음 | AskUserQuestion으로 확인 (아래 (d) 참조) |
| `index.html` 충돌 | 다중 화면 자동 생성 시마다 항상 갱신 | 자동 덮어쓰기 (선언적 결과) |

> "수정"/"바꿔"/"고쳐"/"바꿔줘" 등 한국어 동사 + "modify"/"update"/"change"/"fix" 영어 동사를 키워드 셋으로 명시.

##### (d) 에러 케이스 AskUserQuestion 템플릿 (C-3)

R-16 §9 에러 처리 5종 케이스 중 사용자 확인이 필요한 케이스의 정확한 질문 문구:

| 케이스 | 질문 | 옵션 |
|--------|------|------|
| 다른 호출 파일명 충돌 | "`{파일명}.html`이 이미 존재합니다. 어떻게 할까요?" | `["덮어쓰기 (수정)", "다른 이름으로 저장 (입력)", "취소"]` |
| 한글 화면명 변환 확인 (A-6과 통합) | "화면명 `{한글입력}` → `{ai_제안_영문}.html`로 저장할까요?" | `["예", "직접 입력", "다른 후보 제안"]` |
| 권한 부족 | (질문 없이 즉시 에스컬레이션) | — |
| CDN 도달 불가 | (작성은 계속, 사용자에게 1줄 안내) | — |
| 저장 위치가 파일임 | "`{경로}`가 파일로 존재합니다. 다른 위치를 지정하세요." | freeText |

##### (e) 화면명 → 파일명 변환 알고리즘 (A-6 정밀화)

**알고리즘**: Hangul Romanization 발음 변환을 사용하지 **않는다**. AI가 의미 기반으로 영문 후보를 제안하고 사용자 확인.

```
input = 화면명 입력
if input ~ /^[a-zA-Z][a-zA-Z0-9 \-_]*$/:
    output = kebab-case(input)  # 예: "Login Screen" → "login-screen"
elif input has 한글:
    candidates = AI가 의미 기반으로 영문 명사 1~3개 제안
    # 예: "로그인" → ["login", "sign-in"], "대시보드" → ["dashboard"]
    if len(candidates) == 1: 자동 적용 + 1줄 통지
    else: AskUserQuestion으로 후보 선택
else (혼합/모호):
    AskUserQuestion으로 직접 입력 받기
output = lowercase + ASCII + hyphen-only  # file:// URL 호환성 (TASK §10)
```

##### (f) 단일 파일 모드 — 섹션 구분 방법 (A-7 정밀화)

단일 파일 모드 활성화 시 (인터뷰 4단계에서 명시 또는 화면 1개):

- 각 화면을 `<section id="screen-{slug}">`으로 감싼다
- 파일 상단에 sticky top nav 삽입 — DaisyUI `navbar` + `tabs-boxed` 컴포넌트 사용
- 각 탭은 `<a href="#screen-{slug}">` 앵커 링크 (페이지 내 스크롤)
- Alpine.js로 활성 탭 강조: `:class="{ 'tab-active': activeTab === '{slug}' }"`

```html
<!-- 단일 파일 모드 골격 -->
<body class="font-pretendard">
  <div class="navbar bg-base-100 sticky top-0 z-10 shadow">
    <div class="tabs tabs-boxed">
      <a href="#screen-login" class="tab">로그인</a>
      <a href="#screen-dashboard" class="tab">대시보드</a>
    </div>
  </div>
  <section id="screen-login" class="min-h-screen p-4">…</section>
  <section id="screen-dashboard" class="min-h-screen p-4">…</section>
  <script>lucide.createIcons();</script>
</body>
```

[MUST] 인용 (재해석 여지 제거):

- `` [MUST] `~/.opal/references/skills.md` §스킬 도구 사용법: "스킬 메타데이터는 JSON 레지스트리가 SSOT이다." `` — 추가 등록 시 JSON에만 추가, skills.md 본문은 변경 불필요
- `` [MUST] `.opal/AGENT.md` §확정 기준 #2: "`~/.opal/` 경로 파일을 Edit/Write하지 않는다. 수정 대상은 반드시 소스 경로에서 찾아 수정한다." `` — 본 스킬 SKILL.md에도 동일 원칙 적용 (배포는 캡틴 권한)
- `` [MUST] `.opal/AGENT.md` §금지사항: "배포 행위 금지: install-mac.sh 실행, ~/.opal/에 파일 직접 복사/생성/수정 금지" `` — html-mockup이 캡틴 명시 지시 없이 배포 행위 트리거 금지

(→ citation-rules.md §2.4 [MUST] 포맷)

#### N-2: templates/boilerplate.html

TASK §9 보일러플레이트 그대로. 스킬은 `Read templates/boilerplate.html` → 토큰 치환 → `Write {저장위치}/{화면}.html` 흐름.

`<head>` 자원 순서:

1. Pretendard CSS (한글 폰트, → D-16)
2. Tailwind CDN (latest, → D-8)
3. DaisyUI CSS (`@4`, → D-5)
4. Alpine.js JS defer (`@3`, → D-6)
5. Lucide JS (latest, → D-7)
6. `./shared/style.css`
7. `./shared/main.js` defer

`<body class="font-pretendard">` + 마지막 `<script>lucide.createIcons();</script>` (TASK §9 명시).

##### 치환 토큰 풀 셋 (A-4)

| 토큰 | 위치 | 필수/선택 | 예시 값 |
|------|------|---------|--------|
| `{{TITLE}}` | `<title>{{TITLE}}</title>` | 필수 | `로그인 — html-mockup` |
| `{{BODY}}` | `<body>` 안 마크업 영역 | 필수 | (화면별 DaisyUI 마크업 전문) |
| `{{NAV}}` | `<body>` 시작 직후 (단일 파일 모드 또는 다중 화면 시) | 선택 | sticky navbar 마크업 (단일 파일 모드 §(f) 참조) — 비어있으면 그대로 빈 문자열 |
| `{{EXTRA_HEAD}}` | `<head>` 끝 직전 | 선택 | 다크모드 ON 시 `<html data-theme="dark">` 변환 또는 화면 전용 인라인 CSS — 비어있으면 빈 문자열 |

치환 절차:

```
read_template = Read("skills/html-mockup/templates/boilerplate.html")
filled = read_template
  .replace("{{TITLE}}", title)
  .replace("{{BODY}}", body_markup)
  .replace("{{NAV}}", nav_markup or "")
  .replace("{{EXTRA_HEAD}}", extra_head or "")
Write("{저장위치}/{화면}.html", filled)
```

#### N-3: templates/shared/style.css (A-2 시드 전문)

```css
/* html-mockup shared styles — 모든 화면 공통 */
/* 주의: Tailwind Play CDN은 외부 CSS 파일에서 @apply 컴파일을 보장하지 않는다.
   외부 파일은 일반 CSS 속성만 사용한다. Tailwind 유틸리티가 필요하면 HTML 인라인 클래스로 적용. */

/* 한글 폰트 — Pretendard 우선 + 시스템 폴백 (R-T5 폴백 체인) */
.font-pretendard {
  font-family: 'Pretendard', 'Pretendard Variable', -apple-system, BlinkMacSystemFont,
               system-ui, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
               'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
}

/* 본문 기본 — 일반 CSS (Tailwind text-base/leading-relaxed 동등) */
body { font-size: 1rem; line-height: 1.625; }

/* 자주 쓰는 컨테이너 — 페이지 가운데 정렬 + 반응형 패딩 */
.mockup-container {
  max-width: 64rem;       /* Tailwind max-w-5xl */
  margin-left: auto;
  margin-right: auto;
  padding-left: 1rem;     /* px-4 */
  padding-right: 1rem;
}
@media (min-width: 640px) {
  .mockup-container { padding-left: 1.5rem; padding-right: 1.5rem; }   /* sm:px-6 */
}
@media (min-width: 1024px) {
  .mockup-container { padding-left: 2rem; padding-right: 2rem; }       /* lg:px-8 */
}

/* 단일 파일 모드 — section 간 시각 구분 (§(f) 단일 파일 모드 참조) */
section[id^="screen-"] { border-top: 1px solid hsl(var(--b3, 220 13% 91%)); }
section[id^="screen-"]:first-of-type { border-top: 0; }
```

- **`@apply` 미사용 정책**: Tailwind Play CDN의 JIT는 HTML 문서 안의 `<style type="text/tailwindcss">` 태그만 처리한다. `<link rel="stylesheet">`로 연결된 외부 `.css` 파일에서 `@apply`는 컴파일 보장이 안 된다 → 외부 파일은 일반 CSS 속성으로 작성하고, Tailwind 유틸리티가 필요한 부분은 HTML 인라인 클래스로 적용 (QA 보강 검증 R-2 지적 반영).
- **다크모드**: 인터뷰에서 ON 시 `<html data-theme="dark">` 한 줄로 활성 (DaisyUI 자동 처리). 별도 CSS 변수 추가 불필요.
- **DaisyUI 색 변수 사용**: `hsl(var(--b3))`처럼 DaisyUI 토큰을 쓰되, fallback 값(`220 13% 91%`)을 함께 명시하여 변수 미정의 환경 안전성 확보.

(→ TASK §확정 §4, §9, §13, §(f))

#### N-4: templates/shared/main.js (A-3 시드 전문)

```js
// html-mockup shared scripts — 모든 화면 공통 동작

// 1) Lucide 아이콘 초기화 — DOM 로드 후 자동 치환
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide && typeof window.lucide.createIcons === 'function') {
    window.lucide.createIcons();
  }
});

// 2) Alpine.js 전역 store — 단일 파일 모드 활성 탭 추적 (§(f) 단일 파일 모드용)
document.addEventListener('alpine:init', () => {
  if (window.Alpine) {
    Alpine.store('ui', {
      activeTab: '',
      setTab(slug) { this.activeTab = slug; }
    });
  }
});

// 3) 해시 변경 시 활성 탭 동기화 (단일 파일 모드)
window.addEventListener('hashchange', () => {
  const slug = location.hash.replace(/^#screen-/, '');
  if (window.Alpine && Alpine.store('ui')) Alpine.store('ui').setTab(slug);
});
```

- Lucide 초기화는 boilerplate의 inline `<script>lucide.createIcons()</script>`와 중복 안전 (idempotent).
- Alpine store는 단일 파일 모드에서만 사용 — 화면별 분리 모드에서는 dead code (영향 없음).

(→ TASK §확정 §4, §(f) 단일 파일 모드)

#### N-5: templates/index.html.tmpl (A-5 마크업 전문)

다중 화면(2개 이상) 시 자동 생성되는 인덱스 페이지. boilerplate 위에 카드 그리드를 얹는 구조. 치환 토큰: `{{TITLE}}`(화면 묶음 제목) + `{{ITEMS}}`(카드 반복 영역).

```html
<!-- index.html.tmpl 본문 (보일러플레이트는 N-2 그대로) -->
<main class="mockup-container py-8">
  <header class="mb-8">
    <h1 class="text-3xl font-bold mb-2">{{TITLE}}</h1>
    <p class="text-base-content/70">총 {{COUNT}}개 화면</p>
  </header>
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {{ITEMS}}
  </div>
</main>
```

각 카드 마크업 (스킬이 화면 N개에 대해 N번 반복 치환):

```html
<a href="{{FILE}}.html" class="card bg-base-100 shadow hover:shadow-lg transition cursor-pointer">
  <div class="card-body">
    <h2 class="card-title flex items-center gap-2">
      <i data-lucide="{{ICON}}" class="w-5 h-5"></i>
      {{NAME}}
    </h2>
    <p class="text-sm text-base-content/70">{{DESC}}</p>
  </div>
</a>
```

치환 변수:

| 토큰 | 값 |
|------|---|
| `{{TITLE}}` | 화면 묶음 제목 (예: "html-mockup 화면 인덱스") |
| `{{COUNT}}` | 화면 개수 (정수) |
| `{{ITEMS}}` | 위 카드 마크업의 N개 연결 문자열 |
| `{{FILE}}` | 화면 파일명 (확장자 제외, 예: `login`) |
| `{{ICON}}` | Lucide 아이콘 이름 (AI 추론 — 로그인=`log-in`, 대시보드=`layout-dashboard` 등) |
| `{{NAME}}` | 화면 사람 이름 (예: "로그인") |
| `{{DESC}}` | 화면 1줄 설명 (인터뷰 §3 응답 또는 추론) |

- 그리드: 모바일 1열 / md(768px+) 2열 / lg(1024px+) 3열 — TASK §13 반응형 ON 정책 (→ §(f) 단일 파일 모드는 별도 분기, index는 항상 카드 그리드)
- 카드 클릭 영역 = 카드 전체 (`<a>`로 감쌈)

(→ R-13, TASK §확정 §11)

#### M-1: 레지스트리 항목 추가

`opal/core/references/opal-skills-registry.json` `groups.standalone` 배열 끝에 추가:

```json
{
  "name": "html-mockup",
  "alias": "mockup",
  "description": "CDN 기반 정적 HTML 화면 빠른 생성 — 태스크 컨텍스트 자동 흡수 + 인터뷰",
  "triggers": ["^html-mockup$", "^mockup$", "(?i)(목업|모크업|HTML\\s*화면\\s*만들|HTML\\s*목업)"],
  "paths": ["{project}/.opal/skills/html-mockup/SKILL.md", "~/.opal/skills/html-mockup/SKILL.md"]
}
```

(→ D-15 `~/.opal/tools/skill-registry/skill-registry.js:67-96`, D-17 `opal/core/references/opal-skills-registry.json:212-255`)

##### trigger 정규식 매칭 케이스 (A-8)

trigger 정규식 4개(`^html-mockup$`, `^mockup$`, `(?i)(목업|모크업|HTML\s*화면\s*만들|HTML\s*목업)`)가 의도대로 매칭되는지 케이스 표로 검증.

| 입력 | 기대 결과 | 매칭 정규식 |
|------|---------|---------|
| `html-mockup` | ✅ found | `^html-mockup$` |
| `mockup` | ✅ found (alias 단독) | `^mockup$` |
| `//mockup 로그인` | ✅ found | skill-commands가 `//mockup`을 추출, `^mockup$` 매칭 |
| `목업 만들어줘` | ✅ found | `(?i)목업` |
| `HTML 화면 만들어줘` | ✅ found | `(?i)HTML\s*화면\s*만들` |
| `HTML 목업 만들어` | ✅ found | `(?i)HTML\s*목업` (목업 우선) |
| `모크업 한 페이지` | ✅ found | `(?i)모크업` |
| `mock` | ❌ not found | 부분 매칭 — `^mockup$` 안 됨 |
| `프로토타입 만들어` | ❌ not found (ui-designer로) | 본 스킬 토큰 없음 |
| `와이어프레임 만들어` | ❌ not found (wireframe-builder로) | 본 스킬 토큰 없음 |
| `HTML로 카드 보여줘` | ❌ not found | "만들"/"목업" 동사 토큰 없음 |
| `mockup-data 분석` | ⚠ found (의도치 않음) | `^mockup$`은 정확 매칭이라 안 잡지만, `mockup` 단어가 포함된 자연어 요청은 다른 정규식이 잡지 않음 → false-positive 없음. 단 `mockup`이 `mockup-data` 등과 헷갈릴 가능성 모니터링 |

> ⚠ 케이스의 `mockup-data`는 `^mockup$` 정확 매칭이라 안전하나, 문법 상 사용자 자연어가 "`mockup-data 분석`"인 경우 skill-commands가 첫 토큰만 잘라 `mockup-data`로 매칭 시도 → `^mockup$`에 부정합 → 정상적으로 not found. 안전.

검증 명령:

```bash
# 긍정 케이스
node ~/.opal/tools/skill-registry/skill-registry.js match "//mockup"          # → found:true
node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"        # → found:true
node ~/.opal/tools/skill-registry/skill-registry.js match "목업 만들어줘"        # → found:true
node ~/.opal/tools/skill-registry/skill-registry.js match "HTML 화면 만들어"    # → found:true

# 부정 케이스
node ~/.opal/tools/skill-registry/skill-registry.js match "mock"                # → found:false
node ~/.opal/tools/skill-registry/skill-registry.js match "프로토타입 만들어"     # → ui-designer 또는 found:false
```

검증 도구:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js validate
node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"
node ~/.opal/tools/skill-registry/skill-registry.js match "mockup"
```

> [MUST] `~/.opal/references/skills.md` §스킬 도구 사용법: "스킬 메타데이터는 JSON 레지스트리가 SSOT이다." — 본 등록은 SSOT 갱신이며, `~/.opal/` 직접 수정이 아닌 소스(`opal/core/references/...`) 갱신으로 수행한다 (→ D-4 §확정 기준 #2).

> [주의] 배포 시점에 `~/.opal/`로 동기화되기 전까지는 `~/.opal/tools/skill-registry/skill-registry.js`가 (배포된 구버전 JSON을 읽으므로) 본 변경을 반영하지 않을 수 있다. `getReferencesDir()`은 배포본 우선이며, 미배포 시에만 소스 폴백 (`skill-registry.js:34-42`). 검증은 캡틴이 `install-mac.sh` 실행 후 수행한다.

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 4개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1, 2, 3, 4 | 병렬 | templates/* 4개 파일은 독립 — 동시 작성 가능 |
| 2 | 5 | 순차 | SKILL.md는 templates 경로를 참조하므로 Phase 1 이후 |
| 3 | 6 | 순차 | 레지스트리는 SKILL.md path 등록 — Phase 2 이후 |
| 4 | 7 | 순차 | 검증은 모든 산출물 완료 후 |

### Step 1: 보일러플레이트 HTML 시드 작성

- [x] 완료
- **파일**: `skills/html-mockup/templates/boilerplate.html`
- **작업 내용**: TASK §9 보일러플레이트 그대로 작성. 치환 토큰 `{{TITLE}}`, `{{BODY}}` 추가. `<head>` 자원 순서(Pretendard → Tailwind → DaisyUI → Alpine → Lucide → shared/style.css → shared/main.js) 준수. 마지막 `<script>lucide.createIcons();</script>` 포함.
- **완료 기준**: 파일이 존재하고, 5개 CDN(Pretendard/Tailwind/DaisyUI/Alpine/Lucide) 링크가 모두 들어가 있으며, lang="ko" + UTF-8 + viewport 메타 + `<body class="font-pretendard">`가 명시된다.
- **테스트**: `cat skills/html-mockup/templates/boilerplate.html | grep -E "Pretendard|tailwindcss|daisyui|alpinejs|lucide"`로 5개 모두 출력 확인.
- **의존**: 없음

### Step 2: 공통 CSS 시드 작성

- [x] 완료
- **파일**: `skills/html-mockup/templates/shared/style.css`
- **작업 내용**: `font-pretendard` 클래스를 Pretendard + 시스템 폰트 폴백으로 매핑. 기본 색/간격 변수는 비워두고 화면 작업 시 추가하는 형태로 시드 최소화 (5~15줄).
- **완료 기준**: 파일이 존재하고, `.font-pretendard` 셀렉터에 `font-family`가 정의되어 있다.
- **테스트**: `grep "font-pretendard" skills/html-mockup/templates/shared/style.css`
- **의존**: 없음

### Step 3: 공통 JS 시드 작성

- [x] 완료
- **파일**: `skills/html-mockup/templates/shared/main.js`
- **작업 내용**: 향후 확장용 placeholder. Lucide 초기화 hook + Alpine 글로벌 자리. 시드 최소(3~10줄, 주석 위주).
- **완료 기준**: 파일이 존재하고 syntax error가 없다 (`node --check`).
- **테스트**: `node --check skills/html-mockup/templates/shared/main.js`
- **의존**: 없음

### Step 4: 인덱스 페이지 시드 작성

- [x] 완료
- **파일**: `skills/html-mockup/templates/index.html.tmpl`
- **작업 내용**: 보일러플레이트 기반 + DaisyUI `card` 그리드 + 치환 토큰 `{{ITEMS}}`. 각 카드는 `<a href="{file}.html">` + 화면 제목 + 1줄 설명.
- **완료 기준**: 파일이 존재하고, `card` 클래스 + `{{ITEMS}}` 토큰 + 보일러플레이트의 5개 CDN이 모두 포함된다.
- **테스트**: `grep -E "\\{\\{ITEMS\\}\\}|card|tailwindcss" skills/html-mockup/templates/index.html.tmpl`
- **의존**: 없음

### Step 5: SKILL.md 본문 작성

- [x] 완료
- **파일**: `skills/html-mockup/SKILL.md`
- **작업 내용**:
  1. YAML frontmatter (`name: html-mockup`, `description: ...`)
  2. 0. 호출 환경 — `//html-mockup` / `//mockup`, 호출 가능 모드 4종 (R-1)
  3. 1. 프로세스 — Step 1~6 상세화
     - Step 1: cwd `.opal/AGENT.md` 검사 → `tasks/{NNN}-*/TASK.md` 매칭 → STATE/MEMORY 폴백 (R-2)
     - Step 2: 감지 결과별 흡수 자원 표 (R-2)
     - Step 3: interview 스킬 호출 (path 우선순위 명시) + 7단계 인터뷰 + 스킵 1줄 통지 형식 (R-3, R-19)
     - Step 4: 4종 입력 자원 처리 (R-17)
     - Step 5: 산출물 생성 흐름 — 보일러플레이트 Read/치환/Write, 화면명 변환, 다중 시 index 자동 (R-4, R-6, R-11, R-12, R-13)
     - Step 6: 보고 형식 분기 (R-18)
  4. 2. 산출물 구조 (R-4)
  5. 3. 기본 기술 스택 + CDN 핀 정책 표 + 대안 2종 (R-5, R-14)
  6. 4. 보일러플레이트 — `templates/boilerplate.html` 사용 절차 (R-11)
  7. 5. 파일명 규칙 (R-12)
  8. 6. 인덱스 페이지 자동 (R-13)
  9. 7. 디자인 정책 (R-15)
  10. 8. 반복 수정 (R-7)
  11. 9. 에러 처리 표 (R-16)
  12. 10. [MUST] 제약 — `.opal/AGENT.md` §확정 기준 #2 / §금지사항 인용
- **완료 기준**: SKILL.md가 존재하고, R-1 ~ R-19 모든 요구사항이 본문에서 매핑 가능(섹션·표로 확인됨), YAML frontmatter가 OPAL 표준(`name`, `description`)에 부합, [MUST] 인용 3개 이상 포함, interview 탐색 경로 우선순위가 op-task와 동일한 형태로 명시됨.
- **테스트**: TASK §V-1 ~ §V-8을 SKILL.md 내용에 매핑 — 각 시나리오를 만족하는 절차/규칙이 본문에 존재하는지 사람이 확인.
- **의존**: Step 1, 2, 3, 4 (templates 경로 참조)

### Step 6: 스킬 레지스트리 등록

- [x] 완료
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: `groups.standalone` 배열 끝에 항목 추가:
  ```json
  {
    "name": "html-mockup",
    "alias": "mockup",
    "description": "CDN 기반 정적 HTML 화면 빠른 생성 — 태스크 컨텍스트 자동 흡수 + 인터뷰",
    "triggers": ["^html-mockup$", "^mockup$", "(?i)(목업|모크업|HTML\\s*화면\\s*만들|HTML\\s*목업)"],
    "paths": ["{project}/.opal/skills/html-mockup/SKILL.md", "~/.opal/skills/html-mockup/SKILL.md"]
  }
  ```
- **완료 기준**: JSON이 valid하고, `name=html-mockup`/`alias=mockup` 항목이 standalone 배열에 1개 존재한다. 다른 standalone 항목과 alias 충돌 없음 (현재 `wfb`, `uid`, `wtm`, `erm`만 사용 중 — `mockup`은 유일).
- **테스트**: `python3 -c "import json; d=json.load(open('opal/core/references/opal-skills-registry.json')); print([s['name'] for s in d['groups']['standalone']])"` — `html-mockup`이 출력에 포함된다.
- **의존**: Step 5

### Step 7: 검증 — 매칭/별칭/validate

- [x] 완료
- **파일**: (검증만 — 산출물 변경 없음)
- **작업 내용**: 캡틴이 본 PLAN 승인 후 EXECUTE 단계에서 다음 명령 실행:
  ```bash
  # 1. 레지스트리 정합성 검증 (본 태스크는 ~/.opal/ 직접 수정 금지이므로 소스 기준 가상 실행 — 배포 후 캡틴 검증)
  node ~/.opal/tools/skill-registry/skill-registry.js validate
  # 2. 정식 매칭
  node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"
  # 3. 별칭 매칭
  node ~/.opal/tools/skill-registry/skill-registry.js match "mockup"
  # 4. // 호출 매칭
  node ~/.opal/tools/skill-registry/skill-registry.js match "//mockup 로그인 화면"
  ```
- **완료 기준**:
  - validate가 errors 0으로 통과 (warnings는 path 미배포 경고 1건 가능 — 캡틴 install-mac.sh 후 해소)
  - match "html-mockup", match "mockup", match "//mockup …" 모두 `found:true` + 같은 paths 반환 (`{project}/.opal/skills/html-mockup/SKILL.md` 또는 `~/.opal/skills/html-mockup/SKILL.md`)
- **테스트**: 위 4개 명령 출력 확인. `found:false`이면 트리거 정규식 또는 alias 등록 오류이므로 Step 6으로 회귀.
- **의존**: Step 6

---

### EXECUTE 산출물 — changed_files 기대 목록 (B-2)

EXECUTE 워커 완료 시 `changed_files`에 다음 6개 절대 경로가 모두 포함되어야 한다. PM Gate에서 누락 검증.

| # | 절대 경로 | 종류 |
|---|----------|------|
| 1 | `/Volumes/Data/AiStudio/workspace/opal/skills/html-mockup/SKILL.md` | 신규 |
| 2 | `/Volumes/Data/AiStudio/workspace/opal/skills/html-mockup/templates/boilerplate.html` | 신규 |
| 3 | `/Volumes/Data/AiStudio/workspace/opal/skills/html-mockup/templates/shared/style.css` | 신규 |
| 4 | `/Volumes/Data/AiStudio/workspace/opal/skills/html-mockup/templates/shared/main.js` | 신규 |
| 5 | `/Volumes/Data/AiStudio/workspace/opal/skills/html-mockup/templates/index.html.tmpl` | 신규 |
| 6 | `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-skills-registry.json` | 수정 |

PM Gate 검증 항목:

- 6개 파일 모두 `changed_files` 배열에 포함
- 각 파일이 실제 존재 (`ls` 또는 `Read` 1회)
- SKILL.md는 YAML frontmatter + 본문 1KB 이상
- boilerplate.html은 5개 CDN URL + lang/charset/viewport + body class="font-pretendard" 포함
- style.css는 `.font-pretendard` 셀렉터 포함
- main.js는 `lucide.createIcons` 호출 포함, `node --check` 통과
- index.html.tmpl은 `card` + `{{ITEMS}}` + 5개 CDN URL 포함
- opal-skills-registry.json은 `python3 -c "import json; json.load(open(...))"` valid JSON, `groups.standalone`에 `name=html-mockup` 항목 존재

---

## 4. QA 체크리스트

### 기능 테스트 (TASK §검증 시나리오 V-1 ~ V-8 매핑)

- [x] **V-1**: 비-OPAL cwd에서 `//mockup` 호출 — SKILL.md Step 1에 cwd `.opal/AGENT.md` 미존재 분기 + Step 2에 "흡수 없음" 분기가 명시되고, 저장 위치 인터뷰가 필수로 진입한다.
- [x] **V-2**: 태스크 폴더 안에서 `//mockup` 호출 — SKILL.md Step 1에 `tasks/{NNN}-*/TASK.md` 패턴 검사 + Step 2에 "TASK.md/ANALYSIS.md/PLAN.md 자동 흡수" 절차 + Step 3에 "추론값 1줄 통지 후 부족분만 인터뷰"가 명시된다.
- [x] **V-3**: 다중 화면 (3개) 호출 — SKILL.md §6 인덱스 페이지 자동 생성 규칙(2개 이상 시 index.html) + §2 산출물 구조에 화면 간 상대 링크 명시 + Step 5에 보일러플레이트 일괄 적용 절차가 있다.
- [x] **V-4**: 같은 화면명으로 반복 호출 (수정) — SKILL.md §8 반복 수정 규칙(같은 파일 덮어쓰기, 신규 생성 금지)이 명시된다.
- [x] **V-5**: 단일 파일 모드 호출 — SKILL.md §2(또는 인터뷰 §4)에 단일 파일 모드 분기 조건 + 한 HTML에 섹션 묶기 절차가 명시된다.
- [x] **V-6**: 정식·별칭 둘 다 매칭 — Step 7에서 `match "html-mockup"`, `match "mockup"` 모두 `found:true`로 같은 SKILL.md 경로 반환.
- [x] **V-7**: 한글 화면명 입력 — SKILL.md §5 파일명 규칙에 transliteration + 사용자 확인 단계가 명시된다.
- [x] **V-8**: 사전 와이어프레임 이미지 입력 — SKILL.md Step 4에 4종 입력 처리(이미지=Read 도구) + 인터뷰 단계 자동 스킵 조건이 명시된다.

### 일관성 테스트

- [x] op-task SKILL.md의 interview 호출 패턴(`{프로젝트}/.opal/skills/interview/SKILL.md` → `~/.opal/skills/interview/SKILL.md`)과 동일한 우선순위로 본 SKILL.md가 호출한다.
- [x] 신규 레지스트리 항목이 standalone 배열의 기존 항목 형식(api-analyzer/wfb/uid/wtm/erm)과 동일한 키 셋(`name, alias, description, triggers, paths`)을 가진다.
- [x] alias `mockup`이 standalone/op-task/op-dev/op-sdd/opal-pilot/opal 그룹 전체에서 유일하다 (`skill-registry.js validate`의 alias uniqueness 검증).
- [x] [MUST] 인용이 `.opal/AGENT.md` 원문(§확정 기준 #2, §금지사항)을 정확히 옮긴다.
- [x] 보일러플레이트 HTML이 TASK §9 본문과 자원 순서·태그 속성까지 일치한다.
- [x] 본 PLAN의 결정이 TASK §확정 설계 방향 1~17과 모두 정합한다 (역추적 가능).

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따른다 (Step 5 기준).
- [x] kebab-case 파일/폴더 네이밍을 따른다 (`html-mockup/`, `boilerplate.html`, `index.html.tmpl`, `style.css`, `main.js`).
- [x] YAML frontmatter가 OPAL 표준 (`name`, `description` 필수)에 부합한다.
- [x] 외부 CDN URL이 TASK §확정 §5, §9의 5개 자원과 정확히 일치한다.
- [x] 본 PLAN이 §1 참조 문서 테이블 + §2 핵심 설계 인라인 인용 + [MUST] 포맷을 모두 적용한다 (citation-rules.md §3, §2.4).

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| R-T1 alias 충돌 — `mockup`이 미래 등록될 다른 스킬과 경합 가능 | 매칭 우선순위 모호 | 본 PLAN에서 standalone 그룹 alias 전수 점검(현재 `wfb`,`uid`,`wtm`,`erm`만 사용 — 충돌 없음). 미래 추가 시 컨벤션 문서에 명기 권고 |
| R-T2 install-mac.sh 일괄 복사 가정이 깨질 가능성 — 향후 화이트리스트 방식으로 변경 시 본 스킬 미배포 | 배포 누락 | install-mac.sh §독립 스킬 라인(`scripts/install-mac.sh:440-441`)이 `install_dir "$FRAMEWORK_ROOT/skills" ...` 패턴을 유지하는 한 OK. PM이 install-mac.sh 변경 PR마다 본 스킬 영향 검토. PLAN에는 가정 명시. |
| R-T3 CDN 변경(DaisyUI 5 메이저 릴리즈, Tailwind v4 default 변경 등) | 화면 깨짐 | 본 스킬은 TASK §12 핀 정책으로 메이저 핀(`@4`, `@3`)을 적용. 메이저 변경 시 SKILL.md 업데이트 별도 태스크. |
| R-T4 file:// CORS — `<a href="other.html">` 정상이나 `fetch('./shared/nav.html')` 차단 가능 | 다중 화면 nav 주입 동작 안 함 | TASK §확정 §4에서 nav.html은 (선택)으로 표시. SKILL.md에 "fetch 사용 시 file:// 환경에서는 동작하지 않을 수 있음" 주의 명시. |
| R-T5 Pretendard CDN URL 깨짐 (gh 경로 변경) | 한글 폰트 폴백 | `style.css`에 시스템 폰트 폴백 체인 명시 (Step 2). 사용자 알림 + 필요 시 인터뷰에서 다른 폰트 교체. |
| R-T6 인터뷰 스킬 미배포 환경 | interview 호출 실패 | 본 SKILL.md에 "interview 스킬 미존재 시 인라인 폴백 — 저장 위치 1문 + 핵심 항목 1~2문" 절차 명시 (op-task가 동일 폴백 패턴). |
| R-T7 영역 간 용어 불일치 | citation-rules.md §7 검출 의무 | 본 태스크는 단일 영역(스킬 정의) — 용어 충돌 검출 대상 없음 (FE/BE/ERD/IA 어느 영역과도 매핑 안 됨). decision_required 항목 없음 (§7.4). |
