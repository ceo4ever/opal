# ADD-1: S-13 기대 verdict 불일치 원인 분리

> 코드·시나리오·PLAN은 수정하지 않았다. 표본이 작아(조건당 2회) 통계 주장은 하지 않고 관찰만 적는다. 원본 응답·프롬프트·메타는 `test-evidence/add1/`(`c{조건}-{회}.response.json|prompt.txt|meta.json`).

## 결론 한 줄

가장 지배적인 요인은 **(P) 프롬프트 안의 경로 이름**이다. 프롬프트 문구는 W-10과 TEST가 글자 그대로 같지만, W-10 fixture 폴더가 사례 ID(`pass-161`)였고 TEST/진단 폴더는 중립 이름(`s13fx`·`pair1-design` 등)이었다. 정의 전달 방식(D)과 cwd(C)는 원인이 아니라는 쪽으로 관찰이 모였다. 표본 변동(V)을 완전히 배제하지는 못한다. 이 해석이 맞다면 W-10의 "24/24 verdict 일치"는 사례 ID가 판정자에게 보인 상태의 측정이라는 한계가 있다.

## ① 프롬프트 차이표

W-10 프롬프트는 `run/eval/run_eval.py`의 `evaluator_prompt()`를 같은 입력으로 렌더해, TEST의 `scratchpad/s13-prompt-design.txt`와 `diff`했다. 경로 3종(receipt·fixture·해시)을 치환한 뒤 **차이 0줄(IDENTICAL)**이었다.

| 항목 | W-10 (`run_eval.py`) | TEST S-13 / 진단(`diag.py`) | 차이 |
|---|---|---|---|
| 지시 문구·`phase`·`scope`·`iteration`·`refinement` | `design-rubric`, scope별, 1, false | 같음 | 없음 |
| `previous_gaps`·refinement 입력 | 없음(`refinement: false`) | 없음 | 없음 |
| 입력 필드(`task_md`·`plan_md`·`scenario_source`·`input_bundle_hash`·`project_root`) | 같음 | 같음 | 없음 |
| `input_bundle_hash` | `8b6ec323…ff7b` | 같음 | 없음(같은 문서 묶음) |
| receipt 파일명 | `…/receipts/pass-161__E1__design.json`류 | `s13-receipt-design.json`, `diag-fx/*-receipt.json` | **이름에 사례 ID 포함 여부** |
| 태스크 폴더 경로 | `<work>/eval-fixtures/pass-161/` | `<scratchpad>/s13fx/`, `diag-fx/single1/` 등 | **폴더명이 `pass-161`인지 중립 이름인지** |
| 프롬프트 안 `pass-161` 출현 | 6회(경로 4 + receipt 경로·verify 명령) | 0회 | **라벨 노출** |
| 에이전트 정의 전달 | 저장소 AGENT.md를 `--agents` JSON + `--agent` | 설치본 `--agent` (진단·TEST) | 전달 방식(D) |
| 모델·effort | `--model opus --effort medium` | 설치본 frontmatter(`model: opus`, `effort: medium`) | 같음. 응답 `modelUsage`는 양쪽 `claude-opus-5-5` |
| cwd | 저장소 루트 | 진단은 저장소 루트, S-13 호출의 cwd는 기록 없음 | 확인 불가 |
| 읽기 허용 | `--add-dir <repo> <fixture>`, `--max-turns 50`, `--permission-mode dontAsk` | 진단은 `--add-dir` 없음, `dontAsk` | 응답 16건 모두 `permission_denials` 0건 |
| 설치본과 저장소 AGENT.md 본문 | 저장소 본문 | 설치본 | `executability` 행의 raw CLI FAIL 문구 1줄 외 같음. decision_clarity와 무관 |

따라서 **지시 문구·`previous_gaps` 유무·입력 필드는 같고**, 실제로 다른 것은 경로 문자열(라벨 노출)과 호출 옵션뿐이다.

## ② 판정 근거 비교

**같은 모호성을 W-10은 이렇게 보았다**(pass-161 design, 3후보 모두 4축 PASS, gaps 0):

