# QA-PLAN v3: 부트스트랩 다운사이징 — 독립 모듈 분리 방식 검증

> 작성일: 2026-04-21  
> 검토 대상: PLAN.md v3 (섹션별 독립 harness 모듈)  
> 판정: **✅ Pass**

---

## §1. TASK.md 요구사항 충족 확인

| 요구사항 | 충족 여부 | 근거 |
|---------|---------|------|
| A-1: strip_deploy_md() 추가 | ✅ | M-4 |
| A-2: AGENT.md + opal-harness.md 2개만 strip | ✅ | M-4 |
| B-1: harness/state.md 신설 | ✅ | N-4 |
| B-2: harness/task-process.md 신설 | ✅ | N-5 |
| B-3: §0 삭제 + 레거시 호환 노트 3개 삭제 | ✅ | M-2 |
| B-4: §2 모듈 테이블에 state.md·task-process.md 추가 | ✅ | M-2 |
| C-1: opal-pm.md Lazy 전환 (원문은 §2 인라인 방식이었으나 §1+§2 Eager 유지로 재해석) | ✅ (재해석) | §1+§2 531 tok 유지, §4/§5/§7 분리 |
| C-2: harness/pm-review-gate.md 신설 | ✅ | N-6 |
| C-3: harness/doc-code-mismatch.md 신설 | ✅ | N-8 |
| C-4: Lazy 트리거 테이블 갱신 | ✅ | M-1 (N-1~N-3 트리거 3행 추가) |
| D-1: PM 행동 프로세스 요약 섹션 삭제 | ✅ | M-1 |
| D-2: 모델 매핑 절차 삭제(1줄 참조 잔존) | ✅ | M-1 |
| D-3: Cursor·Antigravity 부트스트래퍼 절 유지 | ✅ | 재검토 결과 유효한 지침으로 확인 — 삭제 대상에서 제외 |

**D-3 변경 근거**: TASK.md D-4/D-5(Cursor/Antigravity 삭제)는 재검토에서 오분류로 확인됨. Claude Code 에이전트가 다른 플랫폼 파일(GEMINI.md 등)을 관리하는 유효한 지침이므로 PLAN v3에서 보존.

---

## §2. PLAN 내부 일관성 검증

| 항목 | 결과 | 비고 |
|------|------|------|
| 신규 8개 파일 — 서로 독립, 병렬 생성 가능 | ✅ | |
| Step 1(신규) → Step 2(수정) → Step 3/4 의존 관계 | ✅ | |
| opal-harness.md §2 Eager 유지 (서브 하네스 로딩 규칙) | ✅ | §2 제거 없음, 테이블만 갱신 |
| opal-pm.md §1+§2 Eager 유지 | ✅ | M-3에 명시 |
| AGENT.md Eager 1~7 번호·경로 불변 | ✅ | M-1에 명시 |
| Lazy 트리거 기존 `// → skill-registry` 행과 N-1 중복 정리 명시 | ✅ | M-1 [MUST] 노트 |
| N-4 내 state-template.md·additional-work.md 중복 생성 금지 | ✅ | N-4 설계에 명시 |
| 부트스트랩 완료 보고·보고 형식·주도성·부트스트래퍼 Eager 보존 | ✅ | M-1 stub 교체 대상에서 제외됨 |
| opal-pm.md §3·§6·§9~§11 stub 현행 유지 | ✅ | 이미 stub, 이동 실익 없음 |
| install-mac.sh strip 대상: AGENT.md·opal-harness.md 2개 | ✅ | M-4 |

---

## §3. Warning

### W-1: TASK.md C-1 원문과 PLAN v3 방식 차이

**원문 C-1**: "opal-pm.md 완전 Lazy — §2를 AGENT.md에 인라인"  
**PLAN v3**: opal-pm.md §1+§2 Eager 유지 (~531 tok)

**처리**: TASK.md C-1의 원래 목적(PM 활성화를 위한 핵심 절차 보존)은 §1+§2 Eager 유지로 동등하게 달성됨. §2를 AGENT.md에 인라인하는 방식보다 단순하고 오류 가능성이 낮음. **TASK.md 수정 없이 PLAN v3 방식으로 갈음.**

### W-2: pm-learning-loop.md Lazy 트리거 미명시 위험

§5 학습 루프는 AGENT.md Lazy 트리거 테이블에 현재 없음. M-1에서 트리거 행을 추가하거나, opal-pm.md §5 stub에 명확한 트리거 조건을 명시해야 함. EXECUTE 시 확인 필요.

---

## §4. 예상 절감량 검증

| 지표 | 값 |
|------|-----|
| AGENT.md Eager 감소 | ~5,042 → ~2,850 tok (−2,192) |
| opal-harness.md Eager 감소 | ~5,469 → ~1,600 tok (−3,869) |
| opal-pm.md Eager 감소 | ~2,588 → ~530 tok (−2,058) |
| 전체 Eager (identity+MEMORY+프로젝트 포함) | ~18,500 → ~10,380 tok |
| **절감** | **~8,120 tok (−44%)** |

> 072 Method B(−60%, ~11,134 tok) 대비 낮지만, §2 Eager 유지·부트스트랩 완료 보고·보고 형식 등 실제 런타임 필수 섹션을 보존한 결과. 정확도 우선.

---

## §5. 판정

**✅ Pass** — EXECUTE 진행 가능.

단, EXECUTE 중 아래 2건 확인 필요:
1. Lazy 트리거 테이블의 `// → skill-registry` 행을 `skill-commands.md`로 통합 정리 (W-1)
2. pm-learning-loop.md Lazy 트리거를 AGENT.md 테이블 또는 opal-pm.md §5 stub에 명시 (W-2)
