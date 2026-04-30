# TASK: html-mockup 일반 스킬 신규 개발

> 작성일: 2026-04-30 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

태스크 진행 중 또는 일반 작업 중에도 호출 가능한 일반 스킬 `html-mockup`을 신규 개발한다. 현재 컨텍스트(태스크 폴더 자동 감지 + TASK/ANALYSIS/PLAN/PROJECT 흡수)와 인터뷰를 결합하여 빠르게 검토 가능한 정적 HTML 화면을 생성한다.

## 배경

태스크를 진행하다 보면 화면 UI/UX를 빠르게 시각적으로 검토할 필요가 있다. 그러나 와이어프레임 전용(`opdw`)은 dev 파이프라인 전제이고, 단순한 화면 1~수 개를 빠르게 만들어 클릭으로 흐름만 확인하기에는 무겁다. 태스크 밖(비서 모드)에서도 동일한 도구가 필요하다.

## 배경 분석 (대화에서 도출)

- **위치 가이드라인**: `docs/PROJECT.md` §폴더 구조맵 — `skills/`는 "독립 스킬 소스 — 파이프라인 없이 단독 사용하는 스킬"로 정의됨 (→ D-1)
- **네이밍 규칙**: `docs/PROJECT.md` §네이밍 규칙 — `skills/` 하위는 `{기능명}/`(kebab-case) 형식, 예: `api-analyzer/`, `interview/` (→ D-1)
- **호출 인프라**: `~/.opal/references/harness/skill-commands.md` §쌍슬래시 커맨드 — `//{스킬명}` 형식으로 호출, 레지스트리(skill-registry.js)에 등록되면 약식 매칭 가능 (→ D-2)
- **태스크 폴더 컨텍스트 자동 흡수 가능 자원**:
  - `tasks/{NNN}-*/TASK.md` — 작업 목표/배경/요구사항/AC
  - `tasks/{NNN}-*/ANALYSIS.md` (있을 경우) — 관련 파일 맵, 제약, 리스크
  - `tasks/{NNN}-*/PLAN.md` (있을 경우) — 설계 결정, 실행 체크리스트
  - `docs/PROJECT.md` — 프로젝트 도메인/원칙/기술 스택
- **인터뷰 스킬 재사용**: `~/.opal/skills/interview/SKILL.md` 또는 `op-task/SKILL.md` STEP 2에서 사용한 "interview 스킬 연동" 패턴을 따른다 — 부족한 정보만 묻고 결과를 확정/미확정으로 분류 (→ D-3)

## 확정된 설계 방향 (대화에서 합의)

### 1. 스킬 정체성

| 항목 | 값 |
|------|---|
| 스킬명 | `html-mockup` |
| 분류 | 일반 스킬 (오케스트레이터 아님, 단계 스킬 아님) |
| 소스 위치 | `skills/html-mockup/` |
| 배포 위치 | `~/.opal/skills/html-mockup/` (install-mac.sh 동기화 대상) |
| 호출 | `//html-mockup` |
| 호출 환경 | 태스크 안 / 태스크 밖 / 비서 모드 / PM 모드 — 전부 호출 가능 |

### 2. 컨텍스트 자동 흡수 로직

스킬 시작 시 다음 순서로 환경을 감지한다:

1. 현재 cwd가 OPAL 프로젝트인가? (`.opal/AGENT.md` 존재)
2. 현재 cwd가 태스크 폴더 안인가? (`tasks/{NNN}-*/TASK.md` 패턴)
3. 태스크 폴더가 아니면, 작업 중인 태스크가 있는지 STATE.md / MEMORY.md로 감지

**감지 결과별 동작**:

| 감지 결과 | 흡수 자원 | 비고 |
|----------|---------|------|
| 태스크 폴더 안 | TASK.md / ANALYSIS.md / PLAN.md (있는 만큼) + `docs/PROJECT.md` | 화면 의도 자동 추론 |
| OPAL 프로젝트(태스크 밖) | `docs/PROJECT.md` | 프로젝트 톤만 흡수 |
| 비-OPAL 환경 | 흡수 없음 | 순수 인터뷰 모드 |

### 3. 인터뷰 정책

