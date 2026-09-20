# GC-SECURITY — T02 최종 폐쇄 확인 (3회차 / 재시도 상한)

- 검사일시: 2026-09-12 23:24 (KST)
- project_root: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_123`
- scope: `all` · element: `final`
- baseline: `gc-findings-security-2026-09-12T22-52-00.json` (2회차)
- 검사 상태: `pass` · missing_capabilities: 없음
- **최종 판정: PASS_WITH_ADVISORIES** (blocking 0건, advisory 4건, informational 2건)

## 0. 적용 기준

| 순서 | 기준 | tier | 적용 |
|---|---|---|---|
| 1 | `docs/SECURITY.md` §1 위협모델 / §2 install 무결성 / §3 MCP 신뢰경계 | T0 | 적용 |
| 2 | 실행 설정 — `opal/tools/state-tool/tests/` (428 passed·3 skipped), `test_state_tool_run_log.py` (3 passed) | T0 | 적용 |
| 3 | OWASP Top 10 (2021) A01/A05, CWE Top 25 (CWE-59·CWE-367·CWE-377·CWE-732·CWE-775) | T1 | 적용 |

검사 대상(`checked_files`)은 `target_files`와 일치한다.

- `opal/tools/state-tool/state_tool.py`
- `opal/tools/run-log-tool/run_log_core.py`
- `opal/tools/run-log-tool/run_log_tool.py`

---

## 1. 6건 재판정 — 전건 실측

보고서를 근거로 쓰지 않고 전건을 직접 실행해 재현 시도했다. 아래 명령·출력은 이번 회차에서 실제로 관측한 것이다.

### GC-101 — tmp 링크 선점 → **닫힘**

`_atomic_write_state_json()`이 `tempfile.mkstemp(prefix=..., dir=...)`로 교체됐다.

실측: `state.json.tmp.1` ~ `state.json.tmp.5000` + `state.json.tmp.$$` 전량을 victim 심볼릭 링크로 선점한 뒤 `init --run-log-mode shadow` 실행.

```
init exit=0
victim content: VICTIM-ORIGINAL-CONTENT   ← 불변
victim perms:  -rw-r--r--                 ← 불변
state.json perms: -rw-------
leftover tmp files: 5001                  ← 전부 내가 심은 링크. 도구가 남긴 tmp 0건
```

이름 선점이 통하지 않는다. `mkstemp`는 62진 8자 난수 이름을 `O_CREAT|O_EXCL`로 배타 생성하며, 충돌해도 실패가 아니라 재추첨이다. 2회차 재현 경로가 소멸했다.

### GC-102 — 락 링크 선점 → **닫힘**

`_acquire_lock()`에 `O_NOFOLLOW` 추가 + `os.chmod(path)` → `os.fchmod(fd)` 교체.

실측: `.opal-task.lock`을 644 victim 심볼릭 링크로 선점.

```
{"ok": false, "command": "init", "error": "task_lock_timeout", ...}
elapsed=30s                                  ← DEFAULT_LOCK_TIMEOUT_MS=30000 상한 준수
victim perms: -rw-r--r--  content: VICTIM-LOCK  ← 권한·내용 모두 불변
```

권한 변경 부작용이 사라졌고, flock이 공격자 지정 inode에 걸리는 D-4 무력화도 성립하지 않는다(open 자체가 거부되므로 fd가 만들어지지 않는다). 재시도 루프는 무한 대기하지 않고 상한에서 종료하며, 실패 분기에서 fd를 만들지 않으므로 자원 누수도 없다.

### GC-103 — `run/` 디렉터리 링크 → **부분** (정적 케이스 닫힘 · TOCTOU 잔존)

정적 링크 선점은 3개 진입점 전부에서 거부된다.

```
init:         error[run_log_write_failed] "run/이 심볼릭 링크입니다(거부)"
append:       error[run_log_write_failed] "run/이 심볼릭 링크입니다(거부)"
validate_run: error[run_log_missing]      ← 2회차의 위조 "pass" 오판정 소멸
outside dir perms: drwxr-xr-x (불변) · files written outside: 0
```

`run/`이 정규 파일인 경우도 `[Errno 20] Not a directory`로 거부된다.

다만 **경합 창은 남아 있다**(→ GC-202). `_ensure_run_dir()`는 검사·`fchmod` 후 디렉터리 fd를 닫고 **경로만** 반환하며, 호출자는 그 경로로 조각을 다시 연다. `O_NOFOLLOW`는 최종 구성요소만 보호하고 `run/` 부모 구성요소는 보호하지 않는다.

### GC-001 계열 (baseline `GC-104`, fp `8d5a7c93d865a105`) — **닫힘**

baseline이 정한 폐쇄 조건은 "`save_state_json()` 경로에서도 `redact()` 호출이 계수되면 닫힘"이다. `redact`를 계수 래퍼로 감싼 하네스로 실측:

```
A: run_log.pending_events 보유 → save_state_json redact 호출: ['E1']   ← 초크포인트 통과
B: run_log 키 없음            → 기록 코어 import 안 함 · redact 0회
C: pending_events == []       → 기록 코어 import 안 함
```

B·C가 **S-2 바이트 동일성(C-3) 보전**의 근거다. 미지정 경로 실측도 일치한다 — `run_log` 키 부재, `schema_version: 1.0`, 락 파일·`run/` 미생성, state.json 644 유지. 조건부 분기가 S-2를 파손하지 않았다.

### GC-004 계열 (baseline `GC-105`, fp `39dfca4da12a43d9`) — **닫힘**

baseline 폐쇄 조건은 "pending_events 보유 상태의 state.json 권한이 0600"이다.

```
run-log 경로:  state.json 0600 · .opal-task.lock 0600 · run/ 0700 · 조각 0600
미지정 경로:   state.json 0644 · run_log 키 부재 (기존 동작 그대로)
```

`mkstemp`가 0600으로 만든 inode를 `os.replace`가 그대로 옮기므로 보관함과 조각의 권한 경계가 일치한다.

### GC-005 계열 (락·디렉터리 링크 추종) — **닫힘**

GC-102·GC-103 실측으로 폐쇄. 보조 확인으로 GC-003(run_id 화이트리스트)과 경로 계약이 함께 살아 있음을 확인했다.

```
../../etc/x · * · run_a/../../b · run_$(id) · run_;id  → 전건 run_id_invalid
./rel                                                  → task_path_not_absolute
init 없이 append                                       → run_log_missing (O_CREAT 미부여 확인)
```

### 재판정 요약

| 항목 | 판정 |
|---|---|
| GC-101 tmp 링크 선점 | **닫힘** |
| GC-102 락 링크 선점 | **닫힘** |
| GC-103 `run/` 링크 | **부분** — 정적 닫힘, TOCTOU 잔존 (GC-202) |
| GC-001 redact 초크포인트 | **닫힘** |
| GC-004 state.json 권한 | **닫힘** |
| GC-005 링크 추종 | **닫힘** |

---

## 2. 이번 수정이 새 취약점을 만들었는가

지시받은 4개 의심 지점을 각각 겨냥해 확인했다. **이번 수정이 도입한 신규 취약점은 없다.**

| 의심 지점 | 결과 |
|---|---|
| `mkstemp` 권한·정리 누락 | 없음. 생성 mode 0600, 예외 경로에서 `unlink`, 정상 경로에서 tmp 잔존 0건 |
| `O_NOFOLLOW` 재시도 루프 무한 대기·자원 누수 | 없음. 30s 상한 실측, 실패 분기에서 fd 미생성 |
| `_ensure_run_dir` TOCTOU 잔존 | **잔존함** — 단, 신규 도입이 아니라 GC-103 수정이 덜 닫은 잔여분 (GC-202) |
| `save_state_json` 조건부 분기의 S-2 파손 | 없음. import·분기 모두 `run_log` 보유 시에만 발생, 미지정 경로 바이트 동일 |

회귀 확인: state-tool 전체 스위트 **428 passed, 3 skipped, 111 subtests passed**, run-log 스위트 **3 passed**. 실패 0건.

3회 연속 "수정이 새 취약점을 도입"하던 이력은 이번 회차에서 끊겼다. 아래 신규 findings는 전부 **수정이 만든 것이 아니라 같은 계열에서 원래 덜 닫혀 있던 잔여분**이다.

---

## 3. 신규 findings

### GC-201 — 조각 파일 하드링크 선점으로 임의 파일에 append (medium / confidence high / advisory)

- 위치: `opal/tools/run-log-tool/run_log_core.py:407` (`init`), `:478` (`append`)
- rule_id: `CWE-59` · source_tier `T1`
- fingerprint: `f8f8f81afb261e45`

`O_CREAT|O_EXCL|O_NOFOLLOW`는 **심볼릭 링크만** 막는다. 하드링크는 심볼릭 링크가 아니므로 `O_NOFOLLOW`가 관여하지 않고, 파일이 이미 존재하므로 `O_EXCL`은 `init`을 멱등 분기(`created: false`)로 보낼 뿐 거부하지 않는다. 이어지는 `append`는 `O_CREAT` 없이 그 inode를 열어 그대로 쓴다.

실측 (macOS, 같은 파일시스템):

```
ln /tmp/gc3/victim_hl2  ehl2/run/run-log-run_2222...-0001.jsonl   ← 하드링크 선점
init   → ok  {"created": false}
append → ok  {"sequence": 2, ...}

