# TASK: oppl 태스크 실행자(opal-loop-action-agent) 도입 — 태스크 단위 컨텍스트 격리

> 작성일: 2026-07-17 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic (TASK 승인 시 캡틴 지시로 semi-agentic에서 전환)
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

oppl(opal-pilot-project-loop)의 태스크 내부 파이프라인(T1~T5+G)을 태스크당 1회 디스패치되는 중간층 실행자 에이전트 `opal-loop-action-agent`에 위임하여, 롱런 워크플로우에서 PM 세션의 컨텍스트 누적을 태스크당 결과 보고 1건 수준으로 격리한다.

## 배경

oppl은 규모 있는 프로젝트를 2-루프 수렴 구조로 완주시키는 롱런 워크플로우다. 현재 구조에서 실작업은 서브에이전트(생성자/Evaluator/test-agent)가 수행하지만, PM이 태스크 하나당 3~4회 디스패치와 그 사이의 게이트 판정·도구 호출·산출물 Read 검토를 전부 자기 세션에서 수행한다(`opal/skills/opal-pilot-project-loop/SKILL.md` §디스패치 — 하이브리드 C). 백로그가 태스크 10~20개면 PM 컨텍스트가 포화되고, 플랫폼 자동 요약(compaction)이 태스크 진행 중간의 임의 지점에서 발생하면 판단 품질이 저하된다.

## 배경 분석 (대화에서 도출)

- **현재 oppl 디스패치 구조**: 태스크당 ① 생성자(T1 설계+T2 시나리오) → ② Evaluator(G 명세 리뷰) → ③ 생성자 재개(T3 구현) → ④ test-agent(T4a) 순으로 PM이 직접 지휘. T4b(규칙검사)는 저위험 시 PM 인라인 (`opal/skills/opal-pilot-project-loop/SKILL.md` §디스패치 (하이브리드 C)).
- **oppd 선례**: `opal/agents/opal-task-action-agent/AGENT.md`는 oppd Phase 3에서 개별 액션을 자율 실행하는 중간층 에이전트로, 자신이 Agent 도구로 기존 워커(opal-task-agent·opal-task-qa-agent·opal-test-agent)를 재디스패치하여 PLAN→QA→EXECUTE→VERIFY→TEST를 완주한다. PM은 액션당 디스패치 1회 + 결과 1건만 수신. opsdd에도 동형 선례(`opal-sdd-action-agent`) 존재.
- **중간층 에이전트의 수명 특성**: 디스패치 인스턴스는 태스크 완료 시 소멸하므로, 태스크마다 컨텍스트가 제로에서 시작한다 — 소유자가 원한 "태스크별 세션 격리"가 /clear·러너 없이 플랫폼 안에서 구현되는 구조.
- **oppl이 현재 잘게 쪼갠 이유**: [MUST] `opal/skills/opal-pilot-project-loop/SKILL.md` §디스패치: "생성자 디스패치는 opal-task-action-agent류의 자율 완주(PLAN→EXECUTE→VERIFY)가 아니라 T1~T3 범위로 한정된 지시임에 유의한다(G 게이트가 T2와 T3 사이를 끊는다)" — 검증 2원화(생성자≠평가자, H-9)를 PM 손에서 보장하려는 설계. 단 oppd 선례처럼 중간층이 Evaluator를 **별도 에이전트로** 내부 디스패치하면 생성자≠평가자 분리는 유지된다.
- **tool-gated 증거의 사후 검증 가능성**: RED-first·G 게이트 증거는 test-tool(scenario-red/lock/mark)의 tool-gated 상태값으로 남으므로, PM이 실행자 완료 후 파일로 검증 가능 (`opal/skills/opal-pilot-project-loop/SKILL.md` §태스크 내부 파이프라인 T2).

## 확정된 설계 방향 (대화에서 합의)

