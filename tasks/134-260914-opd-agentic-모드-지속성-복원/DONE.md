# DONE: agentic 모드 지속성 복원

## 결과

`state-tool resolve-mode`를 추가해 Pilot의 effective mode 판정을 **명시 플래그 > 유효한 저장 mode > 신규 태스크 semi-agentic 기본값**으로 단일화했다. 기존 agentic 태스크는 사용자 검토 왕복과 새 프로세스·세션 재개 후에도 `state.json.mode`를 복원하며, 명시 override는 다른 진행 상태를 보존한 채 mode만 원자 갱신한다.

누락·비문자·허용값 밖 mode는 interactive로 fail-closed 처리하고, 손상 JSON은 `state_json_malformed`로 차단한다. 자동 승인·validate·boot-summary도 같은 정규화 계약을 사용한다. project brief에는 mode와 mode source를 표시하되 판정 SSOT로 사용하지 않는다.

`oppd → opwt`와 `opd ↔ opds` 전환은 부모의 effective mode를 명시 상속한다. interactive·semi-agentic 경계, 트랙 전환 사용자 수락, CLOSE 사용자 승인과 플랫폼 독립성은 기존 계약을 유지했다. 2026-09-15 CLOSE 승인 왕복에서 `agentic / source=state` 복원이 실제 확인됐다.

## 변경 파일

- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/schema/state.schema.json`
- `opal/tools/state-tool/tests/test_state_tool.py`
- `opal/tools/state-tool/tests/test_mode_resolution.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `scripts/tests/task134_mode_persistence_contract.py`
- `opal/core/references/harness/modes.md`
- `opal/core/references/harness/state.md`
- `opal/core/references/opal-harness-agentic.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/opal-pilot-dev/references/track-routing.md`
- `opal/skills/opal-pilot-dev/references/track-escalation.md`
- `opal/skills/opal-pilot-project-dev/SKILL.md`
- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`
- `tasks/134-260914-opd-agentic-모드-지속성-복원/AGENTIC-LOG.md`
- `tasks/134-260914-opd-agentic-모드-지속성-복원/GC-CONVENTION-2026-09-14T19-22-00.md`
- `tasks/134-260914-opd-agentic-모드-지속성-복원/gc-findings-convention-2026-09-14T19-22-00.json`
- `tasks/134-260914-opd-agentic-모드-지속성-복원/test-scenario.json`

## 검증

- `python3 -m unittest discover -s opal/tools/state-tool/tests -p 'test_*.py'` — 452건 PASS, 환경·조건부 3건 skip, 실패 0건
- `python3 -m unittest discover -s opal/tools/event-loader/tests -p 'test_*.py'` — 18건 PASS
- `python3 -m unittest scripts.tests.task134_mode_persistence_contract` — 5건 PASS
- `python3 scripts/tests/task113_bootstrap_audit.py` — source bootstrap audit PASS
- `bash scripts/tests/test_agent_adapter_fields.sh` — 15건 PASS
- 임시 HOME 대상 install — 변경 배포 자산 exact 6건·strip-deploy Markdown 8건 원본 일치
- `code-scan validate --changed` — 6/6, coverage 100%, violation 0
- `test-tool scenario-status` — S1~S10 PASS, FAIL/BLOCKED/awaiting_human 0건
- 컨벤션 진단 — 대상 17개, blocking·Critical·High 0건
- 보안 검사와 `git diff --check` — PASS

## 회고적 학습 후보

.opal/brain/pages/entity/state-tool.md
.opal/brain/pages/concept/skill-opal-pilot-dev.md
.opal/brain/pages/concept/session-project-action-needed-briefing.md

## 참고

- 커밋·merge·실사용 환경 install은 사용자 권한으로 남겨둠.
- 기존 HEAD부터 존재한 `opal-pilot-dev-short` 디렉터리 때문에 과거 cleanup 테스트 1건이 baseline FAIL이지만, task 134 변경 배포 자산 검증에는 영향 없음.
