# QA: PLAN v2 — 파이프라인 현황판 JSON 분리 + state-tool 도입 (B안)

> 검토일: 2026-05-01 | 판정: **Conditional Pass**
> 검증 기준: 갭 15건 정정 완결성 + EXECUTE 워커 컨텍스트 완결성

---

## 1. 요약

PLAN v2(1034줄)는 QA-PLAN(v1) 지적 사항 2건(Step 완료 기준 정량화, agentic na 마킹 검증)을 신설된 §2.11~§2.17로 충실히 해소하고, G-1~G-15 갭 15건 대부분을 명세 수준으로 정정했다. 특히 §2.11~§2.17은 EXECUTE 워커가 추측 없이 그대로 구현할 수 있는 상세 알고리즘(정규식·에러 코드·JSON 응답·전이 그래프)을 제공한다. 그러나 v2 보강 과정에서 **파일 목록 테이블(N-1, N-4, N-5)과 §2.1, M-40, Step 14에 "7개 서브 명령" 표현이 9개로 갱신되지 않은 내부 불일치(Warning)**가 잔존한다. G-7 전이 그래프에서 `status --set blocked` 명시 허용 여부가 모호한 부분도 워닝 수준으로 존재한다. 이 두 항목은 EXECUTE 워커 컨텍스트에서 혼란을 야기할 수 있어 수정 권장이나, EXECUTE 진행을 완전 차단하지는 않는다.

---

## 2. 검증 결과

### 2.1 갭 15건 정정 검증 (G-1 ~ G-15)

