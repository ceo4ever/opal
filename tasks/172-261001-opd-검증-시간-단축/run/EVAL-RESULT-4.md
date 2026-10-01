<!--
ADD-3 evaluator 평가 세트 정비와 low 포함 재측정 결과(형식 오류 빈도 포함). 후보 E0(opus)·E1(opus medium)·E3(opus low), 사례 11건 x 3회.
규칙 SSOT는 run/eval3/RULES.md(호출 전 고정). 집계는 run/eval3/run_eval3.py --aggregate가 만든 run/eval3/results4.json이고, 표는 run/eval3/report_tables4.py가 results4.json에서 만든다.
원본: run/eval3/raw/(호출 응답 198건·receipt·combine), 지적 판정: run/eval3/adjudication.md, 방법(불투명 ID·중립 경로): run/eval2/notes-method.md.
-->
# EVAL-RESULT-4: 정비한 평가 세트에서 E0·E1·E3 재측정 (형식 오류 빈도 포함)

99 trial(198 호출) 모두 결과를 얻었다. 모델 응답 측 형식 오류는 0건이다. 사전 고정 규칙으로 채택 가능한 후보는 없다(세 후보 모두 규칙 2 미달). 이 측정은 계정 한도 장애로 한 번 중단·재실행되었고, 이는 규칙 문면에서 벗어난 결정이라 §5에 밝힌다.

## 1. 조건과 사전 고정 규칙

- 규칙 파일 `run/eval3/RULES.md`, sha256 `e4dbf27426d389083f2e0e26d66d214ad14286489bae91f1059e2325b9cf16ad`. 이 보고서 작성 시 `shasum -a 256`으로 다시 계산해 PM이 전달한 값과 같음을 확인했다.
- 규칙 요지(복제하지 않는다):
  1. 결함 누락: defect 15 trial 중 기대 실패 축을 놓친 trial = 0.
  2. clean 안정성: clean 9 trial 중 결합 verdict fail <= 2.
  3. 형식 오류: 후보당 66호출 중 <= 2. 형식 오류는 (a) 계약 JSON 없음 (b) JSON 문법 오류 (c) 필수 키·축·점수 누락 (d) 타임아웃·호출 실패.
  4. 결합 성립: 후보당 33 trial 중 결합 불성립 <= 3.
  - 네 조건을 모두 만족해야 채택 가능. borderline은 규칙 밖(fail 비율만 보고). 결합 결과가 없는 trial의 최악 가정 값은 참고치로만 쓴다. 호출 한 건의 실패는 재시도하지 않는다.
- 평가 세트 11건, 불투명 ID d01~d11: clean 3(원본 pass 3건에서 adjudication이 real로 본 항목만 닫은 판본), borderline 3(원본 pass 그대로), defect 5(기존 결함 5건 그대로). 라벨은 호출이 끝난 뒤 공개했다(§2.2).
- 후보: E0 `opus`(effort 미지정), E1 `opus --effort medium`, E3 `opus --effort low`. 11 x 3 x 반복 3 = 99 trial. trial마다 design·scenario 두 호출 = 198 호출, 결합(`design-gate combine`) 99건.
- 호출: 정식 wrapper `opal-agent`(`--json --allowed-tools Read,Grep,Glob,Bash --opal-bootstrap off --timeout 300`, evaluator AGENT.md 본문을 system prompt로), trial마다 fresh worker.dispatch receipt와 fresh fixture(폴더명은 불투명 토큰), trial 순서 무작위, 동시 6. 방법 상세는 `run/eval2/notes-method.md` 참조.

## 2. 측정 표

### 2.1 후보별 요약 (`results4.json`의 `cands`)

