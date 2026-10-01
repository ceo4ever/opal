## 6. 측정 관찰 (후보 간 상대 비교)

이 절의 수치는 2~5절 표에서 파생한 값이며 절대 누락률이 아니다. 사례가 10건·8건뿐이고 합성 사례가 섞여 있어 후보 간 상대 비교로만 읽는다.

### 6.1 checker

1. **163-pass 뒤집힘은 보정 후 사라졌다(최초 측정에서는 4개 후보 모두 뒤집힘).** 최초 측정의 뒤집힘은 모델이 아니라 사전 검사(W-1)의 판정 결함 때문이었다. 163 구간의 테스트 파일 6개는 `# @header` 다음 줄에 `# module: ...` 형식의 줄 주석 헤더를 쓰고, `code-scan scan --json`은 이 형식에서 기준 커밋·현재 모두 `{}`를 반환한다. 보정 전 `check_header`는 기준 쪽을 텍스트 포함으로, 현재 쪽을 scan 결과로 판정해 거짓 "회귀" High를 만들었다. 보정 후에는 양쪽에 같은 scan 판정을 적용하므로 기존부터 인식되지 않던 형식은 finding을 만들지 않는다(8절). 보정 후 163-pass는 4개 후보 모두 finding 0건이다. 모델이 만든 High+ finding은 처음부터 0건이었다.
2. **High+ 누락 0은 후보 간 변별력이 없다.** 기대 High+ finding(162의 @header 2건, `SKILL.md` frontmatter 1건)은 전부 기계 규칙이라 모든 후보가 사전 검사 결과로 받는다. 모델 판단이 필요한 합성 판단 사례 2건의 기대는 medium 이하여서 High+ 누락 지표에 들어가지 않는다. 후보 간 차이는 판단 사례 2건과 소요 시간에서만 나타난다.
3. **판단 사례**: syn-j1(한글 식별자)과 syn-j2(영문 문서 절)에서 K0·K1·K2는 두 사례 모두 `§언어 규칙` medium finding을 냈다. K3(haiku·medium)는 syn-j2는 냈으나 syn-j1은 finding 0건이었다(판정 일치 X 1건). 누락한 심각도는 medium 이하다.
4. **소요 시간**(재집계 후에도 불변; 163-pass는 모델 호출 시간이라 보정과 무관): 162-defect를 뺀 9사례 공통 평균은 K0 38.0초, K1 31.5초, K2 43.2초, K3 126.3초다(K1 대비 K0 약 1.2배, K3 약 4배). K3는 평균 21.8턴으로 sonnet 후보(7.7~9.9턴)보다 턴이 2배 이상 많았다. sonnet 세 후보의 차이는 이 표본에서 사례별 편차(예: syn-j2 K2 77.0초)와 비슷한 크기라 순서를 확정하지 않는다.
5. **최초 결과 없음 2건(162-defect K1·K2)은 후보 품질이 아닌 진입 게이트 때문이었고, 재집계에서 첫 결과를 확보했다.** 최초 호출 두 건은 에이전트가 `event-loader verify`를 직접 실행했을 때 `stale_receipt`(agent-registry 경로: receipt는 `~/.opal/references/agents.md`, 검증은 저장소 소스 `opal/core/references/agents.md` 기준)를 받고 `status: blocked`로 반환했다(원본 `raw/checker/initial-no-result/`). 재집계에서는 프롬프트에 verify 절대경로 명령(`--project-root` 포함)을 명시하고 호출 직전 receipt를 새로 만들어 두 건을 실행했으며, 둘 다 사전 검사 @header High 2건을 포함한 최종 JSON을 만들었다(K1 40.0초, K2 48.4초; 8절). 최초 원인은 확정하지 않았다.

### 6.2 evaluator

1. 3개 후보 모두 결합 verdict 24건 중 24건이 170 단일 호출 기대와 일치했다(H-2: 호출을 scope로 나눠도 기대 verdict가 달라진 사례 없음). 결함 누락 0, pass 뒤집힘 0이다. 170에서 xhigh가 뒤집었던 pass-163·pass-169도 E0·E1·E2 모두 pass였다.
2. 결함 사례에서 기대 실패 축 외의 축도 FAIL로 판정한 경우가 많았다(예: 168·169의 4축 전부). 기대 축을 못 잡은 건수만 누락으로 세었으므로 이 초과 지적은 채택 판정에 들어가지 않는다. 후보 간 차이도 작다.
3. **소요 시간**: 결합 소요(두 호출 중 긴 쪽) 평균은 E0 57.3초, E1 57.2초, E2 78.3초다. E1은 E0과 시간 차이가 없고 E2는 E0 대비 약 1.37배다. 두 호출을 동시에 실행한 쌍 벽시계 평균은 E0 57.3초, E1 57.2초, E2 78.3초이고, 개별 소요의 합 평균(E0 105.6초, E1 101.6초, E2 143.6초)보다 24쌍 모두 짧았다.
4. effort 미지정(E0)이 실제로 어느 effort로 실행되었는지는 CLI 출력으로 확인되지 않는다. E0과 E1의 시간이 같다는 사실만 관측했다. 호출당 비용 합은 E0 $4.36, E1 $3.87, E2 $7.30이다.

