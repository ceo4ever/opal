# DONE: 부트스트랩 다운사이징 — Eager 로드 최적화

> 완료일: 2026-04-21 12:51 | 시작일: 2026-04-20 20:21 | 적용 스킬: opp | 모드: interactive
> 입력: TASK.md, PLAN.md (v3), QA-EXECUTE.md
> 산출물: harness 모듈 7건 + 수정 파일 4건

---

## 1. 태스크 개요

세션 시작 시 Eager 로드되는 부트스트랩 파일(AGENT.md, opal-harness.md, opal-pm.md)의 총 토큰 소비(~13,000 tok)를 절반 수준으로 감축한다. 소스는 보존하되 Lazy 로드 가능한 섹션을 독립 harness 모듈로 분리하고, install-mac.sh 배포 시점에 변경이력을 strip한다.

---

## 2. 요구사항 진행 결과 (TASK.md 기준)

### Track A — install-mac.sh 배포 시 strip

| # | 요구사항 | 상태 | 비고 |
|---|---------|------|------|
| A-1 | `strip_deploy_md()` 함수 추가 | ✅ | line 179 |
| A-2 | strip 대상 파일 범위 정의 | ✅ | **범위 확장**: AGENT.md + 모든 배포 .md 파일(53개) |

### Track B — opal-harness.md 슬림화

| # | 요구사항 | 상태 | 비고 |
|---|---------|------|------|
| B-1 | `harness/state.md` 신설 + §3 stub | ✅ | 104줄 |
| B-2 | `harness/task-process.md` 신설 + §4 stub | ✅ | 58줄 |
| B-3 | §0 용어 정의 + §3 레거시 호환 노트 3개 제거 | ✅ | `grep "^## 0" / grep "레거시 호환"` = 0 |
| B-4 | §2 모듈 테이블에 신규 항목 추가 | ✅ | line 93, 94 |

### Track C — opal-pm.md Lazy 전환

| # | 요구사항 | 상태 | 비고 |
|---|---------|------|------|
| C-1 | PM 컨텍스트 로드 절차 AGENT.md 인라인 | ✅ | AGENT.md Eager 4단계가 opal-pm.md Read (기존 유지) + §2 PM 직접 작업 docs 프리로드 규칙 추가 |
| C-2 | `harness/pm-review-gate.md` 신설 + §4 stub | ✅ | - |
| C-3 | `harness/doc-code-mismatch.md` 신설 + §7 stub | ✅ | 34줄 |
| C-4 | Lazy 트리거 테이블 갱신 | ✅ | AGENT.md line 29(skill-commands), line 35(memory-learning) |

### Track D — AGENT.md 죽은 지침 정리

| # | 요구사항 | 상태 | 비고 |
|---|---------|------|------|
| D-1 | PM 행동 프로세스 요약 섹션 제거 | ✅ | `grep "^## PM 행동 프로세스"` = 0 |
| D-2 | 모델 매핑 절차 섹션 제거 (1줄 참조만 유지) | ✅ | 상세 절차 제거, `~/.opal/references/opal-model-mapping.md` 참조 1줄 |
| D-3 | 부트스트래퍼 자동 관리 Cursor/Antigravity 절 제거 | ⏸️ | **취소**: 의사결정 로그 #3 — 유효 지침으로 재확인 (Claude Code에서 타 플랫폼 파일 관리 목적) |

> D-3는 대화 중 재검토하여 보존하기로 결정. TASK 요구사항에서 공식 취소됨.

---

## 3. 핵심 산출물

### 신규 harness 모듈 7건

| 파일 | 출처 | 로드 시점 |
|------|------|----------|
| `harness/skill-commands.md` | AGENT.md §스킬레지스트리·§쌍슬래시 | `//` 커맨드 입력 시 |
| `harness/memory-learning.md` | AGENT.md §기억과 학습 | 메모리 쓰기 / "이거 기억해둬" 발화 시 |
| `harness/state.md` | opal-harness.md §3 | TASK 시작 / Gate 직후 State Gate |
| `harness/task-process.md` | opal-harness.md §4 | TASK 단계 진입 시 |
| `harness/pm-review-gate.md` | opal-pm.md §4 | PM Gate 수행 시 |
| `harness/pm-learning-loop.md` | opal-pm.md §5 | 판단 불확실 / 학습 루프 진입 시 |
| `harness/doc-code-mismatch.md` | opal-pm.md §7 | 문서·코드 불일치 감지 시 |

### 수정 파일 4건

