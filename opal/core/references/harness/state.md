# State (상태 관리)

> 출처: opal/core/references/opal-harness.md §3
> 로드 시점: TASK 단계 시작 시 / EXECUTE Step 진행 시 / PM Gate 직전 상태 자가 점검 시
> 역할: STATE.md 이벤트 테이블 / 상태 전이 흐름 / 상태 자가 점검 / 세션 복원

---

### STATE.md 기본 구조

오케스트레이터 전용. 단계 스킬은 STATE.md를 갱신하지 않는다 (EXECUTE Step 진행 제외).

> **[강제]** 아래 각 이벤트 발생 시 STATE.md 갱신은 **필수**다. 갱신 미수행 시 다음 단계 진입이 금지된다. 행 mark 자체가 state 기록이며, 단계 건너뛰기·순서 위반은 state-tool stage-transition guard가 차단한다. PM은 PM Gate 직전에 상태 자가 점검(아래 §상태 자가 점검)으로 갱신 여부를 확인한다.

> **[MUST] 파이프라인 행 상태 변경은 `state-tool`로만 수행한다. LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다.**
>
> 호출 형식: `~/.opal/tools/state-tool/run.sh <command> <task-path> [options]`
>
> 위반 시 도구가 거부하며 에러 코드를 반환한다. 주요 에러:
> `marker_missing`(STATE.md 마커 누락) / `worker_scope_violation`(워커 권한 초과) / `state_not_initialized`(state.json 미존재)
> — 전체 에러 카탈로그 23종: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.18
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-7 / `PLAN.md` §2.11 G-6 / §1.5 M-1

| 이벤트 | 갱신 주체 | 파이프라인 현황판 행 갱신 | 상태: 필드 | 강제 여부 | 갱신 명령 |
|--------|----------|--------------------|-----------|----------|---------|
| TASK 완료 | 오케스트레이터 | STATE.md 초기 생성 + 파이프라인 현황판 행 구성 | 진행 중 | **필수** | `~/.opal/tools/state-tool/run.sh init <task-path> --skill <약어> --mode <모드>` |
| 단계 시작 | 오케스트레이터 | 해당 단계 작업 행 → 🔄 | 진행 중 | **필수** | `~/.opal/tools/state-tool/run.sh advance <task-path> --row <N>` |
| 단계 완료(작업) | 워커(1차) + PM(확인) | 해당 단계 작업 행 → ✅ (산출물 생성은 작업 행에 흡수) | - | **필수** | `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done` |
| PM Gate 통과 (문서검증 포함) | PM | PM Gate 행 → ✅ | - | **필수** | `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done` |
| 사용자 확인 완료 | PM | 사용자 확인 행 → ✅ | 완료 (직전 단계가 CLOSE 진입 게이트인 경우) | **필수** | `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done --owner user` |
| EXECUTE Step 완료 | 워커(1차) + PM(확인) | - | 진행: Step N/M | **필수** | `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done --as-worker --worker-stage EXECUTE --step <N/M>` |
| 블로커 | 워커 | 해당 행 → ❌ | 블로커 | **필수** | `~/.opal/tools/state-tool/run.sh block <task-path> --row <N> --reason <text>` |
| 태스크 완료 | 오케스트레이터 | CLOSE 단계 `DONE.md 생성` 행 → ✅ | 완료 (CLOSE 단계 완료 시 발생) | **필수** | `~/.opal/tools/state-tool/run.sh mark <task-path> --row <N> --done` |
| 추가작업 진입 | 오케스트레이터 | - | 추가작업중 (CLOSE 단계 재진입) | **필수** | `~/.opal/tools/state-tool/run.sh add-row <task-path> --after <N> --stage <단계> --item <항목>` |
| 추가작업 완료 | 오케스트레이터 | - | 추가작업완료 (CLOSE 재진입 완료) | **필수** | `~/.opal/tools/state-tool/run.sh status <task-path> --set additional_work_done` |

**갱신 모델**: 워커가 1차 갱신을 수행하고(best effort), PM이 PM Gate 직전 상태 자가 점검에서 확인하여 미갱신/오갱신 시 즉시 보완한다. **note 소유자 호칭**: `{owner_name}` 플레이스홀더 사용 시 state-tool이 identity.md `owner_name`으로 치환한다(규칙 상세: `opal/core/AGENT.md` §정체성 적용).

