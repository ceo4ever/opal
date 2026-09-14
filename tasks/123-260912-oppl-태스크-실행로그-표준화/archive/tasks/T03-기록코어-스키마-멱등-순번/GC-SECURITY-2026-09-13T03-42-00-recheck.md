# GC SECURITY REPORT (RECHECK) — 2026-09-13T03-42-00

> T03 기록코어(스키마·멱등·순번) 보안 **재검사** / oppl 태스크 파이프라인 T4b 규칙검사 축
> 직전 검사: `GC-SECURITY-2026-09-13T02-58-00.md` (판정 FAIL, blocking 7건)
> 자기완결 보고서 — 이 문서만으로 모든 판정의 재현이 가능하다.

## 1. 헤더

- 실행 일시: 시작 2026-09-13 03:35 / 완료 2026-09-13 03:42 / 소요 약 7분
- 범위: 지정 `target_files` 3개 (호출자 확정 목록 그대로, 재선별 없음)
- 에이전트: opal-security-checker (read-only 진단 전담 — 소스 미수정)
- APPLY 수행 여부: **N** (보고만)
- 판정: **FAIL** — `disposition: blocking` **1건** (GC-212)

### 검사 대상

| # | 파일 | 행수 | 읽음 |
|---|---|---|---|
| 1 | `opal/tools/run-log-tool/run_log_core.py` | 1,467 | 전문 |
| 2 | `opal/tools/run-log-tool/run_log_tool.py` | 190 | 전문 |
| 3 | `opal/tools/run-log-tool/tests/test_run_log_tool.py` | 1,626 | 관례·충실도 확인 범위 |

### 적용 기준

| 순위 | 기준 | tier |
|---|---|---|
| 1 | `docs/SECURITY.md` §1 위협 모델 — CWE-22 / CWE-377 / CWE-829 / CWE-1333, §6 path 정규화 | T0 |
| 2 | `docs/run-log/CONTRACT.md` §1.1·§1.1.1·§1.1.2·§1.1.3 (폐쇄형 스키마·token 원문 금지) | T0 |
| 3 | OWASP Top 10 (2021) A01/A03/A05 · CWE Top 25 (CWE-20/59/61/400/522/732/754) | T1 |

### 검사 방법 (required_fidelity = real-usage)

전건 **`bash opal/tools/run-log-tool/run.sh <subcmd>` 실제 subprocess 실행 + 디스크 조각 파일 검사**, 또는 §2.6 인프로세스 호출 실행으로 확인했다. mock·patch·스텁·가짜 파일시스템을 쓰지 않았다. 구현 워커의 처리 보고를 신뢰하지 않고 10건 전건을 직접 재현했다.

---

## 2. 한 줄 결론

**blocking 0건이 아니다 — blocking 1건이다.** 직전 blocking 7건 중 **6건(GC-201·202·203·204·205·206)이 실측으로 닫혔고**, GC-207만 T06 이관으로 남았다. 재작업은 기존 방어를 약화시키지 않았고 정상 입력도 막지 않는다(31 tests passed, 정상 가져오기·멱등 재실행 실측 확인). 다만 신설 공용 헬퍼 `_reject_symlink_or_escape()`/`_safe_read_bytes()`가 **심볼릭 링크만** 막고 **하드 링크와 비정규 파일(FIFO)을 막지 않아**, GC-202가 지적한 "태스크 경계 밖 내용이 내부 출처로 위장돼 적재된다"가 **하드 링크로 그대로 재현된다**(GC-212, 실측). 두 신규 지적은 `_safe_read_bytes()` 한 곳의 `os.fstat()` 게이트로 함께 닫힌다.

---

## 3. 직전 지적 10건 처리 검증 (실측)