1. **계층 구조**: 알투(PM, 세션 유지)가 루프 수준 판단(L0 태스크 선택·L∞ 관찰·done-check·사람 게이트·소유자 보고)을 유지하고, 태스크 내부(T1~T5+G)만 실행자에게 위임한다. 실행자는 태스크 1개 수명의 일회용 인스턴스다(상주 부PM 아님 — 상주형은 누적 문제가 실행자로 이전되므로 배제).
2. **에이전트 명명**: 기존 계열 관례(oppd→opal-task-action-agent, opsdd→opal-sdd-action-agent)를 따라 `opal-loop-action-agent`로 명명한다.
3. **검증 2원화 보존**: 실행자가 생성자(fe/be/db/task)·Evaluator·test-agent를 **각각 별도 에이전트로** 내부 디스패치하여 생성자≠평가자(H-9)를 유지한다.
4. **사람 게이트 불변**: 비가역 행동(배포·DB·확정)과 에스컬레이션은 실행자에게 위임하지 않는다. 실행자는 blocked 상태로 결과만 반환하고, PM이 소유자에게 에스컬레이션한다.
5. **결과 계약 반환**: 실행자는 완료 시 압축 결과 계약({태스크ID, verdict, 시나리오 결과, 변경 파일, DONE.md 경로, 특이사항})만 PM에게 반환한다.
6. **범위 제외 (후속 검토)**: A(`--resume` 재개 프로토콜)·컨텍스트 감지 자동화(context-check 도구)는 이번 태스크에서 제외한다 — 소유자가 추가 고민 후 별도 검토하기로 확정.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | oppl 태스크 내부 파이프라인(T1~T5+G)을 일회용 실행자 `opal-loop-action-agent`에 위임하여 PM 컨텍스트 누적을 태스크당 결과 보고 1건 수준으로 격리 | - | oppd `opal-task-action-agent` 선례 구조 |
| 범위 | 포함: 신규 에이전트 정의 + oppl SKILL.md 디스패치·태스크 내부 파이프라인 절 개편 + 관련 references 정합 + install 배포 반영. 제외: `--resume` 재개 프로토콜, 컨텍스트 감지 자동화(후속 검토), oppd/opsdd 변경 없음 | - | 소유자 확정(범위 제외 §6) |
| 제약 | 검증 2원화(생성자≠평가자, H-9) 유지 / 사람 게이트·CLOSE 게이트 불변 / 3-SSOT tool-gated 원칙 유지 / `~/.opal/` 직접 수정 금지(프로젝트 소스 수정 후 install) / 변경이력 표 갱신 의무 | - | `.opal/AGENT.md` §금지사항 |
| 완료기준 | ① `opal/agents/opal-loop-action-agent/AGENT.md` 존재 + 입력 명세·내부 파이프라인·결과 계약 정의 ② oppl SKILL.md가 태스크당 실행자 1회 디스패치 구조로 개편 ③ 실행자 디스패치 실증(테스트 시나리오 PASS) ④ 하네스 상한·에스컬레이션 계약이 문서에 명시 | - | TEST-SCENARIO에서 검증 시나리오 확정 |

## 요구사항

