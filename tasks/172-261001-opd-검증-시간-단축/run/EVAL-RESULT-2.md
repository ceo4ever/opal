<!--
W-10 재측정(중립 경로) 결과. 호출은 정식 wrapper(opal-agent), 사례 라벨 대신 불투명 ID. PLAN D-13 채택 규칙 그대로.
이 문서의 표는 run/eval2/run_eval2.py가 run/eval2/raw/ 원본 응답에서 계산해 생성한다(`python3 run_eval2.py --report-only`).
본문 1·5절은 eval2/notes-method.md·notes-conclusion.md를 그대로 넣는다. 결과는 후보 간 상대 비교로만 서술한다(H-3).
-->
# EVAL-RESULT-2: checker·evaluator model·effort 중립 경로 재측정 (W-10 재측정)

실행 호출 88회(checker 40·evaluator 48), 결과 있음 87·결과 없음 1. 모든 호출은 사례x후보당 1회이며 재시도하지 않았다.

## 1. 중립화 방법과 남은 누출 한계

### 1.1 방법

ADD-1(`ADD1-S13-REVIEW.md`)이 보인 "fixture 폴더·receipt 이름의 사례 라벨이 pass 판정을 도왔을 가능성"을 확인하려고 W-10 평가 세트 전체(checker 4후보 x 10사례, evaluator 3후보 x 8사례 x scope 2)를 다시 쟀다. 사례·후보·채점·채택 규칙(PLAN D-13)은 W-10과 같고, 바꾼 것은 이름·경로·호출 경로뿐이다.

1. **불투명 ID**: 사례 18건(checker 10 + evaluator 8)에 `c01`~`c18`을 한 풀에서 무작위로(`random.SystemRandom().shuffle`) 배정했다. checker와 evaluator ID가 섞여 있어 ID만으로 종류도 알 수 없다. 사례 라벨<->ID 매핑은 `run/eval2/mapping.json`에만 있고, 호출이 끝날 때까지는 작업 경로 밖(스크래치패드)에 두었다가 호출이 끝난 뒤 옮겼다. 프롬프트·cwd·경로에는 노출하지 않았다.
2. **경로·이름**: 임시 체크아웃 `<work>/n/cNN/repo`, evaluator fixture `<work>/fx/cNN`, receipt `…/cNN__K1/receipt.json`·`cNN__E1__design.json`, 출력 폴더 `…/cNN__K1/out`, raw 응답 `cNN__K1.json`. `pass`/`defect`/`syn-`/태스크 번호/결함 종류는 쓰지 않았다. 호출 중 산출은 모두 스크래치패드 작업 폴더에 쓰고 끝난 뒤 `eval2/raw/`로 옮겼다(에이전트가 태스크 폴더의 라벨이 붙은 파일을 우연히 읽는 경로를 줄이려는 격리).
3. **프롬프트 검사**: checker 프롬프트 10종을 `pass|defect|syn-|16x|17x|eval` 정규식으로 검사했다. 라벨 문자열은 없고 `172`(모든 호출이 공유하는 저장소 워크트리 경로)만 나왔다. 단 한 사례의 `target_files`에 파일명 `test_red_s161_unit_contract.py`가 있어 `161`이 한 번 들어간다(아래 한계 1). evaluator 프롬프트는 fixture 경로가 `…/fx/cNN`이라 라벨이 없다. fixture의 `state.json`·`STATE.md`에도 `pass-`/`defect-` 문자열이 없음을 `grep`으로 확인했다.
4. **호출**: 88회 모두 정식 wrapper `~/.opal/tools/opal-agent/run.sh --json --model <별칭> [--effort <수준>] --allowed-tools Read,Grep,Glob,Bash --cwd <중립 경로> --opal-bootstrap off --timeout 300 --system-prompt "<저장소 opal/agents/<이름>/AGENT.md frontmatter 제외 본문>"`로 1회씩, 재시도 없이 실행했다(raw `claude -p` 없음). 후보 값은 W-10과 같다(K0 sonnet·미지정 / K1 sonnet·low / K2 sonnet·medium / K3 haiku·medium, E0 opus·미지정 / E1 opus·medium / E2 opus·high). cwd는 checker는 사례 체크아웃(`n/cNN/repo`), evaluator는 fixture 폴더(`fx/cNN`)다. 호출마다 `event-loader load --event worker.dispatch`로 receipt를 새로 만들고 `verify ok:true`를 확인한 뒤, 프롬프트에 receipt 경로와 절대경로 verify 명령을 실었다(88회 모두 receipt 단계 통과). wrapper의 `--opal-bootstrap off`가 첫 줄 `[WORKER]`를 붙이므로 프롬프트 본문에는 마커를 넣지 않았다.
5. **흐름·채점**: checker는 사전 검사 -> 변경 구간만 읽기 -> `merge`(최종 finding JSON을 채점), evaluator는 `scope: design`/`scope: scenario` 두 호출을 동시에 실행하고 실제 `state-tool design-gate combine`으로 결합한 verdict·FAIL 축을 채점한다. 동시 실행은 최대 6(evaluator 한 쌍은 슬롯 2). 사전 검사는 W-10 재집계 때 보정한 저장소 소스(`opal/tools/convention-precheck/`)를 그대로 쓴다.
6. **재사용한 코드**: `run/eval/build_cases.py`·`run_eval.py`를 `run/eval2/build_cases2.py`·`run_eval2.py`로 복사·수정했다(기존 `run/eval/`은 수정하지 않았다). `recompute_precheck.py`는 W-10 당시 사전 검사를 보정한 뒤 모델 응답을 재집계하려고 만든 것이라, 이번에는 보정된 사전 검사로 처음부터 쟀으므로 쓰지 않았다.

### 1.2 남은 누출·교란 (한계)