| ID | 주장 | 실측 결과 | 판정 |
|---|---|---|---|
| GC-201 | import-agentic 링크 거부 이식 | `run_log_write_failed` 거부, 조각 적재 0건 | **resolved** |
| GC-202 | `.oppl-run/` + 하위 4종 각각 방어 | 디렉터리 링크·하위 4종 개별 링크 전부 거부, `sources: []` | **resolved** |
| GC-203 | `ValueError`/`OverflowError` 포획 | 봉투 반환(exit 0), 불량 행만 제외 | **resolved** |
| GC-204 | 비-object JSON `isinstance` 검사 | 봉투 반환, `scanned: 0` | **resolved** |
| GC-205 | `RecursionError` 3지점 포획 | 가져오기·조각 양쪽 봉투 반환 | **resolved** |
| GC-206 | `errors="replace"` 전환 | 봉투 반환 — **의견 §5-1 참조** | **resolved (의견 동반)** |
| GC-207 | (T06 이관) | 미조치 — 64 MiB 원본에 RSS 225 MB | **이관됨(advisory)** |
| GC-208 | 중첩 키 4집합 폐쇄 | 4집합 전부 `schema_invalid` 거부, §1.1.1·§1.1.2 표와 **정확히 일치** | **resolved** |
| GC-209 | 거대 행만 건너뛰고 배치 계속 | 배치 계속·재실행 멱등 — **의견 §5-2 참조** | **resolved (의견 동반)** |
| GC-210 | (T06 이관) | 미조치 — `import_oppl():1460` 재읽기 잔존 | **이관됨(advisory)** |
| GC-211 | `mkdir(mode=0o700)` | **최말단만 0700, 중간 경로는 0755** | **부분 조치(informational)** |

### 3.1 재현 명령 (그대로 복사 실행 가능)

```bash
cd /Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_123
R() { bash opal/tools/run-log-tool/run.sh "$@"; }

# GC-201 — 심볼릭 링크 거부
mkdir -p /tmp/rc/v6/out /tmp/rc/v6/t
printf '## 대행 일지\n\n| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n|---|---|---|---|---|---|\n| 1 | 2026-09-13 01:00 | PLAN | DECISION | SECRET-OUTSIDE | ok |\n' > /tmp/rc/v6/out/secret.md
R init --task /tmp/rc/v6/t --run-id run_v6 --format json
ln -s /tmp/rc/v6/out/secret.md /tmp/rc/v6/t/AGENTIC-LOG.md
R import-agentic --task /tmp/rc/v6/t --run-id run_v6 --format json
# → {"ok": false, "error": {"code": "run_log_write_failed", "message": "... 심볼릭 링크입니다(거부)"}}
grep -c SECRET-OUTSIDE /tmp/rc/v6/t/run/*.jsonl   # → 0

# GC-202 — .oppl-run/ 디렉터리 링크 + 하위 4종 개별 링크
# (journal.md / *.result.json / *.events.jsonl / *.exitcode 전부 링크로 심음)
# → {"ok": true, "data": {"scanned": 0, "imported": 0, "skipped_idempotent": 0, "sources": []}}
# → LEAK-RESULT|LEAK-JOURNAL|LEAK-EVENTS grep 전부 0

# GC-203/204/205/206 — 신뢰 불가 원본 4종
# 2026-13-45 99:99 행     → {"ok": true, "scanned": 1, "imported": 1}  (정상 행만 적재)
# [1,2,3] result.json     → {"ok": true, "scanned": 0}
# '['*200000 중첩         → {"ok": true, "scanned": 0}  (가져오기)
#                         → validate-run은 malformed_line 위반으로 보고 (조각 경로)
# b'\xff\xfe bad'         → {"ok": true, "scanned": 0}  (AGENTIC-LOG.md·journal.md 양쪽)
# 전건 exit=0, 스택 트레이스 0건
```

**GC-208 재현(§2.6 인프로세스, PM 디스패치가 지정한 token 원문 적재 입력):**

```python
ev = {"event":"activity","request_id":"r1","worker_run_id":"wr_1",
      "actor":{"kind":"worker","id":"w1"}, "summary":"hello",
      "provenance":{"type":"direct","recorded_by":{"kind":"worker","id":"w1"},
                    "worker_log_token_id":"wlt_abc",
                    "worker_log_token":"SUPER-SECRET-RAW",
                    "source":{"kind":"worker_event"}}}
run_log_core.append('/tmp/rc/gt','run_gt',ev)
# → schema_invalid: "provenance에 정의되지 않은 키: ['worker_log_token']"
# actor / provenance.recorded_by / provenance.source 에 임의 키를 심어도 각각 거부됨
# 조각의 'SUPER-SECRET-RAW' 출현 횟수: 0
```

**허용 키 집합 대조 (누락·과잉 없음):**

