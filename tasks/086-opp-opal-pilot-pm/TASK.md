# TASK: opal-pm 레퍼런스 신규 구축 — PM 행동 프로세스 SSOT

> 작성일: 2026-04-05 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요구사항 + 현황 조사
> 출력: TASK.md

## 작업 목표

기존 opal-orchestrator 스킬을 **폐기**하고, PM 행동 프로세스를 **레퍼런스 문서 `opal-pm.md`**로 재설계한다. 현재 AGENT.md(글로벌)에 흩어진 PM 행동 규칙을 `opal-pm.md`로 통합하여 SSOT를 확보한다. PM이 프로젝트 문서를 종합적으로 읽고, 핵심 제약을 추출하여 워커에게 정확한 컨텍스트를 제공하며, 문서/코드 불일치 시 판단하는 프로세스를 정의한다.

레퍼런스로 두면 알투뿐 아니라 오케스트레이터, QA 에이전트, 워커 에이전트 등 **누구든 필요할 때 참조**할 수 있다.

## 배경

### 현황 조사 결과

**1. opal-orchestrator 스킬이 사용되지 않고 있음**

- `opal/skills/opal-orchestrator/SKILL.md`가 존재하지만 부트스트랩에서 실제로 Read하지 않음
- AGENT.md(글로벌)에 "opal-orchestrator/SKILL.md를 읽어 오케스트레이션 모드로 동작"이라고 명시되어 있지만, Eager 단계에서 스킵됨
- PM 행동 규칙은 AGENT.md + 하네스 + 각 오케스트레이터 SKILL.md에 분산

**2. PM이 프로젝트 문서를 정확하게 파악하지 않고 워커에게 지시**

- PM은 PROJECT.md 문서 테이블에서 경로만 확인하고 워커에게 전달
- 문서 내용을 직접 읽지 않아 핵심 제약을 모른 채 디스패치
- BACKEND.md → BE-FRAMEWORK.md 같은 문서 간 종속 관계를 파악하지 않음
- 결과적으로 워커가 문서를 읽어도 핵심 맥락 없이 형식적으로만 참조

**3. 문서/코드 불일치 시 판단하는 프로세스가 없음**

현재 흐름:
```
PM: 문서 경로만 전달 → 워커: 문서를 믿고 실행 → 코드와 다르면? → 아무도 안 잡음
```

이상적 흐름:
```
PM: 문서 Read → 핵심 제약 추출 → 워커에게 컨텍스트 주입
워커: 문서 + 실제 코드 모두 확인
  ├─ 일치 → 바로 실행
  └─ 불일치 → 코드(실질적 문서) 기준으로 작업 + PM에게 불일치 보고
PM: 불일치 사항을 opi 최신화 대상으로 기록
```

**4. PM 규칙이 분산된 현재 구조**

| 현재 위치 | 내용 | 문제 |
|----------|------|------|
| AGENT.md (글로벌) "PM 컨텍스트 로드" | 문서 테이블 읽기, 참조 문서 전달 의무 | AGENT.md가 비대해짐 |
| AGENT.md (글로벌) "PM 검토 게이트" | 워커 결과 검토 절차 | 분리해야 할 분량 |
| AGENT.md (글로벌) "PM 학습 루프" | 판단 불확실 시 질문 → 기록 | 동일 |
| 하네스 interactive §3 | PM Gate 체크리스트 확인 | 하네스에 유지 (프로세스 규칙) |
| opal-orchestrator SKILL.md | PM 행동 Step 1~6 | 사용되지 않는 유휴 스킬 |
| `.opal/AGENT.md` (프로젝트) | PM 프로필, 검토 기준, 금지사항 | 프로젝트별 설정이므로 유지 |

**5. 스킬이 아닌 레퍼런스가 적합한 이유**

- OPAL 스킬은 `//` 커맨드 또는 워커 디스패치로 호출하는 컴포넌트
- PM 행동 규칙은 호출하는 것이 아니라 **부트스트랩 시 로드하여 세션 내내 활성**
- 이 패턴은 기존 레퍼런스(`opal-harness.md`, `opal-model-mapping.md`)와 동일
- 레퍼런스로 두면 알투, 오케스트레이터, QA 에이전트, 워커 등 **누구든 필요 시 참조** 가능

