# SCENARIO GATE 1 — 목표-커버 루브릭 판단축 채점

> 실행 일시: 2026-08-15T15:36:54+0900 | phase: `scenario-rubric` | iteration: 1
> 판정 주체: opal-evaluator-agent (판단축 ①⑤⑥ 전담)
> scenario_source: `/Volumes/Data/AiStudio/workspace/opal/tasks/092-260815-opd-워크트리-작업공간-분리/TEST-SCENARIO.md` (S-1~S-23)
> 판정 입력(참조): `TASK.md`(F-1~F-9, 완료기준 ①~⑦, C-1~C-9) · `PLAN.md`(F-001~F-009, H-1~H-16, DEC-1~DEC-6, TS-001~TS-08x) · `.scenario-coverage-input.json`
> 규칙 SSOT: `opal/core/references/harness/scenario-gate.md` §2(6축·판정주체 분리) · §5-1(종료조건 임계)
> CONTRACT.md: 부재 (opd 1차 접합) — `scenario-rubric`은 Phase 2 CONTRACT 병합 대상이 아니므로 전용 3축 루브릭만 적용

> **판정 경계 [MUST]**: 결정론축 ②③④(요구·기능·리스크 매핑 커버리지)는 test-tool `scenario-coverage-check`가 exit 0(requirements 9 / features 9 / hypotheses 16 / scenarios 23, `all_covered: true`)으로 이미 판정 완료했다. 본 보고서는 이를 **대신 판정하지 않는다**(scenario-gate.md §2). 아래 지적은 전부 "매핑 표의 불완전"이 아니라 **"있어야 할 시나리오가 애초에 존재하지 않음"**(070 사건 형태)에 관한 것이다.

---

## 1. 판단축별 판정

| 축 | 점수 | 통과선 | 판정 |
|----|------|--------|------|
| ① 목표 달성 | **1** / 2 | ≥1 | 통과선 충족(0점 아님) |
| ⑤ 채택/잔존 | **1** / 2 | ≥1 | 통과선 충족(0점 아님) |
| ⑥ 경계/부정 | **1** / 2 | ≥1 | 통과선 충족(0점 아님) |
| **평균** | **1.00** | ≥1.5 | **미달** |

### ① 목표 달성 — 1점

**목표 문장(TASK §작업 목표)**: "OPAL 태스크 파이프라인에 모드 축과 **직교하는 `--worktree`/`--wt` 축을 신설하여**, 태스크별 코드 작업공간을 `{프로젝트}/.opal-worktrees/task_{NNN}/`에 git worktree로 격리한다."

**가점 근거 — S-23은 부품 동작 확인이 아니라 격리의 실증이다.**
S-23의 기대 결과 3항(①슬롯 092 편집·커밋 시 슬롯 093 `git status --porcelain` 비어 있음 ②두 슬롯이 서로 다른 브랜치를 각각 체크아웃 중 ③메인 작업본이 양쪽 모두에 영향받지 않음)은 "`worktree add`가 exit 0을 반환했다" 수준이 아니라 **간섭 부재라는 목표 속성 자체를 관측**한다. 특히 ③은 TASK §배경이 지목한 실제 통증("브랜치 전환이 진행 중인 다른 태스크를 깨뜨린다")에 1:1 대응한다. 이 점에서 070의 "목표 시나리오 부재"와는 다르다 — 목표 시나리오는 **존재한다**.

**감점 근거 — 목표의 후반부("파이프라인에 축을 신설")가 실행으로 검증되지 않는다.**
목표 문장의 주어는 "worktree-tool이 격리한다"가 아니라 "**OPAL 태스크 파이프라인**이 축을 신설하여 격리한다"이다. 그런데 플래그 입력에서 격리 작업본까지의 접합 경로 — `--wt` 파싱 → `task-process.md` 스텝 4.5 훅 → `worktree-tool create` → `state init --worktree` → 워커 디스패치 코드 루트 주입 — 을 **한 번이라도 실행하는 시나리오가 0건**이다.

- F-004(TASK 후처리 훅)의 §4.1 매핑은 `S-3` 단 1건이며, S-3은 `git diff --stat opal/skills/opal-pilot-*/SKILL.md`다. 즉 **훅의 존재를 diff 부재로 확인**할 뿐 훅을 실행하지 않는다.
- F-006(디스패치 경로 계약)도 매핑이 `S-3`(grep) 1건이다.
- DEC-2 §파이프라인 계층("`create` 실패 시 비차단 계속 + `state.json`에 `worktree` 키 미기록") — PLAN이 명시적으로 확정한 계약인데 대응 시나리오도 가설도 없다.

