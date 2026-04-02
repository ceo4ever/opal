# DONE: OPAL 스킬 MCP 사전 확인 메커니즘 추가

> 완료일: 2026-04-02
> 태스크: 073-opp-mcp-skill-registration

## 완료 요약

MCP 의존성이 있는 스킬 호출 시 실행 전 사전 확인하는 메커니즘을 추가했다.
`//wtm browser` 호출 시 Playwright MCP 미등록을 Phase 2 진입 전에 감지하고 안내 후 중단한다.

## 수정 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/mcps.md` | 스킬 MCP 의존성 테이블 + playwright 항목 + MCP 등록 방법 섹션 추가 |
| `skills/web-to-markdown/SKILL.md` | `## 의존성` 상단에 `### 필수 MCP` 서브섹션 추가 (browser 모드 사전 확인 규칙) |
| `opal/core/AGENT.md` | Lazy 트리거 `MCP 사용 요청` → `MCP 사용 요청 또는 MCP 의존 스킬 호출` |

## 검증 결과

- [x] mcps.md에 `### playwright` 항목 등록
- [x] mcps.md에 "스킬 MCP 의존성" 테이블 존재 (wtm 포함)
- [x] mcps.md에 "MCP 등록 방법" + Playwright settings.json 예시 포함
- [x] SKILL.md `## 의존성` 상단에 `### 필수 MCP` 서브섹션 존재
- [x] browser 모드 사전 확인 규칙 Phase 진입 전 조건으로 명시
- [x] AGENT.md Lazy 트리거 조건 업데이트

## 미완료 (수동 필요)

- [ ] `~/.opal/references/mcps.md` 동기화 (install-mac.sh 실행)
- [ ] `~/.opal/skills/web-to-markdown/SKILL.md` 동기화 (install-mac.sh 실행)
- [ ] `~/.opal/AGENT.md` 동기화 (install-mac.sh 실행)
- [ ] `~/.claude/settings.json`에 Playwright MCP 등록 (캡틴 직접)

## 다음 액션

1. `install-mac.sh` 실행하여 소스→배포 경로 동기화
2. `~/.claude/settings.json`에 Playwright MCP 등록 후 Claude Code 재시작
3. `//wtm browser http://www.storelink.io` 재테스트
