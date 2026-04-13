# DONE: op-dev-plan 탑다운 기능 중심 구조 개편 + 후속 파이프라인 정합화

> 완료일: 2026-04-13 14:11 KST | 태스크: 114 | 스킬: opp (opal-pilot-project) | 모드: interactive

## 1. 완료 요약

`op-dev-plan`의 PLAN 단계를 **탑다운 기능 중심 구조**로 전면 개편했다. `execution-plan.json`을 폐기하고 PLAN.md를 단일 SSOT로 통합했으며, 후속 소비자(`op-dev-execute`, `op-dev-qa`, `ui-designer`)를 새 구조에 맞게 정합화했다. 캡틴 지시로 수정 전 원본 파일 8개를 `backup/`에 보관하여 롤백 안전성을 확보했다.

## 2. 요구사항 충족 (TASK.md R0~R8)

| ID | 요구사항 | 결과 | TS |
|----|---------|------|-----|
| R0 | 수정 전 원본 파일 백업 (PLAN에서 추가) | ✅ | TS-016~TS-018 |
| R1 | op-dev-plan SKILL.md 탑다운 기능 중심 구조 재작성 | ✅ | TS-001~TS-003 |
| R2 | plan-guide.md 기능 중심 단계 재설계 | ✅ | TS-004 |
| R3 | execution-plan.json 폐기 처리 (하위호환 보존) | ✅ | TS-007~TS-009 |
| R4 | PLAN.md 구조 파싱 규칙 명세 | ✅ | TS-005 |
| R5 | Flat/Multi 모드 자동 축소 규칙 추가 | ✅ | TS-006 |
| R6 | op-dev-execute features 루프 전환 | ✅ | TS-010~TS-011 |
| R7 | ui-designer plan-driven 입력 전환 | ✅ | TS-012~TS-013 |
| R8 | op-dev-qa 기능-QA 매핑 검증 규칙 추가 | ✅ | TS-014~TS-015 |

## 3. 산출물

### 태스크 산출물
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/TASK.md`
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/PLAN.md` (v1.1 — F-000 백업 포함)
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/QA-PLAN.md`
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/QA-EXECUTE.md`
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/STATE.md`
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/DONE.md` (본 문서)

### 수정된 소스 파일 (8개)
| 파일 | 버전 | 핵심 변경 |
|------|------|----------|
| `opal/skills/op-dev-plan/SKILL.md` | v2.0 | §1~§9 기능 중심 출력 형식, Step 1~10 재정렬, Flat/Multi-Feature 모드, Deprecated 고지, 기능-QA 매트릭스 |
| `opal/skills/op-dev-plan/references/plan-guide.md` | v2.0 | 0~6단계 전면 재구성, 기능 식별 1단계 신설, PLAN.md 파싱 규칙 섹션 신설, Flat/Multi 판정 테이블 |
| `opal/skills/op-dev-execute/SKILL.md` | v1.2 | 입력 우선순위 PLAN.md §4 1순위, json 폴백, PLAN.md 기반 실행 섹션 |
| `opal/skills/op-dev-execute/references/execute-guide.md` | v1.1 | PLAN.md §4 기반 실행, §3.N.2 FE 화면 참조, 과거 태스크 폴백 규칙 |
| `opal/skills/op-dev-qa/SKILL.md` | v1.1 | P-7 기능-QA 커버리지 검증 ID 추가 (Multi-Feature 모드 전용) |
| `opal/skills/op-dev-qa/references/qa-dev-guide.md` | v1.1 | PLAN Full 검증 기준 P-7 행 추가 |
| `skills/ui-designer/SKILL.md` | v1.1 | plan-driven 입력을 PLAN.md §3.N.2로 변경 |
| `skills/ui-designer/modes/plan-driven.md` | v1.1 | 입력 소스 PLAN.md §3.N.2 서브섹션으로 전환, json 폴백 |

### 백업 (9개)
- `tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/MANIFEST.md`
- `backup/opal/skills/op-dev-plan/SKILL.md` (11108B)
- `backup/opal/skills/op-dev-plan/references/plan-guide.md` (14208B)
- `backup/opal/skills/op-dev-execute/SKILL.md` (9845B)
- `backup/opal/skills/op-dev-execute/references/execute-guide.md` (7777B)
- `backup/opal/skills/op-dev-qa/SKILL.md` (6354B)
- `backup/opal/skills/op-dev-qa/references/qa-dev-guide.md` (5336B)
- `backup/skills/ui-designer/SKILL.md` (12377B)
- `backup/skills/ui-designer/modes/plan-driven.md` (4348B)

## 4. QA 결과 요약