결과적으로 **훅이 `create`를 아예 호출하지 않도록 잘못 접합되어도 S-1~S-23 전건이 그대로 PASS한다.** 이것이 070이 남긴 결함의 형태다(도구는 만들어졌으나 파이프라인이 그것을 쓰는지 아무도 확인하지 않음).

**운영 계층 관점 보강 필요**: 실환경 S-18(revup)·S-19(mams)는 운영 계층 검증이 맞으나 **단일 슬롯 생성·원복**만 다룬다. "여러 태스크를 동시 수행"이라는 목표의 핵심 주장이 실제 프로젝트에서 확인되는 지점이 없고, 합성 fixture(S-23) 1건에만 의존한다.

→ 목표 시나리오 존재(0점 아님) + 목표의 절반이 문서 검사로만 처리(2점 아님) = **1점**

### ⑤ 채택/잔존 — 1점

**"교체형 아님" 대체 해석 판단 — 타당하다.**
산출물 §4.3 각주("본 태스크는 신규 축 추가이지 구형 대체가 아니므로 '구형 잔존 0' 기준은 적용 대상이 아니다. 다만 '현행 동작 유지'가 잔존 검증 성격을 가지므로 S-1·S-2·S-3으로 커버한다")를 **인정한다.** 가산형 변경에서 잔존축의 의미 있는 대응물은 "구형이 사라졌는가"가 아니라 "**구형 경로가 무손상인가**"이며, S-1(키 미생성) · S-2(STATE.md 바이트 동일) · S-3(pilot 9종 diff 0)은 그 불변식을 정확히 겨눈다. 이 해석은 빈틈이 아니다.

**감점 근거 — "채택" 절반이 얇다.** 잔존은 견고하나, 신설 축이 **실제로 채택되어 동작하는지**를 보는 시나리오가 부족하다.

1. **`--worktree` 지정 경로의 값 정합 미검증.** S-1은 미지정 시 키 부재를, S-2는 유/무 렌더 동일성을 본다. 그러나 지정했을 때 `state.json`의 `worktree` **값이 실제 worktree 경로와 일치하는지**, `state-tool show --format json`으로 되읽어 동일 값이 나오는지는 어느 시나리오도 확인하지 않는다. F-5의 존재 이유가 "워커·PM이 어느 작업본에서 작업 중인지 **도구가 답할 수 있어야 함**"인데, 답이 맞는지를 아무도 묻지 않는다. 값이 `null`이든 빈 문자열이든 S-1·S-2는 통과한다.
2. **`status` 서브명령이 23개 시나리오 전체에서 단 한 번도 호출되지 않는다.** F-2 AC는 "4서브명령이 모두 JSON `{"ok":...}`를 반환"을 요구하고(PLAN TS-012), PLAN §3.2.4는 `status`를 **F-008 CLOSE 안내가 소비하는 명령**으로 설계했다. 소비자(CLOSE 안내)와 공급자(`status`) 양쪽 모두 미검증이다.
3. **CLOSE 정리 안내 게이트 미검증.** §4.1의 F-8 매핑은 S-6~S-10, 즉 `remove` 3중 가드뿐이다. F-8의 나머지 절반인 "opd STEP 6에서 머지 대기 안내를 출력한다"(C-6)에 대응하는 시나리오가 없다.

→ 잔존 대체 해석 타당·커버 견고(0점 아님) + 채택 측 3건 공백(2점 아님) = **1점**

### ⑥ 경계/부정 — 1점

**가점 근거**: 부정 경로 시나리오가 실제로 두텁다 — S-6·S-7·S-8(가드 3종 고유 코드) · S-10(`--force` 우회 기록) · S-12(중간 실패 롤백) · S-13(base-ref 동결 결정론) · S-14(부적합 config 3종) · S-16(비차단 경고). "정상 경로만 있다"와는 거리가 멀다.

**감점 근거 — 설계가 명시적으로 규정한 부정 경로 다수가 통째로 누락되었다.** PLAN §3.2.2 `ERROR_CODES` 카탈로그 17종 중 다음이 어느 시나리오에도 나타나지 않는다.

