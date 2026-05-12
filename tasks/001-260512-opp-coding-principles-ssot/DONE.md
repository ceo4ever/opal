# DONE: 카르파시 행동 원칙 흡수 — Coding Principles SSOT 신설 + TASK AC 보강

> 완료일: 2026-05-12 | 적용 스킬: opp | 모드: semi-agentic
> 태스크 번호: 001

---

## 1. 완료 산출물

### 영구 SSOT 변경 (Framework 영역)

| # | 파일 | 처리 | 버전 |
|---|------|------|:----:|
| 1 | `opal/core/references/harness/coding-principles.md` | **신규** — 코딩 행동 원칙 SSOT (영문, OPAL 자립 표현) | v1.1 |
| 2 | `opal/core/references/opal-harness.md` | §2 모듈 테이블 + §10 Coding Principles stub 신설 | v4.9 |
| 3 | `opal/core/AGENT.md` | "그냥 해" 표 유지 카테고리에 Coding Principles 행 추가 | v2.5 |
| 4 | `opal/agents/opal-fe-agent/AGENT.md` | Step 5.5 — `op-dev-execute`/`op-dev-wireframe` 진입 시 §4 Read 의무 | v1.1 |
| 5 | `opal/agents/opal-be-agent/AGENT.md` | Step 5.5 — `op-dev-execute` 진입 시 §4 Read 의무 | v1.1 |
| 6 | `opal/agents/opal-task-agent/AGENT.md` | 행동 규칙에 EXECUTE 진입 시 §4 Read 의무 | v1.1 |
| 7 | `opal/skills/op-task/SKILL.md` | AC 가이드에 §4 영문 인용 + Bad/Good 예시 2행 | v1.6 |
| 8 | `opal/skills/op-dev-test-scenario/SKILL.md` | AC↔verify check 매핑 표 의무 + 형식 예시 | v1.3 |

### 태스크 산출물

| 산출물 | 경로 |
|--------|------|
| TASK.md | `tasks/001-260512-opp-coding-principles-ssot/TASK.md` |
| PLAN.md (v1.1) | `tasks/001-260512-opp-coding-principles-ssot/PLAN.md` |
| QA-PLAN.md | `tasks/001-260512-opp-coding-principles-ssot/QA-PLAN.md` |
| AGENTIC-LOG.md | `tasks/001-260512-opp-coding-principles-ssot/AGENTIC-LOG.md` |
| QA-EXECUTE.md | `tasks/001-260512-opp-coding-principles-ssot/QA-EXECUTE.md` |
| DONE.md (이 문서) | `tasks/001-260512-opp-coding-principles-ssot/DONE.md` |
| STATE.md / state.json | `tasks/001-260512-opp-coding-principles-ssot/STATE.md` |

---

## 2. 핵심 의사결정 (M-1~M-4 + 추가작업)

| # | 결정 | 근거 요약 |
|---|------|----------|
| M-1 | F-5 매핑 룰 → `op-dev-test-scenario/SKILL.md` 배치 | PLAN 단계 스킬은 AC 참조만; verify check 매핑은 TEST-SCENARIO 책임 |
| M-2 | `opal-harness.md` §10 신설로 등재 | §9가 마지막(OPAL Tools), §8 @header와 별도 개념 |
| M-3 | 워커 자가 로드 = 조건부 + 도메인별 트리거 차이 | FE: wireframe 포함 / BE: 미포함 / Task: op-task-execute 포함 |
| M-4 | opal-task-agent → "## 행동 규칙" 섹션 추가 | 해당 섹션이 이미 의무 열거 위치 |
| AW-1 | coding-principles.md 영문 재작성 + 외부 출처 표현 제거 | 영구 SSOT는 외부 출처 의존 제거. 캡틴 명시 선택 (옵션 A) |

---

## 3. QA 결과

### PLAN 단계 (QA-PLAN.md)

