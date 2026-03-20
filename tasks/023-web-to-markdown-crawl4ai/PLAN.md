# PLAN: web-to-markdown 스킬 Phase 2 백엔드를 Crawl4AI로 교체

> 작성일: 2026-03-20 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/web-to-markdown/SKILL.md` | 스킬 본체. Phase 1/2 실행 흐름, 의존성, 변경이력 정의 | O |
| `agents/claude/wtm-worker/AGENT.md` | Claude Code 워커 에이전트. Phase 2 브라우저 폴백 절차 정의 | O |
| `agents/cursor/wtm-worker.md` | Cursor 워커 에이전트. 동일 구조 | O |
| `agents/antigravity/wtm-worker/SKILL.md` | Antigravity 워커 스킬. 동일 구조 | O |

### 현재 구현

**Phase 2 브라우저 폴백 흐름 (4개 파일 공통):**

1. Phase 1(WebFetch/fetch) 실패 시 Phase 2 진입
2. Playwright MCP 연결 여부 확인
   - MCP 있음: `browser_navigate` -> `browser_wait` -> `browser_snapshot` -> MD 정제
   - MCP 없음: Node.js 인라인 스크립트로 Playwright 직접 호출 (`node -e "const { chromium } = require('playwright'); ..."`)
   - Playwright 미설치: `npm install -D playwright && npx playwright install chromium` 안내 후 중단
3. 획득한 HTML을 에이전트가 추출 모드(full/clean)에 따라 MD 정제

**SKILL.md 의존성 섹션:**
- WebFetch(내장) 필수, Playwright MCP 선택, Playwright 선택, Agent 도구 선택

**산출물 메타데이터의 "추출 방식" 필드:**
- `WebFetch | Playwright MCP | Playwright Script` (SKILL.md, Claude AGENT.md)
- `fetch | Playwright MCP | Playwright Script` (Antigravity SKILL.md)

**SKILL.md 실행 흐름 다이어그램:**
```
Phase 2: 브라우저 폴백
  ├─ Playwright MCP 있음 → MCP 도구 사용
  └─ Playwright MCP 없음 → 스크립트 실행
        └─ Playwright 미설치 → 설치 안내 후 중단
```

### 영향 범위

- **상위 의존**: 이 스킬을 호출하는 OPAL 오케스트레이터, 사용자 직접 호출 -- 인터페이스(full/clean 모드, 저장 경로, 산출물 형식)가 유지되므로 영향 없음
- **하위 의존**: Phase 1(WebFetch)은 변경 없음. Phase 2만 Playwright -> Crawl4AI로 교체
- **공유 구조**: 산출물 메타데이터의 "추출 방식" 필드에 `Crawl4AI` 값 추가 필요
- **관련 테스트**: 해당 없음 (문서 기반 스킬, 자동 테스트 코드 없음)

---

## 2. 구현 계획

### 변경 파일

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/web-to-markdown/SKILL.md` | Phase 2 섹션 전체 교체, 의존성 업데이트, 산출물 메타데이터 업데이트, 변경이력 추가 |
| 2 | `agents/claude/wtm-worker/AGENT.md` | Phase 2 섹션 교체, method 반환값 업데이트 |
| 3 | `agents/cursor/wtm-worker.md` | Phase 2 섹션 교체, method 반환값 업데이트 |
| 4 | `agents/antigravity/wtm-worker/SKILL.md` | Phase 2 섹션 교체, method 반환값 업데이트 |

### 핵심 설계

#### SKILL.md Phase 2 섹션 교체 내용

**실행 흐름 다이어그램 변경:**
```
Phase 2: 브라우저 폴백 (Crawl4AI)
  ├─ Crawl4AI 설치 확인 (python3 -c "import crawl4ai")
  ├─ 설치됨 → Python 스크립트 실행
  └─ 미설치 → 설치 안내 후 중단
```

**Phase 2 본문 교체 -- Crawl4AI Python 스크립트:**

```python
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

- **full 모드**: `result.markdown.raw_markdown` 사용 (전체 콘텐츠 보존)
- **clean 모드**: `result.markdown.fit_markdown` 사용 (PruningContentFilter로 노이즈 제거)

**Playwright MCP 옵션 제거**: Crawl4AI가 내부적으로 Playwright를 사용하므로, 별도 MCP 경로 불필요. 단일 경로로 단순화.

**미설치 안내 메시지 변경:**
```
브라우저 폴백 불가: Crawl4AI가 설치되어 있지 않습니다.

