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
