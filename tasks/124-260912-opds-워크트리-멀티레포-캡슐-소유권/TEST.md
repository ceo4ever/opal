---
template: sdlc-v2
---
# TEST: 워크트리 multi-repo 캡슐 소유권 — 계약 이관과 worktree-tool 구현

> 입력: [TEST-SCENARIO.md](TEST-SCENARIO.md), [TASK.md](TASK.md), [PLAN.md](PLAN.md), [REGRESSION-EVIDENCE.md](REGRESSION-EVIDENCE.md)
> 수행: opal-test-agent (BE mode) | 완료일시: 2026-09-12 19:40 KST
> 결과 SSOT: `test-scenario.json` (locked, 28 시나리오)

## 판정

**All Pass** — 28/28 PASS, FAIL 0건, BLOCKED 0건.

`test-tool scenario-status` 최종 집계:

```json
{"ok": true, "command": "scenario-status", "locked": true, "total": 28,
 "red_confirmed": 19, "red_required": 19, "red_confirmed_required": 19,
 "passed": 28, "failed": 0, "blocked": 0}
```

RED-first 규율 충족: `red_required` 19건 전건이 구현 전 실패 증거(`red_confirmed`)를 가진 뒤 이번 TEST에서 GREEN으로 전환됐다.

## 실행 방식

- 시나리오별로 **대응 테스트를 개별 실행**해 그 exit code와 pytest 요약을 증거로 삼았다. 전체 스위트 1회 통과를 28건 증거로 뭉뚱그리지 않았다.
- 회수·롤백 순서와 `sparse-checkout`·`prune` 호출 유무는 테스트가 설치하는 **git tracer**(`_install_git_tracer`)의 실제 호출 로그로 관측했다. 문구 존재 확인이 아니다.
- 결정론 검사 4건(S-21·S-22·S-23·S-25)은 grep·ls·git diff·`code-scan validate`를 본 세션에서 직접 실행했다.
- S-18·S-19는 EXECUTE가 이미 수집한 `REGRESSION-EVIDENCE.md`의 해당 절을 **절 번호를 명시해 인용**했다. 측정에 쓰인 임시 fixture(497M)가 §6.2에서 삭제 실증됐고 격리 `HOME` 배포 경로도 회수돼 재실행이 불가하므로 인용을 택했으며, 대신 본 세션에서 독립 교차확인을 추가했다(아래 참조).

## 시나리오별 판정

