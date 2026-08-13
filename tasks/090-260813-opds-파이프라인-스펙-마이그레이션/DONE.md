# DONE: 미전환 6 pilot 파이프라인 스펙 마이그레이션 — 10/10 완전 전환

> 완료일: 2026-08-13 18:01 KST | 태스크: 090 | 파이프라인: opds (agentic)
> 산출물: TASK.md · PLAN.md · TEST-SCENARIO.md · SCENARIO-GATE-1.md · SCENARIO-GATE-2.md · AGENTIC-LOG.md · DONE.md

---

## 1. 무엇을 해결했나

파이프라인 행 정의가 두 곳에 흩어져 있었다. 4개 pilot은 `references/pipeline.json`을 읽었고, 나머지 6개는 SKILL.md 마크다운 표를 파서로 긁었다(`build_rows_from_skill_md` — deprecated 표기를 단 채 여전히 주 경로였다).

이 분열은 세 가지 실해를 내고 있었다.

- **oppl·oppd는 태스크를 아예 시작할 수 없었다.** `init --rows-from .../SKILL.md`가 `skill_md_parse_error: header not found`로 하드 실패했다. 섹션 헤더(`## STATE.md 초기 생성`)와 표 헤더(`| # | Stage | 항목 |`)가 파서 정규식과 어긋난 탓이다.
- **registry `pipeline` 필드가 실제와 달랐다.** 확정 드리프트 6건 + 결측 1건. opsdd는 전면 상이했고 oppd는 필드 자체가 없었다.
- **`tools.md:152`는 이미 전환된 opp를 `.md`로 호출하라고 예시하고 있었다** — 지금도 틀린 명령이 문서에 살아 있었고, 복사하는 사람마다 구형 경로가 재도입될 수 있었다.

이제 **10/10 pilot이 단일 SSOT·단일 파싱 경로**를 쓴다. deprecated `.md` 파싱 경로의 호출자는 0건이다.

## 2. 왜 이 설계인가

| # | 결정 | 근거 |
|---|------|------|
| D-1 | 범위를 **행 구성 이관 + registry 정합**까지로 한정. 실행 스펙 필드(`agent`/`model`/`inputs`/`outputs`/`gate`)는 후속 | 후속 개선이 이 태스크를 기반으로 하므로 기반을 먼저 확정 |
| D-2·D-3 | 신규 6종에 죽은 `pm_gate` 배열을 만들지 않되, 기존 4종의 것도 이번엔 건드리지 않음 | 소비처 0인 데이터를 증식시키지 않는다. 제거는 `task_steps[].gate` 인라인 이관과 함께 |
| D-4 | **행 구성 전후 동등이 최우선 제약** | 마이그레이션은 형식 이관이지 파이프라인 변경이 아니다 |
| D-5 | SKILL.md 행 표를 삭제하지 않고 **미러로 존치** | 표 제거는 후속(SKILL.md 감량)의 범위 |
| D-7c | opsdd는 `meta.stages`에 `EXECUTE`를 쓰고 **산문 `EXECUTE-LOOP` 표기는 일절 건드리지 않음** | `EXECUTE-LOOP`은 Phase 이름, `EXECUTE`는 stage 값 — 다른 개념 계층이다. 개명하면 8파일 41곳이 연쇄 변경돼 문서 개편으로 변질된다 |
| D-7a | oppl은 `.md` init이 하드 실패하므로 **표 19행을 직접 baseline으로** 대조 | "전"을 파서로 뜰 수 없으니 행 정규식을 표 구간에 직접 적용해 기준값을 확보 |
| D-7b | oppd 행 구성은 **실사용 선례 8행 + 표준화 판단 3건 = 13행**으로 캡틴 확정 | `003-oppd-invest-stock/state.json`(완주 태스크)이 실재 baseline. 신규 설계가 아니라 관측 기반 |
| D-10 | 잔존 검증 범위를 **pilot SKILL.md 밖으로 확장** | 목표-커버 게이트 iteration 1의 gap — "검증하는 명제(pilot 10개)"가 "주장하는 명제(호출자 0건)"보다 좁았다 |

## 3. 무엇을 바꿨나

**신규 6** — `opal/skills/{opal-pilot-data-design, opal-pilot-gc, opal-pilot-write-tech, opal-pilot-sdd, opal-pilot-project-loop, opal-pilot-project-dev}/references/pipeline.json`
(각각 15 / 7 / 10 / 25 / 19 / 13 task_step)

**수정 11**

