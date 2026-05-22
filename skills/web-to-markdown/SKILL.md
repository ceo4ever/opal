---
name: web-to-markdown
description: |
  **웹 페이지를 마크다운으로 변환하는 스킬**. URL을 입력받아 웹 콘텐츠를 정제된 .md 파일로 변환하여 AI 에이전트가 바로 활용할 수 있게 한다.
  반드시 이 스킬을 사용해야 하는 상황: "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와", "사이트 분석해줘", "링크 내용 정리해줘", "웹 콘텐츠 추출".
  URL을 주면서 내용을 파악하거나 정리해달라는 요청이 있으면 이 스킬을 사용한다. Phase 1(cmux-tool) → Phase 2(playwright-tool) 2단 폴백 전략으로 안정적으로 처리한다.
---

# 웹 페이지 마크다운 변환 스킬

> 작성일: 2026-03-20 | 버전: v2.0

URL을 입력받아 웹 페이지 콘텐츠를 정제된 마크다운(.md)으로 변환한다. Phase 1(cmux-tool) → Phase 2(playwright-tool CLI) 2단 폴백 전략으로 다양한 웹 페이지를 안정적으로 처리하고, 복수 URL은 서브에이전트로 병렬 처리한다. WebFetch는 제거되었다 (M-1 (a)안 — 단순성 우선).

---

## 호출 인터페이스

> 다른 스킬·에이전트·PM이 이 스킬을 호출할 때 참조한다.

### 사용자/PM 호출 (쌍슬래시 커맨드)

```
//wtm {url}                                # 단일 URL, full 모드, Phase 1(cmux)→2(playwright)
//wtm {url1} {url2} {url3}                 # 복수 URL, 병렬 처리
//wtm --browser {url}                      # deprecated alias — 기본 동작과 동일 (2단 체인)
//wtm --browser {url1} {url2}              # browser 모드 + 복수 URL (deprecated alias)
//wtm --surface <handle>                   # 현재 페이지(B 모드) — navigate 안 함, cleanup 금지
//wtm --surface <handle> {url}             # surface 재사용 + navigate(C 모드)
//wtm --wait <ms> {url}                    # wait ms 지정 (기본 2000, 0=생략)
//wtm --clean {url}                        # 본문만
//wtm --wireframe {url}                    # 와이어프레임
```

### 에이전트 디스패치 (Agent prompt 예시)

단일 URL:
```
이 스킬(web-to-markdown)을 사용해 아래 URL을 마크다운으로 변환해줘.
URL: {url}
모드: {full|clean|wireframe|browser}
저장 경로: {path}
```

복수 URL (병렬):
```
이 스킬(web-to-markdown)을 사용해 아래 URL 목록을 마크다운으로 변환해줘.
URL 목록:
  - {url1} → {save-path1}
  - {url2} → {save-path2}
모드: {full|clean|browser}
각 URL은 서브에이전트로 병렬 처리한다.
```

### 입출력 요약

| 항목 | 내용 |
|------|------|
| 입력 | URL 1개 이상, 모드 (기본: full) |
| 출력 | `{slug}.md` 파일 (산출물 형식 섹션 참조) |
| 저장 경로 | 사용자 지정 > 태스크 폴더 > `/tmp/web-to-markdown/` |
| 복수 URL | 자동 병렬 처리 (2~5개), browser 모드도 병렬 허용 |

---