| 미커버 경로 | 설계 근거 | 왜 중요한가 |
|---|---|---|
| `CONFIG_NOT_FOUND` / `CONFIG_INVALID_JSON` (`worktree.json` 부재·파손) | PLAN TS-005, **F-3 AC (3)항 "`worktree.json` 부재 시 동작"**, §3.3.3 (3) | `--wt`를 쓰는 프로젝트가 **가장 먼저 만나는 실제 상황**이다. 하네스 SSOT가 3대 필수 기재 항목으로 못박은 동작인데 검증이 0건 |
| `WORKTREE_EXISTS` / `BRANCH_EXISTS` (정상 슬롯 중복 생성) | PLAN §3.2.3 pre-flight (1) | S-12는 "롤백 후 재실행이 **막히지 않음**"만 본다. 반대 방향(살아 있는 슬롯에 같은 번호로 재생성 시 **거부되고 기존 슬롯 무손상**)은 미검증. 오작동 시 진행 중인 태스크의 작업본이 훼손된다 |
| `NOT_A_GIT_REPO` pre-flight 거부 | PLAN TS-013 | S-12(TS-014)는 pre-flight **통과 후** 실패 → 롤백 경로다. "아무것도 만들지 않고 거부"(TS-013)는 별개 계약이며 DEC-2 all-or-nothing의 첫 번째 방어선 |
| `repos: []` 빈 배열 | PLAN §3.1.3 검증 순서 4 → `CONFIG_INVALID_TYPE` | S-14는 3종(누락·무효 layout·경로 이탈)만 다룬다. F-1 AC가 요구한 3종 고유 코드는 충족하나 검증 함수의 나머지 분기는 무검증 |
| 심볼릭 링크 `repos[]` | PLAN §3.1.3 `_is_inside()` — "**심볼릭 링크는 해석하지 않는다**(경로 문자열 기준)" | 명시적 설계 결정인데 이를 고정하는 케이스가 없다. 구현자가 `resolve()`로 바꿔도 아무 시나리오가 깨지지 않는다(보안 판정 방향이 뒤집히는 변경) |

권한 오류 경로는 PLAN TS-081(캐시 진단 예외 흡수)에만 존재하고 시나리오 미반영이나, 비차단 경고 계열이라 위 5건보다 우선순위가 낮다.

→ 부정 경로 다수 존재(0점 아님) + 설계 규정 부정 경로 5종 공백(2점 아님) = **1점**

---

## 2. 별도 검토 사항 (감점 사유 아님)

| 항목 | 판정 | 근거 |
|---|---|---|
| §0.2 M2(E2E 자동화) 면제 | **정당** | 트리거 3종 대조가 정확하다 — FE 화면(`dashboard/frontend/` 변경 없음)·인증/인가(토큰·세션·권한 코드 없음)·외부 API(로컬 git subprocess만) 전부 미해당. 변경 영역이 CLI 도구 + 참조 문서 단독이므로 "비즈니스 로직 단독 변경 M2 면제" 조항에 부합. 면제 사유를 표로 명시하고 근거를 단 처리 방식도 적절 |
| S-18·S-19·S-20의 M3(사용자 협업) 배정 | **정당** | 캡틴 작업 환경(revup·mams) 직접 조작 + S-20은 12GB 캐시 이동·셸 프로파일 영속화라는 비가역 변경이다. 자동화 금지가 옳다. 다만 그 결과 **운영 계층 목표 검증이 수동 단일 슬롯 확인에 의존**하게 된 점은 ①축 감점에 반영했다(G-2 참조) |
| §0.1 RED-first 트랙 분기 | 판정 범위 밖 | 본 게이트는 ①⑤⑥ 판단축 전담. 기록만 함 |

---

## 3. gaps — 재작성 지시

> Producer(PM+캡틴)가 반영한다. 본 에이전트는 판정만 수행하며 `TEST-SCENARIO.md`를 직접 수정하지 않는다.