| 집합 | 구현 (`run_log_core.py`:117-122) | CONTRACT | 일치 |
|---|---|---|---|
| `actor` | kind, id, provider, session_id | §1.1.1 4행 | ✅ |
| `provenance` | type, recorded_by, worker_log_token_id, source | §1.1.2 (type / recorded_by.* / worker_log_token_id / source.*) | ✅ |
| `recorded_by` | kind, id | §1.1.2 `recorded_by.kind`·`.id` | ✅ |
| `source` | kind, id, sha256, observed_at, locator, upstream_event_id | §1.1.2 `source.*` 6행 | ✅ |

`data`는 폐쇄하지 않았다 — §1.2가 사건별 자유 payload로 정의하므로 **올바른 선택**이다(과잉 폐쇄 아님).

**PM 판정① `actor_sequence` 범위 (MV-10) 실측:**

```
worker_run_id=wr_A  request=a1  →  sequence 2  actor_sequence 1
worker_run_id=wr_A  request=a2  →  sequence 3  actor_sequence 2
worker_run_id=wr_B  request=b1  →  sequence 4  actor_sequence 1   ← 같은 actor.id, 1부터 재시작
```

판정①대로 집행된다.

---

## 4. 신규 지적 (2건)

### Blocking (1건)

- [ ] **GC-212** [`opal/tools/run-log-tool/run_log_core.py`:347] 경계 검사가 **하드 링크**를 막지 못해, 태스크 밖 파일 내용이 태스크 내부 출처로 위장돼 적재된다
  - 카테고리: CWE-59 Link Following / CWE-61 UNIX Symbolic Link (Symlink) Following (hard link 변종) / CWE-22
  - 위반 기준: 프로젝트(`SECURITY.md` §1 CWE-22, §6 path 정규화) — T0
  - fingerprint: `06cf099492c97a47` / severity **high** / confidence **high** / disposition **blocking**
  - 관측 사실: `_reject_symlink_or_escape()`가 쓰는 두 검사 모두 하드 링크를 통과시킨다.
    ```python
    356  path = pathlib.Path(path)
    357  if path.is_symlink():            # ← 하드 링크는 심볼릭 링크가 아니다 → False
    ...
    361      resolved_task_dir = pathlib.Path(task_dir).resolve()
    362      path.resolve().relative_to(resolved_task_dir)   # ← 하드 링크는 traversal이 없다 → 항상 성공
    ```
    `_safe_read_bytes()`(:369-385)의 `O_NOFOLLOW`도 심볼릭 링크만 막는다 — 하드 링크는 그 자체가 정규 파일이므로 열린다. **경계 이탈 방어가 파일 종류 검사를 갖고 있지 않다.**
  - 재현 (실측 완료 — 외부 내용 1건이 조각에 적재됨):
    ```bash
    mkdir -p /tmp/rc/h1/t /tmp/rc/h1/out
    bash opal/tools/run-log-tool/run.sh init --task /tmp/rc/h1/t --run-id run_h1 --format json
    printf '## 대행 일지\n\n| # | 시점 | 단계 | 카테고리 | 내용 | 결과 |\n|---|---|---|---|---|---|\n| 1 | 2026-09-13 01:00 | PLAN | DECISION | HARDLINK-OUTSIDE | ok |\n' > /tmp/rc/h1/out/ext.md
    ln /tmp/rc/h1/out/ext.md /tmp/rc/h1/t/AGENTIC-LOG.md     # 심볼릭 아님 — 하드 링크
    bash opal/tools/run-log-tool/run.sh import-agentic --task /tmp/rc/h1/t --run-id run_h1 --format json
    # → {"ok": true, "data": {"scanned": 1, "imported": 1, "skipped_idempotent": 0}}
    grep -c HARDLINK-OUTSIDE /tmp/rc/h1/t/run/*.jsonl        # → 1
    ```
    적재된 사건의 출처(위장 확인):
    ```json
    {"summary": "HARDLINK-OUTSIDE",
     "source": {"kind": "legacy_line", "id": "AGENTIC-LOG.md",
                "sha256": "47310729fb...", "locator": "AGENTIC-LOG.md#L5"}}
    ```
  - 설명: GC-202가 blocking으로 지적한 것과 **영향이 동일**하다 — 태스크 경계 밖 파일의 내용이 append-only 기록에 들어가고, `source.id`·`locator`가 `AGENTIC-LOG.md`(태스크 내부)로 기록돼 사후 감사에서 외부 출처임을 알 수 없다. 이 태스크의 목적인 **출처(provenance) 검증**이 무력화된다. 심볼릭 링크만 닫고 하드 링크를 열어두면 방어를 우회하는 비용이 `ln -s` → `ln` 한 글자다. macOS에서는 소유하지 않은 파일(`-r--r----- root:wheel /etc/sudoers`)에도 하드 링크 생성이 성공함을 실측 확인했으므로, 가져오기 실행 주체가 링크 생성자보다 높은 권한(CI 러너·공유 워크트리의 타 사용자 에이전트)이면 기밀성 침해까지 확대된다. 공격 전제는 GC-201/202와 동일하다(태스크 디렉터리에 쓰기 가능한 주체) — 그 전제를 인정해 GC-201/202를 blocking으로 판정했으므로 일관되게 blocking이다. 다만 하드 링크는 **같은 파일시스템**이어야 하므로 심볼릭 링크보다 공격 범위가 좁다는 점은 명시한다.
  - 해결 방안: `_safe_read_bytes()`의 `os.open()` 직후 `os.fstat(fd)`로 **연 파일 자체**를 판정한다(경로 재검사가 아니라 fd 기준이라 TOCTOU도 함께 닫힌다).
    ```python
    st = os.fstat(fd)
    if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        os.close(fd); return None, err("run_log_write_failed", detail="정규 파일·단일 링크가 아닙니다(거부)")
    ```
    `st_nlink != 1` 거부는 GC-213(FIFO)과 같은 한 곳에서 닫힌다. 부작용 검토: git 작업본 파일·APFS clonefile은 `st_nlink == 1`이므로 정상 입력을 막지 않는다. `cp -al` 형태로 복원한 아카이브만 예외이며, 그 경우 운영자가 실체 복사로 전환해야 한다 — 이 트레이드오프는 소유자가 판단한다.
  - 자동 수정: N
  - 검증: 위 재현이 거부 봉투를 반환하고 `grep -c HARDLINK-OUTSIDE`가 0이면 해결. 동시에 §3.1의 정상 가져오기 재현(`scanned: 3, imported: 3`)이 그대로 통과해야 한다.