- E0(opus 기본): D-4의 incomplete 사유 두 개가 동시에 성립할 때의 우선순위가 없다고 직접 적고도 "나열 순서로 판단할 수 있는 수준이라 FAIL 사유로 보지 않았다"로 결론.
- E1(opus medium): 같은 D-4 우선순위와 D-3 `file_globs` 매칭 방식이 "명시가 부족하지만 시나리오가 대표 사례를 고정하고 있어 구현자에게 실질적인 선택을 남기는 결함으로 보지 않았다".
- E2(opus high): 4축 PASS.
- 이번 ADD-1 조건 ①(`pass-161` 경로) 2회도 같다. D-4 우선순위와 H-2의 check 소요 필드 부재를 알아보고도 "시나리오가 기대값을 이미 정했다·외부 계약을 바꿀 만한 선택이 아니다"로 PASS. 4턴으로 끝났다.

**TEST·진단은 같은 모호성을 이렇게 보았다**(중립 경로, 11건 모두 FAIL `decision_clarity`):

- S-13: gap 3건. D-2 ①과 D-3 충돌(`run` 없이 `run_files`만 있는 도구), `check`와 파일 필터의 순서, `{files}` 치환·`file_globs` 매칭 규칙.
- 진단 pair1·pair2·pair3과 단일 3회도 같은 지점에서 FAIL. 공통 근거는 "S-4(b)가 `run_files`만 있는 도구에 `not_applicable`을 기대하는데 D-2 ①을 그대로 구현하면 어긋난다"와 "D-4 incomplete 사유 우선순위 없음"이다.

정리하면 **두 쪽이 같은 문장을 보고 있다**. D-3 `file_globs` 매칭 방식과 D-4 우선순위는 W-10 E1도 "있다"고 인식했다. 갈린 것은 그 모호성을 "구현자 선택으로 남는 결함"으로 세느냐 "시나리오가 고정하므로 결함 아님"으로 세느냐의 **엄격도**다. D-2 ①과 `run_files` 단독 충돌(S-4(b))은 W-10 응답 어디에도 언급이 없고, TEST 쪽에서만 반복해서 나왔다. 단 pass-161 문서 자체가 `run_files` 단독 도구 규칙을 닫지 않은 것은 사실이라, 중립 경로에서 FAIL이 나온 것이 오탐이라고 단정하지 못한다. 170이 이 사례를 pass로 판정한 기록이 기대의 출처다.

## ③ 실험 표 (pass-161, scope design만, 정식 wrapper `~/.opal/tools/opal-agent/run.sh`)

공통: `--json --model opus --effort medium --allowed-tools Read,Grep,Glob,Bash --opal-bootstrap off --timeout 300`, 정의=저장소 `opal/agents/opal-evaluator-agent/AGENT.md` 본문을 `--system-prompt`로. 호출마다 fresh `worker.dispatch` receipt와 `--make-fixture` 임시 태스크. 6건 동시 실행, 재시도 없음, 6건 모두 결과 있음.

| 조건 | 프롬프트 | 폴더명 | cwd | 회 | 4축 (C/DC/E/R) | design gaps | DC gap | 소요(초) | 턴 |
|---|---|---|---|---|---|---|---|---|---|
| ① | W-10형 | `…/eval-fixtures/pass-161` | 저장소 루트 | 1 | PASS/PASS/PASS/PASS | 0 | 0 | 71.1 | 4 |
| ① | W-10형 | 같음 | 저장소 루트 | 2 | PASS/PASS/PASS/PASS | 0 | 0 | 51.6 | 4 |
| ② | TEST형 | `…/s13fx` | scratchpad | 1 | PASS/**FAIL**/PASS/PASS | 2 | 2 | 70.0 | 6 |
| ② | TEST형 | 같음 | scratchpad | 2 | **FAIL**/**FAIL**/PASS/PASS | 3 | 2 | 85.8 | 7 |
| ③ | W-10형 + `--agents` 주입 | — | — | — | **생략** | — | — | — | — |
| ④ | TEST형 | `…/s13fx` | 저장소 루트 | 1 | PASS/**FAIL**/PASS/PASS | 3 | 3 | 73.5 | 6 |
| ④ | TEST형 | 같음 | 저장소 루트 | 2 | PASS/**FAIL**/PASS/PASS | 2 | 2 | 75.8 | 8 |