| ID | AC/C | 판정 | 증거 요약 |
|---|---|---|---|
| S-1 | AC-1 | PASS | `-k test_t124_s1_create_registers_root_and_child_worktrees` exit 0 (1 passed/117 deselected, 3.40s). `ok: true`, entries 3건(root·alpha·beta), slot root가 루트 저장소 worktree로 등록·자식 2건이 각자 저장소에 등록 |
| S-2 | AC-2 | PASS | `-k ..._s2_issued_task_path_satisfies_ownership_invariant` exit 0 (1.25s). `task_home == slot root`, `artifact_repo == "."`, 불변식 `task_path == realpath(task_home/tasks/900-…)` 성립, 메타 4필드 응답과 일치 |
| S-3 | AC-3, AC-16 | PASS | `-k ..._s3_root_eligibility_violation...` exit 0 (**5 passed**/113 deselected, 6.20s — R-1~R-5 parametrize). 전건 `TASK_ARTIFACT_REPO_INVALID` + `violations == [해당 조건]` 1건만 |
| S-4 | AC-3, C-2 | PASS | `-k ..._s4_root_eligibility_block_has_no_side_effects` exit 0 (**5 passed**, 4.32s). V1~V5 전건 slot 디렉토리 미생성 + 전 repo worktree 0건 |
| S-5 | AC-4 | PASS | `-k ..._s5_init_draft` exit 0 (**6 passed**/112 deselected, 5.47s). V1~V5 초안에 `task_artifacts` 부재, R-1에서 `baseBranch`·`_baseBranch_candidates`도 부재. 대조군 M0는 `{"repo":"."}`+`baseBranch` 제시 |
| S-6 | AC-4, H-4 | PASS | `-k ..._s6_child_base_refs_resolve...` exit 0 (1.37s). alpha=`origin/main`, beta=`origin/develop`(자기 `origin/HEAD`), 원격 없는 root=`main`(자기 HEAD 폴백). 빈 문자열 0건 |
| S-7 | AC-5 | PASS | `-k ..._s7_non_dot_artifact_repo_is_unsupported` exit 0 (0.82s). `TASK_ARTIFACT_REPO_UNSUPPORTED` |
| S-8 | AC-5 | PASS | `-k ..._s8_missing_task_artifacts...` exit 0 (0.84s). `TASK_ARTIFACT_REPO_MISSING` 기존 계약 보존 |
| S-9 | AC-6 | PASS | `-k ..._s9_root_tracking_overlap...` exit 0 (0.78s). `TASK_ARTIFACT_REPO_OVERLAP`(INVALID 아님 — D-24 판정 순서), payload에 `workspace/alpha`, slot 미생성·worktree 0건 |
| S-10 | AC-7 | PASS | `-k ..._s10_preflight_entry_set_equals_created_worktree_set` exit 0 (1.33s). 선언 집합 == 등록 집합, 3건, slot root 포함. 코드: `worktree_tool.py:1088-1092`(정의)·`:1114`(base-ref)·`:1135`(생성)이 `plan_entries`만 소비 |
| S-11 | AC-8 | PASS | `-k ..._s11_base_refs_are_frozen_per_repo_with_overrides` exit 0 (1.19s). 메타 `entries[].base_ref` = root:`main`, alpha:`main`, beta:`develop` |
| S-12 | AC-8 | PASS | `-k ..._s12_unknown_base_branch_override_key_is_rejected` exit 0 (0.74s). `CONFIG_UNKNOWN_REPO` + 위반 키 `workspace/gamma` 동봉 |
| S-13 | AC-9, AC-16 | PASS | `-k ..._s13_remove_without_force...` exit 0 (2.16s). tracer 로그 회수 순서 `[beta, alpha, slot_root]`. `ok: true`, `forced: false`, `bypassed_guards: []`(GUARD_DIRTY 미발생), slot·메타 회수 |
| S-14 | AC-9 | PASS | `-k ..._s14_mid_create_failure_rolls_back_children_before_root` exit 0 (1.76s). beta base를 `no-such-base`로 두어 생성 국면 실패 → 롤백 순서 `[alpha, slot_root]`, 잔여 worktree 0건·slot 0건 |
| S-15 | AC-10, C-6 | PASS | `-k ..._s15_blocked_child_removal...` exit 0 (2.13s). `git worktree lock`(3중 가드는 clean) → `WORKTREE_REMOVE_FAILED` + 실패 경로 동봉, 메타·slot root·alpha 디렉토리 보존 |
| S-16 | AC-10 | PASS | `-k ..._s16_remove_retry_without_force...` exit 0 (2.51s). 1차 부분 회수(beta 제거됨) 확인 → unlock 후 `--force` 없이 재호출 `ok: true`, `forced: false`. tracer 순서 `[alpha, slot_root]` — beta 재제거 시도 없음(skip) |
| S-17 | AC-11, C-6 | PASS | `-k ..._s17_registration_path_mismatch...` exit 0 (**2 passed**/116 deselected, 3.69s). (a)·(b) 두 경우 모두 `WORKTREE_REMOVE_FAILED`. tracer 로그에 `worktree prune` **0건**, (b)의 `user-file.txt` 보존, 메타·slot 보존 |
| S-18 | AC-12, C-2, C-8, H-3 | PASS | REGRESSION-EVIDENCE **§1.2** 18쌍 전건 바이트 동일·정규화 0회·stderr 6건 0B / **§1.3** `init` draft 8키 집합·순서·값 동일, stdout 791B 동일, 신설 키 monorepo 미노출 / **§1.5** 비공허성(배포본 3파일 sha256 DIFF, 배포본↔소스 BYTE-EQ, 신규 계약 문자열 after 11회·base 0회) / **§1.4** 데이터 루트 지문 `e661dbe7…` 양쪽 동일 |
| S-19 | AC-13, C-3 | PASS | REGRESSION-EVIDENCE **§3.2** 6명령 × 3채널 = 18쌍 전건 바이트 동일·정규화 0회·exit 0/0. #12·#13 stdout sha256이 태스크 119 §1.2 기록값과 동일. **§3.3**이 커버 한계를 명시 |
| S-20 | AC-15, H-2 | PASS | `pytest opal/tools/worktree-tool/tests/ -q` exit 0 → **118 passed in 81.86s**. 지정 회귀 4건 개별 재실행 → 4 passed/114 deselected (1.42s). **수정 없음 실증**: 4 함수 본문 md5가 HEAD 사본과 전건 SAME, test 파일 diff는 `@header` 1줄 교체 외 전부 append(`@@ -2193,3 +2194,845 @@`) |
| S-21 | AC-14, C-7 | PASS | `worktree.md:86` §multi-repo 캡슐 소유권 계약 존재. 하위: `:98` R-1~R-5(`:106-110` 5행 표), `:102` 판정 순서, `:153` 생성·회수 순서(역순 [MUST]), `:166` 경로×등록 2축 멱등 4행 판정표. `docs/proposals/` 잔존 **0건**, `archives/`에 존재. 선행 제안서 헤더에 `**§8 대체**:` 1행 |
| S-22 | C-1 | PASS | 제안서 §4·§5·§6 항목 대조 — 아래 §계약 대조표. 구현에만 있는 계약 0건, 제안서 계약 누락 0건. `git diff -M`로 제안서가 **먼저** 개정됐음 확인(헤더 "태스크 진행 중 2건 개정: R-5 신설, 판정 순서 확정") |
| S-23 | C-4 | PASS | `worktree_tool.py:239-244` `isinstance(repos, list)` + `all(isinstance(r, str))` → `list[str]` 유지, 위반 시 `CONFIG_INVALID_TYPE`. 소비부 `:1178` `sparse-checkout set *cfg["repos"] *cfg["taskCapsuleCone"]` 불변. `grep 'repos.append|repos + \[|repos.insert'` → **0건** |
| S-24 | C-5, D-11 | PASS | `-k ..._s24_multi_repo_create_never_calls_sparse_checkout` exit 0 (1.68s). tracer 로그 `sparse-checkout` **0건**. 코드: `:1173`·`:1178`은 monorepo 분기 전용 |
| S-25 | C-9 | PASS | `code-scan validate --changed <2파일>` → `validate: OK — coverage 100% (2/2)` exit 0. `@header` description 실측 내용 → 아래 §C-9 |
| S-26 | H-1, AC-16 | PASS | `-k ..._s26_root_slot_stays_clean...` exit 0 (1.21s). create 직후 루트 slot `git status --porcelain` 출력 공백 |
| S-27 | H-1 | PASS | `-k ..._s27_control_root_slot_becomes_dirty...` exit 0 (0.80s). V5에서 pre-flight 없이 raw `git worktree add`로 동일 배치 → `?? workspace/` 출현. R-5 필요성 반증 대조군 고정 |
| S-28 | H-5 | PASS | `-k ..._s28_fixture_matches_pug_observed_shape_and_is_supported` exit 0 (1.36s). 축1 루트가 `tasks`·`.opal/AGENT.md`·`.opal/MEMORY.json` 추적 / 축2 `ls-files -- workspace` 공백 + `check-ignore -q workspace/alpha` rc=0 / 축3 `main` vs `develop` 상이. 같은 fixture에서 `create ok: true`(대표성) |

