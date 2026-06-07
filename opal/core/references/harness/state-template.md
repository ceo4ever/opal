# STATE.md 공통 템플릿

> 출처: opal-harness.md §3
> 로드 시점: TASK 단계에서 STATE.md 초기 생성 시
> 역할: STATE.md 공통 템플릿 + 파이프라인 현황판 행 구성 규칙 + 산출물 행 규칙

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
> - `--next-action`: `## 다음 액션` 섹션 초기값. 생략 시 기본값 `"PLAN 단계 진입"` (TASK 단계가 첫 단계면 `"TASK 단계 진행"`)
>
> **마커 형식 (T-6)**: `state init`은 STATE.md의 파이프라인 현황판 표 영역을 아래 HTML 주석 마커로 감싼다.
> ```
> <!-- pipeline:start -->
> ## 파이프라인 현황판
> ...
> <!-- pipeline:end -->
> ```
> 마커가 손실되면 갱신 명령이 `marker_missing` 에러로 거부된다 (`PLAN §2.18 #2`). `show` 명령만 fallback 출력으로 우회.
>
> **자유 텍스트 3개 섹션 자동 생성 (§2.11 G-8)**:
> `state init` 실행 시 아래 3개 섹션을 자동 생성한다. 이후 갱신 명령은 `## 의사결정 로그`에만 자동 추가 (§2.17), `## 블로커`와 `## 다음 액션`은 PM이 수동 갱신 (state-tool 범위 밖).
>
> | 섹션 | 초기 생성 내용 |
> |------|-------------|
> | `## 의사결정 로그` | 빈 표 (`| # \| 시점 \| 결정 \| 근거 \|` + 헤더 구분선) |
> | `## 블로커` | `없음` |
> | `## 다음 액션` | `--next-action` 인자 값 또는 기본값 |
>
> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` F-8 / `PLAN.md` §2.11 G-8 / §2.19.1 / §1.5 M-2

---

### STATE.md 공통 템플릿

> **출력 형식 참조용** — 아래 템플릿은 `state init`이 생성하는 STATE.md의 구조를 보여준다. 워커가 state-tool 출력 형식을 검증할 때 참조한다. LLM이 이 템플릿을 직접 복사하여 STATE.md를 작성하는 것은 금지된다.

각 opal-pilot는 이 템플릿의 `{모드}`, `{단계 목록}`, `{파이프라인 현황판 행 목록}`을 도메인에 맞게 치환한다.

```markdown
# STATE: {태스크 제목}

> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: {모드}  (값: `interactive` / `semi-agentic` / `agentic` 중 하나)
- 단계: {단계 목록}
- 진행: {Step N/M 완료 (EXECUTE 시)}
- 상태: {진행 중 / 완료 / 블로커 / 추가작업중 / 추가작업완료}

<!-- pipeline:start -->
## 파이프라인 현황판

> 상태값: ⬜ 대기 / 🔄 진행 중 / ✅ 완료 / ❌ 실패 / - 해당 없음
> **수행 원칙**: 위에서 아래로 순서대로 처리한다. 현재 행이 ✅가 아니면 다음 행으로 진행 불가.

| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
{파이프라인 현황판 행 목록}
<!-- pipeline:end -->

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음

## 다음 액션
{--next-action 인자 또는 기본값 "PLAN 단계 진입"}
```

**파이프라인 현황판 행 구성 규칙**:
- TASK 단계: `작업`, `사용자 확인` (Gate 없음. TASK.md 생성은 `작업` 행에 흡수)
- 일반 단계(PLAN/EXECUTE 등): `작업`, `PM Gate`, `사용자 확인` 순
  - 산출물 생성(PLAN.md 등)은 `작업` 행에 흡수한다 — 별도 산출물 생성 행을 두지 않는다.
  - 문서 QA(요구사항→설계 검토)는 PM Gate가 직접 흡수한다 — 별도 `QA Gate` 행/QA 산출물 행을 두지 않는다 (`harness/pm-review-gate.md` §문서 QA 검증 참조).
  - state 기록은 행 mark 자체로 이뤄진다 — 별도 `State Gate` 행을 두지 않는다 (단계 건너뛰기는 state-tool stage-transition guard가 차단).
- CLOSE 단계: 모든 파이프라인의 마지막 단계. `DONE.md 생성` (1행). Gate 없음. 사용자 확인 없음 — 직전 단계의 사용자 확인이 CLOSE 진입 게이트 역할.
- Gate가 없는 단계(opp TASK 등)는 PM Gate 행 생략
- EXECUTE 단계(코드 변경)는 산출물 행 없음 — `작업` 행에 흡수
- 오케스트레이터 SKILL.md "STATE.md 도메인 치환값"에 해당 스킬의 파이프라인 현황판 행 예시가 명시됨

> **CLOSE 진입 게이트**: 사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가. 이 규칙은 agentic 모드에서도 유지된다.

**산출물 행 규칙**:
1. 산출물 생성은 `작업` 행에 흡수한다 — 별도 산출물 생성 행을 두지 않는다. 워커가 산출물(PLAN.md 등)을 생성한 뒤 PM이 파일 존재·내용을 확인하고 `작업` 행을 ✅ 처리한다.
2. DONE.md 행: CLOSE 단계의 (유일) 행에 위치

> **레거시 호환 (CLOSE 단계)**: 기존 STATE.md(CLOSE 단계 도입 전 생성)는 소급 변경하지 않는다. 신규 태스크부터 CLOSE 단계를 반영한다. 기존 STATE.md의 "최종 단계에 부착된 마감 블록"은 레거시 구조로 유효하다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-12 | 최초 작성 — opal-harness.md §3에서 분리 (111) |
| v1.1 | 2026-04-15 | CLOSE 단계 공통 블록 규칙 추가 + 최종 단계 예외 규칙 제거 + CLOSE 진입 게이트 원칙 반영 + DONE.md 행 규칙을 CLOSE 귀속으로 변경 + 레거시 호환 원칙 추가 (121) |
| v1.2 | 2026-05-01 | `[MUST] LLM 직접 작성 금지 — state init 호출` 블록 추가. 마커 형식 명세(T-6). 자유 텍스트 3개 섹션 자동 생성 명세(§2.11 G-8). 기존 템플릿 본문은 출력 형식 참조용으로 보존 + 마커 주입 — TASK F-8 / PLAN §2.11 G-8 / §2.19.1 / §1.5 M-2 (134) |
| v1.3 | 2026-05-09 11:22 | --mode choices에 semi-agentic 추가 + 기본값 안내 추가 + 모드 필드 3-way 값 안내 (140) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "캡틴이" → "소유자가" 치환 (139) |
| v1.5 | 2026-06-07 | 행 구성 규칙·산출물 행 규칙을 새 STATE 구조로 정합화 — 일반 단계 행을 `작업/PM Gate/사용자 확인`으로 축소(QA Gate·QA 산출물·State Gate 행 제거: 문서 QA는 PM Gate 흡수, state 기록은 행 mark 자체, 단계 건너뛰기는 stage-transition guard). 산출물 생성은 작업 행에 흡수. CLOSE를 `DONE.md 생성` 1행으로 갱신. 동작 검증(TEST/verify) 영역 불변 (014 Phase 4-2) |