### Advisory (1건)

- [ ] **GC-213** [`opal/tools/run-log-tool/run_log_core.py`:369] 태스크 디렉터리의 FIFO가 가져오기 프로세스를 무한 정지시킨다
  - 카테고리: CWE-400 Uncontrolled Resource Consumption / CWE-410 Insufficient Resource Pool (가용성)
  - 위반 기준: Base (CWE-400, OWASP A05) — T1
  - fingerprint: `7091760dd43ed032` / severity **medium** / confidence **high** / disposition **advisory**
  - 관측 사실: `_safe_read_bytes()`는 파일 **종류**를 보지 않는다. FIFO는 심볼릭 링크가 아니고 경계 안에 있으므로 :357·:362 두 검사를 통과하고, `os.open(..., O_RDONLY | O_NOFOLLOW)`(:376)이 writer를 기다리며 블록한다. 타임아웃·`O_NONBLOCK`이 없다.
  - 재현 (실측 완료 — 두 가져오기 경로 모두 8초 초과 정지, 강제 kill 필요):
    ```python
    os.mkfifo(base + '/AGENTIC-LOG.md')          # import-agentic → HUNG >8s
    os.mkfifo(base + '/.oppl-run/journal.md')    # import-oppl    → HUNG >8s
    ```
  - 설명: 영향은 가용성 한정이다. **배타 락 밖에서 일어나므로**(원본 읽기·파싱은 `_run_import_batch()` 진입 전) 다른 기록 주체를 막지는 않는다 — 이 점 때문에 blocking이 아니다. 그러나 프로세스가 영원히 끝나지 않고 봉투도 내지 않으므로 자동화 파이프라인이 무한 대기한다. 참고로 **디렉터리**를 같은 이름으로 두는 경우는 정상 처리된다(`Is a directory` → `run_log_write_failed` 봉투, 실측 확인) — FIFO만 구멍이다.
  - 해결 방안: GC-212와 **같은 한 줄**(`stat.S_ISREG(st.st_mode)` 검사)로 닫힌다. 두 지적을 하나의 수정 단위로 묶는 것을 권고한다.
  - 자동 수정: N
  - 검증: 위 재현이 8초 안에 거부 봉투를 반환하면 해결.