## 계약 대조표 (S-22 근거)

| 제안서 절 | 계약 | 구현 좌표 | 대조 |
|---|---|---|---|
| §4.1 | `"."`만 허용, 그 외 UNSUPPORTED | `worktree_tool.py:288` | 일치 |
| §4.1 | R-1~R-4 각각 판정 + 조건 번호 동봉 | `:1049`, `:1063` | 일치 |
| §4.1 | 판정 순서 R-1~R-4 → 겹침 → R-5 | `:1042`(주석) `:1053`→`:1056`→`:1060` | 일치 |
| §4.1 | `repos[]`에 `"."` 미추가 | grep 0건 | 일치 |
| §4.3 | multi-repo에 sparse-checkout 미적용 | `:1173`·`:1178` monorepo 한정 | 일치 |
| §4.4 | 추적 겹침 → OVERLAP, 생성 전 차단 | `:1053`·`:1056` `_root_overlap_paths` | 일치 |
| §4.5 | ordered `plan_entries` 단일 소비 | `:1082-1092`·`:1114`·`:1135` | 일치 |
| §5.1 | `baseBranchOverrides` 키 `repos[] ∪ {"."}`, 벗어나면 CONFIG_UNKNOWN_REPO | `:306` | 일치 |
| §5.2 | `repos` `list[str]` 유지 | `:241-243` | 일치 |
| §5.3 | `init` 초안 키 확장은 multi-repo 분기 한정 | `_build_init_draft` 조기 반환 | 일치 |
| §6.1 | 회수·롤백 자식 → 루트 역순 | `:1432` `reversed(entries) if multi_repo` | 일치 |
| §6.2 | 전건 성공 후에만 메타·slot 삭제 | `:1488` 이후 `_delete_meta` 미도달 | 일치 |
| §6.3 | 경로×등록 2축, `_dest_registered` 재사용, prune·삭제 금지 | `:1440-1455` | 일치 |
| §6.3 | 롤백 실패 시 `residual` 보고 | `:998-1027`, `:1188-1196` | 일치 |