## 7. 한계

1. **합성 사례 대표성(H-3)**: checker의 합성 6건은 필자가 만든 최소 변경이며 기계 규칙 3건은 사전 검사가 결정론으로 잡는다. 실제 변경의 판단 규칙 위반 분포를 대표하지 않는다. 판단 사례가 2건뿐이라 모델 간 변별은 약하다. 결과는 후보 간 상대 비교로만 읽고 절대 누락률은 주장하지 않는다.
2. **헤드리스 호출은 실제 서브에이전트 디스패치와 완전히 같지 않다**: `claude -p --agents … --agent …`로 에이전트 정의를 주입했고 `--permission-mode dontAsk --allowedTools Read Grep Glob Bash`로 권한을 열었다. 실제 PM 디스패치의 컨텍스트 주입·모델 별칭 매핑(`standard`→sonnet 등)·세션 effort 상속과 다를 수 있다. 호출마다 `--no-session-persistence`를 썼고 사용자 전역 MCP·커넥터가 로드된 상태에서 호출되었다.
3. **동시 실행 영향**: 최대 6개 호출이 동시에 돌아 소요 시간에 서로의 부하가 섞인다. 같은 사례의 후보들이 같은 시각대에 실행되도록 사례 순서로 제출했으나, 시간은 1회 측정값이며 반복 분산을 알 수 없다.
4. **사례 구성 판단**(PLAN D-13 문구 우선): ① 과거 기록 4건 중 통과 3건의 `target_files`는 해당 태스크의 과거 `gc-findings-convention-*.json` `checked_files`를, 162 결함은 기록이 없어 구간 변경 파일 중 `tasks/` 아래 산출물을 제외한 목록을 썼다. ② 합성 사례의 기준 저장소는 `docs/CONVENTIONS.md`와 참조 문서 사본을 가진 임시 git 저장소다. ③ 판단 사례의 기대는 "해당 파일에 `§언어 규칙` finding이 있고 심각도가 medium 이하"로 읽었다. ④ evaluator의 기대 실패 축은 170 `EVAL-RESULT.md` 표(162·163은 decision_clarity+executability, 167·168·169는 decision_clarity)를 썼고 원본 gate 축(168·169는 completeness 등 추가)은 쓰지 않았다. ⑤ 결과 없음·미실행이 있는 후보는 측정 불완전으로 "채택 불가"로 두었다(결과 없음을 통과로 세지 않기 위한 해석이며 D-13 문구에는 없다).
5. **evaluator fixture**: 결함 fixture 5건은 `design-gate start`의 결정론 검사를 통과하지 못해(TASK.md sdlc-v2 frontmatter 등), `start`가 만든 시도(`bundle_hash`·`iteration` 1)를 유지한 채 임시 fixture의 `design_gate.status`만 `evaluating`으로 되돌려 `combine`을 실행했다. evaluator는 state.json을 입력으로 받지 않으므로 판정에는 영향이 없다고 보지만, 실제 PM 경로 그대로는 아니다.
6. **사전 검사 기여**: checker의 최종 JSON은 사전 검사 finding을 포함하므로 모델 단독 성능이 아니라 "사전 검사 + 모델 + merge" 흐름의 결과다. 모델이 `merge`를 수행하지 않으면 결과 없음이다.

## 8. 재집계 경위

### 8.1 최초 측정이 드러낸 결함

최초 측정(`results-initial.json`·`results-initial-EVAL-RESULT.md`로 보존)에서 163-pass가 checker 4개 후보 모두에서 "pass 뒤집힘"이 되어 checker 전 후보가 채택 불가였다. 원인은 모델이 아니라 `convention_precheck.py` `check_header`의 비교 기준 불일치였다. 수정 파일의 "기준 커밋에 @header가 있었는지"는 텍스트 포함(`"@header" in base`)으로, "지금 없는지"는 `code-scan scan --json` 결과가 비었는지로 판정했다. 163의 테스트 파일 6개(`# @header` 다음 줄에 `# module: ...` 줄 주석 헤더)는 code-scan이 기준·현재 모두 `{}`로 해석하는 기존 형식인데도 거짓 "회귀" High가 되었다. 163의 과거 검사 기록은 같은 6개를 info/advisory로 보고했고 통과였다. PLAN D-10 ①은 "기준 커밋 버전에는 @header가 있었는데 지금 없으면(회귀)"를 규칙으로 정했으므로, 결함은 규칙이 아니라 구현이 기준 쪽을 다른 판정기로 본 것이다.

