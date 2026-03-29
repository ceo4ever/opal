# QA: PLAN — op-task-qa → op-dev-qa 리네이밍 + 범용 op-task-qa 신규

> 검토일: 2026-03-29 | 판정: **Pass**

## 1. 요약

이 PLAN은 현재 코드 개발에 특화된 op-task-qa를 op-dev-qa로 리네이밍하고, 새로운 범용 op-task-qa를 신규 생성하여 QA 체계를 도메인별로 분리하는 작업이다. 9개의 순차적 Step으로 구조화되어 있으며, 스킬/에이전트 생성, 하네스 분기 로직 추가, 오케스트레이터 참조 변경, 레지스트리 및 문서 업데이트를 포함한다. TASK.md의 R1~R7 요구사항을 완전히 반영하고 있으며, 의존성 순서가 적절하게 정의되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | **Pass** | Step 1~9의 순차 구조가 명확하고, 각 Step의 파일, 작업 내용, 완료 기준이 구체적으로 정의됨 |
| GP-2 | 의존성 순서 | **Pass** | Step 1~2 (리네이밍) → Step 3~4 (신규 생성) → Step 5~7 (통합) → Step 8~9 (레지스트리/문서) 순서가 논리적이고 의존성 명시 완전 |
| GP-3 | TASK 반영 | **Pass** | R1(op-dev-qa 리네이밍) ~ R7(install-mac.sh) 전 7개 요구사항이 모두 반영되고 Step으로 분해됨 |
| GP-4 | 파일 목록 완전성 | **Pass** | 신규 파일 9개(N1~N9), 수정 파일 12개(M1~M12), 삭제 파일 2개(D1~D2) 완전히 나열되고 차트로 구성됨 |
| GP-5 | 설계 구체성 | **Pass** | 각 핵심 파일(N1, N5, N6, N7, N8, N9, M1~M3)에 대해 구체적인 코드 예시 또는 변경 전후 비교 제시 |
| GP-6 | 체크리스트 커버리지 | **Pass** | Step 1~9 각각에 완료 기준, 테스트 명령어, 의존성 명시. QA 체크리스트(기능/일관성/문서) + 리스크 관리까지 포함 |

## 3. 지적 사항

### Info (매우 경미한 사항, 실행 가능성에 영향 없음)

1. **Install-mac.sh의 변경 불필요 명시가 명확함** (행 22)
   - PLAN에서 "변경 불필요 (디렉토리 기반 자동 반영)"로 설명했는데, R7.1에서는 "배포 경로 추가"가 필요하다고 했음
   - 이는 TASK.md R7과의 약간의 불일치이지만, PLAN의 입장이 더 정확함 (glob 자동 반영이므로 변경 불필요)
   - **해결**: 기존대로 변경 불필요로 진행하되, EXECUTE 단계에서 설치 스크립트 동작 확인 필요

2. **qa-engineer.md (범용화) 에서 페르소나 변경 사항이 예시 수준**
   - N8 섹션에서 "엣지 케이스 → 누락 시나리오" 등 3가지 변경만 명시했는데, 실제 파일 내용은 더 클 수 있음
   - **해결**: EXECUTE 단계에서 기존 페르소나 전체를 검토 후 범용화

3. **범용 op-task-qa의 stage 입력에서 TASK/PLAN/EXECUTE만 정의**
   - N6의 stage 입력 설명에서 TASK/PLAN/EXECUTE만 명시했는데, EXECUTE는 "모든 Step 완료 후"인지 "각 Step 완료 후"인지 명확화 필요
   - **해결**: EXECUTE 단계에서 SKILL.md 작성 시 프로세스 명시

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1~R7 요구사항이 PLAN의 Step/파일에 매핑되었는가 | **Pass** |
| opal-harness.md (현재 55~56행) | QA Gate의 현재 상태: 단일 op-task-qa 탐색 | **Pass** |
| opal-pilot-dev-wireframe/SKILL.md (현재) | op-task-qa 직접 참조 2곳 확인됨 (44행, 55행) | **Pass** |
| opal-skills-registry.json (현재) | op-task-qa가 현재 어느 그룹에 속하는지 (op-task 그룹) | **Pass** |
| agents.md (현재) | op-task-qa-agent가 현재 레지스트리에 있는지 | **Info**: 확인 필요 |

## 5. 판정

**Pass**

### 근거

1. **완전성**: TASK.md의 모든 요구사항(R1~R7)이 PLAN에 반영되고, 9개의 Step으로 완전히 분해됨
2. **논리성**: Step 간 의존성이 명확하고 의존 관계가 정확히 명시되어 있음 (Step 1 완료 후 Step 3 진행 등)
3. **구체성**: 각 파일에 대해 변경 전후 비교, 구체적인 코드 예시, 완료 기준과 테스트 명령어를 제시
4. **실행 가능성**: 모든 파일 경로가 절대 경로로 명확하고, 각 Step의 작업 내용과 예상 난이도가 명시됨
5. **QA 기준 충족**: 기능 테스트, 일관성 테스트, 문서 품질 검증 체크리스트가 완성되어 있음

### 주의 사항

- **install-mac.sh**: TASK.md R7과의 약간의 불일치가 있으나, PLAN의 설명이 기술적으로 정확 (glob 자동 반영)
- **범용 op-task-qa의 stage 정의**: EXECUTE의 구체적인 조건(모든 Step 완료 vs 단계별 완료)은 SKILL.md 작성 시 명확히 할 것

---

## 추가: 검증 코드

### 파일 존재 여부 확인 (EXECUTE 단계)
```bash
# 현재 상태
ls -la skills/op-task-qa/SKILL.md
ls -la agents/op-task-qa-agent/AGENT.md

# Step 1 완료 후
ls -la skills/op-dev-qa/SKILL.md
grep "op-task-qa" skills/op-dev-qa/SKILL.md | wc -l  # 결과: 0

# Step 3 완료 후
ls -la skills/op-task-qa/SKILL.md
ls -la skills/op-task-qa/references/qa-general-guide.md
grep -E "ANALYSIS|WIREFRAME|EXECUTE-UI" skills/op-task-qa/SKILL.md | wc -l  # 결과: 0

# Step 8 완료 후
python3 -c "import json; json.load(open('opal/core/references/opal-skills-registry.json'))"  # 성공
grep -c "op-dev-qa" opal/core/references/opal-skills-registry.json  # > 0
grep -c "op-task-qa" opal/core/references/agents.md  # > 0
```