## AC 커버 상태

| AC | 시나리오 | 상태 |
|---|---|---|
| AC-1 | S-1 | 충족 |
| AC-2 | S-2 | 충족 |
| AC-3 | S-3, S-4 | 충족 |
| AC-4 | S-5, S-6 | 충족 |
| AC-5 | S-7, S-8 | 충족 |
| AC-6 | S-9 | 충족 |
| AC-7 | S-10 | 충족 |
| AC-8 | S-11, S-12 | 충족 |
| AC-9 | S-13, S-14 | 충족 |
| AC-10 | S-15, S-16 | 충족 |
| AC-11 | S-17 | 충족 |
| AC-12 | S-18 | 충족 (인용 증거) |
| AC-13 | S-19 | 충족 (인용 증거) |
| AC-14 | S-21 | 충족 |
| AC-15 | S-20 | 충족 |
| AC-16 | S-3, S-13, S-26 | 충족 |

## C 커버 상태

| C | 시나리오 | 상태 |
|---|---|---|
| C-1 제안서가 설계 원문 | S-22 | 충족 — 제안서 선개정 후 구현 확인 |
| C-2 monorepo 6명령 바이트 동일 | S-4, S-18 | 충족 (인용 증거) |
| C-3 비워크트리 바이트 동일 | S-19 | 충족 (인용 증거) |
| C-4 `repos[]` 타입·의미 불변 | S-23 | 충족 |
| C-5 multi-repo에 cone 미적용 | S-24 | 충족 |
| C-6 prune·미등록 디렉토리 삭제 금지 | S-15, S-17 | 충족 |
| C-7 규범 원문 `worktree.md` 소유 | S-21 | 충족 |
| C-8 실 `~/.opal/` 직접 수정 금지 | S-18(§4), 본 세션 | 충족 — 아래 관측 참조 |
| C-9 `@header` 갱신 | S-25 | 충족 |

### C-9 — `@header` 실측 내용