victim_hl2 AFTER:
  {"sequence":1,"note":"victim audit log"}          ← 원본 줄
  {"run_id": "run_2222...", "event": "run.started"} ← 관통해 들어간 사건
victim perms: -rw-r--r-- 2 links
```

첫 시도에서 victim이 JSON으로 파싱되지 않으면 GC-006의 `malformed_line` 가드가 append를 우발적으로 막는다. 그러나 그것은 부수 효과이지 방어가 아니다 — victim이 JSONL·NDJSON이면 위와 같이 관통한다.

- 영향: 공격자가 하드링크를 걸 수 있는 임의 파일에 **append-only** 오염. 기존 내용 덮어쓰기·읽기는 불가. 감사 로그·추가 줄을 허용하는 설정 파일이 표적이 된다.
- 완화 현황: Linux는 `fs.protected_hardlinks=1`(대부분 배포판 기본값)이 비소유 파일 하드링크를 차단한다. **macOS는 동등 보호가 없고, 위 재현은 macOS에서 성립했다.**
- disposition을 `advisory`로 두는 근거: `docs/SECURITY.md` §1 위협모델 표가 이 공격자 모델(태스크 디렉터리 로컬 쓰기 권한)을 선언하지 않는다(→ GC-204). T1 기준만으로 blocking 승격하지 않는다는 schema §5 규칙을 따른다.
- remediation: 조각 open 직후 `os.fstat(fd).st_nlink != 1`이면 닫고 거부한다. `init`·`append` 양쪽에 동일 적용. 약 3줄.
- verification: 위 재현 절차에서 `append`가 봉투 오류로 거부되고 victim이 불변이면 닫힘.

### GC-202 — `_ensure_run_dir` 검사가 open까지 이어지지 않는 TOCTOU (medium / confidence high / advisory)

- 위치: `opal/tools/run-log-tool/run_log_core.py:166` (dirfd 획득·즉시 폐기), 소비처 `:399`·`:452`·`:190`
- rule_id: `CWE-367` · source_tier `T1`
- fingerprint: `4b9686abe3539353`

`_ensure_run_dir()`는 `os.open(run_dir, O_DIRECTORY|O_NOFOLLOW)`로 올바른 fd를 얻어 `fchmod`까지 안전하게 수행한 뒤 **그 fd를 닫고 경로만 반환한다**. 호출자는 경로로 조각을 다시 열며, `O_NOFOLLOW`는 최종 구성요소만 보호하므로 `run/` 부모가 그 사이 링크로 바뀌면 막지 못한다. `append()`의 `run_dir.is_symlink()` 재검사, `_resolved_segments()`의 검사도 같은 이유로 검사와 사용이 분리돼 있다.

경합 성립을 결정론적으로 재현했다(검사 직후 `run/`을 링크로 치환하는 하네스):

```
init result: {'ok': True, ..., 'created': True}
segment landed OUTSIDE task dir: ['run-log-run_toctou-test-0001-0001.jsonl']
outside dir mode now: 0o755          ← 권한 변경 부작용은 없음 (fchmod가 검증된 fd에만 적용됨)
```

- 영향: 실행 로그 조각이 태스크 경계 밖에 기록된다. GC-103이 막은 **권한 변경 부작용은 재현되지 않으며**, 남은 것은 기록 위치 이탈뿐이다.
- 착취 난도: 공격자가 좁은 창을 실제로 이겨야 한다. 위 재현은 창을 인위적으로 벌린 것이므로 **구조적 간극 존재는 confidence high, 실전 착취 가능성은 경합 의존**이다.
- remediation: `_ensure_run_dir()`가 dirfd를 닫지 말고 반환하고, 조각 open을 `os.open(basename, flags, dir_fd=dirfd)`(openat 상대 열기)로 바꾼다. 부모 구성요소 치환이 원천 무효가 되며 `_resolved_segments()`도 같은 fd 기준으로 통일할 수 있다.
- verification: 위 하네스로 `run/`을 치환해도 조각이 태스크 경계 밖에 생기지 않으면 닫힘.

### GC-203 — outbox `status: pending` 반제 커밋 미회수 (low / confidence high / advisory)

- 위치: `opal/tools/state-tool/state_tool.py:1554`~`1574`
- rule_id: `OWASP-A05` · source_tier `T1`
- fingerprint: `3cc863bf3e4ac7a3`

1차 원자 쓰기(`status: pending` + 보관함 적재) 성공 후 락 획득이 실패하면 `err()`가 프로세스를 종료하고, state.json은 `pending` + `pending_events` 1건 상태로 **영구히 남는다**. `status == "pending"`을 회수·조정하는 코드가 없다(전수 grep 결과 해당 분기 부재).

GC-102 실측에서 그대로 관측됐다.

```
(락 심볼릭 링크 선점 → task_lock_timeout 후)
status: pending | pending_events: 1 | active_run_id: run_0e733c21-...
run/ segments: 0

