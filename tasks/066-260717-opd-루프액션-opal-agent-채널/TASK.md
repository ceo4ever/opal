# TASK: 루프 액션 에이전트 내부 디스패치 채널 opal-agent 전환 — 동기/비동기 이원화

> 작성일: 2026-07-17 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청 (065 후속 — 릴레이 마찰 구조 해소)
> 출력: TASK.md

## 작업 목표

`opal-loop-action-agent`(루프 액션 에이전트)의 내부 4축 디스패치(생성자·Evaluator·test-agent·checker)를 플랫폼 Agent 도구에서 **opal-agent(headless CLI 위임)**로 전환한다. 호출 모드는 단시간 축=동기 / 장시간 축=비동기+결과 파일로 이원화하여, 065 실증에서 확인된 비동기 릴레이 마찰(부모 턴 조기 종료·손자 보고 우회)을 구조적으로 제거한다.

## 배경

065에서 루프 액션 에이전트를 도입해 태스크당 1회 디스패치 구조를 실증했으나, 내부 디스패치(Agent 도구)에서 3가지 마찰이 관찰되었다: ① 부모(루프 액션 에이전트)가 자식 완료 통지를 받지 못하고 턴을 조기 종료(3회, PM 재개 지시로 커버) ② 손자 워커의 보고가 부모가 아닌 PM 메인으로 우회 도달 ③ 서브에이전트 간 메시징 제약으로 T1 생성자의 T3 재개가 사실상 불가(oppl 하이브리드 설계의 핵심 요소 유실). 근거: `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md` #12d·#12e.

## 배경 분석 (대화에서 도출)

- **opal-agent 능력 실측 현황**: `opal/tools/opal-agent/README.md` — claude/codex E2E 실측 완료(단발·resume·JSON), gemini/grok/cursor는 명령 조립 검증 수준. `--resume <session_id>`(claude)로 세션 이어가기 지원, `--session-id` cold 지정 가능(059).
- **동기/비동기 특성**: `claude -p`는 비대화형이지만 호출 관점에서 동기(블로킹). 단 Bash 도구 타임아웃(기본 2분·최대 10분)이 동기성의 상한 — 장시간 워커(T1 설계·T3 구현)는 백그라운드 실행 + 결과 파일 수거가 필요(캡틴 확인 사항).
- **비동기 결과 수거의 결정론성**: opal-agent는 JSON을 stdout으로 내므로 파일 리다이렉트 시 프로세스 무관 매체(파일)로 결과가 남음 — Agent 도구의 통지 채널 불안정과 달리 부모가 언제 깨어나도 Read로 확정 수거.
- **부트스트랩 시너지**: `[WORKER]` 첫 줄 마커(3단 스킵 사다리, 059)가 headless 호출 전제로 설계되어 있어 워커 프롬프트 규약 재사용 가능.
- **비용 계정**: claude -p는 소유자 구독을 소비(콘솔 브레인 선례 — `memory/console-brain-subscription-auth.md`: API키·SDK 금지, 구독 로컬 claude -p). 태스크당 내부 프로세스 4~5개의 rate limit 영향 실측 필요.
- **하네스 전제**: 디스패치 의무·Observability(§5)·모델 매핑이 Agent 도구 전제로 서술됨 — opal-agent 채널 항목 보강 필요.
- **선행 개선**: ANALYSIS 워커 model light→standard 상향은 캡틴이 별도 커밋(cb69e28)으로 이미 반영.

## 확정된 설계 방향 (대화에서 합의)

1. **채널 단일화**: 루프 액션 에이전트의 내부 4축 전부 opal-agent 호출로 통일한다 (릴레이 지침 방식 ①안 배제 — 마찰의 구조적 제거).
2. **호출 모드 이원화**: 단시간 축(G 명세 리뷰·T4a 검증 실행·T4b 규칙검사) = 동기 호출 / 장시간 축(T1 설계+T2 시나리오·T3 구현) = 비동기(백그라운드) + 결과 파일 수거.
3. **생성자 연속성**: T1 생성자의 session_id를 보존하여 T3에서 `--resume`으로 재개한다 (하이브리드 설계의 "생성자 재개" 복원).
4. **결과 파일 규약 신설**: 경로·JSON 스키마·완료 마커를 계약으로 정의한다 (수거 결정론성의 SSOT).
5. **권한 표준**: 프로젝트 스코프 한정 `--allowedTools` 세트를 표준화한다. `--dangerously-skip-permissions` 사용 금지.
6. **1차 릴리스 범위**: claude 플랫폼 한정 명시 (opal-agent E2E 실측 완료 범위). 타 플랫폼은 점진 검증.
7. **불변 사항**: PM→루프 액션 에이전트 디스패치는 Agent 도구 유지(전환 대상은 내부 축만). 검증 2원화(H-9)·blocked 계약·3-SSOT 경계·결과 계약 6필드는 065 확정 그대로.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 루프 액션 에이전트 내부 4축 디스패치를 opal-agent 채널(동기/비동기 이원화 + resume 연속성)로 전환하여 릴레이 마찰 제거 | - | opal-agent claude E2E 실측 완료 |
| 범위 | 포함: AGENT.md 개정·결과 파일 규약·allowedTools 표준·하네스 §5/디스패치 규정 보강·oppl SKILL 정합·동작 실증. 제외: PM→루프 액션 에이전트 채널(Agent 도구 유지), oppd/opsdd 액션 에이전트 전환, claude 외 플랫폼 E2E, opal-agent 도구 자체의 기능 개조(기존 기능 범위 내 사용 원칙 — 부족 시 PLAN에서 decision_required) | 결과 파일 규약의 구체 스키마·경로는 PLAN에서 설계 | `opal/tools/opal-agent/README.md` |
| 제약 | `--dangerously-skip-permissions` 금지 / 구독 소비 고려 병렬도 제한 / 하네스 SSOT(`opal/core/references/`) 수정 시 발췌·복제 금지 원칙 / 재시도 수치 비복제(harness §1 포인터) / `~/.opal/` 직접 편집 금지 / H-9·blocked·3-SSOT·결과 계약 6필드 불변 | - | `.opal/AGENT.md` §금지사항, 065 확정 계약 |
| 완료기준 | ① 샘플 태스크(065 S-7급)를 내부 워커 전원 opal-agent 채널로 완주 — **PM 재개 지시 0회** + 결과 계약 6필드 반환 ② T1→T3 resume 연속성 실측(동일 session_id) ③ 비가역 fixture blocked 반환 유지 ④ 결과 파일 규약 준수 실측(비동기 축) ⑤ 문서 정합(AGENT.md·SKILL·하네스 변경이력 포함) | - | TEST-SCENARIO에서 시나리오 확정 |