## 추출 모드

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **full** (기본) | 전체 콘텐츠 보존. nav, sidebar, header, footer 등 구조 요소를 유지한다. 메뉴 구조, 내비게이션 링크 등 유용한 정보가 보존된다. | 사이트 구조 파악, 메뉴/링크 수집, 전체 페이지 아카이빙 |
| **clean** | 본문만 추출. nav, header, footer, sidebar, 광고 등 비본문 요소를 제거한다. | 본문 콘텐츠만 필요할 때, 문서/블로그 아티클 추출 |
| **wireframe** | 와이어프레임 분석. 화면 구조, 구성요소, 기능 동작, 네비게이션, 데이터 I/O를 구조화된 기획 관점으로 추출한다. | 와이어프레임 HTML을 기획 문서로 변환할 때, opwt 정책서/IA 작성 시 참조 |
| **--browser** | **deprecated alias — 기본 동작과 동일 (2단 체인)**. Phase 1(cmux-tool) → Phase 2(playwright-tool CLI). 하위 호환 목적으로 유지. | 기존 --browser 호출 호환성 (신규 사용 불필요) |
| **--surface \<handle\>** | B 모드 (현재 페이지). Phase 1(cmux-tool)으로 즉시 진입, navigate 안 함, cleanup 절대 금지. | cmux surface 재사용, 인증 세션 활용 |
| **--surface \<handle\> {url}** | C 모드 (surface 재사용 + navigate). Phase 1(cmux-tool) goto 호출. | surface 재사용하며 다른 URL 이동 |

사용자가 모드를 명시하지 않으면 **full** 모드를 적용한다. "본문만", "내용만", "clean" 등의 키워드가 있으면 clean 모드를 적용한다. "와이어프레임", "wireframe", "화면 분석", "기획 분석" 등의 키워드가 있으면 wireframe 모드를 적용한다.

`--browser`, "브라우저로", "browser", "로컬" 등의 키워드가 있거나,
URL 호스트가 `localhost`, `127.0.0.1`, `[::1]`인 경우 `browser` 모드를 자동 적용한다.
(`browser`와 `--browser` 둘 다 허용한다 — deprecated alias로 유지, 기본 동작과 동일.)
browser 모드에서는 기본 동작과 동일하게 Phase 1(cmux-tool) → Phase 2(playwright-tool CLI) 2단 체인을 수행한다.

---

## 실행 흐름

```
URL/--surface 입력 (단일 또는 복수)
  │
  ├─ 단일 URL/surface → 직접 처리
  │     │
  │     ├─ [silent fallback 분기] command -v cmux 검사
  │     │     ├─ cmux 감지 → Phase 1 시도
  │     │     └─ cmux 미감지 → Phase 1 skip → Phase 2 직행 (사용자 안내 없음)
  │     │
  │     ├─ Phase 1: cmux-tool (1순위)
  │     │     ├─ bash ~/.opal/tools/cmux-tool/run.sh (모드 A/B/C)
  │     │     ├─ {"ok": true} → content 정제 → 저장
  │     │     ├─ {"ok": false, "error": "not_in_cmux|cmux_not_installed|surface_parse_failed|open_failed"}
  │     │     │       → Phase 2 폴백
  │     │     └─ {"ok": false, "error": "usage|invalid_surface|goto_failed|wait_failed|eval_failed"}
  │     │             → 즉시 에스컬레이션 (status: blocked)
  │     │
  │     └─ Phase 2: playwright-tool CLI (fallback)
  │           ├─ bash ~/.opal/tools/playwright-tool/run.sh {url} --mode {mode}
  │           ├─ {"ok": true} → content 정제 → MD 저장
  │           └─ run.sh 미설치 → 설치 안내 후 중단
  │
  └─ 복수 URL → 서브에이전트 병렬 디스패치
        ├─ URL별 서브에이전트 1개씩 생성
        ├─ 각 에이전트가 위 단일 URL 프로세스 실행
        └─ 전체 완료 후 결과 요약 보고
```

---

## Phase 1: cmux-tool (1순위)

cmux browser 자동화 래퍼로 URL을 가져온다. cmux 미설치 시 silent fallback으로 Phase 2로 즉시 이동한다.

### silent fallback 분기

Phase 1 진입 직전 `opal-wtm-agent`가 단일 분기로 cmux 감지를 확인한다:

```bash
if command -v cmux >/dev/null 2>&1; then
  # Phase 1: cmux-tool 시도
else
  # cmux 미감지 → Phase 2 직행 (사용자 안내 없음)
fi
```

### 실행

