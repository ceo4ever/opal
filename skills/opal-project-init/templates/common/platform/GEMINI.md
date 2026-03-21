# === OPAL START ===
## OPAL AI Agent — 필수 부트스트랩

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. 이 단계를 건너뛰면 안 된다.

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 AGENT.md의 온보딩 절차를 따른다)
# === OPAL END ===

# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| Backend | {{TECH_STACK_BACKEND}} |
| Frontend | {{TECH_STACK_FRONTEND}} |
| Database | {{DB_TYPE}} |

## 프로젝트 문서

이 프로젝트의 개발 가이드는 `docs/` 폴더에 있다.
작업 시작 전 반드시 아래 문서를 참조한다:

- `docs/INDEX.md` — 전체 문서 인덱스 (여기서 필요한 문서를 찾는다)
- `docs/server/PROJECT_STRUCTURE.md` — 서버 프로젝트 구조
- `docs/client/ARCHITECTURE.md` — 클라이언트 아키텍처 원칙

### 상황별 참조 문서
- 새 서비스 개발: `docs/server/DOMAIN_GUIDE.md`
- 새 화면 개발: `docs/client/ARCHITECTURE.md`
- 환경 설정: `docs/server/ENVIRONMENT.md`, `docs/client/ENVIRONMENT.md`
- 문제 해결: `docs/client/COMMON_ISSUES.md`

## 코드 컨벤션

<!-- 프로젝트에 맞게 커스터마이징 -->

## 개발 환경

- 서버: http://localhost:{{SERVER_PORT}}
- 클라이언트: http://localhost:{{CLIENT_PORT}}