1. **사례 문서·체크아웃 내용의 번호와 라벨 성격**: 사례 문서(TASK/PLAN/TEST-SCENARIO)와 과거 사례 체크아웃은 내용 안에 태스크 번호(161·162·163·167~169 등)와 결함 서술을 그대로 담고 있다. 지시에 따라 바꾸지 않았다. 과거 4사례의 체크아웃은 detached HEAD로 실제 커밋 이력이 보이고(`git log`로 읽으면 제목이 보인다), 한 사례의 `target_files`에는 `s161`이 들어 있다. 에이전트가 이 내용을 라벨 대용으로 썼는지는 가를 수 없다.
2. **저장소 안의 라벨 파일**: 프롬프트·cwd에는 없지만, 에이전트가 쓰는 도구는 절대경로로 저장소(`task_172` 워크트리, 모든 호출의 `project_root`/skill 경로)를 읽을 수 있고 그 안에 `tasks/172-…/run/eval/`(라벨이 붙은 W-10 결과)와 `run/eval2/*.py`가 있다. 호출 중에 mapping.json은 작업 경로 밖에 있었지만 이 파일들은 있었다. 호출 87건의 최종 응답 텍스트에서 `pass-16x`·`defect-16x`·`run/eval/`·`EVAL-RESULT`·`eval2`·`mapping.json`·`W-10` 인용은 0건이었다. 도구 호출 기록(어떤 파일을 읽었는지)은 저장하지 않아 중간에 읽었는지는 확인하지 못했다.
3. **라벨 외 변경 요인이 함께 바뀌었다**: 중립판은 정식 wrapper(`--system-prompt`, 권한은 wrapper의 `--dangerously-skip-permissions`, `--max-turns` 없음, `--timeout 300`)로, W-10은 raw `claude -p --agents … --agent …`(`--permission-mode dontAsk`, `--max-turns` 80/50)로 호출했다. evaluator의 cwd도 저장소 루트에서 fixture 폴더로 바뀌었다. 따라서 4절의 차이는 "라벨 제거"만의 효과가 아니다. ADD-1의 통제 실험(조건 ①: wrapper+`--system-prompt`+라벨 경로 -> pass-161 2/2 PASS, 조건 ④: wrapper+중립 경로 -> 2/2 FAIL)이 호출 경로 변경만으로는 pass-161 변화가 설명되지 않음을 보였지만, 이번 측정이 모든 사례에서 그렇다는 것을 입증하지는 않는다.
4. **표본**: 사례x후보당 호출 1회, 동시 실행 6으로 소요에 호출 간 간섭이 섞인다. 같은 호출을 반복하지 않았으므로 판정이 달라진 행이 라벨 효과인지 표본 변동인지 이 측정만으로는 가를 수 없다(특히 후보 한 개에서만 뒤집힌 행).
5. **checker의 채점은 규칙 키+파일+심각도**라서 평가 단위가 라벨의 도움을 받기 어려운 구조다. 반대로 evaluator의 pass/fail 경계 판단(엄격도)은 라벨에 민감할 수 있다는 것이 ADD-1의 관찰이었고, 변화는 evaluator에서만 판정이 갈렸다(4절).

## 2. 측정 표 (불투명 ID 기준)

후보: checker K0 sonnet·미지정 / K1 sonnet·low / K2 sonnet·medium / K3 haiku·medium, evaluator E0 opus·미지정 / E1 opus·medium / E2 opus·high(W-10과 같다). ID<->사례 매핑은 `run/eval2/mapping.json`(4절 비교표에서만 사례명을 풀어 쓴다). 소요는 wrapper 프로세스 시작부터 JSON 수신까지 벽시계 초다. 동시 실행 최대 6.

### 2.1 checker (40행)

