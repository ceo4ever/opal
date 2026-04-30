---
name: html-mockup
description: |
  **CDN 기반 정적 HTML 화면 빠른 생성 스킬**. 태스크 컨텍스트 자동 흡수 + 인터뷰로 화면 1~수개를 생성한다.
  반드시 이 스킬을 사용해야 하는 상황: "화면 만들어줘", "목업 만들어줘", "HTML로 빠르게 보여줘", 와이어프레임 검토용 정적 화면 필요 시.
  필수 입력: 저장 위치 (인터뷰). 보장 출력: HTML 화면 파일 + shared/ + 다중 시 index.html.
---

# html-mockup — CDN 기반 정적 HTML 화면 생성

> 빠른 목업(mockup) = 정적 HTML + CDN 스택. 빌드 불필요, 브라우저에서 바로 열린다.
> "목업"은 빠른 검토용 정적 화면, "프로토타입"은 풀 인터랙션 UI(→ ui-designer 스킬)와 구분.

---

## 0. 호출 환경

| 항목 | 값 |
|------|---|
| 호출 명령 | `//html-mockup` 또는 `//mockup` |
| 별칭 | `mockup` |
| 호출 가능 모드 | 비서(Assistant) / 태스크(Task) / PM / 오케스트레이터 — 모드 무관 |
| 특이 사항 | OPAL 프로젝트 여부 불문 (비-OPAL cwd에서도 동작) |

(→ TASK §요구사항 R-1)

---

## 1. 프로세스

### Step 1: 환경 감지

| 순서 | 조건 | 판정 |
|------|------|------|
| 1 | cwd에 `.opal/AGENT.md` 존재? | Yes → OPAL 프로젝트 |
| 2 | cwd 또는 상위에 `tasks/{NNN}-*/TASK.md` 패턴 존재? | Yes → 태스크 폴더 |
| 3 | STATE.md 또는 MEMORY.md 존재? | Yes → 세션 컨텍스트 폴백 |
| 4 | 위 모두 없음 | 비-OPAL / 컨텍스트 없음 |

### Step 2: 컨텍스트 흡수

감지 결과에 따라 아래 자원을 Read하여 화면 설계 힌트를 추출한다.

| 환경 | 흡수 자원 | 추출 내용 |
|------|---------|---------|
| OPAL 프로젝트 + 태스크 폴더 | `TASK.md`, `ANALYSIS.md` (있으면), `PLAN.md` (있으면) | 화면 목록, 핵심 기능, 데이터 구조 |
| OPAL 프로젝트 (태스크 폴더 없음) | `STATE.md`, `MEMORY.md` | 진행 중 컨텍스트 |
| 비-OPAL | (없음) | 흡수 스킵 → 인터뷰 전체 수행 |

추론 가능한 항목(화면 종류, 핵심 데이터 등)은 인터뷰에서 스킵하고 `"{항목}은 컨텍스트에서 {추론값}으로 자동 결정. 변경하시려면 알려주세요."` 1줄 통지로 대체.

(→ TASK §확정 §2, R-2)

### Step 3: 인터뷰

interview 스킬을 호출하여 부족분만 묻는다.

**interview 스킬 탐색 경로 (우선순위 순)**:
1. `{project}/.opal/skills/interview/SKILL.md`
2. `~/.opal/skills/interview/SKILL.md`
3. (미존재 폴백) 인라인 폴백 — 저장 위치 1문 + 핵심 항목 1~2문으로 최소 인터뷰 수행

**7단계 인터뷰 질문 (한 라운드 3~4문 묶음 — interview SKILL.md §라운드 규칙 준수)**:

| # | 단계 | 질문 | 옵션/형식 | 스킵 조건 |
|---|------|------|----------|---------|
| 1 | 저장 위치 | "HTML 화면을 저장할 위치는?" | multipleChoice: `["현재 태스크 폴더의 mockup/", "현재 cwd 직속 mockup/", "직접 입력"]` | **필수 — 스킵 불가** |
| 2 | 화면 종류·개수 | "어떤 화면을 몇 개 만들까요? (예: 로그인 / 대시보드 / 설정 — 3개)" | freeText | TASK.md/PLAN.md에서 화면 식별 가능 시 스킵 |
| 3 | 핵심 액션·데이터 | "각 화면에서 보여줄 핵심 액션이나 데이터 예시가 있나요?" | freeText (선택, "없음" 허용) | 컨텍스트에서 핵심 설계 추론 가능 시 스킵 |
| 4 | 분리 모드 | "화면 구성 방식은?" | multipleChoice: `["화면별 분리 (기본)", "단일 파일에 섹션으로 묶기"]` | 화면 1개 → 자동 단일 파일 — 스킵 |
| 5 | UI 라이브러리 | "UI 컴포넌트 라이브러리는?" | multipleChoice: `["DaisyUI (기본 추천)", "Flowbite", "없음 (Tailwind만)"]` | 사전 지시 시 스킵 |
| 6 | 다크모드 | "다크모드 토글이 필요한가요?" | multipleChoice: `["아니오 (기본)", "예 — DaisyUI 테마 토글 사용"]` | 사전 지시 시 스킵 |
| 7 | 입력 자원 | "참고할 와이어프레임 이미지·Figma URL·참고 사이트가 있나요?" | freeText (선택, "없음" 허용) | 호출 시 사전 첨부됨 → 자동 스킵 |

라운드 묶기 권장: **R1**(1~3), **R2**(4~6), **R3**(7). 컨텍스트 자동 흡수가 충분하면 R1만으로 종결 가능.

(→ TASK §요구사항 R-3, R-19)

### Step 4: 입력 자원 처리

| 입력 종류 | 처리 방법 | 자동 스킵 조건 |
|---------|---------|-------------|
| 이미지 (와이어프레임/스크린샷) | Read 도구로 이미지 분석 → 레이아웃·컴포넌트 추출 | 인터뷰 7단계 자동 스킵 |
| Figma URL | WebFetch 도구로 페이지 내용 분석 (미리보기 또는 임베드) | 인터뷰 7단계 자동 스킵 |
| 참고 사이트 URL | WebFetch 도구로 구조 분석 | 인터뷰 7단계 자동 스킵 |
| 텍스트 설명 | 요구사항 파싱 → 화면 구성 추론 | 컨텍스트로 대체 |

(→ TASK §요구사항 R-17)

### Step 5: 산출물 생성

#### 5-1. 보일러플레이트 적용 (화면마다 반복)

```
read_template = Read("skills/html-mockup/templates/boilerplate.html")
filled = read_template
  .replace("{{TITLE}}", title)
  .replace("{{BODY}}", body_markup)
  .replace("{{NAV}}", nav_markup or "")
  .replace("{{EXTRA_HEAD}}", extra_head or "")
Write("{저장위치}/{화면파일명}.html", filled)
```

#### 5-2. 화면명 → 파일명 변환 (§5 파일명 규칙 참조)

#### 5-3. 다중 화면 시 인덱스 페이지 자동 생성 (§6 인덱스 페이지 참조)

#### 5-4. shared/ 폴더 복사

```
Copy "skills/html-mockup/templates/shared/" → "{저장위치}/shared/"
```

(→ TASK §요구사항 R-4, R-6, R-11, R-12, R-13)

### Step 6: 보고

| 시나리오 | 보고 형식 |
|---------|---------|
| 단일 화면 신규 | "✅ `{저장위치}/{파일명}.html` 생성 완료. 브라우저에서 바로 열 수 있습니다." |
| 다중 화면 신규 | "✅ {N}개 화면 생성 완료. `{저장위치}/index.html`로 전체 목록 확인 가능." |
| 반복 수정 | "✅ `{파일명}.html` 덮어쓰기 완료. 변경 내용: {요약}" |

(→ TASK §요구사항 R-18)

---

## 2. 산출물 구조

### 저장 트리 (다중 화면 예시)

```
{저장위치}/
├── index.html           ← 화면 인덱스 (2개+ 시 자동 생성)
├── login.html
├── dashboard.html
├── settings.html
└── shared/
    ├── style.css        ← 공통 스타일 (Pretendard 폰트 매핑 등)
    └── main.js          ← 공통 JS (Lucide 초기화, Alpine store)
```

### 외부 분리 원칙

- `shared/style.css`, `shared/main.js`는 모든 화면에서 공유 (`./shared/` 상대 경로)
- 화면 전용 스타일/스크립트는 해당 HTML 파일 내 `<style>` / `<script>` 인라인으로 추가
- `nav.html` 등 fetch 기반 공용 조각(fragment)은 `file://` 환경에서 CORS 차단 가능성 있음 — 사용 시 주의 명시

(→ TASK §요구사항 R-4)

---

## 3. 기본 기술 스택

### CDN 핀 정책 표