| 파일 | 변경 |
|------|------|
| 위 6종 `SKILL.md` | `--rows-from`을 pipeline.json으로 교체, 행 표 앞에 미러 주석, `[SSOT]` 오기술 정정, 변경이력 1행. oppd는 미러 표 13행 신설 |
| `opal/core/references/opal-skills-registry.json` | `pipeline` 10종 정합화(`meta.stages` 파생) + oppd `domain: dev` + v3.10.0 |
| `opal/core/references/tools.md` | 시놉시스 `<path-to-skill.md>` → `<path-to-pipeline.json>`, 실행 예시 경로 정정 |
| `opal/core/references/harness/task-process.md` | 행 원천 서술을 pipeline.json SSOT로 정정 |
| `opal/skills/op-task/SKILL.md` | 동일 정정 |
| `docs/CONVENTIONS.md` | §State 관리에 행 원천 규칙 1줄 + v1.2.0 |

**건드리지 않은 것 (의도)** — `opal/tools/state-tool/state_tool.py`·`state-tool/README.md`(도구 자신의 에러 메시지·분기 설명), opsdd 산문 `EXECUTE-LOOP` 17곳과 `execute-loop-guide.md`, oppl 섹션·표 헤더, `state-template.md:94`·`qa-standards.md:46`(캡틴이 범위 밖 확정).

## 4. 동작 증거

| 검증 | 결과 |
|------|------|
| **전후 동등 (D-4)** | 그룹 A 4종(opdd·opgc·opwt·opsdd) × 2 mode, before(`.md` 파싱) vs after(pipeline.json) `[(row_id, stage, item)]` **8/8 완전 동일** |
| oppl 3자 대조 | 표 19행 ↔ `task_steps` 19 ↔ after `rows[]` 19 — 특수문자(`—` U+2014, `✓` U+2713, 백틱, `{NN}`) 포함 문자 단위 동일 |
| oppd 3자 대조 | D-7b 13행 ↔ `task_steps` 13 ↔ after `rows[]` 13 완전 일치 |
| **하드 실패 해소** | before `skill_md_parse_error: header not found` → after **oppl `rows_count: 19` / oppd `rows_count: 13`**, 둘 다 exit 0 |
| 채택 | 10 pilot × 2 mode = **20회 init 전부 exit 0·`ok:true`·`schema_version: "1.1"`**, deprecation 경고 **0회** |
| 잔존 | 대상 6종 변경이력 밖 `rows-from.*SKILL.md` **0건** / 레포 전역(`opal/`·`docs/`·`README.md`) 구형 지시 **0건** |
| `spec-validate` | **10/10** `ok:true`·violations 0 |
| registry | `pipeline` 10/10이 `meta.stages`와 순서·원소 완전 일치, oppd `domain` 존재 |
| **무변경 보장** | opsdd `EXECUTE-LOOP` **17=17**, `execute-loop-guide.md`·외부 6파일·도구 2파일 `git status` **0줄** |
| 모드 축 | agentic `na` 집합 = `{사용자 확인, stage≠CLOSE}`. oppd는 id 2·12만 na, id 6·9(`…확정`)는 비대상 확인 |
| 배포 | install 후 배포본 pipeline.json 10건 소스와 `diff` 0, **배포 경로로 실제 init 성공**(oppl 19 / oppd 13 / opsdd 25) |
| TEST-SCENARIO | **18 Pass / 0 Fail** (S-17은 `[SUPERVISOR]` 캡틴 직접 수행 대기) |

목표-커버 게이트는 iteration 2에서 `verdict: pass`(①2·⑤2·⑥2, 평균 2.00, gaps 0). 결정론 파트 `coverage-check` exit 0(요구 9 / 기능 7 / 가설 18 / 시나리오 18)와 함께 tool-gated 두 증거를 충족했다.

## 5. 태스크가 만든 결함 1건 — 태스크 안에서 닫음

**S-16이 잡은 것**: `oppd SKILL.md:171`에 `mark --na`로 처리하라고 썼는데 **그런 플래그가 없다**. TASK.md D-7b 표준화 판단 ③이 존재하지 않는 CLI 기능을 전제했고, 그 전제가 지시문이 되어 install로 배포까지 나갔다.

실측: `mark --help`에 `--na` 없음 / 호출 시 `unrecognized arguments` / id 10~12 미완 상태의 CLOSE는 `stage_transition_violation`으로 차단 / 동작하는 경로는 `--force --note`뿐.

**처리**(캡틴 확정): 도구 구현이 아닌 **문서 정정**. TASK.md 제약 (a)("`state_tool.py` 소스 무변경")를 지켰다. 정정 → 재배포 → 재판정 Pass.