**수행 순서 강제 원칙**: 파이프라인 현황판 테이블은 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가. 일반 단계 행은 `작업 / PM Gate / 사용자 확인`으로 구성된다(문서 QA는 PM Gate가 흡수, 별도 QA Gate·State Gate 행 없음). Gate가 없는 단계(TASK 등)는 PM Gate 행을 생략한다.

**상태: 필드 전이 흐름**:

```
진행 중 → (CLOSE 단계 완료) → 완료
완료 → 추가작업중(CLOSE 재진입) → 추가작업완료
↑________________________추가작업 반복 시___↓
```

### 파이프라인 todo 미러 (네이티브 할일 패널)

> **소유자**: PM. 전 pilot 상속(pilot SKILL.md는 재서술하지 않음). **적용 시점**: state-tool 이벤트(`init`/`advance`/`mark`/`block`) 호출 직후 PostToolUse hook이 결정론 트리거한다.

파이프라인 현황판을 **단계(stage) 단위로**(항목 단위 아님) 네이티브 할일 패널에 비춘다 — 소유자는 STATE.md를 열지 않고도 하단 패널에서 진행 상황을 확인한다.

**메커니즘 (hook 트리거, 산문 지시가 아닌 도구 집행)**: ① state-tool이 이벤트 응답에 단계별 파생 상태 `todo_mirror` 페이로드(`{action, todos[]}`)를 함께 출력(도구가 결정론 산출, PM 재계산 아님) → ② PostToolUse hook(`todo_mirror_hook.py`)이 세션에 주입 → ③ PM이 `action=create`면 `TaskCreate`, `action=update`면 `TaskUpdate`로 기계적으로 릴레이(네이티브 패널은 LLM 도구 호출로만 기록되므로 최종 1스텝은 LLM 몫).

> **[게이트 — 능력 감지]** `TaskCreate`/`TaskUpdate` 등이 노출된 세션(현재 Claude Code)에서만 수행 — 없는 플랫폼(Cursor/Gemini/Codex 등)은 절 전체 스킵. 하드코딩 분기가 아닌 **능력 감지**이며(헌법 Core Stance), hook은 어댑터 계층(`claude-hooks.json`)에만 격리되어 비Claude는 기존 no-op 유지.
> **[SSOT 불변]** STATE.md/state-tool이 유일 SSOT. todo 패널은 읽기 전용 거울이며 충돌 시 STATE.md가 이긴다 — 진행·게이트 판단 근거로 쓰지 않는다.

**미러 규칙**: 대상 = 현황판 행을 `단계`로 그룹핑한 단계당 todo 1개(TASK/PLAN/EXECUTE/TEST/CLOSE 등). 상태 파생(state-tool 집계) = 전부 ✅→`completed` / 하나라도 🔄·일부 ✅→`in_progress` / 전부 ⬜→`pending` / `na` 행은 중립 제외. 갱신은 `init` 직후 state-tool이 출력하는 `todo_mirror`(create)로 시작하고, `advance`/`mark`/`block` 직후 state-tool이 재파생하는 `todo_mirror`(update)마다 state-tool 호출과 1:1 동반한다. 블로커(`block`, ❌)는 `in_progress` 유지(실패 상태 없음, 블로커 자체는 STATE.md·보고로 표면화).

> L2 경량 트랙은 파이프라인·state-tool을 쓰지 않으므로 이 절이 적용되지 않는다(todo 미러 없음).

### STATE.md 공통 템플릿

> **[필수 로드]** TASK 단계에서 STATE.md 초기 생성 시 로드한다.
> 탐색: `harness/state-template.md`
>
> 적용 주체: PM(오케스트레이터)
> 적용 시점: STATE.md 초기 생성 시
> PM Gate 검증: STATE.md가 공통 템플릿 구조를 따르는가

### 추가작업 프로세스

> **[필수 로드]** 태스크 완료 후 추가 수정 필요 시 로드한다.
> 탐색: `harness/additional-work.md`
>
> 적용 주체: PM(오케스트레이터)
> 적용 시점: 태스크 완료 후 추가 수정 감지 시
> PM Gate 검증: ADD_DONE.md 템플릿 준수, 상태 전이가 올바른가

### 세션 복원

새 세션에서 `tasks/{NNN}-{name}/STATE.md`가 존재하면 Read하여 정확한 지점에서 재개한다.

---

### 상태 자가 점검