**G-1 [①⑤ 최우선] S-24 신설 — 파이프라인 관통(플래그→훅→도구→state) 시나리오**
계층 L2, M1(pytest 또는 Bash). `task-process.md` 스텝 4.5 절차를 그대로 실행하여 다음 3항을 기대 결과로 둔다.
① `worktree-tool create --project-root {proj_a} --task 092` → `ok:true`이고 응답 `worktree_root`가 `{proj_a}/.opal-worktrees/task_092`와 문자열 일치.
② 그 `worktree_root`를 `state-tool init --worktree <경로>`에 전달 → `state-tool show --format json`의 `data.worktree`가 전달값과 **정확히 동일**.
③ `create`가 `ok:false`(예: `CONFIG_NOT_FOUND`)인 경우 `state init`에 `--worktree`를 전달하지 않아 `state.json`에 `worktree` 키가 **부재**하고 태스크가 중단되지 않음(DEC-2 파이프라인 계층 "성공 후에만 기록" + 비차단 계속).
→ 현재 F-004 훅과 DEC-2 파이프라인 정책은 S-3의 `git diff` 외에 어떤 검증도 받지 않으며, 훅이 `create`를 호출하지 않아도 전 시나리오가 PASS한다.

**G-2 [①] S-18의 기대 결과에 2슬롯 동시성 확인 추가**
현행 S-18은 단일 슬롯 생성·원복만 본다. 기대 결과에 "`create --task 092` 후 `create --task 093`으로 슬롯 2개를 만들고, 슬롯 092에서 파일 1개 편집 시 슬롯 093과 메인 `workspace/`의 `git status`가 불변임을 확인한 뒤 양쪽 `remove`로 원복"을 추가하라. → 목표 주장("여러 태스크 동시 수행")이 실환경에서 한 번도 확인되지 않는 상태를 해소한다.

**G-3 [⑤] S-1·S-2의 기대 결과에 `worktree` 값 정합 추가**
"키 존재"에서 멈추지 말고 ①`state.json`의 `worktree` 값이 `--worktree`로 전달한 절대경로와 문자열 동일 ②`state-tool show --format json`이 동일 값을 반환(`null`·빈 문자열 불가)을 명시하라. → F-5의 목적("도구가 어느 작업본인지 답한다")이 현재 아무 시나리오에서도 검증되지 않는다.

**G-4 [⑤] S-25 신설 — `status` 서브명령 + CLOSE 안내 게이트**
계층 L2, M1. 기대 결과: ①dirty / unpushed / 미머지 각 상태에서 `status`가 `{branch, dirty, unpushed, merged, pending_setup}`을 `remove`와 **동일 판정**으로 보고하되 `ok:true`로 거부하지 않음(PLAN §3.2.4) ②`opal-pilot-dev/SKILL.md` STEP 6에 worktree "머지 대기" 안내 스텝이 존재하고 그 안내가 `status` 출력을 근거로 삼음. → `status`는 23개 시나리오 전체에서 한 번도 호출되지 않으며, F-8의 CLOSE 안내 절반이 무검증이다.

**G-5 [⑥] S-26 신설 — `.opal/worktree.json` 부재·파손**
계층 L2, M1. 기대 결과: ①config 없는 프로젝트에서 `create` → `{"ok":false,"error":"CONFIG_NOT_FOUND"}` ②이때 `.gitignore`·`.opal-worktrees/`가 **생성되지 않음**(부수 효과 0 — PLAN §3.2.3에서 pre-flight가 `ensure_gitignore_entry()`보다 선행하므로) ③깨진 JSON → `CONFIG_INVALID_JSON`. → PLAN TS-005 + F-3 AC (3)항이 규정한 동작인데 시나리오 0건이다.

**G-6 [⑥] S-27 신설 — 살아 있는 슬롯에 동일 태스크 번호 재생성**
계층 L2, M1. 기대 결과: `create --task 092` 성공 후 동일 인자로 재실행 → `WORKTREE_EXISTS`(또는 브랜치 선점 시 `BRANCH_EXISTS`) 거부 + **기존 슬롯의 worktree 디렉토리·브랜치·`.meta/task_092.json`이 전부 무손상**. → S-12는 롤백 후 재실행이 막히지 않는 방향만 보며, 반대 방향(중복 거부 + 기존 슬롯 보호)이 비어 있다.

**G-7 [⑥] S-14의 조건에 부적합 3종 추가**
현행 3종(키 누락·`layout` 무효·경로 이탈)에 다음을 추가하라. ①`repos: []` 빈 배열 → `CONFIG_INVALID_TYPE`(PLAN §3.1.3 검증 순서 4) ②`repos[1]`이 `.git` 없는 디렉토리인 유형 A fixture로 `create` → pre-flight `NOT_A_GIT_REPO` 거부 + **worktree 0개·브랜치 0개**(PLAN TS-013 — S-12의 롤백 경로와 별개 계약) ③`repos[0]`이 프로젝트 밖을 가리키는 심볼릭 링크 → PLAN §3.1.3 `_is_inside()`의 "심볼릭 링크를 해석하지 않는다(경로 문자열 기준)"는 명시적 결정대로 **통과**함을 고정. ③은 구현자가 `resolve()`로 바꾸면 보안 판정 방향이 뒤집히는 지점이므로 시나리오로 못박아야 한다.