설치 방법:
  pip install crawl4ai && crawl4ai-setup
```

**의존성 섹션 변경:**

| 도구 | 필수 여부 | 용도 |
|------|----------|------|
| WebFetch (내장) | 필수 | Phase 1 경량 fetch |
| Crawl4AI (`crawl4ai`) | 선택 | Phase 2 브라우저 폴백 |
| Agent 도구 | 선택 | 복수 URL 병렬 처리 |

- Playwright MCP, Playwright 항목 제거
- Crawl4AI 항목 추가
- MCP 등록 안내 블록 제거, Crawl4AI 설치 안내로 교체

**산출물 메타데이터 "추출 방식" 필드:**
- 기존: `WebFetch | Playwright MCP | Playwright Script`
- 변경: `WebFetch | Crawl4AI`

**변경이력 추가:**
- `v1.1 | 2026-03-20 | Phase 2 백엔드를 Playwright에서 Crawl4AI로 교체`

**버전 태그 변경:**
- `v1.0` -> `v1.1`

#### 워커 에이전트 3개 파일 공통 변경

Phase 2 섹션:
- "Playwright MCP 연결 여부 확인" 분기 로직 제거
- Crawl4AI 스크립트 실행 단일 경로로 교체
- 미설치 안내 메시지를 `pip install crawl4ai && crawl4ai-setup`으로 변경

산출물 형식:
- "추출 방식" 값을 `WebFetch | Crawl4AI`로 변경

반환 형식:
- method 값을 `WebFetch | Crawl4AI`로 변경

---

## 3. 실행 체크리스트

- [x] Step 1: **SKILL.md Phase 2 교체** -- `skills/web-to-markdown/SKILL.md` -- 실행 흐름 다이어그램, Phase 2 섹션, 콘텐츠 추출 섹션의 "추출 방식", 의존성 섹션, 미설치 안내, 변경이력, 버전 태그 수정
- [x] Step 2: **Claude 워커 교체** -- `agents/claude/wtm-worker/AGENT.md` -- Phase 2 섹션, 산출물 형식의 "추출 방식", 반환 형식의 method 값 수정
- [x] Step 3: **Cursor 워커 교체** -- `agents/cursor/wtm-worker.md` -- Phase 2 섹션, 산출물 형식의 "추출 방식", 반환 형식의 method 값 수정
- [x] Step 4: **Antigravity 워커 교체** -- `agents/antigravity/wtm-worker/SKILL.md` -- Phase 2 섹션, 산출물 형식의 "추출 방식", 반환 형식의 method 값 수정

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] SKILL.md Phase 2가 Crawl4AI 기반으로 완전히 교체되었는가
- [ ] full 모드에서 `raw_markdown`, clean 모드에서 `fit_markdown` 매핑이 올바른가
- [ ] Crawl4AI 미설치 시 안내 메시지가 `pip install crawl4ai && crawl4ai-setup`인가
- [ ] 의존성 테이블에서 Playwright 관련 항목이 제거되고 Crawl4AI가 추가되었는가
- [ ] 산출물 메타데이터의 "추출 방식"에 `Crawl4AI` 값이 포함되어 있는가
- [ ] 워커 에이전트 3개 파일 모두 동일한 변경이 적용되었는가

### 회귀 테스트
- [ ] Phase 1(WebFetch) 로직이 전혀 변경되지 않았는가
- [ ] 추출 모드(full/clean) 인터페이스가 유지되는가
- [ ] 저장 경로 규칙(slug, 우선순위)이 유지되는가
- [ ] 복수 URL 병렬 처리 로직이 유지되는가
- [ ] 에지 케이스 처리(인증, PDF, 긴 페이지, robots.txt)가 유지되는가

### 코드 품질
- [ ] 4개 파일의 마크다운 형식이 일관적인가
- [ ] Playwright 관련 잔여 참조가 없는가 (Phase 2 범위 내에서)
- [ ] 변경이력이 올바르게 추가되었는가
