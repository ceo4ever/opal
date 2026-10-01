# ADD-4 보조 측정 규칙 (사전 고정 — 호출 전에 기록, 데이터를 본 뒤 변경 금지)

작성 시점: 호출 시작 전. sha256은 반환·후속 보고서에 싣는다.

## 목적

보조 측정이며 채택 판정이 아니다. ADD-3(`run/EVAL-RESULT-4.md`)에서 clean 3건이 세 후보 모두 fail했고, clean-pass-163의 지적 중 "태스크 폴더에 REQUEST.md가 없다"는 사례 문서 결함이 아니라 fixture 결손이다. 원본 TASK.md·PLAN.md가 같은 폴더의 `REQUEST.md`를 입력으로 가리키는데 170 eval-set 복사본과 fixture 생성기(`DOC_NAMES = ("TASK.md","PLAN.md","TEST-SCENARIO.md")`만 복사)가 그 파일을 넣지 않았다. 이 결손만 보정해 clean 3건을 E1·E3로 다시 재서 "뒤집힘이 fixture 결손 탓이었는지"를 본다. `run/eval3/RULES.md`는 수정하지 않는다.

## 세트

- clean 3건만. ADD-3 clean 판본(`run/eval3/cases/{d01,d02,d10}`, `run/eval3/mapping.json`의 kind=clean)과 TASK/PLAN/TEST-SCENARIO가 byte 동일(`cmp`로 확인).
- 불투명 ID는 새로 무작위 배정 `e01~e03`. 라벨↔ID 매핑은 호출이 끝날 때까지 스크래치 `e4w/mapping.json`에만 둔다. 기대 verdict pass.

## 보정 (fixture 결손만)

- REQUEST.md를 참조하는 clean 사례는 pass-161·pass-163 두 건, pass-169는 비참조. 근거(grep):
  - 161판(ADD-3 d10): TASK.md:8·16, PLAN.md:6·76·80
  - 163판(ADD-3 d02): TASK.md:10, PLAN.md:6·10·34~40·66
  - 169판(ADD-3 d01): `REQUEST` 참조 없음
- 161: `git show 624ea8a0:tasks/161-260927-opd-검증도구-실행정확성-복구/REQUEST.md` (17435 B). 이 파일은 도입 커밋 624ea8a0 이후 변경 이력이 없다(`git log -- <경로>`에 624ea8a0 단 1건, `git diff --stat 624ea8a0 HEAD -- <경로>` 빈 출력). eval-set pass-161 원본 구간은 `624ea8a0^..47414d6a`(PLAN D-13)이므로 이 판본이 eval-set 시점과 동일하다.
- 163: `git show 7a6b3017:tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/REQUEST.md` (26161 B). eval-set 원본 커밋과 같은 시점.
- 169: 추가하지 않는다. 문서 3종은 그대로. `bundle_hash`는 3파일 기준이라 REQUEST.md 추가로 바뀌지 않는다.

## 후보와 호출

- 후보: E1 `opus --effort medium`, E3 `opus --effort low`. E0·E2 제외.
- 3사례 x 2후보 x 3회 = 18 trial, 36호출. 호출 방식·프롬프트·결합은 `run/eval3/RULES.md` §후보와 호출, 형식 오류 정의는 같은 파일 §형식 오류와 동일(참조만).
- 재시도: ADD-3처럼 모델 응답 실패는 재시도하지 않는다. 다만 `claude 비정상 종료 (exit 1)`·stderr 공백·응답 없음의 계정 한도 서명은 미측정으로 보고 PM이 재실행한다(EVAL-RESULT-4 §5와 같은 처리).

## 보고 지표

- 후보별 clean fail/9와 형식 오류 수, 사례별 verdict·FAIL 축.
- ADD-3 대비: clean fail E1 8/9·E3 3/9. 사례별 d02(163) E1 3/3·E3 1/3, d10(161) E1 3/3·E3 1/3, d01(169) E1 2/3·E3 1/3.
- "REQUEST.md 없음" 지적의 소멸 여부.
- 채택 판정은 하지 않는다.