```bash
bash ~/.opal/tools/cmux-tool/run.sh <url|--surface <handle> [url]> [--mode <m>] [--wait <ms>]
```

- A 모드 (`url` 단독): 신규 surface 열기 → 추출 후 tab close
- B 모드 (`--surface <handle>`): 현재 페이지 추출 (cleanup 절대 금지)
- C 모드 (`--surface <handle> <url>`): surface 재사용 + navigate (cleanup 절대 금지)

JSON 출력 파싱:
- `{"ok": true, "content": "..."}` → content 정제 → 저장
- `{"ok": false, "error": "not_in_cmux|cmux_not_installed|surface_parse_failed|open_failed"}` → Phase 2로 폴백
- `{"ok": false, "error": "usage|invalid_surface|goto_failed|wait_failed|eval_failed"}` → 즉시 에스컬레이션

### cmux 설치 안내 (사용자 명시 요청 시만)

- 공식 사이트: https://cmux.com/
- GitHub: https://github.com/manaflow-ai/cmux

### 추출 방식 표기

산출물 형식의 `추출 방식` 필드에 `cmux (모드 A|B|C)`로 표기한다.

---

## Phase 2: playwright-tool CLI (fallback)

JavaScript 렌더링이 필요한 페이지를 playwright-tool CLI로 처리한다. cmux 미감지(silent) 또는 Phase 1 폴백 트리거 4종 수신 시 진입한다.

### CLI 설치 확인

```bash
ls ~/.opal/tools/playwright-tool/run.sh 2>/dev/null || echo "NOT_FOUND"
```

`NOT_FOUND` 출력 시 아래 "playwright-tool 미설치 시" 안내를 따른다.

### 실행

1. `~/.opal/tools/playwright-tool/run.sh` 경로 확인
2. Bash 호출:
   ```bash
   bash ~/.opal/tools/playwright-tool/run.sh {url} --mode {full|clean}
   ```
3. JSON 출력 파싱: `{"ok": true, "content": "..."}`
4. `content`를 "콘텐츠 추출 및 MD 정제" 규칙에 따라 최종 정제
5. `{slug}.md` 저장

실패 시: `{"ok": false, "error": "..."}` → 오류 사유 안내 후 중단

- **full 모드**: 전체 구조(nav, sidebar, header, footer)를 보존하며 Markdown으로 변환.
- **clean 모드**: 비본문 요소(nav, header, footer, sidebar, 광고)를 제거하고 본문만 추출.

### playwright-tool 미설치 시

사용자에게 설치 방법을 안내하고 중단한다:

```
playwright-tool CLI가 설치되어 있지 않습니다.
설치 방법: scripts/install-mac.sh 실행 후 옵션 1 (OPAL 설치) 선택
```

---

## Wireframe 모드

wireframe 모드는 기존 3단계 폴백 위에 분석 레이어를 추가하여 화면을 기획 관점으로 구조화한다.

### 실행 로직

```
URL 입력 (wireframe 모드)
  │
  ├─ 2단 폴백으로 콘텐츠 취득 (full 모드 기반)
  │   Phase 1: cmux-tool → Phase 2: playwright-tool CLI (fallback)
  │
  └─ 분석 레이어 적용
        ├─ 화면 개요 추출 (타이틀, 목적, URL 경로)
        ├─ 구성요소 분석 (헤더, 메인, 사이드바, 푸터 등 영역별)
        ├─ 기능 동작 분석 (버튼, 폼, 인터랙션 요소)
        ├─ 네비게이션 구조 (링크, 메뉴, 브레드크럼)
        └─ 데이터 I/O 정의 (입력 필드, 출력 데이터, API 호출 추정)
```

### Phase 1 cmux-tool 지시 (wireframe 전용)

cmux-tool로 전체 HTML을 취득한 후 아래 기획 관점 분석 레이어를 적용한다:

```
분석 지시: 이 와이어프레임 페이지를 기획 관점에서 분석해줘.
전체 HTML 구조를 보존하면서, 화면 구성요소(헤더, 메인, 사이드바, 푸터),
버튼/폼/링크 등 인터랙션 요소, 네비게이션 링크, 입출력 필드를 식별해줘.
```