---

## 4. 결과 계약

```json
{
  "scores": {"goal": 1, "adoption": 1, "boundary": 1},
  "average": 1.0,
  "gaps": [
    "G-1 [goal/adoption] S-24 신설 — 파이프라인 관통(--wt→task-process 스텝 4.5 훅→worktree-tool create→state-tool init --worktree) 실행 검증. 기대결과 3항: create ok:true + worktree_root 경로 일치 / state show --format json의 data.worktree가 전달값과 동일 / create 실패 시 --worktree 미전달로 worktree 키 부재 + 태스크 비중단(DEC-2 파이프라인 계층). 현재 F-004 훅과 DEC-2 파이프라인 정책은 S-3의 git diff 외 무검증이며, 훅이 create를 호출하지 않아도 전 시나리오가 PASS한다.",
    "G-2 [goal] S-18의 기대 결과에 2슬롯 동시성 추가 — create --task 092 후 --task 093으로 슬롯 2개 생성, 092 편집 시 093과 메인 workspace의 git status 불변 확인 후 양쪽 remove 원복. 목표 주장('여러 태스크 동시 수행')이 실환경에서 미확인 상태다.",
    "G-3 [adoption] S-1·S-2의 기대 결과에 값 정합 추가 — state.json의 worktree 값이 --worktree 전달 절대경로와 문자열 동일하고, state-tool show --format json이 동일 값을 반환(null·빈 문자열 불가). 현재 '키 존재'만 보므로 값이 null이어도 통과한다.",
    "G-4 [adoption] S-25 신설 — status 서브명령 + CLOSE 안내 게이트. dirty/unpushed/미머지 각 상태에서 status가 {branch,dirty,unpushed,merged,pending_setup}을 remove와 동일 판정으로 보고하되 ok:true로 거부하지 않음 + opd SKILL.md STEP 6의 '머지 대기' 안내가 status 출력을 근거로 함. status는 23개 시나리오에서 한 번도 호출되지 않는다.",
    "G-5 [boundary] S-26 신설 — .opal/worktree.json 부재 시 create가 CONFIG_NOT_FOUND 반환 + .gitignore·.opal-worktrees/ 미생성(부수효과 0), 깨진 JSON은 CONFIG_INVALID_JSON. PLAN TS-005 + F-3 AC (3)항이 규정한 동작인데 시나리오 0건이다.",
    "G-6 [boundary] S-27 신설 — 살아 있는 슬롯에 동일 태스크 번호로 create 재실행 시 WORKTREE_EXISTS/BRANCH_EXISTS 거부 + 기존 worktree·브랜치·.meta/task_092.json 무손상. S-12는 '롤백 후 재실행이 막히지 않음'만 보며 반대 방향이 비어 있다.",
    "G-7 [boundary] S-14의 조건에 3종 추가 — (1) repos:[] 빈 배열 → CONFIG_INVALID_TYPE (2) repos[1]이 .git 없는 디렉토리 → pre-flight NOT_A_GIT_REPO 거부 + worktree 0개·브랜치 0개(PLAN TS-013, S-12 롤백 경로와 별개) (3) repos[0]이 프로젝트 밖 심볼릭 링크 → PLAN §3.1.3 _is_inside()의 '심볼릭 링크 미해석' 결정대로 통과함을 고정."
  ],
  "verdict": "fail"
}
```

**종합 verdict: `fail`** — 세 판단축 모두 통과선(≥1점)은 충족하여 0점 축은 없으나, 평균 1.00이 `scenario-gate.md` §5-1 수렴 임계(평균 ≥1.5)에 미달한다. 재작성 후 iteration 2로 재채점한다.

---

## 변경이력

| 버전 | 일시 | 내용 |
|------|------|------|
| v1.0 | 2026-08-15T15:36:54+0900 | iteration 1 채점 — goal 1 / adoption 1 / boundary 1, 평균 1.00, verdict fail, gaps 7건 |