---

## 5. 의견을 요청받은 2건

### 5-1. GC-206 `errors="replace"`가 가져오기 무결성에 허용 가능한가 — **조건부 예이지만, 지금은 사실상 무해하다**

- **현행 동작**: 비-UTF-8 바이트는 U+FFFD로 치환된다. 치환된 내용은 (a) `summary`로 적재되고 (b) **정규화 문자열의 SHA-256으로 `source.sha256`과 `request_id`에 반영된다**(`_build_legacy_event():1078`). 즉 기록되는 해시는 **원본 바이트의 해시가 아니라 치환 후 텍스트의 해시**다.
- **왜 지금은 무해한가**: `_parse_legacy_agentic_log()`는 `시점` 열이 `YYYY-MM-DD HH:mm`인 6열 행만 후보로 받는다. U+FFFD가 섞인 행은 시각 열이 깨지면 애초에 후보에서 탈락하고, 시각 열이 온전하면 나머지 열의 치환은 사람이 읽는 `summary`의 손실일 뿐이다. 실측에서도 깨진 원본은 `scanned: 0`이었다. **가져오기는 단방향이고 역변환이 금지돼 있으므로**(D-T03-11) 원문 복원 의무가 없다.
- **남는 위험 1 (충돌)**: 서로 다른 두 바이트열이 같은 U+FFFD 텍스트로 수렴하면 같은 `request_id`가 되어 두 번째 행이 **멱등 적중으로 조용히 누락**된다. 가능성은 낮지만 "가져오기 능력"의 완전성에는 흠이다.
- **남는 위험 2 (출처 정합)**: `source.sha256`이 디스크의 원본 바이트를 가리키지 않아, 운영자가 원본을 `shasum`으로 대조하면 불일치한다. `import_oppl`의 `sources[].sha256`은 원본 바이트 해시(`hashlib.sha256(raw)`)라서 **두 경로의 해시 의미가 서로 다르다**.
- **권고**: 이번 범위에서 바꾸지 않는 데 동의한다(가용성 확보가 우선이고 D-T03-11이 역변환을 금지한다). 다만 **`sha256`을 치환 후 텍스트가 아닌 원본 바이트에서 계산하도록 T06/T11 중 소유자가 정하는 시점에 정리**하고, `CONTRACT.md`에 "legacy 가져오기는 손실 허용 디코딩을 쓰며 `source.sha256`의 기준은 X다"를 명문화할 것을 권한다. 보안 지적으로 계상하지 않는다.

### 5-2. GC-209 `scanned` 차감이 원래 정의를 왜곡하는가 — **왜곡한다. 다만 보안 결함은 아니고, 대안이 더 나쁘다**

- **원래 정의**(D-T03-12): `scanned == 원본에서 인식한 사건 후보 수`, 불변식 `scanned == imported + skipped_idempotent`.
- **실측**: 3행(작은A / 21 KB 거대B / 작은C) 원본에서 `{"scanned": 2, "imported": 2}`. 배치는 이어지고 A·C 모두 적재되며 재실행도 멱등(`skipped_idempotent: 2`)이다 — **처리 자체는 올바르다.**
- **왜곡의 실체**: 거대 행 B는 **파서가 분명히 인식했고**(후보로 만들어 append까지 시도했다) 상한 때문에 거부됐다. 그런데 `scanned`에서 빼버리면 stdout 봉투는 `scanned: 2, imported: 2`로 **완전히 깨끗해 보인다**. 즉 "인식했으나 버렸다"는 사실이 **구조화된 출력에서 사라진다**. 유일한 신호가 stderr 1줄인데, 이 도구의 정상 사용 형태는 `--format json`이고 호출자는 stdout만 파싱한다 — 실측에서도 stderr 경고는 파이프에서 즉시 유실됐다.
- **구현 워커의 논거는 타당하다**: 새 집계 필드를 만들면 `surfaces.json`의 ok 응답 필드가 늘어 MV-30 3자산(surfaces·CONTRACT §2.2·§2.2.1) 동시 개정이 필요하고, 그것은 PM 소유 자산이다. 범위를 지킨 선택이다.
- **권고**: 지금 구현을 되돌리지 말 것. 대신 **소유자(PM)가 `skipped_invalid` 집계 필드 추가를 T11 또는 계약 개정 단위로 접수**하라. 그때까지는 시각 형식 불일치 행(진짜로 "인식하지 못한" 행)과 상한 초과 행(인식했으나 버린 행)이 `scanned`에서 구분 불가라는 사실을 `CONTRACT.md`에 한 줄로 남기는 것이 최소 조치다. **보안 finding으로 계상하지 않는다** — 가용성은 오히려 개선됐고(영구 차단 해소), 문제는 관측성이다.