(링크 제거 후 재시도)
{"ok": false, "error": "already_initialized", "message": "state.json이 이미 존재합니다. --force로 덮어쓰기 가능"}
status: pending | pending_events: 1     ← 여전히 반제 상태, --force 외 복구 경로 없음
```

- 영향: 가용성. 태스크 디렉터리에 쓸 수 있는 로컬 공격자가 락 경로에 링크 하나를 심어 해당 태스크의 run-log 초기화를 영구 차단할 수 있고, 정상 사용자도 프로세스 중단·디스크 오류로 같은 상태에 빠진다. 보관함의 사건이 조각으로 넘어가지 못한 채 남으므로 T06 마스킹 적용 후에는 마스킹 이력 판단도 흐려진다.
- disposition `advisory`: T02는 워킹 스켈레톤이고 outbox 회수는 2단 커밋 설계를 완성하는 후속 작업 성격이다.
- remediation: `init`/후속 명령 진입 시 `run_log.status == "pending"`이면 보관함 사건을 조각으로 재적재하고 `active`로 승격하는 회수 절차를 둔다(`redact()` 멱등 계약이 이 재적재를 이미 안전하게 만든다).
- verification: 락 선점으로 pending을 만든 뒤 선점을 풀고 재실행했을 때 `status: active` + 조각 1건으로 수렴하면 닫힘.

### GC-204 — `docs/SECURITY.md` 위협모델이 이번 3회차가 방어한 표면을 선언하지 않음 (info / confidence high / advisory)

- 위치: `docs/SECURITY.md:13`~`22` (§1 위협 모델)
- rule_id: `SECURITY.md §1` · source_tier `T0`
- fingerprint: `f23b0c72fefdccf1`

§1 위협 표면 표는 curl-pipe-bash 신뢰 모델 / fork 가능성 / third-party skill supply chain / MCP spawn 4항목이며, **"태스크 디렉터리에 쓰기 권한을 가진 로컬 공격자"를 선언하지 않는다.** 채택 표준 목록에도 `CWE-377`은 있으나 `CWE-59`(Link Following)·`CWE-367`(TOCTOU)이 없다.

GC-101·102·103과 위 GC-201·202는 전부 선언되지 않은 그 공격자 모델을 전제로 제기·수정됐다. schema §5 "T0과 T1이 충돌하면 T0이 우선하며 임의 병합 없이 충돌 위치를 별도 finding으로 남긴다"에 따라 별건으로 기록한다.

이 불일치가 **이번 회차 판정에 직접 작용한다**: 같은 계열인 GC-201·202를 blocking으로 승격할 T0 근거가 없다. 반대로 §1에 이 표면을 추가하면 GC-201·202는 즉시 blocking으로 재평가되어야 한다.

- remediation: §1 표에 로컬 태스크 디렉터리 파일 경합 표면을 추가하고 채택 CWE에 `CWE-59`·`CWE-367`을 넣거나, 반대로 "태스크 디렉터리는 소유자 단독 신뢰 경계"를 명시해 해당 계열을 범위 밖으로 확정한다. **둘 중 무엇을 택하든 소유자 결정 사항이며 이 검사는 문서를 수정하지 않는다**(스킬 §7-3, role 계약 §4).
- verification: §1이 이 표면에 대해 포함/제외 중 하나를 명시하면 닫힘.

### GC-205 — 락 open의 전 `OSError` 일괄 재시도로 오류 코드가 오도됨 (info / confidence high / informational)

- 위치: `opal/tools/run-log-tool/run_log_core.py:269`
- rule_id: `CWE-755` · source_tier `T1` · fingerprint: `d786f73e10f62004`

`except OSError`가 링크 선점(ELOOP)뿐 아니라 `EACCES`·`ENOTDIR`·`ENOSPC` 같은 **복구 불가 오류까지** 같은 재시도 루프에 넣는다. 영구 실패에서도 30초를 소진한 뒤 `task_lock_timeout`으로 보고되어, 운영자가 원인을 경합으로 오인한다. 보안 영향은 없고 진단 품질 문제다.

- remediation: `ELOOP`·`EEXIST` 계열만 재시도하고 나머지는 즉시 원인 코드로 반환한다.

### GC-206 — `os.fdopen` 실패 시 fd 누수 (info / confidence medium / informational)

- 위치: `opal/tools/state-tool/state_tool.py:478`~`493`
- rule_id: `CWE-775` · source_tier `T1` · fingerprint: `418de370d1cff269`

`mkstemp`가 돌려준 fd가 `os.fdopen()` 자체에서 예외를 만나면 소유권이 파일 객체로 넘어가지 않아 닫히지 않는다(`except Exception`은 tmp 파일만 `unlink`한다). state-tool은 단명 CLI이므로 실 영향은 사실상 없다. 인프로세스 반복 호출자가 생기면 재평가한다.

- remediation: `fd`를 `try` 안에서 획득하거나 실패 시 `os.close(fd)`를 명시한다.

---

## 4. baseline delta

비교 키는 `fingerprint`다.

| 분류 | 건수 | 항목 |
|---|---|---|
| `resolved` | 5 | `4543d40c10ff0144`(GC-101) · `e667b7a77d7de42a`(GC-102) · `8d5a7c93d865a105`(GC-001 계열) · `39dfca4da12a43d9`(GC-004 계열) · GC-005 계열 |
| `persisting` | 1 | `39498958fe1c059d`(GC-103) — 정적 케이스는 닫혔고 잔여 경합이 GC-202로 승계됨 |
| `new` | 6 | GC-201 · GC-202 · GC-203 · GC-204 · GC-205 · GC-206 |
| `suppressed` | 0 | — |

`resolved` 5건은 모두 이번 `checked_files`에 포함된 파일에서 판정했으므로 schema §7의 유효 조건을 만족한다.

---

## 5. 잔존 위험 3분류 — 인계

재시도 상한 도달로 이 분류가 그대로 인계 문서가 된다.

### (A) T02에서 닫아야 할 것

**없음.** 재판정 6건 중 blocking으로 남은 항목이 0건이고, 신규 findings 중 T0 근거로 blocking에 해당하는 항목도 없다(GC-204가 그 근거 부재를 설명한다). T02는 보안 사유로 차단되지 않는다.

다만 **GC-201은 상한이 없었다면 T02에서 닫았을 항목**이다. 수정이 `os.fstat(fd).st_nlink != 1` 검사 3줄이고, 이미 손대고 있는 두 함수 안에서 끝나며, GC-101~103과 정확히 같은 계열의 마지막 구멍이다. 상한 도달로 (B)로 넘기되, **비용 대비 가치가 이 목록에서 가장 높다**는 점을 명시한다.

### (B) 후속 태스크가 완성할 것

| 항목 | 인계처 | 근거 |
|---|---|---|
| GC-201 하드링크 선점 | 링크 방어 계열 후속 (T04 조각 회전 시 조각 open 경로를 다시 만짐 — 그때 함께) | 같은 계열 마지막 구멍, 수정 3줄 |
| GC-202 openat 기반 경로 고정 | 동상 | `_ensure_run_dir` dirfd 반환 + `dir_fd=` 전환. GC-201과 같은 함수라 **한 번에 처리하는 것이 옳다** |
| GC-203 outbox pending 회수 | T03 (사건 계약·멱등 판정 소관) | 2단 커밋 설계 완성분. `redact()` 멱등이 이미 재적재를 안전하게 만들어 둠 |
| GC-204 위협모델 선언 | 소유자 결정 후 문서 갱신 | 이 결정이 GC-201·202의 집행 수준을 좌우하므로 **(B) 중 선행 항목** |
| GC-205 오류 코드 세분화 | 진단 품질 개선 시 | 보안 영향 없음 |

### (C) 수용 가능한 잔여 위험

| 항목 | 수용 근거 |
|---|---|
| GC-206 fd 누수 | 단명 CLI. 인프로세스 반복 호출자 등장 시에만 재평가 |
| 락 링크 선점에 의한 30초 지연 자체 | 상한이 집행되고 victim 무결성이 보전된다. 가용성 영향은 GC-203 쪽에 귀속 |
| 미지정 경로 state.json 644 | S-2 바이트 동일성(C-3) 보전을 위한 **의도된 계약**. run-log 경로만 0600으로 좁히는 현 설계가 맞다 |
| `redact()` pass-through | T02 명시 범위. T06이 본문을 채운다. 초크포인트 배선은 이번에 닫혔으므로 T06은 본문만 채우면 된다 |
| `_run_log_core_dir()`의 `~` 확장 | `HOME` 통제는 이미 전면 침해 상황이고, 배포·레포 양쪽에서 형제 경로가 우선한다 |

---

## 6. 최종 판정

**PASS_WITH_ADVISORIES**

- 검사 `status`: `pass` — `checked_files` == `target_files`
- `missing_capabilities`: 없음
- `disposition: blocking`: **0건**
- advisory 4건 (GC-201·202·203·204), informational 2건 (GC-205·206)

schema §6에 따라 advisory·informational은 차단 사유로 계산하지 않는다. T02는 **보안 사유로 차단되지 않는다.**

판정에 붙는 유일한 조건은 GC-204다 — `docs/SECURITY.md` §1이 로컬 태스크 디렉터리 경합을 위협 표면으로 채택하면, GC-201·GC-202는 T0 근거를 얻어 blocking으로 재평가되어야 하며 이 PASS는 그 시점에 무효가 된다. 소유자가 §1을 갱신할지 먼저 결정할 것을 권한다.

---

## 부록 — 기준 문서 결측 안내

`docs/SECURITY.md`는 존재하며 T0 기준으로 적용됐다. 초안 생성 유도 대상이 아니다. §1 범위 공백은 GC-204로 기록했으며, 이 검사는 기준 문서를 자동 생성·갱신하지 않는다.