| Gate | 판정 | Pass / Fail / Info |
|------|-----|-------------------|
| PLAN QA Gate | ✅ Pass | 27 / 0 / 2 |
| EXECUTE QA Gate | ✅ Pass | 18 / 0 / 1 |

**전체 TS-001~TS-018 (18개) 통과**. 제약 조건 회귀(H-1~H-10) 전체 통과. 자기정합(J-1~J-4) 전체 통과.

## 5. Gate 기록

| Gate | 결과 | 시점 |
|------|------|------|
| TASK State Gate | ✅ | 12:28 |
| PLAN State Gate | ✅ | 12:51 |
| PLAN QA Gate | ✅ Pass (27/0/2) | 12:56 |
| PLAN PM Gate | ✅ Pass | 12:56 |
| EXECUTE State Gate | ✅ | 14:04 |
| EXECUTE QA Gate | ✅ Pass (18/0/1) | 14:11 |
| EXECUTE PM Gate | ✅ Pass | 14:11 |

## 6. 특이사항

### 6.1 PLAN 시범 적용 + 자기정합
본 태스크의 PLAN.md는 새 탑다운 기능 중심 구조를 **시범 적용**하여 작성되었다. EXECUTE 결과(새 op-dev-plan SKILL.md + plan-guide.md)와 PLAN.md 구조가 **자기정합**이 되도록 설계했으며, QA §5 자기정합 검증에서 J-1~J-4 모두 Pass 확인.

### 6.2 F-000 백업 횡단 추가 (PLAN v1.1)
PLAN 승인 시점에 캡틴이 백업 요구사항을 추가 지시하여 F-000을 횡단 기능으로 신설. Step 번호 shift(기존 1~7 → 2~8), Phase 4→5 재정렬, TS-016~TS-018 추가.

### 6.3 문서-코드 불일치 (1건)
TASK.md에 `opal/skills/ui-designer/` 경로로 기재되어 있었으나 실제 경로는 `skills/ui-designer/` (독립 스킬 소스). PLAN 작성 시 코드 기준으로 정정하여 작업 수행. opi 최신화 메모리로 별도 기록.

### 6.4 Info 사항 (2건, Non-blocking)
- `op-dev-qa/SKILL.md` frontmatter에 version 필드 없음 (원래 없던 것, 다른 파일들은 version 필드 있음). 기능 영향 없음.
- TASK.md R6 AC 표현("PLAN.md §2·§3 입력") vs 실제 구현(§4 실행 체크리스트를 1차 입력, §2·§3는 폴백) — 개념적으로 §4가 §2·§3에서 도출되므로 정합. 용어 미세 차이.

### 6.5 하위호환 처리
- **과거 태스크의 execution-plan.json**: 삭제/수정하지 않음. op-dev-execute·ui-designer가 폴백 경로로 여전히 소비 가능.
- **과거 형식 PLAN.md**(v1 섹션 구조): op-dev-execute가 `PLAN.md §4 → PLAN.md §3(구형) → json` 3단계 폴백으로 처리.
- **@header 규칙**: 수정 대상 .md 파일은 프로젝트 code-scan.json의 extensions에 md가 없어 @header 블록 미적용. SKILL.md의 YAML frontmatter가 메타데이터 역할.

## 7. 롤백 방법 (필요 시)

`backup/` 폴더가 원본 경로 구조를 유지하므로 단일 명령으로 복원 가능:

```bash
cd /Volumes/Data/AiStudio/workspace/opal
cp -R tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/opal ./
cp -R tasks/114-260413-opp-op-dev-plan-feature-driven-redesign/backup/skills ./
```

상세는 `backup/MANIFEST.md` 참조.

## 8. 후속 조치 권고

1. **배포 결정**: 본 태스크는 소스 수정만 수행. 실제 적용은 캡틴이 `install-mac.sh`로 별도 배포 필요 (AGENT.md 개발/배포 경계 원칙).
2. **실전 파일럿**: v2 새 구조의 실제 체감 검증을 위해, 다음 일반 FE/BE 개발 태스크에서 opd/opds로 새 PLAN 구조를 한두 번 적용해보는 것을 권장. 특히 기능 분해 일관성·md 파싱 안정성을 확인.
3. **opsdd 선택 가이드 보강**: plan-guide.md에 "SPEC부터 시작 → opsdd / TASK부터 시작 + 다기능 → op-dev-plan v2 / 단일 수정 → opds"라는 선택 가이드가 추가되면 사용자 혼선 감소 (후속 태스크).
4. **커밋**: 캡틴이 커밋을 지시하면 하나의 태스크 = 하나의 커밋 원칙으로 `feat(114): op-dev-plan 탑다운 기능 중심 구조 개편 + 후속 파이프라인 정합화` 형식 제안.
