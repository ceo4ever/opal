---
name: opal-start
description: |
  **재진입 가이드 스킬** — 현재 OPAL 환경 상태를 진단하여 사용자에게 다음 액션을 권유한다. //start, "시작", "처음부터" 등으로 호출된다.
  반드시 이 스킬을 사용해야 하는 상황: 사용자가 //start 입력 시 / 첫 사용자가 무엇을 해야 할지 모를 때 / 온보딩 이후 재진입이 필요할 때.
triggers:
  - "//start"
  - "시작"
  - "처음부터"
  - "어디서부터 시작"
  - "다음에 뭐 해야"
  - "온보딩 다시 보고싶어"
version: 1.0.0
---

# opal-start — OPAL 재진입 가이드

## 목적

사용자가 OPAL 환경에서 어디서 막혔는지 진단하고, 다음 한 가지 액션을 명확하게 권유한다.

상세 진단·라우팅 흐름은 `references/start-flow.md`를 Read하여 참조한다.

## 프로세스

### Step 1: 환경 진단

다음 항목을 순차 점검한다 (Read/Bash 활용):

1. `~/.opal/identity.md` 존재 여부
2. `~/.opal/AGENT.md` 존재 여부 (OPAL 설치 확인)
3. 현재 작업 디렉토리(cwd)가 프로젝트인지 — 강신호: `.git/`, `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod`, `CLAUDE.md` / `GEMINI.md` / `.cursor/` 중 1개 이상 존재
4. cwd에 `.opal/AGENT.md` 존재 여부 (OPAL 프로젝트 초기화 여부)
5. cwd에 `docs/PROJECT.md` 존재 여부

점검 후 아래 형식으로 진단 결과 표를 출력한다:

```
[OPAL Start] 환경 진단 결과

| 항목 | 결과 |
|------|------|
| ~/.opal/identity.md | ✓ 있음 / ✗ 없음 |
| ~/.opal/AGENT.md (OPAL 설치) | ✓ 있음 / ✗ 없음 |
| cwd 프로젝트 여부 | ✓ 프로젝트 / - 비프로젝트 |
| .opal/AGENT.md (프로젝트 초기화) | ✓ 있음 / ✗ 없음 / - 해당없음 |
| docs/PROJECT.md | ✓ 있음 / ✗ 없음 / - 해당없음 |
```

### Step 2: 분기별 안내

진단 결과에 따라 다음 분기 중 하나를 권유한다. 분기 우선순위는 위에서 아래 순서로 적용한다.

| 진단 결과 | 권유 액션 |
|----------|----------|
| `~/.opal/AGENT.md` 부재 | "OPAL이 설치되지 않았습니다. one-liner로 설치하세요: `curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh \| bash`" |
| identity 부재 (OPAL 설치됨) | "에이전트 정체성을 먼저 설정합니다 — `//onboarding` 또는 자동 발화 대기" |
| identity 있음 + cwd 비프로젝트 | "비서 모드 진입. 프로젝트 작업이 필요하시면 프로젝트 폴더로 이동 후 `//opi`를 실행하세요. 일반 작업은 자연어로 요청하세요." |
| identity 있음 + cwd 프로젝트 + `.opal/AGENT.md` 부재 | "`//opi`로 이 프로젝트에 OPAL 환경을 초기화하세요" |
| identity 있음 + cwd 프로젝트 + `.opal/AGENT.md` 있음 + `docs/PROJECT.md` 있음 | "PM 모드 정상. 다음 중 선택하세요: `//opp <요청>` (범용 작업) / `//opds <요청>` (개발 Short Task) / `//opd <요청>` (개발 Full Task) / `//opi` (프로젝트 정의 갱신)" |
| identity 있음 + cwd 프로젝트 + `.opal/AGENT.md` 있음 + `docs/PROJECT.md` 없음 | "프로젝트 문서(docs/PROJECT.md)가 없습니다. `//opi`로 프로젝트를 재초기화하거나 PROJECT.md를 생성하세요." |
| 의존성·경로·MCP 등 시스템 이상 의심 | "`opal-cli doctor`로 의존성·경로·MCP·부트스트래퍼 정합성을 진단할 수 있어요. (미설치 시: `~/.opal/tools/doctor/run.sh`)" |

> **주의**: doctor 권유는 위 분기에서 해결되지 않는 이상 징후가 있을 때만 추가로 안내한다. 정상 경로에서는 생략한다.

상세 라우팅 흐름은 `references/start-flow.md`에 기술되어 있다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0.0 | 2026-05-09 00:00 | 초기 작성 (139) — //start 재진입 가이드 스킬 신규 |