- 부족분만 묻는다 (최소 1문 = **저장 위치 확인**은 항상 필수)
- 인터뷰 항목 후보:
  - 저장 위치 (필수) — 태스크 안이면 `mockup/` 제안, 밖이면 cwd 기준 제안
  - 화면 종류·개수 (자명하지 않으면)
  - 핵심 액션·데이터 예시 (자명하지 않으면)
  - 단일 파일 vs 화면별 분리 (선택, 기본은 분리)
  - UI 라이브러리 — DaisyUI(기본 추천) / Flowbite / 없음(Tailwind만)
- 컨텍스트로 추론 가능한 항목은 묻지 않고 "추론 결과 + 변경 의사 확인"으로 대체

### 4. 산출물 구조

```
{저장 위치}/
  shared/
    style.css       # 공통 스타일 (커스텀 색상, 한글 폰트 등)
    main.js         # 공통 인터랙션 (모달 토글, 폼 검증 흉내 등)
    nav.html        # (선택) 공통 네비/사이드바 — fetch로 주입
  {화면명-1}.html
  {화면명-2}.html
  ...
```

- **외부 분리 원칙**: 토큰 절약을 위해 CSS/공통 JS는 `shared/`에 분리. 각 HTML은 `<head>`에 CDN + `./shared/*` 링크만 포함하고 본문은 화면 마크업만 들어간다.
- **다중 화면**: 같은 호출 안에서 여러 화면을 생성할 수 있다. 화면 간 이동은 상대 경로 링크(`<a href="dashboard.html">`)로 연결한다.
- **단일 파일 모드**: 인터뷰에서 캡틴이 명시적으로 요청 시에만 활성화 (한 파일에 섹션으로 묶기).

### 5. CDN UI 컴포넌트 스택

기본 조합 (전부 CDN, 빌드 0):

| 자원 | 역할 | CDN URL |
|------|------|--------|
| Tailwind CSS | 유틸리티 | `https://cdn.tailwindcss.com` |
| DaisyUI | 컴포넌트 클래스 (`btn`, `card`, `modal` 등) — 토큰 절약 효과 최대 | `https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css` |
| Alpine.js | 선언적 인터랙션 (토글/모달/탭) | `https://unpkg.com/alpinejs@3/dist/cdn.min.js` |
| Lucide Icons | 아이콘 SVG 자동 치환 | `https://unpkg.com/lucide@latest` |

대안: Flowbite(Tailwind 표준 클래스 위주) / 없음(Tailwind만) — 인터뷰에서 선택.

### 6. 미리보기 정책

- **저장만**: 캡틴이 직접 브라우저로 파일을 열어 확인한다.
- 스크린샷·자동 미리보기 등은 본 태스크 범위 밖.

### 7. 반복 수정 루프

- 첫 생성 후 캡틴 피드백 시 **같은 파일 갱신** (덮어쓰기). 새 파일 생성 아님.
- **변경 이력 별도 기록 없음**: `CHANGELOG.md` 등 보조 파일 만들지 않고 그냥 덮어쓰기 (캡틴 결정).

### 8. 별칭(alias)

- 정식 호출: `//html-mockup`
- 별칭 호출: `//mockup`
- 둘 다 같은 SKILL.md로 라우팅된다 (스킬 레지스트리 alias 필드 사용).

### 9. HTML 보일러플레이트 표준

모든 화면 HTML은 다음 보일러플레이트로 시작한다 (단일 파일 모드 포함):

```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{화면 제목}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet">
  <script defer src="https://unpkg.com/alpinejs@3/dist/cdn.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <link rel="stylesheet" href="./shared/style.css">
  <script defer src="./shared/main.js"></script>
</head>
<body class="font-pretendard">
  <!-- 화면 마크업 -->
  <script>lucide.createIcons();</script>
</body>
</html>
```

- **Pretendard**는 한글 폰트 기본값. 인터뷰에서 캡틴이 다른 폰트 요청 시 교체.
- **`<body class="font-pretendard">`** 같은 클래스는 `shared/style.css`에서 폰트 패밀리를 매핑.

### 10. 화면명 → 파일명 변환 규칙

| 입력 | 변환 |
|------|------|
| 영문 입력 (`Login Screen`) | kebab-case → `login-screen.html` |
| 한글 입력 (`로그인`) | 영문 transliteration 시도 후 사용자 확인 — `login`으로 제안 → 캡틴 수정 가능 |
| 혼합/모호 | 인터뷰에서 파일명 직접 확인 |

