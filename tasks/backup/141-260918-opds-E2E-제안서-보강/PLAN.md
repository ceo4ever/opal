---
template: sdlc-v2
---
# PLAN: E2E 여정·조각 라이브러리 제안서 검토 지적 5건 반영

> 입력: [TASK.md](TASK.md) (ANALYSIS 없음 — opds Short profile. 근거 실측은 아래 `Decisions and contracts`의 인용이 소유한다)

## Approach

`docs/proposals/e2e-journey-fragment-library.md` 한 파일의 §2·§3·§4·§5·§9를 개정한다. 제안을 채택하거나 E2E 기능을 구현하지 않으며, 상태는 `검토`로 유지한다(C-2, `opal/core/references/harness/proposal-lifecycle.md` §상태 어휘:58 — "`제안` · `검토` · `적용완료` · `폐기` 4종만 쓴다. 앞의 둘은 `docs/proposals/`, 뒤의 둘은 `docs/proposals/archives/`에 둔다").

모든 Work item이 같은 파일을 바꾸므로 병렬화 이점이 없다. 실행 그룹을 순차(P1→P6)로 두고, 결정이 확정돼야 요약이 정확해지는 §2를 마지막 본문 작업(P5)에 둔다.

**code-scan 인용.** `code-scan search redaction`(7 file(s) 적중)이 `[util] redaction.py`의 @header를 "T05 증적 마스킹 — Authorization·Cookie·Set-Cookie 헤더와 URL query 비밀값을 저장 직전에 마스킹하고 §A.12 redaction 결과(artifact_path·redacted_fields·redaction_failed)를 반환한다. 저장 자체는 하지 않는다 — 호출자는 `lib/e2e/evidence.py` 단일 관문뿐이다"로 반환한다. 같은 조회가 `[util] evidence.py`를 "모든 증적 쓰기가 이 모듈을 거치고, 저장 직전 반드시 lib/e2e/redaction.py를 통과한다(CONTRACT.md §A.12)"로 보유한다. 이 두 결과가 D-9의 전제다 — 마스킹 보강 지점은 writer마다 흩어져 있지 않고 **단일 관문 하나**이므로, 제안서가 고칠 곳을 한 지점으로 지목할 수 있다.

