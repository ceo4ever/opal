# DONE: 파이프라인 스펙 중복정리 — SKILL.md 감량 + PM Gate SSOT 승격

> 완료일: 2026-08-14 11:44 KST | 태스크: 091 | 파이프라인: opd (agentic)
> 산출물: TASK.md · ANALYSIS.md · PLAN.md · TEST-SCENARIO.md · SCENARIO-GATE-1.md · SCENARIO-GATE-2.md · AGENTIC-LOG.md · baseline/ 20건 · DONE.md

---

## 1. 무엇을 해결했나

090이 파이프라인 **행 구성**을 `references/pipeline.json`으로 단일화했지만, 이관 범위를 "행 구성 + registry 정합"으로 한정했다(D-1). 그래서 SKILL.md에는 새 SSOT와 중복되거나 구형 좌표계를 쓰는 서술이 그대로 남았다.

세 층의 문제가 있었다.

- **중복**: 미러 표 134행이 `task_steps[]`와 100% 동일한데 어느 도구도 읽지 않았다. 표를 지키는 장치는 "편집 금지" 주석뿐이었다.
- **구형 좌표**: `--row N` 45건이 `docs/CONVENTIONS.md:228`의 금지 규정을 위반한 채 남아 있었다. 산문 `행 N` 36건도 미러 표를 좌표계로 전제했다.
- **미배선 SSOT**: `pm_gate`는 스키마에 정의됐지만 `state_tool.py`가 **읽지도 검증하지도 않았다**. 두 곳에 정의가 갈라진 채 이미 드리프트가 발생해 있었다(opd ⑥항 누락, opdw 표현 불일치).

이제 **PM Gate 정의가 `task_steps[].gate` 단일 SSOT**이고, `state-tool mark`가 이를 실제로 집행한다 — `artifacts` 존재를 결정론 검증해 미충족 시 거부하고, 통과 시 `checklist`를 stdout으로 반환한다. SKILL.md의 수동 사본은 전량 사라졌다.

## 2. 왜 이 설계인가

| # | 결정 | 근거 |
|---|------|------|
| **미결-1** | artifacts는 **정적 경로 + 글롭 2종만 적격**. `changed_files`·`GC-CONVENTION-*.md`는 삭제가 아니라 **checklist로 전치**(원문 보존) | `GC-CONVENTION-*.md`는 단순 glob이 아니라 **조건부 산출물**이다("대상 ≥1건 시 발동" — `opal-pilot-dev/SKILL.md:201` 외 3곳). 부재가 위반인지 정상인지 도구가 구분 불가하다. `changed_files`는 애초에 파일명이 아닌 논리 개념이며 state-tool은 git diff에 접근하지 않는다 |
| **미결-2** | opwt는 **정적 7건만 `--task-step` 전환**, 동적 4건은 `add-row --key` 규약으로 위임 + 규약 신규 저술 | pipeline.json 스펙에 모드 변형 개념이 없어, 3모드 확장은 spec v2 설계가 되어 태스크가 변질된다. 별도 이월 |
| **미결-3** | `gate`를 **init 시점에 row로 복사·state.json 영속** | `key`/`conditional`의 직접 확장(`state_tool.py:950-962` 선례). 재로드 방식은 state.json에 pipeline.json 경로가 없어 45+ 호출부에 인자 전파가 필요하다 |
| **미결-4** | `--force` 우회 **허용** + `gate_artifact_force` 의사결정 로그 강제 | 기존 가드 2종이 이미 force 우회를 허용한다(`:640`, `:697`). `--force`는 `--note` 필수라 이탈에 기록 비용이 붙는다 — 산문 조언과 구별되는 지점 |
| **미결-5** | `todo_mirror_hook.py`까지 **확장**(범위 확대) | R-12가 SKILL.md checklist 표를 제거하므로, 세션 주입이 없으면 정보가 순손실된다. Step 9 단독 배치로 롤백 경계 확보 |
| **순서** | 게이트 데이터(Phase 2)를 SKILL.md 편집(Phase 4)**보다 먼저** | 산출량 상한의 "동일 파일 2 Step 금지"를 지키려면 R-12를 각 pilot Step에 흡수해야 하고, 그 선행 조건이 R-9다. 논리 순서는 파일 내 편집 순서로 보존 |