## 요구사항

### 구조 정리

- [x] R1. opal-orchestrator 스킬을 **폐기**하고, `opal/core/references/opal-pm.md` 레퍼런스를 신규 생성한다
- [x] R2. AGENT.md(글로벌)의 PM 행동 규칙(PM 컨텍스트 로드, PM 검토 게이트, PM 학습 루프, 참조 문서 전달 의무)을 `opal-pm.md`로 이관한다. AGENT.md에는 `opal-pm.md` 위임 참조만 남긴다
- [x] R3. 부트스트랩 Eager 단계에서 `opal-pm.md`를 Read하도록 AGENT.md 부트스트랩 절차를 수정한다. 순서: harness(3단계) → opal-pm.md(신규 4단계) → .opal/AGENT.md(5단계). PM 행동 프로세스를 먼저 로드하고, 프로젝트 설정으로 구체화

### PM 문서 파악 프로세스

- [x] R4. PM 디스패치 전 프로세스 정의 — **매 디스패치마다** 동적으로 수행:
  1. PROJECT.md 문서 테이블을 Read하여 현재 등록된 문서 전체를 파악 (opi로 추가된 새 문서 포함)
  2. 현재 작업과 관련된 문서를 선별
  3. 선별된 문서를 직접 Read하여 핵심 제약을 추출 (예: "BaseMedia 상속 필수", "미들웨어 체계 준수")
  4. 문서 간 종속 관계 확인 (예: BACKEND.md → BE-FRAMEWORK.md 필수 참조)
  5. 핵심 제약 중 영구적 기준으로 추가해야 할 사항이 있으면 `.opal/AGENT.md` 확정 기준 추가를 제안
- [x] R5. 워커 컨텍스트 주입 강화: 문서 경로뿐 아니라 핵심 제약 요약 + 종속 문서 + "문서/코드 불일치 시 코드 우선, 불일치 보고" 지시를 포함

### 문서/코드 불일치 판단

- [x] R6. 워커 행동 규칙 추가: 문서와 실제 코드가 다를 경우 코드(실질적 문서) 기준으로 작업하고, 불일치 사항을 PM에게 보고
- [x] R7. PM이 불일치 보고를 받으면 opi 최신화 대상으로 기록하는 절차 정의

### 역할 분리

- [x] R8. `opal-pm.md`는 PM **행동 프로세스**(HOW)를 정의하고, `.opal/AGENT.md`는 프로젝트별 PM **설정**(WHAT — 검토 기준, 금지사항, 확정 기준)을 유지하는 역할 분리

## 제약 조건

- `.opal/AGENT.md`(프로젝트별 PM 설정)는 구조 유지. 내용 수정 없음
- 하네스의 Guards, Gates, State 구조는 변경하지 않음. PM Gate(interactive §3)는 하네스에 유지
- 플랫폼 독립 (Claude Code, Cursor, Gemini)
- 기존 오케스트레이터(opp/opds/opd)의 PM Gate 참조가 깨지지 않도록 호환 유지
- `opal-pm.md`는 레퍼런스 문서이므로 `//` 호출 대상이 아님. 스킬 레지스트리에 등록하지 않음

## 기술 스택

- Markdown (레퍼런스 문서, AGENT.md 수정)
- OPAL 프레임워크 레퍼런스 형식

## 관련 문서

- `opal/skills/opal-orchestrator/SKILL.md` — 기존 스킬 (폐기)
- `~/.opal/AGENT.md` — 글로벌 에이전트 정의 (PM 규칙 이관 원본)
- `opal/core/references/opal-harness.md` — 하네스 공통 (레퍼런스 패턴 참조)
- `opal/core/references/opal-harness-interactive.md` — interactive §3 PM Gate
- `.opal/AGENT.md` — 프로젝트별 PM 프로필 (유지)
- `docs/PROJECT.md` — 프로젝트 문서 테이블
