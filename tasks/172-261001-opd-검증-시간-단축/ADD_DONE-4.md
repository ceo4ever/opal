# ADD_DONE-4: evaluator effort medium → low (캡틴 결정 반영)

| 필드 | 내용 |
|---|---|
| 추가작업 번호 | ADD-5(캡틴 결정 반영 — evaluator effort medium→low) |
| 일시 | 2026-10-01 21:17 (KST) |
| 사유 | ADD-3·ADD-4 재측정 결과를 본 캡틴이 "low를 선택"이라고 명시 결정했다 |

## 변경 내용

- (a) 결정: 캡틴이 `opal-evaluator-agent`의 effort를 `low`로 선택했다. 근거 요약 — ADD-3(`run/EVAL-RESULT-4.md`)에서 E3(low)는 결함 누락 0/15, 형식 오류 0/66, clean fail 3/9로 세 후보 중 최소였다. ADD-4(`run/EVAL-RESULT-5.md`) REQUEST.md 보정 세트에서 E3는 clean fail 2/9, 형식 오류 0/18이었다. 결합 소요는 E0 대비 약 0.45배다.
- (b) 한계: 위 두 측정을 합산한 근거이며, RULES.md(ADD-3)의 "한 세트에서 4조건 동시 충족" 정식 채택 측정(보정 세트 11건 재측정, ADD-5 후보였음)은 캡틴 결정으로 생략했다. clean-pass-163은 보정 뒤에도 E3 2/3 fail이며, 남은 지적은 B2·B3 주제의 REQUEST 근거 재등장이다. 현행 E0·E1도 같은 규칙에서 채택 불가였으므로 이 선택은 "채택 가능 후보 중 선택"이 아니라 "측정된 후보 중 상대적 최선"이다.
- (c) 설치본 사실: `~/.opal/agents/opal-evaluator-agent/AGENT.md`는 2026-10-01 21:04에 허브 `main`(v0.7.3-58-gf4cb0f01) 기준으로 재설치되어 현재 `effort: default`이며 이 브랜치(172)의 effort 선언을 포함하지 않는다. 이 변경은 소스에만 반영되고 설치본은 172 머지 후 install 때 갱신된다. `~/.opal/`은 수정하지 않았다.

## 변경 파일

- `opal/agents/opal-evaluator-agent/AGENT.md`(9행 `effort: medium` → `effort: low`), `tasks/172-261001-opd-검증-시간-단축/DONE.md`(13행 문장 추가, 기존 문장 보존), `tasks/172-261001-opd-검증-시간-단축/ADD_DONE-4.md`(신규).

## 검증

- `bash scripts/tests/test_agent_effort_policy.sh` 실행 결과는 PM 반환값에 기록(PASS 4 / FAIL 0 목표).
- `grep -n "^effort" opal/agents/opal-evaluator-agent/AGENT.md` → `effort: low`.
- 설치본 확인: `grep -n "^effort" ~/.opal/agents/opal-evaluator-agent/AGENT.md` → `9:effort: default`, `ls -la` → 27850 bytes, Oct 1 21:04.