**영구 차단 배제 3중 논증** (캡틴이 지정한 실패 모드): ① opdw `execute.pm_gate`의 2토큰이 전량 전치되어 `artifacts: []`가 되고 빈 배열은 즉시 return → 차단 자체가 미발생 ② 적격 규칙상 조건부·비-경로 토큰은 artifacts 진입 불가 → 재발 방지 ③ `--force --note` 최종 안전망.

## 3. 무엇을 바꿨나

**29 파일 수정 / 840 insertions / 438 deletions**

| 영역 | 파일 | 변경 |
|------|------|------|
| 스키마 | `pipeline-spec.schema.json`·`state.schema.json` | `gate` 객체 신설(양쪽 동형), 최상위 `pm_gate` 정의 삭제 |
| 도구 | `state_tool.py` | ERROR_CODES 5종, `validate_pipeline_spec()` gate 검사 4건, `_is_safe_artifact_token()`·`check_gate_artifacts()`·`build_gate_payload()` 신설, rows 빌더 2곳 gate 전파, `cmd_mark` 가드+decision 로그+응답 배선 |
| 도구 | `todo_mirror_hook.py` | `extract_gate_checklist()` 신설, 3-페이로드 분기(076·088·091 병존) |
| 스펙 | pipeline.json **9종** | `task_steps[].gate` **27건** — 이관 9건(opd4·opds2·opdw2 + opp2 중복 제외) / SKILL.md 표 이관 / 신규 저술 9건(opwt1·opsdd2·oppd3·oppl3). opgc는 PM Gate 개념 부재로 **무변경** |
| 스킬 | pilot SKILL.md **10종** | 미러 표 134행 삭제 · `--row` 45건 → `--task-step` · 산문 `행 N` 36건 → key 참조 · 도메인 치환값 중복 제거 · init 정본 1개화 · PM Gate 표 → 포인터 · opwt 동적 key 규약 신규 |
| 하네스 | `state-template.md`·`qa-standards.md` | 미러 표 의무 서술을 pipeline.json 원천 지시로 교체 |
| 규약 | `docs/CONVENTIONS.md` | §State 관리에 게이트 SSOT 규칙 + artifacts 적격 기준 + force 기록 의무 (v1.3.0) |
| 테스트 | `test_state_tool.py`·`test_todo_mirror_hook.py` | `TestTaskStepGate` 12건 · gate violation 4건 · `TestGateChecklistRelay` 2건 · ErrorCodes 39→44 |

**건드리지 않은 것 (의도)** — opsdd 산문 `EXECUTE-LOOP` 17곳(090 D-7c), 변경이력 표 전량, `--rows-spec` 경로, opgc pipeline.json, 기존 태스크 폴더 state.json.

## 4. 동작 증거

