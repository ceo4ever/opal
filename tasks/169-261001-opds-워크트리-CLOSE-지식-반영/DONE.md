# DONE: 워크트리 CLOSE에서 문서·brain·산출물 지식 반영

## 결과

워크트리 태스크의 CLOSE에서 `op-brain-ingest`가 실제로 브랜치 자신의 `.opal/brain/`에 page를 쓸 수 있게 됐다. 막고 있던 유일한 지점은 `brain_tool.py`의 `require_write_root`가 `--allocator-root` 미지정 시 워크트리 여부와 무관하게 전면 거부하던 가드였다 — 이 가드를 제거하고, 워크트리에서도 조회와 동일하게 cwd(task_root) 자신에 기본 쓰기가 성공하도록 통일했다. `--allocator-root` 명시 경로(다른 루트를 지정할 때 쓰는 기존 기능)는 그대로 유지했다.

CLOSE 파이프라인(op-brain-ingest 디스패치 → 회고 → `worktree-tool finalize`(merge 전 귀속 커밋) → 사용자 merge 안내) 자체는 이미 "워크트리에서 쓰고 merge 전에 확정"하는 순서로 배선돼 있었다 — 이번 변경은 그 배선을 막던 가드 하나를 없앤 것이다. 함께 정정한 사항:

- `done-template.md`·`op-oppb-knowledge-finalize/SKILL.md`·`opal-pilot-dev/SKILL.md`·`op-brain-ingest/SKILL.md`·`worktree_tool.py`·`README.md` 6개 문서에 남아 있던 "merge 후 허브가 brain을 반영한다"류의 낡은 전제를 모두 새 계약으로 통일했다.
- `opal-pilot-dev/SKILL.md`의 merge 후 안내에 `brain-tool index` 재생성 스텝과, brain 관련 merge 충돌 발생 시 해결 절차(수동 병합 → `brain-tool validate`/`lint` → 필요시 index 재실행 → 커밋)를 추가했다.
- `.gitattributes`에 `.opal/brain/log.md`·`.opal/brain/index.md`의 `merge=union` 전략을 추가했다. 같은 page를 두 브랜치가 겹치는 내용으로 고치는 경우는 `merge=union`을 적용하지 않고 git 기본 3-way merge(표준 conflict marker)로 안전하게 폴백하도록 의도적으로 남겨 뒀다 — union을 구조적 frontmatter 문서에 적용하면 오히려 데이터가 깨질 위험이 있기 때문이다.
- 태스크 161/162/167이 선언했지만 이 버그 때문에 실제로 반영되지 못했던 brain 후보(신규 2건, 갱신 4건)를 허브에 직접 백필했다(파일만 작성, 커밋은 사용자 승인 경계라 하지 않음 — 아래 참고 참조). 163의 선언은 이미 반영돼 있어 재작업하지 않았다.

유지된 것: `.opal/MEMORY.json` 워크트리 쓰기 거부(memory-tool, 별도 코드 경로), 선언하지 않은 brain 경로 변경 시 `worktree-tool finalize`의 차단(S⊆D 판정), 허브(비워크트리) 태스크의 brain-tool 동작.

## 변경 파일

