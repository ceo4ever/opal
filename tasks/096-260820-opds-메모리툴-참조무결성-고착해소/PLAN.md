# PLAN: memory-tool 참조 무결성 검사 + 본문 부재 행 고착 해소

> 작성일: 2026-08-20 08:06 KST | 입력: TASK.md (ANALYSIS.md 없음 — Short Task, 코드 분석 직접 수행)
> 모드: Multi-Feature (F-001~F-004) | 실행 모드: **복잡**
> 실측 기준선: `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` → **163 passed, 25 subtests passed in 18.03s** (2026-08-20 08:0x 실행)

> **개정 v1.1 (재설계 루프 1/2회차, 2026-08-20)** — 목표-커버 게이트 iteration 1 `verdict: fail` + **G-3(P0)** 반영.
> `_resolve_memory_file()`이 `None`을 반환하는 경로에서 §3.2.2 가드가 통과해 **본문 존재 확인 없이 인덱스 행이 삭제**되는 결함을 해소했다.
> 변경 절: §3.1.2·§3.1.5(검출 어휘 2분) / §3.2.2(가드 재설계·ERROR_CODES 2종→**3종**) / §3.3.2(문서 표 2행→3행) / §리스크 가설 표 H-2 / §4.2 Step 3·5 / §4.4·§4.5 수치 정합 / §5.1(QA-024·QA-025 신설) / §5.2 / §9(R-2 갱신, R-13 신설).
> 그 외 절은 무변경 — [MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names."
>
> **개정 v1.2 (재설계 루프 2/2회차, 2026-08-20)** — 게이트 iteration 2 **pass**(2/2/2, gaps 0) 후 채점 외 필수 정정 3건 반영.
> ① §9 R-13 잔존 고착 범위를 코드·전이표와 정합(`모두 거부` → `{active, promoted, candidate} × 해석 불가`) + 성격을 **선재 고착**으로 정정 / ② §4.2 Step 3 완료 기준의 오탐 grep을 함수 범위 한정 결정론 검사로 교체 / ③ **`promote` 어휘 정합 — (가) 범위 내 정정 채택**(§3.2.1·§3.2.2·§3.2.5·§3.3.2·§4.4·§4.5·§5.1·§5.2).
>
> **ID 네임스페이스 [MUST]** — 본 PLAN의 검증 항목 ID는 **`QA-NNN`**이다. `TEST-SCENARIO.md`의 `TS-NNN`과 **번호 공간이 분리**되며 서로 대응하지 않는다(개정 전 PLAN의 `TS-NNN`을 전량 개명).
> 표의 컬럼명은 `TS-ID`로 유지한다 — `opal/skills/op-dev-plan/references/plan-guide.md` §PLAN.md 파싱 규칙이 컬럼명을 `TS-ID`로 못박고 있어(후속 소비자 파서 계약) 컬럼명 변경은 계약 파손이기 때문이다. **값만** 네임스페이스를 갖는다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`memory-tool`은 인덱스 행(`.opal/MEMORY.json`)이 가리키는 본문 `.md`의 실재 여부를 **검출하지 않고**(`build_review_block()` `memory_tool.py:828-870`), 본문이 없는 행은 `promote`의 본문 존재 요구(`:1164-1168`)와 `delete`의 상태 가드(`:1355-1357`)가 조합되어 **어떤 명령으로도 도달할 수 없는 고착 상태**에 빠진다. 본 태스크는 (1) `review`에 참조 무결성 검사를 추가하고, (2) 상태 임의 조작 없는 정식 정리 경로를 열며, (3) 규범 문서의 라이프사이클 표를 스키마 enum 5종과 정합시킨다.

핵심 설계 판단은 두 가드를 **약화하지 않고 술어를 좁히는 것**이다 — 무손실 가드가 보호하는 자산은 "인덱스 행"이 아니라 "본문에 담긴 지식"이므로, 본문이 실재하지 않는 행에 한해 정리를 허용하고 본문이 실재하면 기존 가드를 그대로 유지한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | `review` 참조 무결성 검사 — `violations`에 `memory_file_missing` 추가 | R-1 | P0 | 없음 |
| F-002 | 본문 부재 행 정식 정리 경로 — `delete --orphan --ref` | R-2 | P0 | F-001 (검출 술어 공유) |
| F-003 | 규범·도구 문서 정합 — 라이프사이클 `candidate` 행 + 신설 경로 반영 | R-3 | P1 | F-002 (절차 확정 후) |
| F-004 | RED 증거 + 전건 회귀 + install 재배포 | R-4 | P0 | F-001, F-002, F-003 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ── F-002 ── F-003 ──┐
   │         │            ├── F-004
   └─────────┴────────────┘
              (RED는 F-004의 선행 서브트랙 — Step 1이 F-001·F-002·F-003 전부에 선행)
```

### 1.4 [MUST] 상위 제약 (원문 인용)

- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**변경이력 누락 금지** — 스킬·에이전트·참조 문서 수정 시 변경이력 표 행 추가 의무."
- [MUST] `opal/core/references/harness/memory-learning.md:24`: "메모리(지식)는 **blind 삭제 금지** — 갯수 상한을 두지 않는 대신, 성숙한 지식은 `promote`로 영구 거처(docs/brain)로 졸업한 뒤 삭제하고, 진부화는 `dead`/`superseded` 전이 후 자가검토(`review`)로 정리한다(데이터 무손실)."
- [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." / "No abstractions for single-use code."
- [MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names. Don't improve adjacent code."
- [MUST] `opal/core/PRINCIPLES.md` §4: "Don't fake it: never substitute a mock for a real integration you were asked to build."
- [MUST] `opal/core/references/harness/red-first.md` §1: "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지."
- [MUST] `opal/core/references/harness/red-first.md` §2: "RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다."
- [MUST] `opal/core/references/harness/red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커."
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 \"## 변경이력\" 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §네이밍: "파일/폴더 이름 | English, kebab-case (Python 파일은 snake_case)" — 신규 파일 없으므로 적용 대상 없음(확인 완료).
- [MUST] `docs/CONVENTIONS.md` §@header 규칙: "코드 파일을 생성·수정할 때 파일 상단에 @header 블록을 작성한다" / "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다." → `memory_tool.py` @header `description`·변경이력 라인 갱신 의무.
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다."

---

## 미확정 사항 판정 (TASK.md §미확정 사항 ①②)

> 본 절이 TASK.md가 PLAN에 위임한 2건의 택일 결과다. 각 판정은 **실측 근거 → 채택 → 탈락 사유** 순으로 기재한다.

### 판정 ① — R-2 구현 방식: **(b) `delete` 상태 가드를 "본문 부재 시" 예외로 완화 (명시적 opt-in 플래그 형태)**

#### 실측 — 두 가드의 현재 술어

| 가드 | 위치 | 현재 술어 | 보호 대상 |
|------|------|----------|----------|
| `promote` 본문 존재 요구 | `memory_tool.py:1164-1168` | `_resolve_memory_file(...) is None or not mem_file.exists()` → `memory_file_not_found` | 이전(졸업) 미확인 상태의 무근거 삭제 |
| `delete` 상태 가드 | `memory_tool.py:1355-1357` | `status not in ("dead", "superseded")` → `delete_requires_dead_or_superseded` | **살아있는 지식**의 blind 삭제 (`memory-learning.md:38`) |

#### 채택 근거

**(1) 가드의 보호 자산은 "인덱스 행"이 아니라 "본문 지식"이다.** `memory-learning.md:38`은 가드의 목적을 "살아있는 지식의 blind 삭제를 차단한다"로 명시한다. 본문 `.md`가 실재하지 않으면 이 저장소 안에 삭제될 지식 자체가 없고, 남은 것은 존재하지 않는 경로를 주장하는 **dangling pointer**다. 따라서 본문 부재 조건 하의 정리는 가드의 **완화가 아니라 술어의 정밀화**다 — 가드가 원래 보호하려던 집합을 한 건도 잃지 않는다.

**(2) 본문이 존재하는 행에 대해 기존 가드는 문자 그대로 불변이다.** 채택안은 `--orphan` 플래그를 쓴 경우에만 상태 가드를 우회하며, 그 경로에서 본문이 **실재하면 즉시 거부**한다(신규 코드 `memory_file_exists`). 즉 플래그는 삭제 가능 집합을 넓히는 방향과 좁히는 방향 양쪽에서 동시에 작동한다 — 상태 축에서는 넓히고, 본문 축에서는 좁힌다. 아래 상태 전이 표에서 **새로 도달 가능해지는 칸은 정확히 고착 칸 1개**다.

| 행 status | 본문 `.md` | `delete` (플래그 없음) | `delete --orphan --ref` |
|-----------|-----------|----------------------|------------------------|
| active / promoted / candidate | 존재 | 거부 `delete_requires_dead_or_superseded` (**불변**) | 거부 `memory_file_exists` (**신규 차단**) |
| active / promoted / candidate | 부재 | 거부 `delete_requires_dead_or_superseded` (**불변** — 무플래그 동작 무변경) | **허용** ← 고착 해소 대상, 유일한 신규 허용 칸 |
| dead / superseded | 존재 | 허용 (**불변**) | 거부 `memory_file_exists` (**신규 차단**) |
| dead / superseded | 부재 | 허용 (**불변**) | 허용 (동치 경로) |
| active / promoted / candidate | **해석 불가** (경로 탈출 등) | 거부 `delete_requires_dead_or_superseded` (**불변**) | 거부 `memory_file_unresolvable` (**G-3 개정** — 확인 불가는 부재가 아니다) |
| dead / superseded | **해석 불가** | 허용 (**불변**) | 거부 `memory_file_unresolvable` (**G-3 개정**) |

> 우회로 신설 여부 검증: 플래그 없이 호출하는 기존 모든 경로의 결과가 **6칸 전부 불변**이다. 새 우회로는 없다. `--orphan`은 본문이 존재하거나 해석 불가한 행에서는 **기존 경로보다 오히려 엄격**하다(dead 행조차 거부).
>
> **[개정 v1.1]** "해석 불가" 2행은 G-3 재설계로 추가됐다. 개정 전 설계는 이 2칸을 **허용**으로 두어 본문 존재 확인 없이 행을 제거했고, 이는 H-2가 P0로 규정한 blind 삭제 경로의 실현이었다. 상세 판정·실증은 §3.2.2 [G-3] 절 참조.

**(3) 명령 수를 늘리지 않는다.** 서브명령은 9종 그대로다. 실측상 "9서브명령"은 코드·문서·테스트 **7곳**에 리터럴로 박혀 있다 — `memory_tool.py:6`(@header), `README.md:4`, `tools.md:763`, `tools.md:772`, `opal-harness.md:288`, `test_memory_tool.py:132`, `test_memory_tool.py:1399`. 신규 서브명령은 이 7곳 동시 개정을 강제한다.

**(4) 무손실 강화 — 인덱스 행의 `summary`를 provenance에 보존한다.** 본문이 없는 행에서 유일하게 남은 지식은 `summary` 필드다. 채택안은 `.memory_provenance.log`(`:1186` 기존 파일 재사용)에 `summary=`까지 기록하므로, 정리 후에도 "무엇이 있었는지"가 남는다. 데이터 무손실 원칙(`memory-learning.md:24`)에 오히려 부합한다.

**(5) `--ref` 필수화로 감사 추적을 오염이 아닌 보강 방향으로 만든다.** TASK.md:41이 지적한 "상태 임의 조작(`update --status superseded`) 우회"는 **상태값을 거짓으로 만들어** 추적을 오염시킨다. 채택안은 상태값을 건드리지 않고 귀착처를 명시적으로 요구하므로 D-2("상태를 임의 조작해 삭제를 강행하는 방식은 정식 경로로 채택하지 않는다")를 정면으로 만족한다.

#### 탈락 근거

| 후보 | 탈락 사유 |
|------|----------|
| **(a) `promote`에 본문 부재 허용 플래그** | `promote`의 계약은 "영구 거처로 **이전 완료**된 지식의 졸업"이다(`memory-learning.md:34`, §졸업 절차 3 "이전 완료 확인 후"). 본문이 소실된 행은 이전할 내용 자체를 읽을 수 없으므로 `--ref`에 기재하는 귀착처가 **검증 불가능한 주장**이 된다 — provenance에 `promote`로 기록되면 "졸업했다"는 거짓 이력이 남아 D-2가 배제한 감사 추적 오염이 형태만 바꿔 재발한다. 또한 `promote`는 성공 경로에서 `mem_file.unlink()`를 무조건 호출하므로(`:1181`) 부재 분기 추가가 필요해 구현 표면도 (b)보다 넓다. 결정적으로, 고착 상태의 성격은 "졸업"이 아니라 **"깨진 참조의 정리"**이며, 의미가 다른 명령에 얹는 것은 §2 Simplicity가 아니라 개념 과적재다. |
| **(c) 신규 서브명령 신설** | 판단 기준의 "명령 수를 늘리지 않는 쪽"에 정면 위배. 9→10 전환은 위 (3)의 7개 리터럴 + argparse 파서 + `cmd_*` 함수 + README 서브명령 절 + `ARCHITECTURE.md:391`·`PROJECT.md` 인벤토리 서술 검토까지 파급된다. 단일 정리 시나리오를 위해 명령 표면을 늘리는 것은 [MUST] `opal/core/PRINCIPLES.md` §2: "No abstractions for single-use code." 위반. |

#### 채택안 상세 계약

```
delete --file <MEMORY.json> --title <제목> --orphan --ref <지식 귀착처> [--with-file]
```

- `--orphan`: "이 행의 본문 `.md`가 부재함"을 주장하는 opt-in 플래그. 도구가 실제로 검증한다.
- `--ref`: `--orphan` 사용 시 **필수**. 지식의 귀착처(예: `docs/CONVENTIONS.md#변경이력`, `.opal/brain/pages/concept/...`, 또는 `미복원: 작성 머신 로컬`). 미지정 시 `orphan_ref_missing`.
- 상태 축 무조건: `--orphan` 경로에서는 `status` 값을 읽지도, 쓰지도, 요구하지도 않는다 → **`update --status` 선행 불필요**(R-2 AC 직접 충족).
- `--with-file`은 본문 부재가 전제이므로 no-op이며 `file_deleted: false`를 유지한다(기존 `:1367-1374`도 파일 부재 시 동일하게 no-op이므로 동작 일관).

### 판정 ② — R-1 검출 결과의 심각도: **(a) `violations`**

#### 실측 — 두 배열이 각각 무엇을 담는가 (`build_review_block()` `:828-870`)

| 배열 | 적재 조건 (실측 줄번호) | 엔트리 형태 | 의미론 |
|------|----------------------|-----------|--------|
| `violations` | `:846` `status not in VALID_STATUSES` / `:848` `rtype not in VALID_TYPES` / `:850` `len(summary) > SUMMARY_MAX_LENGTH` / `:852` `len(title) > TITLE_MAX_LENGTH` | `{"type": <종류>, "title": ..., <메트릭>}` — `type` 디스크리미네이터를 가진 **이종 리스트** | **행 자신의 필드값이 규칙을 어긴 데이터 결함.** 스키마 enum 위반 2종 + 길이 규칙 위반 2종. `title_too_long`은 `x-advisory` 파생(`:88`)이므로 이 배열은 "스키마 위반"이 아니라 **"규칙 위반 일반"**을 담는다 |
| `cleanup_candidates` | `:868` `status in ("dead", "superseded")` | `{"title", "status"}` | **PM이 이미 진부화를 선언한 행.** 적재 조건이 `delete`의 허용 조건(`:1356` `status not in ("dead","superseded")` → 거부)과 **문자 그대로 동일**하다 |

#### 채택 근거

**(1) 본문 부재는 "정리 대기"가 아니라 "인덱스가 거짓을 주장하는 상태"다.** `cleanup_candidates` 적재 조건은 `dead`/`superseded` — PM이 **의도적으로 부여한 종결 상태**다. 반면 본문 부재 행의 상태는 `active`일 수도 `candidate`일 수도 있으며(실측: `.opal/MEMORY.json`의 2건은 `candidate`), 누구도 그 지식을 진부하다고 선언한 적이 없다. 검출 단계에서 처분을 미리 판정하지 않는 것이 옳다.

**(2) `cleanup_candidates`는 "`delete`가 받아준다"는 암묵 계약을 갖는다 — 이를 깨면 안 된다.** `memory-learning.md:35-36`은 두 상태 행 모두를 "자가검토 `cleanup_candidates`로 표면화 후 `delete`로 제거"로 규정한다. 즉 이 배열의 소비자 계약은 **"여기 실린 행은 무플래그 `delete`로 즉시 제거 가능"**이다. 본문 부재 `candidate` 행을 여기에 실으면 무플래그 `delete`가 `delete_requires_dead_or_superseded`로 거부하므로(판정 ① 표 2행) 계약이 깨진다. 엔트리 형태 `{"title","status"}`에는 "이건 `--orphan`이 필요하다"를 표현할 자리도 없다. → **기존 배열의 의미 경계 침범**이므로 판단 기준상 배제.

**(3) TASK.md 자신의 완료기준이 `violations`를 지목한다.** TASK.md §명확화 결과 완료기준 (1): "본문 부재 행이 `review` **violations**에 검출된다."

**(4) `violations`는 `type` 디스크리미네이터 기반 확장 지점이 이미 존재한다.** 4종이 이미 서로 다른 메트릭 키(`value`/`length`)를 갖는 이종 리스트이므로, 5번째 `type`을 추가하는 것은 **구조 변경이 아니라 값 추가**다. 기존 4종의 엔트리 형태는 손대지 않으므로 R-1 AC("기존 violations 4종의 반환 형태는 불변")를 구조적으로 보장한다.

#### 탈락 근거

| 후보 | 탈락 사유 |
|------|----------|
| **(b) `cleanup_candidates`** | 위 (2) — 배열의 delete-가용성 계약을 깬다. `memory-learning.md:35-36`·`README.md:188`이 명시한 소비자 의미를 침범한다. |
| **(c) 신규 배열** | `review` 응답 최상위 키가 4개→5개로 늘어나 `review`·9개 변경 명령 응답·`README.md:176-185`·`tools.md:825`의 계약 예시가 모두 바뀐다. 단일 검사 1종을 위해 응답 스키마를 확장하는 것은 [MUST] `opal/core/PRINCIPLES.md` §2: "No speculative abstraction or unrequested flexibility." 위반. `violations`가 이미 이종 확장을 지원하므로 신규 컨테이너는 불필요. |

#### 채택안 상세 계약

```json
{"type": "memory_file_missing", "title": "<행 제목>", "file": "<인덱스의 file 필드 원문>"}
```

`violations` 배열에 기존 4종 **뒤에** 추가(행 루프 내 append 순서 유지 — 동일 행에서 기존 4종의 상대 순서 불변).

---

## 리스크 가설 표

> PLAN 단계에서 작성. `TEST-SCENARIO.md` §1 Block B(PLAN 유래 ④ 리스크 커버 축)의 입력이 된다 (→ D-5 §1.6 (b)).

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `build_review_block()` 시그니처 (`doc` → `doc, json_path=None`) | 함수 호출 계약 — 호출부 **9곳**(`:909`, `:990`, `:1118`, `:1194`, `:1229`, `:1376`, `:1389`, `:1432`, `:1443`) 중 하나라도 누락하면 그 명령에서만 검사가 조용히 무력화된다(TypeError가 아니라 **침묵 실패** — 기본값 `None`이 검사를 건너뛰므로) | P1 | L1 (전 변경 명령 응답 검사) | QA-004 |
| H-2 | `delete --orphan` | 무손실 가드 — 본문이 실재하는 행까지 통과하면 살아있는 지식의 blind 삭제 경로가 신설된다 ([MUST] `memory-learning.md:38` 위반). **벡터 2종**: ① 본문 실재 확인 누락 ② **`_resolve_memory_file()` `None` 반환 시 가드 통과(G-3 — 개정 전 설계의 실제 결함. `memory/` 밖에 본문이 살아있어도 인덱스만 끊겨 지식이 소실된다)** | **P0** | L1 (본문 존재 × 4개 status 전수) + **`_resolve_memory_file` `None` 반환 3경로 전수**(resolve 예외 / 경로 탈출 / 빈 `file`) | QA-008, QA-009, **QA-024, QA-025** |
| H-3 | `delete --orphan` 운영 의미 | "본문 부재"가 진짜 소실이 아니라 **타 머신 미동기화**일 수 있다(TASK.md:13 배경 그대로) — 조기 제거 시 지식이 영구 유실 | **P0** | L1(provenance에 `summary` 보존) + 운영 규범(`--ref` 필수·캡틴 판단) | QA-012, QA-021 |
| H-4 | 검출 술어 ↔ 처분 술어 | 두 곳이 다른 방식으로 경로를 해석하면 "`review`는 검출했는데 `delete --orphan`은 `memory_file_exists`로 거부" 또는 그 역이 발생 — 사용자가 빠져나갈 수 없는 2차 고착 | P1 | L1 (검출→정리 왕복 시나리오) + 구현 규약(양쪽 모두 `_resolve_memory_file()` `:797-816` 재사용) | QA-006 |
| H-5 | `review`/`delete` 응답 키 추가 | 하위 소비자 파싱 — `state-tool`이 CLOSE 시 memory-tool을 subprocess 호출(`link_memory_history()`, `ARCHITECTURE.md:81`)하고 `improve-tool`이 `show` 응답에 의존(`memory_tool.py:1272` 주석 H-4) | P1 | L2 (실 프로세스 호출 회귀 — state-tool 스위트 동시 실행) | QA-013, QA-022 |
| H-6 | 실환경 `.opal/MEMORY.json` 적용 | 프로젝트 SSOT 파일 손상 — 락/원자적 쓰기 실패 시 커밋 대상 파일이 깨진다 | **P0** | L2 (사본 리허설 선행, 원본 read-only 검출만) | QA-020, QA-021 |
| H-7 | 라이프사이클 표 ↔ 스키마 enum | 수동 동기화 계약 — 이번에 맞춰도 다음 enum 변경 때 다시 어긋난다(본 태스크의 R-3 자체가 그 재발 사례) | P2 | L1 (문서-스키마 파리티 테스트로 **기계 집행** 전환) | QA-015 |
| H-8 | install 실행 시점 | 배포 순서 계약 — TEST 전 install 시 미검증 규칙이 전역 홈(`~/.opal/`)으로 퍼진다 (D-3 / 095 계승) | P1 | 절차 게이트 (Step 6이 Step 5에 의존) + 배포본 diff 검증 | QA-019 |
| H-9 | 신규 ERROR_CODES **3종**(총 23→26) | 문서 파리티 — `README.md:270-293` / `tools.md:832-853` 에러 코드 표에 누락되면 SSOT 3중 불일치 재발 (094 실측 교훈: "093/091 6종 README 누락 발견") | P2 | L1 (ERROR_CODES ↔ 문서 표 파리티 테스트) | QA-017 |
| H-10 | `review` 호출당 파일 stat 증가 | 성능·락 점유 — 매 변경 명령이 `review`를 자동 첨부하므로 행 수만큼 `Path.exists()`가 락 **밖**에서 추가된다 | P2 | 실측 비교 (기준선 18.03s) | QA-018 |
| H-11 | 역방향 고아(인덱스에 없는 `memory/*.md`) | 실측 2건 존재 — `.opal/memory/노션_액티비티_지속_업데이트_규칙.local.md`, `.opal/memory/follow-up-code-scan-phase2.md`. 본 태스크는 인덱스→파일 방향만 다루므로 반대 방향은 여전히 미검출 | P2 | 범위 밖 — **후속 보고만** (TASK.md §범위 "제외"에 준함) | 없음 (§9 R-5에 기재) |

---

## 2. 기능별 분석

### F-001: `review` 참조 무결성 검사

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `build_review_block()` `:828-870` — 자가검토 블록 생성 | 수정 |
| BE | `opal/tools/memory-tool/memory_tool.py` | `_resolve_memory_file()` `:797-816` — 경로 해석 + memory/ 탈출 가드 | 재사용(무변경) |
| BE | `opal/tools/memory-tool/memory_tool.py` | 호출부 9곳 `:909`·`:990`·`:1118`·`:1194`·`:1229`·`:1376`·`:1389`·`:1432`·`:1443` | 수정(인자 1개 추가) |
| 문서 | `opal/tools/memory-tool/README.md:176-189` | `review` 응답 구조 + 배열 설명 | 수정 |
| 문서 | `opal/core/references/tools.md:825` | `review` 블록 계약 예시 | 수정(검토 후) |
| 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 회귀 기준선 + 신규 시나리오 | 수정 |

#### 2.1.2 현재 구현 (실측)

`build_review_block(doc)` (`:828`)는 **`doc` 딕셔너리 하나만** 받는다. 독스트링 `:829-831`: "dict(MEMORY.json 문서)를 받아 read 없이 소비한다." — 즉 **설계상 파일 시스템에 접근하지 않는 순수 함수**다. 이것이 R-1 결함의 구조적 원인이다: 참조 무결성은 정의상 파일 시스템 조회를 요구하는데, 함수가 경로를 모른다.

행 루프(`:840-870`)는 각 행에서 `status`/`title`/`rtype`/`summary`/`date_str` 5필드만 읽고 **`file` 필드는 한 번도 읽지 않는다**. 이후 3개 리스트에 분배한다:
- `violations` — `:846`/`:848`/`:850`/`:852` 4종 (판정 ② 실측표 참조)
- `promote_candidates` — `:855-866`, `status == "active"` 이고 `[REVIEW]` 마커 또는 `PROMOTE_AGE_DAYS`(30일) 경과
- `cleanup_candidates` — `:867-868`, `status in ("dead","superseded")`

반환(`:873-878`)은 4키 dict. `history_status`는 FIFO 초과 여부.

`_resolve_memory_file(md_path, file_field)` (`:797-816`)는 `MEMORY.json` 부모 디렉토리 기준으로 상대 경로를 resolve하고, 백틱·공백을 strip하며(마이그레이션 잔재 대응 `:806`), `memory/` 하위를 벗어나면 `None`을 반환한다(`:812-815` 경로 탈출 가드). `promote`(`:1164`)와 `delete --with-file`(`:1371`)이 이미 이 함수를 쓴다.

스키마상 `file`은 **필수 필드**이며(`memory.schema.json` `$defs.memoryRow.required` = `["title","date","type","status","file","summary"]`) 패턴은 `^memory/[^/].*\.md$`다. 즉 스키마는 **경로 형태**만 강제하고 **실재**는 강제할 수 없다 — JSON Schema의 표현력 밖이다. 이것이 "스키마 무변경"(TASK 제약 4)이 옳은 이유이자, 검사가 런타임 코드에 있어야 하는 이유다.

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: 9개 지점 전부 `cmd_*` 함수 내부이며, 모두 지역 변수 `json_path`를 이미 보유한다(전부 `pathlib.Path(args.file)`로 생성). 추가 배선 불필요.
- **하위 의존(피호출)**: `_resolve_memory_file()` 재사용 — 신규 헬퍼 0개.
- **응답 계약 소비자**: `README.md:176-189`, `tools.md:825`, 테스트 `test_memory_tool.py:776-779`(키 존재 검사)·`:869-932`(배열 의미 검사)·`:1265-1266`.
- **`@header` exports**: `build_review_block` 이름 불변 → `memory_tool.py:10` exports 배열 무변경.
- **외부 저장소 소비자 없음**: repo 전수 grep 결과 `build_review_block`은 `memory-tool/` 밖에서 참조되지 않는다(`tasks/` 산출물 문서 제외).
- **관련 테스트**: `TestReviewAmbient`(`:~770`), `TestReviewRoleBoundary`(`:869`) — 기존 계약 보존 확인 대상.

---

### F-002: 본문 부재 행 정식 정리 경로

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `cmd_delete()` `:1328-1377` | 수정 |
| BE | `opal/tools/memory-tool/memory_tool.py` | `ERROR_CODES` `:105-160` | 수정(**3종** 추가, 총 23→26) |
| BE | `opal/tools/memory-tool/memory_tool.py` | `main()` delete 파서 `:1531-1537` | 수정(2옵션 추가) |
| BE | `opal/tools/memory-tool/memory_tool.py` | `get_kst_date()` `:172` / provenance 로그 `:1186-1194` | 재사용 |
| 문서 | `opal/tools/memory-tool/README.md:193-205`, `:270-293` | `delete` 절 + 에러 코드 표 | 수정 |
| 문서 | `opal/core/references/tools.md:806-807`, `:832-853` | delete 커맨드 행 + 에러 코드 표 | 수정 |
| 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 신규 시나리오 | 수정 |

#### 2.2.2 현재 구현 (실측)

`cmd_delete()` (`:1328-1377`) 흐름:
1. `:1336-1338` — `--title` 비공백 검증.
2. `:1340` — `memory_lock(json_path, "delete")` 진입.
3. `:1344-1350` — 제목 선형 탐색, 미발견 시 `row_not_found`.
4. `:1352-1357` — `status` 추출 후 **무손실 가드**: `if status not in ("dead","superseded"): err(...)`. 주석 `:1355`에 `[MUST — 무변경]` 토큰이 이미 박혀 있다.
5. `:1359` — 행 삭제 → `:1361-1363` 스키마 재검증 → `:1365` 원자적 쓰기.
6. `:1367-1374` — `--with-file` 시 본문 삭제. 파일 부재면 조용히 no-op(`file_deleted` false 유지).
7. `:1376-1377` — 락 해제 후 `review` 생성, `ok(...)` 반환.

`cmd_promote()`의 provenance 기록(`:1186-1194`)은 `.memory_provenance.log`(MEMORY.json과 같은 디렉토리)에 append하며, 실패는 비치명적으로 삼킨다(`:1193-1194` `except Exception: pass`). `cmd_delete`에는 **provenance 기록이 전혀 없다**.

고착 재현 논리(실측 확인):
- `.opal/MEMORY.json`의 `fixture 실환경 미재현 시 결함 통과`(status `candidate`, `file: memory/테스트_fixture가_실환경_구조를_재현하지_않으면_결함이_통과한다.md`) — `.opal/memory/` 실제 목록에 해당 파일 **없음**.
- `promote` → `:1167-1168`에서 `memory_file_not_found` 거부.
- `delete` → `:1356` `"candidate" not in ("dead","superseded")` → `delete_requires_dead_or_superseded` 거부.
- 도달 가능한 명령 0개. TASK.md §배경 분석 (2)와 일치.

#### 2.2.3 영향 범위

- **상위 의존**: `delete` 서브명령 CLI 인터페이스. 기존 호출(`--title` [+`--with-file`])은 인자 기본값이 `False`/`None`이므로 **완전 하위호환**.
- **하위 의존**: `_resolve_memory_file()`(F-001과 동일 술어 — H-4 대응), `get_kst_date()`, `validate_document()`, `atomic_write_json()`, `memory_lock()`.
- **공유 상태**: `.memory_provenance.log` — `promote`와 파일을 공유하므로 **행 접두 토큰으로 구분**해야 한다(`promote` vs `delete-orphan`).
- **락 경계**: provenance 기록은 `promote`의 선례(`:1186`, 락 **안**)를 따라 락 구간 내부에 배치한다.
- **관련 테스트**: `TestErrorCodesJson`(`:1893-1921`) — `_ERROR_CODES_REQUIRED`(`:1476`) 집합 검사이므로 **추가는 통과, 삭제만 실패**. 신규 코드 **3종** 추가는 기존 테스트를 깨지 않는다(실측 확인 — 총 개수를 단정하는 검사 없음).

---

### F-003: 규범·도구 문서 정합

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/memory-learning.md` | `:29-40` 라이프사이클 표 + 가드 노트 / `:95-104` 변경이력 | 수정 |
| 문서 | `opal/tools/memory-tool/README.md` | `:168-205` review·delete 절 / `:258-266` 라이프사이클 / `:270-293` 에러 코드 / `:302-309` 변경이력 | 수정 |
| 문서 | `opal/core/references/tools.md` | `:806-807` delete 커맨드 / `:825` review 예시 / `:832-853` 에러 코드 / `:1132-` 변경이력 | 수정 |
| 설계 | `opal/tools/memory-tool/schema/memory.schema.json:54` | status enum 5종 — **정합 기준(무변경)** | 참조 |
| BE | `opal/tools/memory-tool/memory_tool.py:1-30` | `@header` description + 변경이력 라인 | 수정 |

#### 2.3.2 현재 구현 (실측)

`memory-learning.md:31-36` 라이프사이클 표는 4행(`active`/`promoted`/`superseded`/`dead`)이다. `memory.schema.json:54` enum은 5종 `["active","promoted","superseded","dead","candidate"]`. **`candidate` 1행 누락** — TASK.md §배경 분석 (3) 확인.

대조 실측: `README.md:258-266`의 라이프사이클 표는 **이미 5행이며 `candidate`를 포함**한다(`:263` "승격 검토 대기(improve-tool 위임 등) | `append --status candidate`"). 즉 **규범 문서(memory-learning.md)만 뒤처져 있고 도구 문서는 앞서 있다** — 불일치의 방향이 확정된다. `candidate` 도입 근거는 `memory_tool.py:16-17` 변경이력 v1.1 "VALID_TYPES에 improvement, VALID_STATUSES에 candidate 추가(additive) — improve-tool record --scope local의 memory-tool append 위임 대상 (058)".

`memory-learning.md:38`은 `delete` 무손실 가드를 [MUST] 노트로 명문화한다. `:24`는 무손실 원칙 본문. `:35-36`은 `cleanup_candidates` → `delete` 경로를 규정한다(판정 ② 근거 (2)).

`tools.md`는 v2.16까지 진행됐고 memory-tool 섹션(`:763-853`)이 커맨드·출력 형식·에러 코드를 중복 게재한다. `opal-harness.md:288`은 **`migrate`를 여전히 나열하는 선재 drift**(078에서 소멸한 서브명령)를 갖고 있다 — 본 태스크 범위 밖(§9 R-6 보고).

#### 2.3.3 영향 범위

- 규범 문서 변경은 PM 판단 근거를 바꾸므로 **배포 전 검증 필수**(D-3).
- `install-mac.sh:220-232` `strip_deploy_md_recursive`가 배포 시 `## 변경이력` 섹션 이하를 제거한다(`:1072`·`:1116`·`:1579`). 따라서 **`.md` 파일은 배포본 diff 0이 성립하지 않는다** — AC (6)의 diff 0 검증 대상은 `memory_tool.py`(strip 비대상)로 한정된다.
- README 변경이력 표의 컬럼 스키마는 `| 버전 | 태스크 | 내용 |`(일시 컬럼 없음, `:304`)이며 다른 두 문서와 다르다. **컬럼 스키마 변경은 범위 밖**([MUST] PRINCIPLES §3 "Touch only what the plan names") — 각 파일의 기존 스키마를 그대로 따른다.

---

### F-004: RED 증거 + 전건 회귀 + install

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` (3100줄) | 신규 3클래스 + 헬퍼 1종 | 수정 |
| 테스트 | `opal/tools/memory-tool/tests/fixtures/fixture_doc_populated.json` | 6메모리·5히스토리 — **in-test 가공으로 재사용**(신규 fixture 0) | 참조 |
| 환경 | `scripts/install-mac.sh` | 재배포 실행(스크립트 자체는 무변경) | 실행 |
| 검증 | `.opal/MEMORY.json` | 실환경 검출 확인 대상(**읽기 전용**) | 참조 |

#### 2.4.2 현재 구현 (실측)

- 기준선: **163 passed, 25 subtests passed in 18.03s**.
- 테스트는 **subprocess 실 프로세스 호출**만 쓴다(`_run()` `:59-70`, `_run_raw()` `:73-76`) — mock/patch/MagicMock 0건. @header `:8`이 "mock/patch/MagicMock 금지(헌법 §4) — 실 fixture·실 프로세스(subprocess)만"으로 규약을 명문화한다. [MUST] `opal/core/PRINCIPLES.md` §4 "Don't fake it" 준수 대상.
- 프리픽스 규약 실측: `[T045/L1-...]`(045 트랙) / `[T078/...]`(078) / `[T079/...]`(079). → 본 태스크는 **`[T096/...]`**.
- 픽스처 설치 헬퍼: `_init_json()`(`:87-95`, 빈 문서), `_setup_populated()`(`:98-116`, MEMORY.json + `memory/` 6파일 생성), `_install_json()`(`.opal/` 하위 배치 — 실환경 레이아웃 재현).
- 문서 파리티 테스트 선례 존재: `TestTaskNumberDocs`(`:2515-2562`)가 `_REPO_ROOT` 기준으로 repo 문서를 직접 읽어 정규식 검사한다 → **R-3 검증에 그대로 재사용 가능한 패턴**.
- 079 선례(테스트 @header 변경이력 v1.2): "신규 픽스처 신설 없음(기존 fixture_doc_populated.json in-test 가공)" → 본 태스크도 동일 방침.

#### 2.4.3 영향 범위

- **fixture 실환경 재현 리스크**: `.opal/MEMORY.json` 실측 기록(092/094 교훈)이 "fixture가 실환경 구조(왕복 경로·깊이)를 재현하지 않으면 결함이 통과한다"를 남겼다. 실환경은 `.opal/MEMORY.json` + `.opal/memory/*.md` **형제 관계**이므로, 신규 orphan 테스트 중 최소 1건은 `_install_json()`(`.opal/` 레이아웃)으로 작성해야 한다.
- **install 순서**: [MUST] D-3 — TEST 전건 통과 이후에만 실행.
- **RED 작성자 분리**: [MUST] `red-first.md` §2 — Step 1(RED)은 `opal-test-agent(mode: red)`, Step 2·3(GREEN)은 `opal-be-agent`.

---

## 3. 기능별 설계

### F-001: `review` 참조 무결성 검사

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | `build_review_block(doc)` → `build_review_block(doc, json_path=None)`; 행 루프에 `memory_file_missing` 검사 추가 | `memory_tool.py:828-870` |
| 2 | `opal/tools/memory-tool/memory_tool.py` | BE | 호출부 9곳에 `json_path` 전달 | `:909`, `:990`, `:1118`, `:1194`, `:1229`, `:1376`, `:1389`, `:1432`, `:1443` |

#### 3.1.2 API·데이터 모델 설계

**함수 시그니처 변경**

```python
def build_review_block(doc, json_path=None):
    """자가검토 블록 생성. dict(MEMORY.json 문서)를 소비한다.
    json_path가 주어지면 각 행의 file 포인터 실재 여부를 검사해
    violations에 memory_file_missing을 추가한다(참조 무결성, 096 R-1).
    json_path=None이면 참조 무결성 검사를 건너뛴다(문서 단독 검토 하위호환).
    """
```

- `json_path` 기본값 `None`: 함수를 직접 import하는 외부 호출자(현재 repo 내 0건)를 위한 하위호환. 저장소 내 9개 호출부는 **전부 명시 전달**한다 (→ H-1).
- 인자를 `pathlib.Path`로 받되 내부에서 `str()` 변환하여 `_resolve_memory_file()`에 넘긴다 — 기존 호출 관례(`:1164` `_resolve_memory_file(str(json_path), file_field)`)와 동일 (→ D-1 `:1164`).

**행 루프 삽입 코드** (`:852` `title_too_long` 검사 **직후**)

```python
        if json_path is not None:
            file_field = row.get("file", "")
            mem_file = _resolve_memory_file(str(json_path), file_field) if file_field else None
            if mem_file is None:
                # 경로 해석 실패 = "본문 부재"가 아니라 "확인 불가" — 처분이 다르므로 어휘를 분리한다 (G-3)
                violations.append({"type": "memory_file_unresolvable",
                                   "title": title, "file": file_field})
            elif not mem_file.exists():
                violations.append({"type": "memory_file_missing",
                                   "title": title, "file": file_field})
```

설계 결정과 근거:
- **삽입 위치**: 기존 4종의 append 순서 뒤 → 동일 행에서 기존 4종의 상대 순서가 불변이므로 R-1 AC("기존 violations 4종의 반환 형태는 불변")를 순서 차원에서도 보장 (→ D-1 `:846-852`).
- **[개정 v1.1] 검출 어휘를 2종으로 분리한다 — `memory_file_missing` ≠ `memory_file_unresolvable`**: 개정 전 설계는 두 경우를 `memory_file_missing` 하나로 뭉쳤으나, §3.2.2 G-3 재설계로 **처분이 갈린다**(전자는 `delete --orphan`으로 정리 가능, 후자는 거부). 검출 어휘와 처분 어휘가 어긋나면 "`review`가 부재라고 했는데 `delete --orphan`이 거부한다"는 2차 혼란이 발생한다 — 이는 내가 H-4로 정의한 계약 위반이자 [MUST] `opal/core/references/harness/citation-rules.md` §7.1 영역 간 용어 일관성 위반이다. 따라서 어휘 분리는 G-3 해소의 **구조적 귀결**이지 선택이 아니다.
  - `memory_file_missing` — 경로 해석 **성공** + 파일 부재. 운영 의미: 본문이 있었으나 사라졌다 → `delete --orphan --ref`로 정리 가능.
  - `memory_file_unresolvable` — 경로 해석 **실패**(`_resolve_memory_file()` `None`). 운영 의미: 본문의 실재 여부를 확인할 수 없다 → `delete --orphan` 거부, **포인터 수리 필요**. 단 `dead`/`superseded` 행은 무플래그 `delete`로 종전대로 제거 가능하다(상태 가드가 `mem_file`을 조회하지 않으므로 — §판정 ① 전이표). 잔존 고착은 `{active, promoted, candidate} × 해석 불가`에 한정된다(§9 R-13).
- **`None`을 "부재"로 취급하지 않는 근거(실증)**: `_resolve_memory_file()`은 `memory/` 밖 경로에 `None`을 반환하는데(`:812-815`), 실측 결과 그런 행의 본문이 **실제로 디스크에 실재할 수 있다** — `file: "memory/../outside_body.md"`는 스키마 패턴 `^memory/[^/].*\.md$`를 통과하면서 `None`으로 해석되고, `outside_body.md`는 그대로 존재했다(§3.2.2 실증 표). 즉 `None`은 "본문 없음"의 증거가 아니라 **"증거 없음"**이다.
- **빈 `file_field` 방어(도달성 실측)**: 빈 문자열은 스키마 패턴 `^memory/[^/].*\.md$`에 **불일치**하고, `load_document()`는 로드 시점에 `validate_document()`를 돌려 위반 시 `schema_validation_failed`로 종료한다(`memory_tool.py:460-462`). 따라서 **CLI 경로에서 빈 `file` 행은 가드에 도달하지 못한다**. 그럼에도 `row.get("file","")` 폴백과 `if file_field else None` 분기는 유지한다 — 방어 비용이 1식이고, 유지 시 `memory_file_unresolvable`로 안전측 분류되기 때문이다(도달 불가 시나리오를 위한 *별도 에러 코드*는 만들지 않는다 — §3.2.2 판정 3 참조).
- **성능**: 행당 `Path.exists()` 1회. 락 **밖**에서 실행되므로(`:1376`, `:1389` 모두 `with` 블록 종료 후) 락 점유 시간에 영향 없음 (→ H-10).
- [MUST] `opal/core/PRINCIPLES.md` §2: "No abstractions for single-use code." — 신규 헬퍼를 만들지 않고 `_resolve_memory_file()`을 재사용한다.

**호출부 9곳 변경** (전량 `build_review_block(doc, json_path)`)

| # | 줄 | 함수 | `json_path` 존재 확인 |
|---|-----|------|---------------------|
| 1 | `:909` | `cmd_init` | `:906` `json_path = pathlib.Path(args.file)` 계열 |
| 2 | `:990` | `cmd_append` | 동 |
| 3 | `:1118` | `cmd_update` | `:1070` |
| 4 | `:1194` | `cmd_promote` | `:1136` |
| 5 | `:1229` | `cmd_prune` | `:1214` |
| 6 | `:1376` | `cmd_delete` | `:1335` |
| 7 | `:1389` | `cmd_review` | `:1387` |
| 8 | `:1432` | `cmd_task_number` (`--bump`) | `:1409` |
| 9 | `:1443` | `cmd_task_number` (`--set`) | 동 |

> `promote`/`delete`는 행·파일 삭제를 **완료한 뒤** `review`를 생성하므로 방금 제거한 행이 위양성으로 잡히지 않는다(`:1172` `del` → `:1194` review / `:1359` `del` → `:1376` review).

**응답 계약 (변경 후)**

```json
{"promote_candidates": [...], "cleanup_candidates": [...],
 "history_status": {"fifo_trimmed": false, "count": 5},
 "violations": [{"type": "memory_file_missing", "title": "PM이 도구 계수를 grep으로 대체해 오판했다",
                 "file": "memory/PM이_도구_계수를_grep으로_대체해_오판했다.md"}]}
```

최상위 키 4종 불변 — [MUST] 판정 ② (c) 탈락 근거 준수.

#### 3.1.3 환경 변경

해당 없음 (표준 라이브러리만 — `memory_tool.py:24-33` import 목록 무변경).

#### 3.1.4 배치/마이그레이션

해당 없음 (`MEMORY.json` 스키마·데이터 무변경 — TASK 제약 4).

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| QA-001 | R-1 AC 전반 | 기능 테스트 | 본문 부재 행 1건이 있을 때 `review` `violations`에 `{"type":"memory_file_missing","title":…,"file":…}` 정확히 1건. (RED: 현재 0건) |
| QA-002 | R-1 AC 후반 | 기능 테스트 | 본문이 전건 실재하면 `memory_file_missing` 0건 |
| QA-003 | R-1 AC "기존 4종 불변" | 회귀 테스트 | `title_too_long`/`summary_too_long`/`invalid_status`/`invalid_type` 엔트리의 **키 집합과 값**이 변경 전과 동일 |
| QA-004 | R-1 AC + H-1 | 통합 테스트 | `append`/`update`/`prune`/`delete`/`task-number --bump`/`init` 응답의 자동 첨부 `review`에도 동일 검출 (호출부 누락 검출) |
| QA-005 | R-1 AC + H-4 + **G-3** | 보안 테스트 | `file`이 `memory/` 밖(`memory/../outside.md` 등)을 가리키는 행은 `memory_file_missing`이 **아니라** `memory_file_unresolvable`로 검출된다(어휘 분리 확인). `memory/` 밖 파일을 stat하지 않는다 |

---

### F-002: 본문 부재 행 정식 정리 경로

#### 3.2.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | `ERROR_CODES`에 `memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable` **3종** 추가 (총 23→26) | `:105-160` |
| 2 | `opal/tools/memory-tool/memory_tool.py` | BE | `cmd_delete()` — `--orphan`/`--ref` 분기 + provenance 기록 + 응답 필드 | `:1328-1377` |
| 3 | `opal/tools/memory-tool/memory_tool.py` | BE | `main()` delete 파서에 `--orphan`·`--ref` 등록 | `:1531-1537` |
| 3b | `opal/tools/memory-tool/memory_tool.py` | BE | **[개정 v1.2] `cmd_promote()`의 `mem_file is None` 분기 어휘 정합** — `memory_file_not_found` → `memory_file_unresolvable` (1줄). `not mem_file.exists()` 분기는 **무변경** | `:1164-1166` |
| 4 | `opal/tools/memory-tool/memory_tool.py` | BE | `@header` description + 변경이력 v2.2 라인 | `:1-30` |

#### 3.2.2 API 설계

**ERROR_CODES 추가 — 신규 3종 (총 23종 → 26종)** (`:105-160` 딕셔너리, `delete_requires_dead_or_superseded` 항목 인접 배치)

```python
    # ── 096 신설 (PLAN §3.2.2) ──
    "memory_file_exists":       "--orphan은 본문 .md가 부재한 행 전용 — 본문이 실재함: {path} (무손실 가드 유지)",
    "orphan_ref_missing":       "--orphan 사용 시 --ref(지식 귀착처) 필수 — 귀착처 미기재 정리 거부 (감사 추적)",
    "memory_file_unresolvable": "<file> 경로를 memory/ 하위로 해석할 수 없어 본문 부재를 확인할 수 없음: file={file} — 확인 불가는 부재가 아니므로 정리 거부 (무손실)",
```

> **총 개수 실측**: 현행 `ERROR_CODES` **23종**(`~/.opal/.venv/bin/python -c "len(m.ERROR_CODES)"` 실행 확인) → 변경 후 **26종**.
> 기존 코드 삭제·개명 0건 → `TestErrorCodesJson`(`:1893-1921`)의 `_ERROR_CODES_REQUIRED` 포함 검사·`_ERROR_CODES_FORBIDDEN` 부재 검사·불변 유지 목록 검사 3건 모두 통과 유지 (해당 테스트는 **집합 포함/부재** 검사이며 총 개수를 단정하지 않으므로, 종수 증가가 기존 테스트를 깨지 않는다 — 실측 확인).

**`cmd_delete()` 시그니처·독스트링**

```python
def cmd_delete(args):
    """dead/superseded 상태 행 물리 제거 (MEMORY.json).
    --title로 행 식별. 행 없으면 row_not_found.
    무손실 가드: active/promoted 행은 delete_requires_dead_or_superseded 반환 + 행 불변 [MUST — 무변경].
    --orphan: 본문 .md가 부재한 행 전용 정리 경로(096 R-2). 상태 가드 대신 본문 부재를
      검증하며, 본문이 실재하면 memory_file_exists로 거부한다(무손실 가드 우회 불가).
      --ref(지식 귀착처) 필수 + .memory_provenance.log에 summary까지 기록(무손실).
    --with-file 시 memory/<file>.md도 삭제(_resolve_memory_file() 경로 화이트리스트 재사용).
    성공 시 review 블록 첨부.
    """
```

#### [G-3] `_resolve_memory_file()` `None` 반환 처분 판정 — **거부** (개정 v1.1)

**결함 실측** — 개정 전 가드 `if mem_file is not None and mem_file.exists()`는 `mem_file is None`일 때 조건이 거짓이 되어 **본문 존재를 확인하지 않은 채 통과**했다. `_resolve_memory_file()`(`:797-816`)이 `None`을 반환하는 경로는 3가지다.

| # | `None` 반환 경로 | 근거 줄 | 스키마 도달성 | 본문이 실재할 수 있는가 |
|---|-----------------|--------|--------------|----------------------|
| 1 | `(md_dir / file_field).resolve()` 예외 | `:806-809` | 가능(드묾) — 패턴 통과 후 OS 계층에서 실패 | **판정 불가** |
| 2 | `target.relative_to(memory_dir)` ValueError = `memory/` 밖 경로 탈출 | `:812-815` | **완전 도달 가능** — `memory/../outside.md`가 스키마 패턴 `^memory/[^/].*\.md$`를 **통과**함(실측) | **예 — 실증됨** |
| 3 | `file_field`가 빈 문자열(호출부 단락) | 호출부 | **도달 불가** — 빈 문자열은 패턴 불일치 → `load_document()`가 `schema_validation_failed`로 차단(`:460-462`) | 해당 없음 |

**실증 (임시 디렉토리 실행)**:

```
'memory/../outside_body.md'  -> _resolve_memory_file = None
'memory/../../etc/hosts.md'  -> _resolve_memory_file = None
''                           -> _resolve_memory_file = None
'memory/real.md'             -> _resolve_memory_file = /private/tmp/g3probe/memory/real.md
실재하는 outside_body.md 존재? True        ← 본문은 살아 있는데 해석은 None
```

**판정: 거부한다.** PM 제안 방향에 동의하며, 반박하지 않는다. 근거는 3층이다.

1. **술어 불일치가 결함의 본질이다.** `--orphan`이 주장하는 술어는 "본문이 **부재**함"인데, 개정 전 코드의 실제 술어는 "본문이 부재 **또는 확인 불가**"였다. 위 실증대로 `None`인 행의 본문이 `memory/` 밖에 **살아서 존재할 수 있으므로**, `None`을 부재로 간주하면 살아있는 지식을 인덱스에서 끊어내고 파일만 고아로 남긴다 — 인덱스로도 `review`로도 다시 찾을 수 없게 되므로 **실질적 지식 소실**이다. [MUST] `opal/core/references/harness/memory-learning.md:24`: "메모리(지식)는 **blind 삭제 금지**".
2. **내가 세운 H-2 계약의 정확한 실현이었다.** H-2는 "본문이 실재하는 행까지 통과하면 살아있는 지식의 blind 삭제 경로가 신설된다"를 P0로 규정했다. 개정 전 코드는 그 경로를 실제로 열어두었으므로, 판정 ①의 채택 근거 (2)("새로 도달 가능해지는 칸은 고착 칸 1개")가 **성립하지 않는 상태**였다. 거부로 전환해야 그 근거가 참이 된다.
3. **안전측 기본값 원칙.** 증거 없음(`None`)을 증거 있음(부재)으로 승격시키는 것은 무손실 체계에서 허용될 수 없다. 확인할 수 없으면 손대지 않는다.

**판정 3 — 빈 `file_field`와 경로 탈출을 하나의 에러 코드로 묶는다 (`memory_file_unresolvable`).**

- **채택 근거 (a) 처분이 동일하다.** 두 경우 모두 "본문 부재를 확인할 수 없음" → 거부. 도구가 취할 행동이 갈리지 않으므로 코드를 나눌 실익이 없다.
- **채택 근거 (b) 빈 `file`은 CLI 경로에서 도달 불가하다(위 표 #3 실측).** 도달 불가 케이스 전용 에러 코드를 만드는 것은 [MUST] `opal/core/PRINCIPLES.md` §3: "No error handling for impossible scenarios." 위반이자 §2 "No speculative abstraction" 위반이다.
- **운영 의미 구분은 코드 분리 없이 달성한다.** PM 지적대로 두 경우의 운영 의미는 다르다(빈 `file` = 본문이 지정된 적 없음 / 경로 탈출 = 본문이 어딘가 실재할 수 있음). 그래서 에러 페이로드에 **`file` 원문 값을 실어** 운영자가 `file=''`와 `file='memory/../outside.md'`를 즉시 구별하게 한다 — 구별 가능성은 보존하고 코드 표면은 늘리지 않는다.
- **탈락안**: 2종 분리(`memory_file_unspecified` + `memory_file_escapes_root`) — 도달 불가 케이스에 코드 1종을 소모하고, README·`tools.md` 표 2곳 × 2행을 추가로 늘리며(H-9 파리티 부담 증가), 처분이 같아 운영자 행동을 바꾸지 못한다.

**가드 분기 설계 (최종)** — `:1352-1357`을 아래로 교체

```python
        row = doc["memories"][target_idx]
        status = row.get("status", "")

        orphan = bool(getattr(args, "orphan", False))
        ref = (getattr(args, "ref", None) or "").strip()

        if orphan:
            file_field = row.get("file", "")
            mem_file = _resolve_memory_file(str(json_path), file_field) if file_field else None
            # G-3: 해석 실패는 "부재"가 아니라 "확인 불가" — 확인할 수 없으면 삭제하지 않는다 [MUST 무손실]
            if mem_file is None:
                err("delete", "memory_file_unresolvable", file=file_field)
            if mem_file.exists():
                err("delete", "memory_file_exists", path=str(mem_file))
            if not ref:
                err("delete", "orphan_ref_missing")
        else:
            # 무손실 가드: active/promoted 행은 삭제 거부 [MUST — 무변경]
            if status not in ("dead", "superseded"):
                err("delete", "delete_requires_dead_or_superseded")
```

설계 결정과 근거:
- **`mem_file is None`을 최우선 거부**: `err()`가 `sys.exit(1)`로 종료하므로(`:159-160`) 이 분기를 통과한 시점에 `mem_file`은 **반드시 non-None**이다. 따라서 뒤따르는 `mem_file.exists()`는 `is not None` 재검사 없이 안전하며, "확인 불가 → 통과"라는 결함 형태가 **코드 구조상 재발 불가능**해진다(개정 전처럼 `and`로 묶으면 None이 조용히 통과하지만, 조기 반환은 그럴 수 없다).
- **`else` 분기의 3줄은 문자 그대로 원본**(`:1355-1357`) — 무플래그 경로의 행위가 비교 가능하게 불변임을 코드 형태로 보장 ([MUST] `memory-learning.md:38`).
- **검사 순서 `memory_file_unresolvable` → `memory_file_exists` → `orphan_ref_missing`**: 가장 강한 안전 조건부터 판정한다. 본문이 실재하거나 확인 불가하면 `--ref`를 붙였든 안 붙였든 무조건 거부해야 하므로, 우회 차단 2종을 `--ref` 검사보다 앞에 둔다 (→ H-2).
- **거부 시 부수효과 0**: 세 `err()` 모두 행 삭제(`:1359`)·`atomic_write_json`(`:1365`) **이전**에 위치하므로 인덱스·본문·provenance 어느 것도 변경되지 않는다.
- **`--orphan` 경로는 `status`를 읽지 않는다**: 술어를 본문 존재 여부 단일 축으로 두는 것이 §2 Simplicity이며, R-2 AC의 `candidate`/`promoted`를 포함하고 `active`까지 자연 포함한다. `status`를 candidate/promoted로 한정하면 `active` + 본문 부재라는 동형 고착이 남는다 — **부분 처방 금지**.
- **`err()`는 `sys.exit(1)`을 호출**(`:159-160`)하므로 락 컨텍스트가 예외 없이 종료되고 파일은 무변경이다 — 기존 실패 경로와 동일한 원자성 보장(`TestAtomicWrite` `:1927` 패턴).
- **`getattr` 폴백 사용**: 기존 코드가 `getattr(args, "with_file", False)`(`:1368`) 관례를 쓰므로 스타일 일치 ([MUST] `opal/core/PRINCIPLES.md` §3: "Match existing style").

#### [정정 3] `promote` 어휘 정합 판정 — **(가) 범위 내 정정 채택** (개정 v1.2)

**실측 결함** (`memory_tool.py:1164-1168`) — `promote`는 **해석 불가**와 **본문 부재**를 똑같이 `memory_file_not_found`("부재" 어휘)로 반환한다.

```python
        mem_file = _resolve_memory_file(str(json_path), file_field)
        if mem_file is None:
            err("promote", "memory_file_not_found", path=file_field)   # ← 해석 불가인데 "부재"라고 말한다
        if not mem_file.exists():
            err("promote", "memory_file_not_found", path=str(mem_file))
```

**채택: (가) 범위 내 정정.** `mem_file is None` 분기만 `memory_file_unresolvable`로 교체한다(1줄). 두 번째 분기는 무변경.

```python
        mem_file = _resolve_memory_file(str(json_path), file_field)
        if mem_file is None:
            err("promote", "memory_file_unresolvable", file=file_field)   # 정정 3
        if not mem_file.exists():
            err("promote", "memory_file_not_found", path=str(mem_file))   # 무변경
```

**채택 근거**

1. **불일치의 원인 제공자가 096이다 — 따라서 범위 내다.** 096 이전에는 `memory_file_unresolvable`이라는 어휘 자체가 없었으므로 `promote`의 라벨은 유일한 답이었고 모순이 아니었다. 096이 `review`에 이 어휘를 도입하는 **순간** 같은 행에 대해 `review`는 "해석 불가", `promote`는 "부재"라고 말하는 모순 표면이 생긴다. 이는 §3.1.2에서 검출 어휘를 2분한 것과 **동일한 구조의 강제**다(그 판단은 게이트 iteration 2에서 인정됨).
2. **운영 피해가 구체적이다.** R-13의 잔존 고착 집합(`{active, promoted, candidate} × 해석 불가`)에 속한 행은 운영자가 **반드시 `promote`를 먼저 시도**하게 된다(살아있는 지식이므로). 거기서 "본문을 찾을 수 없음"을 받으면 사라진 파일을 찾아 헤매게 되는데, 실제 원인은 **포인터가 잘못된 것**이고 본문은 `memory/` 밖에 멀쩡히 있을 수 있다. 잘못된 라벨이 잘못된 복구 행동을 유도한다.
3. [MUST] `opal/core/references/harness/citation-rules.md` §7.1: 영역 간 동일 개념이 다른 토큰으로 쓰이는 것을 능동 검출·해소 대상으로 규정한다. 여기서 두 토큰은 **완전히 동일한 술어**(`_resolve_memory_file(...) is None`)를 가리킨다.
4. **회귀 위험 0 — 실측.** `promote`의 `mem_file is None` 분기를 밟는 테스트가 **존재하지 않는다**(§5.2 실측 표). `memory_file_not_found` 키 자체는 두 번째 분기가 계속 사용하므로 `TestErrorCodes.REQUIRED_CODES`(`:1038-1046`)의 **존재 검사도 통과 유지**된다.
5. **동작은 불변, 라벨만 정밀해진다.** 거부 여부·exit code·부수효과가 모두 같다. 무손실 가드를 넓히지도 좁히지도 않는다.

**탈락: (나) 범위 밖 이월.** [MUST] PRINCIPLES §3 "Touch only what the plan names"가 근거였으나, 위 (1)에 따라 이 불일치는 **인접 코드의 선재 결함이 아니라 096이 만든 표면**이므로 §3의 보호 대상이 아니다. 이월하면 096이 스스로 만든 모순을 남긴 채 종료하게 된다.

**[확정] `promote` 기대 에러 코드 (PM의 TS-037 ③ 확정용)**

| `promote` 대상 행의 상태 | 기대 에러 코드 | 변경 여부 |
|------------------------|--------------|----------|
| `file` 해석 불가 — 경로 탈출 / resolve 예외 / 빈 `file` (`_resolve_memory_file` → `None`) | **`memory_file_unresolvable`** | **096에서 변경** |
| `file` 해석 성공 + 본문 `.md` 부재 | `memory_file_not_found` | 불변 |
| 제목 미발견 / `--title`에 `../` | `row_not_found` | 불변 (`:1147-1148`, `:1157-1158`) |
| `--to` 누락·오값 / `--ref` 누락 | `invalid_promote_target` / `promote_ref_missing` | 불변 |

---

**provenance 기록** — `:1365` `atomic_write_json()` 직후, 락 **안**에 배치 (`promote` `:1186-1194` 선례)

```python
        provenance_logged = False
        if orphan:
            today = get_kst_date()
            provenance_entry = (
                f"{today} | delete-orphan | title={row['title']} | "
                f"type={row.get('type', '')} | status={status} | ref={ref} | "
                f"file={row.get('file', '')} | summary={row.get('summary', '')}\n"
            )
            try:
                with (json_path.parent / ".memory_provenance.log").open("a", encoding="utf-8") as f:
                    f.write(provenance_entry)
                provenance_logged = True
            except Exception:
                pass  # provenance 기록 실패는 비치명적 (promote :1193-1194 동형)
```

- **행 접두 토큰 `delete-orphan`**: `promote`의 `promote` 토큰(`:1188`)과 동일 파일을 공유하므로 구분자가 필요하다 (→ F-002 §2.2.3 공유 상태).
- **`summary=` 포함이 핵심**: 본문이 없는 행에서 유일하게 남은 지식이 `summary`다. 이를 기록해야 정리가 진짜 무손실이 된다 (→ H-3, 판정 ① 채택 근거 (4)).
- `get_kst_date()`(`:172`)는 `node date.js` 우선 + Python UTC+9 폴백을 이미 갖추므로 신규 처리 불필요.

**응답 계약**

```python
    review = build_review_block(doc, json_path)
    result = {"title": title, "row_removed": True, "file_deleted": file_deleted,
              "orphan": orphan, "review": review, "migration": migration}
    if orphan:
        result.update({"reason": "memory_file_missing", "ref": ref,
                       "provenance_logged": provenance_logged})
    ok("delete", **result)
```

- **`orphan`은 항상 반환**(무플래그 시 `false`) — 소비자가 분기 없이 읽을 수 있다.
- **`reason`/`ref`/`provenance_logged`는 orphan 경로에서만** — R-2 AC "응답에 제거 사유와 지식 귀착처가 기록된다" 충족. `reason` 값은 F-001의 violation `type`과 **동일 토큰 `memory_file_missing`**을 쓴다(검출→처분 어휘 일관, citation-rules §7.1 영역 간 용어 일관성).
- 기존 키(`title`/`row_removed`/`file_deleted`/`review`/`migration`) 전부 보존 → 하위 소비자 무영향 (→ H-5).

**argparse 등록** (`:1531-1537` delete 파서)

```python
    p_delete.add_argument("--orphan", action="store_true",
                          help="본문 .md가 부재한 인덱스 행 정리 — 본문이 실재하면 memory_file_exists로 거부(무손실 가드 유지). --ref 필수")
    p_delete.add_argument("--ref", default=None,
                          help="지식 귀착처 (--orphan 필수) — 예: docs/CONVENTIONS.md#변경이력 | .opal/brain/pages/... | '미복원: 작성 머신 로컬'")
```

**명명 근거**: `--orphan`은 "인덱스에만 남은 고아 행"을 가리키는 통용 용어이고, 위반 토큰 `memory_file_missing`과 에러 코드 `memory_file_exists`가 서로 대응 쌍을 이룬다. `--ref`는 `promote`의 동명 인자(`:1521-1522`)와 의미(영구 거처 위치)가 같으므로 어휘를 재사용한다.

#### 3.2.3 환경 변경

해당 없음.

#### 3.2.4 배치/마이그레이션

해당 없음. 단, **실환경 적용은 2단 분리**한다 (→ H-6):
- **단계 A (본 태스크 범위)**: `.opal/MEMORY.json`을 임시 디렉토리로 **복사**하여 `--orphan` 리허설 → 검출 2건이 정리 가능함을 실증. **원본 무변경.**
- **단계 B (캡틴 판단 사항 — 본 태스크에서 실행하지 않음)**: 실제 2건 제거. PLAN은 실행 명령만 제시하고 실행하지 않는다.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| QA-006 | R-2 AC 전반 + H-4 | 기능 테스트 | `candidate` + 본문 부재 행에 `delete --orphan --ref X` → `ok:true`, `orphan:true`, `reason=="memory_file_missing"`, `ref=="X"`, 행 제거. 직전 `review`에서 같은 행이 `memory_file_missing`으로 검출됨(검출→정리 왕복) |
| QA-007 | R-2 AC 전반 | 기능 테스트 | `promoted` + 본문 부재 행도 동일하게 성공 |
| QA-008 | R-2 AC 후반 + **H-2** | 회귀 테스트 | `active` + 본문 **존재** 행에 `--orphan --ref X` → `memory_file_exists` 거부, 인덱스 행 불변, 본문 파일 불변 |
| QA-009 | R-2 AC 후반 + **H-2** | 회귀 테스트 | `dead` + 본문 **존재** 행에 `--orphan --ref X` → `memory_file_exists` 거부 (orphan이 우회로가 아님을 4개 status 전수로 확인) |
| QA-010 | R-2 AC + 감사 추적 | 기능 테스트 | `--orphan` 단독(`--ref` 없음) → `orphan_ref_missing`, 행 불변 |
| QA-011 | 무플래그 동작 불변 | 회귀 테스트 | 본문 부재 `candidate` 행에 플래그 없이 `delete` → 여전히 `delete_requires_dead_or_superseded`, 행 불변 (silent 완화 없음) |
| QA-012 | R-2 AC "제거 사유·귀착처 기록" + **H-3** | 기능 테스트 | `.memory_provenance.log`에 `delete-orphan` 행 1건, `ref=`·`summary=`·`status=` 토큰 포함 |
| QA-013 | 원자성 + H-5 | 통합 테스트 | orphan delete 후 `.tmp`/`.lock` 잔여 0건, `show`가 `ok:true`(스키마 유효), 기존 응답 키 5종 전부 존재 |
| QA-014 | R-2 AC "단일 명령" | 기능 테스트 | `update --status` 호출 없이 **단일 `delete` 호출 1회**로 행이 제거된다(호출 계수 검증) |
| **QA-024** | **G-3 / H-2 벡터②** | 보안 테스트 | 경로 탈출 `file`(`memory/../outside.md` — 스키마 패턴 통과)이고 **`memory/` 밖에 본문이 실재**하는 행에 `--orphan --ref X` → `memory_file_unresolvable` 거부, 인덱스 행 불변, **`memory/` 밖 본문 파일 불변**(삭제·stat 없음) |
| **QA-026** | **정정 3 / 어휘 일관성** | 기능 테스트 | 해석 불가 `file`을 가진 행에 `promote --to docs --ref X` → **`memory_file_unresolvable`** 거부(종전 `memory_file_not_found` 아님). 해석 성공 + 본문 부재 행은 **여전히 `memory_file_not_found`**(2번째 분기 불변). 같은 행에 대해 `review`·`promote`·`delete --orphan` 세 명령의 어휘가 일치한다 |
| **QA-025** | **G-3 / H-2 벡터② 전수** | 보안 테스트 | `_resolve_memory_file()` `None` 반환 **3경로 전수** — ① 경로 탈출 ② 빈 `file`(스키마 검증을 우회해 in-test 직접 주입) ③ resolve 예외 — 전부 `memory_file_unresolvable`로 거부되고 행이 불변이다. 어느 경로도 삭제로 이어지지 않는다 |

---

### F-003: 규범·도구 문서 정합

#### 3.3.1 파일 변경 계획

**신규 생성**: 없음.

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/memory-learning.md` | 문서 | 라이프사이클 표에 `candidate` 행 추가 + orphan 정리 경로 [MUST] 노트 신설 + 변경이력 v1.5 | `:31-38`, `:95-104` |
| 2 | `opal/tools/memory-tool/README.md` | 문서 | `review` 응답 구조·설명, `delete` 절, 에러 코드 표 2행, 변경이력 v2.2 | `:176-205`, `:270-293`, `:302-309` |
| 3 | `opal/core/references/tools.md` | 문서 | delete 커맨드 행, review 출력 예시, 에러 코드 표 2행, 변경이력 v2.17 | `:806-807`, `:825`, `:832-853`, `:1132-` |
| 4 | `opal/tools/memory-tool/memory_tool.py` | BE | `@header` description 갱신 + 변경이력 v2.2 라인 | `:1-30` |

#### 3.3.2 문서 설계

**(1) `memory-learning.md` 라이프사이클 표 — `candidate` 행 추가**

`:33`(`active`) 직후에 삽입한다. 순서 근거: `README.md:262-266`의 기존 표가 `active` → `candidate` → `promoted` → `superseded` → `dead` 순이므로 두 문서의 행 순서를 일치시킨다.

| 상태 | 의미 | 진입 트리거 | 도구 동작 |
|------|------|-----------|----------|
| `candidate` | 승격 검토 대기. 아직 성숙 판정 전인 기록 | `append --status candidate` — improve-tool `record --scope local`의 memory-tool 위임 등 | 인덱스 행 유지. `promote_candidates` 산출 대상은 아니다(`active` 한정) → 성숙 판정 시 `promote`, 진부화 시 `update --status dead\|superseded` |

근거: 상태 도입 경위는 `memory_tool.py:16-17` v1.1 변경이력, `promote_candidates`의 `active` 한정은 `memory_tool.py:855`, enum 실재는 `memory.schema.json:54`.

**(2) `memory-learning.md` — orphan 정리 경로 [MUST] 노트 신설**

기존 `:38` [MUST] 노트 **직후**에 두 번째 노트를 추가한다. `:38` 본문과 기존 4행 서술은 **수정하지 않는다**(R-3 AC "기존 4행의 서술은 R-2 반영분 외 diff 0"). `:24` 무손실 원칙 본문도 무변경 — 그 문장이 규정하는 것은 "진부화 정리"이고, 본 경로는 "깨진 참조의 복구"라는 별개 범주이기 때문이다.

추가할 노트 초안:

> **[MUST] 참조 무결성과 고아 행 정리**: 인덱스 행의 `file` 포인터가 가리키는 본문 `.md`가 실재하지 않으면 자가검토(`review`)가 `violations`에 **`memory_file_missing`**으로 표면화한다. 이런 고아 행은 `promote`(본문 필수)와 `delete`(상태 가드)가 조합되어 어떤 명령으로도 도달할 수 없었으므로, `delete --orphan --ref <지식 귀착처>`를 정식 경로로 둔다. `--orphan`은 **본문이 실재하면 `memory_file_exists`로 거부**하므로 위 무손실 가드를 우회하지 않는다. 정리 시 행의 `summary`가 `.memory_provenance.log`에 함께 기록된다(데이터 무손실). 상태를 임의 조작(`update --status superseded`)해 삭제를 강행하는 우회는 감사 추적을 오염시키므로 금지한다.
>
> **[MUST] 확인 불가 ≠ 부재**: `file` 포인터를 `memory/` 하위로 **해석할 수 없는** 행(경로 탈출 등)은 별도 어휘 **`memory_file_unresolvable`**로 표면화되며, `promote`와 `delete --orphan`이 이를 거부한다 — 본문이 `memory/` 밖에 실재할 수 있어 부재를 확인할 수 없기 때문이다. 이런 행의 올바른 처방은 삭제가 아니라 **포인터 수리**다(`dead`/`superseded` 행은 종전대로 무플래그 `delete`로 제거할 수 있다).

**(3) `README.md` 변경 4곳**

| 위치 | 변경 |
|------|------|
| `:180-185` review 응답 예시 | `violations` 예시에 `memory_file_missing` 엔트리 1건 표기 |
| `:189` 배열 설명 | `- violations: 스키마 위반(요약 길이>80·enum 위반 등) + **참조 무결성 위반(`memory_file_missing` — `file` 포인터가 가리키는 본문 `.md` 부재)**` |
| `:193-205` delete 절 | 시놉시스에 `[--orphan --ref <귀착처>]` 추가 + 가드 표(판정 ①의 4×2 상태 전이 표 축약) + provenance 기록 설명 |
| `:270-293` 에러 코드 표 | `memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable` **3행** 추가 (`delete_requires_dead_or_superseded` 행 인접) |
| `:271` 기존 `memory_file_not_found` 행 | **[정정 3]** 의미 컬럼을 "경로 해석은 **성공**했으나 `memory/<file>.md`가 부재 (promote/delete `--with-file`)"로 한정 — 해석 불가 케이스는 `memory_file_unresolvable`로 분리됐음을 반영 |
| `:302-309` 변경이력 | `\| v2.2 \| 096 \| … \|` 1행 추가 (**이 파일의 기존 3컬럼 스키마 `버전\|태스크\|내용` 유지** — 컬럼 추가는 범위 밖) |

**(4) `tools.md` 변경 4곳**

| 위치 | 변경 |
|------|------|
| `:806-807` delete 커맨드 | `--orphan --ref` 예시 1줄 추가 |
| `:825` review 블록 예시 | 설명 주석에 참조 무결성 검사 포함 명시 |
| `:832-853` 에러 코드 표 | **3행** 추가 (`memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable`) + 기존 `memory_file_not_found` 행 의미를 "해석 성공 + 본문 부재"로 한정 (**정정 3**) |
| 변경이력 | `\| v2.17 \| 2026-08-20 HH:mm \| … (096) \|` |

> `:763`·`:772`의 "9서브명령"·"커맨드 (9 서브명령)" 표기는 **변경 불필요** — 판정 ①이 서브명령 수를 유지하기 때문 (선택 근거의 실증).

**(5) `memory_tool.py` @header**

- `:6` `description`: 말미에 `delete --orphan --ref로 본문 부재 고아 행 정리(본문 실재 시 거부 — 무손실 가드 유지, provenance summary 보존)·review 참조 무결성 검사(memory_file_missing)` 추가.
- 변경이력 블록(`:14-22`)에 v2.2 라인 추가:
  ```
  v2.2 2026-08-20 참조 무결성 검사 + 고아 행 정리(096) — build_review_block(doc, json_path)로
                  file 포인터 실재 검사 추가(violations memory_file_missing), delete --orphan/--ref
                  신설(본문 실재 시 memory_file_exists / 경로 해석 실패 시 memory_file_unresolvable
                  거부 — 확인 불가는 부재가 아님), promote의 해석 불가 반환도 동일 코드로 정합,
                  ERROR_CODES 3종 추가(23→26)
  ```

> [MUST] `docs/CONVENTIONS.md` §@header 규칙: "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다."

**(6) docs/ 갱신 판정 결과 — 갱신 불요**

| 후보 문서 | 판정 | 근거 |
|----------|------|------|
| `docs/ARCHITECTURE.md:81`·`:391` | 불요 | memory-tool 행이 서술하는 것은 도구 역할·서브명령 종수(9)·CLOSE 자동 연결이며 전부 불변 |
| `docs/PROJECT.md:224` | 불요 | `.opal/MEMORY.json` 레지스트리 행("변경은 memory-tool만 수행") 불변 |
| `docs/CONVENTIONS.md` | 불요 | 신규 코딩 패턴·네이밍 규칙 도입 0건 (도구 내부 계약 변경) |
| `docs/BACKEND.md` / `docs/FRONTEND.md` | 해당 없음 | 프로젝트에 부재 (`docs/` 실측: ARCHITECTURE·CONVENTIONS·PROJECT·SECURITY + architecture-diagram/·proposals/·backup/) |

> `opal/core/references/opal-harness.md:288`은 memory-tool 서브명령 목록에 **078에서 소멸한 `migrate`를 여전히 나열하는 선재 drift**를 갖고 있다. 본 태스크가 만든 결함이 아니고 TASK 범위 밖이므로 **수정하지 않고 §9 R-6으로 보고**한다 ([MUST] `opal/core/PRINCIPLES.md` §3: "Don't refactor what isn't broken." — 인접 개선 금지).

#### 3.3.3 환경 변경

해당 없음.

#### 3.3.4 배치/마이그레이션

해당 없음. 단, `install-mac.sh:220-232` `strip_deploy_md_recursive`가 배포 시 `.md`의 `## 변경이력` 이하를 제거하므로 **`.md` 파일은 배포본 diff 0 대상이 아니다**.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| QA-015 | R-3 AC "enum과 문자 단위 일치" + **H-7** | 산출물 검사 | `memory-learning.md` 라이프사이클 표에서 파싱한 상태 값 집합 == `memory.schema.json` `$defs.memoryRow.properties.status.enum` 집합 (문자 단위, 5종) |
| QA-016 | R-3 AC "3열 채움" | 산출물 검사 | `candidate` 행의 의미·진입 트리거·도구 동작 3열이 모두 비어있지 않다 |
| QA-017 | R-3 AC + **H-9** | 산출물 검사 | `ERROR_CODES`의 신규 **3종**이 `README.md` 에러 코드 표와 `tools.md` 에러 코드 표에 모두 등재. 총 종수 26 |
| QA-018 | R-3 AC "기존 4행 diff 0" | 회귀 테스트 | 기존 4개 상태 행의 3열 텍스트가 변경 전과 동일 (R-2 반영은 별도 노트로 분리했으므로 표 본문 무변경) |

---

### F-004: RED 증거 + 전건 회귀 + install

#### 3.4.1 파일 변경 계획

**신규 생성**: 없음 (신규 fixture 파일 0 — 079 선례 계승).

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 테스트 | `[T096/...]` 신규 3클래스 + 헬퍼 1종 + @header exports·변경이력 v1.3 | `:1-30`, `:98-116`, `:2515` |

#### 3.4.2 테스트 설계

**헬퍼 추가** (`_setup_populated()` `:98-116` 직후)

```python
def _setup_populated_orphan(tmp_dir: pathlib.Path, skip=("improve_candidate.md",)) -> pathlib.Path:
    """_setup_populated와 동일하되 skip에 든 본문 .md를 생성하지 않는다 —
    인덱스 행은 있고 본문이 없는 고아 행 상태를 만든다(096 R-1/R-2).
    """
```

- `improve_candidate.md`를 기본 skip 대상으로 삼는 근거: 대응 인덱스 행이 `status: "candidate"`(`fixture_doc_populated.json`)여서 **실환경 2건과 동일한 상태값**이다 (092/094 교훈 — fixture가 실환경을 재현해야 한다).
- `prefs_graduated.md`(status `promoted`) skip 변형으로 QA-007을 구성한다.

**신규 클래스 3종**

| 클래스 | 프리픽스 | 담당 TS |
|--------|---------|---------|
| `TestReviewReferenceIntegrity` | `[T096/L1-R1]` | QA-001~QA-005 |
| `TestDeleteOrphan` | `[T096/L1-R2]` | QA-006~QA-014, **QA-024, QA-025** |
| `TestLifecycleDocParity` | `[T096/L1-R3]` | QA-015~QA-018 |

**실환경 레이아웃 재현 [MUST]**: `TestDeleteOrphan` 중 최소 1건(QA-006 권장)은 `_install_json()`(`.opal/` 하위 배치)을 사용해 실환경 왕복 경로(`.opal/MEMORY.json` ↔ `.opal/memory/*.md`)를 재현한다.
> 근거: `.opal/MEMORY.json` 히스토리 092 result — "실환경 검증이 pytest 전건 GREEN 상태에서 결함을 2회 검출 — 두 번 다 fixture가 실환경 구조(왕복 경로·깊이)를 재현하지 않은 것이 원인."

**mock 금지 [MUST]**: 전 케이스 `_run()`/`_run_raw()` subprocess 실행. `unittest.mock` import 금지 — [MUST] `opal/core/PRINCIPLES.md` §4: "Don't fake it" / `test_memory_tool.py:8` @header 규약.

**RED 증거 요건**: Step 1 완료 시 `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` 실행 결과에서 **신규 케이스가 FAIL(exit≠0)**, 기존 163건은 pass임을 stdout 그대로 기록한다 — [MUST] `red-first.md` §1. QA-018(기존 4행 diff 0)·QA-011(무플래그 불변) 등 **불변식 가드 케이스는 RED 시점에도 통과할 수 있다**(078 @header 선례 명문화).

**테스트 불변성 [MUST]**: Step 2 이후 `test_memory_tool.py`의 신규 케이스를 수정하지 않는다 — `red-first.md` §3. 수정이 필요하다고 판단되면 블로커로 보고한다.

#### 3.4.3 환경 변경

해당 없음. 실행 인터프리터는 `~/.opal/.venv/bin/python`(Python 3.14, pytest 9.1.0) — 시스템 `python3`에는 의존성이 없다.

#### 3.4.4 배치/마이그레이션

**install 재배포** (Step 6, TEST 전건 통과 후):

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework && ./scripts/install-mac.sh
diff ~/.opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/memory_tool.py   # 기대: 출력 0줄
```

> `.md` 배포본은 `strip_deploy_md_recursive`(`install-mac.sh:1116`, `:1579`)로 변경이력이 제거되므로 diff 대상에서 제외한다.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| QA-019 | R-4 AC "전건 GREEN" + H-8/H-10 | 회귀 테스트 | `pytest opal/tools/memory-tool -q` → 기준선 163 + 신규 전건 pass, 실패 0. 소요가 기준선(18.03s) 대비 유의미하게 증가하지 않음 |
| QA-020 | R-4 AC "install diff 0" + H-8 | 산출물 검사 | install 후 `diff ~/.opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/memory_tool.py` 출력 0줄 |
| QA-021 | 완료기준 (5) + H-6 | 통합 테스트 | 실환경 `.opal/MEMORY.json`에 **소스 직접 실행**으로 `review`(**읽기 전용**) → `memory_file_missing` **정확히 2건**(`fixture 실환경 미재현 시 결함 통과`, `PM이 도구 계수를 grep으로 대체해 오판했다`), `memory_file_unresolvable` **0건**(3행 전부 정상 경로) |
| QA-022 | H-5 | 회귀 테스트 | `state-tool` 테스트 스위트 전건 pass (CLOSE 히스토리 자동 연결이 memory-tool을 subprocess 호출하므로) |
| QA-023 | 완료기준 (5) + H-6 + G-1 | 통합 테스트 | `.opal/MEMORY.json` **사본**에 **소스 직접 실행**(install 이전이므로 배포본 `run.sh` 사용 금지)으로 `delete --orphan --ref …` 리허설 → 2건 제거 성공 + provenance 기록. **원본 무변경**(리허설 전후 해시 동일) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (RED) | F-001·F-002·F-003 | 1 | opal-test-agent | 단독 | [MUST] `red-first.md` §2 작성자≠구현자. RED 증거 없이 Phase 2 진입 금지 |
| 2 (GREEN·코드) | F-001 | 2 | opal-be-agent | 순차 | 동일 파일(`memory_tool.py`) — Step 3과 병렬 불가 |
| 2 (GREEN·코드) | F-002 | 3 | opal-be-agent | 순차 | Step 2 완료 후 (`_resolve_memory_file` 술어 공유 확인 필요) |
| 3 (문서) | F-003 | 4 | opal-task-agent | 순차 | Step 3 확정된 계약을 문서에 반영 |
| 4 (검증) | F-004 | 5 | opal-test-agent | 순차 | 전건 회귀 + 실환경 검출·리허설 |
| 5 (배포) | F-004 | 6 | opal-task-agent | 순차 | [MUST] D-3 — TEST 전건 통과 이후 |

**agent 배정 근거 (프롬프트 요구 판정)**

| Step | 배정 | 근거 |
|------|------|------|
| 1 | `opal-test-agent` | [MUST] `opal/core/references/harness/red-first.md` §2: "RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다." — `opal-be-agent`/`opal-task-agent` 2택보다 이 [MUST]가 우선한다 |
| 2, 3 | **`opal-be-agent`** | (i) 변경 내용이 Python CLI의 **가드 술어·에러 계약·응답 스키마·락 내 부수효과 순서**로 전형적 백엔드 로직 엔지니어링이며, `op-dev-plan` SKILL.md §agent 필드 배정 규칙의 `BE → opal-be-agent` 매핑에 직접 대응한다. (ii) **프로젝트 선례**: 동일 파일(`memory_tool.py`)의 직전 기능 추가(079)에서 `test_memory_tool.py` @header 변경이력 v1.2가 "구현(GREEN)은 opal-be-agent 별도 담당 (red-first.md §2)"으로 배정을 명시했다. 동일 대상·동일 작업 유형이므로 선례를 따른다. `opal-task-agent`(범용)는 도메인 판단이 필요 없는 문서·설정 작업용이므로 무손실 가드 설계 판단이 걸린 이 단계에 부적합 |
| 4 | `opal-task-agent` | 대상 3종(`memory-learning.md`·`README.md`·`tools.md`)이 전부 프레임워크 참조/도구 문서다. SKILL.md §agent 배정 규칙의 "문서 → PM 직접"은 **`docs/` 갱신 Step 전용**이며(§docs/ 갱신 Step 자동 생성 규칙), 본 Step은 `docs/` 대상이 아니다(§3.3.2 (6) 판정: docs/ 갱신 불요). 도메인 판단 없는 정합 반영이므로 범용 워커가 적합 |
| 5 | `opal-test-agent` | 전건 회귀 + 실환경 검증. 검증 2원화(생성자≠평가자) 유지 — Step 2·3 구현자와 분리 |
| 6 | `opal-task-agent` | install 실행 + diff 검증. 환경 영역 기본 배정(SKILL.md §agent 배정 규칙 "환경 → opal-task-agent") |

### 4.2 실행 체크리스트

> 총 **6개** Step | Phase **5개** | 실행 모드: **복잡**

#### Step 1: RED 시나리오 테스트 작성 + RED 증거 기록
- [x] 완료
- **소속 기능**: F-001, F-002, F-003 (RED 트랙)
- **영역**: 테스트(BE)
- **agent**: `opal-test-agent` (mode: red)
- **파일**: `opal/tools/memory-tool/tests/test_memory_tool.py`
- **작업 내용**:
  1. 헬퍼 `_setup_populated_orphan(tmp_dir, skip=…)` 추가 (`_setup_populated()` `:98-116` 직후, 동일 스타일)
  2. `TestReviewReferenceIntegrity` `[T096/L1-R1]` — QA-001~QA-005
  3. `TestDeleteOrphan` `[T096/L1-R2]` — QA-006~QA-014 + **QA-024·QA-025(G-3 `None` 반환 3경로 전수)**. QA-006은 `_install_json()`(`.opal/` 레이아웃)으로 실환경 왕복 경로 재현 [MUST]. QA-024는 `memory/` **밖에 실재하는 본문 파일**을 만든 뒤 `file: "memory/../<name>.md"` 행으로 겨냥해야 한다 — 이 배치가 없으면 결함이 재현되지 않는다
  4. `TestLifecycleDocParity` `[T096/L1-R3]` — QA-015~QA-018. `TestTaskNumberDocs`(`:2515-2562`)의 `_REPO_ROOT` 문서 읽기 패턴 재사용
  5. @header `exports`에 3클래스 추가 + 변경이력 v1.3 라인(096)
  6. `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` 실행 → **RED 증거(exit≠0 + 실패 목록) stdout 원문 기록**
- **완료 기준**: 신규 케이스가 FAIL하고 기존 163건은 pass. RED 증거 stdout이 산출물에 남는다. mock/patch/MagicMock 0건(`grep -c "mock\|patch\|MagicMock"` = 0). 불변식 가드 케이스(QA-011·QA-018)는 RED 시점 통과 허용
- **테스트**: QA-001~QA-018, QA-024, QA-025 (자기 자신)
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: F-001 구현 — `build_review_block` 참조 무결성 검사
- [x] 완료
- **소속 기능**: F-001
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**:
  1. `build_review_block(doc)` → `build_review_block(doc, json_path=None)` (`:828`) + 독스트링 갱신
  2. 행 루프 `:852` 직후에 `memory_file_missing` 검사 블록 삽입 (§3.1.2 코드)
  3. 호출부 **9곳 전부** `json_path` 전달 — `:909`, `:990`, `:1118`, `:1194`, `:1229`, `:1376`, `:1389`, `:1432`, `:1443`
- **완료 기준**: QA-001~QA-005 GREEN. `grep -c "build_review_block(doc)" memory_tool.py` == 0 (호출부 누락 0건 — H-1 결정론 확인). 기존 163건 회귀 0
- **테스트**: QA-001, QA-002, QA-003, QA-004, QA-005
- **실행 방법**: sub-agent
- **의존**: Step 1 (RED 증거 확보 후 — [MUST] `red-first.md` §1)

#### Step 3: F-002 구현 — `delete --orphan --ref` 정식 정리 경로
- [x] 완료
- **소속 기능**: F-002
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**:
  1. `ERROR_CODES`(`:105-160`)에 `memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable` **3종** 추가 — 총 **23종 → 26종** (기존 코드 삭제·개명 0건)
  2. `cmd_delete()` `:1352-1357` 가드 분기 교체 (§3.2.2) — `else` 분기 3줄은 원본 문자 그대로 보존
  3. `:1365` 직후 provenance 기록 블록 추가(락 안, `summary=` 포함)
  4. 응답에 `orphan` 항상 + orphan 시 `reason`/`ref`/`provenance_logged` 추가
  5. `main()` delete 파서(`:1531-1537`)에 `--orphan`(store_true)·`--ref` 등록
  6. **[개정 v1.2 / 정정 3]** `cmd_promote()` `:1165-1166`의 `err("promote", "memory_file_not_found", path=file_field)` → `err("promote", "memory_file_unresolvable", file=file_field)` (**1줄**). `:1167-1168` `not mem_file.exists()` 분기는 **문자 그대로 무변경**
- **완료 기준**: QA-006~QA-014 + **QA-024·QA-025** GREEN. 상태 전이 표(4 status × 3 본문상태 = 12칸) 중 **신규 허용 칸이 정확히 1개**임을 QA-008·QA-009·QA-011·QA-024·QA-025로 확인. `_resolve_memory_file()` `None` 반환 3경로 전수가 `memory_file_unresolvable`로 거부됨. **G-3 가드 형태 검사(함수 범위 한정, 결정론)** 통과. `ERROR_CODES` 총 26종. 서브명령 수 9 불변(`--help` 검사 `test_memory_tool.py:132`·`:1399` 통과). 기존 163건 회귀 0
  > **[개정 v1.2] G-3 가드 형태 검사 — 함수 범위 한정 결정론 기준**
  > ```bash
  > ~/.opal/.venv/bin/python - <<'EOF'
  > import inspect, importlib.util
  > s = importlib.util.spec_from_file_location('mt', 'opal/tools/memory-tool/memory_tool.py')
  > m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
  > src    = inspect.getsource(m.cmd_delete)
  > orphan = src.split('if orphan:')[1].split('else:')[0]          # orphan 가드 블록만 절취
  > assert 'if mem_file is None:'      in orphan, 'G-3 조기 반환 부재'
  > assert 'memory_file_unresolvable'  in orphan, 'G-3 거부 코드 부재'
  > assert 'is not None and'       not in orphan, 'G-3 결함 패턴(None 동시판정) 잔존'
  > print('G-3 guard OK')
  > EOF
  > ```
  > **교체 근거**: 종전 기준 `grep -c "mem_file is not None and mem_file.exists()" == 0`은 **오탐**이었다 — 실측 결과 해당 패턴은 파일 전체에서 `:1372` **1건**이며, 그것은 `--with-file` 블록으로 orphan 가드가 아니고 방향도 안전측(파일이 실재할 때만 `unlink`)이며 **096 변경 범위 밖**이다. 종전 기준을 그대로 두면 (a) 완료 기준이 영구 미충족이거나 (b) 워커가 선재 코드를 건드리게 유도한다 — [MUST] `opal/core/PRINCIPLES.md` §3: "Touch only what the plan names." 위반. 새 기준은 `cmd_delete`의 `if orphan:` 블록만 절취해 검사하므로 `:1372`를 구조적으로 배제하며, **부재 검사(negative)에서 존재 검사(positive)로 방향을 전환**해 "조기 반환이 실제로 있는가"를 직접 확인한다.
- **테스트**: QA-006~QA-014, QA-024, QA-025, QA-026
- **실행 방법**: sub-agent
- **의존**: Step 2 (동일 파일 순차 수정 + `_resolve_memory_file` 술어 일치 확인 — 검출 어휘 2종과 처분 어휘 2종이 일치해야 한다)

#### Step 4: F-003 규범·도구 문서 정합 + 변경이력
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/memory-learning.md`, `opal/tools/memory-tool/README.md`, `opal/core/references/tools.md`, `opal/tools/memory-tool/memory_tool.py`(@header만)
- **작업 내용**:
  1. `memory-learning.md` — 라이프사이클 표 `:33` 직후에 `candidate` 행 삽입, `:38` 노트 직후에 orphan 정리 [MUST] 노트 신설. **기존 4행·`:24`·`:38` 본문 무변경**
  2. `README.md` — `:180-185` review 예시, `:189` 배열 설명, `:193-205` delete 절(가드 표 포함), `:270-293` 에러 코드 2행
  3. `tools.md` — `:806-807` delete 커맨드, `:825` review 예시 주석, `:832-853` 에러 코드 2행
  4. `memory_tool.py` `:6` @header description + `:14-22` 변경이력 v2.2 라인
  5. 변경이력 3건 (§4.4 변경이력 계획 표)
- **완료 기준**: QA-015~QA-018 GREEN. 라이프사이클 표 상태 집합 == 스키마 enum 5종. 신규 에러 코드 **3종**이 README·tools.md 양쪽 표에 등재. 각 문서 변경이력에 KST 일시 + `(096)` 포함 1행 추가. `tools.md:763`·`:772`의 "9서브명령" 표기 무변경
- **테스트**: QA-015, QA-016, QA-017, QA-018
- **실행 방법**: sub-agent
- **의존**: Step 3 (확정된 CLI 계약을 문서에 반영해야 하므로)

#### Step 5: 전건 회귀 + 실환경 검출·리허설
- [x] 완료
- **소속 기능**: F-004
- **영역**: 테스트
- **agent**: `opal-test-agent`
- **파일**: (검증 전용 — 소스 무변경)
- **작업 내용**:
  1. `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` — 전건 GREEN 확인 + 소요 시간을 기준선 18.03s와 비교
  2. `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool -q` — H-5 하위 소비자 회귀
  3. **실환경 검출(읽기 전용)**: 소스 직접 실행으로 `.opal/MEMORY.json`에 `review` → `memory_file_missing` 2건 확인
  4. **실환경 리허설(사본)**: `.opal/MEMORY.json` + `.opal/memory/`를 임시 디렉토리에 복사 → **소스 직접 실행**(`~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py delete --file <사본>/MEMORY.json --title … --orphan --ref …`) 2회 → 제거 성공·provenance 기록 확인 → **원본 해시 전후 동일 확인**
  > **[MUST] 실행 도구 규율**: Step 5는 install **이전**이므로 배포본 `~/.opal/tools/memory-tool/run.sh`를 쓰지 않는다 — 그 시점의 배포본에는 `--orphan`이 없어 `unrecognized arguments`로 실패한다. 본 Step의 전 항목은 **소스 직접 실행**(`~/.opal/.venv/bin/python opal/tools/memory-tool/memory_tool.py`)으로 수행한다. 배포본 실행 검증은 Step 6 소관이다 (게이트 G-1).
  5. **실제 제거는 실행하지 않는다** — 캡틴 판단 사항. 실행 명령문만 보고에 제시
- **완료 기준**: QA-019·QA-021·QA-022·QA-023 전건 통과. 실패 0. 원본 `.opal/MEMORY.json` 무변경(해시 동일). 테스트 파일 수정 0건([MUST] `red-first.md` §3)
- **테스트**: QA-019, QA-021, QA-022, QA-023
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: install 재배포 + 배포본 정합 확인
- [x] 완료
- **소속 기능**: F-004
- **영역**: 환경
- **agent**: `opal-task-agent`
- **파일**: `scripts/install-mac.sh` 실행 (스크립트 자체 무변경)
- **작업 내용**:
  1. `./scripts/install-mac.sh` 실행
  2. `diff ~/.opal/tools/memory-tool/memory_tool.py opal/tools/memory-tool/memory_tool.py` → 0줄
  3. 배포본 실동작 확인: `~/.opal/tools/memory-tool/run.sh review --file <프로젝트>/.opal/MEMORY.json` → `memory_file_missing` 2건
  4. `.md` 배포본은 변경이력 strip 대상이므로 diff 대상에서 제외(`install-mac.sh:220-232`) — 대신 본문 절 존재 여부만 grep 확인
- **완료 기준**: QA-020 통과. `memory_tool.py` diff 0줄. 배포본 `run.sh`로 신규 경로 실동작
- **테스트**: QA-020
- **실행 방법**: sub-agent
- **의존**: Step 5 — [MUST] TASK.md §확정된 설계 방향 D-3: "배포는 TEST 전건 통과 이후에 수행한다. 검증 미완 규칙이 전역 홈으로 퍼지는 창을 만들지 않는다"

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | [MUST] `red-first.md` §1 — RED 증거 없이 GREEN 진입 금지 |
| Step 2 → Step 3 | 동일 파일(`memory_tool.py`) 순차 수정. 추가로 Step 3의 `--orphan` 술어가 Step 2의 검출 술어와 일치해야 하므로(H-4) 선행 확정 필요 |
| Step 3 → Step 4 | 문서가 기술할 CLI 계약(플래그명·에러 코드·응답 필드)이 Step 3에서 확정된다 |
| Step 4 → Step 5 | Step 5의 QA-015~QA-018이 Step 4 산출물을 대상으로 한다 |
| Step 5 → Step 6 | [MUST] D-3 배포 순서 — 검증 미완 상태의 전역 홈 배포 금지 (H-8) |
| Step 2 ∦ Step 3 | 병렬 불가 — 동일 파일 충돌 |
| Step 4 부분 ∥ 없음 | 3개 문서는 동일 에이전트 내 순차 처리(파일 충돌 없으나 계약 어휘 일관성을 한 컨텍스트에서 보장) |

> **Short Task Step 수 권장(5개 이하) 초과 판정**: 6 Step. Full Task 에스컬레이션을 **검토 후 불필요로 판정**한다 — 초과분 1개는 설계 복잡도가 아니라 절차 게이트(install 분리, D-3)에서 나온 것이고, 미해결 분석 과제가 없으며(코드 분석 완료·미확정 2건 판정 완료), 변경 모듈이 단일 도구에 국한된다.

### 4.4 변경이력 계획

> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
> 일시는 작업 시점에 `node ~/.opal/tools/date/date.js datetime`으로 실측 취득한다 (`memory-learning.md:18` 타임스탬프 취득 규칙).

| # | 파일 | 현재 최신 | 새 버전 | 표 컬럼 스키마 | 변경내용 초안 (`(096)` 포함) |
|---|------|----------|--------|--------------|---------------------------|
| 1 | `opal/core/references/harness/memory-learning.md` | v1.4 (`:104`) | **v1.5** | `버전 \| 날짜 \| 내용` | 라이프사이클 표에 `candidate` 행 추가 — 스키마 `status` enum 5종과 정합(종전 4행, `memory.schema.json:54` 대비 누락). `delete --orphan --ref` 고아 행 정리 경로 [MUST] 노트 신설 — `review` `memory_file_missing` 검출 → 정리 왕복, 본문 실재 시 `memory_file_exists` 거부로 무손실 가드 불가침, `summary` provenance 보존, 상태 임의 조작 우회 금지 명문화. 기존 4행 서술·`:24` 무손실 원칙 diff 0 (096) |
| 2 | `opal/tools/memory-tool/README.md` | v2.1 (`:309`) | **v2.2** | `버전 \| 태스크 \| 내용` (일시 컬럼 없음 — 기존 스키마 유지) | `review` 참조 무결성 검사 반영 — `violations`에 `memory_file_missing`(`file` 포인터 실재 검사) 추가, 응답 예시·배열 설명 갱신. `delete --orphan --ref` 절 신설(가드 전이 표·provenance 기록). 에러 코드 표 **3행** 추가(`memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable`). `violations` 어휘 2종 분리 명시(`memory_file_missing` = `--orphan` 정리 가능 / `memory_file_unresolvable` = `--orphan` 거부·포인터 수리 필요). `promote`의 해석 불가 반환 코드를 `memory_file_not_found` → `memory_file_unresolvable`로 정합(동작 불변, 라벨만 정밀화). 서브명령 9종 불변 |
| 3 | `opal/core/references/tools.md` | v2.16 (`:1132-` 표 말미) | **v2.17** | `버전 \| 일시 \| 변경내용` | memory-tool 섹션 정합 — `delete` 커맨드에 `--orphan --ref` 예시 추가, `review` 출력 예시 주석에 참조 무결성 검사 명시, 주요 에러 코드 표에 `memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable` **3행** 추가 + `memory_file_not_found` 의미를 "해석 성공 + 본문 부재"로 한정. 커맨드 종수(9) 무변경 (096) |
| 4 | `opal/tools/memory-tool/memory_tool.py` | v2.1 (`:20-22`) | **v2.2** | @header 내 변경이력 라인 | `build_review_block(doc, json_path)` 참조 무결성 검사(`memory_file_missing` / `memory_file_unresolvable` 2종 분리) + `delete --orphan/--ref` 신설(본문 실재 시 `memory_file_exists`, 경로 해석 실패 시 `memory_file_unresolvable` 거부) + ERROR_CODES **3종** 추가(23→26) (096) |
| 5 | `opal/tools/memory-tool/tests/test_memory_tool.py` | v1.2 (`:27-30`) | **v1.3** | @header 내 변경이력 라인 | 096 RED-first 블록 추가 — 참조 무결성·고아 행 정리·문서 파리티 3클래스(QA-001~QA-018·QA-024·QA-025). 신규 픽스처 신설 없음(`fixture_doc_populated.json` in-test 가공). 구현(GREEN)은 opal-be-agent 별도 담당 (red-first.md §2) (096) |

### 4.5 변경 대상 파일 총괄 (5개)

| # | 경로 | 영역 | 변경 유형 | 핵심 변경 | 완료 기준 |
|---|------|------|----------|----------|----------|
| 1 | `opal/tools/memory-tool/memory_tool.py` | BE | 수정 | `build_review_block` 시그니처 + 검사 / 호출부 9곳 / `cmd_delete` orphan 분기 + provenance / `cmd_promote` 어휘 1줄 정합 / ERROR_CODES **3종** / argparse 2옵션 / @header | QA-001~QA-014 + QA-024·QA-025 GREEN, `mem_file is not None and mem_file.exists()` 패턴 잔존 0건(G-3), `build_review_block(doc)` 잔존 0건, 서브명령 9 불변, 기존 163 회귀 0 |
| 2 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 테스트 | 수정 | 헬퍼 1 + 클래스 3(`[T096/...]`) + @header | RED 증거 확보(Step 1) → 최종 전건 GREEN(Step 5), mock 0건, 신규 fixture 파일 0 |
| 3 | `opal/core/references/harness/memory-learning.md` | 문서 | 수정 | `candidate` 행 + orphan [MUST] 노트 + v1.5 | 표 상태 집합 == 스키마 enum 5종(QA-015), `candidate` 3열 채움(QA-016), 기존 4행 diff 0(QA-018) |
| 4 | `opal/tools/memory-tool/README.md` | 문서 | 수정 | review·delete 절 + 에러 코드 **3행** + v2.2 | 신규 에러 코드 **3종** 등재(QA-017), 라이프사이클 표(이미 5행) 무변경 |
| 5 | `opal/core/references/tools.md` | 문서 | 수정 | delete 커맨드·review 예시·에러 코드 **3행** + v2.17 | 신규 에러 코드 **3종** 등재(QA-017), "9서브명령" 표기 무변경 |

> **미변경 확정**: `opal/tools/memory-tool/schema/memory.schema.json`(TASK 제약 4), `scripts/install-mac.sh`(실행만), `docs/*`(§3.3.2 (6) 판정), `opal/core/references/opal-harness.md`(선재 drift — §9 R-6 보고만), `.opal/MEMORY.json`(실제 제거는 캡틴 판단).

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 본문 부재 행이 `review` `violations`에 검출된다 | QA-001 | `memory_file_missing` 엔트리 수 == 본문 부재 행 수 |
| F-001 | 정상 상태에서 위양성 0 | QA-002 | 본문 전건 실재 시 `memory_file_missing` 0건 |
| F-001 | 기존 violations 4종 반환 형태 불변 | QA-003 | 4종 엔트리의 키 집합·값·상대 순서가 변경 전과 동일 |
| F-001 | 전 변경 명령의 자동 첨부 review에서도 검출 (호출부 누락 0) | QA-004 | 6개 명령 응답 전부에서 검출 + `grep -c "build_review_block(doc)"` == 0 |
| F-001 | 해석 불가 행을 **별도 어휘**로 검출하며 memory/ 밖을 stat하지 않음 | QA-005 | `_resolve_memory_file` None 반환 행이 `memory_file_unresolvable`(≠ `memory_file_missing`)로 검출 |
| F-002 | 고아 행이 단일 명령으로 정리된다 (`update --status` 불요) | QA-006, QA-007, QA-014 | `delete --orphan --ref X` 1회 호출로 `ok:true` + 행 제거 |
| F-002 | **무손실 가드 우회 불가 — 본문 존재 행은 status 무관 거부** | QA-008, QA-009 | `memory_file_exists`, 인덱스·본문 모두 불변 |
| F-002 | 귀착처 미기재 정리 거부 | QA-010 | `orphan_ref_missing`, 행 불변 |
| F-002 | 무플래그 `delete` 동작 완전 불변 | QA-011 | 본문 부재 `candidate`에 무플래그 → `delete_requires_dead_or_superseded` |
| F-002 | 제거 사유·귀착처·요약이 감사 로그에 남는다 | QA-012 | `.memory_provenance.log`에 `delete-orphan` 행 + `ref=`·`summary=` |
| F-002 | 원자성·잔여 0 | QA-013 | `.tmp`/`.lock` 0건, `show` `ok:true` |
| F-002 | **확인 불가 행은 삭제하지 않는다 (G-3, P0)** | **QA-024** | 경로 탈출 + `memory/` 밖 본문 실재 시 `memory_file_unresolvable` 거부, 인덱스 행·본문 파일 모두 불변 |
| F-002 | **`None` 반환 3경로 전수 방어 (G-3, P0)** | **QA-025** | resolve 예외·경로 탈출·빈 `file` 전부 거부 + 행 불변. 삭제로 이어지는 경로 0 |
| F-002 | **`promote` 어휘 정합 — 확인 불가 ≠ 부재 (정정 3)** | **QA-026** | 해석 불가 행의 `promote`가 `memory_file_unresolvable` 반환. 해석 성공+부재 행은 `memory_file_not_found` 유지. `review`·`promote`·`delete --orphan` 3명령 어휘 일치 |
| F-003 | 라이프사이클 표 == 스키마 enum 5종 | QA-015 | 문자 단위 집합 동일 |
| F-003 | `candidate` 행 3열 채움 | QA-016 | 의미·진입 트리거·도구 동작 전부 비공백 |
| F-003 | 신규 에러 코드 문서 파리티 | QA-017 | README·tools.md 표에 **3종** 등재(총 26종 정합) |
| F-003 | 기존 4행 diff 0 | QA-018 | 4개 상태 행 3열 텍스트 불변 |
| F-004 | 전건 GREEN + 성능 비퇴행 | QA-019 | 163+신규 전건 pass, 소요 ≈ 18s 대 |
| F-004 | 배포본 정합 | QA-020 | `memory_tool.py` diff 0줄 |
| F-004 | 실환경 검출 실증 | QA-021 | `.opal/MEMORY.json` review → `memory_file_missing` 2건 |
| F-004 | 하위 소비자 무영향 | QA-022 | state-tool 스위트 전건 pass |
| F-004 | 실환경 정리 리허설 + 원본 보전 | QA-023 | 사본에서 2건 제거 성공 + 원본 해시 전후 동일 |

### 5.2 회귀 테스트

- [ ] 기존 **163 passed / 25 subtests** 전건 유지 (기준선 대비 실패 0)
- [ ] `TestReviewAmbient`(`:~770`) — review 4키 존재 계약 불변
- [ ] `TestReviewRoleBoundary`(`:869-932`) — `promote_candidates`는 active만, 졸업지 단정 필드 없음, `cleanup_candidates`는 dead/superseded
- [ ] `TestErrorCodesJson`(`:1893-1921`) — 구 코드 부재 + 필수 코드 존재 + 무손실 가드 코드 보존. **신규 3종 추가 후에도 통과**(집합 포함/부재 검사이며 총 개수를 단정하지 않음). `ERROR_CODES` 총 **23종 → 26종**
- [ ] **[개정 v1.2] `promote` 어휘 변경(정정 3) 회귀 영향 — 실측 0건**. `memory_file_not_found`를 참조하는 테스트 4곳을 전수 확인했고, 어느 것도 `promote`의 `mem_file is None` 분기를 밟지 않는다:

| 테스트 위치 | 성격 | 실제로 도달하는 분기 | 영향 |
|-----------|------|-------------------|------|
| `:536-552` `test_promote_nonexistent_title_rejected` | 미존재 **제목** promote | `row_not_found`(`:1157-1158`) — `mem_file` 조회 전에 종료. 게다가 두 코드를 `assertIn`으로 **택일 허용** | 없음 |
| `:942-956` `test_promote_path_traversal_rejected` | `--title`에 `../` | `_path_has_traversal(title)`(`:1147-1148`) → `row_not_found`. 에러 코드 단정 없이 `ok:false`만 검사 | 없음 |
| `:1038-1046` `TestErrorCodes.REQUIRED_CODES` | `ERROR_CODES` 키 **존재** 검사 | 키 자체 — `memory_file_not_found`는 2번째 분기가 계속 사용하므로 **잔존** | 없음 |
| `:1182-1217` `test_delete_with_file_path_traversal_rejected` | **`delete`** `--with-file`, `file: "../sensitive.md"` | `"../sensitive.md"`는 스키마 패턴 `^memory/[^/].*\.md$` **불일치** → `load_document`가 `schema_validation_failed`(허용 목록에 포함). promote 미관여 | 없음 |

- [ ] `TestSkeleton::test_all_eight_subcommands_registered`(`:132`) / `:1399` — 서브명령 9종 유지
- [ ] `TestAtomicWrite`(`:1927`) — 실패 시 원본 불변 + 잔여 0
- [ ] `TestUpdateBackCompat` / `TestUpdateKindHistory` / `TestUpdateHistoryLossless` — 079 트랙 무영향
- [ ] `state-tool` 스위트 — CLOSE 히스토리 자동 연결(subprocess 호출) 무영향 (H-5)
- [ ] 무플래그 `delete` 4개 상태 × 본문 존재/부재 8칸 전이표 중 7칸 결과 불변

### 5.3 코드/문서 품질

- [ ] [MUST] `docs/CONVENTIONS.md` §@header 규칙 — `memory_tool.py`·`test_memory_tool.py` @header description·변경이력 라인 갱신
- [ ] [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 — 5개 파일 전부 KST 일시 + `(096)` 포함(파일별 기존 컬럼 스키마 준수)
- [ ] [MUST] `opal/core/PRINCIPLES.md` §3 — 계획이 지목하지 않은 인접 코드 미수정 (`opal-harness.md:288` 선재 drift 미접촉 확인)
- [ ] [MUST] `opal/core/PRINCIPLES.md` §2 — 신규 헬퍼 함수 0개, 신규 서브명령 0개, 신규 응답 배열 0개
- [ ] 표준 라이브러리 전용 유지 (`memory_tool.py:24-33` import 목록 무변경)
- [ ] Python 파일 snake_case 네이밍 — 신규 파일 0이므로 해당 없음
- [ ] `code-scan validate` 통과 (@header 커버리지)
- [ ] 검출 토큰과 처분 토큰 어휘 일치 (`memory_file_missing` 단일 어휘 — citation-rules §7.1 영역 간 용어 일관성)

### 5.4 보안

- [ ] 경로 탈출 방어 유지 — `--orphan` 경로도 `_resolve_memory_file()`(`:812-815` memory/ 화이트리스트)만 사용하며 임의 경로 stat/unlink 없음 (QA-005)
- [ ] `--orphan`은 파일을 **삭제하지 않는다** (본문 부재가 전제). 파일 삭제 경로는 기존 `--with-file`뿐이며 화이트리스트 통과 후에만 `unlink` (`:1371-1373`)
- [ ] `--ref` 값은 로그에만 기록되고 경로로 해석되지 않는다 (경로 주입 표면 없음)
- [ ] provenance 로그 쓰기 실패가 명령 실패로 전파되지 않으며(`except Exception: pass`), 예외 메시지로 경로를 노출하지 않는다
- [ ] 하드코딩된 토큰·시크릿 0건 (신규 코드에 자격증명 없음)
- [ ] 실환경 `.opal/MEMORY.json`은 Step 5에서 **읽기 전용**으로만 접근하며 파괴적 조작은 사본에서만 수행 (H-6)
- [ ] `.gitignore` 영향 없음 (신규 산출 파일 없음 — `.memory_provenance.log`는 기존 경로)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | **복잡** (6개 이상) |
| 변경 파일 수 | 5개 | **복잡** (4개 이상) |
| 모듈 범위 | 도구 1(코드+테스트) + 프레임워크 참조 문서 2 | **복잡** (다중) |
| 작업 유형 | 결함 수정 + 소규모 기능 추가(플래그 1) | 단순 |
| 외부 의존성 | 없음 (표준 라이브러리, 신규 패키지·API 0) | 단순 |
| **실행 모드** | **복잡** | 3개 기준 해당 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 ─ [A1] opal-test-agent (mode: red)        Step 1        ← RED 증거 게이트
             │
Batch 2 ─ [A2] opal-be-agent                      Step 2 → 3    ← 동일 파일, 단일 에이전트 내 순차
             │
Batch 3 ─ [A3] opal-task-agent                    Step 4        ← 문서 3종 정합
             │
Batch 4 ─ [A4] opal-test-agent                    Step 5        ← 검증 2원화 (A2와 분리)
             │
Batch 5 ─ [A5] opal-task-agent                    Step 6        ← install (TEST 통과 후)
```

**그룹핑 근거**:
1. **파일 충돌 방지**: Step 2·3은 `memory_tool.py` 동일 파일 → 반드시 같은 에이전트(A2)에 배치.
2. **검증 2원화**: A1(RED 작성)·A4(검증)은 A2(구현)와 분리 — [MUST] `red-first.md` §2 + 생성자≠평가자.
3. **병렬 없음**: 전 Step이 선행 산출물에 의존하므로 병렬화 여지가 없다. 병렬을 억지로 만들면 H-4(술어 불일치)·H-8(배포 순서)이 실현된다.

### C-2. 스킬 요구사항

| 에이전트 | 스킬 | 상태 |
|---------|------|------|
| A1 | `op-dev-execute` (RED 서브트랙) + `opal/core/references/harness/red-first.md` | 기존 |
| A2 | `op-dev-execute` | 기존 |
| A3 | `op-dev-execute` (문서 영역) + `docs/CONVENTIONS.md` §변경이력 | 기존 |
| A4 | `op-dev-test` (BE 모드) | 기존 |
| A5 | 스킬 불요 — 스크립트 실행 + diff | — |

**갭 판별**: 신규 스킬 후보 없음. 동일 패턴이 3개 이상 Step에 반복되지 않으며(문서 정합만 Step 4 단일), 전 작업이 기존 스킬로 커버된다.

### C-3. 도구 요구사항

| 도구 | 용도 | 설치 상태 |
|------|------|----------|
| `~/.opal/.venv/bin/python` (3.14) | 실행 인터프리터 — 시스템 python3에는 의존성 부재 | 기존 |
| `pytest` 9.1.0 | 회귀·시나리오 실행 | 기존 |
| `~/.opal/tools/date/date.js` | 변경이력 KST 일시 취득 ([MUST] `memory-learning.md:18`) | 기존 |
| `scripts/install-mac.sh` | 재배포 (Step 6) | 기존 |
| `~/.opal/tools/memory-tool/run.sh` | 배포본 실동작 확인 (Step 6) | 기존 |
| `state-tool` | 파이프라인 행 상태 갱신 | 기존 |

신규 설치 0건.

### C-4. 테스트 전략

| 계층 | 내용 | 명령 |
|------|------|------|
| L1 (단위·계약) | QA-001~QA-018 + QA-024·QA-025 — subprocess 실 프로세스, 실 fixture. mock 금지 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool -q` |
| L1 (문서 파리티) | QA-015~QA-017 — repo 문서 직접 파싱 (`TestTaskNumberDocs` 패턴) | 동상 |
| L2 (하위 소비자) | QA-022 — state-tool 스위트 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool -q` |
| L2 (실환경) | QA-021 검출(읽기 전용) / QA-023 리허설(사본) | 소스 직접 실행 |
| L3 (배포본) | QA-020 — install 후 diff 0 + `run.sh` 실동작 | `diff` + `run.sh review` |

**RED 게이트**: Step 1 종료 시 `exit≠0` 증거 stdout 기록 → Step 2 진입 조건. [MUST] `red-first.md` §3에 따라 Step 2 이후 테스트 파일 수정 금지.

**TEST-SCENARIO.md 관계**: 본 PLAN의 TS-NNN은 PLAN 내부 설계 시나리오다. `TEST-SCENARIO.md`는 PM+캡틴 페어가 별도 작성하며(본 워커 출력 범위 밖), §리스크 가설 표 H-1~H-11과 §1.2 F-001~F-004가 그 Block B(③기능커버·④리스크커버) 입력이 된다 (→ D-5 §1.6 (b)).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python 3.14 표준 라이브러리 전용 CLI (`argparse`/`json`/`pathlib`/`re`) | — (`trailofbits/modern-python`은 uv·ruff·async 패턴 중심이라 본 태스크의 표준 라이브러리 전용 단일 파일 CLI에 적용 항목 없음 — 미적용) |
| 테스트 | pytest 9.1.0 + `unittest.TestCase` + subprocess 실 프로세스 | `op-dev-test` (BE 모드) |
| 설계 | JSON Schema draft-07 (`memory.schema.json` — SSOT, 무변경) | — |
| 문서 | Markdown 규범 문서 + 변경이력 표 | `docs/CONVENTIONS.md` §변경이력 |
| FE | 해당 없음 | — (FE 화면 0건 → §3.N.2 화면 서브섹션 미작성) |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| context7 | **미사용** — 외부 라이브러리 0건(표준 라이브러리 전용). 최신 API 조회 대상 없음 |
| shadcn MCP | **미사용** — FE 화면 없음 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py` | 변경 대상. `:105-160` ERROR_CODES / `:797-816` `_resolve_memory_file` / `:828-870` `build_review_block` / `:1062-1125` `cmd_update` / `:1126-1211` `cmd_promote` / `:1328-1377` `cmd_delete` / `:1384-1401` `cmd_review` / `:1531-1537` delete 파서 |
| D-2 | 소스 | test_memory_tool.py | `opal/tools/memory-tool/tests/test_memory_tool.py` | 회귀 기준선(163 passed) + 프리픽스 규약 `[T045/T078/T079]` + `_setup_populated`(`:98`)·`_install_json` 헬퍼 + `TestTaskNumberDocs`(`:2515`) 문서 파리티 패턴 |
| D-3 | 설계 | memory.schema.json | `opal/tools/memory-tool/schema/memory.schema.json` | `:54` status enum 5종 — R-3 정합 기준. `$defs.memoryRow.required`에 `file` 포함, `file` 패턴은 형태만 강제(실재 강제 불가) → 검사가 런타임 코드에 있어야 하는 근거. **무변경** |
| D-4 | 설계 | 기억과 학습 규범 | `opal/core/references/harness/memory-learning.md` | R-3 변경 대상. `:24` 무손실 원칙 / `:31-36` 라이프사이클 4행 / `:38` delete 가드 [MUST] / `:35-36` `cleanup_candidates`→`delete` 계약(판정 ② 근거) / `:18` 타임스탬프 취득 |
| D-5 | 설계 | RED-first 규칙 | `opal/core/references/harness/red-first.md` | `:§1` RED 증거 의무 / `:§2` 작성자≠구현자 / `:§3` 테스트 불변성 / `:§1.6` 선작성 트랙(PM 별도 수행 — 본 워커 범위 밖) |
| D-6 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | `:242-246` 변경이력 작성 의무 / `:211-216` @header 규칙 / `:248-253` 배포 경계 / `:12`·`:18` 네이밍 |
| D-7 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | `:224` `.opal/MEMORY.json` 레지스트리 행(불변 확인) / 폴더 구조맵 |
| D-8 | 설계 | OPAL 헌법 | `opal/core/PRINCIPLES.md` | §2 Simplicity(판정 ① 탈락 근거) / §3 Surgical Changes(인접 개선 금지) / §4 Don't fake it(mock 금지) |
| D-9 | 설계 | memory-tool README | `opal/tools/memory-tool/README.md` | `:168-189` review 계약 / `:193-205` delete / `:258-266` 라이프사이클(**이미 5행 — candidate 포함**, 불일치 방향 확정 근거) / `:270-293` 에러 코드 표 |
| D-10 | 설계 | 도구 레퍼런스 | `opal/core/references/tools.md` | `:763-853` memory-tool 섹션 — `:825` review 계약 예시 / `:832-853` 에러 코드 표 / `:763`·`:772` "9서브명령" 리터럴(판정 ① 근거) |
| D-11 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 원칙 / §2 인용 포맷 / §4 PLAN 단계 인용 의무 / §7.1 영역 간 용어 일관성 |
| D-12 | 소스 | install 스크립트 | `scripts/install-mac.sh` | `:220-232` `strip_deploy_md`/`strip_deploy_md_recursive`(`.md` 변경이력 strip → diff 0 대상 한정 근거) / `:1116`·`:1163-1167` tools 배포 |
| D-13 | 설계 | 하네스 도구 표 | `opal/core/references/opal-harness.md` | `:288` memory-tool 행 — `migrate` 잔존 선재 drift 확인(**미접촉**, §9 R-6) |
| D-14 | 소스 | 프로젝트 메모리 실측 | `.opal/MEMORY.json` + `.opal/memory/` | 인덱스 3행 중 본문 부재 2행(둘 다 `candidate`) 실측 / 히스토리 092·094 result의 fixture 실환경 재현 교훈 |
| D-15 | 설계 | 아키텍처 | `docs/ARCHITECTURE.md` | `:81`·`:391` memory-tool 서술(불변 확인 — docs/ 갱신 불요 판정 근거) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | `build_review_block` 호출부 9곳 중 일부 누락 시 **침묵 실패**(기본값 `None`이 검사를 건너뛰므로 TypeError 없음) | F-001 | 중 | Step 2 완료 기준에 `grep -c "build_review_block(doc)" == 0` 결정론 검사 포함 + QA-004가 6개 명령 응답 전수 확인 (H-1) |
| R-2 | `--orphan`이 무손실 가드 우회로가 되어 살아있는 지식이 삭제됨 | F-002 | **높음** | 본문 실재 시 무조건 `memory_file_exists` 거부(status 무관) + **경로 해석 실패 시 `memory_file_unresolvable` 거부**. QA-008·QA-009가 4개 status × 본문 존재를, **QA-024·QA-025가 `None` 반환 3경로**를 전수 검증. `else` 분기 3줄을 원본 문자 그대로 보존해 비교 가능성 확보. **[개정 v1.1]** 개정 전 설계는 `None`을 통과시켜 이 리스크를 실현했다(G-3) — 조기 반환 구조로 재발 불가하게 교정 (H-2) |
| R-3 | 본문 부재가 "타 머신 미동기화"인데 조기 제거 → 지식 영구 유실 | F-002 | **높음** | ① `--ref` 필수화로 귀착처 판단 강제 ② provenance에 `summary` 보존(무손실) ③ 실환경 실제 제거는 캡틴 판단 사항으로 분리(Step 5는 리허설까지만) (H-3) |
| R-4 | 검출 술어(`review`)와 처분 술어(`delete --orphan`)가 갈려 2차 고착 발생 | F-001, F-002 | 중 | 양쪽 모두 `_resolve_memory_file()`(`:797-816`) 단일 함수 사용을 구현 규약으로 못박음. QA-006이 검출→정리 왕복을 한 시나리오에서 확인 (H-4) |
| R-5 | **역방향 고아** — 인덱스에 없는 `memory/*.md` 실측 2건(`.opal/memory/노션_액티비티_지속_업데이트_규칙.local.md`, `.opal/memory/follow-up-code-scan-phase2.md`)은 본 태스크 후에도 미검출로 남는다 | 범위 밖 | 낮음 | **후속 보고만.** TASK.md §범위는 "인덱스 행의 `file` 경로 실재 여부"로 한정된다. 반대 방향 검사 추가는 별건 태스크로 제안 (H-11) |
| R-6 | **선재 drift 미접촉** — `opal/core/references/opal-harness.md:288`이 078에서 소멸한 `migrate`를 memory-tool 서브명령으로 여전히 나열 | 범위 밖 | 낮음 | **보고만.** [MUST] `opal/core/PRINCIPLES.md` §3 "Don't refactor what isn't broken" — 본 태스크가 만든 결함이 아니고 TASK 범위 밖 |
| R-7 | Step 수 6이 Short Task 권장(5)을 초과 | F 전반 | 낮음 | §4.3 말미에 에스컬레이션 검토·불필요 판정 근거 기재. 초과분은 절차 게이트(install 분리)에서 발생한 것이며 설계 미해결 과제 없음 |
| R-8 | README 변경이력 표에 일시 컬럼이 없어 `docs/CONVENTIONS.md` §변경이력의 `YYYY-MM-DD HH:mm` 요구와 형식이 어긋난다 | F-003 | 낮음 | **본 태스크에서 컬럼 스키마를 바꾸지 않는다**([MUST] PRINCIPLES §3). 각 파일 기존 스키마 준수 + 태스크 번호 `(096)`은 전 파일 공통 기재. 표 스키마 통일은 별건으로 제안 |
| R-9 | `.md` 배포본은 변경이력 strip으로 소스와 diff가 0이 아니어서 AC (6)을 오판할 수 있다 | F-004 | 낮음 | diff 0 검증 대상을 `memory_tool.py`(strip 비대상)로 명시 한정. `.md`는 본문 절 존재 여부 grep으로 확인 (Step 6 작업 내용 4) (D-12) |
| R-10 | install을 TEST 전에 실행해 미검증 규칙이 전역 홈에 배포 | F-004 | 중 | Step 6이 Step 5에 하드 의존. [MUST] TASK D-3 / 095 계승 (H-8) |
| R-11 | 하위 소비자(state-tool CLOSE 자동 연결, improve-tool) 응답 파싱 파손 | F-001, F-002 | 중 | 응답 최상위 키 4종·`delete` 기존 5키 전부 보존(추가만). QA-022가 state-tool 스위트로 실증 (H-5) |
| R-12 | 실환경 `.opal/MEMORY.json` 손상 | F-004 | **높음** | Step 5는 원본에 대해 `review`(읽기 전용)만 수행하고, 파괴적 조작은 사본에서만. 리허설 전후 원본 해시 동일 확인을 완료 기준에 포함 (H-6) |
| **R-13** | **[개정 v1.2 정정] 선재 잔존 고착 클래스** — **`{active, promoted, candidate} × 해석 불가`** 행은 `promote`(`:1164-1166` 거부)·무플래그 `delete`(`:1355-1357` 상태 가드 거부)·`delete --orphan`(`memory_file_unresolvable` 거부) 모두에 막힌다. `cmd_update`(`:1062-1125`)는 `--status`/`--summary`/`--new-title`만 다루므로 **`file` 필드를 고칠 명령이 없다**. **범위 주의**: `dead`/`superseded` × 해석 불가 행은 **고착이 아니다** — 무플래그 `delete`의 `else` 분기가 `mem_file`을 조회하지 않고 상태만 보므로 종전대로 허용되며(§판정 ① 전이표 "해석 불가 / dead·superseded / 허용(불변)"), `--with-file`은 `memory/` 밖 파일을 건드리지 않는다(`:1372` 화이트리스트) | 범위 밖 | 낮음 | **선재 고착이며 096이 만들지도 넓히지도 않았다.** 근거: 세 거부 지점 중 둘(`:1355-1357` 상태 가드, `:1164-1166` promote 거부)과 `cmd_update`의 `file` 미지원이 **전부 096 이전부터 존재**했다 — 096 이전에도 이 행들은 도달 불가였다. 096이 추가한 `delete --orphan`은 이 집합을 **허용으로 바꾸지 않았을 뿐** 새로 막지 않았다. **096의 순효과는 개선이다**: 종전에는 `review`가 이 행을 전혀 표면화하지 못해 **침묵 고착**이었으나, 이제 `memory_file_unresolvable`로 **진단 가능**해졌다. ① 확인 불가 행은 지우는 것보다 남기는 편이 항상 안전하다(무손실). ② 올바른 처방은 삭제가 아니라 **포인터 수리**(`update --file` 신설)이며 이는 신규 기능 = 범위 밖 — [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement." ③ 실환경 도달 0건(`.opal/MEMORY.json` 3행 전부 정상 경로). **후속 태스크로 제안**하며 DONE.md 이월 항목에 기재한다 |