| 항목 | E0 | E1 | E3 |
|---|---|---|---|
| trial 수 (호출 수) | 33 (66) | 33 (66) | 33 (66) |
| 형식 오류 design/scenario/합계 | 0/0/0 | 0/0/0 | 0/0/0 |
| 결합 불성립 (33 중) | 0 | 0 | 0 |
| 결함 누락 (15 trial 중) | 0 (최악 가정 0) | 0 (최악 가정 0) | 0 (최악 가정 0) |
| clean fail (9 중) | 7 (최악 가정 7) | 8 (최악 가정 8) | 3 (최악 가정 3) |
| borderline fail (9 중, 규칙 밖) | 8 | 6 | 5 |
| 규칙 1 결함 누락 = 0 | O | O | O |
| 규칙 2 clean fail <= 2 | X | X | X |
| 규칙 3 형식 오류 <= 2 | O | O | O |
| 규칙 4 결합 불성립 <= 3 | O | O | O |
| 채택 가능 | 불가 | 불가 | 불가 |
| 결합 소요 평균/중앙/p90/최대(초) | 78.8/68.5/110.1/229.8 | 74.1/73.7/102.5/134.4 | 35.7/31.2/53.1/75.0 |

### 2.2 사례 x 후보 (rep1; rep2; rep3의 결합 verdict와 FAIL 축)

축 약어: comp=completeness, deci=decision_clarity, exec=executability, reco=recoverability. `x3`은 세 반복이 같은 값이다.

| ID | 라벨 | 종류 | 기대 | E0 | E1 | E3 |
|---|---|---|---|---|---|---|
| d01 | clean-pass-169 | clean | pass | pass; fail(comp,reco); pass | fail(reco); fail(deci,reco); pass | pass; pass; fail(comp) |
| d02 | clean-pass-163 | clean | pass | fail(comp,deci,exec,reco); fail(comp,deci,reco); fail(reco) | fail(comp,deci,exec,reco); fail(comp,deci,reco); fail(exec,reco) | fail(comp,exec); pass; pass |
| d10 | clean-pass-161 | clean | pass | fail(comp,deci) x3 | fail(deci); fail(comp,deci); fail(deci) | pass; pass; fail(exec) |
| d03 | borderline-pass-161 | borderline | pass | fail(deci); fail(deci); fail(comp,deci) | fail(deci) x3 | fail(deci); pass; pass |
| d05 | borderline-pass-163 | borderline | pass | fail(comp,reco); fail(reco); fail(comp,deci,reco) | fail(comp,deci,reco); fail(deci); fail(comp,deci,reco) | fail(deci); fail(comp,deci); fail(deci) |
| d07 | borderline-pass-169 | borderline | pass | fail(deci); fail(comp); pass | pass x3 | fail(comp); pass; pass |
| d04 | defect-162-i1 | defect | fail[deci,exec] | fail(comp,deci,exec,reco) x3 | fail(comp,deci,exec); fail(comp,deci,exec,reco); fail(comp,deci,exec,reco) | fail(comp,deci,exec,reco) x3 |
| d06 | defect-168-i2 | defect | fail[deci] | fail(comp,deci,exec,reco); fail(comp,deci,exec); fail(comp,deci,exec,reco) | fail(comp,deci,exec,reco) x3 | fail(comp,deci,exec,reco) x3 |
| d08 | defect-163-i1 | defect | fail[deci,exec] | fail(deci,exec); fail(comp,deci,exec); fail(comp,deci,exec,reco) | fail(deci,exec); fail(comp,deci,exec); fail(deci,exec) | fail(deci,exec) x3 |
| d09 | defect-169-i2 | defect | fail[deci] | fail(comp,deci,exec,reco) x3 | fail(comp,deci,exec,reco) x3 | fail(comp,deci,exec,reco) x3 |
| d11 | defect-167-i2 | defect | fail[deci] | fail(deci,exec); fail(comp,deci,exec); fail(comp,deci,exec) | fail(deci,exec); fail(comp,deci,exec); fail(deci,exec) | fail(deci,exec) x3 |

### 2.3 소요 (초)

| 후보 | 구분 | 평균 | 중앙 | p90 | 최대 |
|---|---|---|---|---|---|
| E0 | 결합 | 78.8 | 68.5 | 110.1 | 229.8 |
| E0 | design 호출 | 77.0 | 67.3 | 110.1 | 229.8 |
| E0 | scenario 호출 | 55.6 | 52.8 | 75.5 | 83.5 |
| E1 | 결합 | 74.1 | 73.7 | 102.5 | 134.4 |
| E1 | design 호출 | 72.1 | 73.7 | 102.5 | 134.4 |
| E1 | scenario 호출 | 54.6 | 54.8 | 65.7 | 84.4 |
| E3 | 결합 | 35.7 | 31.2 | 53.1 | 75.0 |
| E3 | design 호출 | 34.8 | 31.1 | 53.1 | 75.0 |
| E3 | scenario 호출 | 27.8 | 26.9 | 34.8 | 47.0 |