### 산출물 형식

```markdown
# 와이어프레임 분석: {페이지 타이틀}

> 소스: {URL}
> 캡처일: {YYYY-MM-DD HH:mm}
> 추출 방식: {cmux (모드 A|B|C) | playwright-tool CLI}
> 추출 모드: wireframe

---

## 1. 화면 개요

| 항목 | 내용 |
|------|------|
| 화면명 | {페이지 타이틀} |
| URL 경로 | {URL path} |
| 화면 목적 | {1줄 요약} |
| 접근 권한 | {public / member / admin — 추정} |

## 2. 화면 구성요소

### 2.1 헤더 영역
- {구성요소 목록}

### 2.2 메인 콘텐츠 영역
- {구성요소 목록}

### 2.3 사이드바 (있는 경우)
- {구성요소 목록}

### 2.4 푸터 영역
- {구성요소 목록}

## 3. 기능 동작

| # | 기능명 | 유형 | 동작 설명 | 조건/제약 |
|---|--------|------|----------|----------|
| 1 | {기능} | 버튼/폼/링크/토글 등 | {동작 설명} | {조건} |

## 4. 네비게이션

| 출발 | 도착 | 트리거 | 비고 |
|------|------|--------|------|
| {현재 화면} | {대상 화면} | {클릭/제출 등} | {조건부 등} |

## 5. 데이터 I/O

### 입력 (Input)
| # | 필드명 | 타입 | 필수 | 검증 규칙 |
|---|--------|------|------|----------|

### 출력 (Output)
| # | 데이터 | 소스 | 표시 형식 |
|---|--------|------|----------|
```

### 저장 경로 규칙

아래 우선순위로 결정한다:

| 순위 | 조건 | 경로 |
|------|------|------|
| 1 | 사용자 지정 경로 | 사용자가 명시한 경로 |
| 2 | PROJECT.md 문서 테이블에 와이어프레임 경로 존재 | 해당 경로 |
| 3 | 그 외 기본값 | `docs/wireframes/` |

### 네이밍 규칙

URL 경로 기반 kebab-case로 파일명을 생성한다:

- `/login` → `login.md`
- `/mypage/order` → `mypage-order.md`
- 도메인은 제외하고 경로 세그먼트만 사용

### 인덱스 자동 생성

복수 URL 처리 시 저장 경로에 `_index.md`를 자동 생성/갱신한다.

```markdown
# 와이어프레임 인덱스

> 생성일: {YYYY-MM-DD HH:mm}
> 총 {N}개 화면

| # | 화면명 | URL 경로 | 파일 | 접근 권한 |
|---|--------|---------|------|----------|
| 1 | {화면명} | {path} | {filename}.md | {권한} |
```

---

## 콘텐츠 추출 및 MD 정제

모든 Phase에서 아래 정제 규칙을 적용한다. Phase 2(cmux) 및 Phase 3(playwright-tool CLI)는 content 필드로 HTML/Markdown을 직접 반환하므로 추가 정제만 수행한다.

**중요**: 어떤 Phase를 거치든 최종 산출물은 반드시 아래 "산출물 형식"을 따르는 .md 파일이어야 한다. 중간 파일(.txt, .html 등)을 생성하지 않는다.

### 공통 제거 대상 (full/clean 모두)

- `<script>`, `<style>`, `<noscript>`, `<iframe>` 태그
- 쿠키 배너, 팝업 오버레이
- 트래킹 픽셀, 빈 링크
- 인라인 스타일 속성

### clean 모드 추가 제거 대상

clean 모드에서만 아래 요소를 추가로 제거한다:

- `<nav>`, `<header>`, `<footer>`, `<aside>` 태그 및 내용
- `role="navigation"`, `role="banner"`, `role="contentinfo"` 요소
- 클래스명에 `nav`, `menu`, `sidebar`, `footer`, `header`, `ad` 포함 요소
- 소셜 공유 버튼, 관련 글 추천 영역

