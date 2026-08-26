---
type: concept
title: 로컬/FW 2원화 개선 분류 판단
tags: [pm-loop, classification, decision-making, scope-determination]
sources: [task:058]
related: [opal-improve, improve-tool]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

PM 개선 루프에서 수집된 개선 후보를 **로컬 PM 개선**(프로젝트 `.opal/` 기록)과 **FW 개선**(전역 `~/.opal/fw-inbox/` 수집)으로 2원화 분류하는 판단 기준이다. 단순 LLM 직관을 지양하고 **2단계 결정론** — 1차 결정론 게이트(즉시 판별) + 2차 루브릭 평가(경계 사례)로 설계하여 분류 편향을 제거했다.

## 결정 배경 (WHY)

기존 PM 학습 루프에서는 개선이 "어디에 기록될" 대상인지 명확히 하지 않았다. TASK.md 확정방향 §2 "로컬 PM 개선과 FW 개선의 분리"는 배포경계 준수(프로젝트 소스 수정 → install 배포) 차원과 **지식 공유 경계** 차원에서 나왔다 (근거: PLAN.md §F-003 2.3.2-3.3.2 설계 결정). 

로컬 개선은 "그 프로젝트 고유 도메인·코드·기획 산출물" 관련이므로 프로젝트 `.opal/MEMORY.md`에 기록하고, FW 개선은 "프레임워크 소스·도구·스킬·하네스·보고형식" 관련이므로 전역 `~/.opal/fw-inbox/`로 수집하여 install 배포 대상이 되도록 설계했다. 

분류 판단을 2단계로 설계한 이유는 검증 2원화 사상(evaluator 루브릭 심판 + test 결정론 검증)을 **분류 판단**에도 적용하기 위함이다 (근거: PLAN.md §F-003 H-2, DONE.md 설계 하이라이트 2). 1차 결정론 게이트만으로는 경계 사례를 놓치므로, 2차 루브릭 평가를 도입하여 재사용성·프로젝트독립성·귀속SSOT 3항목으로 채점하고, 동점이면 소유자에게 에스컬레이션한다 (근거: PLAN.md §F-003 3.3.2 분류 2차).

## 영향 범위

- **저장 위치 분기**: 로컬 → `.opal/MEMORY.md` append (memory-tool 위임) / FW → `~/.opal/fw-inbox/{메타}.md` write
- **분류 주체**: opal-improve 스킬과 CLOSE 회고 인라인 스텝이 LLM으로 2단계 판단 수행 (`file_path:opal/skills/opal-improve/SKILL.md`)
- **기록 집행**: improve-tool이 판단된 scope를 **결정론적으로 집행** — `--scope <local|fw>` 파라미터로 분기 (`file_path:opal/tools/improve-tool/improve_tool.py`)

## 분류 기준 상세

### 1차 결정론 게이트 (대상 시그널로 즉시 판별)

| 대상 시그널 | scope | 예시 |
|-----------|-------|------|
| 프레임워크 소스(`opal/`·`skills/`·`agents/`·`scripts/`·`~/.opal` 배포물) | **fw** | state-tool 버그 수정, CLOSE 프로세스 개선, 스킬 명명 정책 |
| 하네스·스킬·도구·부트스트랩 | **fw** | memory-tool enum 확장, install 배포 점검 |
| 보고형식·프로세스(AGENT.md, CONVENTIONS.md) | **fw** | agent 역할 정의 수정, 문서 작성 컨벤션 변경 |
| 프로젝트 고유 도메인 규칙·코드·기획 산출물 | **local** | 이 프로젝트의 데이터 모델, 비즈니스 정책, 서비스 기획 이슈 |

**결정 테스트 (역할 일반어)**: "이 개선이 프로젝트에 독립적으로 **모든 프로젝트/PM에 유효한가?**" → Yes = **fw** / No = **local**.

> 주의: 이 repo(ai-framework) 특수성 — 프로젝트 자체가 프레임워크이므로 대부분 **fw로 수렴**한다. 일반 프로젝트(회사 서비스)에선 1차 게이트만으로 대부분 갈린다 (근거: PLAN.md §F-003 3.3.2 지적).

### 2차 루브릭 평가 (경계 사례만 — 1차가 명확하지 않을 때)

| 루브릭 항목 | fw 쪽 | local 쪽 | 채점 |
|-----------|--------|---------|------|
| **재사용성** | 다른 프로젝트에서도 유효한 개선 | 이 프로젝트 한정 | fw +1, local +1 |
| **프로젝트 독립성** | 특정 도메인/코드 무관 | 특정 도메인/코드 의존 | fw +1, local +1 |
| **귀속 SSOT** | 반영될 SSOT가 프레임워크 문서/코드 | 반영될 SSOT가 프로젝트 문서/코드 | fw +1, local +1 |

**확정 규칙**: 과반(≥2점) 쪽으로 확정. **동점(1:1)이면 소유자에게 질의(에스컬레이션)** — 자동 결정 금지 (근거: PLAN.md §F-003 3.3.2).

## 관련 페이지

- [[opal-improve]] — 분류 판단 실행 스킬
- [[improve-tool]] — 분류 결과 기록 집행
- [[close-retrospective-hardstep]] — CLOSE 회고에서 분류 판단
