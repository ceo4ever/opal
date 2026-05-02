# DONE: 파이프라인 현황판 JSON 분리 + state-tool 도입 (B안)

> 태스크 ID: 134-260501-opp-pipeline-state-tool | 적용 스킬: opp | 모드: interactive
> 시작: 2026-05-01 17:58 | 종료: 2026-05-02 23:30
> 결과: **완료 (Conditional Pass — 후속 갭 G1~G8 별도 태스크 분리)**

---

## 1. 작업 목표 (TASK.md 인용)

STATE.md의 "파이프라인 현황판" 표를 단일 진실(SSOT)이 JSON인 구조로 분리하고, Python 기반 `state-tool`로만 갱신 가능하게 만들어 LLM의 절차 우회/오갱신을 차단한다. STATE.md의 표 영역은 툴이 자동 렌더한 뷰로 유지하여 사람 가독성도 함께 보장.

**1차 가치**: 절차 강제력 / **2차 가치**: 토큰 효율

---

## 2. 결과 요약

### 2.1 정량 지표

| 항목 | 값 |
|------|-----|
| 총 진행 기간 | 약 30시간 (5/1 17:58 → 5/2 23:30) |
| EXECUTE Step | 16/16 완료 (Phase 1~9) |
| 신규 파일 | 5개 (state-tool 본체+래퍼+스키마+README+테스트) |
| 수정 파일 | 41개 (하네스 9 / 스킬 10 / 에이전트 8 / 가이드 12 / 등록부 1 / 배포 1) |
| 단위 테스트 | 121건 통과 (0 fail / 0 error) |
| 회귀 테스트 | 134 자기 회귀 + dummy 3건(opp/opd/force) 모두 통과 |
| 의사결정 로그 | 40건 |
| 후속 갭 | 8건 (G1~G8) |

### 2.2 핵심 산출물

