# ADD_DONE-1: S-13 검토와 도구·스킬 누락 방지

| 필드 | 내용 |
|---|---|
| 추가작업 번호 | ADD-1(S-13 검토), ADD-2(도구·스킬 누락 방지·FW 개선 후보 반영) |
| 일시 | 2026-10-01 (KST) |
| 사유 | 캡틴 요청: S-13을 CLOSE 이후 추가작업으로 검토하고, `opal-agent` 같은 정식 도구를 놓치지 않게 하는 방지책을 반영한다 |

## 변경 내용

**ADD-1. S-13 검토(분석, 코드 변경 없음)**

W-10 측정(같은 `pass-161`, 같은 후보 opus+medium)은 `pass`, TEST·진단은 단일·병렬 모두 `fail`(7/7)이었다. 요인을 분리하는 실험을 `opal-agent` wrapper로 수행했다(`run/ADD1-S13-REVIEW.md`).

- 프롬프트 문구는 경로 3종을 치환하면 W-10과 TEST가 `diff` 0줄로 같다. 다른 것은 경로·파일명과 호출 옵션이다.
- 에이전트 정의 전달 방식(`--system-prompt` 대 `--agents` 대 설치본)과 작업 디렉터리는 원인이 아니다(전달 방식을 바꾼 조건과 cwd를 바꾼 조건에서 결과가 같았다).
- 가장 지배적인 요인은 프롬프트에 실린 **경로·파일명의 사례 라벨**이다. W-10 fixture 폴더와 receipt 이름에는 `pass-161`이 있었고 TEST·진단 폴더는 중립 이름이었다. 중립 경로 실행 11건은 모두 `fail`, `pass-161` 경로 실행 5건(W-10 3 + 실험 2)은 모두 `pass`였다. 모델 응답은 `pass-161`을 인용하지 않았다.
- 판정 근거를 보면 모호성은 같고 엄격도가 갈렸다. W-10은 같은 모호성을 보고도 "시나리오가 대표 사례를 고정한다"며 pass를 냈고, 중립 경로 실행은 D-2 ①과 S-4(b) 충돌을 더해 "구현자 선택"으로 세고 fail을 냈다.
- 한계: 라벨이 폴더명만이 아니라 부모 폴더와 receipt 파일명에도 있어 어느 문자열이 효과를 냈는지는 가르지 못했다. 표본이 작아 통계 주장은 하지 않는다. 단순 표본 변동은 배제하지 못했다.

**함의(검토 결과로 새로 드러난 위험)**: W-10의 평가 세트는 사례 ID가 `pass-*`·`defect-*`·`161-pass`·`162-defect`처럼 의미를 가진 경로로 호출되었다. 그래서 W-10의 "결함 누락 0·pass 뒤집힘 0·결합 verdict 24/24 일치" 결과가 라벨의 도움을 받았을 가능성이 있다. 이번에는 `pass-161`만 중립 경로로 재측정했고 나머지 사례는 하지 않았으므로 W-10 전체가 무효라고 말할 근거는 없다. 다만 캡틴이 결정한 model·effort의 근거가 이 한계를 가진다.

**S-13 재설계 권고(적용하지 않음)**: S-13을 계약 검증으로 줄이고(두 응답 형식·`combine` 성공·`record`가 결합 결과를 수락하는지·벽시계가 개별 합보다 짧은지), 결합 verdict와 FAIL 축은 같은 중립 fixture의 단일 호출과 비교해 기록한다. 기대 `pass`는 수용 기준으로 쓰지 않는다. 수정 범위: `TEST-SCENARIO.md` S-13 한 행, `PLAN.md` AC-8/H-2 문구와 D-13 한계, `EVAL-RESULT.md` 한계 한 줄.

**ADD-2. 도구·스킬 누락 방지와 FW 후보 반영**

- `opal/core/AGENT.md`: 도구 선택 표에 "다른 LLM·에이전트 헤드리스 호출 → `opal-agent`" 행을 추가하고 `tools.md` 로드 트리거를 "파일·데이터 변환 또는 외부 CLI·에이전트 호출 도구의 첫 사용"으로 넓혔다.
- `opal/core/references/tools.md`: 기존 `opal-agent` 행에 "raw `claude -p`·`codex exec`·`gemini -p` 대신 이 도구" 문구를 보강했다.
- `opal/agents/opal-evaluator-agent/AGENT.md`: executability 앵커에 "외부 호출에 정식 OPAL wrapper를 쓰지 않고 raw CLI를 지정하면 FAIL"을 추가했다(캡틴이 이 변경을 명시 승인).
- `opal/core/references/harness/pm-improvement-loop.md`: 회고 시 raw CLI 직접 호출 `grep` 확인과 3개 태스크 관찰 뒤 재발하면 Bash 사전 차단 훅·설계 게이트 검사로 승격하는 규칙을 추가했다.
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`: FW 후보 2건 — 판정 도구 신설 시 "과거 통과 구간 0 finding" 사례 포함, 모델 판정은 계약과 분포를 분리해 검증하고 단일 표본 verdict 일치를 수용 기준으로 삼지 않기.
- 범위 밖: 훅(Bash 사전 차단)과 `design-gate-check` 확장은 하지 않았다(관찰 후 재검토).

## 변경 파일

- `opal/core/AGENT.md`
- `opal/core/references/tools.md`
- `opal/core/references/harness/pm-improvement-loop.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md`
- `tasks/172-261001-opd-검증-시간-단축/run/ADD1-S13-REVIEW.md`
- `tasks/172-261001-opd-검증-시간-단축/run/test-evidence/add1/`

## 검증

- 문서 변경: 변경 문맥과 표 구조 확인, `git diff`로 의도한 줄만 변경됨을 확인(5개 소스 파일 +7/−3).
- `event-loader` 시험: 23 통과·2 실패(`test_static_check_ok`, `test_project_brief_cli_preserves_inputs_and_multitask_counts`). `main`에서도 실패하는 기존 2건과 같은 이름이며 새 실패는 없다(`main`에서 이번에 다시 대조하지는 않았다).
- `scripts/tests/test_agent_effort_policy.sh`: PASS=4, FAIL=0.
- ADD-1 실험 6회는 전부 `opal-agent`로 수행했고 결과가 있었다. 조건 ③(W-10의 `--agents` 주입 재현)은 wrapper가 지원하지 않아 생략했다.
- 배포: 이 변경은 소스에만 반영되었고 설치본(`~/.opal/`)은 다음 install 때 갱신된다.