## 3. 채택 판정

| 후보 | 규칙 1 결함 누락 | 규칙 2 clean fail | 규칙 3 형식 오류 | 규칙 4 결합 불성립 | 판정 |
|---|---|---|---|---|---|
| E0 | 0/15 통과 | 7/9 미달 | 0/66 통과 | 0/33 통과 | 채택 불가 |
| E1 | 0/15 통과 | 8/9 미달 | 0/66 통과 | 0/33 통과 | 채택 불가 |
| E3 | 0/15 통과 | 3/9 미달(기준 <= 2에 1건 초과) | 0/66 통과 | 0/33 통과 | 채택 불가 |

- 결과가 없는 trial이 0건이라 보수적 참고치(결합 없음 최악 가정)는 판정값과 같다(결함 누락 0/0/0, clean fail 7/8/3). 99건 전체의 결합 불성립 합계도 0이다.
- PM이 전달한 실측값과 `results4.json`의 값은 후보별 요약 수치에서 모두 일치했다. 한 가지 차이: 전달 메모는 d01(clean-pass-169)의 E0 fail을 0/3으로 적었으나 `results4.json`은 1/3(rep2, `fail(comp,reco)`)이다. 이 보고서는 `results4.json` 값을 쓴다. 후보별 clean fail 합계(7/8/3)는 전달값과 같다.

## 4. 형식 오류

- 모델 응답 측 형식 오류(RULES (a)~(c), 모델이 낸 응답 결함)는 198호출 중 0건이다. 후보별 design·scenario 모두 0이다.
- (d)로 분류될 뻔한 호출 실패는 계정 한도 장애였다. 어떻게 다뤘는지는 §5에 있다. 최종 결과에 남은 99 trial에는 (d)로 센 호출이 없다.
- 이전 측정(EVAL-RESULT-3)에서 E3는 16호출 중 1건(c14 design)이 JSON 문법 오류였다. 이번 E3 66호출에서는 재현되지 않았다. 표본(이전 16, 이번 66)이 작고 사례 세트도 달라서 E3의 형식 안정성을 단정하지 않는다.

## 5. 측정 중단과 재실행 (규칙 이탈 선언)

사실관계.

1. 이 측정은 두 세션·두 Claude 계정에서 수행됐다. 첫 세션(다른 계정)이 99 trial을 돌리던 중 계정 세션 한도(HTTP 429)에 걸렸고, 63 trial(125호출)이 `claude 비정상 종료 (exit 1)`, 응답 없음, 소요 약 4초로 실패했다. 유효 trial은 36개였다.
2. PM(이 세션)이 이 63 trial의 결과·원본만 제거하고(토큰 목록은 `run/eval3/rate-limit-removed.json`의 `rate_limited_trials`) 같은 `plan.json`·같은 토큰·같은 사례/후보/반복으로 재실행했다. 36건의 유효 응답은 다시 호출하지 않았다.
3. 재실행 중 이 계정도 한도에 걸려 8 trial(15호출, 같은 exit 1 서명)이 실패했다(`round2_this_account`). 한도 해제 후 같은 방식으로 다시 실행했다.
4. 두 trial은 한 scope만 실패해 성공한 scope 응답을 보존하고 실패한 scope만 다시 호출했다: `tac845c`(d01 E3 r2, 첫 라운드에서 design만 실패)와 `tee12f9`(d05 E1 r1, 재실행 중 design만 실패). 이 두 trial은 design·scenario 호출 시각이 다르다.
5. 출처 추적: `run/eval3/run.log`의 `=== resume start ... ===`(라운드 1 재실행, 63 trial)와 `=== resume round2 ... ===`(8 trial) 구분선, 그리고 `rate-limit-removed.json`.

판정 기준과 이탈.

