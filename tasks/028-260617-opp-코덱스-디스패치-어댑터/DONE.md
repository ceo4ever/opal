# DONE: Codex 워커 디스패치 어댑터 정합

> 완료일: 2026-06-17 16:34 | 적용 스킬: opp | 모드: agentic
> 입력: TASK.md / PLAN.md | 결과: 어댑터 문서 3종 + install 스크립트 2종 정합

## 요약

Codex CLI에서 OPAL 워커 디스패치가 동작하도록 어댑터 계층을 정합했다. 핵심 발견은 **Codex tool-backed 세션(모델이 도구로 자율 디스패치하는 경로 = OPAL 스킬의 워커 호출 경로)에서는 커스텀 에이전트 이름 기반 호출이 노출되지 않는다**는 점([Issue #15250](https://github.com/openai/codex/issues/15250), OPEN)이며, 공식 우회법인 **인라인 주입**(PM이 `~/.opal/agents/<name>/AGENT.md` 본문을 generic `spawn_agent`의 message에 주입)을 어댑터 문서에 규칙으로 명문화했다. `.toml` 생성은 스펙 정합·대화형 호명에 유효하므로 유지한다. 헌법(플랫폼 독립)을 준수하여 `opal/core/AGENT.md`에는 분기를 추가하지 않고 어댑터(agents.md)에만 규칙을 두었다.

## 변경 파일

| 파일 | 변경 내용 | 요구사항 |
|------|----------|---------|
| `opal/core/references/agents.md` | 메커니즘 표 Codex 행 + frontmatter 변환 표 Codex 컬럼 + §Codex tool-backed 인라인 주입 규칙 신설 + 함수 참조 codex 추가 (v1.7) | R-1, R-2 |
| `opal/core/references/pm/dispatch-process.md` | Step 0 직후 Codex tool-backed 인라인 주입 포인터 (v1.5) | R-3 |
| `opal/core/references/opal-model-mapping.md` | install 정합 기록 + 인라인 주입 model 매핑 참조 (v1.5) | R-6 |
| `scripts/install-mac.sh` | `install_codex_config` 신설(config `[agents]` 멱등 작성) + 호출부 연결 + stale Codex 매핑 2개소 정정 (v3.2) | R-4, R-6 |
| `scripts/install/windows.ps1` | `Install-CodexConfig` 미러 + 호출부 연결 + ModelMap 정정 (v1.13.0) | R-5, R-6 |

## 검증 (PM Gate 강화 검토 — 직접 검증)

- 불변식: `git diff opal/core/AGENT.md` 빈 결과 (헌법 분기 금지 준수)
- 멱등성 실테스트: `install_codex_config` 3회 실행 → `[agents]` 1건, 기존 `[mcp_servers]`·`[projects]` 보존
- 모델 매핑 4지점 동일: agents.md·opal-model-mapping.md·install-mac.sh·windows.ps1 모두 `gpt-5.4-mini/gpt-5.4/gpt-5.5`
- 실제 코드 `gpt-5.3-codex` 0건 (변경이력 history 줄에만 잔존 = 정상)
- `bash -n scripts/install-mac.sh` 통과, windows 헬퍼(`$Utf8NoBom`/`Write-Opal*`) 정의 확인
- `.toml` 생성 로직 유지, Claude/Cursor/Gemini 어댑터 불변, 변경이력 5문서 기재
- 실배포 확인: `~/.codex/config.toml`에 `[agents]`(max_threads=6/max_depth=1/job_max_runtime_seconds=1800) 작성됨

## 부수 성과

- install 3개소의 일몰 예정 모델(`gpt-5.3-codex`, 2026-06-30 일몰) stale을 발견·정정하여 SSOT v1.4와 정합화 (R-6 확대, PM 승인 — AGENTIC-LOG #4)

## 동작 검증 결과 (대화형 TUI)

- `/agent`(단수) = **실행 중 서브에이전트 스레드 watch 피커**이지 정의 목록이 아님 (공식: "Switch the active agent thread"). 캡틴 화면에 `Main [default]`만 보인 것은 정상 — spawn된 서브에이전트가 없기 때문.
- `~/.codex/agents/` 정의를 나열하는 슬래시 커맨드는 Codex에 없음. 커스텀 에이전트는 **자연어 호명**으로 spawn된다.

## 후속 (미해결 / 별도 태스크 권장)

1. **인라인 주입 실증**: Codex tool-backed에서 generic `spawn_agent`에 AGENT.md 본문을 주입하는 최소 재현으로 실제 spawn 동작 확인 (028은 문서·어댑터 정비까지, 런타임 실증은 미수행).
2. **model 핀 검증**: toml `model = "gpt-5.4"`가 캡틴 Codex(ChatGPT-auth)에서 실사용 가능한 ID인지 확인. 거부 시 매핑 핀 재점검.
3. **max_depth 검토**: 현재 `max_depth=1`(PM→워커 1단계). 워커의 중첩 디스패치가 필요하면 `2`로 상향 (커뮤니티 가이드는 2 사용).
4. **multi_agent_v2 검토**: v1 한계 시 `codex features enable multi_agent_v2` 효과 평가 (단, [#20077](https://github.com/openai/codex/issues/20077) — v2 spawn_agent의 fork 기본값/override 거부 이슈 확인 필요).

## 참조

- [Codex Subagents](https://developers.openai.com/codex/subagents) / [Slash Commands](https://developers.openai.com/codex/cli/slash-commands) / [Config Reference](https://developers.openai.com/codex/config-reference)
- [Issue #15250](https://github.com/openai/codex/issues/15250) — tool-backed 이름호출 불가 + 인라인 주입 우회법
- brain: `.opal/brain/pages/concept/codex-platform-integration.md` (task 009 통합 맥락)
- AGENTIC-LOG: `tasks/028-260617-opp-코덱스-디스패치-어댑터/AGENTIC-LOG.md`