| 항목 | 결과 |
|------|:----:|
| TASK 추적성 (F-1~F-5 분해) | Pass |
| 형식 정합 (§4 중복) | **Fail → PM 정정 (PLAN v1.1) → Pass** |
| 의사결정 근거 (M-1~M-4) | Pass |
| 일관성 (에이전트 트리거) | Warning → M-3 도메인 의도 명시로 해소 |
| 변경이력·인용·배포 경계 | Pass |
| **PLAN 최종 판정** | **Pass** |

### EXECUTE 단계 (QA-EXECUTE.md)

| 항목 | 결과 |
|------|:----:|
| A. F-1 coding-principles.md (frontmatter, 6섹션, §3 5행, §6 매트릭스, 변경이력) | Pass |
| B. F-2 워커 자가 로드 (3개 에이전트, M-3 도메인 차이) | Pass |
| C. F-3 "그냥 해" 표 | Pass |
| D. F-4 AC 가이드 영문 인용 + Bad/Good 2행 | Pass |
| E. F-5 매핑 룰 + 형식 예시 (3열) | Pass |
| F. 하네스 통합 (§2 + §10) | Pass |
| G. 변경이력 표 7개 + 신규 1개 | Pass |
| H. 일관성·회귀·품질 | Pass |
| **EXECUTE 최종 판정** | **Pass** |

### PM Gate 샘플 검증

| 샘플 | 결과 |
|------|:----:|
| coding-principles.md 전체 Read (6섹션·매트릭스·frontmatter) | Pass |
| opal-harness.md §10 stub 정합 | Pass |
| AGENT.md "그냥 해" 표 라인 147 행 등재 | Pass |
| op-task SKILL.md 영문 인용 라인 102 | Pass |
| PLAN.md §4 8 Step 체크박스 8/8 [x] 갱신 | Pass |

### 추가작업 (AW-1) 자가 검증

| 항목 | 결과 |
|------|:----:|
| "카르파시"·"Karpathy" 표현 잔존 | **0건** |
| §1~§6 6섹션 헤딩 | 6/6 존재 |
| §3 Rarity Matrix 5행 | 5/5 존재 |
| 변경이력 v1.0 + v1.1 | 2/2 존재 |

---

## 4. 잔여 미해결 / Known Issues

| # | 항목 | 비고 |
|---|------|------|
| K-1 | 단일 SSOT 영문 / 다른 OPAL SSOT 한국어 → 언어 일관성 부정합 | 캡틴 옵션 A 명시 선택으로 수용 |
| K-2 | `op-task/SKILL.md` AC 가이드에 "Karpathy CLAUDE.md §4" 인용 잔존 | 캡틴 발화 범위 외 (옵션 A는 coding-principles.md만 처리) — 향후 일관성 이슈 발생 시 재논의 |

---

## 5. 후속 태스크 후보

| # | 항목 | 비고 |
|---|------|------|
| F-1 | `scripts/install-mac.sh` 실행 — F-2 에이전트 3종 변경을 `~/.opal/agents/`에 배포 | **캡틴 후속 수행** (자동 안내) |
| F-2 | op-task/SKILL.md 카르파시 인용 처리 정책 결정 | K-2 일관성 이슈 발생 시 |
| F-3 | OPAL SSOT 영문 정책 통합 결정 (모든 SSOT 영문화 vs 한국어 유지) | K-1 일관성 이슈 발생 시 |

---

## 6. 카르파시 ↔ OPAL 매핑 흡수 결과

태스크 출처: `https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md`

| 카르파시 원칙 | OPAL 적용 위치 |
|--------------|---------------|
| §1 Think Before Coding | `coding-principles.md §1` + `op-task/SKILL.md` AC 가이드 |
| §2 Simplicity First | `coding-principles.md §2 (PLAN) / §3 (TEST-SCENARIO 희박 케이스) / §4 (EXECUTE)` |
| §3 Surgical Changes | `coding-principles.md §4 (EXECUTE)` + 워커 자가 로드 |
| §4 Goal-Driven Execution | `coding-principles.md §6 application matrix` + `op-dev-test-scenario/SKILL.md` AC↔verify 매핑 |

---

## 7. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 14:54 | 태스크 완료 — 신규 1 + 수정 7, AW-1 영문 재작성 (001) |