- `opal/tools/brain-tool/brain_tool.py`
- `opal/tools/brain-tool/tests/test_brain_tool.py`
- `opal/core/references/harness/done-template.md`
- `opal/skills/op-oppb-knowledge-finalize/SKILL.md`
- `opal/skills/opal-pilot-dev/SKILL.md`
- `opal/skills/op-brain-ingest/SKILL.md`
- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/worktree-tool/README.md`
- `.gitattributes`
- (허브, 미커밋) `.opal/brain/pages/flow/test-cycle-early-human-handoff.md`(신규), `.opal/brain/pages/concept/scenario-economy-advisory-gate.md`(신규), `.opal/brain/pages/entity/test-tool.md`(갱신), `.opal/brain/pages/concept/scenario-goal-coverage-gate-loop.md`(갱신), `.opal/brain/pages/entity/op-scenario-gate-skill.md`(갱신), `.opal/brain/pages/entity/state-tool.md`(갱신), `.gitattributes`(동일 4줄)

## 검증

- `python -m pytest opal/tools/brain-tool/tests/test_brain_tool.py -q` → 159 passed (반전 3건 + 불변 4건 + 전체).
- `python -m pytest opal/tools/worktree-tool/tests/ -q` → 167 passed, 1 failed(`test_s22_concurrent_slot_warning_appears_from_second_slot_only` — uv 캐시 볼륨 차이로 인한 환경 특이적 실패, 이번 변경과 무관, docstring/README 텍스트 정정만 있었고 로직 미변경 확인).
- TEST-SCENARIO.md S-1~S-8, S-12(9건) 전부 PASS — 실제 합성 git 저장소로 단일 브랜치 merge(S-3), 미선언 경로 차단(S-4), 두 브랜치 log/index union 병합(S-5), 같은 page 충돌+수동 해결 절차(S-12)까지 mock 없이 실측(`test-scenario.json` 참조).
- PM Gate: 컨벤션 자동 진단(opal-convention-checker) Critical/High 0건, Medium advisory 2건(테스트 파일 헤더 문구 잔존)은 즉시 정정 후 pytest 재확인.

## 회고적 학습 후보

.opal/brain/pages/entity/brain-tool.md
.opal/brain/pages/entity/worktree-tool.md
.opal/brain/pages/concept/worktree-close-brain-write-contract.md

## 참고

- 허브의 161/162/167 백필(6 page + `.gitattributes` 4줄)은 파일로만 작성돼 있고 아직 커밋되지 않았다 — `tasks/169-261001-opds-워크트리-CLOSE-지식-반영/run/brain-backfill-report.md`에 정확한 경로 목록과 경고 문구가 있다. **이 백필을 먼저 하나의 커밋으로 main에 반영한 뒤에만(그래야 `.gitattributes`의 `merge=union`이 활성화된다) 이 태스크(169) 브랜치를 포함해 어떤 브랜치든 merge하라.**
- **[MUST] 이 태스크의 수정은 아직 전역 배포본(`~/.opal/`)에 반영되지 않았다.** CLOSE의 op-brain-ingest 디스패치에서 실측 확인: `~/.opal/tools/brain-tool/run.sh`(배포본, mtime 2026-09-29)는 여전히 구버전이라 `_inside_worktree` 차단이 그대로 남아 있고, 워크트리 cwd 기본 쓰기가 `allocator_root_required`로 거부된다. 저장소 소스(`opal/tools/brain-tool/brain_tool.py`, mtime 2026-10-01)의 수정 자체는 diff로 정확함을 확인했다 — TEST 단계(S-1~S-8, S-12)는 이 저장소 소스를 pytest/직접 호출로 검증했으므로 결과는 유효하다. **merge 후 `scripts/install-mac.sh`를 재실행해 배포본을 갱신하면**, 이 태스크 자신의 brain 후보도 실제로 ingest할 수 있다. 재실행 후 워크트리(또는 merge된 브랜치) cwd에서 아래 3개 명령을 플래그 없이 그대로 실행하면 된다(본문은 이미 작성돼 스크래치에 보관돼 있었으나 세션 종료 시 사라지므로, 아래는 재현 가능하도록 핵심 구조만 남긴다 — 실제 본문은 PLAN.md D-1~D-15·DONE.md 본 문서를 근거로 op-brain-ingest를 다시 디스패치해 새로 작성해도 된다):
  - `pages/concept/worktree-close-brain-write-contract.md` (신규) — brain-tool 쓰기 루트 반전 + CLOSE/merge 설계 통합.
  - `pages/entity/brain-tool.md` (갱신) — `require_write_root` 기본값 반전 반영.
  - `pages/concept/worktree-task-root-allocator-root-split.md` (갱신) — "브레인 도구도 명시 인자 없는 쓰기를 전용 오류로 막는다"던 WHY 섹션(:39)이 이제 틀린 서술이므로 교정 필요.
- 태스크 168(opd2)의 진행 중 산출물, oppb의 Project Knowledge Finalizer 아키텍처(별도 batch-once 설계)는 이번 변경 범위 밖이다.
- `opal/tools/worktree-tool/tests/` 스위트의 기존 환경 특이적 실패(`test_s22_concurrent_slot_warning_appears_from_second_slot_only`) 1건은 이 태스크가 만든 것이 아니며 별도 확인이 필요하면 후속 태스크로 남긴다.
