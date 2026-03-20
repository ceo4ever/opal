# DONE: web-to-markdown 스킬 Phase 2 백엔드를 Crawl4AI로 교체

> 완료일: 2026-03-20 | 모드: Short Task | 작업 유형: 개선

## 완료 요약
web-to-markdown 스킬의 Phase 2 브라우저 폴백을 Playwright MCP/스크립트 2분기에서 Crawl4AI 단일 경로로 교체했다. 스킬 본체와 3개 플랫폼 워커 에이전트 모두 반영 완료.

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/web-to-markdown/SKILL.md` | Phase 2 섹션 전체 교체 (Crawl4AI), 의존성/메타데이터/변경이력 업데이트, v1.1 |
| 2 | `agents/claude/wtm-worker/AGENT.md` | Phase 2 → Crawl4AI, 추출 방식/method 값 변경 |
| 3 | `agents/cursor/wtm-worker.md` | 동일 변경 |
| 4 | `agents/antigravity/wtm-worker/SKILL.md` | 동일 변경 |

## 핵심 변경 사항
### Before
- Phase 2: Playwright MCP 또는 Node.js Playwright 스크립트 (2분기)
- 설치: `npm install playwright && npx playwright install chromium`
- 마크다운 변환: 스킬이 직접 HTML→MD 정제 규칙 적용
- Anti-bot 기능 없음

### After
- Phase 2: Crawl4AI Python 스크립트 (단일 경로)
- 설치: `pip install crawl4ai && crawl4ai-setup` (Playwright 내장)
- 마크다운 변환: Crawl4AI 내장 (`raw_markdown` / `fit_markdown`)
- Anti-bot, stealth, undetected browser 내장

## 테스트 결과
- Playwright 잔여 참조 확인: Pass (맥락상 적절한 참조만 존재)
- 4개 파일 일관성 확인: Pass

## 산출물 목록
| 파일 | 설명 |
|------|------|
| `tasks/023-web-to-markdown-crawl4ai/TASK.md` | 작업 정의서 |
| `tasks/023-web-to-markdown-crawl4ai/PLAN.md` | 통합 PLAN |
| `tasks/023-web-to-markdown-crawl4ai/QA-PLAN.md` | PLAN QA 리뷰 |
| `tasks/023-web-to-markdown-crawl4ai/DONE.md` | 완료 리포트 |
