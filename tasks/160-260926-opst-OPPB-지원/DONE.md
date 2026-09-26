# DONE: opst OPPB 지원

## 결과

`opal-skill-tester`에 OPPB 판정 프로필, P1·P3·P4·P5 단계 측정, canonical 태스크의
`.oppb-run/<run_id>/run.closed.json` 보존본 판정, legacy `.opal-runs` 부재 판정과
물리 worktree 회수 판정을 추가했다. 일반 worktree Pilot의 checkpoint 판정은 기존대로 유지한다.

실제 유료 헤드리스 실행은 앱 기능 회귀 7건과 숨은 인수 테스트 4건을 모두 통과했지만,
P5 `worktree_finalize=done` 표기와 달리 worktree가 남아 있어 최종 `FAIL`로 판정됐다.
이는 테스터가 OPPB 종료 계약 위반을 검출한 결과이며 OPPB 런타임 자체 수정은 범위에 포함하지 않았다.

## 변경 파일

- `opal/skills/opal-skill-tester/scripts/skill_tester.py`
- `opal/skills/opal-skill-tester/tests/test_skill_tester_oppb.py`
- `opal/skills/opal-skill-tester/scenarios/function-oppb-low-stock/`
- `opal/skills/opal-skill-tester/references/metrics.md`
- `opal/skills/opal-skill-tester/references/scenario-spec.md`
- `opal/skills/opal-skill-tester/SKILL.md`
- `opal/skills/opal-skill-tester/README.md`
- `tasks/160-260926-opst-OPPB-지원/evidence/`
- `tasks/160-260926-opst-OPPB-지원/skill-tests/`
- `tasks/160-260926-opst-OPPB-지원/GC-CONVENTION-20260926-2134.md`
- `tasks/160-260926-opst-OPPB-지원/gc-findings-convention-20260926-2134.json`
- `tasks/160-260926-opst-OPPB-지원/PM-GATE.md`

## 검증

- `pytest -q opal/skills/opal-skill-tester/tests/test_skill_tester_oppb.py` — 6 passed.
- `skill_tester.py validate --all` — 시나리오 5건 모두 통과.
- `py_compile skill_tester.py .../hidden/test_hidden.py` — 통과.
- `git diff --check` — 통과.
- `code-scan validate --changed <9개 파일 CSV>` — `newly_uncovered=0`;
  기존 문서의 `pre_existing=4`만 비차단 보고.
- 독립 컨벤션 검사 — 경로·구문·JSON·공백·EOF 검사 통과. 신규 요구서의 헤더 결손 1건 보정 후 PM Gate PASS.
- 기존 outdir 재채점 — `oppb_archive_count=1`, `oppb_archive_ok=true`,
  `oppb_legacy_root_absent=true`, `oppb_worktree_finalized=false`, 최종 `FAIL`.

## 회고적 학습 후보

없음

## 참고

- OPPB P5 finalize가 `TASK_PATH_AMBIGUOUS`로 막혔는데도 행이 완료 처리되어 worktree와 registry가 남았다.
- P4 첫 acceptance 실패 뒤 Supervisor 종료 구간에서 PM이 repair runner/verifier를 직접 조율해
  `P3 이후 Supervisor channel only` 계약 위반 가능성이 있다.
- evidence metadata의 `code_head`가 실제 검증 head보다 오래된 값으로 남았다.
- 위 세 항목은 OPPB 런타임 후속 태스크 후보이며 태스크 160에서는 자동 수정하지 않았다.
