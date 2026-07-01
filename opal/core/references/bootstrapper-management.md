# OPAL 프로젝트 부트스트래퍼 자동 관리
> 설치/프로젝트 진입 시점 가이드(런타임 비행동). 탐색: ~/.opal/references/bootstrapper-management.md
> 출처: opal/core/AGENT.md §프로젝트 부트스트래퍼 자동 관리 (050 이관)

## 개요 (2-tier: 전역=비서/프로젝트=PM·이식성)

2-tier 모델에서 **전역 마커는 비서 tier를 상시 활성화**하고, **프로젝트 마커는 (Claude/Cursor/Codex) PM 승격을 강화하는 보조 신호이자 (Gemini/Codex) 이식성·폴백 트리거**다. PM 승격 게이트는 `.opal/AGENT.md` 존재이므로, 프로젝트 마커 유무는 PM 진입에 필수가 아니다. 자동 삽입 정책은 아래와 같다: **Antigravity(Gemini) 환경에 한해** 자동 삽입을 수행하고, Claude Code/Cursor/Codex는 전역 마커가 비서 tier를 상시 활성화하므로 자동 삽입을 수행하지 않는다.

## Claude Code — 자동 삽입 스킵

install-mac.sh가 `~/.claude/CLAUDE.md`(글로벌)에 OPAL 마커를 자동 삽입하여 모든 Claude Code 세션에서 비서 tier가 상시 활성화된다. PM 승격 게이트는 `.opal/AGENT.md` 존재이므로, 프로젝트 `CLAUDE.md` 마커는 PM 진입에 불필요(중복·무해)하다. 따라서 프로젝트 `CLAUDE.md` 자동 삽입은 **수행하지 않는다**.

이유:
- `~/.opal/` 미설치 환경에서는 마커가 있어도 무용 (Read 자체 실패)
- `~/.opal/` 설치 환경에서는 전역 마커가 비서 tier를 상시 활성화하며, PM 승격은 `.opal/AGENT.md` 존재 신호로 AGENT.md가 자동 수행
- → 프로젝트 `CLAUDE.md` 마커는 PM 진입에 불필요(중복·무해). 단 전역 마커가 임의 제거된 환경의 폴백 진입점으로 수동 삽입 가능

수동 삽입이 필요한 경우(글로벌 마커를 임의 제거한 환경 등)에는 아래 마커를 프로젝트 `CLAUDE.md`에 직접 추가한다:

```
# === OPAL START ===
## OPAL AI Agent — 필수 부트스트랩

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. 이 단계를 건너뛰면 안 된다.

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 AGENT.md의 온보딩 절차를 따른다)
# === OPAL END ===
```

## Cursor — 자동 삽입 스킵

`~/.cursor/rules/000-opal-agent.mdc`가 `alwaysApply: true`로 설정되어 모든 폴더에서 전역 비서 tier가 자동 활성화된다. PM 승격 게이트는 `.opal/AGENT.md` 존재이므로, 프로젝트 단위 `.cursorrules` 마커는 PM 진입에 불필요(중복·무해)하다. 따라서 프로젝트 단위 자동 삽입은 수행하지 않는다. 단 전역 마커가 없는 환경의 폴백 진입점으로 수동 삽입 가능.

## Codex — 자동 삽입 스킵

install-mac.sh가 `~/.codex/AGENTS.md`(글로벌)에 OPAL 마커를 자동 삽입하며, Codex CLI는 세션 시작 시 글로벌 → 프로젝트 순으로 AGENTS.md를 항상 자동 로드한다 ([Codex AGENTS.md 가이드](https://developers.openai.com/codex/guides/agents-md)). PM 승격 게이트는 `.opal/AGENT.md` 존재이므로, 프로젝트 `AGENTS.md` 마커는 PM 진입에 불필요(중복·무해)하다. 따라서 프로젝트 단위 `AGENTS.md` 자동 삽입은 **수행하지 않는다**.

이유:
- `~/.opal/` 미설치 환경에서는 마커가 있어도 무용
- `~/.opal/` 설치 환경에서는 전역 마커가 비서 tier를 상시 활성화하며, PM 승격은 `.opal/AGENT.md` 존재 신호로 AGENT.md가 자동 수행
- → 프로젝트 `AGENTS.md` 마커는 PM 진입에 불필요(중복·무해). 단 전역 마커가 없는 환경의 폴백 진입점 및 Codex 이식성 트리거로 수동 삽입 가능 (opi가 생성)

## Antigravity(Gemini) — 자동 삽입 수행

현재 프로젝트 루트의 `GEMINI.md`를 확인한다:

- **파일 있음 + `# === OPAL START ===` 마커 없음**: 파일 맨 아래에 부트스트래퍼를 추가
- **파일 있음 + 마커 있음**: 이미 삽입됨, 스킵
- **파일 없음**: 부트스트래퍼만 포함된 `GEMINI.md`를 새로 생성

삽입 내용은 위 Claude Code 절의 마커 블록과 동일하다. 2-tier 관점에서, Gemini는 전역 진입점이 Claude/Cursor/Codex와 달라 프로젝트 `GEMINI.md` 마커가 비서 tier 진입에 유효하다. 따라서 프로젝트 마커가 비서 tier 활성화의 실제 진입점이 되며, 이식성·폴백 트리거 역할을 함께 수행한다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-30 17:37 | AGENT.md §부트스트래퍼 자동 관리 이관 (050) |
