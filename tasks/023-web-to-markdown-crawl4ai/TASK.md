# TASK: web-to-markdown 스킬 Phase 2 백엔드를 Crawl4AI로 교체

> 작성일: 2026-03-20 | 작업 유형: 개선

## 작업 목표
web-to-markdown 스킬의 Phase 2 브라우저 폴백을 Playwright 직접 사용에서 Crawl4AI(Python 라이브러리)로 교체하여, 마크다운 변환 품질과 안정성을 높인다.

## 배경
현재 스킬은 Phase 1(WebFetch) 실패 시 Phase 2로 Playwright를 직접 호출하는데:
- Playwright를 별도로 설치해야 하고 (`npm install playwright && npx playwright install chromium`)
- 마크다운 변환 로직을 스킬이 직접 처리해야 하며
- Anti-bot, 세션 관리 등 고급 기능이 없다

Crawl4AI는:
- `pip install crawl4ai && crawl4ai-setup`으로 Playwright 포함 설치
- `result.markdown`으로 LLM 최적화 마크다운 내장 변환
- Anti-bot, stealth, undetected browser, 캐시 모드 등 내장
- Fit Markdown으로 LLM 컨텍스트 최적화 지원

## 요구사항
- [ ] Phase 2 백엔드를 Crawl4AI Python 스크립트로 교체
- [ ] Crawl4AI의 `result.markdown` 활용하여 마크다운 변환
- [ ] 기존 스킬 인터페이스(full/clean 모드, 저장 경로 규칙) 유지
- [ ] Crawl4AI 미설치 시 설치 안내 메시지 업데이트
- [ ] Phase 1(WebFetch) 로직은 그대로 유지

## 제약 조건
- Python 3.x 필요 (macOS 기본 제공)
- crawl4ai는 pip 패키지 — Node.js 의존성 제거됨
- 스킬 인터페이스(사용법, 모드, 저장 경로)는 변경 없음
- wtm-worker 에이전트의 Phase 2 부분도 동일하게 업데이트

## 관련 문서
- `skills/web-to-markdown/SKILL.md` — 현재 스킬
- `agents/claude/wtm-worker/AGENT.md` — 워커 에이전트
- https://docs.crawl4ai.com/ — Crawl4AI 공식 문서
