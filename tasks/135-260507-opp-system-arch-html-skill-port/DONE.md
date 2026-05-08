# DONE: system-architecture-html 스킬 OPAL 통합 + 트윈 빌드 비교

> 시작: 2026-05-07 11:11 (KST)
> 종료: 2026-05-08 13:11 (KST)
> 적용 스킬: opp (interactive)
> 작업 유형: 신규+개선 (스킬 통합 + 산출물 생성)

---

## 1. 작업 결과 요약

캡틴이 추가한 외부 출처 스킬 `system-architecture-html`을 OPAL **standalone 그룹**(일반 도구 스킬)으로 통합 등록하고, ai-framework 프로젝트 시스템 아키텍처를 두 버전(원본 vs OPAL 호환 수정)으로 산출하여 캡틴이 직접 비교 검토할 수 있는 환경을 마련했다.

`//html-sa` 호출이 가능하도록 `opal-skills-registry.json` `groups.standalone`에 등록되었으며, SKILL.md는 OPAL 호환으로 수정되어 Claude Code 로컬 + 다른 플랫폼에서 동일하게 동작 가능한 상태가 되었다.

## 2. 핵심 결정·변경 사항

### 2.1 결정 변경 (2026-05-08 캡틴 지시)

초기 PLAN은 `community-skills/anthropics/`로 이전을 가정했으나, 캡틴 지시에 따라 **standalone 일반 도구 스킬**로 정착하는 방향으로 변경. 사유:

- OPAL 호환 수정(M-2)으로 SKILL.md가 OPAL 표준 형식과 동급이 됨 → "외부 출처" 라벨이 형식적
- 다른 standalone 스킬(html-mockup, ui-designer, erd-modeler, wireframe-builder, web-to-markdown, api-analyzer, interview)과 동일 카테고리·관리 패턴 적용이 발견성·일관성 측면에서 유리
- 출처 정보는 SKILL.md frontmatter `license: Proprietary`로 보존

### 2.2 R-1~R-7 충족 결과

| # | 요구사항 | 결과 |
|---|---------|------|
| R-1 | 스킬 위치 정착 | ✅ `community-skills/anthropics/` → `skills/system-architecture-html/` 이동 (5파일 SHA256 일치) |
| R-2 | 레지스트리 등록 | ✅ `opal-skills-registry.json` `groups.standalone` 7→8 (alias `html-sa`, 트리거 4종, paths 1개) |
| R-3 | 등록 검증 | ✅ (α) 소스 파싱 `alpha-pass` / (β) `~/.opal/` validate `valid:true, errors:[]` |
| R-4 | 1차 산출물 (원본) | ✅ `outputs/A_original.html` (24,421B) — 환경 감지 흔적 0 (비교 기준선) |
| R-5 | OPAL 호환 5종 수정 | ✅ a(`/mnt/user-data` 제거) / b(`present_files` 제거) / c(§0 호출 환경) / d(Step 1·2 환경 감지·컨텍스트 흡수) / e(한국어 트리거) |
| R-6 | 2차 산출물 (수정) | ✅ `outputs/B_opal_revised.html` (25,996B) — 환경 감지 흔적 4가지 visible |
| R-7 | 메모리 규칙 (`~/.opal/` 무수정) | ✅ `find ~/.opal -newer state.json` → 0건 |

## 3. 산출물

### 3.1 캡틴 비교 검토 대상 (HTML)

- `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html`
- `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html`

### 3.2 통합된 스킬 (재사용 가능 자산)

- `skills/system-architecture-html/SKILL.md` (OPAL 호환 수정 후)
- `skills/system-architecture-html/references/template.html`
- `skills/system-architecture-html/references/design-system.md`
- `skills/system-architecture-html/references/copywriting.md`
- `skills/system-architecture-html/references/examples.md`

### 3.3 레지스트리

- `opal/core/references/opal-skills-registry.json` (`groups.standalone[7]` 신규 항목)

### 3.4 태스크 산출물

- `TASK.md` (R-1~R-7 모두 [x] + Override 표기)
- `PLAN.md` (646줄 + 🚨 결정 변경 박스)
- `QA-PLAN.md` (verdict: pass)
- `EXECUTE.md` (7-Step 실행 결과)
- `QA-EXECUTE.md` (verdict: pass)
- `STATE.md` / `state.json` (파이프라인 행 1~20 모두 ✅)
- `DONE.md` (이 문서)

## 4. 미완료·후속 항목

### 4.1 본 태스크 범위 외 (별도 처리 필요)

- **`~/.opal/`로의 배포**: ai-framework 소스만 갱신했으므로 `//html-sa` 호출이 실제 매칭되려면 `scripts/install-mac.sh` 실행 또는 동등 동기화 필요. 메모리 규칙 `feedback_deploy_boundary.md`에 따라 본 태스크에서는 수행하지 않음. 캡틴이 적절한 시점에 배포 진행.
- **Git 커밋**: 하네스 §1 Guards에 따라 본 태스크는 자동 커밋 수행하지 않음. 캡틴이 명시 요청 시 커밋.

### 4.2 향후 검토 가능 항목

- standalone 그룹 cross-reference 표기: 각 스킬 SKILL.md 상단에 "관련 스킬: html-mockup(화면) / wireframe-builder(와이어프레임) / system-architecture-html(시스템 아키텍처)" 같은 안내 추가 → 발견성 ↑

## 5. 변경 파일 목록

| 종류 | 경로 | 비고 |
|------|------|------|
| 이동 (5건) | `community-skills/anthropics/system-architecture-html/{SKILL.md, references/*}` → `skills/system-architecture-html/{...}` | 내용 무변경 (SHA256 일치). Step 1 Override |
| 수정 | `skills/system-architecture-html/SKILL.md` | OPAL 호환 5종 a~e |
| 수정 | `opal/core/references/opal-skills-registry.json` | `groups.standalone[7]` 신규 |
| 신규 | `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` | 24,421B |
| 신규 | `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` | 25,996B |
| 신규 | `tasks/135-260507-opp-system-arch-html-skill-port/{TASK,PLAN,QA-PLAN,EXECUTE,QA-EXECUTE,DONE,STATE}.md, state.json` | 태스크 산출물 |

## 6. 메모리 갱신

- `.opal/MEMORY.md` 작업 히스토리에 본 태스크(135) 완료 행 추가 (FIFO 정리)
- `last_task_number: 135` 유지 (이미 TASK 단계에서 갱신됨)
- 본 태스크 학습 사항으로 보관할 만한 패턴 (선택적):
  - **외부 출처 스킬을 OPAL standalone으로 흡수하는 표준 절차**: 위치 결정 → SKILL.md OPAL 호환 수정 → standalone 레지스트리 등록 → 트윈 빌드로 차이 검증 (재사용 가능)
  - **Override 박스 패턴**: 태스크 진행 중 결정 변경 발생 시 PLAN.md 본문 무수정 + 상단 Override 박스 추가 → 결정 추적성 보존하면서 진행 (향후 유사 상황에 적용 가능)

## 7. 인용

- 작업 명세 SSOT: `tasks/135-260507-opp-system-arch-html-skill-port/TASK.md`, `PLAN.md` (`🚨 결정 변경` 박스 우선)
- 검증 결과: `QA-PLAN.md`, `QA-EXECUTE.md`
- OPAL Pilot 표준: `~/.opal/references/opal-pm.md`, `opal-harness.md`, `opal-harness-interactive.md`
- 인용 규칙: `~/.opal/references/harness/citation-rules.md`
- 메모리 규칙 근거: `.opal/memory/feedback_deploy_boundary.md`
