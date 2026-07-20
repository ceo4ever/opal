# PM 개선 루프 (Improvement Loop)

> 출처: opal/core/references/opal-pm.md §5
> 로드 시점: 태스크 CLOSE 회고 하드스텝 시 / `//opim` 온디맨드 시 / 판단이 불확실할 때 / 반복 패턴 감지 시
> 역할: 학습·개선 신호를 관찰→분류→기록한다 — prose 권고가 아니라 도구(improve-tool)로 결정론적 집행(tool-gated)

---

## 1. 두 트랙 개요

PM의 학습·개선은 입력 경로에 따라 **두 트랙**으로 나뉜다. 두 트랙 모두 최종적으로 §5 도구 집행(improve-tool)으로 수렴한다.

| 트랙 | 진입 경로 | 입력 | 집행 |
|------|----------|------|------|
| **A. 회고** | 태스크 CLOSE 하드스텝 — 자동 enforce(tool-gated) | 태스크/세션 궤적 신호(워커 재시도·폴백, 소유자 재지시·피드백, PM Gate 반복 이슈, PLAN 재진입, STATE.md 검증/재설계 루프 로그) | CLOSE 스텝 내 `improve-tool record` 직접 호출 |
| **B. 피드백·질문** | `//opim`(opal-improve) 온디맨드 + 피드백 nudge(soft) | 대화·L2·판단 불확실 시 질문 | opal-improve 5단계(§3) → `improve-tool record` |

**트랙 B 세부 — 질문 프로토콜**: PM 검토 기준·확정 기준에 없는 판단이 필요하면 소유자에게 질문한다(선택지와 영향을 정리하여 "A와 B 중 어느 방향이 맞을까요?"). 답변은 §4 기록 위치 테이블 기준으로 분류·기록한다. 다음 세션에서 확정 기준을 로드하면 해당 원칙은 재질문 없이 자동 적용된다.

> 두 트랙 모두 판단(분류)은 LLM(스킬/회고 스텝)이 수행하고, 기록(집행)은 improve-tool이 결정론적으로 수행한다 — 판단과 집행의 분리(`opal/skills/opal-improve/SKILL.md` §5 정합).

---

## 2. 트리거 테이블

| 시점 | PM 동작 | 트랙 |
|------|---------|------|
| 태스크 완료 시(CLOSE) | 이번 태스크에서 발견한 패턴/문제를 분석하고 개선 항목을 식별 → `improve-tool record` | A |
| 소유자 피드백 수신 시 | 피드백을 분류하여 즉시 반영(로컬 → 프로젝트 `.opal/`, FW → `~/.opal/fw-inbox/`) | B |
| 워커 실패/재지시 발생 시 | 실패 원인 분석 → 방지 규칙을 해당 에이전트/SSOT에 추가 | A/B |
| PM Gate에서 반복 이슈 감지 시 | "같은 유형의 문제가 2회 이상 발생"하면 확정 기준 후보로 기록 | A |
| 대화 중 새로운 결정 시 | 소유자와 합의된 방향을 즉시 해당 파일에 반영 | B |

> **지칭 정정**: 이 트리거 테이블은 본 문서(§2)가 유일한 SSOT다. 구 `self-improvement.md`가 "트리거 테이블은 opal-pm.md §5에 유지"라 지칭한 것은 오류였다(실제 표는 항상 이 문서에 있었다) — 문서 통합으로 지칭 오류가 소멸했다.

---

## 3. 5단계 프로세스

```
1. 관찰: 태스크/대화/궤적 신호에서 개선 대상 발견
2. 분류: 로컬 PM 개선 / FW 개선 (2원화 판단 — 1차 결정론 게이트 → 2차 경계 시 루브릭.
         상세 기준: opal/skills/opal-improve/SKILL.md §분류)
3. 기록: `improve-tool record --scope <local|fw> ...` 호출 (결정론 집행)
4. 보고: "개선 후보 N건 기록: {요약}" — 소유자에게 간략 보고
5. 승인: 소유자 이의 없으면 확정. 이의 있으면 조정.
```

- **no-op 안전** [MUST]: 개선 후보가 **없으면** 기록 없이 "개선후보 0건"으로 보고한다 — op-brain-ingest의 skipped 패턴과 동일하게 CLOSE를 차단하지 않는다.
- **역할 분리**: 판단(1~2단계)은 LLM, 기록(3단계)은 improve-tool(결정론), 보고·승인(4~5단계)은 PM↔소유자 대화.

---

## 4. 학습 2분류 + 기록 위치

개선 후보는 **로컬 PM 개선**과 **FW 개선** 2트랙으로 분류하여 각기 다른 목적지에 기록한다. 분류 판단 기준(결정론 게이트·루브릭)의 상세는 `opal/skills/opal-improve/SKILL.md` §분류 참조 — 이 표는 분류가 확정된 이후의 기록 위치 SSOT다.

