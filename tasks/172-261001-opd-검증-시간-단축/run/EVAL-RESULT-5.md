<!--
ADD-4 보조 측정: clean 3건의 fixture 결손(REQUEST.md 누락)을 보정하고 E1·E3를 3회씩 재측정한 결과. 채택 판정 아님.
규칙은 run/eval4/RULES-ADD4.md(호출 전 고정). 집계는 run/eval4/run_eval4.py --aggregate가 만든 run/eval4/results-add4.json.
원본: run/eval4/raw/(응답 36건·receipt·combine), 사례 문서: run/eval4/cases/, 지적 판정 기준: run/eval3/adjudication.md, 비교 대상: run/EVAL-RESULT-4.md.
작성: 2026-10-01 21:10 KST.
-->
# EVAL-RESULT-5: REQUEST.md 보정 후 clean 3건 보조 측정 (E1·E3 x 3회)

18 trial(36 호출) 모두 결과를 얻었다. 형식 오류와 결합 불성립은 0건이다. 이 측정은 보조 측정이며 채택 판정이 아니다.

## 1. 목적과 규칙

- 규칙 파일 `run/eval4/RULES-ADD4.md`, sha256 `57289eb2840648fee6e8b75bc6bbffd3b053e40d76a33f8dc78dc396b9662900`. 이 보고서 작성 시 `shasum -a 256`으로 다시 계산해 PM이 전달한 값과 같음을 확인했다.
- 규칙 요지(복제하지 않는다): ADD-3에서 clean 3건이 세 후보 모두 fail했고, 지적 중 "태스크 폴더에 REQUEST.md가 없다"는 사례 결함이 아니라 fixture 결손이었다(원본 TASK/PLAN이 가리키는 REQUEST.md를 fixture 생성기가 복사하지 않음). 이 결손만 보정해 E1(`opus --effort medium`)·E3(`opus --effort low`)로 3사례 x 3회 다시 쟀다.
- 보정: REQUEST.md를 161판(커밋 `624ea8a0`)과 163판(커밋 `7a6b3017`) fixture에 추가했다. 169판은 REQUEST를 참조하지 않아 추가하지 않았다(`mapping.json`의 `request_md_added`: e01 true, e02 true, e03 false).
- 세트: TASK/PLAN/TEST-SCENARIO는 ADD-3 clean 판본(`run/eval3/cases/{d01,d02,d10}`)과 byte 동일하다(RULES-ADD4 §세트가 `cmp`로 확인했다고 기록). 호출 방식·프롬프트·결합은 `run/eval3/RULES.md`와 같다. 불투명 ID e01~e03, 라벨은 호출이 끝났으므로 §2.2에 공개한다.

## 2. 결과 (`results-add4.json`)

### 2.1 후보별

| 항목 | E1 | E3 |
|---|---|---|
| trial 수 (호출 수) | 9 (18) | 9 (18) |
| 형식 오류 design/scenario | 0/0 | 0/0 |
| 결합 불성립 | 0 | 0 |
| clean fail (9 중) | 9 | 2 |
| 결합 소요 평균/중앙/p90/최대(초) | 89.4/91.8/102.1/102.1 | 38.9/34.3/66.0/66.0 |

### 2.2 사례 x 후보 (rep1; rep2; rep3의 결합 verdict와 FAIL 축)

축 약어: comp=completeness, deci=decision_clarity, exec=executability, reco=recoverability.

| ID | 라벨 | 기대 | E1 | E3 |
|---|---|---|---|---|
| e01 | clean-pass-163 | pass | fail(comp,deci,exec); fail(comp,deci); fail(comp,deci,exec,reco) | fail(comp); fail(comp,deci); pass |
| e02 | clean-pass-161 | pass | fail(deci) x3 | pass x3 |
| e03 | clean-pass-169 | pass | fail(comp); fail(comp); fail(reco) | pass x3 |

## 3. ADD-3 대비 (clean fail 시행 수)

| 사례 | ADD-3 ID | REQUEST.md 보정 | ADD-3 E1 / E3 | ADD-4 E1 / E3 |
|---|---|---|---|---|
| 163 | d02 -> e01 | 추가 | 3/3 / 1/3 | 3/3 / 2/3 |
| 161 | d10 -> e02 | 추가 | 3/3 / 1/3 | 3/3 / 0/3 |
| 169 | d01 -> e03 | 없음 | 2/3 / 1/3 | 3/3 / 0/3 |
| 합계 | | | 8/9 / 3/9 | 9/9 / 2/9 |

- E3는 이번 측정에서 161·169 전 시행이 pass가 됐고, 163에서는 1/3에서 2/3 fail로 늘었다. 표본이 3회라 이 변화가 변동 범위 안인지 단정하지 않는다. 169는 보정 대상이 아닌데도 E3 fail이 1/3에서 0/3이 됐으므로, 보정 외의 시행 간 변동이 이 정도 있다는 사실도 함께 보인다.
- E1은 보정과 무관하게 전 시행 fail이다(ADD-3 8/9 -> 9/9).
- E3 합계 2/9는 ADD-3 RULES 규칙 2의 상한(<=2)과 같은 값이다. 이 측정은 채택 판정이 아니고 세트·후보·규칙이 다르므로 규칙 통과 여부는 판정하지 않는다.