- RULES.md의 "한 호출의 실패는 재시도하지 않는다"는 모델 응답 실패(타임아웃·is_error·형식 오류)를 다루는 규칙이다. 계정 한도 장애는 모델이 입력을 받은 적이 없는 "미측정"이라서 형식 오류 (d)로 세지 않고 재실행했다.
- 이것은 사전 고정 규칙의 문면에서 벗어난 PM 결정이다. 분류 근거는 실패 서명이다: exit 1, stderr 공백, 응답 JSON 없음, 소요 4~30초, 두 세션 모두 한도 메시지 직후에 발생.
- 영향: verdict·FAIL 축·형식 오류율에는 영향이 없다(제거된 호출에는 모델 응답이 없었다). 소요는 두 계정·세 시각대(첫 세션 약 18:1x~18:3x, 재실행 18:39~20:0x, 2차 20:2x~20:3x)가 섞여 있으므로 후보 간 상대 비교로만 읽는다.

## 6. clean 세트 평가

clean 3건에서 결합 verdict가 fail인 18 trial(d10 7, d02 7, d01 4)의 design 응답(`raw/ev/<token>__design.json`의 `response.result` 안 JSON)에서 `design.gaps`를 읽고, `adjudication.md` 기준으로 주제 단위로 분류했다. 한 gap이 여러 주제를 담으면 주제별로 나눠 센다.

- (가) adjudication이 real로 판정해 clean 판본에서 닫은 항목(A1~A5·A8·B1·C1~C6)의 재발
- (나) adjudication이 not-real로 둔 항목(A6·A7·B2·B3·B4)과 같은 주제
- (다) 이전 측정에 없던 새 지적(위 어느 항목에도 해당하지 않음)

이 절은 지적의 분류까지만 한다. 지적이 옳은지(진짜 모호성인지)는 재판정하지 않았고 후속 결정으로 남긴다.

| 사례 | 후보 | fail 시행 | 주제 수 (가)/(나)/(다) | 지적 요지 |
|---|---|---|---|---|
| d10 clean-pass-161 | E0 | 3/3 | 0/3/5 | (나) 상대 경로 `--changed-files`의 기준·`{files}` 결합·인용·경로 표기(A6·A7, 3회); (다) README resolve 예시 갱신 담당 Work item 없음(comp, 2회), check 소요 필드 부재(H-2 대 D-7), 제외 사유 중복 시 우선순위, `stopped_at` null 여부 |
| d10 clean-pass-161 | E1 | 3/3 | 0/4/5 | (나) 상대 경로 기준(A6)·`{files}` 인용·경로 형식(A7); (다) check 소요 필드 부재(2회), README resolve 예시 담당, `scope.kind: project`의 `checked`·`excluded` 값, `hint` 방출 조건 |
| d10 clean-pass-161 | E3 | 1/3 | 0/0/1 | (다) fixture의 eslint 등이 작업본 node_modules를 찾는 방식(exec) |
| d02 clean-pass-163 | E0 | 3/3 | 0/4/7 | (나) AC-6 실측·기록 담당 Work item 없음(B3, 2회), 회귀 테스트 재실행 담당(B4, 2회); (다) 태스크 폴더에 REQUEST.md 없음(3회), 설치 후 롤백 경로, `recover` CLI 진입점·인자·응답, adapter의 `status_unsupported` 구현 위치, 영향 판정 기록 위치 |
| d02 clean-pass-163 | E1 | 3/3 | 0/4/17 | (나) AC-6 담당(B3, 2회), 회귀 재실행 담당(B4), polling 상한 설정 키(B2); (다) REQUEST.md 없음(3회), PowerShell 테스트 부재(2회), 설치 후 롤백(3회), `recover` 계약(2회), 162 복구 절차 위임(2회), `--exclude-owner` 오류 코드, settings.py 소유·순서, 구 argv 문자열, `registry_owner_deferred_to_hub` 진단 필드, 영향 판정 기록 위치 |
| d02 clean-pass-163 | E3 | 1/3 | 0/1/1 | (나) AC-6 담당(B3); (다) REQUEST.md 없음(exec) |
| d01 clean-pass-169 | E0 | 1/3 | 0/0/2 | (다) opds CLOSE가 적용 대상에서 빠짐(AC-2), 허브 `.gitattributes` 롤백 경로(C4와 인접하나 대상이 다름) |
| d01 clean-pass-169 | E1 | 2/3 | 0/0/4 | (다) `brain-tool log`의 `--new` 대 `--updated` 배분, 허브 `.gitattributes` 롤백(2회), index.md·log.md가 커밋 묶음·경로 목록에서 빠짐 |
| d01 clean-pass-169 | E3 | 1/3 | 0/0/1 | (다) opds CLOSE가 적용 대상에서 빠짐(AC-2) |