---

## 6. 잔존·이관 항목

### 이관 확정 (이번 범위 아님 — 재지적하되 "이관됨")

- [ ] **GC-207** [`run_log_core.py`:1180] 가져오기 원본 읽기 크기 상한 부재 → **T06 소유**
  - fingerprint: `39aa904f0294805b` / severity **medium** / confidence **high** / disposition **advisory (이관됨)**
  - 실측: 64 MiB `AGENTIC-LOG.md` → `maximum resident set size 225689600` (약 225 MB). 상한 여전히 없음.
  - 완화 근거: GC-201 수정으로 `/dev/zero` 심볼릭 링크 결합 공격은 차단됐다(링크 거부). 단독 메모리 폭증만 남는다. GC-212 미조치 시 **하드 링크로 거대 파일을 끌어오는 경로는 아직 열려 있다** — GC-212를 먼저 닫으면 이 항목의 잔존 위험이 더 줄어든다.

- [ ] **GC-210** [`run_log_core.py`:1460] `sources[].sha256` 이중 읽기 TOCTOU → **T06 소유**
  - fingerprint: `94c178725d084c11` / severity **low** / confidence **high** / disposition **advisory (이관됨)**
  - 실측: `import_oppl()`이 `_all_oppl_candidates()` 파싱 후 `_safe_read_bytes(task_dir / p)`로 같은 파일을 **다시 읽는다**(:1458-1464). 재읽기는 여전히 **락 밖**이다. 개선점 1가지: 재읽기가 `_safe_read_bytes()`로 바뀌어 처리되지 않은 `OSError`가 밖으로 나가는 문제는 사라졌다(`read_err` 봉투로 흡수 → `continue`).

### 부분 조치 (informational)

- [ ] **GC-211** [`run_log_core.py`:430] 락 획득 시 디렉터리 생성 — 최말단만 0700, 중간 경로는 umask 0755
  - fingerprint: `fcb6319ed80e8963` / severity **low** / confidence **high** / disposition **informational**
  - 실측:
    ```
    drwxr-xr-x  /tmp/rc/newtree        ← 0755
    drwxr-xr-x  /tmp/rc/newtree/a      ← 0755
    drwxr-xr-x  /tmp/rc/newtree/a/b    ← 0755
    drwx------  /tmp/rc/newtree/a/b/c  ← 0700  (최말단만 적용)
    ```
    `pathlib.Path.mkdir(mode=...)`는 **최말단 디렉터리에만** 모드를 적용한다(원 보고서가 이미 지적한 제약). 또한 읽기 전용 명령(`validate_run`)이 여전히 존재하지 않는 경로 트리를 **생성한다** — 오타 난 `--task`에 빈 트리를 남기는 부작용도 그대로다.
  - 권고: 이번 범위에서 추가 조치 불필요(informational). 근본 해결은 "읽기 전용 명령은 태스크 디렉터리 부재 시 생성 대신 `run_log_missing`으로 거부"이며, 이는 계약(§2.6 호출 형태) 변경을 수반하므로 소유자 판단 사항이다.

---

## 7. 확인하고 문제없던 항목

지적으로 올리지 않았으나 명시적으로 검사해 **이상 없음**을 확인한 항목이다. (PM 디스패치가 물은 항목 6가지를 포함한다.)