| # | 경로 | 역할 | 줄수 |
|---|------|------|------|
| N-1 | `opal/tools/state-tool/state_tool.py` | 9개 서브 명령 본체 + ERROR_CODES 23종 | 1272 |
| N-2 | `opal/tools/state-tool/run.sh` | bash 래퍼 (~/.opal/.venv/bin/python) | 12 |
| N-3 | `opal/tools/state-tool/schema/state.schema.json` | JSON Schema Draft-07 | 105 |
| N-4 | `opal/tools/state-tool/README.md` | 9개 명령 사용법 + 종료 코드 + 에러 카탈로그 | 277 |
| N-5 | `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 (121 케이스) | 1759 |

### 2.3 9개 서브 명령

| 명령 | 동작 |
|------|------|
| `init` | state.json + STATE.md(마커 + 자유 텍스트 3섹션) 생성. `--rows-from`/`--rows-spec` 외부 주입, `--import-existing` 흡수 |
| `show` | 마크다운 표/JSON/full 출력. 마커 손실 시 fallback |
| `advance` | ⬜→🔄 전환 |
| `mark` | ⬜/🔄→✅ 전환. `--as-worker --worker-stage`, `--owner user`, `--auto-pass`, `--force` 지원 |
| `block` | any→❌ + current_status=blocked |
| `validate` | 정합성 검증 → violations[] |
| `add-row` | 추가작업 행 삽입 + current_status 자동 `additional_work` 전환 + row_id 재정렬 |
| `status` | current_status 명시 전환 (5종 enum) |
| `gate-pass` | Gate 4행 일괄 ✅ (4행 표준 패턴 한정) |

---

## 3. 변경 파일 매트릭스

### 3.1 신규 — `opal/tools/state-tool/`
- `state_tool.py` (본체)
- `run.sh` (래퍼)
- `schema/state.schema.json`
- `README.md`
- `tests/test_state_tool.py`

### 3.2 수정 — 하네스 (9)
- `opal/core/references/opal-harness.md` §3 [MUST] state-tool 호출 의무 + §9 도구 테이블
- `opal/core/references/opal-harness-interactive.md` Gate 후 mark 호출 + state validate 자가진단
- `opal/core/references/opal-harness-agentic.md` --auto-pass + agentic_close_gate_requires_user
- `opal/core/references/harness/state.md` 갱신 이벤트 표 + [MUST] 블록
- `opal/core/references/harness/state-template.md` [MUST] LLM 직접 작성 금지 + 마커 형식
- `opal/core/references/harness/task-process.md` `state init` 호출 명시
- `opal/core/references/harness/pm-review-gate.md` 12번 항목 + force 자가진단 + gate-pass
- `opal/core/references/harness/additional-work.md` add-row + status 호출
- `opal/core/references/tools.md` state-tool 섹션 신규

### 3.3 수정 — 스킬 (10)
- `opal/skills/opal-pilot-{project, dev, dev-short, dev-wireframe, gc, project-dev, sdd, write-tech}/SKILL.md` (8) — P-1~P-8 매트릭스 일관 적용
- `opal/skills/op-task/SKILL.md` — `state init` 호출
- `opal/skills/op-dev-execute/references/execute-guide.md` — 워커 mark `--as-worker --worker-stage`

### 3.4 수정 — 에이전트 (8)
- `opal/agents/opal-{be, db, fe, plan, task, sdd-action, task-action}-agent/AGENT.md` (7)
- `opal/agents/opal-planning-agent/personas/service-planner.md` (1)

### 3.5 수정 — 가이드 (12)
- 실질 갱신 3개: oppd `parallel-execution-guide.md` / `verification-loop-guide.md` / sdd `execute-loop-guide.md`
- 단순 참조 9개: harness `parallel-execution.md` / `qa-standards.md` / oppd `wbs-guide.md` / `roadmap-guide.md` / `prd-guide.md` / `trd-guide.md` / sdd `spec-plan-guide.md` / `verify-guide.md` / gc `done-template.md`

### 3.6 수정 — 배포 (1)
- `scripts/install-mac.sh` — state-tool/run.sh chmod +x 처리

---

## 4. 검증 결과

### 4.1 단위 테스트 (Step 2)
- `python3 -m unittest opal/tools/state-tool/tests/test_state_tool.py`
- **Ran 121 tests in 0.097s — OK** (0 fail / 0 error)
- 23종 에러 코드 cross-ref / G-5~G-15 시나리오 / C-1~C-6 충돌 / 9개 명령 happy path / 자유 텍스트 보존

### 4.2 회귀 테스트 (Step 7 + Step 16)
- **134 자기 회귀**: `state init --import-existing` 1차 시도 즉시 성공. 마커 자동 삽입 + 자유 텍스트 보존 + validate 0건
- **dummy(1) interactive×opp 20행**: init/mark/CLOSE 게이트 거부+복구/add-row+status 전이 모두 통과
- **dummy(2) agentic×opd 25행**: 사용자 확인 자동 na 마킹 / `agentic_close_gate_requires_user` 거부 / `--owner user` 복구
- **dummy(3) force**: `already_initialized` / `note_required_for_force` / 의사결정 로그 자동 기재 (트리거 #1)

### 4.3 EXECUTE QA Gate (행 13)
- opal-task-qa-agent 검증 결과: **Conditional Pass** (갭 G1~G5 후속 분리, 본 태스크 차단 없음)
- QA-EXECUTE.md 23KB 산출물

### 4.4 PM Gate (행 16)
- state validate: violations 0건
- 121 단위 테스트 통과
- 4개 회귀 통과
- 영역 간 용어 일관성 통과

### 4.5 사용자 확인 (행 18)
- 캡틴 "확인" 발화 (2026-05-02 23:30) → owner=user 마킹 → CLOSE 진입 승인

---

## 5. 발견 갭 — 후속 태스크 후보

| # | 갭 | 발견 시점 | 영향 | 처리 방안 |
|---|---|----------|------|---------|
| **G1** | import-existing 사용자 확인 행 owner 자동 인식 미구현 | Step 7 회귀 | 마이그레이션 시 mark 정정 필요 | 후속 태스크 — `state_tool.py` import-existing 로직 보강 |
| **G2** | init 시 `## 현재 상태 - 진행:` "TASK 단계" 초기화 — 마지막 진행 단계 자동 추론 부재 | Step 7 회귀 | import-existing 후 표기 불일치 | 후속 태스크 — import-existing 시 마지막 done 행의 stage 추론 |
| **G3** | `> 최종 갱신:` 헤더 부가 설명 자동 제거 (G-5 의도 동작) | Step 7 회귀 | PM 의사소통 정보 손실 | 운영 가이드 — 부가 설명은 의사결정 로그/다음 액션에 기재 |
| **G4** | mark --as-worker --step <N/M> 부분 진행 표기가 행 자체를 ✅ 처리 | Step 8 후 행 12 ✅ | EXECUTE 16개 Step 미완 시점에 행 ✅ 표기 | 후속 태스크 — `--step` 메타 필드 분리 |
| **G5** | opp/opd/opds PLAN 5행 패턴 vs 도구 GATE_PATTERN 4행 — gate-pass 거부 | Step 16 dummy + task 010 | PLAN §2.13 G-10 가정 결함 | 후속 태스크 — schema v2 단계별 구조화 + GATE_PATTERN 동적 추론 |
| **G6** | rows[] 단계별 구조화 검토 (schema v2) — `stages: [{name, rows}]` | 캡틴 검토 | 단계별 일괄 처리 / pass-stage / G5 자연 해결 | 후속 태스크 — schema v2 + 마이그레이션 도구 |
| **G7** | 사용자 확인 행 init 시 owner=PM 부정확 (interactive 모드) | 캡틴 검토 + task 010 | 운영상 misleading | 후속 태스크 — `expected_owner` 필드 또는 enum 확장 |
| **G8** | `validate`가 timestamp/패턴 위반 미탐지 | task 010 검증 | schema 엄격 검증 누락 | 후속 태스크 — `state_tool.py` validate 로직 보강 + 단위 테스트 추가 |

