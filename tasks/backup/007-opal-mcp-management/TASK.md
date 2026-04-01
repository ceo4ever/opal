# TASK: OPAL MCP 관리 체계 구축

> 작성일: 2026-03-12 | 작업 유형: 🆕 신규 개발

## 작업 목표

OPAL 프레임워크에 MCP 서버 관리 체계를 구축하여, 기본 MCP를 내재화하고 `install-mac.sh`로 각 LLM 플랫폼(Claude Code, Cursor, Antigravity 등)에 자동 배포할 수 있도록 한다.

## 배경

- 현재 OPAL에는 `references/mcps.md` 레지스트리가 존재하지만 "등록된 MCP 서버 없음" 상태
- shadcn/ui 스킬처럼 MCP 서버가 필요한 스킬이 늘어나고 있으나, MCP 설치/배포가 수동
- 각 플랫폼(Claude Code, Cursor, VS Code 등)마다 MCP 설정 파일 포맷과 경로가 다름
- 사용자가 `install-mac.sh` 한 번으로 기본 MCP까지 세팅되면 즉시 활용 가능

## 요구사항

- [ ] MCP 설치의 3가지 패턴을 지원하는 관리 체계 설계
  - **설정 머지형**: 정적 설정 정보를 플랫폼별 mcp.json에 머지/생성 (stdio 로컬 + 원격 URL)
  - **CLI 위임형**: MCP 서버가 제공하는 `mcp init` CLI를 호출하여 설치
  - **패키지 설치형**: npm 패키지 설치 후 설정 생성
- [ ] 소스에 MCP 설정 템플릿 구조 추가 (`opal/core/mcps/` 또는 적절한 위치)
- [ ] `install-mac.sh`에 MCP 설치 기능 추가
  - 플랫폼별 mcp.json 머지/생성 (기존 사용자 설정 보존)
  - Claude Code: `~/.claude/mcp.json`
  - Cursor: `~/.cursor/mcp.json`
- [ ] `references/mcps.md` 레지스트리에 기본 MCP 등록
- [ ] OPAL 에이전트가 MCP 도구를 인지하고 활용할 수 있도록 연동

## 제약 조건

- 기존 사용자의 mcp.json이 있으면 **덮어쓰지 않고 머지**해야 함
- Node.js가 없는 환경에서도 설정 머지형은 동작해야 함
- CLI 위임형/패키지 설치형은 Node.js 의존 — 없으면 안내 메시지 출력
- 플랫폼별 mcp.json 포맷 차이를 흡수해야 함

## 관련 문서

- `opal/core/references/mcps.md` — 현재 빈 MCP 레지스트리
- `community-skills/vercel-labs/shadcn/mcp.md` — shadcn MCP 설정 참조
- `community-skills/anthropics/mcp-builder/` — MCP 서버 빌드 가이드
- `scripts/install-mac.sh` — 현재 설치 스크립트