> **소유자**: PM. 단계 작업 완료 후 PM Gate 직전 수행 — 별도 `State Gate` 행은 두지 않는다(기록은 행 mark 자체, 순서 위반은 state-tool stage-transition guard가 차단). PM Gate 검토에 앞서 STATE.md 갱신 정합성을 확인하는 절차다.

**점검 위치**: 작업(산출물 생성 포함) → **상태 자가 점검** → PM Gate

**자가 점검 프롬프트**: ① `최종 갱신` 타임스탬프가 현재 단계 완료 시점 이후인가 ② `단계` 필드가 현재 완료 단계를 반영하는가 ③ 파이프라인 현황판 테이블의 현재 단계 행 상태값(✅/🔄/⬜)과 `상태:` 필드(진행 중/완료/추가작업중/추가작업완료)가 적절한가

| 확인 결과 | 동작 |
|----------|------|
| 3개 항목 모두 충족 | PM Gate 진입 허용 |
| 1개 이상 미충족 | STATE.md를 즉시 갱신(행 mark) 후 재점검 → PM Gate 진입 |

**차단 규칙**: 이전 단계 상태가 `완료`가 아니면 다음 단계 진입 금지(state-tool stage-transition guard로 강제). 자가 점검 미통과 상태에서 PM Gate·DONE.md 생성 단계로 진입하지 않는다.

**표준 단계 순서**: `워커 완료(산출물 포함) → 상태 자가 점검(하네스 §3, STATE.md 갱신 확인) → PM Gate(문서 QA 흡수)`

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — opal-harness.md §3 분리. 레거시 호환 노트 3건 제외 (128) |
| v1.1 | 2026-05-01 | 갱신 이벤트 표에 "갱신 명령" 컬럼 추가 + `[MUST] state-tool 호출만 허용` 블록 추가 — TASK F-7 / PLAN §2.11 G-6 / §1.5 M-1 (134) |
| v1.2 | 2026-06-07 | QA→PM Gate 통합 + State Gate 행 제거 정합화 — 이벤트 표에서 QA Gate/State Gate/산출물 생성 행 제거(문서 QA는 PM Gate 흡수, 산출물 생성은 작업 행 흡수, state 기록은 행 mark 자체, 단계 건너뛰기는 stage-transition guard). `State Gate` 섹션을 `상태 자가 점검`(PM Gate 직전 PM 절차)으로 재정의. 표준 단계 순서 문구를 `작업→상태 자가 점검→PM Gate`로 갱신. 동작 검증(TEST/verify) 영역 불변 (014 Phase 4-2) |
| v1.3 | 2026-07-10 13:12 | note 소유자 호칭 참조 1줄 추가 — `{owner_name}` 플레이스홀더 사용 안내 + `opal/core/AGENT.md` §정체성 적용(오염 금지) 참조(재서술 금지) (054) |
| v1.4 | 2026-07-16 16:04 | 파이프라인 todo 미러 절 추가 — STATE.md 단계를 네이티브 할일 패널에 단계 단위로 미러(능력 감지 게이트, SSOT 불변 읽기 전용 거울). 전 pilot 상속, state-tool 이벤트와 1:1 동반. L2 미적용 (064) |
| v1.5 | 2026-07-23 17:43 | 파이프라인 todo 미러 hook 강제 정합 — prose 지시 → PostToolUse hook 트리거+state-tool `todo_mirror` 페이로드 방식으로 재서술(SSOT 불변·능력감지 게이트 보존, hook 어댑터 격리 명시), na 중립 파생 명문화, `open`→`pending` 용어 통일, "PM이 직접 재계산" 의존 제거(도구가 결정론 파생) (076) |
| v1.6 | 2026-08-09 21:07 | 중복 서술 압축 — §파이프라인 todo 미러·§상태 자가 점검 산문을 표/불릿 축약 + §갱신 모델/§note 소유자 호칭 병합. `state-tool` 명령 행 전건(11) 보존. 144→118줄 (C1) (087) |
| v1.7 | 2026-08-09 21:24 | Step 10 재측정 C5 Fail 원복 — §파이프라인 todo 미러 §미러 규칙 "갱신" 서술에서 압축 중 누락된 `state-tool` 명시 언급 2건 복원(3→1로 과압축된 것을 되돌림), G3 본문 언급 수를 Step 1 기준선(72) 이상으로 회복. 줄수 증가 없음(118줄 유지), `run.sh` 명령 행 11건 무영향 (087) |
