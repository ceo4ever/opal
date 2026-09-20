<!--
  module: GC-CONVENTION-260830
  layer: task-artifact
  domain: opal-pilot-gc
  description: 태스크 104(역공학-개념모델링-스킵) 컨벤션 체크 보고서 — 5개 대상 파일 diff hunk 중심
-->

# GC CONVENTION REPORT — 260830

## 1. 헤더

- 실행 일시: 2026-08-30 17:26 (KST) / 갱신 2026-08-30 17:40 (KST) — `opal/skills/op-data-model/SKILL.md` 5번째 대상 추가 보완 검사
- 범위: task 104 changed_files 5개 (docs/proposals/opal-data-design.md, opal-pilot-data-design/SKILL.md, references/pipeline.json, .opal/brain/pages/flow/opdd-pipeline-flow.md, opal/skills/op-data-model/SKILL.md)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재 — 유일 기준)
- APPLY 수행 여부: N (읽기 전용 실행, 보고서만 생성)

> 갱신 이력: 최초 실행 시 `target_files`가 4건으로 전달되어 `opal/skills/op-data-model/SKILL.md`가 누락됐었다(당시 §7 「기존 이슈」에 관찰만 기록). 오케스트레이터 정정 지시에 따라 해당 파일을 5번째 대상으로 추가해 보완 검사하고 본 보고서를 같은 경로에 갱신했다.

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 1 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 (PM 판단 필요 — 규칙 적용 범위 자체가 모호) |
| 파일별 상위 | docs/proposals/opal-data-design.md (1건) |
| 카테고리별 빈도 | 문서화 (1 파일) — 빈도 트리거(N=3) 미달 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |

**결론**: diff hunk 5건 모두 §언어 규칙(한국어 본문+영어 병기)·§네이밍·§YAML Frontmatter·§변경이력 표 형식·§배포 경계·§플랫폼 분기 격리에서 **위반 없음**. 유일한 지적 사항은 심각도가 낮고 규칙 적용 대상 자체가 불명확한 절차적 관찰 1건(`docs/proposals/opal-data-design.md`).

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (1건)

- [ ] GC-C001 [docs/proposals/opal-data-design.md] 이번 diff로 §3.2/§3.2.1/§3.4가 실질 변경됐으나 문서 전체에 `## 변경이력` 섹션 자체가 없어 이번 변경도 이력에 남지 않음
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §변경이력 작성 의무) — 원문: "스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
  - 설명: 본 파일(`docs/proposals/opal-data-design.md`)은 diff 이전부터 `## 변경이력` 섹션이 없는 상태이며(구조 자체가 이번 태스크로 신설/제거된 것이 아님), CONVENTIONS.md의 "참조 문서" 범주에 `docs/proposals/*` 제안서가 포함되는지는 문서상 명시되어 있지 않다. 다만 이 파일은 SKILL.md 등에서 `§3.2`/`§3.4`처럼 절 번호로 지속 인용되는 사실상의 SSOT 문서이므로, 변경 추적 필요성은 실질적으로 존재한다.
  - 해결 방안: (a) 이 문서를 §변경이력 작성 의무 적용 대상으로 볼지 PM이 확정 — 대상이면 `## 변경이력` 표를 신설하고 이번 변경분(104)을 첫 행 또는 이력 행으로 기재. (b) 제안서(proposal) 유형은 애초에 변경이력 대상이 아니라고 확정한다면 본 지적은 기각(N/A) 처리.
  - 자동 수정: N (섹션 신설 여부는 PM 판단 필요)
  - 참조: `docs/CONVENTIONS.md` §변경이력 작성 의무 (본문 인용 위 참조)

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 (이슈 총 1건 — 빈도 임계값 N=3 미달, Critical/High 0건).

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 6. 검사 상세 노트 (diff hunk 대조)

