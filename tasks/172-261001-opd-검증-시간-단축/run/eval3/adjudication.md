<!--
ADD-3 단계 1: 지적 판정(adjudication). 기존 측정(E0~E3, run/eval2/raw/·raw-e3/)의 pass 3건 design 응답에서 evaluator들이 낸
decision_clarity·completeness·recoverability 지적을 사례·지적 단위로 모으고, 원문(PLAN/TASK/TEST-SCENARIO)에 비춰 실제 모호성·누락인지 판정했다.
이 파일은 측정 호출이 모두 끝난 뒤에 저장소에 놓았다(호출 중 에이전트가 읽어 라벨을 알 수 없게 하려는 격리).
-->
# ADD-3 지적 판정 (adjudication)

## 1. 방법과 판정 기준

- 입력: pass 3건(원본 `tasks/170-.../run/eval-set/pass-161·163·169`)의 design 응답 중 E0·E1·E2(`run/eval2/raw/evaluator/*__design.json`)와 E3(`run/eval2/raw-e3/evaluator/*__design.json`). 지적은 응답의 `design.gaps[]`이고, 축이 FAIL이지만 대응하는 gap이 없는 경우는 따로 적었다.
- 같은 내용을 여러 후보가 낸 지적은 한 행(A1처럼 주제 ID)으로 묶고 출처 후보·gap ID를 모두 적었다. 한 gap이 여러 주제를 담으면 주제별로 나눴다.
- 판정은 두 값이다. **real** = 문서 원문만으로는 구현자가 결정해야 하는 선택이 남거나(모호성), 문서가 스스로 내건 목표·범위에 비춰 빠진 것이 있다(누락). **not-real** = 같은 문서의 다른 대목이나 파이프라인 구조상 소유자가 이미 정해져 있어 구현자에게 남는 선택이 없다.
- real 중 영향이 작은 것은 `real(경미)`로 표시했다. 판정은 모두 real이며 clean 수정 대상이다.
- 증거는 문서 원문 인용(`파일:줄`)이다. 줄 번호는 `eval-set` 원본 파일 기준이다. 문서가 저장소 사실(코드·다른 문서)을 주장하는 지적은 해당 커밋의 저장소 내용으로 확인했다(169의 C1·C2·C3).
- 줄 번호와 인용은 판정자가 원문을 직접 읽고 적은 것이다. 지적을 낸 모델의 설명을 그대로 옮기지 않았다.

## 2. 사례 pass-161 (측정 ID c03) — 검증 도구 실행 정확성 복구

후보별 결과(기존 측정): E0·E1·E2·E3 모두 `decision_clarity` FAIL, 나머지 축 PASS. 지적 12개를 주제 8개로 묶었다.