| 발견 내용 | 분류 | 기록 위치 | 예시 |
|----------|------|----------|------|
| 프로젝트 공통 원칙 | 로컬 | `.opal/AGENT.md` 확정 기준 | "모든 API는 인증 필수" |
| PM 검토 기준 개선 | 로컬 | `.opal/AGENT.md` PM 검토 기준 | "회귀 테스트 커버리지 체크 추가" |
| BE 도메인 규칙 | 로컬 | `.opal/agents/opal-be-agent/AGENT.md` 확정 기준 | "camelCase 응답" |
| FE 도메인 규칙 | 로컬 | `.opal/agents/opal-fe-agent/AGENT.md` 확정 기준 | "shadcn Dialog 사용 시 Portal 필수" |
| DB 도메인 규칙 | 로컬 | `.opal/agents/opal-db-agent/AGENT.md` 확정 기준 | "soft delete 컬럼명 is_deleted" |
| 전문 에이전트 테이블 변경 | 로컬 | `.opal/AGENT.md` 전문 에이전트 섹션 | 새 에이전트 추가/제거 |
| 일회성 판단(이번만 적용) | 로컬 | `.opal/memory/` | 프로젝트 한정 임시 결정 |
| **에이전트 행동·스킬·도구·하네스 SSOT 개선** | **FW** | **`~/.opal/fw-inbox/`**(출처메타 포함 자기완결 항목, install 배포 경유 반영) | "회고 스텝 보고 형식 개선", "CLOSE 훅 순서 조정" |

- [MUST] 프레임워크-우선 원칙: 에이전트 행동 개선(보고형식·프로세스 등)은 개인 memory가 아니라 프레임워크 소스 SSOT 수정 대상이다 → `~/.opal/fw-inbox/`에 제안으로 적재한 뒤 소유자/PM 검토를 거쳐 install 배포 경로로 반영한다.
- **자기 개선 제한** [MUST]:
  - 기존 확정 기준의 수정/삭제는 소유자 승인 필수 — 추가만 자율, 변경/삭제는 제안 후 승인
  - 금지사항 추가는 소유자 승인 필수
  - 프레임워크 에이전트(`~/.opal/agents/`)는 수정하지 않는다 — 프로젝트 에이전트만 갱신

---

## 5. 도구 집행

학습 산출의 기록은 prose 권고가 아니라 **도구가 결정론적으로 집행**한다("Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." — `~/.opal/PRINCIPLES.md`).

| 집행 지점 | 도구/스킬 | 역할 |
|----------|----------|------|
| CLOSE 회고 하드스텝(트랙 A) | `~/.opal/tools/improve-tool/run.sh record --scope <local\|fw> ...` | 4-pilot(opd/opwt/opgc/oppd) CLOSE에서 직접 호출 |
| `//opim` 온디맨드(트랙 B) | `opal/skills/opal-improve/SKILL.md` | 관찰→분류→기록(improve-tool 호출)→보고→승인 |
| local scope 기록 | improve-tool → memory-tool 위임(`append --file <root>/.opal/MEMORY.md`) | `.opal/MEMORY.md` 부재 시 graceful skip(no-op) |
| fw scope 기록 | improve-tool → `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` write | 출처메타(host·project·situation·created) 포함 자기완결 |

모든 출력은 `{"ok":true/false, ...}` JSON 계약을 따른다(성공/실패/no-op 3경로 공통, `"ok"` 필드 항상 보장).

---

## 6. hook 미채택 근거 (플랫폼 독립)

Claude Code의 UserPromptSubmit(매 발화)·Stop(매 턴)·PostToolUse·git post/pre-commit 등 hook 계약을 검토했으나 전면 미채택했다.

| 사유 | 설명 |
|------|------|
| 빈번함 | 매 발화/매 턴 단위로 실행되어 신호 대비 잡음이 과다하다 |
| 플랫폼 종속 | hook은 Claude Code 전용 계약 — Cursor/Codex/Antigravity 등 타 플랫폼에서 재현 불가(`docs/CONVENTIONS.md` §플랫폼 분기 격리와 상충) |
| 의미 판단 불가 | bash 훅은 "개선 후보인가"를 판단할 수 없다 — 판단은 LLM 컨텍스트가 필요하다 |

대신 **태스크 CLOSE 하드스텝(트랙 A) + 순수 스킬 온디맨드(트랙 B)** 조합만 채택한다 — 세션 백스톱도 생략(hook 0개, 플랫폼 독립 100%).

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — opal-pm.md §5 분리 (128) |
| v2.0 | 2026-07-17 | **rename**(`pm-learning-loop.md` → `pm-improvement-loop.md`) + `pm/self-improvement.md` 내용 흡수(5단계 프로세스·기록위치 테이블·자기 개선 제한) + 6섹션 재구성(두 트랙 개요/트리거 테이블/5단계 프로세스/학습 2분류+기록위치/도구 집행/hook 미채택 근거) — 정의 3문서(opal-pm.md §5 stub·pm-learning-loop.md·self-improvement.md)를 단일 SSOT로 통합. `self-improvement.md`는 이 통합으로 삭제. 트리거 테이블 지칭 오류(§2) 소멸. improve-tool/opal-improve(`//opim`) 연결(§5 신설) (058)