| 검증 | 결과 |
|------|------|
| **전후 동등 (최우선 제약)** | `diff -r baseline after` **20/20 무출력** — 10 pilot × 2 mode 행 구성 완전 불변 |
| **중간 동등** | F-003 완료 시점(코드 미변경) 재측정 **20/20 diff 0** — pipeline.json 편집이 행 구성을 훼손하지 않음을 조기 확정 |
| **회귀** | pytest **284 → 304 passed, 0 failed** (32 subtests). 린트 위반 15건은 `git show HEAD:` 대조로 전량 기존부채, 신규 회귀 0 |
| **RED-first** | RED 15 failed 확보(구현 2파일 `git diff` 0으로 작성자≠구현자 확인) → GREEN 전건 전환 |
| **게이트 집행 (배포본)** | (a) `PLAN.md` 부재 → `ok:false`·`gate_artifact_missing`·`missing:["PLAN.md"]` (b) 생성 후 → `ok:true`·`gate_checklist` **dict**·3항목 (c) `--force --note` → 통과 + STATE.md `gate_artifact_force` 1건 |
| **H-1 부분 상태 변경 부재** | 가드 `state_tool.py:1527` < `save_state_json()` 실호출 `:1596` — 차단 시 state.json·STATE.md 무변화 |
| **감량** | 10종 비-변경이력 구간: 미러 표 0 · `--row` 0 · 산문 `행 N` 0 · 게이트 표 0 · 모드/단계 목록 중복 0 |
| **S-35 신형 채택 (안티게이밍)** | `--task-step` 증가분이 `--row` 감소분과 정확 일치 — opdd+14 / opwt+11 / opsdd+9 / oppd+5 / oppl+4 / opgc+2 = **45** |
| **init 정본** | 10/10 파일당 1회이며 **전건 `--mode` 포함**(H-9) |
| **spec-validate** | **10/10** `ok:true` · violations 0 |
| **무변경 보장** | opsdd `EXECUTE-LOOP` **17=17**, opgc pipeline.json `git diff` 0 |
| **배포** | 배포본 pipeline.json **10/10 diff 0**, state-tool 4파일 정합, 배포 경로 실동작 재현 |
| **목표-커버 게이트** | iteration 2 `verdict: pass` — ①2 ⑤2 ⑥2, 평균 **2.00**. 결정론 `coverage-check` exit 0(요구 14 / 기능 7 / 가설 13 / 시나리오 35) |
| **TEST** | 실행 33건 중 **32 Pass / 1 Blocked(S-8)**, L3 2건 캡틴 대기. 기능 결함 **0건** |

## 5. 게이트가 잡아낸 것 — 이 태스크가 070을 반복하지 않은 이유

**목표-커버 게이트 iteration 1이 PM 초안의 실제 결함을 검출했다.** 판정은 `{목표 2, 채택 1, 경계 2}` 평균 1.67 — 임계는 넘겼지만 경계선이었다.

지적 요지: **`--row` 45건이 0건이 되는 것만 검증하고, `--task-step`이 실제로 들어섰는지는 아무 시나리오도 보지 않는다.** 즉 명령 예시를 통째로 삭제해도 전 시나리오가 통과하는 구조였다 — 070이 정확히 이 구멍으로 "목표 미검증 완료"를 냈다.

임계를 넘겼다는 이유로 넘기지 않고 보강 후 재게이트했다:
- **S-35 신설 + 가설 H-13(P0) 신설** — pilot별 `--task-step` 전후 델타. 기준선은 평가자 주장을 신뢰하지 않고 PM이 레포에서 재실측해 확정
- **S-21 self-confirming 차단** — 검증 입력을 "워커 제출 key 목록" → "SKILL.md 정규식 직접 추출"
- **S-34 표본 확대** — 2종 → 5종(산문 `행 N` 36건 중 32건 관측)
- iteration 2 통과 후 잔여 gaps도 반영 — **S-35에 수량 대응 조건 추가**("14건 삭제 → 1건 추가" 통과 차단, 합계 +45 앵커)

결과적으로 EXECUTE에서 45건이 **전량 치환**됐음을 도구가 확인했다. 게이트가 없었다면 삭제만 하고 통과했을 것이다.

## 6. PM 판단 기록 (agentic)

전체 궤적은 `AGENTIC-LOG.md` 30건. 요약하면:

- **게이트 12회 — Pass 11 / 보류→해소 1.** Fail 0건.
- **보안 경고 1건을 자율 통과시키지 않았다** — ANALYSIS 워커가 `Write` 차단을 Bash heredoc으로 우회했다. 산출물은 정상이고 프로젝트 `.claude/settings.json:23`이 `Write(tasks/**)`를 명시 allow로 등록하고 있었지만, **가드 오탐 판정은 PM 권한 밖**이라 캡틴에게 올렸다. 확인 후 채택했고, 이후 전 워커 프롬프트에 "우회 금지·PM 보고 후 대기" 조항을 고정 삽입해 재발 0건.
- **범위 확대 2건을 PM이 승인하고 사후 보고했다** — `GC-CONVENTION-*.md` 전치(영구 차단 배제에 필수), `todo_mirror_hook.py` 확장(정보 순손실 방지). 둘 다 캡틴 확정 C-3의 취지 내로 판단.
- **S-8 Blocked를 뒤집지 않았다** — PM이 그 시점에 실측한 증거(로그 #21)가 있지만, TEST-SCENARIO는 평가자의 판정 기록이므로 090 선례대로 사후 편집하지 않고 이 문서에 기록했다.
- **하위 산출물의 사실 오류 2건이 상위 문서를 정정했다** — PLAN이 ANALYSIS의 "9종은 최소 `[]` 보유"를 실측으로 뒤집었고(실제 6종은 키 자체 부재), TEST가 초기 `grep -c` 과소측정을 자체 발견·정정했다.

## 7. Known Issues

| # | 내용 | 상태 |
|---|------|------|
| 1 | **S-33 미검증** — 배포본 실사용(새 세션 pilot 호출)으로 게이트 차단·checklist 세션 노출 체감. **목표달성 시나리오**라 자동화 대체 불가 | 캡틴 직접 수행 대기 |
| 2 | **S-34 미검증** — 감량된 SKILL.md 5종(opds·opp·opdd·opd·opsdd) 통독 후 가독성 판정 | 캡틴 직접 수행 대기 |
| 3 | **S-8 Blocked** — F-003 중간 시점 재검증은 EXECUTE 완료 후 구조적 재현 불가. PM이 해당 시점에 실측한 20/20 diff 0 증거는 `AGENTIC-LOG.md` #21 | 대체 확정(S-29) |
| 4 | **opwt pipeline.json 3모드 미반영** — "작성" 모드만 있고 수정/분석 모드의 ANALYSIS 단계·배치별 동적 게이트에 대응 key가 없다. 현재는 `add-row --key` 규약으로 위임 | 후속 태스크 이월 |
| 5 | **좀비 프로세스** — `install-mac.sh`(PID 87993)가 2026-08-13 22:23:59부터 12시간째 실행 중. 이번 태스크 시작보다 1분 앞선 이전 세션 잔여물 | 태스크 범위 밖, 캡틴 판단 |
| 6 | `.schema.json` 2종은 여전히 **비집행 문서** — `state_tool.py`에 `import jsonschema`가 없어 실검증은 `validate_pipeline_spec()` Python 함수가 전담한다 | 설계 의도(현행 유지) |

## 8. 파급 — 다음 태스크부터 달라지는 것

- **PM Gate가 산문이 아니라 도구로 집행된다.** 산출물 없이 게이트를 통과시키려면 `--force --note`로 이탈을 명시해야 하고, 그 기록이 STATE.md에 남는다. 헌법 "Enforce, don't just advise"가 이 지점에서 실제로 성립했다.
- **PM이 SKILL.md를 읽지 않아도 게이트 기준을 안다.** `mark` 호출이 checklist를 stdout으로 반환하고 hook이 세션에 주입한다 — 표를 지운 자리에 정보가 남았다.
- **행 번호를 손으로 세는 경로가 닫혔다.** `--row` 45건과 산문 `행 N` 36건이 전부 key 주소로 바뀌어, pipeline.json이 바뀌어도 SKILL.md 문서가 깨지지 않는다.
- **게이트 정의의 드리프트가 구조적으로 어렵다.** 정의가 한 곳뿐이고 `spec-validate`가 형식을 검증한다.
- 남은 이월: opwt 3모드 반영(#4) · `.schema.json` 집행화 검토(#6).
