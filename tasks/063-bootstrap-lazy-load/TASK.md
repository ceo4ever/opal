# TASK: 부트스트랩 Eager/Lazy 재설계 + 서브에이전트 부트스트랩 생략

> 작성일: 2026-04-01 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 부트스트랩 속도 저하 문제를 두 축으로 해결한다:
1. **PM 세션**: identity + harness만 Eager 로드, 나머지는 Lazy(사용 시점) 로드
2. **서브에이전트**: 부트스트랩 전체 생략 — PM이 디스패치 프롬프트에 필요 컨텍스트를 직접 주입

## 배경

현재 `~/.opal/AGENT.md` 부트스트랩은 10단계로 세션 시작 시 모든 파일을 일괄 Read한다.

**문제 1 — PM 세션 과잉 로드**:

| 단계 | 파일 | PM 세션 필요 여부 |
|------|------|-----------------|
| 1 | identity.md | ✅ 항상 필요 |
| 3 | opal-harness.md | ✅ 항상 필요 (Guards가 PM 세션 전체에 적용) |
| 4 | skill-registry (node 실행) | ❌ `//` 커맨드 시만 |
| 5 | agents.md | ❌ 워커 디스패치 시만 |
| 5 | mcps.md | ❌ MCP 사용 시만 |
| 6 | opal-model-mapping.md | ❌ 워커 디스패치 시만 |
| 8 | `.opal/AGENT.md` (PM 컨텍스트) | ❌ PM 작업 시만 |
| 9 | `.opal/MEMORY.md` (브리핑) | ❌ 프로젝트 진입 시만 |

**문제 2 — 서브에이전트 중복 부트스트랩**:

오케스트레이터가 워커를 디스패치하면, 워커도 CLAUDE.md(또는 플랫폼 부트스트래퍼)를 받아 동일한 10단계 부트스트랩을 수행한다. `//opp` 하나 실행 시 PM + PLAN 워커 + QA 워커 + EXECUTE 워커가 각각 풀 부트스트랩을 실행 — 대부분 워커에게 불필요한 작업이다.

## 요구사항

### PM 세션 Eager/Lazy 구조

- [ ] **Eager 로드**: identity.md + opal-harness.md 두 개만 즉시 로드
- [ ] **Lazy 트리거 정의**: 나머지 참조 문서의 로드 시점 명시
  - `skill-registry` → `//` 커맨드 입력 시
  - `agents.md` / `opal-model-mapping.md` → 워커 디스패치 직전
  - `mcps.md` → MCP 사용 요청 시
  - `.opal/AGENT.md` (PM 컨텍스트) + `docs/PROJECT.md` → 프로젝트 작업 요청 시
  - `.opal/MEMORY.md` → PM 컨텍스트 로드 시 함께 또는 온디맨드
- [ ] **부트스트랩 완료 보고 형식 갱신**: Eager ✅ / Lazy ⏳ 구분 반영

### 서브에이전트 부트스트랩 생략

- [ ] **`[WORKER]` 마커 감지 규칙**: AGENT.md에 "디스패치 프롬프트 상단에 `[WORKER]` 마커가 있으면 부트스트랩을 생략한다" 규칙 추가
- [ ] **오케스트레이터 디스패치 템플릿 갱신**: 모든 opal-pilot-* 스킬의 워커 디스패치 프롬프트 상단에 `[WORKER]` 마커 추가
- [ ] **PM 컨텍스트 주입 지침**: 워커에게 필요한 컨텍스트(하네스 핵심 규칙, 관련 참조 문서)를 PM이 디스패치 프롬프트에 포함하도록 오케스트레이터 지침 명시
  - 기존 "참조 문서 전달 의무"와 통합

### 플랫폼 공통 적용

- [ ] `opal/core/AGENT.md` 수정 단일 파일로 Claude Code / Cursor / Antigravity / Gemini 전 플랫폼에 자동 적용됨을 명시

## 제약 조건

- 워커 동작 방식은 변경하지 않는다 — 로드 시점/방식만 변경, 기능은 동일
- 각 스킬의 기존 Harness 폴백("부트스트랩에서 로드되지 않은 경우 Read") 패턴 유지
- `install-mac.sh` 배포 구조와 소스 구조 동기화 필수

## 기술 스택

- Markdown 문서 편집 (AGENT.md, 각 opal-pilot-* SKILL.md)
- OPAL 스킬/하네스 구조

## 관련 문서

- `opal/core/AGENT.md` — 부트스트랩 절차 소스 (핵심 수정 대상)
- `~/.opal/AGENT.md` — 배포본 (install-mac.sh로 자동 갱신)
- `~/.opal/references/opal-harness.md` — 하네스 (참조)
- `opal/core/skills/opal-pilot-*/SKILL.md` — 오케스트레이터 디스패치 섹션 (수정 대상)
- `docs/PROJECT.md` — 프로젝트 문서 레지스트리