## 요구사항

- [ ] R-1 **AGENT.md 내부 디스패치 절 개정**: `opal/agents/opal-loop-action-agent/AGENT.md`의 4축 디스패치 서술을 opal-agent 호출(동기/비동기 이원화 + `[WORKER]` 마커 + 모델 매핑)로 교체. 왜: 확정 방향 §1·§2. AC: 4축 각각의 호출 모드(동기/비동기)·명령 형태·결과 수거 방식이 절로 존재하고, Agent 도구 내부 디스패치 서술이 잔존하지 않는다.
- [ ] R-2 **결과 파일 규약**: 비동기 축의 결과 파일 경로 규칙·JSON 스키마·완료 판정 방법을 AGENT.md(또는 references)에 계약으로 정의. 왜: 확정 방향 §4. AC: 경로 규칙·필수 필드·완료 마커·수거 실패 시 처리(재시도/blocked)가 명문화된다.
- [ ] R-3 **생성자 resume 연속성**: T1 완료 시 session_id 보존 → T3 `--resume` 재개 절차 명문화. 왜: 확정 방향 §3. AC: session_id 보존 위치와 재개 명령 형태가 문서에 존재하고 실증(R-7)에서 동일 세션 재개가 관측된다.
- [ ] R-4 **권한 표준(`--allowedTools`)**: 내부 워커용 표준 allowlist 세트 정의(프로젝트 스코프 한정). 왜: 확정 방향 §5. AC: 축별 allowlist가 문서화되고 `--dangerously-skip-permissions` 금지가 명문화된다.
- [ ] R-5 **하네스·oppl 정합**: 하네스 디스패치/Observability 서술에 opal-agent 채널 항목 보강 + oppl SKILL.md 내부 디스패치 언급 정합 + 각 변경이력 행. 왜: 배경 분석(하네스 전제). AC: 하네스 §5(또는 해당 절)에 opal-agent 채널 규칙 존재, oppl SKILL과 AGENT.md 서술 모순 없음, 변경 문서 전부 변경이력 행(066).
- [ ] R-6 **1차 범위 명시**: claude 한정 릴리스와 타 플랫폼 점진 검증 계획을 AGENT.md에 명시. 왜: 확정 방향 §6. AC: 플랫폼 가용성 표(또는 문구)가 존재한다.
- [ ] R-7 **동작 실증**: 065 S-7/S-8급 샘플로 opal-agent 채널 완주 실증 — 재개 지시 0회, resume 연속성, blocked 유지, 결과 파일 수거 실측. 왜: PRINCIPLES §4. AC: TEST-SCENARIO 해당 시나리오 전부 PASS + 증거 기록.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `memory/console-brain-subscription-auth.md`: 구독(로컬 claude -p) 사용 — API키·SDK 금지 선례 준수.
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: 재시도 수치 비복제 — harness §1 포인터 유지.
- 065 확정 계약 불변: 검증 2원화 순서(H-9)·blocked 7종 트리거·3-SSOT 경계(test-tool만)·결과 계약 6필드.
- Bash 타임아웃(기본 2분·최대 10분)이 동기 호출의 상한 — 장시간 축은 반드시 비동기.

## 기술 스택

- Markdown (AGENT.md/SKILL.md/하네스 문서)
- Python/Bash (opal-agent — `~/.opal/tools/opal-agent/run.sh`, 표준 라이브러리만. 이번 태스크는 기존 기능 범위 내 사용이 원칙, 개조 필요 판단 시 PLAN decision_required)
- Claude Code headless (`claude -p`, `--resume`, `--allowedTools`, `--output-format json`)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 루프 액션 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 개정 대상 — 내부 디스패치 절 |
| D-2 | 소스 | opal-agent 도구 | `opal/tools/opal-agent/README.md`, `opal_agent.py` | 채널 능력 SSOT — 동기/resume/JSON/플랫폼 매핑 |
| D-3 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 정합 대상 — 내부 디스패치 언급 |
| D-4 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` §5·§6 | Observability·모델 매핑 보강 지점 |
| D-5 | 기록 | 065 AGENTIC-LOG | `tasks/065-260717-opd-oppl-태스크-실행자/AGENTIC-LOG.md` #12d·#12e | 릴레이 마찰 실측 근거 |
| D-6 | 설계 | 에이전트 마커 3-way | `tasks/059-*/` 산출물 (git log 10b3912 이전) | `[WORKER]`·`--session-id` 설계 근거 |