### MD 변환 규칙

| HTML | Markdown |
|------|----------|
| `<h1>`~`<h6>` | `#`~`######` |
| `<p>` | 빈 줄로 구분된 단락 |
| `<a href="url">text</a>` | `[text](url)` |
| `<img src="url" alt="text">` | `![text](url)` |
| `<ul>/<ol>` | `-` / `1.` 리스트 |
| `<table>` | Markdown 테이블 |
| `<code>`, `<pre>` | 인라인 코드 / 코드 블록 |
| `<strong>`, `<b>` | `**bold**` |
| `<em>`, `<i>` | `*italic*` |

### 산출물 형식

```markdown
# {페이지 타이틀}

> 소스: {URL}
> 캡처일: {YYYY-MM-DD HH:mm}
> 추출 방식: {cmux (모드 A|B|C) | playwright-tool CLI}
> 추출 모드: {full | clean}

---

{마크다운 콘텐츠}
```

---

## 저장 경로 (우선순위)

산출물 저장 경로를 아래 우선순위로 결정한다:

| 순위 | 조건 | 경로 |
|------|------|------|
| 1 | 사용자 지정 경로 | 사용자가 명시한 경로 |
| 2 | 태스크 작업 중 | `{task-folder}/references/{slug}.md` |
| 3 | 그 외 | `/tmp/web-to-markdown/{slug}.md` |

### slug 생성 규칙

URL에서 도메인과 경로를 조합하여 kebab-case slug를 생성한다:

- `https://docs.example.com/api/v2/auth` → `docs-example-com-api-v2-auth`
- 최대 80자, 초과 시 뒤에서 truncate
- 동일 slug 존재 시 `{slug}-{n}.md` (n=2,3,...)

### 태스크 폴더 감지

현재 작업 컨텍스트에서 태스크 폴더를 감지한다:

1. 현재 대화에서 사용 중인 태스크 경로 확인 (예: `tasks/{task-name}/`)
2. 해당 폴더 내 `references/` 디렉토리 존재 확인 (없으면 생성)
3. 태스크 폴더를 감지할 수 없으면 순위 3(임시 경로)으로 넘어간다

---

## 복수 URL 처리

2개 이상의 URL이 입력되면 서브에이전트로 병렬 처리한다.

### 워커 에이전트

**에이전트 이름**: `opal-wtm-agent`

탐색 경로 (우선순위):
1. `{프로젝트}/.opal/agents/opal-wtm-agent/AGENT.md`
2. `~/.opal/agents/opal-wtm-agent/AGENT.md`

### 처리 방식 선택 기준

| 조건 | 권장 방식 |
|------|----------|
| URL 수 2~5개, 서로 다른 호스트 | 서브에이전트 병렬 디스패치 |
| URL이 동일 호스트 | PM 직접 순차 수집 |
| URL 수 6개 이상 (browser 모드 제외) | PM 직접 순차 수집 |
| browser 모드 + 복수 URL | 에이전트 병렬 디스패치 허용 (각자 독립 브라우저 인스턴스) |

> 참조: opal-harness §7.4 Concurrency Limit — 합산 200KB 초과 또는 단일 50KB 초과 시
> 순차 실행 또는 Max 2개 병렬로 제한한다.

### 실행 방식

