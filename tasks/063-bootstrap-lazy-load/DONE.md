# DONE: 부트스트랩 Eager/Lazy 재설계 + 서브에이전트 부트스트랩 생략

> 완료일: 2026-04-01

## 요약

OPAL 부트스트랩 속도 저하 문제를 두 축으로 해결했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/AGENT.md` | 부트스트랩 Eager/Lazy 구조 재작성 + `[WORKER]` 마커 규칙 + 보고 형식 갱신 |
| `opal/skills/opal-pilot-project/SKILL.md` | `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가 |
| `opal/skills/opal-pilot-dev/SKILL.md` | 동일 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | 동일 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 동일 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 동일 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 동일 |

## 핵심 변경 사항

### PM 세션 Eager/Lazy 구조

| 구분 | 파일 | 트리거 |
|------|------|--------|
| **Eager** | identity.md | 세션 시작 즉시 |
| **Eager** | opal-harness.md | 세션 시작 즉시 |
| **Lazy** | skill-registry | `//` 커맨드 입력 시 |
| **Lazy** | agents.md + model-mapping | 워커 디스패치 직전 |
| **Lazy** | mcps.md | MCP 사용 요청 시 |
| **Lazy** | PM 컨텍스트 + MEMORY | 프로젝트 작업 요청 시 |

### 서브에이전트 부트스트랩 생략

- `[WORKER]` 마커 규칙: 디스패치 프롬프트 첫 줄에 `[WORKER]`가 있으면 부트스트랩 전체 생략
- 6개 opal-pilot-* 스킬 디스패치 섹션에 `[WORKER]` 마커 + PM 컨텍스트 주입 지침 추가
- Claude Code / Cursor / Antigravity / Gemini 전 플랫폼 공통 적용 (AGENT.md 단일 소스)

## 배포

`install-mac.sh` 재실행 필요 — `opal/core/AGENT.md` → `~/.opal/AGENT.md` 동기화
