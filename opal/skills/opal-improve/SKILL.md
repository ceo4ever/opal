---
name: opal-improve
description: |
  **PM 개선 루프 온디맨드 스킬(`//opim`)** — 관찰→분류→기록→보고→승인 5단계로 개선 후보를 로컬 PM 개선(프로젝트 `.opal/`) 또는 FW 개선(`~/.opal/fw-inbox/`)으로 분류하여 improve-tool로 결정론적으로 기록한다.
  반드시 이 스킬을 사용해야 하는 상황: "개선 제안", "프레임워크 개선", "개선 기록", "회고" 등 소유자가 개선 논의를 시작하거나 PM이 판단 불확실·반복 패턴을 감지했을 때(트랙 B — 피드백·질문 온디맨드).
  트랙 A(태스크 CLOSE 회고 하드스텝)의 참조 모델이기도 하다 — 4-pilot(opd/opwt/opgc/oppd) CLOSE 회고 스텝은 본 스킬의 관찰→분류→기록 프로세스를 그대로 참조한다.
alias: opim
triggers:
  - "^opal-improve$"
  - "^opim$"
  - "(?i)(개선\\s*제안|프레임워크\\s*개선|개선\\s*기록|회고)"
version: "1.0"
domain: improvement
---

# opal-improve — PM 개선 루프 (`//opim`)

## 역할

PM의 학습·개선 신호를 **관찰→분류→기록→보고→승인** 5단계로 처리하는 온디맨드 스킬이다. prose 권고가 아니라 `improve-tool`이 결정론적으로 기록을 집행한다(tool-gated) — 판단(1~2단계)은 이 스킬(LLM)이 수행하고, 기록(3단계)은 도구가 전담한다.

- **SSOT**: `opal/core/references/harness/pm-improvement-loop.md` — 두 트랙 개요·트리거 테이블·5단계 프로세스·학습 2분류/기록위치·도구 집행·hook 미채택 근거의 단일 근거 문서다. 본 SKILL.md의 §분류(STEP 2)는 그 SSOT §4가 참조하는 상세 기준 본체다.
- **진입 경로**: 소유자가 개선을 직접 제안할 때, PM이 판단 불확실 시 질문할 때, 반복 패턴(같은 유형 문제 2회 이상)을 감지했을 때, 또는 대화 중 소유자와 새 방향이 합의됐을 때.
- **참조 관계**: 태스크 CLOSE 회고 하드스텝(트랙 A, 4-pilot)은 격리된 오케스트레이터 인라인 스텝이라 이 스킬을 직접 호출하지는 않지만, 아래 STEP 2 분류 기준을 동일하게 따른다.

---

## 5단계 프로세스

```
1. 관찰 → 2. 분류(로컬/FW 2원화) → 3. 기록(improve-tool) → 4. 보고 → 5. 승인
```

### STEP 1. 관찰

개선 대상을 발견한다. 입력 경로는 두 가지다.

| 입력 경로 | 신호 예시 |
|----------|----------|
| 온디맨드(대화) | 소유자의 직접 피드백, 대화 중 질문에 대한 답, L2 반복 이슈 |
| 회고 참조(태스크·세션 궤적) | 워커 재시도·폴백, 소유자 재지시, PM Gate 반복 이슈, PLAN 재진입, STATE.md 검증/재설계 루프 로그 |

개선 후보가 발견되지 않으면 STEP 2 이하를 건너뛰고 "개선후보 0건"으로 STEP 4를 수행한다(no-op 안전 — 아래 참조).

### STEP 2. 분류 — 로컬 PM 개선 vs FW 개선 (2원화 판단: 결정론 게이트 → 루브릭)

단일 LLM 직관 판단을 지양한다. 이 프로젝트의 검증 2원화(전단 루브릭 심판 / 후단 결정론 검증 — oppl의 `opal-evaluator-agent` + `opal-test-agent`) 사상을 분류 판단에 적용하여, **1차 결정론 게이트**로 대부분을 즉시 확정하고 **경계 사례만** 2차 루브릭으로 넘긴다.

#### 2-1. 1차 — 결정론 게이트 (deterministic)

개선이 반영될 **대상**으로 즉시 판별한다. 한쪽이 명확하면 확정하고 2차 루브릭은 건너뛴다.

| 대상 시그널 | scope |
|------------|-------|
| 프레임워크 소스(`opal/`·`skills/`·`agents/`·`scripts/`·`~/.opal` 배포물)·보고형식·하네스·스킬·도구·부트스트랩 | **fw** |
| 그 프로젝트 고유 도메인 규칙·코드·기획 산출물 (프레임워크 무관) | **local** |

#### 2-2. 2차 — 루브릭 평가 (경계 사례만)

1차로 한쪽이 명확하지 않을 때만 아래 루브릭으로 채점하여 과반 scope로 확정한다.

| 루브릭 항목 | fw 쪽 | local 쪽 |
|-----------|-------|---------|
| 재사용성 — 다른 프로젝트에서도 유효한 개선인가 | 유효 | 이 프로젝트 한정 |
| 프로젝트 독립성 — 특정 도메인/코드에 의존하는가 | 독립 | 의존 |
| 귀속 SSOT — 반영될 SSOT가 프레임워크 문서/코드인가 | 프레임워크 | 프로젝트 |

**결정 테스트 (역할 일반어)**: "이 개선이 프로젝트에 독립적으로 **모든 프로젝트/PM에 유효한가?**" → Yes = **fw** / No = **local**.