**RED-first 비적용.** 근거: `opal/core/references/harness/red-first.md:15` — "탐색적 프로토타입, 시각 UI, 행위 불변 리팩터, 설정·문서: 구현 후 검증 가능", `:48` — "문서·설정처럼 RED 대상이 아닌 작업은 결정론 검사나 실제 적용 확인으로 검증한다". 실행 코드가 없어 실패를 관측할 테스트를 만들 수 없다. 대신 W-5가 결정론적 문서 구조 검사(grep + `git status --porcelain`)로 AC를 판정한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. §2 해법 요약 표에 **`착수 선행 조건`** 열을 신설한다 | 각 축 행이 선행 조건을 갖는지 한 칸에서 읽힌다. `재사용(조각)` 행 → Q-1 + 증적 마스킹 보강, `확장(driver wrapper)` 행 → Q-6 + driver 적합성 스위트. 선행 조건 없는 축은 `없음` | AC-1은 Q-1·Q-6·적합성 스위트 3건을 요구한다. 증적 마스킹 보강을 함께 싣는 것은 새 주장이 아니라 제안서 §4:100이 이미 "**이 구멍을 막는 것이 조각 도입의 선행 조건이다**"라고 선언한 사실을 요약 표에 반영하는 것이다 — 빼면 §2와 §4가 서로 다른 선행 조건 집합을 말하게 된다 |
| D-2. 열 신설 방식을 택하고 절 번호·쟁점 ID는 손대지 않는다 | §1~§9 번호와 Q-1~Q-9 ID가 현행 그대로 유지된다 | C-4. 열 추가는 재배치·재번호가 아니므로 기존 문서를 인용하는 후속 참조가 끊기지 않는다 |
| D-3. Q-1을 §9에서 **옮기지 않고** 등급 표기만 부여한다 | Q-1 행이 §9 자리를 지킨 채 `[착수 선행 조건]` 표기를 갖고, §2 표가 이를 참조한다 | C-4가 ID 재배치를 금지한다. 승격은 "위치 이동"이 아니라 "등급 표시"로 달성한다 |
| D-4. Q-1 승격 근거로 제안서 §1 표 1행(`:15`)을 본문에 인용한다 | Q-1 메모와 §2 선행 조건 칸이 "동결 spec은 사후 변경 불가 → 조각 전개가 동결 RED S-27에 걸리면 조각 기능 자체가 구현 불가"라는 인과를 명시한다 | AC-2. 근거는 문서 내부 실측 인용이며 외부 사실 추가가 아니다. `.opal/brain/pages/concept/e2e-frozen-spec-seeding-constraint.md` §귀결이 같은 제약을 "태스크 캡슐 안에서는 사후에 E2E 시나리오를 추가할 수 없다"로 보유한다 |
| D-5. §5 신선도 키를 `(여정 해시, 참조 조각 해시 집합, surface_id, 대상 commit, **선택 driver 정체(`driver`+`session_mode`)**, **달성 충실도**)`로 확장한다 | 재실행 생략 허용 조건이 4개에서 5개가 된다. 추가 조건: **이전 증적의 driver 정체가 이번 실행에서 선택될 정체와 같고, 달성 충실도가 이번 요구 충실도 이상일 것** | AC-3. `.opal/e2e/order.json`(§7)으로 순서를 바꾸면 선택되는 driver 정체가 달라지므로 키가 불일치해 이전 `pass` 증적을 재인용할 수 없다. 이 방어가 없으면 부분 driver가 1순위가 된 뒤에도 구 증적이 재인용된다 — `.opal/brain/pages/concept/e2e-candidate-order-and-fidelity-ownership.md` §왜 부분 driver를 1순위에 두지 않는가가 그 위험을 보유한다 |
| D-6. 충실도 비교는 정의를 복제하지 않고 `FIDELITY_ORDER`를 참조한다 | §5는 "달성 충실도 ≥ 요구 충실도" 판정만 적고 `mock`/`real-http`/`real-usage` 등급 정의 문장을 보유하지 않는다 | `opal/tools/test-tool/lib/scenario.py:119` `FIDELITY_ORDER = {"mock": 0, "real-http": 1, "real-usage": 2}`가 단독 소유이며, 제안서 §8 표가 이미 "충실도 정의 단일 소유. 이 제안은 참조만 한다"로 못박았다 |
| D-7. §5에 `api` profile 상한 비대칭을 주의로 남긴다 | "`api` profile은 상한이 `real-http`이므로 `real-usage`를 요구 충실도로 시드하면 키가 영원히 충족되지 않는다"를 한 문장으로 적는다 | `.opal/brain/pages/concept/e2e-candidate-order-and-fidelity-ownership.md` §충실도 — 태스크 127에서 `api` 표면에 `required_fidelity: real-usage`를 시드해 `all_surfaces_green` 도달 불가가 실제로 발생했다(B-5 이월). 충실도를 키에 넣는 이번 변경이 이 함정을 재현할 수 있어 같은 절에서 경고한다 |
| D-8. §4에 `value_ref`의 **적용 범위 한계**를 명시한다 | "`value_ref`는 조각 안 step만 덮는다. 조각 밖 본문에 직접 쓴 `fill`은 여전히 원문이 증적에 남는다"를 적는다 | AC-4. `value_ref`는 조각 계약(§4)의 규칙이므로 본문 연산에 효력이 없다 |
| D-9. §4에 증적 층에서 고쳐야 할 지점을 경로·줄번호로 적되 **코드는 이번 태스크에서 고치지 않는다** | `opal/tools/test-tool/lib/e2e/redaction.py`의 `SECRET_HEADER_NAMES`(`:26`)·`SECRET_QUERY_KEYS`(`:39`)가 **키 이름 집합**이고 `redact_value()`(`:175`)의 dict 분기(`:196`)가 그 집합에 든 키만 `MASK`로 바꾸므로, `{"kind": "fill", "target": "#pw", "value": "..."}` 레코드는 `value` 키가 어느 집합에도 없어 마스킹되지 않는다 — 이 판정 규칙을 보강해야 한다는 **요구**만 제안서에 기재한다 | AC-4 + TASK `Affected users and systems` 범위 제외(`opal/tools/test-tool/` 구현 코드). 실측 확인: `SECRET_QUERY_KEYS`는 `password`·`token`·`secret`·`session` 등을 담고 `value`를 담지 않는다 |
| D-10. §3 승격 판정을 **도구 게이트**로 규정한다 | "승격 자격은 `test-tool`의 exit 계약이 소유한 `pass` 증적 존재를 도구가 확인한 뒤에만 성립한다. 사람은 조각화 검토(같은 step 시퀀스의 `fragments/` 추출 여부)만 판단하며, **사람의 산문 판단만으로는 `docs/e2e/`로 승격할 수 없다**"를 §3 태스크·일회성 표 또는 그 직후에 적는다 | AC-5 + `~/.opal/PRINCIPLES.md:15` [MUST] — "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." 제안서 §6:128이 이미 "판정은 스킬이 하지 않는다 … 판정은 `test-tool`의 exit 계약(0/6/7/18/19/20)이 소유"로 같은 경계를 세웠으므로 새 규범이 아니라 그 경계를 승격 지점까지 잇는 것이다 |
| D-11. §9에 Q-5 결번 행을 신설하고 **취소선 + 처리 결과** 표기를 Q-4와 맞춘다 | Q-5 행의 쟁점 칸은 Q-4와 동일하게 취소선 처리한 원 제목(`import` 모드의 한계) 뒤에 `→ **결번(번호 이관, 내용 소실 없음)**`을 붙이고, 메모 칸이 이관 사실과 현 위치(Q-9)를 적는다 | AC-6. git 이력으로 확인됨: 커밋 `6d1c8f1`까지 Q-5는 "`import` 모드의 한계"였고, 커밋 `28e91e1`(ADD-1 반영)에서 Q-4가 Ego Lite로 재배정되며 구 Q-4(`.e2e/` 이름 충돌)·구 Q-5가 각각 Q-8·Q-9로 이관되어 Q-5 번호가 비었다. 따라서 "번호 결번(이력 확인 불가)"이 아니라 **확인된 번호 이관**으로 사실대로 적는다 |
| D-12. 제안서 상태 행과 변경이력 | `> 상태: 검토`를 유지하고, 수기 누적 변경이력 절을 만들지 않는다. 상단 `최종 갱신` 괄호 주석만 이번 개정 사유로 갱신한다 | C-2·C-5. 이력은 git과 태스크 기록이 소유한다 |