- 파일명은 항상 ASCII 영소문자 + 하이픈만 사용 (file:// URL 호환성).

### 11. 인덱스 페이지 자동 생성

- **화면 1개**: 인덱스 페이지 생성하지 않음.
- **화면 2개 이상**: `index.html`을 자동 생성. 내용:
  - 각 화면명을 1줄 설명과 함께 표/리스트로 노출
  - `<a href="{화면}.html">`로 이동 링크
  - DaisyUI `card` 또는 `list` 컴포넌트 사용

### 12. CDN 버전 핀 정책

| 자원 | 핀 정책 | 이유 |
|------|--------|------|
| Tailwind | `cdn.tailwindcss.com` (latest) | Play CDN은 메이저 핀 미지원, 자동 latest |
| DaisyUI | `daisyui@4` (메이저 핀) | 컴포넌트 클래스 호환성 보장 |
| Alpine.js | `alpinejs@3` (메이저 핀) | 디렉티브 API 호환성 |
| Lucide | `lucide@latest` | 아이콘 추가 자동 반영 |
| Pretendard | latest (`gh/orioncactus/pretendard`) | 한글 폰트, 안정성 높음 |

> 캡틴이 정확한 버전을 요청하면 인터뷰에서 변경 가능.

### 13. 반응형 / 다크모드 정책

- **반응형**: 기본 ON. Tailwind `sm:`/`md:`/`lg:`/`xl:` 유틸을 적극 활용. 모바일 기준으로 시작해 데스크톱으로 확장.
- **다크모드**: 기본 OFF (light only). 인터뷰에서 "다크모드 필요?" 질문 시 ON. ON이면 DaisyUI 테마 토글(`data-theme`) 적용.

### 14. 에러 케이스 처리

| 케이스 | 처리 |
|--------|------|
| 저장 위치 폴더가 이미 존재 | 기존 폴더 사용. 안의 파일은 (아래 케이스로 분기) |
| 같은 호출 안에서 같은 화면명 반복 (수정 의도) | 덮어쓰기 (확정 §7) |
| 다른 호출에서 같은 파일명 충돌 | 캡틴에게 확인 — "덮어쓸까요? 다른 이름으로 저장할까요?" |
| 저장 위치 권한 문제 | 즉시 캡틴 에스컬레이션, 진행 중단 |
| CDN 도달 불가 (네트워크) | 본 스킬은 오프라인 보장하지 않음 (Out-of-scope §O-1) — 작성은 계속, 캡틴이 브라우저로 열 때 발견 |

### 15. 입력 자원 확장

캡틴은 다음 입력을 처음부터 또는 인터뷰 단계에서 제공할 수 있다:

| 자원 유형 | 처리 |
|----------|------|
| 와이어프레임 이미지 (`.png`/`.jpg`) | Read 도구로 이미지 로드 → 시각적 구조 참조 |
| Figma URL / 디자인 사이트 URL | WebFetch 또는 캡틴이 캡처해서 첨부 (직접 fetch 어려우면 캡틴 확인) |
| 참고 사이트 URL (실제 제품) | WebFetch로 톤·구조 흡수 |
| 텍스트 설명 / 마크다운 | 인라인 흡수 |

- 인터뷰에서 "참고할 디자인이나 와이어프레임이 있습니까?" 한 번 묻고, 없으면 스킵.
- 사전 제공된 입력은 인터뷰에서 그 단계 자동 스킵.

### 16. 보고 형식 (생성 후)

내용 규모에 따라 분기한다:

| 상황 | 보고 형식 |
|------|---------|
| 단일 화면 신규 | 1줄 — `📎 mockup/{파일명}.html 생성` |
| 다중 화면 신규 | 트리 — `shared/`, `index.html`, 각 화면 파일을 들여쓰기로 |
| 반복 수정 | 변경 요약 — "어떤 화면에 어떤 변경이 적용됐는지" 한두 줄 |

### 17. 인터뷰 흐름 (단계별, 컨텍스트 추론 시 스킵)

다음 순서로 단계별 진행. **각 단계마다 컨텍스트로 추론 가능하면 그 단계는 스킵하고 추론 결과 1줄 통지 후 다음 단계로**:

| # | 단계 | 필수/선택 | 스킵 조건 |
|---|------|---------|---------|
| 1 | 저장 위치 | **필수** | 스킵 불가 (확정 §3) |
| 2 | 화면 종류·개수 | 필수 | 컨텍스트(TASK.md/PLAN.md)에서 자명 |
| 3 | 핵심 액션·데이터 | 선택 | 컨텍스트에서 추론 가능 |
| 4 | 단일 파일 vs 화면별 분리 | 선택 | 기본 화면별 분리 |
| 5 | UI 라이브러리 | 선택 | 기본 DaisyUI |
| 6 | 다크모드 여부 | 선택 | 기본 OFF |
| 7 | 입력 자원 (이미지/URL) | 선택 | 캡틴이 사전 제공 시 자동 스킵 |

> 단계 스킵 시 1줄 안내만 — "{단계}는 컨텍스트에서 {추론값}으로 자동 결정. 변경하시려면 알려주세요." 형태.

## 요구사항

- [x] **R-1 스킬 디렉토리 구조 생성** — `skills/html-mockup/`에 `SKILL.md` + 필요 시 보조 자원(`references/`, `templates/`) 작성
  - 어디에: `skills/html-mockup/SKILL.md`
  - 왜: 일반 스킬 표준 위치 (→ D-1 §폴더 구조맵)
  - AC: `skills/html-mockup/SKILL.md`가 존재하고, YAML frontmatter(`name`, `description`)가 OPAL 표준(다른 일반 스킬 비교)에 부합한다.

- [x] **R-2 컨텍스트 자동 감지 프로세스 정의** — SKILL.md "프로세스" 섹션에 cwd 기반 환경 감지 + 태스크 폴더 감지 + 자원 흡수 절차를 단계로 명시
  - 어디에: `skills/html-mockup/SKILL.md` "프로세스" 섹션
  - 왜: 호출 환경에 따른 흡수 동작 분기(확정 설계 §2)
  - AC: SKILL.md에 (1) `.opal/AGENT.md` 존재 검사, (2) `tasks/{NNN}-*/` 패턴 매칭, (3) 결과별 흡수 자원 목록이 명시된 단계가 존재한다.

- [x] **R-3 인터뷰 정책 정의** — 부족분만 묻는 정책 + 저장 위치 필수 질문 + UI 라이브러리 선택지 명시
  - 어디에: `skills/html-mockup/SKILL.md` "인터뷰" 섹션
  - 왜: 컨텍스트 자동 흡수와 결합한 최소 인터뷰(확정 설계 §3)
  - AC: SKILL.md에 (1) 저장 위치 필수, (2) 컨텍스트 추론 가능 항목은 스킵, (3) 추론 결과는 사용자에게 확인하는 절차가 모두 명시된다.

- [x] **R-4 산출물 구조 + 외부 자원 분리 규칙 명시** — `shared/` 폴더 + 화면별 HTML 분리 + 단일 파일 모드 분기
  - 어디에: `skills/html-mockup/SKILL.md` "산출물" 섹션 (또는 templates/)
  - 왜: 토큰 절약(확정 설계 §4)
  - AC: SKILL.md에 산출물 폴더 구조가 트리 형태로 명시되고, 각 HTML이 `shared/style.css`, `shared/main.js`, CDN 링크를 어떻게 참조하는지 예시 코드(또는 템플릿 파일)로 제시된다.

- [x] **R-5 CDN UI 컴포넌트 스택 기본값 + 대안 명시** — Tailwind + DaisyUI + Alpine.js + Lucide 기본, Flowbite/없음 대안
  - 어디에: `skills/html-mockup/SKILL.md` "기술 스택" 또는 "기본 자산" 섹션
  - 왜: 빠른 검토용 표준 스택 고정(확정 설계 §5)
  - AC: 4개 CDN URL이 SKILL.md에 그대로 기재되고, 대안 2종(Flowbite, Tailwind만)이 선택지로 명시된다.

- [x] **R-6 다중 화면 + 화면 간 네비게이션 규칙 명시** — 화면별 분리 기본, 상대 링크로 흐름 연결
  - 어디에: `skills/html-mockup/SKILL.md` "다중 화면" 섹션
  - 왜: 클릭 흐름 검토 지원(확정 설계 §4)
  - AC: SKILL.md에 화면별 분리 기본 정책 + `<a href="other.html">` 상대 링크 사용 + 단일 파일 모드 분기 조건이 명시된다.

- [x] **R-7 반복 수정 루프 규칙 명시** — 같은 파일 덮어쓰기, 신규 생성 금지
  - 어디에: `skills/html-mockup/SKILL.md` "반복 수정" 섹션
  - 왜: 산출물 누적 방지(확정 설계 §7)
  - AC: SKILL.md에 "수정 시 같은 파일 갱신, 새 파일 생성하지 않음" 규칙이 명시된다.

- [x] **R-8 스킬 레지스트리 등록** — `skill-registry.js`가 `//html-mockup` 매칭에 성공하도록 레지스트리 메타데이터(이름, alias, description, group, domain) 추가
  - 어디에: 레지스트리 데이터 위치 (PLAN에서 확인 — `~/.opal/tools/skill-registry/` 데이터 소스 확인 필요)
  - 왜: 쌍슬래시 호출 전제(확정 설계 §1, → D-2)
  - AC: `node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"`이 `found: true`로 응답한다 (PLAN에서 확인된 등록 절차 적용 후).

- [x] **R-9 install-mac.sh 배포 동기화 검토** — 새 스킬 디렉토리가 `~/.opal/skills/`로 배포되는지 확인
  - 어디에: `scripts/install-mac.sh` (변경 필요 여부 PLAN에서 결정)
  - 왜: PM 검토 기준 — `install-mac.sh 배포 구조와 소스 구조가 일치하는가` (.opal/AGENT.md PM 검토 기준)
  - AC: install-mac.sh가 `skills/` 전체를 자동 배포하는 패턴이면 변경 불필요로 명시 / 명시적 매핑이 필요하면 PLAN에서 변경 항목으로 등록한다.

- [x] **R-10 별칭(alias) 등록** — `//html-mockup` 정식 + `//mockup` 별칭이 모두 매칭되도록 레지스트리 alias 필드 등록
  - 어디에: 스킬 레지스트리 데이터 (R-8 등록 절차에 통합)
  - 왜: 호출 편의(확정 §8)
  - AC: `node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"`과 `match "mockup"` 둘 다 같은 SKILL.md 경로로 `found:true` 응답.

- [x] **R-11 HTML 보일러플레이트 표준 명시** — 모든 화면에 공통 적용되는 `<!doctype>` ~ `</html>` 보일러플레이트 명시
  - 어디에: `skills/html-mockup/SKILL.md` "보일러플레이트" 섹션 (또는 `templates/boilerplate.html`)
  - 왜: 일관된 화면 토대(확정 §9)
  - AC: SKILL.md(또는 templates)에 보일러플레이트 전문이 포함되고, lang/charset/viewport/Pretendard/CDN 4종/shared 링크가 모두 들어간다.

- [x] **R-12 화면명 → 파일명 변환 규칙 명시** — 영문/한글/혼합 입력에 대한 변환 정책
  - 어디에: `skills/html-mockup/SKILL.md` "파일명 규칙" 섹션
  - 왜: 캡틴이 한글 화면명을 줄 때 모호성 제거(확정 §10)
  - AC: SKILL.md에 (1) 영문 → kebab-case, (2) 한글 → transliteration + 사용자 확인, (3) 모호 시 인터뷰 분기 — 3가지가 명시된다.

- [x] **R-13 인덱스 페이지 자동 생성 로직** — 화면 2개 이상 시 `index.html` 자동 생성
  - 어디에: `skills/html-mockup/SKILL.md` "인덱스 페이지" 섹션
  - 왜: 다중 화면 탐색 편의(확정 §11)
  - AC: SKILL.md에 (1) 화면 1개 → 인덱스 생성 안 함, (2) 화면 2개↑ → `index.html` 자동, (3) DaisyUI 컴포넌트 사용한 링크 표 — 3가지가 명시된다.

- [x] **R-14 CDN 버전 핀 정책 명시** — 자원별 핀 전략
  - 어디에: `skills/html-mockup/SKILL.md` "CDN 자원" 섹션
  - 왜: 환경 일관성 + 패치 자동 반영 균형(확정 §12)
  - AC: SKILL.md에 5개 자원(Tailwind/DaisyUI/Alpine.js/Lucide/Pretendard) 각각의 핀 전략과 이유가 표로 명시된다.

- [x] **R-15 반응형/다크모드 기본 정책 명시**
  - 어디에: `skills/html-mockup/SKILL.md` "디자인 정책" 섹션
  - 왜: 캡틴 묵묵부답 시 적용할 디폴트(확정 §13)
  - AC: SKILL.md에 (1) 반응형 기본 ON + 모바일 우선, (2) 다크모드 기본 OFF + 인터뷰 시 ON 가능 — 2가지가 명시된다.

- [x] **R-16 에러 케이스 처리 흐름 명시**
  - 어디에: `skills/html-mockup/SKILL.md` "에러 처리" 섹션
  - 왜: 충돌·권한 문제 시 일관된 동작(확정 §14)
  - AC: SKILL.md에 5종 케이스(폴더 존재/같은 호출 반복/다른 호출 충돌/권한/CDN 도달 불가)별 처리 절차가 표로 명시된다.

- [x] **R-17 입력 자원 확장 — 사전 입력 + 인터뷰 단계 통합**
  - 어디에: `skills/html-mockup/SKILL.md` "입력 자원" 섹션
  - 왜: 와이어프레임/Figma/참고 URL 활용 가능성(확정 §15)
  - AC: SKILL.md에 4종 입력(이미지/Figma URL/참고 사이트 URL/텍스트)별 처리 도구(Read/WebFetch)와 인터뷰 시 자동 스킵 조건이 명시된다.

- [x] **R-18 보고 형식 분기 명시**
  - 어디에: `skills/html-mockup/SKILL.md` "보고 형식" 섹션
  - 왜: 단일/다중/수정 상황별 적절한 보고(확정 §16)
  - AC: SKILL.md에 3가지 상황(단일 화면 신규/다중 화면 신규/반복 수정)별 보고 템플릿이 명시된다.

- [x] **R-19 단계별 인터뷰 + 컨텍스트 추론 시 스킵 로직**
  - 어디에: `skills/html-mockup/SKILL.md` "인터뷰" 섹션 (R-3 확장)
  - 왜: 컨텍스트 자동 흡수와 결합한 최소 인터뷰(확정 §17)
  - AC: SKILL.md에 7단계 인터뷰 순서(저장 위치/화면/액션/분리 모드/UI 라이브러리/다크모드/입력 자원)와 각 단계의 스킵 조건이 명시되고, 스킵 시 "{단계}는 {추론값}으로 자동 결정. 변경하시려면 알려주세요." 형태의 1줄 통지 형식이 포함된다.

## 미확정 사항 (PLAN에서 결정)

- **M-1 스킬 레지스트리 등록 절차**: `skill-registry.js`가 어떤 데이터 소스(JSON 파일? `~/.opal/references/skills.md`?)를 읽어 매칭하는지 PLAN에서 확인 후 등록 방법 결정
- **M-2 install-mac.sh의 `skills/` 처리 방식**: 자동 일괄 복사인지, 명시적 화이트리스트인지 PLAN에서 확인 후 동기화 필요 여부 결정
- **M-3 인터뷰 스킬 재사용 vs 인라인**: `~/.opal/skills/interview/SKILL.md`를 재사용할지, 본 스킬에 인라인 인터뷰 절차를 작성할지 PLAN에서 결정 (현재 op-task가 어떤 방식을 쓰는지 함께 확인)
- **M-4 templates/ 보조 파일 필요 여부**: HTML 보일러플레이트(R-11), `shared/style.css` 시드, `shared/main.js` 시드를 별도 템플릿 파일로 둘지, SKILL.md 안에 인라인으로 둘지 PLAN에서 결정

## 검증 시나리오 (EXECUTE 후 캡틴 확인용)

| # | 케이스 | 검증 절차 | 합격 기준 |
|---|------|---------|---------|
| V-1 | 비-OPAL cwd에서 `//mockup` 호출 | 임의 빈 폴더에서 호출 | 인터뷰 모드 진입, 컨텍스트 흡수 0, 저장 위치 질문 노출 |
| V-2 | 태스크 폴더 안에서 `//mockup` 호출 | 임의 태스크 폴더(예: 본 132)에서 호출 | TASK.md/PLAN.md 자동 흡수, 화면 의도 추론 결과 통지, 부족분만 인터뷰 |
| V-3 | 다중 화면 (3개) 호출 | 한 호출에서 화면 3개 요청 | `shared/`, `index.html`, 화면 3개 HTML 생성 + 화면 간 상대 링크 + index에서 3개 카드 노출 |
| V-4 | 같은 화면명으로 반복 호출 (수정) | V-3 직후 한 화면을 수정 요청 | 같은 파일 덮어쓰기, 신규 파일 생성 0 |
| V-5 | 단일 파일 모드 호출 | 인터뷰에서 "단일 파일" 명시 | 한 HTML 파일에 섹션으로 묶임, 화면별 분리 0 |
| V-6 | 정식·별칭 둘 다 매칭 | `skill-registry.js match "html-mockup"` 및 `match "mockup"` | 둘 다 `found:true` + 같은 SKILL.md 경로 반환 |
| V-7 | 한글 화면명 입력 | "로그인 화면 만들어줘" | transliteration 결과(`login-screen`) 제안 + 캡틴 수정 가능 흐름 |
| V-8 | 사전 와이어프레임 이미지 입력 | 호출 시 `.png` 첨부 | Read로 이미지 로드 → 시각 구조 반영 + 입력 자원 인터뷰 단계 자동 스킵 |

## 범위 밖 (Out-of-scope)

| # | 항목 | 사유 |
|---|------|------|
| O-1 | 오프라인 환경 보장 | CDN 의존이 본 스킬의 정체성. 오프라인 지원은 별도 모드/태스크에서 다룬다. |
| O-2 | 자동 미리보기 / 스크린샷 첨부 | 확정 설계 §6 — "저장만". 캡틴이 직접 브라우저로 확인. |
| O-3 | 빌드 도구(npm/vite/webpack 등) 통합 | "빌드 0"이 본 스킬의 핵심 정체성. |

## 제약 조건

- 빌드 0(npm/yarn 등 패키지 매니저 의존 없음). 모든 자원은 CDN 또는 `shared/` 정적 파일.
- file:// 스킴(브라우저로 파일 직접 열기)에서도 정상 작동해야 함 — 상대 경로 사용, 외부 fetch 시 file:// CORS 고려.
- 한글 폰트 가독성 확보 (Pretendard, Noto Sans KR 등 CDN 권장).
- OPAL `~/.opal/` 직접 수정 금지 (확정 기준 #2). 모든 변경은 이 프로젝트 소스에서 수행.
- 배포 행위 금지 (PM 금지사항). install-mac.sh 실행은 캡틴 명시 지시 필요.
- 커뮤니티 스킬 원본 수정 금지 (PM 금지사항) — 본 태스크와 무관하지만 일반 원칙으로 유지.

## 기술 스택

- 산출물 자체: 정적 HTML + Tailwind CSS (CDN) + DaisyUI (CDN) + Alpine.js (CDN) + Lucide Icons (CDN)
- 스킬 메타: Markdown (SKILL.md), YAML frontmatter
- 보조 도구: `node ~/.opal/tools/skill-registry/skill-registry.js` (스킬 레지스트리)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PROJECT.md | `docs/PROJECT.md` | 폴더 구조맵 + 네이밍 규칙 (skills/ 위치 근거) |
| D-2 | 설계 | skill-commands.md | `~/.opal/references/harness/skill-commands.md` | `//` 호출 인프라 + 레지스트리 매칭 절차 |
| D-3 | 소스 | op-task SKILL.md | `~/.opal/skills/op-task/SKILL.md` | 인터뷰 스킬 연동 패턴 + interview 탐색 경로 |
| D-4 | 설계 | AGENT.md (프로젝트) | `.opal/AGENT.md` | PM 검토 기준 + 금지사항 (install-mac.sh 동기화, 배포 행위 금지) |
| D-5 | 외부 | DaisyUI | [DaisyUI](https://daisyui.com/) | 컴포넌트 클래스 라이브러리 (토큰 절약) |
| D-6 | 외부 | Alpine.js | [Alpine.js](https://alpinejs.dev/) | 선언적 인터랙션 |
| D-7 | 외부 | Lucide Icons | [Lucide](https://lucide.dev/) | SVG 아이콘 자동 치환 |
| D-8 | 외부 | Tailwind CDN | [Tailwind CDN](https://tailwindcss.com/docs/installation/play-cdn) | 빌드 없는 유틸리티 CSS |
