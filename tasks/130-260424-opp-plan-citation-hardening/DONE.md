# DONE: Citation Rules 하네스 보편화 — 근거 제시 원칙 강화

> 완료일시: 2026-04-24 11:42 | 태스크: 130 | 적용 스킬: opp | 모드: agentic

---

## 1. 태스크 요약

citation-rules.md를 **"상상·추정 금지, 근거 제시 의무"의 하네스 SSOT**로 승격하고, OPAL의 모든 pilot · PLAN/TASK/ANALYSIS 스킬 · QA 스킬이 이를 필수 적용하도록 **SSOT + Trigger 패턴**으로 구조를 정비. 근거 유형은 트랙별(비개발 = 문서+웹 / 개발 = 기획+설계+소스)로 구분.

---

## 2. 수행 내용 (R-1 ~ R-8)

### R-1 ~ R-5 — citation-rules.md SSOT 본체 완성 (v2.0)

- **§0 근거 제시 원칙** `[MUST]` 신설 — "상상·추정·기억 기반 기재 금지" 최상위 선언
- **§1.5 개발/비개발 트랙별 근거 매트릭스** 신설 (2행 × 5열)
- **§2.5 개발 트랙 [MUST] 토큰 대상** 신설 — 6종(필드명/함수 시그니처/타입명/ERD 컬럼명/IA 화면 ID·라우트/정책 조항 번호) + Good/Bad 예시
- **§7 영역 간 용어 일관성 검토 + decision_required 계약** 신설 — §7.1 검출 대상 영역 쌍 / §7.3 산출물 §리스크 기재 포맷 / §7.4 JSON 스키마(type·summary·tokens·areas·source_refs·suggested_resolution) / §7.5 `[MUST]` 에스컬레이션 원칙
- **기존 §1~§6 구조 보존** (하위호환)

### R-6 — opal-harness.md §2 Citation Rules 적용 의무 블록 (v4.5)

- "모든 pilot / PLAN·TASK·ANALYSIS 스킬 / QA 스킬은 citation-rules.md를 필수 Read하고 준수" 선언
- interactive · agentic **양쪽 모두 적용** 명시
- 기존 Lazy 로드 모듈 테이블 `citation-rules` 행과 역할 분리(정책 vs 로드 시점) 공존

### R-7 — 18개 관련 문서에 Trigger 1줄 주입

공통 템플릿:
```
> **[MUST]** 산출물 작성·검증 시 `opal/core/references/harness/citation-rules.md`를 Read하여 규칙(근거 제시 원칙 / 트랙별 매트릭스 / [MUST] 토큰 / 영역 간 용어 일관성 / decision_required 계약)을 준수한다.
```

pilot 8개 + PLAN 5개 + PLAN 가이드 1개 + TASK/ANALYSIS 2개 + QA 2개 + QA 가이드 1개 = 18개 파일 전수 주입. **규칙 내용 복제 없음** (SSOT 원칙 준수).

### R-8 — 전 수정 파일 변경이력 일괄 갱신

20개 파일 모두 2026-04-24 / 태스크 130 참조 행 추가.

---

## 3. 변경 파일 (20개)

| # | 카테고리 | 파일 | 주요 변경 |
|---|---------|------|---------|
| 1 | SSOT 본체 | `opal/core/references/harness/citation-rules.md` | §0/§1.5/§2.5/§7 신설 + v2.0 |
| 2 | 공통 하네스 | `opal/core/references/opal-harness.md` | §2 Citation Rules 적용 의무 블록 + v4.5 |
| 3 | pilot | `opal/skills/opal-pilot-project/SKILL.md` | Trigger + 변경이력 |
| 4 | pilot | `opal/skills/opal-pilot-project-dev/SKILL.md` | Trigger + 변경이력 |
| 5 | pilot | `opal/skills/opal-pilot-dev/SKILL.md` | Trigger + 변경이력 |
| 6 | pilot | `opal/skills/opal-pilot-dev-short/SKILL.md` | Trigger + 변경이력 |
| 7 | pilot | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | Trigger + 변경이력 |
| 8 | pilot | `opal/skills/opal-pilot-sdd/SKILL.md` | Trigger + 변경이력 |
| 9 | pilot | `opal/skills/opal-pilot-write-tech/SKILL.md` | Trigger + 변경이력 |
| 10 | pilot | `opal/skills/opal-pilot-gc/SKILL.md` | Trigger + 변경이력 |
| 11 | PLAN 스킬 | `opal/skills/op-dev-plan/SKILL.md` | Trigger + 변경이력 |
| 12 | PLAN 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | Trigger + 변경이력 |
| 13 | PLAN 스킬 | `opal/skills/op-task-plan/SKILL.md` | Trigger + 변경이력 |
| 14 | PLAN 스킬 | `opal/skills/op-sdd-plan/SKILL.md` | Trigger + 변경이력 |
| 15 | PLAN 스킬 | `opal/skills/op-sdd-action-plan/SKILL.md` | Trigger + 변경이력 |
| 16 | TASK 스킬 | `opal/skills/op-task/SKILL.md` | Trigger + 변경이력 |
| 17 | ANALYSIS 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | Trigger + 변경이력 |
| 18 | QA 스킬 | `opal/skills/op-dev-qa/SKILL.md` | Trigger + 변경이력 |
| 19 | QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | Trigger + 변경이력 |
| 20 | QA 스킬 | `opal/skills/op-task-qa/SKILL.md` | Trigger + 변경이력 |