요약.

- (가) 재발(real로 보고 닫은 항목의 재지적)은 18개 fail trial 전체에서 0건이다. 닫은 문장 자체를 겨냥한 재지적은 나타나지 않았다.
- (나) not-real 주제의 재지적은 d10(A6·A7)과 d02(B2·B3·B4)에 있다. d01에는 not-real 항목이 없다.
- (다) 새 지적이 대부분이다. 두 가지는 여러 후보·시행에서 반복됐다: d02의 "태스크 폴더에 REQUEST.md가 없다"(E0 3회, E1 3회, E3 1회; 세 후보 모두 지적)와 d01의 "opds CLOSE 미적용"(E0, E3). 이 둘은 adjudication에 없던 주제다.
- 정비 불충분 신호: clean 3건 모두 세 후보에서 fail이 나왔다(d10 E0 3/3·E1 3/3·E3 1/3, d02 E0 3/3·E1 3/3·E3 1/3, d01 E0 1/3·E1 2/3·E3 1/3). 특히 d10·d02는 E0·E1에서 전 시행이 fail이다. 이 신호가 판본 결함을 뜻하는지, 평가자가 clean 문서에도 계속 gap을 찾는 것인지는 이 분류만으로 가르지 않는다.
- 참고(규칙 밖) borderline fail 비율: d03(161 원본) E0 3/3·E1 3/3·E3 1/3, d05(163 원본) 3/3·3/3·3/3, d07(169 원본) 2/3·0/3·1/3.

## 7. 소요

§2.3 표가 값이다. 결합 소요 평균은 E0 78.8초, E1 74.1초, E3 35.7초로, E3는 E0의 약 0.45배, E1의 약 0.48배다. 중앙값 기준으로는 E3 31.2초가 E0 68.5·E1 73.7초의 약 0.46·0.42배다. E0 평균(78.8)이 E1(74.1)보다 큰 것은 최대값(229.8 대 134.4) 하나의 영향이 있어 의미 있는 차이로 보지 않는다. 소요는 두 계정·세 시각대가 섞여 있어 상대 비교로만 읽는다.

## 8. 해석과 한계

- 결함 검출: 세 후보 모두 defect 15/15 fail, 기대 축 누락 0으로 차이가 없다.
- clean 안정성: 세 후보 모두 규칙 2에 미달한다. E3가 가장 덜 뒤집었다(3/9, E0 7/9, E1 8/9). 다만 그 이유가 low가 덜 엄격해서인지, 다른 요인인지는 이 측정으로 가를 수 없다. borderline도 같은 순서(E3 5/9, E1 6/9, E0 8/9)지만 규칙 밖 참고치다.
- 형식 오류 0건은 EVAL-RESULT-3의 우려(E3 JSON 문법 오류)를 66호출에서 재현하지 못했다는 뜻이다. 문제가 없다는 증명은 아니다.
- 결론: 사전 고정 규칙으로는 채택 가능 후보가 없다. 선택지는 캡틴 결정 사항이며 사실만 나열한다: (1) 규칙 2의 기준 재검토, (2) clean 세트를 더 정비한 뒤 재측정(§6의 반복 지적을 판정 대상으로 삼을 수 있다), (3) 현행 유지. 이 보고서는 추천하지 않는다.
- 한계: adjudication은 단독 판정자의 판단이고 독립 검증이 없다. 표본은 사례당 3회로 작다. 두 계정·세 시각대가 섞였다(§5). 사례 문서 안에 태스크 번호가 노출되어 있다(EVAL-RESULT-2 한계 승계). 후보 간 상대 비교만 서술하며 절대 오탐·누락률을 주장하지 않는다.