> 결정 테스트·본문·재사용 지식에는 특정 정체성 이름이 아니라 역할 일반어 `PM`을 사용한다 — 재사용·공유 지식에 개인 호칭을 배제하는 원칙(`AGENT.md §정체성 적용 > 재사용 지식(brain) 예외`)과 정합한다.

#### 2-3. 동점 시 — 소유자 에스컬레이션

루브릭 3항목이 fw/local 동점(예: 1.5 vs 1.5, 판단 불가)이면 스킬이 임의로 확정하지 않는다. 선택지와 각 항목 채점 근거를 정리하여 소유자에게 질문한다(예: "A(fw)와 B(local) 중 어느 방향이 맞을까요?"). 소유자 답변을 최종 scope로 확정하고 STEP 3으로 진행한다.

#### 2-4. 분류 결과별 저장 위치

- **로컬 PM 개선** → 프로젝트 `.opal/`: `.opal/AGENT.md` 확정기준·PM 검토기준, 전문 에이전트(`opal-{fe,be,db}-agent`) 확정기준, `.opal/memory/`(일회성 판단).
- **FW 개선** → `~/.opal/fw-inbox/`: 에이전트 행동(보고형식·프로세스)·스킬·도구·하네스 SSOT 개선. 프레임워크-우선 원칙 — 에이전트 행동 개선은 개인 memory가 아니라 프레임워크 소스 SSOT 수정 대상이며, `fw-inbox`에 제안으로 적재한 뒤 소유자/PM 검토를 거쳐 install 배포 경로로 반영한다.

> ⚠️ **이 repo(ai-framework) 특수성**: 프로젝트 자체가 프레임워크라 대부분 **fw로 수렴**한다. 일반 프로젝트(회사 서비스 등)에선 결정론 게이트만으로 대부분 갈린다.
> **판단 주체·집행 경계**: 위 2원화 판단은 **LLM(이 스킬 또는 회고 하드스텝)** 이 수행하고, 확정된 scope는 `improve-tool record --scope <local|fw>`가 **결정론적으로 집행(기록)**한다. 도구는 판단하지 않는다.

### STEP 3. 기록 — improve-tool 호출 계약

확정된 scope로 `improve-tool`을 호출한다. 스킬은 scope·제목·본문·상황·출처를 판단해 인자로 넘기고, 실제 write는 도구가 전담한다.

```bash
~/.opal/tools/improve-tool/run.sh record --scope <local|fw> \
  --title "<개선 제목>" \
  --body "<개선 본문 요약>" \
  --situation <retrospective|feedback|conversation> \
  --source-task <NNN | task-path | ""> \
  --project-root <프로젝트 절대경로>
```

| scope | 집행 동작 |
|-------|----------|
| `local` | `<project-root>/.opal/MEMORY.json` 존재 시 memory-tool `append`로 위임(`--type improvement --status candidate`). MEMORY.json 부재 시 `{"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.json"}` no-op 반환 — 예외 전파 없음 |
| `fw` | `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md`를 결정론적으로 write. frontmatter에 출처 메타 4종(`host`·`project`·`situation`·`created`) 전부 포함 |

모든 응답은 JSON `"ok"` 계약을 따른다(성공 `{"ok":true,...}` / 실패 `{"ok":false,"error":"..."}` / no-op `{"ok":true,"skipped":true,...}`). `ok:false` 응답이면 에러 메시지를 확인해 소유자에게 에스컬레이션한다.

### STEP 4. 보고

기록 결과를 소유자에게 간략 보고한다.

- 개선 후보가 있었던 경우: "개선 후보 N건 기록: {scope별 요약}"
- 개선 후보가 없었던 경우: "개선후보 0건" — **이 경우도 정상 종료**다. `op-brain-ingest`의 skipped 패턴과 동일하게 상위 흐름(CLOSE 등)을 차단하지 않는 no-op 안전을 따른다.

### STEP 5. 승인

소유자 이의가 없으면 확정한다. 이의가 있으면 조정한다.

**자기 개선 제한 [MUST]** (`pm-improvement-loop.md` §4 흡수):
- 기존 확정 기준의 수정/삭제는 소유자 승인 필수 — 추가만 자율, 변경/삭제는 제안 후 승인.
- 금지사항 추가는 소유자 승인 필수.
- 프레임워크 에이전트(`~/.opal/agents/`)는 수정하지 않는다 — 프로젝트 에이전트만 갱신 대상.

---

## 참조

- SSOT: `opal/core/references/harness/pm-improvement-loop.md`
- 집행 도구: `opal/tools/improve-tool/` (`run.sh record|list|show`)
- 회고 하드스텝(트랙 A) 참조처: `opal/skills/opal-pilot-{dev,write-tech,gc,project-dev}/SKILL.md` CLOSE 단계

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-17 14:20 | 최초 작성 — 관찰→분류→기록→보고→승인 5단계, 분류 2원화(1차 결정론 게이트표 + 2차 루브릭표 + 동점 소유자 에스컬레이션 + 역할일반어 `PM` 결정 테스트), improve-tool record 호출 계약, `pm-improvement-loop.md` SSOT 참조 (058)
| v1.1 | 2026-07-28 | local scope 표의 구 마커 포맷 참조를 `MEMORY.json`(memory-tool 단독 SSOT)으로 갱신 (078)