---

## 4. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 10 섹션 마스터 문서 (C-1~C-7 로드맵, 대화 의사결정 타임라인, R-1~R-8) |
| `PLAN.md` | 20 Step / 4 Phase 실행 체크리스트, 파일별 주입 위치 매트릭스, 리스크 6건 |
| `QA-PLAN.md` | PLAN 검증 Pass (Warning 1건 보정 완료) |
| `QA-EXECUTE.md` | EXECUTE 검증 **Pass** (Critical/Warning/Info 0건) |
| `STATE.md` | 20행 파이프라인 현황판 + 의사결정 로그 11건 |
| `AGENTIC-LOG.md` | DECISION 13건 + GATE 5건 + IMPROVE 1건 + ERROR/FIX 각 1건 |
| `DONE.md` | 본 문서 |

---

## 5. 성공 기준 달성 (TASK.md §10)

- [x] citation-rules.md에 근거 제시 원칙이 `[MUST]` 포맷으로 서두에 선언 (R-1)
- [x] 개발/비개발 트랙별 근거 매트릭스 존재 (R-2)
- [x] 개발 트랙 `[MUST]` 토큰 6종 Good/Bad 예시 포함 (R-3)
- [x] 영역 간 용어 일관성 검토 규칙 + `decision_required` 계약 스키마 + 에스컬레이션 원칙 모두 기재 (R-4)
- [x] citation-rules.md 변경이력 갱신 (R-5)
- [x] opal-harness.md §2에 Citation Rules 적용 의무 블록 존재 (R-6)
- [x] R-7 대상 18개 파일에 트리거 1줄 정확히 주입, 누락 0건 (R-7)
- [x] 전 수정 파일(20개) 변경이력에 태스크 130 참조 행 존재 (R-8)
- [x] citation-rules.md 기존 섹션 구조 보존 — 하위호환 유지
- [x] 트리거 블록에 규칙 내용이 복제되어 있지 않음 — SSOT 원칙 준수

---

## 6. agentic 대행 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 5회 (Pass: 5 / Fail: 0) |
| 3회 초과 Gate | 0건 |
| 오류 발견 | 1건 (Minor — PLAN Phase 테이블 Step 범위 표기 오차) |
| 수정 지시 | 1건 (PM 직접 보정, 반영 완료) |
| PM 의사결정 | 13건 |
| 개선 사항 | 1건 (설계 단순화 — 캡틴 SSOT/Trigger 통찰 반영) |
| 에스컬레이션 | 0건 |

전체 진행 이력은 `AGENTIC-LOG.md` 참조.

---

## 7. 특이사항 / 후속 조치

- **후속 태스크 없음** — α안(단일 태스크)으로 C-1~C-7 모두 완료. TASK.md에 기재됐던 β안 2단계 분할은 SSOT/Trigger 패턴 채택 후 폐기됨.
- **배포 시점**: 본 태스크는 개발만 수행. `~/.opal/`로의 배포는 캡틴 명시 지시(`install-mac.sh` 실행) 시에만 수행 (개발/배포 경계 원칙, AGENT.md §금지사항).
- **커밋**: 수행되지 않음. 캡틴 요청 시 별도 수행.
- **127번 태스크**: TASK 단계에서 진행 중 상태 유지 (본 태스크와 독립).

---

## 8. 방향 전환 기록 (참고)

본 태스크는 진행 중 **2차례의 방향 전환**을 겪었다:

1. **1차**: PLAN 인용 의무 강화(국소) → Citation Rules 하네스 보편화 (캡틴 원칙 선언)
2. **2차**: consistency-rules 통합안(B안) → SSOT + Trigger 패턴 (캡틴 구조적 통찰)

두 전환 모두 캡틴의 통찰로 설계가 단순화·명료화되었으며, 결과적으로 단일 태스크로 완결할 수 있는 구조가 되었다. 상세 의사결정 타임라인은 `TASK.md §3` 참조.