**정정문에 또 오류가 있었다**: "`--force`가 STATE.md에 의사결정 로그를 자동 기재한다"는 거짓이었다. 출처는 `opal-harness-agentic.md:109`이며 PM이 검증 없이 계승했다. 실측 결과 `mark`의 자동 기재는 `--auto-pass`(`state_tool.py:1525`)·`--as-worker --force`(`:1530`) 2트리거 전용이고, 평범한 `mark --force`는 `state.json` 행 `note`에만 남는다(`--note` 필수는 사실 — `note_required_for_force`). 실측 기준으로 재정정 후 3차 재배포했다.

## 6. PM 판단 기록 (agentic)

전체 궤적은 `AGENTIC-LOG.md` 43건. 요약하면:

- **게이트 8회 전건 Pass** — TASK / PLAN PM Gate(v2.3) / 목표-커버 iter1·iter2 / 행 4 집행 / PLAN PM Gate 재검증(v2.4) / Batch 1 / EXECUTE 완료 / TEST.
- **PLAN PM Gate를 재검증했다** — 세션 1의 판정은 v2.3 기준이었고 이후 v2.4(F-008·DEC-11·Step 8)가 신설돼 증거가 낡았다. 무효화하고 다시 걸었다.
- **워커 폴백 3건 사후 승인** — opsdd 변경이력 문구에서 `EXECUTE-LOOP` 리터럴 제외(계수 게이트 우선), opwt `[SSOT]` 블록 2문장 정정(동일 오기술), PLAN 버전 예측 드리프트 4건 자율 보정. 셋 다 워커가 자진 표면화했다.
- **Gate Fail 1건 재지시** — Step 8이 `--rows-spec` 언급을 삭제했다(PLAN §3.8.2 ③ 위반). `--rows-spec`은 폐기 대상이 아니며 `tools.md:84`·`:147`에 현존한다. 역할 분리 형태로 복원시켰다.
- **PLAN §3.5.2 ⑩(`rm -rf $WORK`) 보류** — before 스냅샷은 편집 후 재현 불가능하고 TEST가 소비한다. R-5가 요구하는 건 **레포** 잔류 0건이지 스크래치패드 삭제가 아니다.
- **S-17을 자동 통과시키지 않았다** — 070 사건(핵심 목표 미검증 완료)의 재발 방지.
- **TEST-SCENARIO를 PM이 사후 편집하지 않았다** — 평가자의 판정 기록이므로 생성자≠평가자 분리를 유지했다(§7 후속 권고 1은 §5로 이미 해소).

## 7. Known Issues

| # | 내용 | 상태 |
|---|------|------|
| 1 | **S-17 미검증** — 배포본 실사용(새 세션 `//oppl`·`//oppd`) 검증. 확인 포인트: init 성공 / 행 수 oppl 19·oppd 13 / deprecation 경고 미출력 | 캡틴 직접 수행 예정 |
| 2 | `opal-harness-agentic.md:109`의 "`--force` 우회 시 STATE.md 의사결정 로그 자동 기재"가 CLOSE `--force` 경로에서 미성립 (뒷부분 `--note` 필수는 사실) | 후속 분리 |
| 3 | 조건부 행 자동 `na` 미구현 — `state_tool.py:966`에 `conditional` 필드 처리는 있으나 na 연결 없음. oppd `--wbs` 경로가 `--force` 우회에 의존 | 후속 분리 |
| 4 | `tools.md:81` `--skill` enum에 `oppl`·`opdd` 누락 | 범위 밖(기존), 후속 |

## 8. 파급 — 다음 태스크부터 달라지는 것

- **10/10 pilot이 pipeline.json 단일 경로**를 쓴다. 후속 개선(실행 스펙 필드 승격·도구 구동 전환)의 혜택이 40%가 아니라 100%에 닿는다.
- **oppl·oppd로 태스크를 시작할 수 있다.** 두 pilot은 그동안 `init` 자체가 불가능했다.
- **행 구성을 손으로 고치는 경로가 닫혔다.** SKILL.md 표는 미러이고 SSOT는 pipeline.json이며, `docs/CONVENTIONS.md` §State 관리가 이를 규칙으로 못 박았다.
- **registry `pipeline`이 파생값이 됐다.** `meta.stages`에서 파생하므로 드리프트가 구조적으로 재발하기 어렵다.
- 남은 이월: 실행 스펙 필드 승격(D-1) · 죽은 `pm_gate` 배열 정리(D-3) · SKILL.md 행 표 삭제·감량(D-5) · ANALYSIS PM Gate 제거(D-6).
