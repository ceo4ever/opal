# DONE: 루프 액션 에이전트 내부 디스패치 채널 opal-agent 전환 — 동기/비동기 이원화

> 완료일: 2026-07-17 18:27 (KST) | 스킬: opd | 모드: agentic (TASK 직후 semi-agentic→agentic 전환, 캡틴 지시)
> 판정: **All Pass** (TEST-SCENARIO S-1~S-9 전량, 에스컬레이션 0건)

## 요약

`opal-loop-action-agent`(루프 액션 에이전트)의 내부 4축 디스패치(생성자·Evaluator·test-agent·checker)를 플랫폼 Agent 도구에서 **opal-agent(claude headless CLI) 채널**로 전환했다. 호출 모드는 단계별 동기(G/T4a/T4b)/비동기(T1/T2/T3) 이원화 — "축=누구를(정체성) / 호출모드=어떻게(단계별)"의 직교 분리로 065 관측 릴레이 마찰(부모 턴 조기 종료·손자 보고 우회·생성자 재개 불가)을 구조적으로 제거했다. 샘플 태스크 실증에서 **PM 재개 지시 0회 완주 + T1→T3 동일 세션 resume + blocked 계약 유지**를 실측했다.

## 완료기준 대조 (TASK.md §명확화 결과)

| # | 완료기준 | 결과 | 증거 |
|---|---------|------|------|
| ① | 샘플 태스크 내부 워커 전원 opal-agent 채널 완주 — PM 재개 지시 0회 + 결과 계약 6필드 | **PASS** | S-8: samples/T01 완주(디스패치 1회·통지 1건), All Pass 6필드 반환, `.oppl-run/` 5축 3-분리 전부 exit 0 |
| ② | T1→T3 resume 연속성 실측(동일 session_id) | **PASS** | session.json UUID `9A63B6ED-…` = t1 = t3 session_id / S-7 독립 실측(합의어 회상 + session_id 동일) |
| ③ | 비가역 fixture blocked 반환 유지 | **PASS** | S-9: T02 blocked(트리거 #1), changed_files=[], 부수효과 0 |
| ④ | 결과 파일 규약 준수 실측(비동기 축) | **PASS** | S-6: 정상 exit 0·유효 JSON / 하드에러 exit 2·stdout 공백·err.log 채움 — 완료 마커(exitcode) 결정론 판별 |
| ⑤ | 문서 정합(AGENT.md·SKILL·하네스 변경이력 포함) | **PASS** | S-1~S-5: "Agent 도구" 내부 서술 잔존 0, 변경이력 4종(066), oppl T2=test-agent 정합, 065 계약 4종 회귀 보존 |

## 변경 파일 (프레임워크 소스 — install 배포 완료 v0.6.9-9)

| 파일 | 버전 | 변경 요지 |
|------|------|----------|
| `opal/agents/opal-loop-action-agent/AGENT.md` | v1.0→v1.1 | §실행 프로세스 재작성(단계×축×호출모드 매트릭스·동기/비동기 명령 형태·축별 timeout 배분·모델 레벨 치환·컨텍스트 재주입) + 신규 4절(§결과 파일 규약 3-분리·§생성자 resume(cold prime)·§allowedTools 표준(skip-permissions 금지)·§플랫폼 가용성(claude 1차)) |
| `opal/core/references/harness/observability.md` | v1.1→v1.2 | 아이콘 룩업 트리거 명확화(PM×Agent 도구) + opal-agent 내부 채널 적용 범위 제외 문단 |
| `opal/core/references/opal-harness.md` | v6.2→v6.3 | §5·§6에 opal-agent 채널 관측·모델 매핑 SSOT 포인터 각 1줄(비복제) |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | v1.2→v1.3 | 내부 디스패치 서술 opal-agent 채널 정합 + §디스패치 표 ①a/①b 분리(T2=test-agent(mode:red) — H-10 정정) |

## 핵심 설계 결정 (PLAN 확정, decision_required 0건)

- **축·호출모드 직교 분리**: 축=디스패치 대상 정체성(검증 2원화 근거), 호출모드=단계별 소요시간 판단 — test-agent가 T2(비동기)/T4a(동기)에서 다른 모드를 갖는 것은 모순 아님.
- **3-분리 캡처**: `.oppl-run/<phase>.{result.json,err.log,exitcode}` — 하드에러(exit 2) 시 stdout 공백이므로 완료 마커=exitcode 파일 존재(결정론). 스키마는 opal-agent 보장 5필드 한정(R-H 회피).
- **cold prime resume**: T1 전 UUID 확정(`--session-id`) → session.json 보존 → T3 `--resume` — 파싱 성공 여부와 무관하게 재개 명령 선조립 가능.
- **비동기 경계**: opal-agent는 블로킹 전용 — 비동기화는 호출측 Bash `run_in_background` 래핑(도구 개조 아님, TASK 범위 정합).
- **Observability 경계**: opal-agent 내부 채널은 아이콘 룩업 비대상 — 결과 파일·요약으로 자체 관측(관측 규칙 적용 범위 축소 정의).

## 불변 유지 (065 확정 계약)

검증 2원화 순서(065-H-9, 순서 evidence 실측: QA-SPEC 14:33:20 < T4a 14:35:31) · blocked 7종 트리거 · 3-SSOT 경계(test-tool scenario-*만) · 결과 계약 6필드 · PM→루프 액션 에이전트 채널 Agent 도구 유지.

## 프로세스 기록

- Gate 판단 9회(Pass 7/Fail 2 — ANALYSIS 출력계약 보완·PLAN 모델셀/네임스페이스 보완, 각 1회 재지시로 해소), EXECUTE FIX 1회(축별 timeout), 3회 초과 Gate 0건, 에스컬레이션 0건. 전체 이력: `AGENTIC-LOG.md` (23건+).
- 폴백 승인 2건: Write 도구 오탐(heredoc 작성) / 실증 디스패치 이름 호출 미등록(정의 경로 주입 — 065 선례, 세션 재시작 후에는 어댑터 이름 호출 가능).

## 후속 (백로그)

1. **067 (캡틴 확정)**: opal-agent **stream-json 개조 + journal 규약** — 워커 이벤트 기계 방출(events.jsonl, 결과 파일 규약 v2) + 루프 액션 에이전트 판단 일지. 투명 모니터링 완전판 (3종 경량판은 건너뜀 — heartbeat/prompt는 stream이 상위 호환).
2. 레포 `.gitignore`에 `.oppl-run/` 반영 (커밋 시 권장 — AGENT.md 권고 문구는 명문화됨).
3. oppl 풀 런(설계 루프→Loop 2 반복→종료조건) 실전 검증 + 구독 rate limit 실측(R-4)은 실전 `//oppl` 투입 시 자연 검증.

## 산출물

- 태스크: TASK.md / ANALYSIS.md / PLAN.md(v1.1) / TEST-SCENARIO.md(실행 완료) / AGENTIC-LOG.md / STATE.md·state.json / DONE.md(본 문서)
- 실증 증거: `samples/T01-정상슬라이스/`(.oppl-run 15파일·out/greeting.md·DONE.md) / `samples/T02-비가역트리거/`(부수효과 0)
