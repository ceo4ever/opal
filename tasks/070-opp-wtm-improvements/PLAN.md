# PLAN: wtm 스킬 개선 — Playwright MCP 전환 + browser 모드 + PM 사전 수집 패턴

> 작성일: 2026-04-02 | 태스크: 070-opp-wtm-improvements

## 수정 대상 파일

- **배포 소스**: `/Volumes/Data/AIStudio/workspace/ai-framework/skills/web-to-markdown/SKILL.md`
- **배포 경로**: `~/.opal/skills/web-to-markdown/SKILL.md`
- 두 파일 모두 동일 내용으로 수정한다.

---

## W1 — Phase 2 교체: Crawl4AI → Playwright MCP

### 1-1. 헤더 버전 변경

```
버전: v1.3 → v1.4
```

### 1-2. 실행 흐름 다이어그램 교체

기존 3단계 폴백(WebFetch → Crawl4AI → Node Playwright) 다이어그램을 2단계로 교체한다.

**변경 전 (실행 흐름 코드블록 내부):**
```
│     ├─ Phase 1: WebFetch (내장 도구)
│     │     ├─ 성공 → 본문 추출 + MD 정제 → 저장
│     │     └─ 실패 (403, 빈 콘텐츠, JS 필요, 타임아웃)
│     │           └─ Phase 2: 브라우저 폴백 (Crawl4AI, Python 3.10+)
│     │                 ├─ 설치됨 + 버전 OK → Python 스크립트 실행
│     │                 └─ 미설치 또는 버전 불일치
│     │                       └─ Phase 3: Node Playwright 폴백
│     │                             ├─ playwright npm 설치됨 → Node 스크립트 실행 + MD 정제
│     │                             └─ 미설치 → 설치 안내 후 중단
```

**변경 후:**
```
│     ├─ [browser 모드] → Phase 1 생략, Phase 2로 즉시 이동
│     │     (localhost/127.0.0.1/[::1] URL 자동 감지 포함)
│     │
│     ├─ Phase 1: WebFetch (내장 도구)
│     │     ├─ 성공 → 본문 추출 + MD 정제 → 저장
│     │     └─ 실패 (403, 빈 콘텐츠, JS 필요, 타임아웃)
│     │           └─ Phase 2: Playwright MCP
│     │                 ├─ browser_navigate(url) → browser_snapshot()
│     │                 ├─ Claude가 Accessibility Tree를 Markdown으로 정제
│     │                 └─ MCP 미등록 → 설치 안내 후 중단
```

### 1-3. Phase 2 섹션 전면 교체

기존 `## Phase 2: 브라우저 폴백 (Crawl4AI)` 섹션 전체(설치 확인, 실행, 사용 불가 시 안내 포함)를 아래로 교체한다.

**교체 후 내용:**

```markdown
## Phase 2: Playwright MCP

JavaScript 렌더링이 필요한 페이지를 Playwright MCP로 처리한다. `browser` 모드에서도 동일하게 사용한다.

### MCP 등록 확인

Claude Code `settings.json`에 Playwright MCP 서버가 등록되어 있어야 한다.
미등록 시 아래 "Playwright MCP 미등록 시" 안내를 따른다.

### 실행

1. `browser_navigate(url="{URL}")` 호출
2. `browser_snapshot()` 호출 — Accessibility Tree 반환
3. Claude가 반환값을 받아 "콘텐츠 추출 및 MD 정제" 규칙으로 Markdown 정제

- **full 모드**: 전체 구조(nav, sidebar, header, footer)를 보존하며 Markdown으로 변환.
- **clean 모드**: 비본문 요소(nav, header, footer, sidebar, 광고)를 제거하고 본문만 추출.

### Playwright MCP 미등록 시

사용자에게 등록 방법을 안내하고 중단한다:

```
⚠️ 브라우저 폴백 불가: Playwright MCP가 등록되어 있지 않습니다.

등록 방법:
  Claude Code settings.json에 아래 내용을 추가하세요.
  {
    "mcpServers": {
      "playwright": {
        "command": "npx",
        "args": ["@playwright/mcp@latest"]
      }
    }
  }
  npx가 자동으로 패키지를 가져오므로 별도 설치가 불필요합니다.
```
```

### 1-4. Phase 3 섹션 삭제

