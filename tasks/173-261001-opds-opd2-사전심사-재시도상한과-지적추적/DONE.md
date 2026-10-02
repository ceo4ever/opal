# DONE: opd2 PLAN 사전심사 — 재검증 절차 정합·회차 상한·지적 해소 추적

## 결과

opd2의 PLAN 사전심사(BUILD 진입 전 Reviewer Call A·B)에서 TASK가 지적한 세 결함을 고쳤다.

- **재검증 절차(AC-1)**: 문서가 안내하던 "실패한 Call만 재실행·통과한 Call 유지"는 도구 동작과 어긋났다(지문에 plan 해시가 들어가 plan을 고치면 이전 통과 기록이 무효). 도구는 그대로 두고 문서를 "수정 뒤 A·B 모두 재디스패치"로 바꿨다. 지문 결합을 풀지 않았으므로 기존 아티팩트 지문 결합 게이트는 약해지지 않았다.
- **회차 상한(AC-2)**: 사전심사 fail 기록이 3건이 되면 도구가 상한 대기로 전환해 재심사 기록·PLAN→BUILD 전이(`transition`·`verify-mark`)·`rewind`·`unblock`을 거부하고 `blocked`(사용자 결정 대기)로 표시한다. 새 서브커맨드 `plan-review-reset`(실명 사용자·사용자 메시지 필수)만 해제하며, 해제 뒤 3회까지 다시 허용한다. `rewind`는 사전심사 기록과 `plan_review_floor`를 함께 초기화한다. 이 상한은 기존 rewind 상한(`retries <= 3`)과 별개다.
- **지적 해소 추적(AC-3)**: fail은 `{id, location, remaining_choice}` 지적 항목을 남기고, 같은 Call의 다음 기록은 직전 미해소 지적 전건에 대해 `{id, status, evidence}`를 보고해야 한다. id 집합 불일치·형식 위반·판정 모순(미해소 지적을 둔 pass, 지적 없는 fail)은 기록 전에 거부되고 상한을 소비하지 않는다. 도구가 계산한 `open_findings`가 미해소 지적을 다음 회차로 잇는다.

**유지된 기존 동작**: `ac_coverage` 커버리지 검사, 아티팩트 지문 결합, builder≠verifier≠reviewer 분리, rewind 상한 3회, state-tool 단일 상태 연동. 변경 전 원장은 새 키(`findings`)가 없는 기록을 집계·추적에서 제외해 그대로 읽히고, 기존 pass 기록으로 BUILD 전이가 된다.

**적용 경계**: opd·opds 설계 게이트, `op-scenario-gate`, evaluator, opd2 VERIFY·REVIEW, 역할 에이전트 등록·effort 적용은 건드리지 않았다.

## 변경 파일

- `opal/skills/opal-pilot-dev2/scripts/lifecycle.py`
- `opal/skills/opal-pilot-dev2/schemas/plan-review.schema.json` (신규)
- `opal/skills/opal-pilot-dev2/tests/test_lifecycle.py`
- `opal/skills/opal-pilot-dev2/agents/coordinator.md`
- `opal/skills/opal-pilot-dev2/agents/reviewer.md`
- `opal/skills/opal-pilot-dev2/SKILL.md`
- `opal/skills/opal-pilot-dev2/references/lifecycle.md`

## 검증

- `python3 -m unittest discover -s opal/skills/opal-pilot-dev2/tests`: 46건 통과(기존 36 + 신규 10, 기존 테스트 무수정). 마지막 문서 수정 뒤 재실행해 통과 재확인.
- `test-scenario.json` S-1~S-10 전건 PASS(RED 대상 6건은 구현 전 실패를 `scenario-red`로 기록·잠금 후 GREEN). S-2는 삭제 문구 부재·교체 문구 존재와 문서의 도구 이름·인자·상한 대기 문구가 `lifecycle.py`와 일치함을 확인. S-9는 변경 파일이 계획 7개뿐이고 `~/.opal/skills/opal-pilot-dev2` 트리 해시가 TEST 전후 동일함을 확인.
- 설치 후(S-10): `scripts/install-mac.sh`의 `install_dir`·`strip_deploy_md_recursive`로 스크래치 배포 루트에 복사한 사본에서 46건 통과, 새 스키마 파일 포함 확인. 실제 `~/.opal/` 설치는 하지 않았다.
- 최종 Gate: 전체 회귀 1회 통과, `git diff --check` 이상 없음, 시크릿 패턴 grep 0건, `opal-convention-checker` Critical/High 0건(finding 0), `opal-security-checker` Critical/High 0건(Low 1·Info 1). ruff·mypy·pyright는 설치되어 있지 않아 실행하지 못했고 `py_compile`만 통과했다.
- 설계 게이트: 2회차 pass(1회차 decision_clarity 2건을 PLAN에 반영해 해소).

## 회고적 학습 후보

.opal/brain/pages/concept/opd2-plan-review-reverify-doc-over-tool-relaxation.md
.opal/brain/pages/concept/opd2-plan-review-fail-limit-and-findings-tracking.md

## 참고

- 보안 검사 Low(GC-002): 깊게 중첩된 JSON 인자가 `RecursionError`를 내면 공용 except 튜플에 없어 `ok:false` JSON 대신 traceback·exit 1이 된다. 원장을 쓰기 전에 실패해 상태는 안전하다. 기존 `collect-evidence --argv`에도 같은 성질이 있어 이 태스크 범위 밖으로 두었다 — 후속 개선 후보.
- 실제 Reviewer 에이전트를 디스패치하는 연동 검증은 하지 않았다(도구 CLI 수준 계약 검증). `resolved` 보고의 내용상 진위는 도구가 검증하지 못한다(`references/lifecycle.md`에 한계 명시).
- 작업 트리에 이 태스크와 무관한 `tasks/150~169` 삭제·`tasks/backup/` 생성이 남아 있다(누가 한 아카이브 작업인지 미확인, 커밋하지 않음). merge 전 정리가 필요하다.
- `main` 통합(`f04f625f`)은 TEST 진입 조건(behind=0)을 위해 사용자 승인 뒤 수행했다.
