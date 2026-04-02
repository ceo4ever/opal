# TASK: wtm 스킬 개선 — Playwright MCP 전환 + browser 모드 + PM 사전 수집 패턴

> 작성일: 2026-04-02 | 작업 유형: 개선 | 적용 스킬: opp
> 입력: 캡틴 피드백 (Crawl4AI 설치 불안정 → Playwright MCP로 전환, browser 모드 추가, URL별 1:1 에이전트 비효율)
> 출력: web-to-markdown/SKILL.md 수정

## 작업 목표

wtm 스킬(web-to-markdown)의 Phase 2를 Crawl4AI에서 **Playwright MCP**로 교체하고, `browser` 모드를 추가하고, URL별 1:1 에이전트 디스패치 비효율을 PM 사전 수집 패턴으로 개선한다.

## 전제 조건

- **Playwright MCP**: Claude Code settings.json에 MCP 서버로 등록. npx로 자동 실행, 별도 설치 불필요.
- **Crawl4AI 제거**: Python 환경 의존성 문제(Homebrew 충돌, 버전 관리)로 Phase 2에서 제거.
- **Markdown 변환**: Playwright MCP의 `snapshot`(Accessibility Tree) 또는 HTML을 Claude가 직접 Markdown으로 정제. 별도 변환 라이브러리 불필요.

## 새 폴백 구조

```
Phase 1: WebFetch       — 정적 페이지, 빠름. 성공 시 바로 종료.
Phase 2: Playwright MCP — JS 렌더링 필요 시 (SPA, localhost, browser 모드).
                          snapshot(Accessibility Tree) → Claude가 Markdown 정제.
```

## 추출 모드

| 모드 | 설명 | 적용 조건 |
|------|------|---------|
| `auto` | WebFetch 시도 → 실패 시 Playwright MCP | 기본값 |
| `browser` | Playwright MCP 즉시 사용. WebFetch 생략 | localhost, SPA/동적 페이지, 캡틴 명시 요청 |

- `localhost` / `127.0.0.1` / `[::1]` URL은 `browser` 모드 자동 적용

## 배경

### W1. Crawl4AI → Playwright MCP 전환

Crawl4AI는 Python 3.10+ 필수이며 macOS Homebrew 환경에서 설치 충돌 발생. 반면 Playwright MCP는 Claude Code settings.json 한 줄로 등록되고, npx가 자동으로 패키지를 가져오므로 환경 의존성이 없다.

Playwright MCP의 `snapshot()`은 Accessibility Tree를 반환하며, Claude가 직접 Markdown으로 정제 가능. Crawl4AI의 "Markdown 자동 변환" 편의성과 동등한 결과를 별도 라이브러리 없이 달성한다.

### W2. browser 모드 추가

localhost URL은 WebFetch가 반드시 실패하고, SPA는 WebFetch로 의미 있는 콘텐츠를 얻을 수 없다. `browser` 모드를 명시하면 Phase 1을 건너뛰고 Playwright MCP로 즉시 처리한다.

### W3. PM 사전 수집 패턴 (복수 URL 비효율 개선)

21개 URL을 21개 에이전트로 병렬 디스패치하면 각 에이전트가 Playwright 브라우저 인스턴스를 개별 생성하여 리소스 고갈. PM이 Playwright MCP를 직접 순차 호출하여 사전 수집하고, 수집된 Markdown을 문서 작성 워커에게 주입한다.

```
기존: URL 21개 → 에이전트 21개 → 각자 Playwright → 리소스 고갈
개선: PM이 Playwright MCP 직접 21회 순차 호출 → md 수집 → 워커 병렬 디스패치
```

## 요구사항

### W1. Phase 2 Crawl4AI → Playwright MCP 교체

**SKILL.md**
- [ ] Phase 2 섹션 전면 교체: Crawl4AI Python 스크립트 → Playwright MCP 호출 방식으로 변경
- [ ] Phase 2 실행: `browser_navigate(url)` → `browser_snapshot()` → Claude가 Markdown 정제
- [ ] wireframe 모드 Phase 2도 동일하게 Playwright MCP 적용
- [ ] 의존성 테이블 수정: Crawl4AI `선택` → 제거, Playwright MCP `선택` → `필수(MCP 등록)`
- [ ] 설치 안내 수정: `pip install crawl4ai` 제거, Playwright MCP 등록 방법으로 교체
- [ ] 변경이력에 v1.4 추가

### W2. browser 모드 추가

**SKILL.md**
- [ ] 추출 모드 테이블에 `browser` 모드 행 추가
- [ ] 모드 자동 감지 규칙 추가: localhost/127.0.0.1/[::1] → `browser` 모드 자동 적용
- [ ] 실행 흐름 다이어그램 업데이트: `browser` 모드 분기 추가 (WebFetch 생략 → Playwright MCP 직행)

### W3. PM 사전 수집 패턴 (복수 URL)

**SKILL.md**
- [ ] "복수 URL 처리" 섹션에 PM 사전 수집 패턴 옵션 추가:
  - 기존 "서브에이전트 병렬 디스패치"는 유지 (소수 URL일 때)
  - 신규 "PM 직접 순차 수집" 패턴 추가: URL이 동일 호스트이거나 browser 모드일 때 권장
  - PM이 Playwright MCP 직접 순차 호출 → `collected-refs/{slug}.md` 저장 → 워커에 경로 주입
- [ ] 두 방식 비교 및 선택 기준 명시

## 제약 조건

- Phase 1 WebFetch의 기존 동작은 변경하지 않는다.
- Phase 3 Node Playwright 폴백은 삭제한다 (Playwright MCP가 Phase 2를 대체하므로 불필요).
- `browser` 모드 키워드 감지 규칙("브라우저로", "browser" 등)도 추출 모드 섹션에 추가한다.

## 관련 문서

- `~/.opal/skills/web-to-markdown/SKILL.md` (배포된 소스 — 읽기 참조용)
- `opal/skills/opal-pilot-write-tech/references/network-guide.md` (opwt와 연동 시 참조)
- `opal/core/references/opal-harness.md` (§7.4 Concurrency Limit — W3 배치 기준 참조)