1. **재작업이 정상 입력을 막지 않는다.** 정상 `import-oppl`(journal.md + PLAN.result.json + EXEC.exitcode) → `scanned: 3, imported: 3`, `sources[]` 3건 정상. 정상 `import-agentic` → `imported: 1`, 재실행 → `skipped_idempotent: 1`. 신설 헬퍼 2종과 중첩 키 폐쇄 어느 쪽도 정상 경로를 차단하지 않는다.
2. **`sources[].path`가 실제로 읽은 경로와 일치한다.** 정상 경로에서 보고된 `sha256`이 디스크 원본의 `shasum -a 256`과 일치함을 실측했다(`738770e5c0e0...`). 링크로 심은 파일은 `sources[]`에 아예 오르지 않는다(`sources: []`) — GC-202가 지적한 "외부 출처의 내부 경로 위장"은 **심볼릭 링크 한정으로** 해소됐다(하드 링크는 GC-212).
3. **`redact()` 단일 초크포인트(D-9)에 가져오기가 여전히 올라타 있다.** `import_agentic`/`import_oppl` → `_run_import_batch():1128` → `append()` → `:908 safe_event = redact(full_event)`. T06이 본문을 채우면 가져오기 경로에도 자동 적용된다. `redact()`가 현재 pass-through인 것 자체는 T06 소관이라 지적하지 않았다.
4. **비밀 유출 — `worker_log_token` 원문이 남는 경로가 이제 없다.** 코어·CLI가 `worker_log_token_id`만 취급하고(CLI는 해당 인자 자체를 노출하지 않는다), 중첩 키 폐쇄로 호출자의 오적재 경로도 닫혔다. 오류 `detail`은 키 이름·enum 값·크기 숫자 등 최소 식별 정보만 싣고 원본 본문을 복제하지 않는다 — 신설 stderr 경고(`:1142`)도 **위치자(`AGENTIC-LOG.md#L6`)만** 출력하고 행 내용을 싣지 않는다.
5. **락·TOCTOU — 이중 획득/미획득 없음.** `_run_import_batch():1157`이 `_with_lock`으로 락을 잡고 내부 `append()`에 `lock_held=True`(:1128)를 넘긴다. 신설 읽기 경로는 락 밖이지만 **쓰기는 전부 락 안**이다. `_safe_read_bytes()`의 단일 `open()` + `O_NOFOLLOW`는 존재 확인·오픈 간극을 없앤다 — 검사 후 심볼릭 링크로 교체하는 경합은 `ELOOP`로 거부된다(경로 재검사가 아닌 fd 확보).
6. **정규식 ReDoS 없음.** 모듈 정규식 5종(`RUN_ID_PATTERN`, `_SHA256_RE`, `_RFC3339_MS_RE`, `_LEGACY_TIMESTAMP_RE`, `_resolve_import_run_id`의 `^run-log-(?P<run_id>.+)-\d{4}\.jsonl$`)을 80,000자 적대적 입력으로 실측 — 전부 0.0011초 이하. 표 파싱은 정규식이 아니라 `split()` 기반이라 백트래킹 대상이 아니다.
7. **D-5 단방향 의존 유지.** `run_log_core.py`·`run_log_tool.py`에 `state_tool`·`state.json` 문자열 **0건**(grep 실측). `mode` 인자는 여전히 받기만 하고 어디서도 읽지 않는다.
8. **오류 코드 3자산(MV-30) 영향 없음.** 재작업이 새 오류 코드를 도입하지 않았다 — 기존 `run_log_write_failed`·`schema_invalid`만 재사용한다. `surfaces.json` / CONTRACT §2.2·§2.2.1 개정 불필요.
9. **테스트 real-usage 충실도 유지.** `mock|patch|MagicMock` 매치 1건은 "사용하지 않는다"는 헤더 산문이며 실제 사용 0건. `subprocess` 실호출 7곳. `opal/tools/run-log-tool/tests/` **31 passed in 200.18s** (직접 실행 확인).
10. **범위 준수.** `opal/tools/state-tool/` 전체를 읽지 않았고 지적하지 않았다(T05 소유).

---

## 8. 문서 업데이트 제안

- [ ] **GC-DP-303** [반복 카테고리 트리거] `docs/SECURITY.md` §1 위협 모델에 **링크 추종 전반**을 명시 추가
  - 근거: 같은 결함 계열이 3회 반복됐다 — T02 GC-101/102/103(조각 경로 심볼릭 링크), T03 GC-201/202(가져오기 경로 심볼릭 링크), T03 GC-212(가져오기 경로 하드 링크). 매번 "심볼릭 링크"만 명시돼 있어 방어도 심볼릭 링크만 닫혔다.
  - 제안 내용: "§1에 CWE-59/CWE-61을 명시하고, **파일을 여는 모든 신규 경로는 fd 기준 3검사를 통과해야 한다**를 규칙화한다 — (a) `O_NOFOLLOW`, (b) `os.fstat(fd)`로 `S_ISREG` 확인(FIFO·device·directory 거부), (c) `st_nlink == 1` 확인(하드 링크 거부). 경로 문자열 기준 검사(`is_symlink()`·`resolve()`)는 보조이며 단독으로는 경계를 보장하지 않는다."