| 라이브러리 | CDN URL | 버전 핀 | 역할 |
|-----------|--------|--------|------|
| Pretendard | `https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css` | `@v1.3.9` | 한글 폰트 |
| Tailwind CSS | `https://cdn.tailwindcss.com` | latest (Play CDN) | 유틸리티 CSS |
| DaisyUI | `https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css` | `@4` | 컴포넌트 |
| Alpine.js | `https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js` | `@3` | 선언적 인터랙션 |
| Lucide | `https://unpkg.com/lucide@latest/dist/umd/lucide.min.js` | latest | SVG 아이콘 |

> **핀 정책**: 메이저 버전 핀 (`@4`, `@3`) 기본 적용. 메이저 업그레이드(DaisyUI 5, Alpine 4 등) 시 SKILL.md 별도 업데이트 태스크로 처리.

### 대안

| 케이스 | 대안 스택 |
|--------|---------|
| DaisyUI 불필요 | Tailwind만 사용 — DaisyUI CDN 제거 |
| 더 풍부한 컴포넌트 | Flowbite CSS + JS CDN 추가 |

(→ TASK §요구사항 R-5, R-14)

---

## 4. 보일러플레이트

파일 위치: `skills/html-mockup/templates/boilerplate.html`

### 치환 토큰 4종

| 토큰 | 위치 | 필수/선택 | 예시 값 |
|------|------|---------|--------|
| `{{TITLE}}` | `<title>` 태그 내 | 필수 | `로그인 — html-mockup` |
| `{{BODY}}` | `<body>` 안 마크업 영역 | 필수 | 화면별 DaisyUI 마크업 전문 |
| `{{NAV}}` | `<body>` 시작 직후 | 선택 | sticky navbar 마크업 (단일 파일 모드) — 미사용 시 빈 문자열 |
| `{{EXTRA_HEAD}}` | `<head>` 끝 직전 | 선택 | 다크모드 ON 시 `<html data-theme="dark">` 변환 또는 화면 전용 인라인 CSS — 미사용 시 빈 문자열 |

### 사용 절차

```
1. Read("skills/html-mockup/templates/boilerplate.html")
2. replace("{{TITLE}}", 화면 제목)
3. replace("{{BODY}}", 화면 DaisyUI 마크업)
4. replace("{{NAV}}", nav_markup or "")
5. replace("{{EXTRA_HEAD}}", extra_head or "")
6. Write("{저장위치}/{파일명}.html", 결과)
```

(→ TASK §요구사항 R-11)

---

## 5. 파일명 규칙