- [ ] R-1 **신규 에이전트 정의**: `opal/agents/opal-loop-action-agent/AGENT.md`를 생성한다. 왜: 확정 방향 §1·§2. AC: 입력 명세(task_id, task 폴더, CONTRACT 경로, area, project_context 등)·내부 파이프라인(T1~T5+G, 생성자/Evaluator/test-agent 별도 디스패치)·결과 계약(확정 방향 §5의 6필드)·재시도 상한(하네스 §1 참조, 수치 복제 금지)·blocked 반환 계약이 모두 섹션으로 존재한다.
- [ ] R-2 **oppl SKILL.md 개편**: `opal/skills/opal-pilot-project-loop/SKILL.md`의 §디스패치(하이브리드 C)·§태스크 내부 파이프라인을 태스크당 실행자 1회 디스패치 구조로 개편한다. 왜: 배경 분석(현재 PM이 태스크당 3~4회 개입). AC: 디스패치 표가 실행자 1회 기준으로 갱신되고, "T1~T3 한정 지시" 문구가 실행자 위임 구조로 대체되며, PM의 L0/L∞/게이트 소유는 변경 없음이 명시된다.
- [ ] R-3 **검증 2원화·게이트 계약 보존 명시**: 개편된 문서에 생성자≠평가자 유지 방식(실행자의 별도 에이전트 내부 디스패치)과 사람 게이트·에스컬레이션 비위임을 명시한다. 왜: 확정 방향 §3·§4. AC: H-9 순서 불변 참조와 blocked 에스컬레이션 경로가 SKILL.md 또는 AGENT.md에 원문으로 존재한다.
- [ ] R-4 **references 정합**: `opal/skills/opal-pilot-project-loop/references/`(loop-control.md·verification.md·contract.md) 중 하이브리드 C 전제로 서술된 부분을 실행자 구조와 모순 없게 갱신한다. 왜: 문서 간 불일치 방지. AC: "하이브리드 C" 언급 지점 전수 확인 + 갱신 또는 유지 근거 기록, 변경 문서마다 변경이력 행 추가.
- [ ] R-5 **배포 반영**: 신규 에이전트가 install 경로에 포함되는지 확인하고 필요 시 반영한다. 왜: `.opal/AGENT.md` §업무 수행 지침(배포 경계). AC: install 실행 후 `~/.opal/agents/opal-loop-action-agent/` 존재(또는 어댑터 산출 확인).
- [ ] R-6 **동작 실증**: 실행자 1회 디스패치로 샘플 태스크(T1~T5+G)가 완주되고 결과 계약이 반환됨을 실측한다. 왜: PRINCIPLES §4(완료는 검증된 동작). AC: TEST-SCENARIO.md의 해당 시나리오 PASS + 증거 기록.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "하네스 우회 금지 — Guards/Gates를 PM 임의 판단으로 건너뛰지 않는다 (특히 CLOSE 진입 게이트)."
- [MUST] `opal/skills/opal-pilot-project-loop/references/loop-control.md` §2: "구체적 재시도 횟수·최대 반복 수는 여기서 새로 정의하지 않는다" — 실행자 문서도 하네스 §1 표를 참조만 하고 수치를 복제하지 않는다.
- 검증 2원화 순서 불변(H-9): Evaluator(구현 전) → test-agent(구현 후) 순서가 실행자 내부에서도 유지되어야 한다 (`opal/skills/opal-pilot-project-loop/references/verification.md` §3).
- oppd(opal-task-action-agent)·opsdd(opal-sdd-action-agent)는 이번 태스크에서 수정하지 않는다.

## 기술 스택

- Markdown 문서 프레임워크 (스킬·에이전트 정의: SKILL.md / AGENT.md)
- Node.js (OPAL tools — state-tool/backlog-tool/test-tool, 이번 태스크에서 코드 변경 없음 예상)
- Bash (install-mac.sh 배포 어댑터 — R-5 확인 대상)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 개편 대상 본문 — §디스패치·§태스크 내부 파이프라인 |
| D-2 | 설계 | oppd 액션 에이전트 (선례) | `opal/agents/opal-task-action-agent/AGENT.md` | 실행자 구조·입력 명세·내부 재디스패치 패턴의 준거 |
| D-3 | 설계 | 루프 제어 가이드 | `opal/skills/opal-pilot-project-loop/references/loop-control.md` | §2 상한 참조 원칙·§8 컨텍스트 관리와의 정합 |
| D-4 | 설계 | 검증 가이드 | `opal/skills/opal-pilot-project-loop/references/verification.md` | H-9 순서 불변·결과 계약 스키마(§5) |
| D-5 | 설계 | 공통 하네스 | `opal/core/references/opal-harness.md` | §1 자동 루핑 제약(수치 SSOT)·§7 병렬 원칙 |
| D-6 | 설계 | PM 프로필 | `.opal/AGENT.md` | 금지사항·검토 기준(재사용성·플랫폼 독립성·하네스 준수) |