```
URL 목록 수신
  │
  ├─ URL 개수 확인
  │     ├─ 1개 → 직접 처리 (서브에이전트 불필요)
  │     └─ 2개 이상 → 서브에이전트 병렬 디스패치
  │
  └─ 서브에이전트 디스패치
        ├─ URL별 Agent 도구 호출 (동시 실행)
        │     prompt (기본 모드): "다음 URL의 웹 페이지를 마크다운으로 변환해줘.
        │              URL: {url}
        │              저장 경로: {save-path}
        │              모드: {mode}  ← full | clean | wireframe 중 하나를 명시
        │              Phase 1(WebFetch) 시도 후 실패하면 Phase 2(playwright-tool CLI)로 폴백.
        │              wireframe 모드인 경우 취득한 콘텐츠에 분석 레이어를 적용하여 산출물을 생성해줘.
        │              결과를 {save-path}에 저장하고, 성공 여부와 사용한 방식을 보고해줘."
        │     prompt (browser 모드): "다음 URL의 웹 페이지를 마크다운으로 변환해줘.
        │              URL: {url}
        │              저장 경로: {save-path}
        │              모드: {mode}
        │              browser 모드: playwright-tool CLI를 직접 호출하여 콘텐츠를 추출해줘.
        │              WebFetch 단계를 생략하고 즉시 CLI를 실행한다.
        │              결과를 {save-path}에 저장하고, 성공 여부와 사용한 방식을 보고해줘."
        │
        └─ 전체 완료 후 결과 종합
```

### PM 직접 순차 수집 패턴

PM(오케스트레이터)이 WebFetch를 직접 순차 호출하여 콘텐츠를 사전 수집하고,
수집된 Markdown 파일 경로를 워커에게 주입한다.

**동작 흐름:**
```
URL 목록 수신 (동일 호스트, URL 6개 이상)
  │
  ├─ PM이 URL별 순차 처리
  │     ├─ Phase 1: cmux-tool → 성공 시 Markdown 정제
  │     ├─ Phase 1 실패 시: bash ~/.opal/tools/playwright-tool/run.sh {url} --mode {mode}
  │     └─ {task-folder}/collected-refs/{slug}.md 저장
  │
  └─ 수집 완료 후 워커 병렬 디스패치
        prompt 예시: "다음 경로의 참조 문서를 활용하여 작업을 수행해줘.
                     참조 경로: {task-folder}/collected-refs/{slug}.md"
```

**사용 시나리오 비교:**
- 기존: URL 21개 → 에이전트 21개 → 각자 브라우저 인스턴스 생성 → 리소스 고갈
- 개선: PM이 직접 21회 순차 수집 → md 수집 → 워커 병렬 디스패치

**저장 경로:**
- `{task-folder}/collected-refs/{slug}.md`
- 태스크 폴더 감지 불가 시: `/tmp/web-to-markdown/collected-refs/{slug}.md`

### 결과 보고

```
[web-to-markdown 완료] {n}개 URL 처리

| # | URL | 방식 | 결과 | 저장 경로 |
|---|-----|------|------|----------|
| 1 | {url} | cmux (모드 A) | ✅ 성공 | {path} |
| 2 | {url} | cmux (모드 B) | ✅ 성공 | {path} |
| 3 | {url} | playwright-tool CLI | ✅ 성공 | {path} |
| 4 | {url} | cmux → playwright-tool CLI | ⚠️ 폴백 성공 | {path} |
```

### B/C 모드 결과 보고 (사용자 surface)

opal-wtm-agent가 B/C 모드로 추출한 경우, 반환 JSON의 `summary` 필드(2차 계층에서 자동 부착된 경고문 포함)를 사용자에게 **그대로** 노출한다. 경고문을 임의로 수정하거나 생략하지 않는다.

보고 형식 예시:

```
✅ web-to-markdown 완료 (Phase 1 cmux, mode=C)
📁 저장: {artifact_path}
⚠️  사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요
```

A 모드(신규 surface 또는 일반 URL)에서는 경고문을 노출하지 않는다 (`user_owned: false`).

---

## 에지 케이스 처리

| 상황 | 대응 |
|------|------|
| 인증 필요 (로그인 페이지 리다이렉트) | "이 URL은 로그인이 필요합니다" 안내 후 중단 |
| PDF URL | WebFetch로 처리, MD 변환은 제한적임을 안내 |
| 매우 긴 페이지 (10만자 초과) | 본문을 10만자에서 truncate, 안내 메시지 추가 |
| 리다이렉트 | 최종 URL을 따라가되, 메타정보에 원본+최종 URL 모두 기록 |
| robots.txt 차단 | 안내 후 중단 (강제 우회 금지) |
| 타임아웃 | Phase 1: 15초, Phase 2(playwright-tool CLI): 30초 후 실패 처리 |