- ③ 생략 사유: `opal-agent`는 `--agents`/`--agent`를 지원하지 않는다(옵션 목록에 `--system-prompt`만 있다). `--bin`으로 우회하면 raw `claude -p`와 같아 지시(raw 금지)에 어긋나므로 하지 않았다.
- ②의 cwd는 S-13 호출의 실제 cwd 기록이 없어 scratchpad로 두었다(저장소 루트와의 대비용). ②의 completeness FAIL(2회차)은 pyright 실측 경로(AC-6)에 관한 것으로, 이번 질문과 별개인 변동이다.
- 정의 전달(D)은 ①이 `--system-prompt`로 PASS이므로 `--agents` 방식이 PASS의 조건이 아니다. wrapper는 `--dangerously-skip-permissions`를 쓰므로(W-10은 `dontAsk`) 권한 방식도 다르지만 거부 0건이라 영향 근거는 없다.

## ④ 원인 판단

| 요인 | 판단 | 근거 |
|---|---|---|
| (P) 프롬프트 | **지배적으로 보임**(좁게는 프롬프트에 실린 경로·파일명의 사례 라벨) | 문구는 동일. 폴더명만 다른 ①과 ④를 비교하면 ① 0/2 FAIL, ④ 2/2 FAIL. W-10 3/3 PASS와 이전 TEST·진단 7/7 FAIL도 같은 방향. 중립 경로 전체는 11건 중 11건 FAIL(TEST·진단 7 + ②④ 4), `pass-161` 경로는 5건 중 5건 PASS |
| (D) 정의 전달 | 아님으로 봄 | ①이 `--system-prompt`(wrapper)로도 PASS. D가 원인이면 ①이 FAIL이어야 한다 |
| (C) cwd·읽기 범위 | 아님으로 봄 | ②(scratchpad)와 ④(저장소 루트) 모두 FAIL. 모델·권한 거부도 차이 없음 |
| (V) 표본 변동 | 배제하지 못함 | 조건당 2회. 다만 중립 경로 11건이 한 방향이고 판정 근거 문장도 반복해서 같은 지점(D-2 ①/D-3, D-4)을 짚는다 |

주의할 점:

1. "라벨 노출"이 직접 원인이라는 것은 **가장 합당한 설명이지 입증이 아니다**. ①은 폴더명뿐 아니라 부모 폴더(`eval-fixtures`)와 receipt 파일명(`pass-161__E1__design.json`)도 함께 달랐다. 어느 쪽 문자열이 효과를 냈는지는 이 실험으로 가르지 못한다. 모델 응답은 `pass-161`을 한 번도 인용하지 않았다.
2. W-10은 사례 ID가 `pass-161·163·169`, `defect-162-i1`처럼 의미를 가진 이름이라 24/24 일치(결함 누락 0, 뒤집힘 0)가 라벨의 도움을 받았을 가능성이 있다. pass-163·169와 결함 사례는 이번에 중립 경로로 재측정하지 않았으므로 **W-10 결과 전체가 무효라고 말할 근거는 없고**, 오염 가능성이 있다는 한계로만 적는다.
3. 어느 쪽이든 pass-161은 "모델이 안정적으로 pass를 내는 사례"가 아니다. 같은 문서가 라벨이 없으면 일관되게 FAIL이므로 기대 verdict를 정답으로 쓰는 S-13 수용 기준은 그 사례에서 성립하지 않는다.

## ⑤ S-13 재설계 제안

S-13이 검증하려는 것은 AC-8(병렬로 나눠도 단일 판정과 같은 계약·verdict를 낸다)이고, 현재 기준은 여기에 "모델이 pass-161에 pass를 낸다"는 **모델 판정 분포**를 섞고 있다. 후보:

