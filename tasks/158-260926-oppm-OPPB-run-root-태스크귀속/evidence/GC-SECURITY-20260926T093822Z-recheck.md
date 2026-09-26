# GC SECURITY RECHECK REPORT — 20260926T093822Z

## 1. 헤더

- 실행 일시: 완료 2026-09-26 09:38:22 UTC
- 범위: task 158의 현재 uncommitted OPPB runtime/tests/skills/docs/schema / 대상 파일 23개
- 기준선: `GC-SECURITY-20260926T091900Z.md`
- 에이전트: 독립 보안 평가자 (`op-gc-security` 계약)
- APPLY 수행 여부: N — read-only 재검사
- 실행 상태: `pass`
- 최종 판정: **FAIL** — 잔여 blocking finding 3건, advisory 1건

## 2. 재검증 요약

| 항목 | 결과 |
|---|---|
| 명시 `--allocator-root`와 manifest 대조 | 보완 확인 |
| run root leaf symlink 거부 | 보완 확인 |
| destination task/archive parent의 정적 symlink 거부 | 보완 확인 |
| Supervisor/workgraph nonblocking exclusive lock | 보완 확인 |
| 기존 archive의 run id 및 tree hash 재계산 | 보완 확인 |
| 전체 targeted test | 27 passed |
| 잔여 차단 | lock 파일 symlink 선행 open, destination TOCTOU, tree hash framing |

1차 GC-001~GC-005의 직접 재현은 대체로 보완됐다. 그러나 동일 보안 경계의 우회 경로 세 건이 남아 최종 PASS로 전환할 수 없다.

## 3. 잔여 finding

### High (3건)

- [ ] GC-R001 [`opal/tools/oppb-runtime-tool/oppb_runtime_tool.py:603`, `_hold_archive_locks`] lock 파일 symlink를 검증 전에 쓰기 모드로 엶
  - 카테고리: CWE-22 Path Traversal
  - fingerprint: `d11e5d5cd91a2712`
  - 기준: Base CWE-22 (T1), disposition `blocking`, confidence `high`
  - 관측: `_hold_archive_locks`는 `supervisor.lock`과 `workgraph.lock`을 `.open("a+")`로 연다. source tree의 `_assert_no_symlinks(run_root)`는 그 뒤 740행에서 실행된다. 두 lock path 중 하나가 외부 경로를 가리키는 symlink이면 검증 전에 target을 따라 열고, target이 없으면 생성할 수 있다.
  - 영향: run tree 안의 lock symlink로 프로세스 권한 범위의 외부 파일을 생성하거나 접근할 수 있다. archive가 이후 거부되더라도 외부 부작용은 이미 발생한다.
  - 해결 방안: lock을 열기 전에 lock path와 핵심 입력 파일을 `lstat`하고, 가능하면 `os.open(..., O_NOFOLLOW|O_CREAT|O_RDWR)`와 검증된 directory fd를 사용한다. symlink 검사는 모든 source read/write보다 먼저 수행한다.
  - 검증: 존재하지 않는 외부 target을 향한 `supervisor.lock`·`workgraph.lock` symlink 각각에 대해 finalize가 외부 target을 생성하지 않고 거부되는 음성 테스트를 추가한다.

- [ ] GC-R002 [`opal/tools/oppb-runtime-tool/oppb_runtime_tool.py:740`, `cmd_finalize_run`] destination symlink 검사와 사용 사이 TOCTOU가 남음
  - 카테고리: CWE-362 Race Condition / CWE-22 Path Traversal
  - fingerprint: `f7a8c38e03f43573`
  - 기준: Base CWE-362·CWE-22 (T1), disposition `blocking`, confidence `high`
  - 관측: `archive_parent.is_symlink()`와 `_is_within()`을 검사하지만, path 기반 검사 뒤 `copytree`·`os.replace`까지 동일 destination directory fd를 고정하지 않는다. source lock은 destination namespace 변경을 막지 못한다. 또한 `allocator_root/tasks` 조상 자체가 symlink인지 검사하지 않는다.
  - 영향: 검사 직후 `.oppb-run` 또는 조상 path를 symlink/rename으로 교체하면 복사·rename을 canonical task 밖으로 유도할 수 있다.
  - 해결 방안: allocator의 실제 `tasks` directory부터 `openat`/dirfd와 no-follow로 destination task 및 `.oppb-run`을 열고, 임시 directory 생성과 최종 rename을 같은 검증된 fd 기준으로 수행한다. destination 전용 lock 또는 원자적인 안전 생성도 필요하다.
  - 검증: 검사 직후 `.oppb-run`을 외부 symlink로 교체하는 race harness와 `allocator_root/tasks` symlink fixture에서 외부 쓰기가 0건이어야 한다.