### 변환 알고리즘

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
output = lowercase + ASCII + hyphen-only  # file:// URL 호환성
```

> **주의**: Hangul Romanization 발음 변환 사용 금지. AI가 의미 기반으로 영문 제안 후 사용자 확인.

### 변환 예시

| 입력 | 결과 파일명 |
|------|----------|
| `Login` | `login.html` |
| `My Dashboard` | `my-dashboard.html` |
| `로그인` | `login.html` (AI 제안, 자동 확인) |
| `대시보드` | `dashboard.html` (AI 제안, 자동 확인) |
| `회원 목록 관리` | `member-list.html` (AI 제안 → 사용자 확인) |

(→ TASK §요구사항 R-12)

---

## 6. 인덱스 페이지 자동 생성

| 화면 수 | 처리 |
|--------|------|
| 1개 | index.html 생성 안 함 |
| 2개 이상 | `{저장위치}/index.html` 자동 생성 (DaisyUI card 그리드) |

인덱스 페이지 템플릿: `skills/html-mockup/templates/index.html.tmpl`

그리드 레이아웃: 모바일 1열 / md(768px+) 2열 / lg(1024px+) 3열

각 카드:
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

(→ TASK §요구사항 R-13)

---

## 7. 디자인 정책

| 항목 | 기본값 | 변경 방법 |
|------|--------|---------|
| 반응형 | **ON** (모바일 우선) | 항상 활성 — 비활성화 불가 |
| 다크모드 | **OFF** (light 테마) | 인터뷰 6단계에서 ON 선택 → `<html data-theme="dark">` |
| 폰트 | Pretendard + 시스템 폴백 | 인터뷰에서 변경 가능 |
| 색상 테마 | DaisyUI 기본 light | 화면별 `data-theme` 속성으로 변경 |

다크모드 ON 시: `boilerplate.html`의 `<html>` 태그에 `data-theme="dark"` 추가 (`{{EXTRA_HEAD}}` 토큰으로 처리하지 않고 `<html>` 태그 직접 수정).

(→ TASK §요구사항 R-15)

---

## 8. 반복 수정

| 시나리오 | 감지 방법 | 처리 |
|---------|---------|------|
| 같은 호출 안에서 수정 | 인터뷰 컨텍스트에 "수정"/"바꿔"/"고쳐"/"바꿔줘"/"modify"/"update"/"change"/"fix" 포함 | 자동 덮어쓰기 |
| 새 호출에서 파일명 충돌 | 저장 위치에 이미 같은 파일명 존재 + 수정 키워드 없음 | AskUserQuestion으로 확인 |
| `index.html` 충돌 | 다중 화면 자동 생성 시마다 | 항상 자동 덮어쓰기 (선언적 결과) |

> CHANGELOG, 백업 파일, 버전 suffix 등은 생성하지 않는다.

(→ TASK §요구사항 R-7)

---

## 9. 에러 처리

| 케이스 | 질문/처리 | 옵션 |
|--------|---------|------|
| 다른 호출 파일명 충돌 | "`{파일명}.html`이 이미 존재합니다. 어떻게 할까요?" | `["덮어쓰기 (수정)", "다른 이름으로 저장 (입력)", "취소"]` |
| 한글 화면명 변환 확인 | "화면명 `{한글입력}` → `{ai_제안_영문}.html`로 저장할까요?" | `["예", "직접 입력", "다른 후보 제안"]` |
| 권한 부족 | 즉시 에스컬레이션 — "저장 위치 `{경로}`에 쓰기 권한이 없습니다. 다른 위치를 지정하세요." | freeText |
| CDN 도달 불가 | 작성은 계속 진행 + 1줄 안내 — "CDN 접근 불가 환경에서는 로컬 실행 시 스타일이 적용되지 않을 수 있습니다." | — |
| 저장 위치가 파일임 | "`{경로}`가 파일로 존재합니다. 다른 위치를 지정하세요." | freeText |

(→ TASK §요구사항 R-16)

---

## 10. [MUST] 제약

> 재해석 금지 — 원문 그대로 인용.

- [MUST] `~/.opal/references/skills.md` §스킬 도구 사용법: "스킬 메타데이터는 JSON 레지스트리가 SSOT이다." — 스킬 추가/수정 시 `opal/core/references/opal-skills-registry.json`만 수정. `~/.opal/` 직접 수정 금지.

- [MUST] `.opal/AGENT.md` §확정 기준 #2: "`~/.opal/` 경로 파일을 Edit/Write하지 않는다. 수정 대상은 반드시 소스 경로에서 찾아 수정한다." — 본 스킬 실행 중 어떤 파일도 `~/.opal/` 경로에 직접 생성/수정하지 않는다. 배포는 캡틴 권한.

- [MUST] `.opal/AGENT.md` §금지사항: "배포 행위 금지: install-mac.sh 실행, ~/.opal/에 파일 직접 복사/생성/수정 금지." — html-mockup 스킬은 캡틴 명시 지시 없이 install-mac.sh 실행 또는 배포 행위를 트리거하지 않는다.

---

## 부속 A: 저장 위치 처리 흐름

```
if not exists(저장위치):
    if writable(parent(저장위치)):
        mkdir -p 저장위치
    else:
        escalate("권한 없음 — 다른 위치 지정 필요")
elif not is_dir(저장위치):
    escalate("동일 이름의 파일 존재 — 다른 위치 지정 필요")
else:
    # 폴더 존재 → 안의 파일은 §9 에러 처리 분기로 위임
    use 저장위치
```

---

## 부속 B: 단일 파일 모드 골격

인터뷰 4단계에서 "단일 파일에 섹션으로 묶기" 선택 시 또는 화면 1개일 때:

- 각 화면을 `<section id="screen-{slug}">` 으로 감싼다
- 파일 상단에 sticky top nav 삽입 — DaisyUI `navbar` + `tabs-boxed` 컴포넌트
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

> `tabs-boxed`는 DaisyUI v4 정확 클래스명 (PM이 v4 공식 문서 직접 검증).

---

## 부속 C: 인터뷰 스킬 미존재 폴백

`{project}/.opal/skills/interview/SKILL.md`와 `~/.opal/skills/interview/SKILL.md` 모두 없을 때:

1. 저장 위치 1문 (필수)
2. 화면 종류·개수 1문
3. 핵심 액션·데이터 + UI 라이브러리 묶어서 1문 (선택)

총 2~3문으로 최소 인터뷰 수행. AskUserQuestion 도구 직접 사용.