| 후보 | 내용 | 장점 | 단점 |
|---|---|---|---|
| A. 계약·결합 규칙과 판정 분포 분리 | S-13 기대를 "두 응답이 계약 형식이고 `combine`이 성공하며 `record`가 수락된다. 결합 verdict는 **기록만** 한다(기대 verdict와 비교하지 않는다)"로 줄인다. 판정 분포 비교는 W-10/진단 문서에서 별도로 다룬다 | 모델 변동으로 계약 시험이 FAIL하지 않는다. 변경이 작다 | 결합 verdict가 단일과 다르지 않다는 AC-8 후반부 검증이 약해진다 |
| B. 같은 조건의 단일 호출과 결합 verdict 일치율 | 같은 fixture(경로·라벨 동일)로 단일(`scope all`)과 병렬 쌍을 N회씩 돌려 **결합 verdict 일치**를 합격 규칙으로 쓴다. 예: 단일·병렬이 각각 N=3일 때 verdict 분포가 같으면 PASS(모두 같은 한 값). 기대 verdict는 쓰지 않는다 | 병렬 분리가 판정을 바꾸는지만 직접 본다. 라벨·사례 선택에 덜 민감하다 | 호출이 3→6~9회로 늘고 시간·비용이 크다. 지금 진단 표본은 이미 이 형태로 있다(단일 3/3, 병렬 4/4 모두 fail) |
| C. 결함 축이 알려진 사례 사용 | pass 사례 대신 결함 사례(예: defect-167 `decision_clarity`)로 "병렬 결합이 같은 축을 FAIL로 잡는다"를 본다. 사례 폴더는 **중립 이름으로 복사**한다 | pass의 경계 판단보다 안정적이고 라벨이 개입하지 않는다 | 이번 실험에서 검증하지 않았다. 결함 사례의 안정성은 별도 측정이 필요하다 |

**권고: A + B의 축소형.** S-13의 합격 규칙은 계약 검증(A)으로 줄이고, 병렬이 판정을 바꾸지 않는지는 "같은 중립 fixture에서 단일 1회와 병렬 1쌍의 결합 verdict·FAIL 축이 같다"는 비교(B의 N=1)와 **기록**으로 둔다. 기대 `pass`는 쓰지 않는다. 이미 있는 진단 표본(단일 3/3 fail, 병렬 4/4 fail, 모두 `decision_clarity`)이 이 형태의 증거로 그대로 쓰인다. 사례를 결함 쪽으로 바꾸는 C는 추가 측정 뒤 선택 사항으로 둔다.

필요한 수정 범위(적용하지 않았다):

- `TEST-SCENARIO.md` S-13 한 행: 기대 결과의 "결합 `verdict`가 `pass`…기대 verdict와 같다"를 "결합 `verdict`·FAIL 축이 같은 fixture의 단일 호출 결과와 같다(둘 다 기록). 기대 verdict와 비교하지 않는다"로, 조건 문구에 "fixture 폴더·receipt 이름에 사례 ID·`pass`/`defect` 라벨을 쓰지 않는다"를 추가.
- `PLAN.md`: AC-8/H-2 문구의 "170 단일 호출 기대 verdict와 일치"를 "같은 조건의 단일 호출과 일치"로 정정. D-13 측정 설명에는 사례 ID를 폴더·receipt 이름에 노출했다는 한계를 추가.
- `EVAL-RESULT.md`(W-10)는 수치를 바꾸지 않고 "사례 ID가 경로에 노출되었다"는 한계 한 줄을 추가하는 정도를 제안한다.
- 필요하면 `test-scenario-guide.md`의 `[실호출 1회]` 규칙에 "판정 라벨이 되는 이름을 프롬프트 경로에 싣지 않는다"를 한 줄 추가.

## ⑥ 병렬 시간 이득에 이 실험이 주는 정보

design 단독 호출의 소요가 verdict 경로에 따라 갈렸다. PASS 경로(①)는 4턴·출력 3.6~5.3천 토큰·51.6~71.1초였고, FAIL 경로(②④)는 6~8턴·출력 4.6~6.2천 토큰·70.0~85.8초였다. 진단의 시나리오 판정 호출(약 65~72초)과 겹쳐 쌍 벽시계는 늘 design 쪽이 정한다. 이는 병렬의 이득이 "design이 시나리오 호출보다 짧거나 비슷할 때만 큰데, 기존 지적을 길게 따지는 FAIL 경로에서는 design이 지배한다"는 이전 관찰과 일치한다. 즉 이득은 모델의 엄격도(어떤 경로를 타는가)에 따라 달라지므로, 시간 이득을 판단하려면 단일 대비 단축을 **같은 중립 조건에서** 따로 재야 한다. 이번 실험은 design 단독만 재서 단일·병렬 직접 비교는 하지 않았다(6건 동시 실행이라 소요에는 호출 간 간섭도 섞여 있다).
