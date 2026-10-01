# GC SECURITY FINAL RECHECK — 20260926T094658Z

## 1. 헤더

- 실행 일시: 완료 2026-09-26 09:46:58 UTC
- 범위: task 158의 현재 uncommitted OPPB runtime/tests/skills/docs/schema / 대상 파일 23개
- 기준선: `GC-SECURITY-20260926T093822Z-recheck.md`
- 에이전트: 독립 보안 평가자 (`op-gc-security` 계약)
- APPLY 수행 여부: N — read-only 최종 재검사
- 실행 상태: `pass`
- 최종 판정: **PASS**

## 2. 결과 요약

| 지표 | 값 |
|---|---:|
| Blocking finding | 0 |
| Advisory finding | 0 |
| Informational finding | 0 |
| 대상 파일 | 23 |
| targeted tests | 30 passed |
| missing capabilities | 0 |

직전 재검사에서 남았던 blocking 3건과 advisory 1건이 모두 보완됐다. 최신 변경 범위에서 추가 보안 finding은 관측되지 않았다.

## 3. 직전 finding 해소 확인

- `GC-R001` lock symlink 선행 open: **resolved**
  - source tree의 symlink를 lock 획득 전에 거부한다.
  - lock 파일은 source directory fd를 기준으로 `O_NOFOLLOW | O_CREAT | O_RDWR`로 연다.
  - lock symlink가 외부의 존재하지 않는 target을 가리킬 때 외부 파일 생성이 0건인 음성 테스트를 확인했다.

- `GC-R002` destination namespace TOCTOU: **resolved**
  - allocator root를 directory fd로 연 뒤 `tasks → canonical task → .oppb-run`을 각 단계 `O_DIRECTORY | O_NOFOLLOW`로 고정한다.
  - temporary directory 생성, 재귀 copy, 최종 rename을 동일 archive fd에서 수행한다.
  - allocator의 `tasks` 조상이 외부 symlink인 경우 외부 쓰기 없이 거부되는 음성 테스트를 확인했다.

- `GC-R003` tree hash framing: **resolved**
  - hash 입력에 domain separator, entry type, 8-byte path length, path, 8-byte content length, content를 포함한다.
  - directory entry도 별도 type으로 봉인하므로 빈 directory 구조도 hash에 반영된다.
  - 이전 구조 collision PoC의 두 tree가 서로 다른 digest를 내는 테스트를 확인했다.

- `GC-R004` archived status hash 미검증: **resolved**
  - archived `status`가 현재 tree hash를 fd/no-follow 순회로 다시 계산해 marker와 대조한다.
  - archive 변조 후 idempotent finalize와 status가 모두 `archive_integrity_failed`로 거부되는 테스트를 확인했다.

## 4. 추가 보안 대조

- 신규 run root와 legacy run root는 root symlink를 거부하고 manifest 기반 경계를 검증한다.
- 명시 `--allocator-root`는 Git repository top-level 검증 후 run manifest의 allocator와 realpath 대조한다.
- successful-run 판정과 retained snapshot은 Supervisor/workgraph nonblocking exclusive lock 구간 안에서 수행된다.
- 재귀 copy와 재검증은 symlink 및 특수 파일을 거부하고 regular file/directory만 처리한다.
- 보존 임시 directory와 marker는 `0700`/`0600`으로 생성되며 파일은 `O_EXCL | O_NOFOLLOW`로 생성한다.
- publish는 동일 archive directory fd의 `rename` 뒤 directory `fsync`까지 수행한다.
- 실제 자격증명/private key 원문은 대상 변경에서 발견되지 않았다.

## 5. 검증 근거

- `$HOME/.opal/.venv/bin/python -m pytest opal/tools/oppb-runtime-tool/tests/test_oppb_init.py -q` → `30 passed in 8.79s`
- `git diff --check` → 오류 없음
- 최종 검토 시 source SHA-256:
  - `oppb_runtime_tool.py`: `2642e6fa98729e9ba33181d4c7bef2c26ad3078e5b967c13de7c47c17c5b1dbd`
  - `test_oppb_init.py`: `d22dabc8a7dea51e67937ff3130a981be939b9ac7b4c5898daa49fdaa6fb1652`
- 활성 기준: `docs/SECURITY.md`, OWASP Top 10/CWE Top 25 내장 baseline
- 비활성 영역: 웹 인증/인가, SQL/command injection, XSS, CSRF, SSRF, dependency vulnerability audit — 대상은 신규 dependency가 없는 Python local filesystem CLI와 문서/테스트 변경이다.

## 6. 검사 대상

1. `docs/proposals/opal-oppb-project-build-pilot.md`
2. `opal/core/references/harness/worktree.md`
3. `opal/skills/op-oppb-knowledge-finalize/README.md`
4. `opal/skills/op-oppb-knowledge-finalize/SKILL.md`
5. `opal/skills/op-scenario-gate/SKILL.md`
6. `opal/skills/opal-pilot-project-build/SKILL.md`
7. `opal/tools/oppb-runtime-tool/README.md`
8. `opal/tools/oppb-runtime-tool/oppb_runtime_tool.py`
9. `opal/tools/oppb-runtime-tool/schema/api-freeze.md`
10. `opal/tools/oppb-runtime-tool/schema/oppb-state.schema.json`
11. `opal/tools/oppb-runtime-tool/tests/test_cache.py`
12. `opal/tools/oppb-runtime-tool/tests/test_checkpoint.py`
13. `opal/tools/oppb-runtime-tool/tests/test_controller.py`
14. `opal/tools/oppb-runtime-tool/tests/test_evidence.py`
15. `opal/tools/oppb-runtime-tool/tests/test_lease.py`
16. `opal/tools/oppb-runtime-tool/tests/test_oppb_init.py`
17. `opal/tools/oppb-runtime-tool/tests/test_probe.py`
18. `opal/tools/oppb-runtime-tool/tests/test_product_flow.py`
19. `opal/tools/oppb-runtime-tool/tests/test_recovery.py`
20. `opal/tools/oppb-runtime-tool/tests/test_revalidation.py`
21. `opal/tools/oppb-runtime-tool/tests/test_supervisor.py`
22. `opal/tools/oppb-runtime-tool/tests/test_verifier_adapter.py`
23. `opal/tools/oppb-runtime-tool/verifier_adapter.py`

## 7. 판정

검사 실행은 완전했고 `missing_capabilities`가 없으며 blocking/advisory finding이 0건이므로 최종 판정은 **PASS**다.
