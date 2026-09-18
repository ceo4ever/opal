# GC SECURITY REPORT (FINAL) — 2026-09-13T04-00-00

> T03 기록코어(스키마·멱등·순번) 보안 **최종 확인 검사 (3회차, 범위 한정)** / oppl 태스크 파이프라인 T4b 규칙검사 축
> 직전 검사: `GC-SECURITY-2026-09-13T03-42-00-recheck.md` (판정 FAIL, blocking 1건 = GC-212)
> 자기완결 보고서 — 이 문서만으로 모든 판정의 재현이 가능하다.

## 1. 헤더

- 실행 일시: 시작 2026-09-13 03:54 / 완료 2026-09-13 04:00 / 소요 약 6분
- 범위: **전수 재검사가 아니다.** 직전 잔여 blocking 1건(GC-212) + advisory 1건(GC-213)의 **폐쇄 확인** + 회귀·부작용 확인으로 한정했다. 범위를 넓히지 않았다.
- 에이전트: opal-security-checker (read-only 진단 전담 — **소스 미수정**)
- APPLY 수행 여부: **N** (보고만)
- 판정: **PASS_WITH_ADVISORIES** — `disposition: blocking` **0건**

### 검사 대상

| # | 파일 | 행수 | 읽음 |
|---|---|---|---|
| 1 | `opal/tools/run-log-tool/run_log_core.py` | 1,510 | `_safe_read_bytes()` 게이트 구간 전문 + 회귀 관련 구간 |
| 2 | `opal/tools/run-log-tool/run_log_tool.py` | 190 | D-5 결합 확인 범위 |
| 3 | `opal/tools/run-log-tool/tests/test_run_log_tool.py` | 1,626 | 커버리지·충실도 확인 범위 |

### 검사 방법 (required_fidelity = real-usage)

전건 **`bash opal/tools/run-log-tool/run.sh <subcmd>` 실제 subprocess 실행 + 디스크 조각 파일 검사**, 또는 §2.6 인프로세스 호출로 확인했다. mock·patch·스텁·가짜 파일시스템을 쓰지 않았다. **구현 워커의 처리 보고를 신뢰하지 않고 직접 재현했다.**

---

## 2. 한 줄 결론

**blocking 0건이다.** GC-212(하드 링크)·GC-213(FIFO)은 `_safe_read_bytes()`의 `os.fstat(fd)` 게이트 + `O_NONBLOCK`으로 **실측 폐쇄**됐고, PM이 특히 지목한 두 부작용(`st_nlink == 1`의 정상 파일 오탐, `O_NONBLOCK`의 short read로 인한 `source.sha256` 훼손)은 **둘 다 발생하지 않음을 실측으로 확인**했다 — 19 MB 파일의 **60,001번째 줄**이 정상 소비됐다. 직전 resolved 8건(GC-201~206·208·209)은 되돌아가지 않았고 31건 테스트가 통과한다. 신규 지적 3건은 전부 non-blocking이며, 그중 **GC-214(링크 방어 4건에 대한 회귀 테스트 0건)**가 가장 실질적이다 — 방어는 옳지만 이를 지키는 테스트가 없다.

---

## 3. 지정 확인 2건 — 실측 결과

| ID | 직전 disposition | 주장된 처리 | 실측 | 판정 |
|---|---|---|---|---|
| **GC-212** | **blocking / high** | `os.fstat(fd)` 게이트 — `S_ISREG` + `st_nlink == 1`, 위반 시 `run_log_write_failed` | 하드 링크 **거부**, 적재 0건, `source.id` 위장 0건 | **resolved** |
| **GC-213** | advisory / medium | 같은 게이트 + `O_NONBLOCK` open 플래그 | FIFO 양쪽 경로 **0.06초** 봉투 반환 (정지 없음) | **resolved** |

