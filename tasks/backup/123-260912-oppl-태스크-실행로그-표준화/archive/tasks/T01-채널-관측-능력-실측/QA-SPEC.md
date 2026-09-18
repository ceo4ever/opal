# QA-SPEC: T01 G 게이트 (구현 전 명세 리뷰)

- 판정 주체: opal-evaluator (opal-agent 채널, `--provider claude --model opus --allowed-tools Read,Grep,Glob --json`, readonly)
- 생성자 세션과 분리된 별도 세션(H-9 생성자≠평가자 유지) — evaluator session_id `fd309e7f-79cf-4989-b346-d8d778652095`
- 산출 시각(UTC): 2026-09-12T10:41:16Z
- 실행 증거: `.oppl-run/g.events.jsonl` (raw), `.oppl-run/g.probe.json` (계측), `.oppl-run/g.exitcode` = 0
- opal-agent 보고 duration_ms: 127879 / is_error: False

## verdict: fail (1회차) → 재작업 지시 7건

아래는 Evaluator 반환 원문이다. 요약·재서술하지 않고 그대로 보존한다.

---

읽기 전용 판정만 수행했고, 어떤 파일도 수정하지 않았다.

## verdict: **fail**

### 1. AC 충족 가능성

**AC-1 — 미달.** `receipt_sha256`의 원천이 설계에 없다.
- CONTRACT §1.5는 self-test receipt를 8필드(`receipt_version`/`channel_id`/`adapter_id`/`adapter_sha256`/`observed`/`claimed_profile`/`evidence`/`produced_at`) 산출물로 정의하는데(CONTRACT.md:211-220), PLAN은 `PLAN.md:65`에서 `observed{}`를 "대입한다"고만 하고 receipt를 **파일로 산출하지 않는다**.
- `PLAN.md:86-91` 산출물 목록에 receipt 파일이 없다. 따라서 `PLAN.md:72`의 `receipt_sha256`은 무엇의 해시인지 정의되지 않았고, VS-1(`PLAN.md:78`)은 `non-null`만 보므로 임의값도 통과한다.

**AC-2 — 미달.** 등급 판정이 관측 원본이 아니라 **파일 존재 여부**에 묶여 있다.
- `PLAN.md:62`: `observed.start = (1)칸이 관측됨(비공백 evidence_path 존재)`.
- 그런데 `PLAN.md:52`의 칸 스키마는 `note`를 "관측 근거 **또는 관측 불가 사유**"로 허용한다 — 관측 실패를 적은 메모 파일도 비공백 경로이므로 `observed.start=true`가 된다.
- VS-2(`PLAN.md:79`)의 판정도 "존재·0바이트 초과"뿐이라 이 경로를 막지 못한다. R-21("프롬프트 준수율만으로 강제 모드를 켜지 않는다", PRD.md:122)과 같은 종류의 약한 근거 문제다.

**AC-3 — 충족.** `PLAN.md:9`가 TRD D-6(TRD.md:53 "한쪽 결과를 다른 쪽에 전용하지 않는다")을 그대로 승계하고, §1 축 A/B와 §3의 축별 파생이 분리돼 있다.

### 2. §3 등급 파생 vs CONTRACT §1.5 — **일치**

`PLAN.md:67-69`의 3분기가 CONTRACT.md:222("셋 다 참이면 `observed_trajectory`, start·terminal만 참이면 `observed_terminal`, 그 외 `cooperative`")와 정확히 대응한다. `PLAN.md:70`이 `monotonic_span`을 enum 파생에서 제외하고 `mode=active` 채택 불가 사실만 별도 기록하는 것도 CONTRACT.md:203(두 active 등급 공통 조건 `duration_source=adapter_monotonic`)과 정합한다.

### 3. `adapter_id`/`adapter_sha256` 충돌 여부 — **충돌 아님, 단 조건이 PLAN에 미기재**

- CONTRACT.md:252-253은 `completion_profile ≠ cooperative`면 두 hash를 필수로 요구하고, CONTRACT.md:265는 "배정값 변경은 계약 개정이 아니라 **재스파이크**"라고 이미 종결 조항을 둔다. PRD.md:143("변환기 구현은 범위 밖")과의 충돌은 **파일이 배포·소비되지 않는 한** 발생하지 않는다.
- 계약 위반이 아닌 처리: `profiles.json`을 태스크 폴더 원본으로만 두고 `state-tool init --run-log-mode active`가 읽는 배포 위치로 승격하지 않는 것. `PLAN.md:91,99`가 이미 승격을 범위 밖으로 두고 있으므로 현재 설계는 위반이 아니다.
- 다만 `PLAN.md:72`는 "Phase 0 실측 probe를 잠정 변환기로 채택"만 적고 **그것이 허용되는 조건(미승격·Phase 1A 실변환기 확정 시 재발급 필수)을 계약 조항으로 묶지 않았다**. 이대로 배포되면 CONTRACT.md:357 `profile_receipt_mismatch`가 확정적으로 발생한다.