폐기한 대안: Q-1을 §9에서 삭제하고 §2로 옮기는 안은 C-4(ID 재배치 금지)를 깨고 Q-1을 인용한 후속 참조를 끊으므로 택하지 않았다.

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. §4 자격증명 처방을 증적 층까지 확장 | opal-task-agent | `docs/proposals/e2e-journey-fragment-library.md` §4 | D-8·D-9 적용. 기존 `value_ref` [MUST] 불릿(`:100`)에 (a) 적용 범위 한계(조각 밖 본문 `fill` 미포함), (b) 고쳐야 할 지점(`lib/e2e/redaction.py`의 `SECRET_HEADER_NAMES`·`SECRET_QUERY_KEYS` 키 이름 판정이 `fill` 레코드의 `value`를 덮지 못함 — 경로·줄번호 인용)을 덧붙인다. 코드는 수정하지 않는다 | 없음 | P1 | AC-4, C-1, C-3 |
| W-2. §3 승격 판정 주체·수단 명시 | opal-task-agent | `docs/proposals/e2e-journey-fragment-library.md` §3 | D-10 적용. "태스크와 일회성" 표의 `태스크 수행 중` 행 또는 그 직후에 승격 자격 판정 주체(`test-tool` exit 계약의 `pass` 증적)·수단·사람 산문 판단 불가를 [MUST]로 적고 §6:128의 판정 소유 경계를 인용한다 | W-1 | P2 | AC-5, C-1, C-3 |
| W-3. §5 신선도 키에 driver 정체·달성 충실도 추가 | opal-task-agent | `docs/proposals/e2e-journey-fragment-library.md` §5 | D-5·D-6·D-7 적용. 키 구성 문장(`:106`)에 선택 driver 정체와 달성 충실도를 넣고, 생략 허용 목록(`:108-109`)에 5번 조건을 추가한다. `order.json`(§7)으로 순서를 바꾸면 이전 `pass` 증적을 재인용할 수 없다는 판정을 명시하고, `FIDELITY_ORDER` 참조·`api` profile 상한 주의를 한 문장씩 남긴다 | W-2 | P3 | AC-3, C-1, C-3 |
| W-4. §9 쟁점 표 정비 — Q-1 등급 표기·Q-5 결번 행 | opal-task-agent | `docs/proposals/e2e-journey-fragment-library.md` §9 | D-3·D-4·D-11 적용. Q-1 행에 `[착수 선행 조건]` 표기와 §1 표 1행(`:15`) 근거를 넣고, Q-4와 Q-6 사이에 Q-5 결번 행을 취소선+처리 결과 표기로 삽입한다. 기존 Q-1~Q-9 ID와 순서는 바꾸지 않는다 | W-3 | P4 | AC-2, AC-6, C-1, C-3, C-4 |
| W-5. §2 요약 표에 착수 선행 조건 열 신설 | opal-task-agent | `docs/proposals/e2e-journey-fragment-library.md` §2, 상단 머리글 | D-1·D-2·D-12 적용. `축`/`내용` 2열 표에 `착수 선행 조건` 열을 추가하고 Q-1·Q-6·driver 적합성 스위트·증적 마스킹 보강을 해당 축 행에 배치한다. 선행 조건 없는 축은 `없음`. 상단 `최종 갱신` 괄호 주석을 이번 개정 사유로 갱신하고 `> 상태: 검토`는 그대로 둔다 | W-4 | P5 | AC-1, AC-2, C-1, C-2, C-5 |
| W-6. 결정론 검증 — AC·제약 관측 | opal-task-agent | (변경 없음 — 관측 전용) | 제안서에 대해 `grep -nE`로 다음 토큰의 존재를 확인한다 — `착수 선행 조건`(AC-1) · `Q-5`(AC-6) · `value_ref`와 `redaction.py`(AC-4) · `FIDELITY_ORDER`와 `order.json`(AC-3) · `S-27`(AC-2) · `사람`과 `승격`(AC-5). 이어 `grep -cE '^. Q-[0-9]'`에 준하는 계수로 쟁점 행이 9건이고 Q-1~Q-9 ID가 빠짐없이 나타남을 확인한다(C-4). `sed -n '3p'`로 `> 상태: 검토` 유지를 확인하고(C-2), `git status --porcelain`이 제안서와 태스크 캡슐 외 신규·수정 파일을 보이지 않음을 확인한다(C-1·AC-7). 변경이력 표제어(`변경이력`·`변경 이력`) 부재를 확인한다(C-5) | W-5 | P6 | AC-7, C-1, C-2, C-4, C-5 |

