# TASK: web-to-markdown 스킬 개발

> 작성일: 2026-03-20 | 작업 유형: 신규 개발

## 작업 목표
URL을 입력받아 웹 페이지 콘텐츠를 정제된 마크다운으로 변환하는 프레임워크 스킬을 개발한다.

## 배경
AI 에이전트가 외부 웹 페이지의 콘텐츠를 참조해야 하는 상황이 빈번하다. 현재는 WebFetch로 단순 조회만 가능하지만, JS 렌더링이 필요한 페이지 처리, 정제된 마크다운 변환, 복수 URL 병렬 처리 등의 체계적인 워크플로우가 없다. 이 스킬을 통해 에이전트들이 웹 콘텐츠를 일관된 형식으로 활용할 수 있게 한다.

## 요구사항
- [ ] SKILL.md 작성: 2단계 폴백 전략 (WebFetch → Playwright 브라우저)
- [ ] 기본 모드: 전체 콘텐츠(nav/sidebar 포함) — 메뉴 구조, 내비게이션 등 유용한 정보 보존
- [ ] clean 옵션: 본문만 추출 (nav/header/footer/sidebar 제거)
- [ ] 저장 경로 우선순위: DTP 태스크 폴더 → docs/web-captures/ → 사용자 지정 → /tmp/
- [ ] 복수 URL 병렬 처리: 서브에이전트(wtm-worker) 활용
- [ ] wtm-worker 에이전트: 3개 플랫폼(Claude/Cursor/Antigravity) 에이전트 파일 생성
- [ ] Playwright MCP 연동 검토: MCP 있으면 우선 사용, 없으면 스크립트 폴백
- [ ] OPAL 후처리: 레지스트리 등록, 버전 태깅

## 제약 조건
- 프레임워크 스킬 (skills/ 디렉토리, 3개 플랫폼 공용)
- SKILL.md 500줄 이하
- 한국어 본문, 영어 코드/필드명
- 기존 초안 위치: skills/web-to-markdown/SKILL.md (Phase 1에서 작성)

## 관련 문서
- 참고 스킬: zephyrwang6/myskill@web-scraper, otrebu/agents@web-to-markdown, canghe-url-to-markdown
- Playwright MCP: microsoft/playwright@playwright-mcp-dev, @playwright/mcp@latest
- 기존 에이전트 구조: agents/claude/, agents/cursor/, agents/antigravity/
