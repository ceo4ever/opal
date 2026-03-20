# DONE: web-to-markdown 스킬 개발

> 완료일: 2026-03-20 | 모드: Short Task | 작업 유형: 신규 개발

## 완료 요약
URL을 입력받아 웹 페이지 콘텐츠를 마크다운으로 변환하는 프레임워크 스킬을 개발했다. full/clean 듀얼 모드, 2단계 폴백(WebFetch → Playwright), 복수 URL 병렬 처리(wtm-worker 서브에이전트)를 지원한다.

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/web-to-markdown/SKILL.md` | 신규 스킬 작성 (323줄) — full/clean 모드, Phase 1/2 폴백, 복수 URL 병렬 |
| 2 | `agents/claude/wtm-worker/AGENT.md` | Claude 플랫폼 워커 에이전트 |
| 3 | `agents/cursor/wtm-worker.md` | Cursor 플랫폼 워커 에이전트 |
| 4 | `agents/antigravity/wtm-worker/SKILL.md` | Antigravity 플랫폼 워커 에이전트 (폴백 모드) |
| 5 | `~/.opal/references/skills.md` | 프레임워크 스킬 테이블에 web-to-markdown 등록 |
| 6 | `~/.opal/references/agents.md` | 에이전트 레지스트리에 wtm-worker 등록 |

## 핵심 변경 사항
### Before
- 웹 페이지 콘텐츠를 체계적으로 마크다운으로 변환하는 스킬 없음
- WebFetch 단독 사용 시 JS 렌더링 페이지 처리 불가

### After
- **full 모드** (기본): nav/sidebar 등 구조 요소 보존 — 메뉴, 내비게이션 정보 활용 가능
- **clean 모드**: 본문만 추출 — 아티클/문서 콘텐츠에 집중
- **2단계 폴백**: WebFetch → Playwright MCP/스크립트로 JS 페이지도 처리
- **복수 URL 병렬**: wtm-worker 서브에이전트로 동시 처리
- **저장 경로 우선순위**: DTP 태스크 폴더 → docs/web-captures/ → 사용자 지정 → /tmp/

## 테스트 결과
All Pass — 시나리오 4/4 Pass, 코드 품질/회귀 Skip (문서 전용), 보안 Pass

## 산출물 목록
| 파일 | 설명 |
|------|------|
| `tasks/019-web-to-markdown-skill/TASK.md` | 작업 정의서 |
| `tasks/019-web-to-markdown-skill/PLAN.md` | 통합 PLAN (분석+계획+체크리스트) |
| `tasks/019-web-to-markdown-skill/QA-PLAN.md` | PLAN QA 리뷰 |
| `tasks/019-web-to-markdown-skill/TEST-SCENARIO.md` | 테스트 시나리오 + 실행 결과 |
| `tasks/019-web-to-markdown-skill/DONE.md` | 완료 리포트 |