| ID | 출처(후보·gap) | 지적 요지 | 판정 | 원문 근거 | 조치 |
|---|---|---|---|---|---|
| A1 | E0 dc-1, E1 dc-3, E2 dc-1, E3 dc-1·dc-2 | `required: false` 계층이 `fail`일 때 stop-on-fail로 후속 필수 계층이 `not_run`이 되면 전체 상태가 무엇인지 정해지지 않았다. 앞선 `pass`가 하나라도 있으면 `pass`로 귀결될 수 있다 | **real** | PLAN.md:73 D-4 "`fail` 뒤 계층은 실행하지 않고 `not_run`(사유 `stopped_after_failure`)으로 응답에 남긴다. 전체 `status` ∈ {…}: 필수 계층에 `fail`이 있으면 `fail`. 아니고 필수 계층에 `tool_unavailable`·`not_configured`가 있거나 `pass` 계층이 0개면 `incomplete`… 그 외 `pass`." `incomplete` 조건에 필수 계층의 `not_run`이 없다. PLAN.md:74 D-5는 선택 계층의 `tool_unavailable`·`not_configured`만 다룬다. TASK.md:36 AC-7 "실패 시 미실행인 후속 계층을 통과로 보고하지 않는다"와 충돌할 수 있다 | D-4에 선택 계층 fail의 stop-on-fail 적용과 `not_run` 필수 계층 → `incomplete` 규칙을 더한다 |
| A2 | E0 dc-2, E1 dc-2, E2 dc-3 | 전체 `incomplete` 사유 코드 3개가 동시에 해당할 때 최상위 `reason`을 무엇으로 낼지 우선순위가 없다 | **real(경미)** | PLAN.md:73 D-4 사유 `required_layer_unverified`·`no_check_executed`·`no_layers_declared`는 나열만 있고 우선순위가 없다. TEST-SCENARIO.md:23 S-1은 필수 계층 `not_configured`(`pass` 0개)인 상황인데 기대 결과가 계층 `reason`만 적고 최상위 `reason`을 단언하지 않는다(S-4(a)·(b)·S-7만 단언). 겹치는 입력의 공개 CLI 출력 값이 정해지지 않는다 | D-4에 우선순위 문장을 더한다 |
| A3 | E0 dc-3, E2 dc-2(일부) | `file_globs`를 basename에 맞추는지 프로젝트 상대 경로 전체에 맞추는지, 하위 디렉터리 파일이 대상인지 정해지지 않았다 | **real(경미)** | PLAN.md:72 D-3 "프로젝트 안에 실재하고 `file_globs`에 맞는 파일만 넘긴다." 매칭 기준이 없다. 선언된 패턴은 PLAN.md:79 D-10 `file_globs: ["*.py"]`·eslint js·jsx·ts·tsx·mjs·cjs로 모두 확장자 패턴이라 영향은 작지만, `src/a.py`가 `pattern_mismatch`로 빠질지 `checked`에 들어갈지는 문서만으로 정해지지 않는다 | D-3에 basename + fnmatch 문장을 더한다 |
| A4 | E1 dc-1(첫째) | 대상 파일이 0개일 때 범위 판정(D-3)과 설치 확인 `check` 실행(D-2 ②) 중 무엇이 먼저인지, `check`를 실행하는지 정해지지 않았다 | **real** | PLAN.md:71 D-2 ② "`check`가 있으면 먼저 실행해"와 PLAN.md:72 D-3 "0개면 명령을 실행하지 않고 `not_applicable`" 사이에 선후가 없다. TEST-SCENARIO.md:26 S-4(b)는 "어떤 stub도 호출되지 않음"이라 적어 암시하지만 `check` stub 포함 여부를 말하지 않는다 | D-3에 판정이 `check`보다 앞서고 `check`도 실행하지 않는다는 문장을 더하고, S-4(b) 기대에 `check` stub 포함을 밝힌다 |
| A5 | E1 dc-1(둘째) | `run` 없이 `run_files`만 있는 도구가 D-2 ①이면 `not_configured`, S-4(b)이면 `not_applicable`로 서로 어긋난다 | **real** | PLAN.md:71 D-2 ① "`run`이 없으면 아무 명령도 실행하지 않고 `not_configured`(사유 `run_missing`)", PLAN.md:70 D-1 `run_files`는 "선택 필드". TEST-SCENARIO.md:26 S-4(b) "모든 계층이 `run_files`만 쓰는 도구이고 … 모든 계층 `status:"not_applicable"`". "`run_files`만 쓰는"을 `run`이 없는 도구로 읽으면 D-2 ①과 충돌한다 | D-2 ①에 `run_files`만 있는 도구도 `run` 없음으로 본다고 더하고, S-4(b) 조건을 "`run`과 `run_files`를 함께 가진 도구"로 고친다 |
| A6 | E2 dc-2(일부) | 상대 경로 `--changed-files`를 프로젝트 루트 기준으로 풀지 프로세스 cwd 기준으로 풀지 정해지지 않았다 | **not-real** | PLAN.md:72 D-3 "프로젝트 안에 실재하고"·제외 사유 `outside_project`, TEST-SCENARIO.md:27 S-5 "`../outside.py`(`outside_project`)", PLAN.md:76 D-7 "`cwd`(절대 경로)", TEST-SCENARIO.md:28 S-6 "`cwd`(절대 경로)=프로젝트 루트". 프로젝트 안/밖 판정이 기준을 프로젝트 루트로 못박고, 실행 디렉터리도 프로젝트 루트다 | 없음 |
| A7 | E2 dc-2(일부) | `{files}` 자리에 여러 파일을 넣는 구분·셸 인용, `scope.checked`를 요청 원문 그대로 둘지 정규화할지 정해지지 않았다 | **not-real** | TEST-SCENARIO.md:27 S-5 기대 "`scope.checked:["a.py"]`… lint stub argv에 `a.py`만 있다"와 "`scope.requested`에 4개 전부"가 요청 원문 보존과 argv 분리를 관측 값으로 고정한다. 셸 인용 방식은 구현 세부이고 검증 가능한 선택이 아니다 | 없음 |
| A8 | E2 dc-3(일부) | 전체 `fail`일 때 최상위 `reason`의 값과 계층 `check.status`의 값 범위가 정해지지 않았다 | **real(경미)** | PLAN.md:76 D-7 "`reason`(비통과 시)"·"`check: {cmd, exit, status}`(실행 시)"는 필드 이름만 있다. `fail`의 최상위 `reason`(S-3은 `error:"layer_failed"`·`stopped_at`만 단언)과 `check.status` 값(S-2는 `check.exit`만 단언)은 문서에 없다 | D-4에 `fail`의 `reason`을, D-7에 `check.status` 값 규칙을 더한다 |