### 4. 등급 인플레이션 여지 — **있다**

- 위 AC-2 지적(`PLAN.md:62` 경로 존재 = 관측)이 1차 경로다.
- VS-3(`PLAN.md:80`)이 "(1)~(3) 중 비어 있지 않은 칸을 **최소 하나** 뒷받침"만 요구해, 칸별 근거 검증 없이 3칸이 함께 승인될 수 있다.
- 반면 `PLAN.md:18`(축 A 단조 구간 "미확인 — 확보 불가로 판정될 수 있다")과 `PLAN.md:32`(기존 산출물 무검증 승격 금지)는 인플레이션을 적극 억제하는 좋은 조항이다.

### 5. 범위 밖 침범 — **없음**

`PLAN.md:5`와 `PLAN.md:93-99`가 `opal/`, `~/.opal/`, 3-SSOT, `CONTRACT.md`를 모두 범위 밖으로 명시한다. `PLAN.md:20`의 `~/.claude/projects/` 접근은 read-only 선언이 있다.
- 단 `PLAN.md:25`의 `opal-agent` 실호출은 **파일을 쓸 수 있는 서브에이전트를 실제로 기동**하는데, PLAN에 그 실행의 프롬프트·작업 디렉터리 제약이 없다. 침범 지시는 아니나 침범 가능 통로다.

---

## 재작업 지시

1. **§5 산출물에 self-test receipt 파일을 추가하라.** 축별 `evidence/<axis>/self-test-receipt.json`을 CONTRACT §1.5의 8필드로 정의하고, `profiles.json.receipt_sha256`은 "그 파일 바이트의 SHA-256"으로 명시하라.
2. **VS-1에 receipt 검증을 추가하라.** receipt 8필드 존재 + `claimed_profile`이 `observed{}` 파생과 일치 + `receipt_sha256`이 receipt 파일 실제 해시와 일치(non-null 검사로 대체 금지).
3. **§3-1의 관측 판정 근거를 바꿔라.** `observed.X = (칸의 observed 필드가 true) ∧ (evidence_path가 그 관측을 실제로 담은 원본) ∧ (관측 불가 note가 아님)`으로 정의하고, VS-2를 "존재·비공백"에서 "칸이 주장하는 관측 항목이 그 파일 안에서 확인됨"으로 강화하라.
4. **VS-3을 칸 단위로 바꿔라.** "(1)~(3) 중 하나"가 아니라, `observed=true`로 선언된 **모든 칸**이 각자의 `evidence_path`로 뒷받침됨을 판정하라.
5. **§3-6에 잠정 변환기 채택 조건을 명문화하라.** (a) 이 `profiles.json`은 태스크 폴더 원본이며 배포 위치로 승격하지 않는다, (b) 승격 전 `state-tool init --run-log-mode active`를 호출하지 않는다, (c) Phase 1A 실변환기 확정 시 `adapter_id`/`adapter_sha256`/`receipt_sha256`을 재발급한다 — 세 줄을 §3-6 또는 §5에 조항으로 넣어라.
6. **§1 축 B에 probe 실행 안전 제약을 추가하라.** `opal-agent` 실호출의 작업 디렉터리·프롬프트를 무변경(읽기/에코 수준)으로 고정하고, 실행 후 `git status`로 워크트리 무변경을 확인하는 항목을 VS-4에 넣어라.
7. **`evidence_paths` 상대 경로의 기준점을 확정하라.** CONTRACT §1.6은 "상대 경로만"이라고만 하므로(CONTRACT.md:254), PLAN이 태스크 폴더 기준인지 프로젝트 루트 기준인지 한 줄로 고정하고 VS-2의 해석 규칙을 거기에 맞춰라.

---

## 루프 액션 에이전트 처리

- verdict fail → T3(구현/실측 확정) 진입을 금지하고 T1 재작업(생성자 warm resume)으로 되돌린다.
- 순서 evidence: 이 QA-SPEC.md 산출 시각 < `profiles.json` 산출 시각 (검증 2원화 순서 불변).