| 갭 | 보강 위치 | 판정 | 근거 |
|----|---------|------|------|
| G-1 | §2.2 `required` 배열 + `created_at`/`updated_at` properties | **충실** | `"required": ["task_id", "skill", "mode", "schema_version", "created_at", "updated_at", "current_status", "rows"]` 명시. pattern `"^\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}$"` 양쪽 동일 적용. G-5에서 `updated_at` 동기화 정책 추가 확인 (PLAN.md:403) |
| G-2 | §2.2 rows[].timestamp/note properties + required 갱신 | **충실** | `"required": ["row_id", "stage", "item", "status", "status_label", "timestamp"]` 명시 (PLAN.md:229). `timestamp`는 oneOf(string|null) + pattern 정의. `note`는 oneOf(string|null). `owner`는 optional(not in required) — 의도적 설계(null 허용) |
| G-3 | §2.2 stage enum 16종 + 8개 SKILL.md grep 근거 표 | **충실** | PLAN.md:283-294에 8개 SKILL.md별 출처 라인 + 기여 토큰 표 완비. 합집합 16종 명시. opsdd "EXECUTE-LOOP" → enum `EXECUTE` 통일 결정 근거 명시 |
| G-4 | §2.2 item 검증 패턴 + STANDARD_ITEMS / GATE_PATTERN 상수 | **충실** | `STANDARD_ITEMS` Python 코드 스니펫 + `GATE_PATTERN = [...]` 정의 (PLAN.md:304-311). validate 명령 사용 근거 + item이 enum 아닌 자유 string인 이유 명시 |
| G-5 | §2.11 최종 갱신 헤더 자동 갱신 정규식 명세 | **충실** | 대상 라인 패턴 `^> 최종 갱신: .*$` + 치환 정규식 `^(> 최종 갱신: ).*$` + 멀티라인 모드 명시 + date.js subprocess 코드 + 실패 정책 명시 (PLAN.md:397-404) |
| G-6 | §2.11 현재 상태 4줄 자동 갱신 매핑 표 + --step 인자 | **충실** | 명령/트리거별 `- 진행:`/`- 상태:` 갱신 매핑 표 8행 완비 (PLAN.md:412-421). `--step <N/M>` 인자 추가 + EXECUTE Step 진행 표기 명세 (PLAN.md:424). `- 모드:`/`- 단계:` init만 작성·이후 미변경 정책 명시 |
| G-7 | §2.11 `state status` 8번째 명령 신설 + 전이 그래프 | **부분** | 시그니처 명시 (PLAN.md:431-433). 허용 전환 5개 열거 + 거부 전환 정책. `어떤 상태 → blocked` 항목에서 `block` 명령이 자동 처리하므로 `status --set blocked` 호출의 허용/거부 여부 불명확 (`--set` 옵션에는 `blocked`가 포함되어 있으나 허용 전환 목록에는 `block 명령 시 자동`으로만 기재 — §2.11 G-7:440). 구현자 입장에서 `status --set blocked`가 valid한지 판단 불가. |
| G-8 | §2.11 init 시 STATE.md 전체 템플릿 + --task-title/--next-action | **충실** | 신규 시그니처 9개 인자 명세 (PLAN.md:450-459). STATE.md 전체 템플릿(자유 텍스트 3개 섹션 포함) 코드 블록 제공 (PLAN.md:464-495). `--import-existing` 처리 정책 명시 |
| G-9 | §2.12 add-row 알고리즘 단계별 명세 + row_id 재정렬 | **충실** | 10단계 순차 알고리즘 (PLAN.md:507-531). row_id 재정렬: `신규 row_id = N+1`, 이후 행 +1 재정렬 정책. 에러 응답 JSON 명시. current_status 자동 전환 분기 명시 |
| G-10 | §2.13 gate-pass 9번째 명령 + 4행 패턴 검증 + 비표준 거부 | **충실** | 시그니처 + 6단계 동작 명세 (PLAN.md:547-562). `gate_pattern_mismatch` / `gate_stage_mixed` 에러 응답 JSON 명시. 비표준(opsdd/oppd) 거부 정책 명시 |
| G-11 | §2.14 show --format md/json/full + 마커 손실 fallback 3종 | **충실** | format 3종 출력 내용 표 (PLAN.md:574-578). 마커 손실 시 format별 fallback 3종 상세 (PLAN.md:582-596). `state.json` 미존재 시 에러 정책 명시 |
| G-12 | §2.15 사용자 확인 owner 매트릭스 + validate 검증 | **충실** | 호출 형식 + owner 저장 동작 (PLAN.md:606-618). validate 검증 2개 조건 (`user_confirmation_owner_mismatch`, `auto_pass_in_interactive_mode`) 명시. 모드×owner 매트릭스 3행 (PLAN.md:637-641) |
| G-13 | §2.16 CLOSE 진입 자동 검증 + agentic close gate requires user | **충실** | 검증 알고리즘 6단계 (PLAN.md:651-674). agentic 모드 거부 에러 `agentic_close_gate_requires_user` 명시. `--force` 우회 + 의사결정 로그 연동 명시 |
| G-14 | §2.17 의사결정 로그 8 트리거 SSOT 표 | **충실** | 8개 트리거 × 결정/근거/state.json영향 3컬럼 표 (PLAN.md:686-695). 기재 동작 명세(위치/표형식/#컬럼/시점/정규식) 완비 (PLAN.md:699-711) |
| G-15 | §2.17 트리거 #1/#3/#8 --note 필수 + 시점 + 컬럼 자동 증가 | **충실** | `--note 필수 트리거` 명시 + `note_required_for_force` 에러 코드 (PLAN.md:704). `#` 컬럼 자동 증가 알고리즘 "기존 표의 마지막 # + 1, 비어 있으면 1부터" 명시. 삽입 정규식 코드 스니펫 제공 |

**G-1~G-15 종합**: 충실 13건 / 부분 1건(G-7) / 누락 0건

---

### 2.2 EXECUTE 워커 컨텍스트 완결성 검증

| 항목 | 판정 | 비고 |
|------|------|------|
| 모호한 표현 잔존 | Pass | "적절히", "필요시", "상황에 따라" 0건. "추정 출력" 1건(R-4/§2.1:205)은 fallback 동작 설명으로 허용 범위 |
| 정량 임계 명시 | Pass | violations 0건, 20개 행, 40건 이상 테스트, grep 0건 등 정량 기준 충분 |
| 추측 의존 표현 | Pass | 설계 결정 전체에 근거 인용(D-N, TASK T-N, §N). §2.11~§2.17은 "EXECUTE 워커는 이 절을 그대로 구현한다 (추가 추측 금지)" 명시 |
| 인라인 인용 | Pass | §2 핵심 설계 본문 전체에 `(→ D-N §N)` / `(→ TASK T-N)` 인용 일관 사용 |
| **PLAN 내부 불일치 — "7개 서브 명령" 잔재** | Warning | N-1/N-4/N-5 신규 파일 테이블에 "7개 서브 명령"(PLAN.md:127,130,131). §2.1 구현 명세 PLAN.md:203에 "7개 서브 명령 시그니처는 TASK F-2 그대로". M-40(Step 14) PLAN.md:155,899에 "커맨드 7종". 실제 §2.11 G-7/G-10에서 9개로 확장되었으나 이 표현들이 미갱신. EXECUTE 워커가 7개 기준으로 N-1 구현 시 누락 위험 |

---

### 2.3 F-1~F-23 TASK 요구사항 커버리지 (재검증)

v1 QA에서 이미 검증된 F-1~F-23 매핑은 v2에서도 보존됨. v2에서 추가된 9번째 명령(status, gate-pass)은 TASK F-2 확장으로 PLAN이 SSOT — TASK 본문과 모순 없음 확인.

| 항목 | 판정 | 비고 |
|------|------|------|
| F-1~F-23 커버리지 | Pass | v1 QA 확인 보존 + v2 신설 §2.x에서 F-2 확장 명시 |
| TASK 본문과 모순 | Pass | "TASK.md 본문은 변경 없이 PLAN이 SSOT" 명시(PLAN.md:444, 564). TASK는 v2 안정화 상태 — 충돌 없음 |
| F-18 체크리스트 갱신 | Pass | v1 QA에서 이미 `[x]` 처리 완료 |

---

### 2.4 T-1~T-13 기술 결정 보존 검증

v2 보강이 §2.1~§2.10의 기존 결정을 역행하지 않았는가?

| 기술 결정 | 보존 여부 | 비고 |
|---------|---------|------|
| T-1~T-13 전체 | Pass | §2.11~§2.17은 T-5(시점), T-6(마커), T-7(advance/mark 분리), T-8(멱등성), T-9(auto-pass), T-10(워커 권한) 결정을 그대로 계승하며 확장만 함 |

---

### 2.5 마이그레이션 순서 정합성 (신규 명령 포함)

| 검증 항목 | 판정 | 비고 |
|---------|------|------|
| status/gate-pass 신설 → Step 1/2에 포함 | Pass | Step 1 작업 내용에 9개 명령 명시(PLAN.md:739). Step 2 테스트에 G-7/G-10 시나리오 포함(PLAN.md:769,772) |
| Step 13(pm-review-gate/interactive/agentic) gate-pass 표기 추가 | Pass | PLAN.md:886,888에 gate-pass 호출 권장 표기 명시 |
| 의존 관계 역행 | Pass | v1 QA 검증 보존 + 신규 명령이 Step 1/2에만 영향 |

---

### 2.6 §4 QA 체크리스트 + §5 리스크 보강 충실도

| 항목 | 판정 | 비고 |
|------|------|------|
| §4 G-7~G-15 시나리오 14건 추가 | Pass | 기능 테스트 19+14=33항목 추가 확인. 일관성 테스트 13항목(§2.11 G-5/G-6/G-8 보강). §4 총 71개 체크항목 |
| §5 R-10/R-11/R-12 추가 | Pass | gate-pass 비표준 거부 / --force 남발 / agentic CLOSE 게이트 리스크 각각 구체적 대응 방안 포함 |

---

### 2.7 인용 규칙 준수 (citation-rules.md)

| 항목 | 판정 | 비고 |
|------|------|------|
| §1 참조 문서 테이블 | Pass | D-1~D-19 19개 유지. v2 보강에서 추가 D-20 등 불필요 (§2.11~§2.17이 기존 D-1~D-19 인용만으로 충분) |
| 인라인 인용 | Pass | §2.11~§2.17 각 결정에 `(→ TASK T-N)` / `(→ D-N)` / state-template.md:N 형태 인용 일관 |
| [MUST] 포맷 | Pass | §2.1에 3건 [MUST] 유지. G-8 STATE.md 직접 작성 금지 연동 명시 |
| [MUST] 토큰 일관성 | Pass | `state.md`, `state-template.md`, `op-task/SKILL.md` 3곳 명시 목표 일관 |

---

### 2.8 영역 간 용어 일관성 (citation-rules.md §7)

| 토큰 | 판정 | 비고 |
|------|------|------|
| `state-tool` 도구명 | Pass | TASK ↔ PLAN 일관 |
| `state.json` 파일명 | Pass | TASK ↔ PLAN 일관 |
| 서브 명령 9개 | **Warning** | §5 용어 일관성 검토에 "9개 서브 명령 일관, 옛 7개 표기 0건 목표" 명시(PLAN.md:979)되어 있으나, 정작 PLAN 본문 자체(N-1, N-4, N-5, §2.1:203, M-40:155,899)에 "7개" 잔재. 자기모순 |
| `STANDARD_ITEMS` / `GATE_PATTERN` | Pass | §2.2 정의 → §2.13 참조 일관 |

---

### 2.9 TASK.md 체크리스트 갱신 분석

v1 QA에서 F-18만 갱신 대상으로 판정하여 이미 `[x]` 처리됨.

v2 보강에서 새롭게 PLAN 단계 설계 완료로 처리 가능한 항목 재검토:

- **F-3** (state.json 스키마 정의): AC는 "JSON Schema (Draft-07) 작성" — PLAN §2.2에서 완전한 스키마를 정의·제공했으나, TASK F-3의 AC는 "구현 완료 + 위반 시 모든 명령이 거부" — **구현이 AC 핵심이므로 EXECUTE 후 처리**. `[ ]` 유지.
- **F-5** (워커 권한 게이트): PLAN §2.4에서 `--as-worker --worker-stage` 방식 결정 완료 — 그러나 AC는 "실제 거부 동작" — **EXECUTE 구현 필요**. `[ ]` 유지.
- **F-23** (추가 회귀 표본): PLAN §2.9에서 dummy 2건 결정 — AC는 "실행 검증" — `[ ]` 유지.

**결론**: v1 QA에서 `[x]` 처리된 F-18 외에 추가 갱신 대상 없음. TASK.md 체크리스트 변경 없음.

---

### 2.10 보강 결과 파일 크기 적정성

576 → 1034줄(약 80% 증가). §2.11~§2.17(약 330줄)이 대부분을 차지하며, 각 절이 EXECUTE 워커 컨텍스트 완결성을 위한 정량 명세(알고리즘/에러코드/JSON/정규식)로 구성되어 **장황이 아닌 필수 명세**로 판단됨. QA 체크리스트 추가(±40줄), 리스크 추가(±10줄)도 적정.

---

## 3. 지적 사항

### Warning-1: PLAN 내부 "7개 서브 명령" 표현 미갱신 (5개소)

**심각도**: Warning

**영향 범위**: EXECUTE 워커 구현 시 혼란 야기 가능

**대상 위치**:
- `PLAN.md:127` N-1 테이블: "도구 본체 — 7개 서브 명령 구현"
- `PLAN.md:130` N-4 테이블: "사용법 문서 — 7개 서브 명령 + ..."
- `PLAN.md:131` N-5 테이블: "단위 테스트 — 7개 명령 × happy path"
- `PLAN.md:203` §2.1: "7개 서브 명령 시그니처는 TASK F-2 그대로"
- `PLAN.md:155,899` M-40/Step 14: "커맨드 7종"

**내용**: v2 보강에서 §2.11 G-7(status)·G-10(gate-pass)으로 서브 명령이 9개로 확장되었으나, 파일 목록 테이블(N-1, N-4, N-5)과 §2.1 구현 명세, M-40(tools.md 등록) 기술에 "7개" 표현이 잔존한다. §4 일관성 테스트(PLAN.md:979)에서 "갱신된 본문에서 옛 7개 명령만 표기된 곳이 0건" 목표를 선언했으나 PLAN 자체에서 자기모순 발생.

**권고**: Step 1 착수 전에 N-1/N-4/N-5 설명란, §2.1:203, M-40/Step 14를 "9개 서브 명령"으로 수정. 또는 EXECUTE 워커가 §2.11 G-7/G-10 및 §3 Step 1/2 작업 내용의 "9개" 표기를 우선 기준으로 삼는다는 명시 노트를 추가.

---

### Warning-2: G-7 전이 그래프 — `status --set blocked` 허용/거부 불명확

**심각도**: Warning

**영향 범위**: state_tool.py 구현 시 `status --set blocked` 처리 방식 불명확

**내용**: §2.11 G-7 시그니처(PLAN.md:433)에서 `--set <in_progress|done|blocked|additional_work|additional_work_done>` 옵션 목록에 `blocked`가 포함되어 있다. 그러나 허용 전환 목록(PLAN.md:435-440)에는 `"어떤 상태 → blocked (block 명령 시 자동)"` 으로만 기재되어, `status --set blocked` 명시 호출이 허용 전환인지 거부 전환인지 판단 불가. `block` 명령과 `status --set blocked`의 중복/충돌 여부도 불명확.

**권고**: EXECUTE 착수 전 한 줄 결정 추가: "status --set blocked는 block 명령과 동일 효과로 허용" 또는 "status --set blocked는 거부 — block 명령만 허용". 단위 테스트 Step 2의 "거부 × 3" 케이스에도 이 결정을 반영.

---

### Info-1: v1 QA Warning 2건 해소 확인

v1 QA Warning-1(Step 3/5/6/8 완료 기준 정량화 미흡)과 Warning-2(agentic na 마킹 검증 항목 누락)는 v2 §2.11~§2.17 신설로 완전 해소됨. Warning-2는 특히 §2.15 G-12 모드×owner 매트릭스 + §2.16 G-13 agentic close gate 차단으로 오히려 강화됨.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md F-1~F-23 | PLAN §3 Step 전체 매핑 (v2 포함) | Pass — 23/23 커버, v2 확장은 PLAN이 SSOT |
| TASK.md T-1~T-13 | PLAN §2 핵심 설계 반영 | Pass — 13/13 반영, v2가 역행하지 않음 |
| TASK.md 제약 마이그레이션 순서 | PLAN §3 Phase 1~9 | Pass — 신규 명령도 Phase 1/2에 통합 |
| citation-rules.md §4 PLAN 의무 | §1 참조 테이블 + 인라인 인용 + [MUST] | Pass |
| v1 QA Warning 2건 | §2.11~§2.17 해소 여부 | Pass — 완전 해소 |

---

## 5. 판정

**Conditional Pass**

PLAN v2는 G-1~G-15 갭 15건 중 14건을 EXECUTE 워커가 그대로 구현 가능한 수준의 명세로 정정하였으며, v1 QA Warning 2건도 해소하였다. 그러나 PLAN 본문 자체에 "7개 서브 명령" 표현이 5개소에 잔존하여(N-1, N-4, N-5, §2.1, M-40/Step 14), §4 일관성 테스트 목표와 자기모순을 일으킨다. 이 항목들을 "9개"로 수정하거나 EXECUTE 워커에게 §3 Step 1/2를 우선 기준으로 삼는다는 노트를 추가한 뒤 EXECUTE를 진행하는 것을 권장한다. G-7 `status --set blocked` 허용/거부 결정도 착수 전 한 줄로 명확히 하는 것을 권장하나, 이 두 항목은 EXECUTE 완전 차단 수준은 아니다.

---

## 6. TASK.md 체크리스트 갱신

**갱신 없음** — v1 QA에서 F-18을 `[x]` 처리. v2 보강에서 추가로 갱신 가능한 항목 없음 (모든 신규 설계는 EXECUTE 구현이 AC 조건).