- [ ] **GC-DP-302(재제출)** [새 카테고리 트리거] `docs/SECURITY.md` §9 "신뢰 불가 원본 파싱" 신설
  - 근거: 직전 검사에서 제안했고 미반영이다. 이번 재작업이 (b)(c) 항목을 코드로는 구현했으나 기준 문서에는 남지 않아, 다음 신규 파서에서 같은 4건이 재발할 수 있다.
  - 제안 내용: "§9 — (a) 원본 파일당 바이트 상한 의무, (b) 디코딩 실패·타입 불일치·중첩 초과·달력 오류는 예외를 밖으로 던지지 않고 건너뜀/손상 집계로 흡수, (c) 파서가 잡아야 할 예외 최소 집합 `OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError, OverflowError, RecursionError`, (d) 원본은 1회만 읽고 해시를 재사용, (e) 손실 허용 디코딩을 쓰는 경로는 `sha256`의 기준(원본 바이트 vs 치환 후 텍스트)을 계약에 명시."

---

## 9. 범위 밖 (지적 아님 — 소유 태스크에 인계)

| 관측 | 소유 태스크 | 비고 |
|---|---|---|
| `redact()` 본문 pass-through(:241-250) | **T06** | 설계대로. 가져오기가 초크포인트에 올라타 있음 §7-3에서 재확인 |
| 가져오기 원본 상한(GC-207) | **T06** | §6에 이관 항목으로 계상 |
| `sources[].sha256` 이중 읽기(GC-210) | **T06** | §6에 이관 항목으로 계상 |
| `_iter_records_from_bytes`가 조각 전량을 메모리에 적재(:552, :960) | **T04** | 조각 경계(4 MiB)·색인이 T04 소관 |
| 색인 부재로 매 append마다 조각 전량 스캔(:551) | **T04** | D-3/D-I 설계대로 |
| `skipped_invalid` 집계 필드 추가(§5-2) | **PM / T11** | 계약 3자산 동시 개정 필요 |
| 가져온 사건의 완료 게이트 불기여 **집행** | **T11** | 이번 태스크는 능력만 |
| 최종 조합 판정의 게이트 집행 | **T08** | append 시점 구조 제약까지만이 이번 범위 |
| `begin-worker`·워커 token 발급·`worker_token_invalid` | 범위 밖 | 미구현이 정상 |
| `opal/tools/state-tool/` 전체 | **T05** | 읽지 않았다 |
| `docs/run-log/` 계약 3자산 | **PM** | 기준으로만 참조, 변경 제안은 §8로 분리 |

---

## 10. 판정 근거

| 판정 축 | 값 |
|---|---|
| check status | `pass` (3개 대상 전부 읽음, `checked_files == target_files`) |
| missing_capabilities | 없음 (`docs/SECURITY.md` 존재 → T0 기준 확보) |
| blocking finding | **1건** (GC-212) |
| advisory | 3건 (GC-213, GC-207 이관, GC-210 이관) |
| informational | 1건 (GC-211 부분 조치) |
| baseline delta | resolved 6 (GC-201·202·203·204·205·206·208 중 7건 해소 — 209 포함 시 8건) / persisting 3 (GC-207·210·211) / new 2 (GC-212·213) |
| **최종 판정** | **FAIL** |

`gc-finding-schema.md` §6: `INCOMPLETE` 조건 불성립, blocking 1건 이상 → **FAIL**.

### 조치 권고 — 한 곳에서 닫힌다

**GC-212 + GC-213은 `_safe_read_bytes()`(:369) 한 함수의 `os.fstat(fd)` 게이트 3줄로 함께 닫힌다.** 그 외 blocking은 없다. 이 3줄을 적용하고 §3.1의 정상 가져오기 재현(`scanned: 3, imported: 3`)과 31건 테스트가 그대로 통과하면 이 축은 PASS_WITH_ADVISORIES로 전환된다(잔여는 T06 이관 2건 + informational 1건).