---

## 의존성

### 필수/선택 도구

| 도구 | 필수 여부 | 필요 시점 | 미설치 시 동작 |
|------|----------|----------|--------------|
| `cmux` 0.64.3+ | 선택 | Phase 1 진입 시 (`command -v cmux` 감지) | silent fallback → Phase 2 직행 (안내 없음) |
| `playwright-tool` CLI | 필수 (OPAL 설치) | Phase 2 진입 시 (cmux 미감지 또는 Phase 1 실패) | 설치 안내 메시지 출력 후 즉시 중단 |
| Agent 도구 | 선택 | 복수 URL 병렬 처리 | — |

**사전 확인 규칙**: Phase 2 진입 전에 아래 Bash 명령으로 `run.sh` 파일 존재 여부를 확인한다. 미설치 확인 시 "playwright-tool 미설치 시" 안내를 즉시 출력하고 실행을 중단한다.

```bash
ls ~/.opal/tools/playwright-tool/run.sh 2>/dev/null || echo "NOT_FOUND"
```

cmux 설치:
- 공식 사이트: https://cmux.com/
- GitHub: https://github.com/manaflow-ai/cmux

playwright-tool 설치:
```bash
scripts/install-mac.sh → 옵션 1 (OPAL 설치)
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-20 | 초기 작성 — full/clean 듀얼 모드, 2단계 폴백(WebFetch→Playwright), 복수 URL 병렬 처리(wtm-agent) |
| v1.1 | 2026-03-20 | Phase 2 백엔드를 Playwright에서 Crawl4AI로 교체 — 마크다운 변환 내장, Anti-bot/stealth 지원 |
| v1.2 | 2026-04-01 | 3단계 폴백(WebFetch→Crawl4AI→Node Playwright), Phase 2 Python 버전 체크, 저장 경로 간소화, wtm 약어 등록 |
| v1.3 | 2026-04-01 | wireframe 모드 추가 — 기획 관점 화면 분석, 5섹션 산출물 형식, docs/wireframes/ 저장 경로, _index.md 자동 생성, 복수 URL 디스패치 시 모드 전달 명시 |
| v1.4 | 2026-04-02 | Phase 2를 Crawl4AI → Playwright MCP로 교체, Phase 3 Node Playwright 삭제, browser 모드 추가, PM 직접 순차 수집 패턴 추가 |
| v1.5 | 2026-04-03 | browser 모드 트리거 키워드 `--browser` 추가 (`browser` 하위 호환 유지) |
| v1.6 | 2026-04-03 | Phase 2 스냅샷 보관 단계 추가 — `/tmp/playwright-mcp/` → task 폴더 자동 복사, yml 재처리 지원 (078) |
| v1.7 | 2026-04-03 | Phase 2를 Playwright MCP → playwright-tool CLI로 교체, browser 모드 병렬 디스패치 허용, MCP 의존성 제거 (079) |
| v1.8 | 2026-04-03 | 호출 인터페이스 섹션 추가 — 쌍슬래시 커맨드, 에이전트 디스패치 예시, 입출력 요약 (079) |
| v1.9 | 2026-05-12 21:35 KST | 워커 에이전트 OPAL 표준화 (wtm-agent → opal-wtm-agent) + Phase 2 cmux 신설 (Phase 2 playwright → Phase 3 재번호) + `--surface <handle>` 3모드(A/B/C) + `--wait <ms>` 옵션 + Crawl4AI 잔존 참조 제거 (002) |
| v2.0 | 2026-05-22 10:00 KST | Phase 1(WebFetch) 완전 제거 → Phase 1(cmux-tool) / Phase 2(playwright-tool) 2단 체인 재번호. `--browser` deprecated alias로 표기 (기본 동작과 동일 — 하위 호환 유지). silent fallback 분기 다이어그램 추가. 의존성 표 갱신 (007) |
