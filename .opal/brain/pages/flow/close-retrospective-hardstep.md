---
type: flow
title: CLOSE 회고 하드스텝 (개선 루프 자동 enforce)
tags: [flow, close-pipeline, improvement, tool-gated, architecture-decision]
sources: [task:058]
related: [[pm-improvement-loop-two-tracks], [op-brain-ingest], [opal-pilot-dev], [improve-tool]]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

CLOSE 파이프라인의 op-brain-ingest 직후에 삽입된 회고 하드스텝이다. 태스크/세션 궤적 신호(워커 재시도·폴백·PM 피드백·검증 루프 로그)를 입력받아 개선 후보를 관찰→분류(로컬/FW)→기록하는 자동 enforce 프로세스다. improve-tool record로 기록을 결정론적으로 집행한다.

## 흐름 단계

### 관찰 (입력)

**세션/태스크 궤적 신호**에서 개선 대상 발견:
- STATE.md 검증·재설계·PM 검수 로그
- 워커 재시도(폴백, 회귀 로지)
- 소유자 재지시·피드백
- PM Gate 반복 이슈
- PLAN 재진입 기록

> **주의**: 산출물 재독이 아님. 그건 PM Gate/QA 담당. 회고 입력은 **파이프라인 자체의 궤적**(왜 이 태스크가 지연/재설계되었나)에 집중한다.

### 분류 (2단계 판단)

개선 후보별로 로컬/FW 판단 실행 — [[local-fw-improvement-classification]] 기준:
1. **1차 결정론 게이트**: 대상(프레임워크 소스/도구/하네스 vs 프로젝트 고유 코드)으로 즉시 판별
2. **2차 루브릭**: 경계 사례에서 재사용성·프로젝트독립성·귀속SSOT로 채점 → 동점 시 소유자 질의

### 기록 (도구 집행)

분류된 각 후보별로 improve-tool 호출:

```bash
~/.opal/tools/improve-tool/run.sh record \
  --scope <local|fw> \
  --title "<제안 제목>" \
  --body "<제안 본문>" \
  --situation retrospective \
  --source-task <NNN> \
  --project-root <루트>
```

**로컬**: MEMORY.md 존재 시 memory-tool append 위임 / 부재 시 graceful skip  
**FW**: `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` 자기완결 항목 생성

### 보고 & 승인

- 보고: "개선 후보 N건 기록" 간략 요약 소유자에게 전달, 또는 "개선 후보 0건"
- 승인: 소유자 이의 없으면 확정

## No-op 안전 [MUST]

궤적 신호에서 개선 후보가 **없으면** 기록 없이 "개선 후보 0건" 보고 — op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다** (근거: PLAN.md §F-004 3.4.2 no-op 안전, DONE.md R1).

## 삽입 위치 (4 pilot CLOSE)

| pilot | 파일 | 삽입점 | 상세 |
|-------|------|--------|------|
| opd | `opal/skills/opal-pilot-dev/SKILL.md` | STEP6 `:248` | op-brain-ingest(`:247`) 직후 · 완료보고(`:248`) 직전 |
| opwt | `opal/skills/opal-pilot-write-tech/SKILL.md` | CLOSE `:399` | brain-ingest(`:398`) 직후 · 완료보고 직전 |
| opgc | `opal/skills/opal-pilot-gc/SKILL.md` | STEP4 `:365` | brain-ingest(`:364`) 직후 · 4.3 opds 체인 직전 |
| oppd | `opal/skills/opal-pilot-project-dev/SKILL.md` | DONE.md `:669` | brain-ingest(`:668`) 직후 · 문서등록 직전 |

> CLOSE 공통 순서: ①DONE.md+mark ② 관련문서 업데이트 ③op-brain-ingest ④회고(새추가) ⑤완료보고.

## 설계 및 근거

**인라인 스텝 선택 (dispatched worker 아님)**: op-brain-ingest는 격리 컨텍스트에서 무거운 page 저술을 하므로 워커 디스패치이나, 회고 입력은 **오케스트레이터만 보유**한 세션 궤적 신호(STATE.md·로그)이므로 CLOSE 인라인 스텝으로 설계했다 (근거: PLAN.md §F-004 설계 결정 D-R1, TASK.md 확정방향 §3).

**op-brain-ingest 답습**: CLOSE 하드연결 + 도구 집행 + 증거 산출의 3요소로 op-brain-ingest 성공 패턴을 답습하여 **자동 enforce 신뢰성** 확보 (근거: DONE.md 설계 하이라이트 1).

## 관련 페이지

- [[pm-improvement-loop-two-tracks]] — 2트랙 구조 (회고/온디맨드)
- [[op-brain-ingest]] — 자매 CLOSE 훅 (지식 누적)
- [[improve-tool]] — 기록 집행 도구
- [[opal-improve]] — 온디맨드 스킬 (별도 5단계 프로세스)