### 8.2 수정 내용

수정 파일(status M)의 기준 커밋 blob을 임시 폴더에 같은 상대경로로 쓰고 project-root의 `.opal/code-scan.json`을 복사해 현재와 같은 `code-scan scan <rel> --json`을 적용한다(`CodeScanClient.base_header_of`). 회귀 = 기준 scan 결과가 비어 있지 않고 현재 scan 결과가 비어 있음. 기준·현재 모두 비어 있으면(기존부터 code-scan이 인식 못 하는 형식) finding을 만들지 않는다. 추가된 파일(A)은 종전대로 scan 결과가 비면 finding이다. 다른 규칙·finding 스키마·fingerprint는 바꾸지 않았다. 162 재현(S-9 시험)은 그대로 정확히 2건이다. 시험 2건을 추가했다(`test_mechanical_rules_header_line_comment_legacy_no_finding`, `test_mechanical_rules_header_regression_kept`; 전체 15건 통과).

### 8.3 재집계 방식

- 모델 호출 40건 중 38건의 응답은 재사용했고 다시 호출하지 않았다. 모델 응답은 사전 검사와 독립이다.
- 최종 finding JSON은 "사전 검사 + 모델 finding"을 에이전트가 `merge`한 결과이므로 사전 검사 산출물이 raw에 저장되어 있었다. 그래서 과거 체크아웃을 같은 커밋·`base_ref`·`target_files`로 다시 만들어 보정된 `scan`을 실행하고(`recompute_precheck.py`), 기존 최종 JSON에서 기존 사전 검사 finding을 뺀 나머지를 모델 finding으로 복원해 보정된 사전 검사와 다시 `merge`했다. 원본 JSON은 `*.initial.json`으로 보존했다. 합성 사례는 체크아웃을 다시 만들면서 `base_ref` 커밋 sha가 달라졌으므로 새 `cases.json`(스크래치)의 값으로 `scan`했고, 기존 사전 검사 결과와 비교해 163-pass 외에는 finding 집합이 같음을 확인했다. 복원한 모델 finding은 어느 사례에서도 없었다.
- 재집계로 바뀐 최종 JSON은 163-pass 4건(K0~K3; 사전 검사 6건 → 0건)뿐이다. 나머지는 변동이 없다.
- 신규 호출 2건: 최초 결과가 없던 `162-defect` K1·K2. 호출 직전 receipt를 새로 만들고 verify `ok: true` 확인 후, 프롬프트에 verify 절대경로 명령(`~/.opal/tools/event-loader/run.sh verify --receipt <receipt> --event worker.dispatch --project-root <저장소 루트>`)을 명시했다(`run_eval.py receipt_block`의 문구 보강). 이번에는 `stale_receipt` 없이 둘 다 완료했다. 이 두 건은 재시도가 아니라 최초 결과 확보다.
- evaluator 48건은 이 보정과 무관하므로 건드리지 않았다(결과 동일).

### 8.4 최초 결과 대비 달라진 판정

| 후보 | 최초 | 재집계 |
|---|---|---|
| K0 | 채택 불가(pass 뒤집힘 1: 163-pass) | 채택 가능(결과 10/10, 누락 0, 뒤집힘 0) |
| K1 | 채택 불가(뒤집힘 1; 결과 없음 1) | 채택 가능(10/10) |
| K2 | 채택 불가(뒤집힘 1; 결과 없음 1) | 채택 가능(10/10) |
| K3 | 채택 불가(뒤집힘 1) | 채택 가능(10/10, 판정 일치 아닌 행 1: syn-j1) |
| E0·E1·E2 | 채택 가능 | 변동 없음 |

D-13 채택 규칙(결함 누락 0 AND pass 뒤집힘 0, 결과 없음은 채택 불가)은 사후에 바꾸지 않았고 보정된 값에 그대로 적용했다. 163-pass 뒤집힘이 사라졌고, 사라지지 않은 항목은 없다. checker 4개 후보는 모두 채택 가능이 되었으나 High+ 누락 0은 후보 간 변별력이 없고(6.1의 2), 후보 선택은 소요 시간과 판단 사례 2건의 차이에서만 갈린다. 추천 문구의 K1은 평균 소요 시간 기준이다(1회 측정, 시간 차이는 분산 안쪽일 수 있다). 결정은 캡틴이 한다.