문서 판단: `docs/PROJECT.md` 레지스트리(`:268`)는 `docs/proposals/`를 Glob 단위로 이미 등재하고 있어 이번 개정으로 레지스트리 내용이 달라지지 않는다. TASK `Affected users and systems`도 레지스트리를 범위 제외로 둔다 — 따라서 문서 갱신 Work item을 만들지 않는다.

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. driver 정체를 신선도 키에 넣으면 재실행 생략이 사실상 성립하지 않을 수 있다 | §5의 존재 이유(범위 축소). driver 선택은 실행 환경(바이너리 유무·probe 결과)에 좌우되므로 같은 commit에서도 정체가 흔들릴 수 있다 | 제안 채택 시 신선도 키가 항상 불일치해 전수 재실행으로 회귀 — §1이 지목한 "매번 전수 재실행" 문제가 되살아난다 | W-3이 조건을 "정체 동일 **AND** 달성 충실도 ≥ 요구 충실도"로 적되, 정체 흔들림을 §5 본문에 한계로 명시한다. 해소책 설계는 이 태스크 범위 밖이며 제안 채택 시 후속 태스크가 소유한다 |
| H-2. §2 열 신설이 기존 표의 기계적 인용을 깬다 | C-4가 지키려는 "기존 문서를 근거로 인용하는 후속 참조" | 열 인덱스로 §2 표를 참조하던 문서가 있으면 어긋난다 | W-6이 `grep -rn "e2e-journey-fragment-library" --include='*.md'`로 외부 참조 지점을 관측하고, 절·ID 기반 참조만 존재함을 확인한다. 절 번호·쟁점 ID는 D-2에 따라 불변이다 |
| H-3. §4에 코드 수정 요구를 적는 것이 "코드를 고치는 태스크"로 읽힐 수 있다 | TASK 범위 제외(`opal/tools/test-tool/` 구현 코드) | EXECUTE 워커가 `redaction.py`를 실제로 수정해 C-1을 깬다 | W-1의 구체적 변경이 "코드는 수정하지 않는다"를 명시하고, W-6의 `git status --porcelain` 관측이 제안서 외 변경을 잡는다 |

## Release and recovery

- 적용 순서: P1→P6 순차. 단일 파일이므로 통합·병합 단계가 없다.
- 검증 범위: 결정론 검사만(RED-first 비적용, `harness/red-first.md:48`). W-6의 grep·`sed`·`git status --porcelain` 관측이 AC-1~AC-7과 C-1~C-5의 판정 근거이며, 여기서 검증이 종료된다. 실행 테스트·실제 연동 검증은 이 태스크에 없다.
- 배포·설치: 없음. `docs/proposals/` 아래 `.md` 1건 변경이며 도구·스킬 배포 경로를 타지 않는다.
- 실패 시: `git diff -- docs/proposals/e2e-journey-fragment-library.md`로 변경 전량을 확인하고 `git checkout -- docs/proposals/e2e-journey-fragment-library.md`로 개정 전 상태로 되돌린다. 커밋 전이면 이 한 줄로 완전 복구된다.
- 종료 확인: 되돌림 여부와 무관하게 파일 3행의 `> 상태:` 값이 `검토`로 남아 있어야 한다(C-2). `적용완료`·`폐기`로 바뀌면 `docs/proposals/archives/` 이관 대상이 되므로(`harness/proposal-lifecycle.md` §상태 어휘:58) 이 태스크의 실패로 판정한다.