`worktree_tool.py:6`의 `description`이 다음을 모두 기술한다: R-1~R-4 각각 판정(R-1 불만족 시 `['R-1']`만 보고) · 판정 순서 R-1~R-4 → 추적 겹침 → R-5 · `TASK_ARTIFACT_REPO_OVERLAP` · ordered `plan_entries` 단일 소비(생성부가 `repos` 미순회) · 생성 루트→자식 / 롤백·회수 자식→루트 역순 · 경로 실재 × Git 등록 2축 멱등 + mismatch 2종 + prune 미호출 · 오류 코드 5종. `test_worktree_tool.py:6`은 "124 TEST-SCENARIO.md S-1~S-17·S-24·S-26~S-28"과 R-1~R-5 차단·역순 회수·2축 멱등을 기술한다.

## 코드 품질·보안·회귀

| 항목 | 결과 |
|---|---|
| 회귀 스위트 | `pytest opal/tools/worktree-tool/tests/ -q` → 118 passed, exit 0 |
| `@header` 무결성 | `code-scan validate --changed` → OK, coverage 100% (2/2), exit 0 |
| 하드코딩 시크릿 | 변경 파일에 자격증명·토큰 도입 0건 (변경은 git 경로 판정·오류 코드·문서) |
| `.gitignore` | 변경 없음 |
| 목업 잔존 | 0건 — 전 시나리오가 실 git 저장소 fixture와 CLI subprocess로 수행됐다. `mock`/`patch` 미사용 |
| 변경 범위 | `git status --porcelain`이 배정 5경로 + 태스크 폴더만 보고. 커밋 0건 |

## 한계 (과대주장 방지)

1. **fixture 한정 판정** — 모든 multi-repo 판정은 `tmp_path`에 구성한 M0/V1~V6 fixture에서 나왔다. `/Volumes/Data/StoreLinkStudio/pug` 실환경 연동은 본 태스크 범위 밖이며(D-22), 실환경 완주는 후속 태스크가 소유한다(H-5). S-28이 fixture가 pug 실측 형상과 3축 동형임을 고정하지만, 동형성은 대표성이지 실환경 통과가 아니다.
2. **S-18·S-19는 인용 증거** — 본 세션이 install 스왑을 재실행하지 않았다. 측정 fixture(497M)와 격리 `HOME` 배포 경로가 §6.2에서 삭제 실증돼 재현이 불가하기 때문이다. 다만 §1.6 AST 대조 결론(`cmd_init`·`cmd_list`·`cmd_status`·`cmd_finalize` UNCHANGED)과 `:1178` monorepo 소비부 잔존은 본 세션에서 `git diff`로 독립 교차확인했다.
3. **S-19 커버 범위** — `event-loader load --event session.project`는 `document_count: 0`이라 manifest 해석·receipt 구성만 대조하며, `harness/worktree.md` 본문이 실리는 이벤트 payload는 판정하지 않는다(§3.3 자기고지).
4. **S-27은 구현 경로가 아니다** — R-5 조건의 필요성을 증명하는 대조군이며 구현 전후 동일 관측이 정상이다.

## 관측 사항 (블로커 아님, PM 확인 권고)

TEST 수행 중 실 `~/.opal/` 트리 전체의 mtime이 `2026-09-12 19:37:56`으로 일괄 갱신됐다(본 에이전트는 install을 실행하지 않았다 — `run.sh` 계열 자가 배포로 추정). 배포본 상태를 확인한 결과:

- `~/.opal/tools/worktree-tool/worktree_tool.py` sha256 앞 16 = `2bb746daa1e4b9da`
- HEAD 사본 = `2bb746daa1e4b9da` (**동일**)
- 워크트리 소스(124 변경본) = `21f6c12d0ec512a3` (**상이**)

즉 배포본은 **124 변경 이전 base**이며, 124의 구현이 실 `~/.opal/`에 배포되지 않았다 — C-8 충족. 이 해시는 REGRESSION-EVIDENCE §1.5가 base로 기록한 값과도 일치한다. 다만 TEST 세션 중 외부 배포 이벤트가 있었다는 사실 자체는 PM이 출처를 확인할 가치가 있다.

## 블로커

없음.
