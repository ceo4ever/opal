# ADD_DONE-3: clean 3건 보조 측정 (REQUEST.md fixture 결손 보정)

| 필드 | 내용 |
|---|---|
| 추가작업 번호 | ADD-4(clean 3건 보조 측정 — REQUEST.md fixture 결손 보정, E1·E3 × 3회) |
| 일시 | 2026-10-01 21:09 (KST) |
| 사유 | 캡틴 승인(빠른 버전): ADD-3에서 드러난 fixture 결손(REQUEST.md 누락)만 보정해 clean 뒤집힘이 결손 탓이었는지 확인한다. 채택 판정이 아닌 보조 측정 |

## 변경 내용

- 결손은 1건이 아니라 2건이었다. 준비 워커가 clean-pass-161(d10)도 TASK.md:8·16, PLAN.md:6·76·80에서 REQUEST.md를 참조함을 발견했다(PM 사전 가정 정정). 161의 REQUEST.md는 도입 커밋 `624ea8a0` 이후 변경 이력이 없어 eval-set 시점 판본과 동일함을 git 이력으로 확인하고 보정에 썼다. 163은 `7a6b3017` 판본. 169는 비참조.
- 규칙 사전 고정 `run/eval4/RULES-ADD4.md`(sha256 `57289eb2…2900`), 세트 구성 `build_cases4.py`(ADD-3 clean 판본과 byte 동일 + REQUEST.md 추가), 측정기 `run_eval4.py`(run_eval3를 import 래핑, CANDS E1·E3, fixture에 REQUEST.md 복사). ADD-3의 RULES.md·run_eval3.py·170 eval-set은 수정하지 않았다.
- 18 trial·36호출, 중단 없음, 형식 오류 0, 결합 불성립 0. 결과 `run/EVAL-RESULT-5.md`, 데이터 `run/eval4/`.

## 결과 요약 (EVAL-RESULT-5)

| 사례 | E1 medium ADD-3 → ADD-4 | E3 low ADD-3 → ADD-4 |
|---|---|---|
| clean-pass-161 | 3/3 → 3/3 fail | 1/3 → 0/3 fail |
| clean-pass-163 | 3/3 → 3/3 fail | 1/3 → 2/3 fail |
| clean-pass-169(비보정) | 2/3 → 3/3 fail | 1/3 → 0/3 fail |
| 합계 | 8/9 → 9/9 | 3/9 → 2/9 |

- "REQUEST.md 없음" 지적은 36호출에서 0건으로 사라졌다. 163 응답은 REQUEST.md를 줄 번호로 인용하며 B2(설정 키)·B3(AC-6 담당) 주제를 REQUEST 요구 대비로 다시 지적했다. 닫은 항목(가)의 재발은 0건.
- E3 합계 2/9는 ADD-3 규칙 2 상한(≤2)과 같은 값이지만 세트·후보·규칙이 달라 "규칙 통과"로 판정하지 않는다. 169는 보정 없이도 E3 fail이 1/3→0/3이 되어 시행 간 변동이 그 정도 있다.
- 결론·추천은 쓰지 않았다(캡틴 결정 사항).

## 변경 파일

- `run/EVAL-RESULT-5.md`, `run/eval4/`(RULES-ADD4.md·build_cases4.py·run_eval4.py·mapping.json·plan.json·cases/·results/ 18건·raw/·run.log·results-add4.json), `ADD_DONE-3.md`, `state.json`·`STATE.md`(state-tool 경유).

## 검증

- 이관본과 원천 `cmp`/`diff -r` 동일, 집계 재생성 `cmp` 동일, RULES-ADD4.md sha256 일치, results 18건. 모든 호출은 `opal-agent` wrapper, trial마다 worker.dispatch receipt load·verify.
