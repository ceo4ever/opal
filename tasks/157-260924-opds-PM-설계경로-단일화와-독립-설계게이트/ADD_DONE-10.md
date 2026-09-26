# ADD_DONE-10: 허브 세션 워크트리 수행 시 lease 기반 체크포인트 계약과 opst 커밋 판정

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-10 |
| 일시 | 2026-09-26 (완료 2026-09-26 14:51 KST) |
| 사유 | opst opd 스모크에서 체크포인트 커밋 0으로 FAIL. 원인 분석 결과 스텝 5.5(전용 터미널) 미기동 시 허브 세션이 워크트리를 수행하는 공식 경로에서 registry가 `hub_owned`로 남아, 체크포인트 예외(1:1 소유)와 `worktree-tool checkpoint`(`checkpoint_ownership_denied`)가 모두 커밋을 막는 계약 빈틈 확인(fw-inbox 09-23 항목과 동일). opd는 문구대로 미커밋, opds는 의도대로 단계별 커밋했으나 도구를 우회한 `git commit` 직접 실행(registry `checkpoint_shas` 빈 배열). 캡틴 판단: 자기 워크트리에서 PM이 단계별 체크포인트 커밋을 하는 것이 하네스 의도이므로 계약을 보완. |
| 변경 내용 | (1) `worktree-tool checkpoint`: registry가 `hub_owned`이면 현재 세션이 태스크 lease(`run/.runtime/owner.json`)를 `current_session_owned`로 보유할 때 소유로 인정(`ownership_basis: hub_lease`, registry 상태 불변). lease 없음·타 세션·released는 `checkpoint_ownership_denied`(reason `hub_lease_not_held`), `session_launching`·`released`는 기존대로 거부. (2) harness `guards.md` §커밋 규칙: 소유 근거 (a) registry 소유 / (b) hub_owned + lease 보유로 명시, 체크포인트는 `worktree-tool checkpoint`로만 만들고 `git commit` 직접 실행은 체크포인트로 인정하지 않음. `task-process.md` §`--wt`: 수행 세션에 lease 보유 허브 세션 포함, 도구 호출 명령과 거부 시 DECISION 기록 절차 명시. `worktree.md` 국면표 주체 보완. README·오류 메시지·도구 description 갱신. (3) opst: 체크포인트 판정을 registry `checkpoint_shas` 기준으로 변경 — 도구 커밋 ≥1 + 우회 커밋 0. REPORT·대시보드에 도구/우회 커밋 수 표시. |
| 변경 파일 | `opal/tools/worktree-tool/{worktree_tool.py,README.md,tests/test_worktree_tool.py}`, `opal/core/references/harness/{guards.md,task-process.md,worktree.md}`, `opal/skills/opal-skill-tester/{scripts/skill_tester.py,scripts/report_html.py,references/metrics.md}`, `tasks/157-…/skill-tests/**` |
| 검증 결과 | RED 3건(lease 보유 허용·타 세션 lease 거부·lease 없음/released 거부) 확인 후 GREEN. worktree-tool 154 passed, ownership-tool 165, event-loader 24, worktree-launcher 148(4 skipped), brain-tool 159, memory-tool 198. 기존 기록 재판정: opds FAIL(도구 0/우회 4), opd FAIL(도구 0/우회 0), opsdd PASS(허브 태스크) — 두 실행 모두 계약 보완 전 실행이므로 예상대로. 보완 후 실제 Pilot 실행 검증은 미수행(비용 확인 필요). |