| 파일 | 변경 요약 | 줄 수 변화 |
|------|---------|-----------|
| `opal/core/AGENT.md` | 스킬·메모리·컨텍스트 stub화, PM 행동/모델 매핑 삭제, Lazy 트리거 2행 추가, 변경이력 v2.0 추가 | 371 → 308 (소스) / 292 (배포) |
| `opal/core/references/opal-harness.md` | §0 삭제, §3/§4 → stub, 레거시 노트 3건 삭제, 모듈 테이블 갱신, v4.4 추가 | 377 → 240 (소스) / 211 (배포) |
| `opal/core/references/opal-pm.md` | §4/§5/§7 → stub, §2 PM 직접 작업 프리로드 규칙 추가, 변경이력 v1.0 신규 | 201 → 131 (소스) / 124 (배포) |
| `scripts/install-mac.sh` | `strip_deploy_md()` + `strip_deploy_md_recursive()` 함수 추가, 호출 4건(AGENT + references/skills/agents 재귀) | 함수 2개 + 호출 4건 추가 |

---

## 4. 절감량 메트릭

### 소스 vs 배포 줄 수 비교

| 파일 | 원본 | 수정 후 소스 | 배포 후 | 감소율 (배포) |
|------|------|------------|--------|-------------|
| AGENT.md | 371 | 308 | 292 | **−21%** |
| opal-harness.md | 377 | 240 | 211 | **−44%** |
| opal-pm.md | 201 | 131 | 124 | **−38%** |
| **합계 (Eager 3파일)** | **949** | **679** | **627** | **−34%** |

> 토큰 기준 예상 절감: 약 7,900 tok (−43%, PLAN 추정 범위 내)

### 추가 효과 (의사결정 로그 #5 반영)

배포 시 53개 .md 파일에서 변경이력 일괄 제거. Eager 외 Lazy 로드 파일도 로드 시점 토큰 절감.

---

## 5. 의사결정 로그 (PLAN + 대화에서 도출)

| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-04-20 | opal-pm.md 전체 Lazy 전환 + §2 AGENT.md 인라인 | PM 활성화 절차는 14줄로 최소화, 나머지는 디스패치 시점에만 필요 |
| 2 | 2026-04-21 | C안 → v3 확정: *-detail.md 폐기, 섹션별 독립 harness 모듈 8개 분리 | 실제 Eager 필수 섹션 재분류. 절감 ~8,120 tok(−44%) |
| 3 | 2026-04-21 | Cursor·Antigravity 부트스트래퍼 절 삭제 취소 | Claude Code 에이전트가 타 플랫폼 파일 관리 목적으로 사용됨 |
| 4 | 2026-04-21 | AGENT.md 변경이력 소스 보존 + 배포 시 strip (A안) | TASK "소스 보존" 원칙 준수. M-1 보정으로 v1.0~v2.0 복원 |
| 5 | 2026-04-21 | strip 범위를 모든 배포 .md 파일(53개)로 확장 | 캡틴 지시. `strip_deploy_md_recursive()` 신규 함수 도입 |

---

## 6. 검증

- **QA-EXECUTE.md**: 전 항목 Pass (§1~§6, M-4-v2 포함)
- **grep 검증**: 삭제 대상 섹션 0 matches 확인 (§0 용어, PM 행동 프로세스, AGENT.md 변경이력 등)
- **strip 시뮬레이션**: 임시 디렉토리에서 `strip_deploy_md_recursive` 동작 확인 — 변경이력 있는 파일만 strip, 없는 파일 무수정, 설치 로그 오염 없음
- **`bash -n` 구문 검사**: install-mac.sh 통과
- **PM Gate**: 11항목 체크리스트 Pass (QA-EXECUTE.md §1.2~§1.5 참조)

---

## 7. 후속 액션

- **배포**: 캡틴이 `install-mac.sh` 실행 시 변경 반영 (배포는 이 태스크 범위 밖)
- **검증 (배포 후)**: `~/.opal/AGENT.md` 및 `~/.opal/references/*.md` 파일들의 `## 변경이력` 섹션 부재 확인
- **새 세션 토큰 측정**: 다음 세션 시작 시 실제 Eager 로드 토큰 감소량 측정 (예상: ~43%)
- **커밋**: 캡틴 지시 시 수행 (하네스 §1 커밋 규칙)

---

## 8. 제약 조건 준수 확인

- ✅ `~/.opal/` 직접 수정 없음 (모든 변경은 `opal/` 소스에서 수행)
- ✅ opal-harness.md §1 Guards + §2 모듈 구조 Eager 유지
- ✅ PM 컨텍스트 로드 절차(§2)는 opal-pm.md에 유지 + AGENT.md §2에 프리로드 규칙 추가
- ✅ harness/ 신규 모듈 탐색 경로 규칙 준수
- ✅ 기존 하네스 §2 모듈 테이블 갱신 (오케스트레이터가 새 경로 탐색 가능)