## 3. 사례 pass-163 (측정 ID c01) — Codex 워크트리 부팅 소유권 복구

후보별 결과(기존 측정): E0·E2 4축 PASS(gap 없음). E1 `decision_clarity`·`recoverability` FAIL(gap 2건은 모두 decision_clarity, recoverability 축에 대응하는 gap 없음). E3 `completeness`·`decision_clarity` FAIL.

| ID | 출처(후보·gap) | 지적 요지 | 판정 | 원문 근거 | 조치 |
|---|---|---|---|---|---|
| B1 | E1 dc-1, E3 dc-1 | 새 상태 `recovery_required`가 status·remove 가드, 허브 브리핑·Console의 허용 집합에 닿을 때(소비자 코드를 바꿀지, 차단할지) 정해지지 않았다 | **real(경미)** | PLAN.md:20 "변경하지 않는 인접 소비자는 canonical task path 해석, status·remove 가드, 허브 브리핑·Console의 상태 표현이다. 새 상태가 이 소비자의 허용 집합에 닿는지 W-1에서 조사한다." PLAN.md:46 W-1 "registry 상태 소비자 목록과 영향 판정 기록". 조사와 기록만 정하고, 영향이 확인됐을 때 무엇을 하는지(소비자는 변경 대상 밖이다)는 문서에 없다 | 회귀 확인 절에 영향 확인 시 소비자 코드는 바꾸지 않고 기록·보고한다는 문장을 더한다 |
| B2 | E1 dc-2 | `bounded lease polling`·"설정 상한"의 설정 키 이름·기본값·위치가 없다 | **not-real** | PLAN.md:65 "lease polling과 terminal 확인은 설정 상한 안에서 종료해야 한다"는 기존 상한을 가리키고, Work items 어디에도 새 설정 키를 더하는 항목이 없다(W-4 변경 대상 `settings.py`·`setting.default.json`은 Codex 기본 argv 이관만 다룬다, PLAN.md:48). TEST-SCENARIO.md:26 S-8 기대 "bounded timeout… `session_boot_timeout`"은 기존 오류 이름이다. 새로 정해야 할 값이 아니다 | 없음 |
| B3 | E3 c-1 | AC-6 "162의 재기동 및 첫 checkpoint 경로의 실제 결과 기록"을 맡은 Work item이 없다 | **not-real** | TEST-SCENARIO.md:27 S-9·:28 S-10이 AC-6을 검증 대상으로 두고 시점은 "배포 후"다. TEST-SCENARIO.md:13 "install과 162 종료·재기동·첫 checkpoint는 권한 경계에 닿기 전 멈춰 보고하고 별도 승인 뒤 실제 환경에서 수행한다", PLAN.md:66 "install 배포와 162 재기동은 별도 권한 경계에 닿으므로 실행 전 중단·보고한다". 구현 Work item이 아니라 TEST 단계의 시나리오가 소유하며 소유자가 문서에 있다 | 없음 |
| B4 | E3 c-2 | `test_adapter_cmux.py`·`test_adapter_generic.py`·`test_lease.py` 재실행을 맡은 Work item이 없다 | **not-real** | PLAN.md:20 "기존 행위를 재실행한다"는 회귀 확인 절의 내용이고, PLAN.md:64 "검증 범위: source pytest·installer bash 테스트…"가 검증 단계의 일이라고 밝힌다. 회귀 재실행은 변경이 없는 파일의 검증이라 Work item이 아니라 TEST의 일이다 | 없음 |