### 3.1 GC-212 재현 — 하드 링크가 거부된다

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_123
mkdir -p /tmp/f3/h1/t /tmp/f3/h1/out
bash opal/tools/run-log-tool/run.sh init --task /tmp/f3/h1/t --run-id run_h1 --format json
printf '## 대행 일지\n\n| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n|---|---|---|---|---|---|\n| 1 | 2026-09-13 01:00 | PLAN | DECISION | HARDLINK-OUTSIDE | ok |\n' > /tmp/f3/h1/out/ext.md
ln /tmp/f3/h1/out/ext.md /tmp/f3/h1/t/AGENTIC-LOG.md     # 심볼릭 아님 — 하드 링크
bash opal/tools/run-log-tool/run.sh import-agentic --task /tmp/f3/h1/t --run-id run_h1 --format json
```

관측 (직전 회차는 `{"ok": true, "imported": 1}`이었다):

```json
{"ok": false, "error": {"code": "run_log_write_failed",
 "message": "기록 조각 쓰기 실패: /tmp/f3/h1/t/AGENTIC-LOG.md이 하드 링크입니다(거부): nlink=2"}}
```

- `ls -li` 로 두 경로가 **같은 inode(53757431), nlink=2**임을 확인했다 — 진짜 하드 링크다.
- `grep -c HARDLINK-OUTSIDE /tmp/f3/h1/t/run/*.jsonl` → **0** (적재 0건)
- `grep -o 'AGENTIC-LOG.md' .../run/*.jsonl | wc -l` → **0** (`source.id` 위장 소멸)

**출처(provenance) 위장 경로가 닫혔다.**

### 3.2 GC-213 재현 — FIFO가 정지시키지 않는다

```python
os.mkfifo('/tmp/f3/fifo/t/AGENTIC-LOG.md')
os.mkfifo('/tmp/f3/fifo/t/.oppl-run/journal.md')
# 10초 타임아웃으로 두 서브커맨드 실행
```

| 경로 | 직전 | 이번 실측 |
|---|---|---|
| `import-agentic` | HUNG > 8s (강제 kill) | **elapsed 0.06s**, exit 1, `run_log_write_failed: ...정규 파일이 아닙니다(거부)` |
| `import-oppl` | HUNG > 8s (강제 kill) | **elapsed 0.07s**, exit 0, `{"ok": true, "scanned": 0, "sources": []}` |

정지가 사라졌고 두 경로 모두 봉투를 반환한다. `import-oppl`이 오류 대신 skip(`scanned: 0`)으로 처리하는 것은 **의도된 파일 단위 skip 정책**이며(`_all_oppl_candidates()`의 `if read_err is not None: continue`), 가용성·경계 양쪽에 문제가 없다.

### 3.3 파일 종류 전수 — 게이트가 무엇을 막는가

| 입력 | `_safe_read_bytes()` 결과 |
|---|---|
| directory | 거부 `정규 파일이 아닙니다` |
| FIFO | 거부 `정규 파일이 아닙니다` |
| `/dev/zero` (char device) | 거부 `정규 파일이 아닙니다` |
| `/dev/null` | 거부 `정규 파일이 아닙니다` |
| 하드 링크된 정규 파일 | 거부 `하드 링크입니다: nlink=2` |
| 부재 파일 | `(None, None)` — 개입 없음 (정상) |
| 일반 정규 파일 | 정상 읽기 |

**부수 효과(유리한 쪽)**: `/dev/zero` 거부로 GC-207(원본 크기 상한 부재)의 **증폭 벡터가 함께 좁혀졌다** — 실측에서 `/dev/zero` 결합 `import-agentic`이 0.06초에 종료했다. GC-207 잔존 위험은 "태스크 안의 진짜 큰 정규 파일" 하나로 줄었다.

---

## 4. PM 지목 부작용 2건 — 반드시 함께 본 항목

### 4.1 `st_nlink == 1`이 정상 파일을 막는가 — **막지 않는다**

실제 가져오기 원본 전수의 nlink를 측정했다.

```
1  ./tasks/123-.../AGENTIC-LOG.md
1  ./tasks/104-.../AGENTIC-LOG.md
1  ./tasks/123-.../T01-.../.oppl-run/journal.md      (이하 .oppl-run 산출물 19건 전부 nlink=1)
1  docs/run-log/CONTRACT.md / docs/CONVENTIONS.md / run_log_core.py   (git 워크트리 체크아웃)
```

**실제 산출물 가져오기 end-to-end (합성 아닌 진짜 파일):**

```bash
cp tasks/123-.../AGENTIC-LOG.md            /tmp/f3/real/t/AGENTIC-LOG.md      # 72행
cp -R tasks/123-.../T01-.../.oppl-run      /tmp/f3/real/t/.oppl-run           # 29파일
bash opal/tools/run-log-tool/run.sh import-agentic ... # → {"scanned": 33, "imported": 33}
bash opal/tools/run-log-tool/run.sh import-oppl    ... # → {"scanned": 18, "imported": 18, sources 5건}
bash opal/tools/run-log-tool/run.sh validate-run   ... # → {"verdict": "pass", "event_count": 51, "violations": []}
```

**macOS·APFS에서 nlink != 1인 정상 사례가 있는가 — 의견:**

| 사례 | 실측 nlink | 오탐 위험 |
|---|---|---|
| APFS **clonefile** (`cp -c`) | **1** | 없음 — clonefile은 블록 공유일 뿐 별도 inode다 |
| 원자적 쓰기(`mkstemp`+`os.replace`, 대부분의 에디터·도구) | **1** | 없음 |
| git 워크트리 체크아웃 | **1** | 없음 |
| Time Machine 로컬 스냅샷 | 별도 볼륨이라 태스크 경로에 나타나지 않음 | 없음 |
| `cp -al` 하드링크 아카이브 복원 | 2+ | **유일한 오탐 경로** |

**결론: macOS·APFS 환경에서 nlink != 1인 정상 사례는 사실상 `cp -al` 복원뿐이다.** 이는 흔치 않고, 발생 시 거부 메시지가 `nlink=N`을 명시하므로 진단이 즉시 가능하며 실체 복사로 전환하면 해소된다. **트레이드오프가 올바른 방향으로 잡혔다** — 하드 링크는 원본과 링크가 구조적으로 구분 불가하므로(둘 다 nlink=2로 동일하게 거부된다) "링크만 거부하고 원본은 허용"이 원리적으로 불가능하다. 안전 측 실패가 정답이다.

### 4.2 `O_NONBLOCK`이 정규 파일 읽기를 훼손하는가 — **훼손하지 않는다 (가장 중점적으로 확인)**

PM이 지목한 위험: short read로 원본이 잘리면 `source.sha256`이 원본과 달라져 GC-202 계열 **출처 무결성** 문제가 된다.

**(a) 바이트 경계 전수 — 잘림 0건**

`_safe_read_bytes()`를 직접 호출해 디스크 원본과 바이트·SHA-256을 대조했다.

| 크기 | 읽은 바이트 | SHA 일치 |
|---|---|---|
| 1 B | 1 | ✅ |
| 4,096 B | 4,096 | ✅ |
| 65,536 B (파이프 버퍼 경계) | 65,536 | ✅ |
| 65,537 B | 65,537 | ✅ |
| 1 MiB | 1,048,576 | ✅ |
| 8 MiB | 8,388,608 | ✅ |
| 64 MiB | 67,108,864 | ✅ |
| 64 MiB + 12,345 B | 67,121,209 | ✅ |

**(b) 결정적 증거 — 19 MB 파일의 꼬리 카나리아**

short read가 있다면 파일 **끝**의 후보는 절대 도달하지 못한다. 19,309,034 바이트(60,001줄) `BIG.events.jsonl`을 만들고 **유일한 `type:"result"` 후보를 마지막 줄에** 두었다.

```json
{"ok": true, "data": {"scanned": 1, "imported": 1,
 "sources": [{"path": ".oppl-run/BIG.events.jsonl", "sha256": "ed9268...", "scanned": 1}]}}
```

조각에 적재된 사건의 위치자:

```
locator = .oppl-run/BIG.events.jsonl#L60001
```

**19 MB 파일의 60,001번째 줄이 소비됐다 — short read가 없다는 직접 증거다.**

**(c) 원리적 근거**: POSIX상 정규 파일의 `read()`는 `O_NONBLOCK` 유무와 무관하게 항상 즉시 완료되며 `EAGAIN`을 반환하지 않는다. `O_NONBLOCK`은 FIFO·소켓·터미널 등 **블로킹 가능한 종류에만** 의미가 있다. 구현 주석이 이 근거를 정확히 기술하고 있으며, 실측이 이를 뒷받침한다.

**(d) 출처 무결성 실측**: 실제 `.oppl-run/` 5개 원본의 `sources[].sha256`을 디스크 `shasum -a 256`과 대조 — 전건 일치 (예: `journal.md` → `b70a2d9750a38cdd...` 양쪽 동일).

> 참고(지적 아님): `sources[].sha256`의 **의미가 파일 종류별로 다르다** — `journal.md`·`*.result.json`·`*.exitcode`는 **파일 전체** 바이트 해시이고, `*.events.jsonl`은 **매칭된 줄(`stripped`)** 의 해시다(`_all_oppl_candidates():1417`). 둘 다 "실제 소비한 바이트"를 가리키므로 무결성상 문제는 없으나, 운영자가 `shasum <file>`로 대조하면 events.jsonl만 불일치한다. 직전 §5-1이 권고한 "`source.sha256`의 기준을 계약에 명문화" 항목에 **이 이원성도 함께** 포함할 것을 권한다.

---

## 5. 회귀 재확인 — resolved 8건이 되돌아갔는가

| ID | 재현 | 관측 | 판정 |
|---|---|---|---|
| GC-201 | 심볼릭 링크 `AGENTIC-LOG.md` | `run_log_write_failed: ...심볼릭 링크입니다(거부)`, leak 0 | **유지** |
| GC-202 | `.oppl-run/` 디렉터리 링크 + 하위 개별 링크 | 디렉터리 링크 거부 / 개별 링크 `sources: []`, leak 0 | **유지** |
| GC-203 | `2026-13-45 99:99` 불량 행 + 정상 행 | exit 0, `{"scanned": 1, "imported": 1}` — 정상 행만 적재 | **유지** |
| GC-204 | `[1,2,3]` 비-object result.json | exit 0, `{"scanned": 0}` | **유지** |
| GC-205 | `'['*200000` 중첩 | exit 0, `{"scanned": 0}` | **유지** |
| GC-206 | `b'\xff\xfe bad'` (journal.md·AGENTIC-LOG.md 양쪽) | exit 0, `{"scanned": 0}` | **유지** (되돌리지 않음 — 합의대로) |
| GC-208 | 중첩 키 4집합 + token 원문 | 4집합 전부 `schema_invalid`, **RAW SECRET 조각 출현 0회** | **유지** |
| GC-209 | 21 KB 거대 행 + 작은 행 2개 | `{"scanned": 2, "imported": 2}`, 재실행 `skipped_idempotent: 2`, A·C 적재 확인 | **유지** (되돌리지 않음 — 합의대로) |

**스택 트레이스 유출 0건, 전건 exit 0(거부 케이스 제외).**

추가 회귀 확인:

- **D-5 단방향 의존**: `run_log_core.py`·`run_log_tool.py`에 `state_tool`·`state.json` 문자열 **0건**(`state.changed` 사건명 제외 후 grep 실측). AC-19/MV-24 유지.
- **MV-30 3자산 동기**: 이번 수정이 **새 오류 코드를 도입하지 않았다** — 기존 `run_log_write_failed` 재사용. `RUN_LOG_ERROR_CODES` 9건 전부 `surfaces.json` err 집합에 존재. `surfaces.json`에만 있는 15건은 T05/T08/T11 소유 코드로 이번 범위와 무관. **계약 3자산 개정 불필요.**
- **파일 권한**: 조각 `-rw-------`(0600), `run/` `drwx------`(0700) 유지.
- **테스트**: `opal/tools/run-log-tool/tests/` **31 passed in 135.60s** (exit 0, 직접 실행 확인).
- **real-usage 충실도**: `mock|patch|MagicMock` 매치 1건은 "사용하지 않는다"는 헤더 산문이며 실제 사용 0건.
- **범위 준수**: `opal/tools/state-tool/`을 읽지도 지적하지도 않았다(T05 소유).

---

## 6. 신규 지적 (3건 — 전부 non-blocking)

### Advisory (1건)

- [ ] **GC-214** [`opal/tools/run-log-tool/tests/test_run_log_tool.py`:1] 링크·파일종류 경계 방어 4건(GC-201·202·212·213)에 **회귀 테스트가 0건**이다
  - 카테고리: CWE-1120 Excessive Code Complexity 계열 — 보안 제어의 검증 부재 (OWASP A05 Security Misconfiguration 보조)
  - 위반 기준: 프로젝트(`TASK.md` C-2 회귀 무손상 요구 + `red-first.md` §4 관례) — T0
  - fingerprint: `ede8b89478507254` / severity **medium** / confidence **high** / disposition **advisory**
  - 관측 사실: 테스트 파일 전수 grep 결과 `symlink`·`심볼릭`·`hard`·`nlink`·`fifo`·`mkfifo`·`S_ISREG`·`정규 파일`·`traversal`·`escape` **전건 0 매치**. 시나리오 S-3~S-29는 스키마·멱등·순번·가져오기 의미론을 덮지만, **경계 방어는 하나도 덮지 않는다**. S-8(`test_source_has_no_state_tool_coupling`)이 정적 문자열 검사를 하는 것과 대조적이다.
  - 설명: 3회 연속 검사에서 **blocking 4건이 전부 이 계열**에서 나왔다(GC-201·202 → 2회차, GC-212 → 3회차). 지금 `_safe_read_bytes()`는 옳지만, 이 함수를 리팩터링하면서 `os.fstat` 게이트나 `O_NONBLOCK`을 떨어뜨려도 **31건 테스트는 전부 초록으로 통과한다**. 방어가 회귀 감지 장치 없이 서 있다. 이는 보안 결함 자체가 아니라 **보안 제어의 내구성 결함**이다.
  - 해결 방안: S-30(가칭) 1개 시나리오로 충분하다 — `run.sh import-agentic`/`import-oppl`에 대해 (a) 심볼릭 링크, (b) 하드 링크(`os.link`), (c) FIFO(`os.mkfifo`, 타임아웃 단언 포함), (d) 정상 파일 대조군을 각각 넣고 **거부 봉투 + 조각 적재 0건 + 정상 대조군 통과**를 판정한다. 기존 `subprocess` 실호출 관례를 그대로 쓰면 되고 새 의존성이 없다. FIFO 케이스는 `subprocess.run(..., timeout=N)`으로 정지 회귀까지 잡는다.
  - 자동 수정: N
  - 검증: 새 시나리오가 현재 구현에서 통과하고, `os.fstat` 게이트 3줄을 임시로 제거하면 **실패**하면 유효하다(RED 확인).

### Informational (2건)

- [ ] **GC-215** [`opal/tools/run-log-tool/run_log_core.py`:411] `os.fdopen()` 실패 시 파일 디스크립터가 닫히지 않는다
  - 카테고리: CWE-775 Missing Release of File Descriptor after Effective Lifetime
  - 위반 기준: Base (CWE-400 계열) — T1
  - fingerprint: `ef3b472b1c0d4574` / severity **low** / confidence **high** / disposition **informational**
  - 관측 사실:
    ```python
    411      try:
    412          with os.fdopen(fd, "rb") as f:
    413              return f.read(), None
    414      except OSError as e:
    415          return None, err("run_log_write_failed", detail=str(e))
    ```
    `os.fdopen()` **자체**가 raise하면 `with` 블록에 진입하지 못해 `fd`가 누수된다. 바로 위 fstat 블록은 `os.close(fd)`를 정확히 수행하므로 이 한 경로만 비대칭이다.
  - 설명: **이번 수정이 만든 문제가 아니다**(fdopen 경로는 이전부터 동일). `os.fdopen` 실패는 메모리 고갈 등 극히 드문 조건에서만 발생하고, CLI는 단발 프로세스라 종료 시 OS가 회수한다. §2.6 인프로세스 장기 호출자에서만 이론적으로 누적된다. **blocking도 advisory도 아니다.**
  - 해결 방안: `try/except`를 `fd` 확보 직후로 넓혀 `except` 블록에서 `os.close(fd)`를 수행하거나, fstat 블록과 fdopen을 하나의 `try ... finally`로 묶는다. GC-214 시나리오 추가 시 같은 단위로 처리하면 비용이 0에 가깝다.
  - 자동 수정: N
  - 검증: fdopen 실패 주입은 real-usage로 재현이 어렵다 — 코드 검토로 `fd` 소유권이 모든 분기에서 이전·해제됨을 확인하는 것으로 족하다.

- [ ] **GC-216** [`opal/tools/run-log-tool/run_log_core.py`:6] `@header.description`과 `_all_oppl_candidates()` docstring이 **현재 방어를 과소 기술**한다
  - 카테고리: CWE-1059 Insufficient Documentation (보안 제어 기술 불일치)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` @header 규칙 — 현재 사실로 제자리 교체) — T0
  - fingerprint: `303c20499b71cd89` / severity **low** / confidence **high** / disposition **informational**
  - 관측 사실: 두 곳이 방어를 `O_NOFOLLOW`까지만 기술하고, 이번에 추가된 `os.fstat` 게이트(`S_ISREG`·`st_nlink`)와 `O_NONBLOCK`을 언급하지 않는다.
    - `:6` `@header.description` — "가져오기 원본 읽기는 조각 경로와 동일한 **심볼릭 링크**·경계 이탈 방어(`_reject_symlink_or_escape`·`_safe_read_bytes`, **O_NOFOLLOW**)를 거치고"
    - `:1353` `_all_oppl_candidates()` docstring — "`_safe_read_bytes()`(**O_NOFOLLOW**)로 읽는다(GC-201/202 …)"
  - 설명: 함수 본문 docstring(`:377-390`)은 GC-212/213을 정확하고 상세하게 기술하고 있어 **모듈 최상단 요약만 낡았다**. 보안 영향은 간접적이다 — 다음 작업자가 `@header`만 읽고 "이 경로의 방어는 O_NOFOLLOW뿐"이라고 판단하면 GC-214가 지적한 회귀가 더 쉽게 일어난다. 컨벤션 축과 중첩되는 지적이므로 **보안 blocking으로 계상하지 않는다.**
  - 해결 방안: 두 문장을 현재 사실로 제자리 교체한다 — 예: "심볼릭 링크·하드 링크·비정규 파일·경계 이탈 방어(`_reject_symlink_or_escape`·`_safe_read_bytes`, `O_NOFOLLOW|O_NONBLOCK` + `os.fstat` `S_ISREG`·`st_nlink` 게이트)". 이력 서술이나 GC 번호 나열이 아닌 **현재 사실 서술**로 쓴다.
  - 자동 수정: N
  - 검증: `@header.description`에 하드 링크·정규 파일 판정이 언급되고, 이력 서술·태스크 번호 이력이 들어가지 않았는지 확인한다.

---

## 7. 이관·강등 항목 (이번 범위 아님 — 재지적하되 분류만)

| ID | 위치 | disposition | 상태 | 소유 |
|---|---|---|---|---|
| **GC-207** | `run_log_core.py` 가져오기 읽기 | advisory **(이관됨)** | 미조치 — 원본 크기 상한 없음(`st_size`·`MAX_*_BYTES` grep 0건). **단, `/dev/zero` 등 device 증폭 벡터는 이번 게이트로 차단됨** | **T06** |
| **GC-210** | `run_log_core.py`:1490 | advisory **(이관됨)** | 미조치 — `import_oppl()`이 `_safe_read_bytes(task_dir / p)`로 같은 파일을 **락 밖에서 재읽기**하는 구조 잔존 | **T06** |
| **GC-211** | `run_log_core.py` 디렉터리 생성 | **informational (강등 유지)** | 미조치 — 최말단·`run/`만 0700, 중간 경로 0755 (실측 재확인) | 소유자 판단 |
| GC-206 `errors="replace"` | — | **되돌리지 않음** | 합의대로 유지. 계약 명문화 권고만 접수 (§4.2 참고의 sha256 이원성 포함) | PM / 계약 |
| GC-209 `scanned` 차감 | — | **되돌리지 않음** | 합의대로 유지. `skipped_invalid` 집계 필드 추가는 계약 3자산 동시 개정 사안 | PM / T11 |

---

## 8. 문서 업데이트 제안 (재제출 2건)

- [ ] **GC-DP-303(재제출)** `docs/SECURITY.md` §1 위협 모델에 **링크 추종 전반 + fd 기준 3검사**를 규칙화
  - 근거: 같은 계열이 **4회** 반복됐다(T02 GC-101/102/103, T03 GC-201/202, T03 GC-212/213). 이번 수정으로 코드는 올바른 형태에 도달했으므로, **그 형태를 기준 문서에 고정**할 시점이다.
  - 제안 내용: "파일을 여는 모든 신규 경로는 fd 기준 3검사를 통과해야 한다 — (a) `O_NOFOLLOW|O_NONBLOCK`, (b) `os.fstat(fd)`로 `S_ISREG` 확인(FIFO·device·directory 거부), (c) `st_nlink == 1` 확인(하드 링크 거부). 경로 문자열 기준 검사(`is_symlink()`·`resolve()`)는 보조이며 단독으로는 경계를 보장하지 않는다." **GC-214와 묶어 반영하면 문서·테스트가 동시에 고정된다.**

- [ ] **GC-DP-302(재제출)** `docs/SECURITY.md` §9 "신뢰 불가 원본 파싱" 신설
  - 근거: 2회 연속 제안했고 미반영이다. 구현은 (b)(c)를 갖췄으나 기준 문서에 없어 다음 파서에서 재발 가능하다.
  - 제안 내용: "(a) 원본 파일당 바이트 상한 의무, (b) 디코딩 실패·타입 불일치·중첩 초과·달력 오류는 예외를 밖으로 던지지 않고 건너뜀/손상 집계로 흡수, (c) 파서가 잡아야 할 예외 최소 집합 `OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, OverflowError, RecursionError`, (d) 원본은 1회만 읽고 해시를 재사용, (e) 손실 허용 디코딩·부분 해시를 쓰는 경로는 `sha256`의 기준(원본 바이트 / 치환 후 텍스트 / 매칭 줄)을 계약에 명시."

---

## 9. 범위 밖 (지적 아님 — 소유 태스크에 인계)

| 관측 | 소유 |
|---|---|
| `redact()` 본문 pass-through, 원본 상한(GC-207), `sources[].sha256` 이중 읽기(GC-210), 시간대 | **T06** |
| 조각 경계·런타임 색인·조각 전량 메모리 적재 | **T04** |
| `skipped_invalid` 집계 필드, `source.sha256` 기준 명문화 | **PM / 계약 3자산** |
| 가져온 사건의 완료 게이트 불기여 **집행** | **T11** |
| 최종 조합 판정 게이트 집행 | **T08** |
| `begin-worker`·워커 token 발급·`worker_token_invalid` | 범위 밖 (미구현이 정상) |
| `opal/tools/state-tool/` 전체 | **T05** (읽지 않았다) |

---

## 10. 판정 근거

| 판정 축 | 값 |
|---|---|
| check status | `pass` (지정 범위 대상 전부 읽음, `checked_files == target_files`) |
| missing_capabilities | 없음 (`docs/SECURITY.md` 존재 → T0 기준 확보) |
| **blocking finding** | **0건** |
| advisory | 3건 (GC-214 신규, GC-207·GC-210 이관됨) |
| informational | 3건 (GC-215 신규, GC-216 신규, GC-211 강등 유지) |
| baseline delta | **resolved 2** (GC-212 blocking·GC-213 advisory) / persisting 3 (GC-207·210·211) / **new 3** (GC-214·215·216, 전부 non-blocking) |
| **최종 판정** | **PASS_WITH_ADVISORIES** |

`gc-finding-schema.md` §6: `INCOMPLETE` 조건 불성립(status pass, `missing_capabilities` 비어 있음), blocking 0건, advisory·informational만 존재 → **PASS_WITH_ADVISORIES**.

### PM 질의에 대한 직답

> **blocking 0건인지 명확히 답하라.**

**blocking 0건이다.** 직전 잔여 blocking이던 GC-212는 하드 링크 거부·적재 0건·출처 위장 소멸로 실측 폐쇄됐고, GC-213은 0.06초 봉투 반환으로 폐쇄됐다. **새로 생긴 blocking도 없다** — 신규 3건은 advisory 1건(GC-214 테스트 부재)·informational 2건(GC-215 fd 누수, GC-216 헤더 낙후)이며 어느 것도 태스크 진행을 차단하지 않는다.

> **회귀·부작용**

`st_nlink == 1` 오탐 없음(실제 산출물 전건 nlink=1, APFS clonefile도 1), `O_NONBLOCK` short read 없음(19 MB 파일 60,001번째 줄 소비 확인, 8개 크기 경계 SHA 전건 일치), resolved 8건 전건 유지, 31건 테스트 통과.

**권고**: 이 축은 통과다. 다만 **GC-214(경계 방어 회귀 테스트 S-30 추가)를 T03 마감 전에 처리할 것을 권한다** — 3회 검사에서 나온 blocking 4건이 전부 이 계열이었고, 지금 그 방어를 지키는 테스트가 하나도 없다. GC-215·GC-216은 같은 편집 단위에 얹으면 추가 비용이 거의 없다.
