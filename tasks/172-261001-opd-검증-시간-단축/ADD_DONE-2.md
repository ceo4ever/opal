# ADD_DONE-2: evaluator 평가 세트 정비와 low 포함 재측정

| 필드 | 내용 |
|---|---|
| 추가작업 번호 | ADD-3(evaluator 평가 세트 정비와 low 포함 재측정 — 형식 오류 빈도) |
| 일시 | 2026-10-01 20:41 (KST) |
| 사유 | 캡틴 요청: EVAL-RESULT-2·3의 pass 사례 뒤집힘이 사례 문서의 실제 모호성인지 가리고, E3(opus low)를 포함해 반복 측정으로 형식 오류 빈도를 잰다 |

## 변경 내용

**1단계 — 세트 정비(`run/eval3/adjudication.md`, `run/eval3/build_cases3.py`, `run/eval3/clean-diffs/`)**

- 기존 측정의 pass 3건 design 응답 지적 18주제를 원문에 비춰 판정했다. real 13(A1~A5·A8, B1, C1~C6), not-real 5(A6·A7, B2~B4). real만 닫은 clean 3건과 원본 그대로인 borderline 3건, 결함 5건으로 11사례(불투명 ID d01~d11)를 구성했다.
- 채택 규칙 4개는 호출 전에 `run/eval3/RULES.md`에 고정했다(sha256 `e4dbf274…16ad`).

**2단계 — 측정(`run/eval3/run_eval3.py`, 결과 `run/EVAL-RESULT-4.md`)**

- E0(opus)·E1(opus medium)·E3(opus low) × 11사례 × 3회 = 99 trial·198호출. 정식 wrapper `opal-agent`, fresh receipt·fresh fixture, 무작위 순서.
- 결과: 모델 측 형식 오류 0건, 결합 불성립 0건, 결함 누락 세 후보 모두 0/15. clean fail은 E0 7/9, E1 8/9, E3 3/9로 **세 후보 모두 규칙 2(≤2) 미달 → 채택 가능 후보 없음**. 결합 소요 평균 E0 78.8초, E1 74.1초, E3 35.7초(상대 비교만).
- EVAL-RESULT-3의 E3 JSON 문법 오류(1/16)는 66호출에서 재현되지 않았다.

**규칙 이탈 선언(EVAL-RESULT-4 §5)**: 측정은 두 세션·두 계정에서 수행됐다. 계정 세션 한도(429)로 71 trial이 `claude exit 1`로 실패해 PM이 "미측정"으로 분류하고 같은 토큰·조건으로 재실행했다. RULES "재시도 없음"의 문면을 벗어난 결정이며 verdict·형식 오류율에는 영향이 없고 소요는 시각대가 섞였다.

## 검토 결과로 드러난 사항(후속 결정 필요)

- **clean 세트 정비는 불충분했다.** clean 3건 모두 세 후보에서 fail이 나왔고, 닫은 항목의 재발은 0건이지만 새 지적이 대부분이다(EVAL-RESULT-4 §6).
- **fixture 결손 1건**: pass-163 원본(`tasks/170-…/run/eval-set/pass-163/`)은 TASK.md·PLAN.md가 `REQUEST.md`를 입력으로 가리키는데 폴더에 그 파일이 없다. clean-pass-163(d02)·borderline-pass-163(d05)의 fail 지적 중 "REQUEST.md 없음"(세 후보 모두 지적)은 문서 모호성이 아니라 평가 세트 복사 시의 결손이다. 170의 eval-set 자체가 이 결손을 가지므로 EVAL-RESULT-2·3의 pass-163 판정에도 같은 영향이 있었을 수 있다. 이 태스크는 170의 eval-set을 수정하지 않았다.
- **선택지(캡틴 결정)**: (1) 규칙 2 기준 재검토, (2) REQUEST.md 결손 보정과 §6 반복 지적 재판정 뒤 clean 세트 재정비·재측정, (3) 현행(E0) 유지. EVAL-RESULT-4는 추천하지 않는다. 캡틴이 확정한 evaluator=opus+medium(E1)은 이 측정에서 clean fail 8/9로 세 후보 중 가장 많이 뒤집었다.

## 변경 파일

- `tasks/172-…/run/EVAL-RESULT-4.md`(신규)
- `tasks/172-…/run/eval3/`(RULES.md·adjudication.md·build_cases3.py·run_eval3.py·report_tables4.py·mapping.json·plan.json·cases/·clean-diffs/·results/ 99건·raw/ 891파일(22MB)·results4.json·run.log·rate-limit-removed.json)
- `tasks/172-…/ADD_DONE-2.md`(이 문서), `state.json`·`STATE.md`(state-tool 경유)
- 저장소 소스(`opal/**`)·170의 eval-set은 변경하지 않았다.

## 검증

- `run_eval3.py --aggregate` 재생성본과 이관본 `results4.json`이 `cmp`로 동일. `results/` 99건·`raw/` 891파일 확인.
- 보고서 수치는 워커가 `results4.json`과 대조했고 PM이 후보별 요약·clean fail 분포를 집계 출력과 재대조했다.
- 호출은 전부 `opal-agent` wrapper(raw CLI 없음), trial마다 `worker.dispatch` receipt load·verify.