- [ ] GC-R003 [`opal/tools/oppb-runtime-tool/oppb_runtime_tool.py:574`, `_tree_sha256`] tree hash가 파일 content 길이/종료 경계를 봉인하지 않음
  - 카테고리: OWASP-A08 Software and Data Integrity Failures
  - fingerprint: `a340c85f6518c6fd`
  - 기준: Base OWASP-A08 (T1), disposition `blocking`, confidence `high`
  - 관측: 각 항목을 `relative_path + NUL + content`로 이어 붙이지만 content 길이나 종료 delimiter를 넣지 않는다. 따라서 파일 경계가 다른 두 tree가 SHA-256 충돌 공격 없이 같은 byte stream을 만들 수 있다. 실측 PoC에서 tree A `{a: b"xb\\0", c: b"Y"}`와 tree B `{a: b"x", b: b"c\\0Y"}`가 모두 `b520a947ad6ca44391ea300432f475de0a10c72add4795a7a9fc020a2e564417`을 반환했다.
  - 영향: archive 파일명과 내용을 구조적으로 바꿔도 marker hash 재검증을 통과할 수 있어 새 idempotent integrity check를 우회한다.
  - 해결 방안: domain separator와 각 entry의 path byte length, content byte length, file type/mode를 명확한 fixed-width 또는 canonical encoding으로 hash한다. 예: `type || path_len || path || content_len || content`.
  - 검증: 위 두 tree의 digest가 달라야 하며 파일 추가·삭제·rename·binary NUL content를 포함한 벡터 테스트를 추가한다.

### Medium advisory (1건)

- [ ] GC-R004 [`opal/tools/oppb-runtime-tool/oppb_runtime_tool.py:813`, `cmd_status`] archived status는 marker hash를 재검증하지 않음
  - 카테고리: OWASP-A08 Software and Data Integrity Failures
  - fingerprint: `ac604a1b2108ee20`
  - 기준: Base OWASP-A08 (T1), disposition `advisory`, confidence `high`
  - 관측: idempotent `finalize-run`은 hash를 재계산하지만 `status`는 `run.closed.json`의 `content_sha256`을 그대로 반환한다.
  - 영향: 변조 archive를 조회한 소비자가 status의 hash를 현재 내용에 대한 검증값으로 오해할 수 있다. 현재 문서는 status를 무결성 verifier로 명시하지 않아 advisory로 분류했다.
  - 해결 방안: status에서도 tree hash를 재검증해 `integrity_verified`를 명시하거나, hash가 marker 선언값일 뿐임을 필드명/문서로 구분한다.
  - 검증: archive 변조 뒤 status가 integrity 실패를 반환하거나 `integrity_verified: false`를 보고해야 한다.

## 4. 기준선 delta

- 1차 `GC-001` 정적 archive-parent symlink: **resolved**, 단 destination namespace TOCTOU는 `GC-R002`로 신규 발견.
- 1차 `GC-002` run-root leaf symlink: **resolved**, 단 lock 파일 선행 open은 `GC-R001`로 신규 발견.
- 1차 `GC-003` mutable allocator manifest 경계: **resolved** — 명시 allocator, repository top-level, manifest realpath 대조 확인.
- 1차 `GC-004` legitimate Supervisor/workgraph writer 경쟁: **resolved** — 두 lock을 nonblocking exclusive로 획득한 snapshot 구간 확인.
- 1차 `GC-005` 단순 archive 변조/marker 맹신: **resolved** — idempotent path의 run id와 tree hash 대조 확인. 다만 hash encoding 자체의 구조 충돌은 `GC-R003`, status 미검증은 `GC-R004`로 남음.

## 5. 검사 근거

- 대상 파일 23개는 1차 보고서와 동일하며 전부 프로젝트 root 아래에 존재한다.
- 최신 `oppb_runtime_tool.py`, `test_oppb_init.py`, README, pilot skill/proposal diff 및 관련 전체 본문을 재검토했다.
- `$HOME/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q` → `27 passed in 7.64s`.
- `_tree_sha256`와 동일한 byte framing의 독립 temporary-directory PoC → 서로 다른 두 tree의 digest 동일(`equal=True`).
- 신규 의존성이 없는 Python filesystem CLI이므로 웹 인증·SQL·XSS·CSRF·SSRF 및 dependency vulnerability audit 영역은 비활성이다.
- 대상 변경에서 실제 자격증명/private key 원문은 발견되지 않았다.

## 6. 판정

blocking finding 3건이 남아 **FAIL**이다. 구현 보완 뒤 lock symlink 음성 테스트, destination race/no-follow 테스트, framed tree-hash 벡터 테스트를 포함해 다시 검증해야 한다.