| # | 파일 | 검사 항목 | 결과 |
|---|------|----------|------|
| 1 | opal-data-design.md | §언어 규칙(본문 한국어+영어 병기) | 준수 — "신규 트랙"/"역공학 트랙" 등 한국어 본문 유지 |
| 1 | opal-data-design.md | §3.4 QA 항목 트랙 분기 문구 | pipeline.json·SKILL.md와 표현 정합 |
| 2 | SKILL.md | §변경이력 표 형식 (v1.6 행) | 준수 — 이 파일 고유 관습(버전 `vN.N`, 날짜만 · 접두사 `v`)을 그대로 따름. 날짜 `2026-08-30 17:18`, 태스크 번호 `(104)` 괄호 포함 정상 |
| 2 | SKILL.md | §Citation Rules ([MUST] 항목 인용) | 준수 — 신규 `[MUST]` 문장에 `docs/proposals/opal-data-design.md §3.2.1` 절 번호 인용 포함 |
| 2 | SKILL.md | §State 관리 (PM Gate SSOT는 pipeline.json, SKILL.md 표 중복 게재 금지) | 준수 — STEP 3 PM Gate는 요약 괄호 1줄만 유지(기존 패턴과 동일), 전체 checklist 배열은 여전히 pipeline.json에만 존재 |
| 2 | SKILL.md | §구현 규칙 §플랫폼 분기 격리 | 준수 — 신설된 트랙 분기는 Claude/Cursor/Gemini 등 플랫폼 조건문이 아니라 모델링 트랙(greenfield/reverse) 조건문 |
| 2 | SKILL.md | §배포 경계 | 준수 — 프로젝트 소스(`opal/skills/...`)만 수정, `~/.opal/` 미접촉 |
| 3 | pipeline.json | JSON 유효성 + `model.pm_gate.gate.checklist` 교체 | 유효 JSON. §네이밍/구조 규칙 해당 없음(데이터 파일) |
| 4 | opdd-pipeline-flow.md | §YAML Frontmatter 키 English | 준수 — `type/title/tags/sources/related/created/updated/status` 전부 영문 키 |
| 4 | opdd-pipeline-flow.md | 브레인 페이지 `updated`/`sources` 갱신 | frontmatter 갱신만, 파일 위치는 프로젝트 로컬 `.opal/`(배포 대상 `~/.opal/`과 무관) — §배포 경계 해당 없음 |
| 5 | op-data-model/SKILL.md | §언어 규칙(본문 한국어+영어 병기) | 준수 — "역공학 트랙", "physical(역추출·정규화) → logical(역산)" 등 한국어 본문 + 기술 용어 영어 병기 유지 |
| 5 | op-data-model/SKILL.md | §모드 선택 규칙 표 신규 행 + 참조 노트 | 준수 — 신규 행 "기존 DB/DDL 스키마 주입 (역공학)" 및 하단 참조 노트가 `opal-pilot-data-design` SKILL.md·proposal 문서와 트랙 용어("역공학"/"신규 트랙") 일관 |
| 5 | op-data-model/SKILL.md | §변경이력 표 형식 (`1.1` 행) | 준수 — 이 파일 고유 관습(`| 버전 \| 일시(KST) \| 변경 내용 \|`, 버전에 `v` 접두사 없음, 예: `1.0`)을 그대로 따름. `1.1`, 날짜 `2026-08-30 17:18`(`YYYY-MM-DD HH:mm`), 변경내용 말미 `(104)` 태스크 번호 괄호 포함 — CONVENTIONS.md §변경이력 작성 의무의 일시·태스크 번호 요건 및 이 파일 자체의 기존 버전 표기 관습 모두 충족 |
| 5 | op-data-model/SKILL.md | 참조 노트 사실 정합성(`op-data-ddl §Step 4`) | `opal/skills/op-data-ddl/SKILL.md`에 실제로 "### Step 4. 역공학 (선택 — DDL → DBML)" + `sql2dbml` 존재 확인 — 깨진 인용 아님(컨벤션 항목은 아니나 참고로 확인) |
| 5 | op-data-model/SKILL.md | §State 관리 / §파일 구조 / §YAML Frontmatter | 해당 diff hunk가 건드리지 않음(frontmatter 미변경, PM Gate 정의 없음) — 검토 대상 없음 |
| 5 | op-data-model/SKILL.md | §배포 경계 / §플랫폼 분기 격리 | 준수 — 프로젝트 소스만 수정, 플랫폼 조건문 없음(트랙 조건문만 추가) |

## 7. 기존 이슈 (이번 diff가 건드리지 않은 기존 문구 — 수정 대상 아님, 참고용)

- `docs/proposals/opal-data-design.md`: 문서 전체에 `## 변경이력` 섹션이 애초에 없음(§3 요약 참조) — 이번 태스크가 신설/제거한 구조가 아니라 diff 이전부터의 상태.
- `opal/skills/op-data-model/SKILL.md` ↔ `opal/skills/opal-pilot-data-design/SKILL.md`: 두 파일의 §변경이력 표 컬럼·버전 표기 관습이 서로 다르다(전자는 `| 버전 | 일시(KST) | 변경 내용 |` + 버전 접두사 없음 `1.1`, 후자는 `| 버전 | 날짜 | 변경 내용 |` + `v` 접두사 `v1.6`). 이는 diff 이전부터 있던 각 파일 고유의 기존 관습이며, 이번 태스크는 각 파일이 **자기 자신의 기존 관습**을 그대로 따랐으므로 위반이 아니다(교차비교 목적의 참고 기재).