| 사례 | 후보 | 기대 | 실제 finding 요약 | 판정 일치 | High+ 누락 | pass 뒤집힘 | 소요(초) | 비고 |
|---|---|---|---|---|---|---|---|---|
| c02 | K0 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 59.4 | 턴 12, $0.26 |
| c02 | K1 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 38.2 | 턴 8, $0.27 |
| c02 | K2 | opal-doc-standard demo-guide.md(medium+) | 1건: medium/사전/doc-변경이력×1 | O | 0 | 0 | 46.1 | 턴 11, $0.30 |
| c02 | K3 | opal-doc-standard demo-guide.md(medium+) | 결과 없음 | 결과 없음 | - | - | 154.6 | 결과 없음: 최종 finding JSON(merge 결과) 미생성 |
| c04 | K0 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 41.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 8, $0.33 |
| c04 | K1 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 35.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 6, $0.27 |
| c04 | K2 | 언어 규칙 demo_tool.py(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 42.7 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.33 |
| c04 | K3 | 언어 규칙 demo_tool.py(info+) | finding 0건 | X | 0 | 0 | 109.8 | 누락: 언어 규칙(demo_tool.py); model findings dropped: out_of_range=4, mechanical_rule=0; 턴 16, $0.21 |
| c06 | K0 | High+ 0건 | finding 0건 | O | 0 | 0 | 48.2 | 턴 10, $0.33 |
| c06 | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 44.1 | 턴 10, $0.31 |
| c06 | K2 | High+ 0건 | 4건: low/모델/언어규칙×4 | O | 0 | 0 | 104.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 20, $0.64 |
| c06 | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 86.5 | 턴 14, $0.20 |
| c07 | K0 | High+ 0건 | finding 0건 | O | 0 | 0 | 62.9 | 턴 13, $0.48 |
| c07 | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 48.0 | 턴 10, $0.35 |
| c07 | K2 | High+ 0건 | 2건: low/모델/convention-categories §5 미사용×1; low/모델/convention-categories §4 죽은 ×1 | O | 0 | 0 | 85.2 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 20, $0.57 |
| c07 | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 176.8 | 턴 16, $0.29 |
| c09 | K0 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 34.9 | 턴 7, $0.27 |
| c09 | K1 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 28.4 | 턴 8, $0.24 |
| c09 | K2 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 38.7 | 턴 9, $0.29 |
| c09 | K3 | YAML Frontmatter SKILL.md(high+) | 1건: high/사전/frontmatter×1 | O | 0 | 0 | 111.3 | model findings dropped: out_of_range=0, mechanical_rule=2; 턴 18, $0.23 |
| c10 | K0 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 62.3 | 턴 11, $0.44 |
| c10 | K1 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 46.4 | 턴 9, $0.35 |
| c10 | K2 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 56.1 | 턴 12, $0.44 |
| c10 | K3 | @header test_event_loader_test_event.py(high+); @header test_state_tool_test_cycle.py(high+) | 2건: high/사전/@header×2 | O | 0 | 0 | 158.7 | 턴 17, $0.39 |
| c11 | K0 | High+ 0건 | 1건: low/모델/@header×1 | O | 0 | 0 | 74.1 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 17, $0.50 |
| c11 | K1 | High+ 0건 | finding 0건 | O | 0 | 0 | 37.4 | 턴 10, $0.27 |
| c11 | K2 | High+ 0건 | 1건: low/모델/header-standard.md §2.1 이력 비×1 | O | 0 | 0 | 64.6 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 16, $0.44 |
| c11 | K3 | High+ 0건 | finding 0건 | O | 0 | 0 | 142.8 | 턴 29, $0.35 |
| c12 | K0 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 27.4 | 턴 6, $0.24 |
| c12 | K1 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 30.8 | 턴 8, $0.25 |
| c12 | K2 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 37.1 | 턴 8, $0.29 |
| c12 | K3 | finding 없음(low 이하) | finding 0건 | O | 0 | 0 | 83.3 | 턴 15, $0.24 |
| c17 | K0 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 47.3 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.38 |
| c17 | K1 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 39.8 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 8, $0.29 |
| c17 | K2 | 언어 규칙 demo-guide.md(info+) | 1건: medium/모델/언어규칙×1 | O | 0 | 0 | 50.4 | model findings dropped: out_of_range=0, mechanical_rule=0; 턴 10, $0.36 |
| c17 | K3 | 언어 규칙 demo-guide.md(info+) | finding 0건 | X | 0 | 0 | 121.4 | 누락: 언어 규칙(demo-guide.md); model findings dropped: out_of_range=1, mechanical_rule=0; 턴 18, $0.33 |
| c18 | K0 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 46.0 | 턴 9, $0.32 |
| c18 | K1 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 40.3 | 턴 10, $0.30 |
| c18 | K2 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 42.6 | 턴 9, $0.29 |
| c18 | K3 | 파일/폴더 demoHelper.py(medium+) | 1건: medium/사전/파일명×1 | O | 0 | 0 | 91.3 | 턴 16, $0.28 |

### 2.2 evaluator 호출별 (48행)

| 사례 | 후보 | scope | 기대 | 실제 | 소요(초) | 비고 |
|---|---|---|---|---|---|---|
| c01 | E0 | design | design 4축 PASS | FAIL 축: 없음 | 87.5 | 턴 11, $0.69 |
| c01 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 51.7 | 턴 5, $0.52 |
| c01 | E1 | design | design 4축 PASS | FAIL 축: decision_clarity,recoverability | 96.3 | 턴 8, $0.64 |
| c01 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 46.4 | 턴 3, $0.34 |
| c01 | E2 | design | design 4축 PASS | FAIL 축: 없음 | 128.5 | 턴 15, $0.98 |
| c01 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 3건 | 76.7 | 턴 4, $0.46 |
| c03 | E0 | design | design 4축 PASS | FAIL 축: decision_clarity | 82.1 | 턴 6, $0.68 |
| c03 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 49.4 | 턴 5, $0.57 |
| c03 | E1 | design | design 4축 PASS | FAIL 축: decision_clarity | 69.0 | 턴 4, $0.50 |
| c03 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 50.3 | 턴 4, $0.45 |
| c03 | E2 | design | design 4축 PASS | FAIL 축: decision_clarity | 100.8 | 턴 9, $0.82 |
| c03 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 70.4 | 턴 8, $0.69 |
| c05 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 33.3 | 턴 3, $0.41 |
| c05 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 39.3 | 턴 4, $0.42 |
| c05 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability | 37.1 | 턴 3, $0.29 |
| c05 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 62.4 | 턴 7, $0.45 |
| c05 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 52.3 | 턴 7, $0.44 |
| c05 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 45.4 | 턴 5, $0.32 |
| c08 | E0 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 52.4 | 턴 3, $0.44 |
| c08 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 57.5 | 턴 6, $0.51 |
| c08 | E1 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 67.9 | 턴 8, $0.46 |
| c08 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 46.4 | 턴 5, $0.33 |
| c08 | E2 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 70.5 | 턴 6, $0.61 |
| c08 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/0 평균 1.0, advisory 0건 | 64.0 | 턴 9, $0.47 |
| c13 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: decision_clarity,executability | 52.3 | 턴 5, $0.47 |
| c13 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 0건 | 43.7 | 턴 4, $0.43 |
| c13 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: decision_clarity,executability | 44.2 | 턴 4, $0.32 |
| c13 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 71.7 | 턴 7, $0.44 |
| c13 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: decision_clarity,executability | 57.8 | 턴 8, $0.41 |
| c13 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/0 평균 0.67, advisory 0건 | 70.4 | 턴 6, $0.58 |
| c14 | E0 | design | design 4축 PASS | FAIL 축: 없음 | 88.9 | 턴 8, $0.88 |
| c14 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/2/2 평균 2.0, advisory 0건 | 59.8 | 턴 9, $0.78 |
| c14 | E1 | design | design 4축 PASS | FAIL 축: 없음 | 170.2 | 턴 20, $1.28 |
| c14 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/1/2 평균 1.67, advisory 0건 | 81.0 | 턴 7, $0.61 |
| c14 | E2 | design | design 4축 PASS | FAIL 축: completeness,recoverability | 156.0 | 턴 16, $1.38 |
| c14 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 2/1/2 평균 1.67, advisory 1건 | 104.4 | 턴 9, $0.67 |
| c15 | E0 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 44.0 | 턴 3, $0.43 |
| c15 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 1건 | 47.3 | 턴 6, $0.48 |
| c15 | E1 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 43.5 | 턴 4, $0.32 |
| c15 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 1건 | 38.4 | 턴 3, $0.29 |
| c15 | E2 | design | design 4축 중 decision_clarity FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 51.3 | 턴 4, $0.31 |
| c15 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 0/2/1 평균 1.0, advisory 1건 | 64.8 | 턴 5, $0.40 |
| c16 | E0 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: decision_clarity,executability | 49.9 | 턴 3, $0.44 |
| c16 | E0 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/2 평균 1.67, advisory 0건 | 38.0 | 턴 3, $0.40 |
| c16 | E1 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability,recoverability | 47.7 | 턴 4, $0.31 |
| c16 | E1 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/1 평균 1.33, advisory 0건 | 67.1 | 턴 7, $0.39 |
| c16 | E2 | design | design 4축 중 decision_clarity·executability FAIL | FAIL 축: completeness,decision_clarity,executability | 63.2 | 턴 8, $0.60 |
| c16 | E2 | scenario | 시나리오 3축 ≥1(평균 ≥1.5) | 점수 1/2/2 평균 1.67, advisory 0건 | 71.6 | 턴 5, $0.37 |

### 2.3 evaluator 결합 (실제 `design-gate combine`, 24행)

| 사례 | 후보 | 기대 verdict | 결합 verdict | 기대 실패 축 | 실제 FAIL 축 | verdict 일치 | 결함 누락 | pass 뒤집힘 | design 소요(초) | scenario 소요(초) | 결합 소요(초) | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c01 | E0 | pass | pass | - | 없음 | O | 0 | 0 | 87.5 | 51.7 | 87.5 | 쌍 벽시계 87.5; rewrite_target=None |
| c01 | E1 | pass | fail | - | decision_clarity,recoverability | X | 0 | 1 | 96.3 | 46.4 | 96.3 | 쌍 벽시계 96.3; rewrite_target=plan |
| c01 | E2 | pass | pass | - | 없음 | O | 0 | 0 | 128.5 | 76.7 | 128.5 | 쌍 벽시계 128.5; rewrite_target=None |
| c03 | E0 | pass | fail | - | decision_clarity | X | 0 | 1 | 82.1 | 49.4 | 82.1 | 쌍 벽시계 82.2; rewrite_target=plan |
| c03 | E1 | pass | fail | - | decision_clarity | X | 0 | 1 | 69.0 | 50.3 | 69.0 | 쌍 벽시계 69.0; rewrite_target=plan |
| c03 | E2 | pass | fail | - | decision_clarity | X | 0 | 1 | 100.8 | 70.4 | 100.8 | 쌍 벽시계 100.8; rewrite_target=plan |
| c05 | E0 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 33.3 | 39.3 | 39.3 | 쌍 벽시계 39.3; rewrite_target=both |
| c05 | E1 | fail | fail | decision_clarity | completeness,decision_clarity,executability | O | 0 | 0 | 37.1 | 62.4 | 62.4 | 쌍 벽시계 62.4; rewrite_target=both |
| c05 | E2 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 52.3 | 45.4 | 52.3 | 쌍 벽시계 52.3; rewrite_target=both |
| c08 | E0 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 52.4 | 57.5 | 57.5 | 쌍 벽시계 57.5; rewrite_target=both |
| c08 | E1 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 67.9 | 46.4 | 67.9 | 쌍 벽시계 67.9; rewrite_target=both |
| c08 | E2 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 70.5 | 64.0 | 70.5 | 쌍 벽시계 70.5; rewrite_target=both |
| c13 | E0 | fail | fail | decision_clarity | decision_clarity,executability | O | 0 | 0 | 52.3 | 43.7 | 52.3 | 쌍 벽시계 52.3; rewrite_target=both |
| c13 | E1 | fail | fail | decision_clarity | decision_clarity,executability | O | 0 | 0 | 44.2 | 71.7 | 71.7 | 쌍 벽시계 71.7; rewrite_target=both |
| c13 | E2 | fail | fail | decision_clarity | decision_clarity,executability | O | 0 | 0 | 57.8 | 70.4 | 70.4 | 쌍 벽시계 70.4; rewrite_target=both |
| c14 | E0 | pass | pass | - | 없음 | O | 0 | 0 | 88.9 | 59.8 | 88.9 | 쌍 벽시계 88.9; rewrite_target=None |
| c14 | E1 | pass | pass | - | 없음 | O | 0 | 0 | 170.2 | 81.0 | 170.2 | 쌍 벽시계 170.2; rewrite_target=None |
| c14 | E2 | pass | fail | - | completeness,recoverability | X | 0 | 1 | 156.0 | 104.4 | 156.0 | 쌍 벽시계 156.0; rewrite_target=plan |
| c15 | E0 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 44.0 | 47.3 | 47.3 | 쌍 벽시계 47.3; rewrite_target=both |
| c15 | E1 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 43.5 | 38.4 | 43.5 | 쌍 벽시계 43.5; rewrite_target=both |
| c15 | E2 | fail | fail | decision_clarity | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 51.3 | 64.8 | 64.8 | 쌍 벽시계 64.8; rewrite_target=both |
| c16 | E0 | fail | fail | decision_clarity,executability | decision_clarity,executability | O | 0 | 0 | 49.9 | 38.0 | 49.9 | 쌍 벽시계 49.9; rewrite_target=plan |
| c16 | E1 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability,recoverability | O | 0 | 0 | 47.7 | 67.1 | 67.1 | 쌍 벽시계 67.1; rewrite_target=both |
| c16 | E2 | fail | fail | decision_clarity,executability | completeness,decision_clarity,executability | O | 0 | 0 | 63.2 | 71.6 | 71.6 | 쌍 벽시계 71.7; rewrite_target=plan |

## 3. 후보별 채택 판정 (D-13 규칙, 중립 경로)

규칙: 결함을 놓친 건수 0 AND pass 사례를 뒤집은 건수 0이면 "채택 가능"이고, checker는 사전 검사 finding과 합산해 High 이상 누락 0건이어야 한다. 결과 없음·미실행이 있으면 측정 불완전으로 "채택 불가"로 둔다(W-10과 같은 해석).

| 후보 | 대상 | 결과 있음/전체 | 결함·High+ 누락 | pass 뒤집힘 | 중립 판정 | 이유 | W-10(라벨) 판정 |
|---|---|---|---|---|---|---|---|
| K0 | checker | 10/10 | 0 | 0 | 채택 가능 | - | 채택 가능 |
| K1 | checker | 10/10 | 0 | 0 | 채택 가능 | - | 채택 가능 |
| K2 | checker | 10/10 | 0 | 0 | 채택 가능 | - | 채택 가능 |
| K3 | checker | 9/10 | 0 | 0 | 채택 불가 | 결과 없음/미실행 1건 | 채택 가능 |
| E0 | evaluator | 8/8 | 0 | 1 | 채택 불가 | pass 뒤집힘 1건 | 채택 가능 |
| E1 | evaluator | 8/8 | 0 | 2 | 채택 불가 | pass 뒤집힘 2건 | 채택 가능 |
| E2 | evaluator | 8/8 | 0 | 2 | 채택 불가 | pass 뒤집힘 2건 | 채택 가능 |

### 3.1 checker pass 뒤집힘의 출처 (참고)

| 후보 | pass 뒤집힘 | 사전 검사 finding만으로 발생 | 모델 finding이 관여한 뒤집힘 |
|---|---|---|---|
| K0 | 0 | 0 | 0 |
| K1 | 0 | 0 | 0 |
| K2 | 0 | 0 | 0 |
| K3 | 0 | 0 | 0 |

## 4. W-10 라벨 버전과의 비교

### 4.1 checker (사례 x 후보 40행)

`finding 집합`은 (규칙 앞 40자, 파일, severity) 집합을 최종 finding JSON에서 비교한 값이다(동일 / 다름 +추가 -사라짐). 라벨판 최종 JSON은 W-10 재집계 후 값이다.

| 사례 | 후보 | 라벨판 일치/High+누락/뒤집힘/finding 수 | 중립판 일치/High+누락/뒤집힘/finding 수 | finding 집합 | 소요 라벨판->중립판(초) | 변화 |
|---|---|---|---|---|---|---|
| syn-m2-changelog-section (c02) | K0 | O/0/0/1 | O/0/0/1 | 동일 | 41.6->59.4 |  |
| syn-m2-changelog-section (c02) | K1 | O/0/0/1 | O/0/0/1 | 동일 | 26.6->38.2 |  |
| syn-m2-changelog-section (c02) | K2 | O/0/0/1 | O/0/0/1 | 동일 | 34.0->46.1 |  |
| syn-m2-changelog-section (c02) | K3 | O/0/0/1 | 결과 없음 | 비교 불가 | 158.2->154.6 | 변화 |
| syn-j1-korean-identifier (c04) | K0 | O/0/0/1 | O/0/0/1 | 동일 | 34.5->41.6 |  |
| syn-j1-korean-identifier (c04) | K1 | O/0/0/1 | O/0/0/1 | 동일 | 37.4->35.2 |  |
| syn-j1-korean-identifier (c04) | K2 | O/0/0/1 | O/0/0/1 | 동일 | 43.9->42.7 |  |
| syn-j1-korean-identifier (c04) | K3 | X/0/0/0 | X/0/0/0 | 동일 | 105.8->109.8 |  |
| 163-pass (c06) | K0 | O/0/0/0 | O/0/0/0 | 동일 | 48.2->48.2 |  |
| 163-pass (c06) | K1 | O/0/0/0 | O/0/0/0 | 동일 | 30.8->44.1 |  |
| 163-pass (c06) | K2 | O/0/0/0 | O/0/0/4 | 다름 +4 -0 | 51.0->104.2 | 변화 |
| 163-pass (c06) | K3 | O/0/0/0 | O/0/0/0 | 동일 | 154.2->86.5 |  |
| 161-pass (c07) | K0 | O/0/0/0 | O/0/0/0 | 동일 | 64.7->62.9 |  |
| 161-pass (c07) | K1 | O/0/0/0 | O/0/0/0 | 동일 | 49.2->48.0 |  |
| 161-pass (c07) | K2 | O/0/0/0 | O/0/0/2 | 다름 +2 -0 | 46.1->85.2 | 변화 |
| 161-pass (c07) | K3 | O/0/0/0 | O/0/0/0 | 동일 | 108.6->176.8 |  |
| syn-m1-skill-no-description (c09) | K0 | O/0/0/1 | O/0/0/1 | 동일 | 24.2->34.9 |  |
| syn-m1-skill-no-description (c09) | K1 | O/0/0/1 | O/0/0/1 | 동일 | 25.0->28.4 |  |
| syn-m1-skill-no-description (c09) | K2 | O/0/0/1 | O/0/0/1 | 동일 | 30.2->38.7 |  |
| syn-m1-skill-no-description (c09) | K3 | O/0/0/1 | O/0/0/1 | 동일 | 114.9->111.3 |  |
| 162-defect (c10) | K0 | O/0/0/2 | O/0/0/2 | 동일 | 57.1->62.3 |  |
| 162-defect (c10) | K1 | O/0/0/2 | O/0/0/2 | 동일 | 40.0->46.4 |  |
| 162-defect (c10) | K2 | O/0/0/2 | O/0/0/2 | 동일 | 48.4->56.1 |  |
| 162-defect (c10) | K3 | O/0/0/2 | O/0/0/2 | 동일 | 187.4->158.7 |  |
| 169-pass (c11) | K0 | O/0/0/0 | O/0/0/1 | 다름 +1 -0 | 43.5->74.1 | 변화 |
| 169-pass (c11) | K1 | O/0/0/0 | O/0/0/0 | 동일 | 32.9->37.4 |  |
| 169-pass (c11) | K2 | O/0/0/0 | O/0/0/1 | 다름 +1 -0 | 47.9->64.6 | 변화 |
| 169-pass (c11) | K3 | O/0/0/0 | O/0/0/0 | 동일 | 125.0->142.8 |  |
| syn-ok-clean (c12) | K0 | O/0/0/0 | O/0/0/0 | 동일 | 29.3->27.4 |  |
| syn-ok-clean (c12) | K1 | O/0/0/0 | O/0/0/0 | 동일 | 22.7->30.8 |  |
| syn-ok-clean (c12) | K2 | O/0/0/0 | O/0/0/0 | 동일 | 28.5->37.1 |  |
| syn-ok-clean (c12) | K3 | O/0/0/0 | O/0/0/0 | 동일 | 123.5->83.3 |  |
| syn-j2-english-doc-section (c17) | K0 | O/0/0/1 | O/0/0/1 | 동일 | 33.8->47.3 |  |
| syn-j2-english-doc-section (c17) | K1 | O/0/0/1 | O/0/0/1 | 동일 | 32.9->39.8 |  |
| syn-j2-english-doc-section (c17) | K2 | O/0/0/1 | O/0/0/1 | 동일 | 77.0->50.4 |  |
| syn-j2-english-doc-section (c17) | K3 | O/0/0/1 | X/0/0/0 | 다름 +0 -1 | 133.8->121.4 | 변화 |
| syn-m3-camelcase-py (c18) | K0 | O/0/0/1 | O/0/0/1 | 동일 | 22.3->46.0 |  |
| syn-m3-camelcase-py (c18) | K1 | O/0/0/1 | O/0/0/1 | 동일 | 25.6->40.3 |  |
| syn-m3-camelcase-py (c18) | K2 | O/0/0/1 | O/0/0/1 | 동일 | 29.9->42.6 |  |
| syn-m3-camelcase-py (c18) | K3 | O/0/0/1 | O/0/0/1 | 동일 | 112.6->91.3 |  |

변화가 있는 행: 6/40.

### 4.2 evaluator 결합 (사례 x 후보 24행)

| 사례 | 후보 | 기대 verdict | 라벨판 결합 verdict / FAIL 축 | 중립판 결합 verdict / FAIL 축 | 라벨판 결함누락/뒤집힘 | 중립판 결함누락/뒤집힘 | 결합 소요 라벨판->중립판(초) | 변화 |
|---|---|---|---|---|---|---|---|---|
| pass-163 (c01) | E0 | pass | pass / 없음 | pass / 없음 | 0/0 | 0/0 | 41.2->87.5 |  |
| pass-163 (c01) | E1 | pass | pass / 없음 | fail / decision_clarity,recoverability | 0/0 | 0/1 | 61.0->96.3 | 변화 |
| pass-163 (c01) | E2 | pass | pass / 없음 | pass / 없음 | 0/0 | 0/0 | 56.1->128.5 |  |
| pass-161 (c03) | E0 | pass | pass / 없음 | fail / decision_clarity | 0/0 | 0/1 | 66.9->82.1 | 변화 |
| pass-161 (c03) | E1 | pass | pass / 없음 | fail / decision_clarity | 0/0 | 0/1 | 54.5->69.0 | 변화 |
| pass-161 (c03) | E2 | pass | pass / 없음 | fail / decision_clarity | 0/0 | 0/1 | 77.1->100.8 | 변화 |
| defect-168-i2 (c05) | E0 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 50.7->39.3 |  |
| defect-168-i2 (c05) | E1 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability | 0/0 | 0/0 | 51.7->62.4 | 변화 |
| defect-168-i2 (c05) | E2 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 62.7->52.3 |  |
| defect-162-i1 (c08) | E0 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 51.3->57.5 |  |
| defect-162-i1 (c08) | E1 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 67.6->67.9 |  |
| defect-162-i1 (c08) | E2 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 84.7->70.5 |  |
| defect-167-i2 (c13) | E0 | fail | fail / decision_clarity,executability | fail / decision_clarity,executability | 0/0 | 0/0 | 73.7->52.3 |  |
| defect-167-i2 (c13) | E1 | fail | fail / completeness,decision_clarity,executability | fail / decision_clarity,executability | 0/0 | 0/0 | 47.4->71.7 | 변화 |
| defect-167-i2 (c13) | E2 | fail | fail / completeness,decision_clarity,executability | fail / decision_clarity,executability | 0/0 | 0/0 | 81.8->70.4 | 변화 |
| pass-169 (c14) | E0 | pass | pass / 없음 | pass / 없음 | 0/0 | 0/0 | 67.2->88.9 |  |
| pass-169 (c14) | E1 | pass | pass / 없음 | pass / 없음 | 0/0 | 0/0 | 61.5->170.2 |  |
| pass-169 (c14) | E2 | pass | pass / 없음 | fail / completeness,recoverability | 0/0 | 0/1 | 108.5->156.0 | 변화 |
| defect-169-i2 (c15) | E0 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 50.1->47.3 |  |
| defect-169-i2 (c15) | E1 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 49.8->43.5 |  |
| defect-169-i2 (c15) | E2 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 70.2->64.8 |  |
| defect-163-i1 (c16) | E0 | fail | fail / completeness,decision_clarity,executability | fail / decision_clarity,executability | 0/0 | 0/0 | 57.6->49.9 | 변화 |
| defect-163-i1 (c16) | E1 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability,recoverability | 0/0 | 0/0 | 64.5->67.1 |  |
| defect-163-i1 (c16) | E2 | fail | fail / completeness,decision_clarity,executability,recoverability | fail / completeness,decision_clarity,executability | 0/0 | 0/0 | 85.3->71.6 | 변화 |

변화가 있는 행(결합 verdict 또는 FAIL 축 집합): 10/24.

### 4.3 달라진 판정 요약 (자동 집계)

| 후보 | 라벨판(W-10): 결과 있음/전체 · 누락 · 뒤집힘 · 불일치 | 중립판: 결과 있음/전체 · 누락 · 뒤집힘 · 불일치 |
|---|---|---|
| K0 checker | 10/10 · 0 · 0 · 0 | 10/10 · 0 · 0 · 0 |
| K1 checker | 10/10 · 0 · 0 · 0 | 10/10 · 0 · 0 · 0 |
| K2 checker | 10/10 · 0 · 0 · 0 | 10/10 · 0 · 0 · 0 |
| K3 checker | 10/10 · 0 · 0 · 1 | 9/10 · 0 · 0 · 2 |
| E0 evaluator | 8/8 · 0 · 0 · 0 | 8/8 · 0 · 1 · 1 |
| E1 evaluator | 8/8 · 0 · 0 · 0 | 8/8 · 0 · 2 · 2 |
| E2 evaluator | 8/8 · 0 · 0 · 0 | 8/8 · 0 · 2 · 2 |

evaluator 변화 행:

- pass-163 (c01) E1: 라벨판 pass / 없음 -> 중립판 fail / decision_clarity,recoverability
- pass-161 (c03) E0: 라벨판 pass / 없음 -> 중립판 fail / decision_clarity
- pass-161 (c03) E1: 라벨판 pass / 없음 -> 중립판 fail / decision_clarity
- pass-161 (c03) E2: 라벨판 pass / 없음 -> 중립판 fail / decision_clarity
- defect-168-i2 (c05) E1: 라벨판 fail / completeness,decision_clarity,executability,recoverability -> 중립판 fail / completeness,decision_clarity,executability
- defect-167-i2 (c13) E1: 라벨판 fail / completeness,decision_clarity,executability -> 중립판 fail / decision_clarity,executability
- defect-167-i2 (c13) E2: 라벨판 fail / completeness,decision_clarity,executability -> 중립판 fail / decision_clarity,executability
- pass-169 (c14) E2: 라벨판 pass / 없음 -> 중립판 fail / completeness,recoverability
- defect-163-i1 (c16) E0: 라벨판 fail / completeness,decision_clarity,executability -> 중립판 fail / decision_clarity,executability
- defect-163-i1 (c16) E2: 라벨판 fail / completeness,decision_clarity,executability,recoverability -> 중립판 fail / completeness,decision_clarity,executability

checker 변화 행:

- syn-m2-changelog-section (c02) K3: 라벨판 O/0/0/1 -> 중립판 결과 없음, finding 집합 비교 불가
- 163-pass (c06) K2: 라벨판 O/0/0/0 -> 중립판 O/0/0/4, finding 집합 다름 +4 -0
- 161-pass (c07) K2: 라벨판 O/0/0/0 -> 중립판 O/0/0/2, finding 집합 다름 +2 -0
- 169-pass (c11) K0: 라벨판 O/0/0/0 -> 중립판 O/0/0/1, finding 집합 다름 +1 -0
- 169-pass (c11) K2: 라벨판 O/0/0/0 -> 중립판 O/0/0/1, finding 집합 다름 +1 -0
- syn-j2-english-doc-section (c17) K3: 라벨판 O/0/0/1 -> 중립판 X/0/0/0, finding 집합 다름 +0 -1

## 5. 결론

### 5.1 후보별 (중립 경로, D-13 규칙)

- **checker**: K0·K1·K2는 10/10 결과, High+ 누락 0, pass 뒤집힘 0으로 **채택 가능**이고 W-10 판정과 같다. K3(haiku·medium)는 사례 1건(합성 문서 규칙 사례)에서 최종 finding JSON을 만들지 못해(결과 없음, 타임아웃 아님) **채택 불가**로 바뀌었다(W-10은 10/10 채택 가능이었다). K3는 판단 사례 2건 모두 finding 0건으로 놓쳐(W-10은 1건) 판정 일치 아닌 행이 늘었지만, 놓친 심각도는 medium 이하라 D-13 누락에는 들지 않는다. 캡틴이 확정한 **K1(sonnet+low)은 중립 측정에서도 채택 가능**이다. 중립판에서 과거 통과 구간 사례 3건 중 K0는 1건, K2는 3건에서 low 심각도 finding을 더 냈고(K1·K3는 내지 않았다), 모두 High 미만이라 뒤집힘이 아니다.
- **evaluator**: E0·E1·E2 **세 후보 모두 채택 불가**다(W-10은 셋 다 채택 가능). 결함 누락은 세 후보 모두 0이고(결함 15행 모두 fail), pass 뒤집힘이 E0 1건·E1 2건·E2 2건이다. 캡틴이 확정한 **E1(opus+medium)은 중립 측정에서 "채택 가능"이 아니다.**
  - pass-161 사례는 세 후보 모두 fail로 뒤집었다. 지적은 D-4 incomplete 사유 우선순위, `required: false` 계층 실패 처리, `file_globs` 매칭 기준 등 `decision_clarity`로, ADD-1이 중립 경로에서 반복해 본 지점과 같다. 세 후보에서 같은 사례가 뒤집혔으므로 effort는 이 사례를 가르지 못한다.
  - E1만 pass-163 사례를 fail(decision_clarity·recoverability)로, E2만 pass-169 사례를 fail(completeness·recoverability)로 뒤집었다. 각 사례에서 다른 두 후보는 pass였다. 한 후보에서만 일어난 뒤집힘이라 effort 효과와 1회 표본 변동을 이 측정으로 가를 수 없다.
  - 현행 E0도 D-13의 "pass 뒤집힘 0"을 중립 경로에서 충족하지 못한다. 즉 기준선 자체가 라벨 없이는 안정적이지 않다(pass-161이 기대 pass인 출처는 170의 pass 판정 기록이다).
  - 참고(채택 규칙 밖의 탐색적 읽기): pass-161을 "문서가 닫히지 않은 사례"로 제외하면 뒤집힘은 E0 0건·E1 1건·E2 1건이 되어 E0이 가장 깨끗하다. 규칙을 사후에 바꾸는 것이므로 판정에는 쓰지 않았다.
- **결합 verdict 일치(H-2)**: W-10은 24/24 일치였으나 중립판은 19/24다. 불일치 5행은 모두 pass 사례를 fail로 판정한 위 뒤집힘이다(pass-161 3행·pass-163 E1·pass-169 E2). 결함 사례 15행은 결합 verdict가 모두 fail이고 기대 실패 축을 놓친 행이 없다. 다만 기대 축 외의 FAIL 축 집합은 후보·사례별로 달라졌다(4.2의 변화 행).

### 5.2 추천 (결정은 캡틴)

- **checker**: 채택 가능 후보는 K0·K1·K2이고 평균 소요가 가장 짧은 K1(sonnet+low)이 캡틴 확정값과 같다. 이 측정에서는 K1을 기준으로 K0가 약 1.3배, K2가 약 1.5배, K3가 약 3배였다(6절). 중립 측정이 K1을 뒤집지 않았다.
- **evaluator**: 중립 측정에서 D-13을 만족하는 후보가 없다. D-13 규칙을 그대로 따르면 C-3에 따라 현행(E0, opus·effort 미지정) 유지가 기본이다. 소요는 E0가 가장 짧아(E1 약 1.3배, E2 약 1.4배) "소요가 짧은 후보"도 E0이고, 라벨판에서 보였던 "E1이 E0과 소요가 같다"는 관찰은 중립판에서 유지되지 않았다(6절). E1(opus+medium)을 쓰려면 D-13 기준 완화나 pass 기대 사례의 재검토(ADD-1 권고: 기대 verdict 대신 단일/병렬 일치로 보기) 결정이 먼저 필요하다. 이는 규칙·사례 정의에 대한 캡틴 결정 사항이다.

### 5.3 주의

- 이 측정으로 "W-10 24/24 일치는 라벨 효과였다"고 단정하지 못한다. 중립판은 호출 경로와 cwd도 함께 바뀌었고, 뒤집힘은 pass 사례 9행(3 사례 x 3 후보) 중 5행에 집중되어 있어 라벨 효과와 일치하는 방향이지만 표본 1회다. 결함 사례에서는 판정(fail)이 모두 유지됐다.
- 위 수치는 후보 간·라벨판 대비 상대 비교용이며 절대 오탐/누락률 주장이 아니다.

## 6. 소요 비교

evaluator 소요는 결합 소요(두 호출 중 긴 쪽), checker 소요는 호출 1건 벽시계다. 평균은 결과 있는 행 기준이며 1회 측정이다. 중립판은 정식 wrapper(`--dangerously-skip-permissions`형 권한, 호출당 프로세스 오버헤드 포함)로 측정해 라벨판(raw `claude -p`)과 호출 경로가 달라 라벨판 대비 값은 경로 차이와 사례 라벨 차이가 섞여 있다. 후보 간 상대 비교(같은 판 안)를 우선 읽는다.

| 후보 | 대상 | 중립판 평균 | 중립판 중앙값 | 중립판 최대 | 중립판 기준 같은 대상 최단 후보 대비 | 라벨판 평균 | 중립판/라벨판 평균 비 |
|---|---|---|---|---|---|---|---|
| K0 | checker | 50.4 | 48.2 | 74.1 | 1.30x | 39.9 | 1.26x |
| K1 | checker | 38.9 | 39.8 | 48.0 | 1.00x | 32.3 | 1.20x |
| K2 | checker | 56.8 | 50.4 | 104.2 | 1.46x | 43.7 | 1.30x |
| K3 | checker | 120.2 | 111.3 | 176.8 | 3.09x | 132.4 | 0.91x |
| E0 | evaluator | 63.1 | 57.5 | 88.9 | 1.00x | 57.3 | 1.10x |
| E1 | evaluator | 81.0 | 69.0 | 170.2 | 1.28x | 57.2 | 1.42x |
| E2 | evaluator | 89.4 | 71.6 | 156.0 | 1.42x | 78.3 | 1.14x |

### 6.1 모든 후보에 결과가 있는 사례만의 평균 (checker, 초)

| 후보 | 공통 사례 수 | 평균 | K1 대비 |
|---|---|---|---|
| K0 | 9 | 49.4 | 1.27x |
| K1 | 9 | 38.9 | 1.00x |
| K2 | 9 | 58.0 | 1.49x |
| K3 | 9 | 120.2 | 3.09x |

### 6.2 evaluator 쌍 벽시계 평균과 개별 합 (중립판, 초)

| 후보 | 결합 소요 평균 | 쌍 벽시계 평균 | design 호출 평균 | scenario 호출 평균 |
|---|---|---|---|---|
| E0 | 63.1 | 63.1 | 61.3 | 48.3 |
| E1 | 81.0 | 81.0 | 72.0 | 58.0 |
| E2 | 89.4 | 89.4 | 85.0 | 71.0 |