`## Phase 3: Node Playwright 폴백` 섹션 전체를 삭제한다. Playwright MCP가 Phase 2로 대체하므로 불필요하다.

### 1-5. Wireframe 모드 실행 로직 업데이트

Wireframe 모드 "실행 로직" 다이어그램 내 폴백 참조 문구를 수정한다.

**변경 전:**
```
  ├─ 기존 3단계 폴백으로 HTML/마크다운 취득 (full 모드 기반)
```

**변경 후:**
```
  ├─ 기존 2단계 폴백으로 콘텐츠 취득 (full 모드 기반)
  │   Phase 1: WebFetch → Phase 2: Playwright MCP
```

### 1-6. 콘텐츠 추출 및 MD 정제 섹션 리드 문장 수정

**변경 전:**
```
Phase 1과 Phase 3에서 아래 정제 규칙을 적용한다. Phase 2(Crawl4AI)는 마크다운 변환을 내장하므로 별도 정제가 불필요하다.
```

**변경 후:**
```
모든 Phase에서 아래 정제 규칙을 적용한다. Phase 2(Playwright MCP)는 Accessibility Tree를 반환하므로 Claude가 직접 Markdown으로 정제한다.
```

### 1-7. 산출물 형식 내 추출 방식 레이블 수정

full/clean 모드와 wireframe 모드 산출물 형식 두 곳 모두 수정한다.

**변경 전:**
```
> 추출 방식: {WebFetch | Crawl4AI | Playwright}
```

**변경 후:**
```
> 추출 방식: {WebFetch | Playwright MCP}
```

### 1-8. 의존성 테이블 수정

**변경 전:**

| 도구 | 필수 여부 | 용도 |
|------|----------|------|
| WebFetch (내장) | 필수 | Phase 1 경량 fetch |
| Crawl4AI (`crawl4ai`) | 선택 | Phase 2 브라우저 폴백 (Python 3.10+, Playwright 내장) |
| Playwright (`playwright`) | 선택 | Phase 3 브라우저 폴백 (Node.js) |
| Agent 도구 | 선택 | 복수 URL 병렬 처리 |

**변경 후:**

| 도구 | 필수 여부 | 용도 |
|------|----------|------|
| WebFetch (내장) | 필수 | Phase 1 경량 fetch |
| Playwright MCP (`@playwright/mcp`) | 필수 (MCP 등록) | Phase 2 브라우저 렌더링, browser 모드 |
| Agent 도구 | 선택 | 복수 URL 병렬 처리 |

### 1-9. 설치 안내 교체

**변경 전:**
```bash
# Crawl4AI (Python 3.10+)
pip install crawl4ai && crawl4ai-setup

# Playwright (Node.js)
npm install playwright
```

**변경 후:**
```json
// Claude Code settings.json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```
설명 문구: `npx가 자동으로 패키지를 가져오므로 별도 설치가 불필요하다.`

### 1-10. 변경이력 v1.4 추가

**추가할 행:**

| v1.4 | 2026-04-02 | Phase 2를 Crawl4AI → Playwright MCP로 교체, Phase 3 Node Playwright 삭제, browser 모드 추가, PM 직접 순차 수집 패턴 추가 |

---

## W2 — browser 모드 추가

### 2-1. 추출 모드 테이블에 browser 행 추가

기존 `wireframe` 행 아래에 `browser` 행을 추가한다.

| **browser** | Playwright MCP 즉시 사용. WebFetch(Phase 1) 생략. | localhost, SPA/동적 페이지, 캡틴 명시 요청 |

### 2-2. 모드 자동 감지 규칙에 browser 감지 추가

기존 모드 감지 문장 뒤에 아래 내용을 추가한다.

```
"브라우저로", "browser", "로컬" 등의 키워드가 있거나,
URL 호스트가 `localhost`, `127.0.0.1`, `[::1]`인 경우 `browser` 모드를 자동 적용한다.
browser 모드에서는 Phase 1(WebFetch)을 생략하고 Phase 2(Playwright MCP)로 즉시 진입한다.
```

### 2-3. 실행 흐름 다이어그램 browser 분기

W1-1-2에서 이미 반영되므로 추가 작업 없음.

---

## W3 — PM 사전 수집 패턴 (복수 URL)

### 3-1. 처리 방식 선택 기준 테이블 추가

기존 "복수 URL 처리" 섹션 도입부(서브에이전트 실행 방식 설명 앞)에 선택 기준 테이블을 추가한다.