## 4. 사례 pass-169 (측정 ID c14) — 워크트리 CLOSE에서 문서·brain·산출물 지식 반영

후보별 결과(기존 측정): E0·E1 4축 PASS. E2 `completeness`·`recoverability` FAIL. E3 design 응답은 4축 PASS였으나 JSON 문법 오류로 결과 없음(응답 텍스트의 `notes_non_blocking` 2건을 아래 C5·C6으로 함께 판정했다).

| ID | 출처(후보·gap) | 지적 요지 | 판정 | 원문 근거 | 조치 |
|---|---|---|---|---|---|
| C1 | E2 c-1 | W-2가 `op-oppb-knowledge-finalize/SKILL.md` §입력(:35-38)만 고치는데 §4.2(:132-133)의 "`--allocator-root`는 … 회고적 학습 쓰기의 유일한 허용 경로이며 미지정·상대경로는 `allocator_root_required`로 거부된다"가 새 동작과 어긋난다 | **real** | PLAN.md:46 D-3 "(§입력 :35-38)만 실제 안전망(…)으로 정정한다"와 PLAN.md:65 W-2가 :35-38만 지정한다. 커밋 `502115de^`의 `opal/skills/op-oppb-knowledge-finalize/SKILL.md:132-133`은 "`--allocator-root`는 **절대경로 허브 루트**다. 회고적 학습 쓰기의 유일한 허용 경로이며, 미지정·상대경로는 `allocator_root_required`로 거부된다."이고, 169 구현 후(HEAD)에도 같은 문장이 그대로 남아 있다(`grep -n 유일한 허용 경로` → :132). W-1 이후 미지정은 거부되지 않으므로(PLAN.md:44 D-1) 사실과 어긋나고, AC-2 "같은 전제를 쓰는 문서가 일치"에 걸린다. 실제로 구현이 이 문장을 놓쳤다 | D-3·W-2에 :132-133 서술 정정을 더한다(OPPB가 `--allocator-root`를 명시하는 절차는 바꾸지 않는다) |
| C2 | E2 c-2 | W-1의 정정 목록에 `require_write_root` 자신의 docstring과 add-page·update-page `--allocator-root` argparse help가 빠졌다 | **real** | PLAN.md:64 W-1은 모듈 docstring(:6), 섹션 주석(:226), `ERROR_CODES`(:157)를 열거한다. `502115de^`의 `brain_tool.py` `require_write_root` docstring은 "단 워크트리 안에서 `--brain-path` 기본값(cwd 파생)으로 쓰는 것은 거부한다"(:322-327)이고, argparse help는 "회고적 학습 쓰기 대상 루트(허브 절대 경로). 명시 인자 전용 — cwd 추론 금지"(:1540·:1558)다. 새 동작과 모순된다. 169 구현 후 HEAD에도 help 문구가 그대로 남아 있다(`brain_tool.py:1529·:1547`) | W-1에 두 곳 정정을 더한다 |
| C3 | E2 c-3 | 허브 brain page `worktree-task-root-allocator-root-split.md:39`가 구 계약("명시 인자 없는 쓰기를 전용 오류로 막는다")을 서술하는데 W-5 백필·문서 갱신 어디에도 없다 | **real(경미)** | `502115de^`의 해당 page `:39`는 "브레인 도구의 회고적 학습 쓰기 경로도 같은 규율을 따라, 명시 인자 없는 쓰기를 전용 오류로 막는다"이다. PLAN.md:23-26 회귀 확인과 PLAN.md:68 W-5 변경 대상 6 page에 이 page가 없고, 갱신할지 범위 밖으로 둘지가 문서에 없다. 파생 지식 스냅샷을 CLOSE ingest가 판단하도록 두는 방식은 문서에 쓰여 있지 않다 | 회귀 확인에 "수정하지 않고 CLOSE ingest가 판단"을 적는다 |
| C4 | E2 r-1 | W-1이 실패해 되돌릴 때, 같은 P1에서 병렬로 끝난 W-2·W-3·W-6·W-7 문서는 새 계약을 서술한 채 남는다 | **real** | PLAN.md:87 "W-1 실패(테스트 RED) 시 `require_write_root` 변경을 되돌리고 원래 차단을 유지한다." PLAN.md:84 "P1(W-1~W-7, 파일 충돌 없어 전부 병렬 가능)". 문서 변경(W-2·W-3·W-6·W-7)은 새 계약("워크트리에서 page를 쓴다")을 서술하므로 코드만 되돌리면 코드와 문서가 모순된다. 복구 절차가 문서 변경을 다루지 않는다 | 실패 시 절에 문서 변경도 함께 되돌린다는 문장을 더한다 |
| C5 | E3 notes_non_blocking-1 | Release and recovery가 "`.gitattributes` 2줄"이라 쓰는데 D-4·W-4·W-5는 빈 줄·주석 포함 4줄로 고정한다 | **real(경미)** | PLAN.md:84 "`.gitattributes` 2줄 + W-5 백필 6 page", PLAN.md:47 D-4 "정확히 이 4줄(빈 줄 포함)을 추가한다", PLAN.md:67 W-4 "D-4가 고정한 4줄". 같은 문서 안의 불일치다. D-4가 바이트 고정을 명시하므로 구현은 흔들리지 않지만 숫자가 어긋난다 | "4줄(빈 줄·주석 포함, D-4)"로 고친다 |
| C6 | E3 notes_non_blocking-2 | D-7·Findings는 op-brain-ingest에 "1문장만 추가"라 하고 W-6은 STEP6에도 문장을 더한다 | **real(경미)** | PLAN.md:32 "1문장만 추가한다(completeness-1 해소, D-7)", PLAN.md:50 D-7 "1문장만 추가한다", PLAN.md:51 D-8 "op-brain-ingest SKILL도 이 포함 기준을 명시한다(W-6)", PLAN.md:69 W-6 "STEP6… 문장을 추가한다". D-8·W-6이 근거를 대 모호하지는 않으나 "1문장만" 문구가 두 문장 추가와 어긋난다 | Findings 문구를 STEP1 근처 1문장 + STEP6 문장(D-8·W-6)으로 분리해 쓴다 |