## 4. "REQUEST.md 없음" 지적의 소멸

`raw/ev/*__design.json`의 `response.result` 18건(scenario 응답 18건은 보지 않았다)에서 `REQUEST`를 모두 찾았다.

| 사례 x 후보 | design 응답 | REQUEST 언급 응답 | 부재 지적 | 파일 내용 인용(`REQUEST.md:줄`) | PLAN 문구 언급(줄 번호 없음) |
|---|---|---|---|---|---|
| e01 E1 | 3 | 3 | 0 | 3 (`:38-43`, `:55`, `:95`, `:138-145`, `:192-200`, `:193-200`) | 0 |
| e01 E3 | 3 | 2 | 0 | 0 | 2 ("REQUEST.md §162 복구 순서" 참조 서술) |
| e02, e03 (E1·E3) | 12 | 0 | 0 | 0 | 0 |

- 부재 지적은 36호출 중 design 18건 기준 0건이다. ADD-3에서 세 후보가 낸 "REQUEST.md가 없다"는 사라졌다.
- PM 사전 확인(e01 E1 3건이 내용 인용)과 일치한다. 추가로 e01 E3 두 건도 REQUEST를 언급하지만 PLAN의 "REQUEST.md §162 복구 순서" 문구를 풀어 쓴 것이고 줄 번호 인용은 없다. e01 E1 rep2는 응답 서두에서 "TASK, PLAN, REQUEST and TEST-SCENARIO"를 읽었다고 적었다.
- e02(161)는 TASK/PLAN이 REQUEST.md를 참조하고 파일도 추가했지만 응답 6건에 REQUEST 언급이 없다.

## 5. e01(163)의 남은 지적

e01 fail 시행 5건(E1 3, E3 2)의 `design.gaps`를 `run/eval3/adjudication.md` 기준으로 분류했다. (가) 닫은 항목 재발 = clean 판본에서 닫은 B1, (나) not-real 재지적 = B2(설정 키)·B3(AC-6 담당 Work item)·B4(회귀 재실행 담당), (다) 새 지적. 지적의 옳고 그름은 재판정하지 않았다.

| 시행 | (가) | (나) | (다) |
|---|---|---|---|
| E1 r1 | 0 | B3, B2 | settings.py 소유(W-4)·순서(W-3) |
| E1 r2 | 0 | B3, B2 | REQUEST.md:38-43 복구 순서가 전제로만 인용됨, W-1 ownership 필드 보존 방식 |
| E1 r3 | 0 | B3, B2 | REQUEST.md:95 소비자 목록·전수 갱신 대비(B1 주제와 인접, 아래 참고), PowerShell 이관 테스트 부재, settings.py 소유·순서, 영향 판정 기록 위치, 설치본 롤백 경로 |
| E3 r1 | 0 | B3 | 0 |
| E3 r2 | 0 | B3, B2 | C-3 다른 워크트리 보존 검증 연결, `recover` CLI 형태·응답 |

- (가) 재발은 0건이다. 다만 E1 r3의 REQUEST.md:95 지적은 B1과 같은 소비자 목록 주제를 다룬다. B1은 "영향 확인 시 소비자 코드를 바꾸지 않고 기록·보고한다"로 닫혔고, 이번 지적은 REQUEST가 PLAN 안의 목록·갱신을 요구한다는 대조라 (다)로 분류했다. 경계는 판정자에 따라 갈릴 수 있다.
- REQUEST.md가 들어가자 평가자 일부는 REQUEST의 요구와 PLAN의 차이를 근거로 지적한다: `:55` 설정 키(E1 3시행 모두, B2 주제), `:95` 소비자 전수 갱신(E1 r3), `:38-43`·`:192-200` 복구·실측 절차(E1 r1~r3, B3 주제). B2·B3 지적이 REQUEST 줄 번호를 근거로 달고 다시 나온 것이며, E3에서는 REQUEST 줄 번호 인용이 없다.

## 6. 한계

- 표본은 사례당 후보당 3회, 후보는 2개다. 시행 간 변동(§3의 169 E3)과 보정 효과를 분리할 수 없다.
- 단일 계정·단일 시각대다. 결과 파일 시각은 20:58~21:05(KST)이고, `run.log`에는 중단·재실행·한도 관련 문구가 없으며 trial 18줄이 중복 없이 있다. 이번에는 중단·재실행이 없었다. `run.log`에 시각이 없어 시각대 자체는 결과 파일 mtime에 의존한다.
- REQUEST.md 보정은 161·163 두 건뿐이다. 169는 원래 비참조라 보정이 없다.
- 평가자가 REQUEST.md를 실제로 읽었다는 증거는 응답에 적힌 줄 번호 인용(e01 E1 3건)과 e01 E1 rep2의 서두 진술뿐이다. E3와 e02 응답에서는 읽었는지 알 수 없다.
- 결론과 추천은 쓰지 않는다(캡틴 결정 사항).

