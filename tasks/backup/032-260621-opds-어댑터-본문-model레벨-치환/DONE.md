# DONE: install 어댑터 본문 model 레벨명 치환 — 액션 에이전트 sub-dispatch 모델 버그 수정

> 완료일: 2026-06-21 | 적용 스킬: opds | 모드: agentic | 상태: 완료(미커밋)

## 작업 결과 요약

install 어댑터(`emit_platform_agent_adapter`)가 에이전트 **본문(body)의 인라인 `model: <레벨>` sub-dispatch 토큰**도 frontmatter와 동일하게 플랫폼 실모델명으로 변환하도록 확장했다 (옵션 A — 캡틴 AskUserQuestion 확정). 이로써 oppd Phase 3 액션 에이전트(opal-task-action-agent·opal-sdd-action-agent)가 sub-worker 디스패치 시 레벨명(`advanced/standard/light`)을 Agent 도구 `model` enum에 그대로 전달해 실패하던 버그를 해소했다. 소스(에이전트 AGENT.md 본문)는 플랫폼 중립(레벨명)을 유지하고, 변환은 배포 시점 어댑터에서만 수행한다(플랫폼 분기 어댑터 격리 — 헌법).

## 변경 파일 (미커밋)

| 파일 | 변경 | F-ID |
|------|------|------|
| `scripts/install-mac.sh` | `_LEVEL_RE`+`_sub_body_model` 추가(`f.write(body)` 직전). 앵커 `[,(]\s*model:` 한정 + cursor `inherit` 토큰 제거 + sentinel 빈괄호 정리. changelog v3.3 | F-001, F-002, F-004 |
| `scripts/install/windows.ps1` | `Convert-BodyModelTokens` 신규(install-mac.sh 문자 단위 동일 정규식 미러) + Markdown·Codex TOML 양 경로 적용. changelog v1.14.0 | F-003 |
| `opal/core/references/agents.md` | §본문 처리 "변경 없이 복사" 무조건 진술 제거 + 인라인 model 토큰 변환/cursor/prose 예외 명시. changelog v1.8 | F-005 |

## 요구사항 충족 (F-001~F-005)

- **F-001** 본문 레벨 치환: GREEN 입증 (claude `opus`/`sonnet`, gemini 실모델명, 레벨명 0건) ✅
- **F-002** cursor inherit 엣지: cursor 본문 model 토큰 0건(오버라이드 제거), frontmatter inherit는 정상 유지 ✅
- **F-003** windows.ps1 미러: 정규식·ModelMap 4컬럼 동기 + 양 직렬화 경로 적용 ✅
- **F-004** 회귀 방지: be:89·db:130 prose 자기참조 불변, 비대상 11개 본문 diff 0, frontmatter 13개 불변 ✅
- **F-005** agents.md 문서 동기 + 변경이력 3곳(032) ✅

## 검증 (RED-first, PM 직접 재현)

- **RED**: 수정 전(HEAD) 어댑터 → 본문 레벨명 잔존(`model: advanced/standard`) 히트 확인
- **GREEN**: 수정 후 어댑터 → claude `opus/sonnet`·gemini 실모델명(바레-paren·백틱-paren 양 형태)·cursor 본문 토큰 0
- **회귀**: prose 자기참조 불변, 비대상 본문 diff 0, frontmatter 불변
- **정적**: `bash -n`·`py compile` PASS. 보안·배포경계 PASS. (PSScriptAnalyzer는 macOS pwsh 부재로 skip — Windows 실행 검증은 후속)
- TEST 판정: **All Pass** (8/0/1). PM Gate 강화 검토에서 어댑터 직접 재현으로 독립 확인.

## 처리 메모

- **P2(활성 플랫폼 dir 미변환)**: 세션 중 PLAN 워커 디스패치 실패로 발견 — 활성 디렉토리(`~/.claude_platform_mkt/agents/`)가 변환 안 된 raw 에이전트 보유. 캡틴 재배포로 frontmatter는 해소됨. 본 태스크는 P1(본문)에 집중.
- **R-3(031 충돌)**: PLAN 워커가 "031이 task-action-agent 본문에 `opus` 하드코딩"으로 decision_required 제기 → PM 직접 검증 결과 **오경보**(소스 `opus` 0건). task-action-agent도 정상 치환 대상으로 확정. 031의 미커밋 소스 변경은 model 토큰을 건드리지 않았고, 032는 에이전트 소스를 수정하지 않으므로 forward-compatible.

## 후속 (follow-up)

1. **[발효 조건] install 재배포(주입)** — 본 수정은 소스만 변경. 활성 env에 적용하려면 재배포 1회 필요(배포본 액션 에이전트 본문이 실모델명으로 변환되어야 sub-dispatch 정상 동작).
2. **[선택] install 배포 타겟 정합** — install-mac.sh가 `~/.claude/agents`만 하드코딩 타겟. 활성 플랫폼 디렉토리(`~/.claude_platform_mkt` 등) 정합은 별도 태스크 후보(P2 근본 해소, 비차단).
3. **[선택] Windows 실행 검증** — windows.ps1 미러는 정적 검토만 완료. Windows VM에서 `Convert-BodyModelTokens` 실행 검증.
4. **커밋** — 캡틴 지시 시 수행 (현재 미커밋).

## 산출물

- TASK.md / PLAN.md / TEST-SCENARIO.md / AGENTIC-LOG.md / DONE.md