```markdown
### 처리 방식 선택 기준

| 조건 | 권장 방식 |
|------|----------|
| URL 수 2~5개, 서로 다른 호스트 | 서브에이전트 병렬 디스패치 |
| URL이 동일 호스트이거나 browser 모드 적용 대상 | PM 직접 순차 수집 |
| URL 수 6개 이상 또는 browser 모드 포함 | PM 직접 순차 수집 |

> 참조: opal-harness §7.4 Concurrency Limit — 합산 200KB 초과 또는 단일 50KB 초과 시
> 순차 실행 또는 Max 2개 병렬로 제한한다.
```

### 3-2. PM 직접 순차 수집 패턴 섹션 추가

기존 "서브에이전트 병렬 디스패치" 실행 방식 섹션 뒤에 신규 섹션으로 추가한다.

```markdown
### PM 직접 순차 수집 패턴

PM(오케스트레이터)이 Playwright MCP를 직접 순차 호출하여 콘텐츠를 사전 수집하고,
수집된 Markdown 파일 경로를 워커에게 주입한다.

**동작 흐름:**
```
URL 목록 수신 (동일 호스트 또는 browser 모드)
  │
  ├─ PM이 URL별 순차 처리
  │     ├─ browser_navigate(url) → browser_snapshot()
  │     ├─ Claude가 Markdown 정제
  │     └─ {task-folder}/collected-refs/{slug}.md 저장
  │
  └─ 수집 완료 후 워커 병렬 디스패치
        prompt 예시: "다음 경로의 참조 문서를 활용하여 작업을 수행해줘.
                     참조 경로: {task-folder}/collected-refs/{slug}.md"
```

**사용 시나리오 비교:**
- 기존: URL 21개 → 에이전트 21개 → 각자 Playwright 브라우저 인스턴스 생성 → 리소스 고갈
- 개선: PM이 Playwright MCP 직접 21회 순차 호출 → md 수집 → 워커 병렬 디스패치

**저장 경로:**
- `{task-folder}/collected-refs/{slug}.md`
- 태스크 폴더 감지 불가 시: `/tmp/web-to-markdown/collected-refs/{slug}.md`
```

### 3-3. 결과 보고 테이블 레이블 수정

기존 결과 보고 예시 테이블에서 `Crawl4AI` 레이블을 `Playwright MCP`로 교체한다.

**변경 전:**
```
| 2 | {url} | Crawl4AI | ✅ 성공 | {path} |
```

**변경 후:**
```
| 2 | {url} | Playwright MCP | ✅ 성공 | {path} |
```

---

## 에지 케이스 처리 섹션 수정

**변경 전:**
```
| 타임아웃 | Phase 1: 15초, Phase 2/3: 30초 후 실패 처리 |
```

**변경 후:**
```
| 타임아웃 | Phase 1: 15초, Phase 2(Playwright MCP): 30초 후 실패 처리 |
```

---

## 수정 순서 체크리스트

1. [x] 헤더 버전 `v1.3` → `v1.4`
2. [x] 추출 모드 테이블에 `browser` 행 추가
3. [x] 모드 자동 감지 규칙에 browser 감지 규칙 추가
4. [x] 실행 흐름 다이어그램 교체 (browser 분기 + 2단계 폴백)
5. [x] Phase 2 섹션 전면 교체 (Crawl4AI → Playwright MCP)
6. [x] Phase 3 섹션 전체 삭제
7. [x] Wireframe 모드 실행 로직 다이어그램 업데이트
8. [x] 콘텐츠 추출 및 MD 정제 섹션 리드 문장 수정
9. [x] 산출물 형식 추출 방식 레이블 수정 (2곳: full/clean 산출물, wireframe 산출물)
10. [x] 복수 URL 처리 섹션에 선택 기준 테이블 추가
11. [x] PM 직접 순차 수집 패턴 섹션 추가
12. [x] 결과 보고 테이블 레이블 수정 (Crawl4AI → Playwright MCP)
13. [x] 에지 케이스 처리 타임아웃 문구 수정
14. [x] 의존성 테이블 수정 (Crawl4AI 제거, Playwright MCP 필수로 변경)
15. [x] 설치 안내 교체 (pip/npm → settings.json 등록 방법)
16. [x] 변경이력 v1.4 추가