후속 태스크 우선순위 권고: **G6(schema v2 단계별 구조화)이 G5/G4를 자연 해결하므로 가장 우선** → G7/G8 → G1/G2 → G3는 운영 가이드만.

---

## 6. 캡틴 액션 권고

본 태스크 CLOSE 후 다음 단계:

1. **git commit** — 본 태스크 모든 산출물 (.opal/AGENT.md §확정 기준 1)
2. **`scripts/install-mac.sh` 실행** — `~/.opal/`에 도구·하네스·스킬·에이전트 배포
3. **다음 신규 태스크에서 자연 검증** — `op-task` 진입 시 `state init` 호출되며 새 흐름이 즉시 적용
4. **후속 갭 태스크 채번** — G1~G8 보강. G6(schema v2)을 가장 우선 권고

---

## 7. 의사결정 로그 (40건)

자세한 흐름은 `STATE.md ## 의사결정 로그` 섹션 참조 (init 채택 → 18 사용자 확인까지).

핵심 결정:
1. **B안 하이브리드 채택** — 파이프라인 표만 JSON 분리, 의사결정 로그/블로커/다음 액션은 자유 텍스트 유지
2. **PLAN 3차례 보강** — v1(16 Step / 9 Phase) → v2(1034줄, G-1~G-15) → v3(1450줄, E-1~E-6, 에러 23종 SSOT, 인자 매트릭스, 입력 형식, 롤백 정책, fallback, P-1~P-8)
3. **EXECUTE 디스패치 전략 (A) 보수적** — Phase 6 Step 8+10 병렬 → Step 9 단독, Phase 7 Step 11+12 병렬, 나머지 순차
4. **갭 8건 모두 후속 태스크 분리** — 본 태스크 차단 없음 확정

---

## 8. 핵심 인용

- TASK.md 요구사항 F-1~F-23 충족
- PLAN.md §2.11~§2.21 SSOT 일관 적용
- `opal/.opal/AGENT.md` §개발/배포 경계 + §확정 기준 #2 준수
- `opal/core/references/harness/citation-rules.md` §0/§2/§7 인용 규칙 적용

---

## 9. 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-02 | DONE.md 최초 작성 — 134 EXECUTE 종료 + CLOSE 진입 |

---

> 본 태스크는 OPAL 프레임워크의 절차 강제력 핵심 인프라(state-tool)를 도입한 작업이며, 이후 모든 OPAL 태스크의 STATE.md 갱신 동작이 도구 차원에서 강제된다. 후속 갭 G1~G8 보강 시 G6(schema v2 단계별 구조화)을 우선 처리하면 G4/G5/G7이 함께 해결되어 효율적이다.