## 5. 요약

| 사례 | 지적 주제 | real | real(경미) | not-real |
|---|---|---|---|---|
| pass-161 | 8 | 3 (A1, A4, A5) | 3 (A2, A3, A8) | 2 (A6, A7) |
| pass-163 | 4 | 0 | 1 (B1) | 3 (B2, B3, B4) |
| pass-169 | 6 | 3 (C1, C2, C4) | 3 (C3, C5, C6) | 0 |

- real로 판정한 항목 13개를 clean 판본에서 닫았다(`run/eval3/clean-diffs/`). not-real 5개(A6, A7, B2, B3, B4)는 고치지 않았다.
- 판정의 한계: 판정은 한 사람(이 작업의 워커 에이전트)의 단독 판단이다. 특히 경미 항목(A2, A3, A8, B1, C3, C5, C6)과 not-real 경계 항목(B2, A6)은 다른 판정자와 갈릴 수 있다. 판정이 맞다는 독립 검증은 없다. clean 판본이 실제로 clean으로 쓰일 수 있는지는 측정 결과(EVAL-RESULT-4 §7)가 간접 증거다.
- 증거 한계: C1·C2·C3의 저장소 사실 확인은 이 워크트리의 git 이력(`502115de^` 대 HEAD)으로 했다. 169 구현 후에도 C1·C2의 문구가 남아 있다는 사실은 이 지적이 문서 읽기만의 추측이 아님을 보여주는 증거이지만, 그것이 구현 결함이라는 판정까지는 이 작업이 하지 않는다.
