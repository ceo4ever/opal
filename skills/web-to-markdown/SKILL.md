---
name: web-to-markdown
description: |
  **웹 페이지를 마크다운으로 변환하는 스킬**. URL을 입력받아 웹 콘텐츠를 정제된 .md 파일로 변환하여 AI 에이전트가 바로 활용할 수 있게 한다.
  반드시 이 스킬을 사용해야 하는 상황: "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와", "사이트 분석해줘", "링크 내용 정리해줘", "웹 콘텐츠 추출".
  URL을 주면서 내용을 파악하거나 정리해달라는 요청이 있으면 이 스킬을 사용한다. 단순 WebFetch로 충분한 경우에도 정제된 마크다운이 필요하면 이 스킬이 더 적합하다.
---

# 웹 페이지 마크다운 변환 스킬

> 작성일: 2026-03-20 | 버전: v1.1

URL을 입력받아 웹 페이지 콘텐츠를 정제된 마크다운(.md)으로 변환한다. 3단계 폴백 전략으로 다양한 웹 페이지를 안정적으로 처리하고, 복수 URL은 서브에이전트로 병렬 처리한다.

## 추출 모드

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **full** (기본) | 전체 콘텐츠 보존. nav, sidebar, header, footer 등 구조 요소를 유지한다. 메뉴 구조, 내비게이션 링크 등 유용한 정보가 보존된다. | 사이트 구조 파악, 메뉴/링크 수집, 전체 페이지 아카이빙 |
| **clean** | 본문만 추출. nav, header, footer, sidebar, 광고 등 비본문 요소를 제거한다. | 본문 콘텐츠만 필요할 때, 문서/블로그 아티클 추출 |

사용자가 모드를 명시하지 않으면 **full** 모드를 적용한다. "본문만", "내용만", "clean" 등의 키워드가 있으면 clean 모드를 적용한다.

---

## 실행 흐름

```
URL 입력 (단일 또는 복수)
  │
  ├─ 단일 URL → 직접 처리
  │     │
  │     ├─ Phase 1: WebFetch (내장 도구)
  │     │     ├─ 성공 → 본문 추출 + MD 정제 → 저장
  │     │     └─ 실패 (403, 빈 콘텐츠, JS 필요, 타임아웃)
  │     │           └─ Phase 2: 브라우저 폴백 (Crawl4AI, Python 3.10+)
  │     │                 ├─ 설치됨 + 버전 OK → Python 스크립트 실행
  │     │                 └─ 미설치 또는 버전 불일치
  │     │                       └─ Phase 3: Node Playwright 폴백
  │     │                             ├─ playwright npm 설치됨 → Node 스크립트 실행 + MD 정제
  │     │                             └─ 미설치 → 설치 안내 후 중단
  │     └─ 결과: {slug}.md 저장
  │
  └─ 복수 URL → 서브에이전트 병렬 디스패치
        ├─ URL별 서브에이전트 1개씩 생성
        ├─ 각 에이전트가 위 단일 URL 프로세스 실행
        └─ 전체 완료 후 결과 요약 보고
```

---

## Phase 1: WebFetch (경량 fetch)

내장 `WebFetch` 도구로 URL을 가져온다. 별도 설치가 필요 없고 빠르다.

### 실행

**full 모드 (기본):**
```
WebFetch(url="{URL}", prompt="이 페이지의 전체 콘텐츠를 마크다운으로 변환해줘. script, style 태그만 제거하고, nav, sidebar, header, footer 등 구조 요소는 보존해줘. 메뉴 링크와 내비게이션 구조도 마크다운으로 변환해줘.")
```

**clean 모드:**
```
WebFetch(url="{URL}", prompt="이 페이지의 본문 콘텐츠를 마크다운으로 변환해줘. nav, header, footer, sidebar, 광고, 쿠키 배너 등 비본문 요소는 제거하고 본문만 추출해줘.")
```

### 성공 판정

다음 조건을 **모두** 만족하면 성공으로 판정한다:

- HTTP 응답이 정상 (리다이렉트 경고 없음)
- 본문 콘텐츠가 100자 이상
- "JavaScript is required", "Please enable JavaScript" 등의 JS 의존 메시지가 없음

### 실패 시 Phase 2로 전환

실패 사유를 기록하고 Phase 2로 넘어간다:

| 실패 유형 | 판정 기준 |
|-----------|----------|
| 접근 차단 | 403, 401, 429 응답 |
| 빈 콘텐츠 | 본문 100자 미만 |
| JS 렌더링 필요 | JS 의존 메시지 감지 또는 의미 없는 스켈레톤만 반환 |
| 리다이렉트 | 다른 호스트로 리다이렉트 발생 |
| 타임아웃 | 응답 없음 |

---

## Phase 2: 브라우저 폴백 (Crawl4AI)

JavaScript 렌더링이 필요한 페이지를 Crawl4AI(Playwright 내장)로 처리한다.

### 설치 확인

Python 3.10+ 버전과 crawl4ai 패키지를 동시에 확인한다:

```bash
python3 -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'; import crawl4ai" 2>/dev/null
```

import 성공 시 진입. 버전 불일치 또는 패키지 미설치 시 Phase 3로 전환한다.

### 실행

Crawl4AI가 설치되어 있으면 Python 스크립트로 실행한다:

```bash
python3 -c "
import asyncio, json, sys
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter

async def crawl():
    browser_config = BrowserConfig(headless=True)
    prune = PruningContentFilter(threshold=0.5)
    crawler_config = CrawlerRunConfig(
        word_count_threshold=10,
        remove_overlay_elements=True,
        process_iframes=True,
        content_filter=prune,
    )
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url='${URL}', config=crawler_config)
        if not result.success:
            print(json.dumps({'success': False, 'status_code': result.status_code}))
            sys.exit(1)
        mode = '${MODE}'
        md = result.markdown.fit_markdown if mode == 'clean' else result.markdown.raw_markdown
        print(md)

asyncio.run(crawl())
"
```

- **full 모드**: `result.markdown.raw_markdown` — 전체 콘텐츠 보존 (HTML→마크다운 직접 변환)
- **clean 모드**: `result.markdown.fit_markdown` — PruningContentFilter로 노이즈 제거된 본문

Crawl4AI가 마크다운 변환을 내장하므로, 별도 MD 정제 로직이 불필요하다.

### Crawl4AI 사용 불가 시

설치 안내 없이 즉시 Phase 3(Node Playwright)로 전환한다.

---

## Phase 3: Node Playwright 폴백

Crawl4AI를 사용할 수 없을 때(미설치, Python 버전 불일치, 런타임 오류) Node.js Playwright로 폴백한다.

### 설치 확인

```bash
node -e "require('playwright')" 2>/dev/null
```

성공 시 진입. 실패 시 설치 안내 후 중단한다.

### 실행

```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('${URL}', { waitUntil: 'networkidle', timeout: 30000 });
  const html = await page.content();
  console.log(html);
  await browser.close();
})();
"
```

Phase 3는 HTML을 stdout으로 출력한다. **에이전트가 이 HTML을 받아서 MD 정제 규칙(아래 "콘텐츠 추출 및 MD 정제" 섹션)을 적용한 뒤 .md 파일로 저장한다.** stdout을 파일로 직접 리다이렉트(`> file.txt`)하지 않는다.

### Playwright 미설치 시

사용자에게 설치 방법을 안내하고 중단한다. Phase 1 결과가 있으면 (불완전하더라도) 그것을 사용한다.

```
⚠️ 모든 브라우저 폴백 불가: Crawl4AI, Playwright 모두 사용할 수 없습니다.

설치 방법 (택 1):
  • Crawl4AI: pip install crawl4ai && crawl4ai-setup  (Python 3.10+ 필요)
  • Playwright: npm install playwright
```

---

## 콘텐츠 추출 및 MD 정제

Phase 1과 Phase 3에서 아래 정제 규칙을 적용한다. Phase 2(Crawl4AI)는 마크다운 변환을 내장하므로 별도 정제가 불필요하다.

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
> 추출 방식: {WebFetch | Crawl4AI | Playwright}
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

**에이전트 이름**: `wtm-agent`

탐색 경로 (우선순위):
1. `{프로젝트}/.opal/agents/wtm-agent/AGENT.md`
2. `~/.opal/agents/wtm-agent/AGENT.md`

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
        │     prompt: "다음 URL의 웹 페이지를 마크다운으로 변환해줘.
        │              URL: {url}
        │              저장 경로: {save-path}
        │              Phase 1(WebFetch) 시도 후 실패하면 Phase 2(브라우저)로 폴백.
        │              결과를 {save-path}에 저장하고, 성공 여부와 사용한 방식을 보고해줘."
        │
        └─ 전체 완료 후 결과 종합
```

### 결과 보고

```
[web-to-markdown 완료] {n}개 URL 처리

| # | URL | 방식 | 결과 | 저장 경로 |
|---|-----|------|------|----------|
| 1 | {url} | WebFetch | ✅ 성공 | {path} |
| 2 | {url} | Crawl4AI | ✅ 성공 | {path} |
| 3 | {url} | WebFetch | ⚠️ 부분 성공 | {path} |
```

---

## 에지 케이스 처리

| 상황 | 대응 |
|------|------|
| 인증 필요 (로그인 페이지 리다이렉트) | "이 URL은 로그인이 필요합니다" 안내 후 중단 |
| PDF URL | WebFetch로 처리, MD 변환은 제한적임을 안내 |
| 매우 긴 페이지 (10만자 초과) | 본문을 10만자에서 truncate, 안내 메시지 추가 |
| 리다이렉트 | 최종 URL을 따라가되, 메타정보에 원본+최종 URL 모두 기록 |
| robots.txt 차단 | 안내 후 중단 (강제 우회 금지) |
| 타임아웃 | Phase 1: 15초, Phase 2/3: 30초 후 실패 처리 |

---

## 의존성

| 도구 | 필수 여부 | 용도 |
|------|----------|------|
| WebFetch (내장) | 필수 | Phase 1 경량 fetch |
| Crawl4AI (`crawl4ai`) | 선택 | Phase 2 브라우저 폴백 (Python 3.10+, Playwright 내장) |
| Playwright (`playwright`) | 선택 | Phase 3 브라우저 폴백 (Node.js) |
| Agent 도구 | 선택 | 복수 URL 병렬 처리 |

설치 방법 (브라우저 폴백, 택 1 이상):
```bash
# Crawl4AI (Python 3.10+)
pip install crawl4ai && crawl4ai-setup

# Playwright (Node.js)
npm install playwright
```

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-20 | 초기 작성 — full/clean 듀얼 모드, 2단계 폴백(WebFetch→Playwright), 복수 URL 병렬 처리(wtm-agent) |
| v1.1 | 2026-03-20 | Phase 2 백엔드를 Playwright에서 Crawl4AI로 교체 — 마크다운 변환 내장, Anti-bot/stealth 지원 |
| v1.2 | 2026-04-01 | 3단계 폴백(WebFetch→Crawl4AI→Node Playwright), Phase 2 Python 버전 체크, 저장 경로 간소화, wtm 약어 등록 |
