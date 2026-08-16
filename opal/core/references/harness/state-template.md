# STATE.md 공통 템플릿

> 출처: opal-harness.md §3
> 로드 시점: TASK 단계에서 STATE.md 초기 생성 시
> 역할: STATE.md 저널 템플릿 + 파이프라인 행 구성 규칙(`state.json` `rows[]`) + 산출물 행 규칙

---

> **[MUST] STATE.md를 LLM이 직접 작성하는 것은 금지된다. 반드시 `state init` 호출로 생성해야 한다.**
>
> **기본값: `semi-agentic`.** 소유자가 `--interactive` 또는 `--agentic`을 명시 호출하지 않으면 자동 적용된다.
>
> ```bash
> ~/.opal/tools/state-tool/run.sh init <task-path> \
>   --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> \
>   --mode <interactive|semi-agentic|agentic> \
>   [--task-title <태스크 제목>] \
>   [--next-action <첫 액션 텍스트>]
> ```
>
> - `--task-title`: STATE.md 1행 제목. 생략 시 `<task-path>` 마지막 디렉토리명 그대로 사용
> - `--next-action`: `state.json` `next_action` 필드 초기값(조회: `state-tool show`). 생략 시 기본값 `"PLAN 단계 진입"` (TASK 단계가 첫 단계면 `"TASK 단계 진행"`)
>
> **STATE.md는 저널이다 (094 R-6)**: `state init`은 파이프라인 현황판 표·마커를 STATE.md에 렌더하지 않는다. 파이프라인 현황(행 상태·진행·`current_status`·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 일원화된다. STATE.md에는 **의사결정 로그·블로커**만 자동 생성된다.
>
> **저널 골격 자동 생성**:
> `state init` 실행 시 아래 2개 섹션을 자동 생성한다. 이후 갱신 명령은 `## 의사결정 로그`에만 자동 추가하고, `## 블로커`는 PM이 수동 갱신한다(state-tool 범위 밖 — `block` 명령은 `state.json` 행 상태만 갱신).
>
> | 섹션 | 초기 생성 내용 |
> |------|-------------|
> | `## 의사결정 로그` | 빈 표 (`| # \| 시점 \| 결정 \| 근거 \|` + 헤더 구분선) |
> | `## 블로커` | `없음` |
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-8 / `PLAN.md` §2.11 G-8 / §2.19.1 / §1.5 M-2 / 094 §3.1.2

---

### STATE.md 공통 템플릿

> **출력 형식 참조용** — 아래 템플릿은 `state init`이 생성하는 STATE.md의 구조를 보여준다(`_build_new_state_md`, 094 §3.1.2 (1)). 워커가 state-tool 출력 형식을 검증할 때 참조한다. LLM이 이 템플릿을 직접 복사하여 STATE.md를 작성하는 것은 금지된다.

STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(모드·단계 목록·행 상태·다음 액션)은 STATE.md에 렌더되지 않으며, `state.json`이 SSOT다 — 조회는 `~/.opal/tools/state-tool/run.sh show <task-path>`로 한다.

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음
```

> 위 코드펜스는 `state init` 직후 실산출 STATE.md의 **섹션 헤딩 시퀀스**(`# STATE: ...` → `## 의사결정 로그` → `## 블로커`)와 정확히 일치한다(S-31 drift 대조 기준). `state.json`의 `rows[]` 구성 규칙(아래 **파이프라인 행 구성 규칙**)과 산출물 행 규칙은 이 템플릿 교체와 무관하게 계속 유효하다 — `rows[]`는 STATE.md에 렌더되는 표가 아니라 `state.json`에 영속되는 SSOT이기 때문이다.

**파이프라인 행 구성 규칙** (`state.json` `rows[]` — STATE.md에 렌더되지 않음):
- TASK 단계: `작업`, `사용자 확인` (Gate 없음. TASK.md 생성은 `작업` 행에 흡수)
- 일반 단계(PLAN/EXECUTE 등): `작업`, `PM Gate`, `사용자 확인` 순
  - 산출물 생성(PLAN.md 등)은 `작업` 행에 흡수한다 — 별도 산출물 생성 행을 두지 않는다.
  - 문서 QA(요구사항→설계 검토)는 PM Gate가 직접 흡수한다 — 별도 `QA Gate` 행/QA 산출물 행을 두지 않는다 (`harness/pm-review-gate.md` §문서 QA 검증 참조).
  - state 기록은 행 mark 자체로 이뤄진다 — 별도 `State Gate` 행을 두지 않는다 (단계 건너뛰기는 state-tool stage-transition guard가 차단).
- CLOSE 단계: 모든 파이프라인의 마지막 단계. `DONE.md 생성` (1행). Gate 없음. 사용자 확인 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할.
- Gate가 없는 단계(opp TASK 등)는 PM Gate 행 생략
- EXECUTE 단계(코드 변경)는 산출물 행 없음 — `작업` 행에 흡수
- 파이프라인 행 구성의 SSOT는 각 pilot의 `references/pipeline.json` `task_steps[]`이다 — 오케스트레이터 SKILL.md에 행 예시를 중복 게재하지 않는다 (091).

> **CLOSE 진입 게이트**: 사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다.

**산출물 행 규칙**:
1. 산출물 생성은 `작업` 행에 흡수한다 — 별도 산출물 생성 행을 두지 않는다. 워커가 산출물(PLAN.md 등)을 생성한 뒤 PM이 파일 존재·내용을 확인하고 `작업` 행을 ✅ 처리한다.
2. DONE.md 행: CLOSE 단계의 (유일) 행에 위치

> **레거시 호환 (CLOSE 단계)**: 기존 STATE.md(CLOSE 단계 도입 전 생성)는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다. 기존 STATE.md의 "최종 단계에 부착된 마감 블록"은 레거시 구조로 유효하다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.8 | 2026-08-16 13:19 | **템플릿 전면 교체(094 R-6)** — `[MUST]` 블록에서 마커 형식 명세(T-6) + 자유 텍스트 3섹션(의사결정 로그/블로커/다음 액션) 자동 생성 서술을 삭제하고, 2섹션(의사결정 로그·블로커) 저널 골격 자동 생성으로 재작성. 본문 템플릿 코드펜스에서 `## 현재 상태`(모드/단계/진행/상태 4줄) + `<!-- pipeline:start/end -->` 마커 + 표 + `## 다음 액션` 섹션을 전부 삭제 — 신형 템플릿은 제목·`> 최종 갱신:`·SSOT 안내 2줄·`## 의사결정 로그`·`## 블로커`만 포함하며, `state init` 실산출 STATE.md의 헤딩 시퀀스와 일치함을 명시(S-31). **파이프라인 행 구성 규칙·산출물 행 규칙은 `state.json` `rows[]` SSOT로 존치**(표 렌더와 무관하므로 무변경) (094) |
| v1.0 | 2026-04-12 | 최초 작성 — opal-harness.md §3에서 분리 (111) |
| v1.1 | 2026-04-15 | CLOSE 단계 공통 블록 규칙 추가 + 최종 단계 예외 규칙 제거 + CLOSE 진입 게이트 원칙 반영 + DONE.md 행 규칙을 CLOSE 귀속으로 변경 + 레거시 호환 원칙 추가 (121) |
| v1.2 | 2026-05-01 | `[MUST] LLM 직접 작성 금지 — state init 호출` 블록 추가. 마커 형식 명세(T-6). 자유 텍스트 3개 섹션 자동 생성 명세(§2.11 G-8). 기존 템플릿 본문은 출력 형식 참조용으로 보존 + 마커 주입 — TASK F-8 / PLAN §2.11 G-8 / §2.19.1 / §1.5 M-2 (134) |
| v1.3 | 2026-05-09 11:22 | --mode choices에 semi-agentic 추가 + 기본값 안내 추가 + 모드 필드 3-way 값 안내 (140) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "캡틴이" → "소유자가" 치환 (139) |
| v1.5 | 2026-06-07 | 행 구성 규칙·산출물 행 규칙을 새 STATE 구조로 정합화 — 일반 단계 행을 `작업/PM Gate/사용자 확인`으로 축소(QA Gate·QA 산출물·State Gate 행 제거: 문서 QA는 PM Gate 흡수, state 기록은 행 mark 자체, 단계 건너뛰기는 stage-transition guard). 산출물 생성은 작업 행에 흡수. CLOSE를 `DONE.md 생성` 1행으로 갱신. 동작 검증(TEST/verify) 영역 불변 (014 Phase 4-2) |
| v1.6 | 2026-07-23 12:09 | "다음 액션은 PM 수동 갱신" 설계 반전 — `advance`/`mark` 시 파이프라인 프론티어에서 자동 파생·갱신(첫 줄만 치환, 하위 자유 기재 보존), `init`/전이 `--next-action` 오버라이드(비지속). `## 블로커`는 기존대로 PM 수동 갱신 유지 (072) |
| v1.7 | 2026-08-14 08:38 | 파이프라인 현황판 행 예시 SSOT를 오케스트레이터 SKILL.md에서 각 pilot `references/pipeline.json` `task_steps[]`로 이전 — SKILL.md 행 예시 중복 게재 금지 명문화 (091) |
