# GC SECURITY REPORT — 2026-09-07 23:18

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 시작 2026-09-07 23:05:00 / 완료 2026-09-07 23:18:35 / 소요 13분 35초
- 범위: 태스크 109 변경분 (`git diff HEAD~2 HEAD`, 25파일 / +1088 −131) / 대상 파일 25개
- 작업 루트: `/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_109`
- 비교 기준(선재/기인 구분): `HEAD~2` = `3fec20c`, `HEAD` = `70d6361`
- 에이전트: opal-security-checker
- APPLY 수행 여부: N (진단 전담 — 소스 파일 무수정, 수정은 CLOSE 단계 `//opds` 이관)

### 기준 문서 상태

| 기준 | 상태 |
|------|------|
| Base — OWASP Top 10 (2021) | 적용 |
| Base — CWE Top 25 / SANS Top 25 | 적용 |
| 프로젝트 — `docs/SECURITY.md` | **존재** (8,065 bytes, §1~§8). Base에 병합 적용 |
| 허브+링크 상세 문서 | 링크 0건 — 단일 문서 프로젝트이므로 허브 전체 적용 |

병합 적용한 프로젝트 규칙 중 본 진단과 직접 관련된 것:
- `docs/SECURITY.md §6 > path 정규화 (GC-013, CWE-22)` — "`path.resolve()`로 정규화 / 결과가 `homedir` 또는 `cwd` 하위가 아닌 경우 skip (path traversal 방어)" = **정규화 후 접두 봉쇄(containment)**가 프로젝트 표준이다.
- `docs/SECURITY.md §7 OPAL_HOME 가드` — 경로 정규화 후 절대경로 비교로 트리 이탈 거부.

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 8 |
| 심각도 분포 | Critical 0 / High 1 / Medium 1 / Low 3 / Info 3 |
| 자동 수정 가능 | 1 (GC-002) |
| 수동 조치 필요 | 7 |
| 파일별 상위 Top 5 | `opal/tools/code-scan/code-scan.js` (2건) / `dashboard/backend/scanner.py` (4건) / `dashboard/backend/routers/doctor.py` (1건) / `opal/tools/brain-tool/brain_tool.py` (1건) |
| 카테고리별 빈도 | CWE-22 경로 처리 (2 파일) / CWE-59 심볼릭 링크 (2 파일) / CWE-248 미처리 예외 (1 파일) / CWE-209 정보 노출 (1 파일) |
| Critical/High 수 | 1 |
| 문서 업데이트 제안 수 | 2 (빈도 0건 + 심각도 1건 + 새 카테고리 1건) |
| **해소 확인** | 착수 시점 진성 취약점 **1건(2입력) → 해소 확인** (§6 전/후 실측) |

### 경로 이탈 반증 시도 총괄

| 축 | 시도 | 결과 |
|----|------|------|
| `resolve_task_dir` 함수 레벨 퍼징 | 36입력 | 이탈 **0건** (§6.2 전건 표) |
| HTTP 엔드포인트 레벨 퍼징 (`/detail`·`/artifact`) | 27입력 × 2엔드포인트 | 이탈 **0건**, 예외 1건(GC-002) |
| 접두 검사 경계 오류(형제 디렉터리) | `tasks-evil/` 실 디렉터리 | **차단** — `+ os.sep` 형태가 정확 |
| `hub_root` 3런타임 순수성·계약 일치 | 골든 케이스 C-1~C-7 × 3구현 | 3구현 전건 일치, 부작용 **0건** |
| `resolve_task_dir` 우회 잔여 조립 경로 | `grep` 전수 | **0건** |
| `code-scan.js` 2단 탐색 상위 이탈 | 픽스처 + 실기기 | **이탈 확인 → GC-001 (High)** |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (1건)

- [ ] GC-001 [`opal/tools/code-scan/code-scan.js:348-361`] `findProjectRoot()` 1차 리터럴 `.opal/` 상향 탐색이 저장소 경계를 넘어 상위 디렉터리(사용자 홈 등)를 스캔 루트로 확정한다
  - 카테고리: CWE-22 (Path Traversal) / CWE-668 (Exposure of Resource to Wrong Sphere) / CWE-427 (Uncontrolled Search Path)
  - 위반 기준: Base (OWASP A01:2021 Broken Access Control) + **프로젝트(SECURITY.md §6 path 정규화 — "결과가 homedir/cwd 하위가 아니면 skip" 봉쇄 원칙)**
  - 태스크 기인/선재: **태스크 109 기인** (`880a486`이 신설한 1차 패스). 선재 코드는 `.git`/`.opal`/`package.json` 3마커를 동일 우선순위로 봤으나, 신규 1차 패스는 **`.opal/`만** 보고 `.git`·`package.json`을 무시한 채 끝까지 상향한다.
  - 설명: 신규 1차 패스는 cwd에서 파일시스템 루트까지 `.opal/` 존재만으로 상향 탐색한다. 자기 `.opal/`이 없고 `.git`/`package.json`으로만 식별되는 저장소는 **자기 루트에서 멈추지 못하고**, `.opal/`을 가진 임의의 조상 디렉터리를 프로젝트 루트로 삼는다. OPAL 설치본은 `~/.opal/`을 항상 만들므로 조건이 상시 성립한다. 그 결과 (a) 저장소 밖 파일의 내용을 읽어 `@header` 서술을 stdout에 노출하고, (b) 저장소 밖의 `.opal/code-scan.json`을 설정 원천으로 신뢰한다 — 공유 상위 디렉터리에 `.opal/code-scan.json`을 놓을 수 있는 주체가 그 하위 모든 프로젝트의 스캔 설정(scopes·exclude·headerSource)을 통제하는 설정 주입 경로가 된다.
  - 재현 (픽스처 — 저장소 밖 파일 내용 노출):
    ```bash
    S=$(mktemp -d); mkdir -p $S/anc/.opal $S/anc/repo/.git $S/anc/repo/src $S/anc/private
    echo '{"name":"x"}' > $S/anc/repo/package.json
    printf '/**\n * @header {"module":"secretmod","layer":"util","domain":"probe","description":"private file OUTSIDE the repo","exports":[]}\n */\n' > $S/anc/private/NOTMYREPO.js
    printf '/**\n * @header {"module":"inrepo","layer":"util","domain":"probe","description":"inside repo","exports":[]}\n */\n' > $S/anc/repo/src/in.js
    cd $S/anc/repo && node <W>/opal/tools/code-scan/code-scan.js scan --header-source inline
    # AFTER (HEAD): 2 file(s) — "[util]  NOTMYREPO.js  — private file OUTSIDE the repo" 포함  ← 이탈
    # BEFORE(HEAD~2): 1 file(s) — "[util]  in.js" 만                                         ← 봉쇄
    ```
  - 재현 (조상 `.opal/code-scan.json`을 설정 원천으로 신뢰):
    ```bash
    echo '{"version":1,"scopes":[{"path":".","layer":"util","domain":"probe"}]}' > $S/anc/.opal/code-scan.json
    cd $S/anc/repo && node <W>/opal/tools/code-scan/code-scan.js scan
    # → header_source_unset 에러가 조상 설정(.opal/code-scan.json)을 근거로 발화 = 조상 설정을 읽었다
    ```
  - 재현 (실기기 — 홈이 스캔 루트로 확정됨, 읽기 전용 확인):
    ```bash
    node -e 'const cs=require("<W>/opal/tools/code-scan/code-scan.js");process.chdir(process.argv[1]);console.log(cs.findProjectRoot())' ~/Documents
    # → /Users/iskang        (홈 디렉터리가 프로젝트 루트)
    node -e '...' ~/.claude
    # AFTER: /Users/iskang   /  BEFORE(HEAD~2): /Users/iskang/.claude   ← 기인 확인
    ```
  - 해결 방안: 1차 패스에 **봉쇄 상한**을 둔다. 셋 중 하나 이상:
    (a) 1차 패스의 상향을 「저장소 경계」에서 멈춘다 — `.git`·`package.json` 등 기존 마커를 만나면 그 지점을 루트로 확정하고 더 올라가지 않는다(선재 동작 복원 + `.opal/` 우선은 같은 디렉터리 안에서만 적용).
    (b) 1차 패스의 상향 한계를 `hubRootFromPath(process.cwd())` 또는 cwd의 git toplevel로 고정해 그 위로 올라가지 않게 한다.
    (c) `$HOME`(및 `path.parse(cwd).root`) 자체를 프로젝트 루트 후보에서 제외한다 — 프로젝트 표준 SECURITY.md §6의 "homedir/cwd 하위" 봉쇄와 방향이 같다.
    어느 안이든 워크트리 → 허브 수렴이라는 본 태스크 목적은 유지된다(허브는 `.git`도 함께 갖는 저장소 루트이므로 (a)·(b)로도 도달한다).
  - 자동 수정: N (탐색 우선순위 결정은 설계 판단)
  - 참조: https://cwe.mitre.org/data/definitions/427.html , https://owasp.org/Top10/A01_2021-Broken_Access_Control/

### Medium (1건)

- [ ] GC-002 [`dashboard/backend/scanner.py:102,110`] `task_id`에 널 바이트가 섞이면 `os.path.realpath`가 `ValueError`를 던져 HTTP **500**이 된다 (선재는 404)
  - 카테고리: CWE-248 (Uncaught Exception) / CWE-158 (Improper Neutralization of Null Byte) / OWASP A05:2021
  - 위반 기준: Base (CWE-248, OWASP A05 Security Misconfiguration — 오류 처리 누락)
  - 태스크 기인/선재: **태스크 109 기인 회귀**. 선재 코드 `os.path.isdir(os.path.join(...))`는 `genericpath.isdir`이 `(OSError, ValueError)`를 삼켜 `False` → 404였다. 신규 `resolve_task_dir`은 `os.path.realpath`(→ `os.lstat`)를 예외 처리 없이 호출한다.
  - 설명: `resolve_task_dir`의 앞단 검사(`os.pardir`·구분자·`isabs`)는 널 바이트를 걸러내지 않는다. 단일 세그먼트에 널 바이트만 붙은 `task_id`(`'101-a\x00'`)는 검사를 통과해 `os.path.realpath`에 도달하고 `ValueError: lstat: embedded null character in path`가 라우터 밖으로 전파된다. 경로 이탈은 아니다(트리 밖 어떤 내용도 실리지 않는다). 영향은 (a) 500 응답으로 정상 404 계약 위반, (b) 서버 로그에 스택트레이스 축적, (c) 디버그 설정에서의 트레이스백 노출 가능성이다.
  - 재현:
    ```bash
    # 엔드포인트 (TestClient, 픽스처 프로젝트)
    GET /api/tasks/detail?project=<proj>&task_id=101-a%00       → 500   (404 기대)
    GET /api/tasks/artifact?project=<proj>&task_id=101-a%00&name=TASK.md → 500
    # 함수 레벨
    python3 -c "import sys;sys.path.insert(0,'<W>');from dashboard.backend.scanner import resolve_task_dir;resolve_task_dir('/tmp/proj','101-a\x00')"
    # → ValueError: lstat: embedded null character in path
    # BEFORE(HEAD~2) 동일 입력: detail 404 / artifact 404
    ```
  - 해결 방안: `resolve_task_dir` 앞단 검사에 `"\x00" in task_id → None`을 추가한다(구분자 검사 바로 옆, `scanner.py:98` 인접). 대안으로 `realpath` 호출을 `try/except (OSError, ValueError): continue`로 감싼다 — 다만 앞단 거부가 「단일 세그먼트 정규화 조건」이라는 함수 계약과 더 일관된다.
  - 자동 수정: Y (1행 추가, 계약 변화 없음 — 404 복원)
  - 참조: https://cwe.mitre.org/data/definitions/158.html

### Low (3건)

- [ ] GC-003 [`dashboard/backend/scanner.py:110-115`] `task_id`가 대소문자 정규화되지 않아 macOS APFS(기본 대소문자 비구분)에서 실제와 다른 표기로도 200이 되고, 그 표기가 캐시 키에 그대로 들어간다
  - 카테고리: CWE-178 (Improper Handling of Case Sensitivity)
  - 위반 기준: Base (CWE-178)
  - 태스크 기인/선재: **선재** — 선재 코드도 `101-A`에 200을 반환했다(실측: BEFORE/AFTER 모두 200). 다만 이 태스크가 해석 책임을 단일 함수로 모았으므로 정규화를 넣을 자리가 여기로 확정됐다.
  - 설명: 실 디렉터리가 `101-a`일 때 `task_id=101-A`가 200이 된다. **경로 이탈은 아니다** — 해석 결과는 `tasks/` 트리 안이고, 접두 검사도 통과한 정상 경로다. 영향은 보안 경계가 아니라 (a) 동일 태스크가 표기별로 서로 다른 캐시 키(`task_detail:{project}:{task_id}:...`, `routers/tasks.py:527`)를 차지하는 캐시 오염·중복, (b) 반환 경로 문자열이 파일시스템 실 표기와 달라지는 비정규 식별자다. 대소문자 구분 파일시스템(Linux 배포 환경)에서는 404가 되어 플랫폼 간 동작이 갈린다.
  - 재현:
    ```bash
    GET /api/tasks/detail?project=<proj>&task_id=101-A   → 200 (실 디렉터리는 101-a)
    # 반환 경로: <proj>/tasks/101-A  ← 실 표기(101-a)와 다른 문자열
    ```
  - 해결 방안: 해석 성공 후 `os.path.basename(resolved)`를 열거(`iter_task_dirs`) 결과 이름 집합과 **정확히 일치**하는지 확인하거나, 열거 이름 집합 소속 여부로 `task_id`를 검증한다(열거·해석 단일 원천화와 방향이 같다). 캐시 키에는 검증된 실 이름을 쓴다.
  - 자동 수정: N (열거·캐시 키 계약에 걸친다)
  - 참조: https://cwe.mitre.org/data/definitions/178.html

- [ ] GC-004 [`dashboard/backend/scanner.py:110-116`] 심볼릭 링크 TOCTOU — `realpath` 접두 검사 시점과 하류 파일 접근 시점 사이에 경로 구성요소가 교체될 여지가 남는다
  - 카테고리: CWE-367 (Time-of-check Time-of-use) / CWE-59 (Link Following)
  - 위반 기준: Base (CWE-367)
  - 태스크 기인/선재: **태스크 109 기인**(신규 코드의 잔여 리스크). 선재 코드는 검사 자체가 없었으므로 「더 나빴다」— 회귀가 아니라 잔여 항목이다.
  - 설명: `resolve_task_dir`은 `realpath`로 완전 해석한 경로를 반환하므로 반환 시점의 판정은 정확하다. 그러나 반환 후 하류(`_read_state`의 `state.json` 열기, `read_markdown`, `_get_artifact_files`)가 그 경로를 다시 열 때 커널은 경로를 재해석한다. 검사와 사용 사이에 `resolved`의 중간 구성요소를 트리 밖을 가리키는 심볼릭 링크로 교체하면 하류 읽기가 트리 밖에 착지할 수 있다. **전제 조건이 무겁다**: 공격자가 이미 `tasks/` 하위에 쓰기 권한을 가져야 하고(그 시점에 이미 저장소 쓰기 권한 보유), 서버는 `127.0.0.1` 바인딩(`main.py:144`)에 CORS가 `localhost:5173`로 제한(`main.py:76-79`)된 읽기 전용 대시보드다. 따라서 실효 위험은 낮다.
  - 재현: 결정론적 재현 명령 없음(경합 창). 구조적 근거는 `scanner.py:110`(검사)과 `routers/tasks.py:509-531`·`646-656`(사용)이 서로 다른 시점에 같은 경로 문자열을 각각 해석하는 형태 그 자체다.
  - 해결 방안: 필요 시 `os.open(resolved, os.O_RDONLY | os.O_DIRECTORY)`로 디스크립터를 확보하고 하류 읽기를 `dir_fd` 상대 경로(`os.open(..., dir_fd=fd)`)로 수행한다. 현 위협 모델(로컬 루프백·읽기 전용)에서는 **수용(accept)**도 정당한 결론이며, 그 경우 `docs/SECURITY.md`에 위협 모델상 수용 사유를 명시할 것을 권고한다.
  - 자동 수정: N
  - 참조: https://cwe.mitre.org/data/definitions/367.html

- [ ] GC-005 [`opal/tools/code-scan/code-scan.js:3675-3684`] 워크트리 실행 경고가 허브 절대경로를 stderr에 노출한다
  - 카테고리: CWE-209 (Generation of Error Message Containing Sensitive Information)
  - 위반 기준: Base (CWE-209 / OWASP A09:2021 Logging Failures)
  - 태스크 기인/선재: **태스크 109 기인** (`70d6361`).
  - 설명: 경고 문면이 `hubRootFromPath(process.cwd())` 결과를 그대로 싣는다. 실측 출력에 `/Volumes/Data/AIStudio/workspace/ai-framework`가 포함된다. 노출 대상은 로컬 워크스페이스 경로이며 자격증명·토큰·홈 사용자명 이상의 비밀은 없다. CI 로그가 공개되는 환경에서는 내부 디렉터리 구조가 노출되나, 절대경로 자체는 이 저장소에서 이미 여러 문서·테스트에 등장한다. **stdout 오염은 없음을 실측으로 확인**했다(§6.4).
  - 재현:
    ```bash
    cd <W> && node opal/tools/code-scan/code-scan.js summary 1>/dev/null
    # stderr: code-scan: [worktree] cwd는 워크트리 안이지만 스캔 루트는 허브 /Volumes/.../ai-framework 입니다 — ...
    ```
  - 해결 방안: 수용 가능. 축소를 택한다면 절대경로 대신 cwd 기준 상대 경로(`path.relative(process.cwd(), cwdHubRoot)`)나 마지막 세그먼트만 싣는다. 진단 목적상 절대경로가 유용하므로 **수용 권고**하되, 판단을 기록으로 남길 것.
  - 자동 수정: N
  - 참조: https://cwe.mitre.org/data/definitions/209.html

### Info (3건)

- [ ] GC-006 [`dashboard/backend/scanner.py:38-41` vs `dashboard/backend/routers/doctor.py:91-93`] 심볼릭 링크 열거 정책이 두 지점에서 반대다
  - 카테고리: 도메인 (일관성) / CWE-59 인접
  - 위반 기준: Base (CWE-59 방어 정책의 일관성)
  - 태스크 기인/선재: **태스크 109 기인** (`iter_task_dirs` 신설 + doctor 예외 명문화).
  - 설명: `_sorted_subdirs`는 `entry.is_dir(follow_symlinks=False)`로 심볼릭 링크 디렉터리를 **전부** 열거에서 제외한다. 반면 `doctor.py:93`의 `d.is_dir()`는 기본값(`follow_symlinks=True`)이라 링크를 센다. 실측: 같은 `tasks/`에서 `iter_task_dirs`는 1건, doctor-style은 3건.
  - 판정: **`iter_task_dirs`의 선택은 안전측이 맞다.** 링크를 열거하지 않으면 트리 밖 대상이 열거 모수에 섞이지 않는다. 부작용은 「정당한 태스크를 숨김」인데, 아카이브를 외부 볼륨으로 옮기고 `tasks/900-x -> /external/900-x` 링크를 남기는 운용이 있으면 그 태스크는 `/api/tasks`·대시보드 집계·`_count_tasks`에서 조용히 사라진다(실측 확인). 반면 `resolve_task_dir`은 **트리 내부를 가리키는** 링크는 해석하므로(실측: `101-alias -> 101-real` 해석 성공, `900-moved -> 트리 밖` 차단), 「열거에는 없는데 직접 조회는 되는」 비대칭이 생긴다. 이탈은 아니다.
  - 해결 방안: 정책을 한쪽으로 명문화한다 — (a) 열거·해석 모두 링크 불허(가장 단순, 비대칭 소멸), 또는 (b) 열거도 `realpath` 접두 검사로 「트리 내부 링크는 허용」에 맞춘다. doctor는 진단 도구 예외(파일 헤더에 명문화됨)로 현행 유지가 타당하나, 링크를 세는 사실을 보고 문면에 드러낼 것을 권고한다.
  - 자동 수정: N
  - 참조: https://cwe.mitre.org/data/definitions/59.html

- [ ] GC-007 [`dashboard/backend/routers/tasks.py:650-655`] `artifact` 의 `name` 검사가 문자열 블랙리스트여서 태스크 폴더 **안의** 심볼릭 링크는 그대로 따라간다
  - 카테고리: CWE-59 (Link Following) / CWE-22 인접
  - 위반 기준: Base (CWE-59)
  - 태스크 기인/선재: **선재** — `name` 검사 로직은 이 태스크에서 한 줄도 바뀌지 않았다(`git diff HEAD~2 HEAD` 확인).
  - 설명: `name`은 `/`·`\`·`..` 문자열 검사만 받고(`tasks.py:651`) `read_markdown`에는 확장자 제한이 없다(`parsers/markdown_reader.py:29-34`). 따라서 `tasks/101-a/evil.md -> /etc/passwd` 같은 트리 내 링크가 있으면 `name=evil.md`로 그 내용이 200으로 실린다. 전제는 `tasks/` 하위 쓰기 권한이므로 GC-004와 동일하게 실효 위험이 낮다. `task_id` 측 이탈은 이 태스크가 `realpath` 접두 검사로 막았으나 `name` 측은 같은 등급의 방어를 받지 못한 상태다 — **방어 수준 비대칭**이 이번 변경으로 도리어 눈에 띄게 됐다.
  - 재현: `tasks/<t>/leak.md`를 트리 밖 파일로 심볼릭 링크한 뒤 `GET /api/tasks/artifact?...&task_id=<t>&name=leak.md` → 200 + 링크 대상 내용.
  - 해결 방안: `artifact_path`에도 `resolve_task_dir`과 같은 판정을 적용한다 — `os.path.realpath(artifact_path).startswith(task_dir + os.sep)` 접두 검사 후 읽기. 4행 수준이며 `task_id` 측 방어와 형태가 같아진다.
  - 자동 수정: N (엔드포인트 계약 접점 — `//opds` 이관 권고)
  - 참조: https://cwe.mitre.org/data/definitions/59.html

- [ ] GC-008 [`opal/tools/brain-tool/brain_tool.py:271-296,1299-1302`] `--brain-path` 기본값/명시값의 의미 비대칭과, `ingest-scan` 스캔 루트가 허브로 고정되는 점
  - 카테고리: 도메인 (신뢰 경계 / 최소 권한)
  - 위반 기준: Base (OWASP A04:2021 Insecure Design — 놀라움 최소화)
  - 태스크 기인/선재: **태스크 109 기인** (설계 의도된 동작).
  - 설명: **격리 자체는 성립한다**(§7 판정 참조 — 명시값이 허브로 리다이렉트되는 경우 0건). 남는 점은 두 가지다. (1) 같은 문자열 `"."`이 기본값일 때는 허브, `--brain-path .`로 명시하면 워크트리로 해석된다(실측). 타입(`_DefaultBrainPath` 대 `str`)이 의미를 결정하므로 값만 보는 독자에게는 놀라운 동작이다 — 다만 이 비대칭이 곧 격리 보장의 메커니즘이므로 **제거 대상이 아니다**. (2) `cmd_ingest_scan`은 쓰기 대상(brain)이 명시 경로로 격리돼도 **읽기 루트는 `_hub_cwd()`로 허브에 고정**된다(`brain_tool.py:1302`). 격리 brain에 허브의 docs/skills/tasks 목록이 들어간다 — 허브 오염은 없으나(단방향 읽기) 격리 테스트의 입력이 워크트리가 아니라 허브가 된다.
  - 재현:
    ```bash
    cd <W> && python3 -c "
    import sys,types,importlib.util; sys.modules.setdefault('yaml',types.ModuleType('yaml'))
    s=importlib.util.spec_from_file_location('bt','<W>/opal/tools/brain-tool/brain_tool.py')
    bt=importlib.util.module_from_spec(s); s.loader.exec_module(bt)
    print('default  ->', bt.resolve_brain_path(bt.DEFAULT_BRAIN_PATH))
    print(\"explicit '.' ->\", bt.resolve_brain_path('.'))
    print('_hub_cwd ->', bt._hub_cwd())"
    # default  -> /Volumes/.../ai-framework/.opal/brain                          (허브)
    # explicit '.' -> /Volumes/.../.opal-worktrees/task_109/.opal/brain          (워크트리)
    # _hub_cwd -> /Volumes/.../ai-framework                                       (ingest-scan 읽기 루트)
    ```
  - 해결 방안: (1) 현행 유지 + `--brain-path`의 도움말 문면에 "명시값은 정규화하지 않는다(격리 보장)"를 한 줄 노출. (2) `ingest-scan`이 스캔 루트를 허브로 고정한다는 사실을 `--source` 도움말이나 출력에 드러내거나, 격리 실행용 `--scan-root` 분리를 검토.
  - 자동 수정: N
  - 참조: https://owasp.org/Top10/A04_2021-Insecure_Design/

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

- [ ] GC-DP-001 [심각도 트리거] High 이슈 "CWE-427 프로젝트 루트 탐색 봉쇄" → `docs/SECURITY.md` 체크리스트 추가 제안
  - 근거: High 1건(GC-001) 발견 (빈도 트리거와 독립 판정 — 동일 fingerprint 파일 수 1로 빈도 임계값 N=3 미달)
  - 제안 내용: "상향 탐색으로 루트를 결정하는 코드는 **상향 상한**을 반드시 명시한다. `$HOME`·파일시스템 루트를 루트 후보에서 제외하고, 저장소 경계 마커(`.git`)를 만나면 그 지점에서 멈춘다. 상위 디렉터리의 설정 파일을 신뢰 원천으로 삼지 않는다. (§6 path 정규화의 봉쇄 원칙을 탐색 경로에도 적용)"

- [ ] GC-DP-002 [새 카테고리 트리거] "허브 루트 해석 / 워크트리 경로 신뢰 경계" → `docs/SECURITY.md` **§9 신설** 제안
  - 근거: `docs/SECURITY.md` 헤더 인덱스(§1~§8) 전건과 키워드 교집합 0 — 「워크트리·허브 루트 해석」 항목이 없다. 이번 변경의 중심 축(3런타임 공유 순수 함수 + `tasks/` 해석 단일 지점)이 문서화되지 않은 상태다.
  - 제안 내용(초안): "**§9 허브 루트 해석 신뢰 경계** — (1) `hub_root`/`hubRootFromPath`는 파일시스템·환경변수·`cwd()`에 접근하지 않는 순수 문자열 함수여야 하며, 3런타임(console BE·brain-tool·code-scan) 구현은 `opal/core/references/hub-root-cases.json` 골든 케이스로 대조한다. (2) 사용자 입력에서 유래한 식별자를 경로로 바꾸는 지점은 단일 함수로 봉인하고, 해석 결과가 허용 트리 내부임을 `realpath` + `root + os.sep` **접두** 검사로 확인한다(`+ os.sep` 생략은 형제 디렉터리 오허용). (3) 앞단 정규화 검사는 널 바이트(`\x00`)를 포함한다. (4) 격리 실행을 위해 명시적으로 주어진 경로는 허브로 수렴시키지 않는다."

---

## 5. 문서 작성 유도 (해당 시)

해당 없음 — `docs/SECURITY.md`가 존재하며(8,065 bytes, §1~§8) Base에 병합 적용했다. 초안 신설 대신 §4의 **§9 신설 제안(GC-DP-002)**으로 갈음한다.

---

## 6. 경로 이탈 반증 시도 — 전건 실측

### 6.1 착수 시점 취약점 해소 확인 (전/후 실측)

측정 방법: `git archive HEAD~2`로 선재 트리를 별도 디렉터리에 전개하고, 동일 픽스처(`.opal/AGENT.md` 보유 프로젝트 + `tasks/101-a/TASK.md`)에 대해 FastAPI `TestClient`로 같은 요청을 양쪽에 보냈다.

| 입력 | BEFORE (`3fec20c`) detail | AFTER (`70d6361`) detail | 판정 |
|------|---------------------------|--------------------------|------|
| `task_id='../'` | **200** | 404 | **해소** |
| `task_id='..'` | **200** | 404 | **해소** |
| `task_id='../../'` | **200** | 404 | 해소 |
| `task_id='/etc'` | **200** | 404 | 해소 |
| `task_id='backup/009-x'` | 200 | 404 | 해소(계약 변경: backup은 이름만으로 조회) |
| `task_id='./101-a'` | 200 | 404 | 해소 |
| `task_id='.'` | **200** | 404 | 해소 |
| `task_id=''` | **200** | 404 | 해소 |
| `task_id='backup'` | **200** | 404 | 해소 |
| `task_id='101-a/'` | 200 | 404 | 해소 |
| `task_id='.././'` | **200** | 404 | 해소 |

PM이 실측한 2건(`'../'`·`'..'`)을 포함해 **선재 200 응답 11입력 전건이 404로 봉쇄됐다**.

**선재 취약점의 실제 심각도 — 임의 파일 읽기까지 도달함을 실측했다** (이 태스크가 해소했다):

```
BEFORE(HEAD~2):
GET /api/tasks/artifact?project=<proj>&task_id=..&name=ROOTLEAK.md
  → 200 {"name":"ROOTLEAK.md","content":"# ROOT LEAK — outside tasks/\n","task_id":".."}

GET /api/tasks/artifact?project=<proj>&task_id=../../../../../../../../../../etc&name=passwd
  → 200 {"name":"passwd","content":"##\n# User Database\n# \n# Note that this file is consulted directly only when the system is..."}
GET ...&task_id=../../../../../../../../../../etc&name=hosts
  → 200 {"name":"hosts","content":"##\n# Host Database\n#..."}

AFTER(HEAD): 위 3건 전부 404 {"detail":"Task not found: ..."}
```

`read_markdown`에 확장자 제한이 없으므로(`parsers/markdown_reader.py:29-34`) 선재 상태는 **UTF-8로 읽히는 임의 파일의 임의 읽기**였다(`/etc/passwd` 실증). 완화 요인은 `127.0.0.1` 바인딩(`main.py:144`)과 CORS `localhost:5173` 제한(`main.py:76-79`)으로 로컬 한정이었다는 점이다. 등급: **선재 High(Critical급 결함, 로컬 전제로 완화) → 태스크 109에서 해소 확인**.

### 6.2 `resolve_task_dir` 함수 레벨 퍼징 — 36입력 전건

픽스처: `tasks/101-a`, `tasks/backup/009-x`, `tasks/sub/nested`, `tasks/한글-톡`(NFC), `tasks/linkout -> <트리 밖>`, `tasks/linkin -> tasks/101-a`, **형제 디렉터리 `tasks-evil/secret`**, 트리 밖 `outside/loot/SECRET.md`.

| 시도 | 입력 | 결과 |
|------|------|------|
| 정상 기준선 | `101-a` | 해석(트리 내부) |
| 정상 기준선 | `009-x` | 해석(`tasks/backup/009-x`) |
| 유니코드 NFC | `한글-톡`(NFC) | 해석(트리 내부) |
| **유니코드 NFD** | `한글-톡`(NFD) | 해석(트리 내부) — APFS 정규화, 이탈 아님 |
| **전각 문자** | `．．／` | 차단 |
| **전각 solidus** | `..／..／101-a` | 차단 |
| **유사 문자(U+2044)** | `..⁄..⁄101-a` | 차단 |
| **URL 인코딩 2중** | `%252e%252e%252f101-a` | 차단 |
| URL 인코딩 1중 | `%2e%2e%2f101-a` | 차단 |
| **오버롱 UTF-8** | `..\xc0\xaf..\xc0\xaf101-a` | 차단 |
| **널 바이트 절단** | `101-a\x00../../etc` | 차단 |
| **널 바이트 접미** | `101-a\x00` | **예외 `ValueError`** → GC-002 |
| **대소문자 변형** | `101-A` | 해석(트리 내부) — 이탈 아님, GC-003 |
| **대소문자 `TASKS/`** | `../TASKS/101-a` | 차단 |
| **형제 디렉터리(경계 오류)** | `../tasks-evil/secret` | **차단** |
| **심볼릭 링크(트리 밖)** | `linkout` | **차단** |
| 심볼릭 링크(트리 밖, 자식) | `linkout/loot` | 차단 |
| 심볼릭 링크(트리 내부) | `linkin` | 해석(→ `tasks/101-a`) — 이탈 아님 |
| 트레일링 점 | `101-a.` | 차단 |
| 트레일링 공백 | `101-a ` | 차단 |
| 삼중 점 | `...` | 차단 |
| `backup` 자체 | `backup` | 차단 |
| 트리 내 비태스크 디렉터리 | `sub` | 해석(트리 내부) — 이탈 아님 |
| 점 | `.` | 차단 |
| 이중 점 | `..` | 차단 |
| 공문자열 | `''` | 차단 |
| 절대경로 | `/etc` | 차단 |
| 트레일링 슬래시 | `101-a/` | 차단 |
| 이중점+슬래시 | `../` | 차단 |
| 이중점+백슬래시 | `..\` | 차단 |
| 이중점+이중슬래시 | `..//` | 차단 |
| 이중점+슬래시+점 | `../.` | 차단 |
| 퍼센트-널 | `..%00/101-a` | 차단 |
| 틸데 | `~` | 차단 |
| 개행 | `101-a\n` | 차단 |
| CRLF 주입 | `101-a\r\n../../etc` | 차단 |

**이탈(트리 밖 착지) 0건.** 유일한 예외 상황은 GC-002(널 바이트 접미 → `ValueError`)이며 그것도 이탈이 아니다.

접두 검사 경계 오류 반증(형태 확인):
```
'/x/tasks-evil/secret'.startswith('/x/tasks' + os.sep)  → False   ← 현재 구현 (정확)
'/x/tasks-evil/secret'.startswith('/x/tasks')           → True    ← os.sep 생략 시 오허용
```
`scanner.py:112`는 `tasks_root_real + os.sep` 형태를 쓴다 → **형제 디렉터리 오허용 없음**.

### 6.3 HTTP 엔드포인트 레벨 퍼징 — 27입력 × 2엔드포인트

`/api/tasks/detail`·`/api/tasks/artifact` 양쪽에 §6.2 입력군 + `..;/`·`....//`·`..%2f..`·`TASKS`·`../ROOTLEAK.md` 등을 재전송한 결과:

- 정상 태스크(`101-a`·`009-x`)만 200. **적대적 입력 전건 404.**
- 예외: `101-a\x00` → 양 엔드포인트 500 (GC-002).
- `name` 파라미터 이탈 시도(`../../ROOTLEAK.md`·`..%2f..%2fROOTLEAK.md`·`../ROOTLEAK.md`) → 전건 **400** (선재 블랙리스트가 작동). 단 링크 경유 우회는 GC-007 참조.

### 6.4 `hub_root` / `hubRootFromPath` 순수성 및 3런타임 계약 일치

`open`·`os.stat`·`os.lstat`·`os.getcwd`·`os.environ`(Python) / `fs.existsSync`·`fs.readFileSync`·`fs.statSync`·`process.cwd`·`process.env`(Node)를 후킹해 호출을 계수했다.

| 구현 | 골든 케이스 C-1~C-7 | 부작용 |
|------|--------------------|--------|
| `dashboard/backend/paths.py:18 hub_root` | 7/7 일치 | **NONE (순수)** |
| `opal/tools/brain-tool/brain_tool.py:229 hub_root` | 7/7 일치 | **NONE (순수)** |
| `opal/tools/code-scan/code-scan.js:338 hubRootFromPath` | 7/7 일치 | **NONE (순수)** |

3구현이 동일 입력에 동일 문자열을 반환한다(교차 대조 전건 일치). `hubRootFromPath`는 비문자열 입력(`null`·`123`)을 그대로 반환한다(방어적, 예외 없음). **신뢰 경계 무너짐 없음 — 계약 성립.**

`code-scan.js` stdout 무오염 실측:
```bash
cd <W> && node opal/tools/code-scan/code-scan.js summary > wt.out 2> wt.err   # 경고 1줄 stderr
cmp wt.out hub.out → 차이 없음 (byte-identical)
```

### 6.5 `resolve_task_dir` 우회 잔여 경로 — `grep` 전수

```bash
grep -rn --include='*.py' -E '"tasks"|tasks_dir' dashboard/backend/ | grep -v '/tests/'
grep -rn --include='*.py' 'task_id' dashboard/backend/ | grep -v '/tests/' | grep -E 'join|Path|open|/'
```
결과: `task_id`를 경로로 조립하는 지점은 `scanner.py:106-107`(= `resolve_task_dir` 내부) **1곳뿐**이다. `routers/tasks.py:509`·`646`은 `resolve_task_dir` 호출로 교체됐고, `routers/tasks.py:457`·`routers/dashboard.py:58`·`scanner.py:126`은 `task_id`가 아니라 `"tasks"` 상수만 붙인다(사용자 입력 미개입). `routers/doctor.py:91`은 진단 도구 예외로 명문화됐고 인자 경로의 1-depth만 센다. **문자열 조립 잔여 경로 0건.**

### 6.6 심볼릭 링크 열거 판정 실측

픽스처 `tasks/101-real`(실 디렉터리), `tasks/900-moved -> 트리 밖`, `tasks/101-alias -> tasks/101-real`:

| 함수 | 결과 |
|------|------|
| `iter_task_dirs` | `['101-real']` — 링크 2건 모두 제외 |
| `_count_tasks` | 1 |
| `resolve_task_dir('900-moved')` | `None` (트리 밖 링크 차단) |
| `resolve_task_dir('101-alias')` | `tasks/101-real` (트리 내부 링크 해석) |
| doctor-style `d.is_dir()` | 3 — `['101-alias','101-real','900-moved']` (링크 따라감) |

판정: 열거의 링크 제외는 **안전측이 맞다**. 상세는 GC-006.

---

## 7. `resolve_brain_path` 격리 판정 (H-3)

**판정: 격리 보장 성립 — 실 허브 brain 오염 경로 0건.**

`--brain-path`를 가진 서브커맨드 전수(9개)에 대해 argparse 결과 타입을 실측했다:

| 서브커맨드 | 기본값 타입 | `--brain-path X` | `--brain-path=.` | 축약 `--brain X` |
|-----------|------------|------------------|------------------|------------------|
| `add-page` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `update-page` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `index` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `log` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `search` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `sync-header` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `lint` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `validate` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `ingest-scan` | `_DefaultBrainPath` | `str` | `str ('.')` | `str` |
| `analyze` | (`brain_path` 속성 없음) | — | — | — |
| `init` | `str` (위치 인자) | — | — | — |

「argparse가 명시값을 받을 때 평범한 `str`로 교체한다」는 전제가 **모든 서브커맨드에서 성립한다** — 플래그 축약형(`--brain`)과 `=` 문법 포함 전건 `str`. `analyze`는 `brain_path`를 아예 갖지 않고 `require_brain`도 호출하지 않아 `AttributeError` 위험이 없다(`cmd_analyze`, `brain_tool.py:1213`). `init`은 위치 인자라 항상 평범한 `str`이며 `cmd_init`(`brain_tool.py:466`)도 `pathlib.Path(args.brain_path)`를 직접 쓴다 → 허브 수렴 미적용.

명시값 리다이렉트 반증(워크트리 cwd에서 실행, `_hub_cwd()` = 허브):

| 명시값 | 해석 결과 | 판정 |
|--------|-----------|------|
| `.` | `<W>/.opal/brain` | 워크트리 유지 |
| `./` | `<W>/.opal/brain` | 워크트리 유지 |
| `<W>/tmp/isolated-brain` | `<W>/tmp/isolated-brain/.opal/brain` | 워크트리 유지 |
| `<W>/.opal/brain` | `<W>/.opal/brain` | 워크트리 유지 |
| `tmp/x` (상대) | `<W>/tmp/x/.opal/brain` | 워크트리 유지 |
| `/tmp/explicit` | `/private/tmp/explicit/.opal/brain` | 리다이렉트 없음 |
| **기본값 센티넬** | `<허브>/.opal/brain` | 의도된 수렴 |

**허브로 리다이렉트된 명시값 0건 → 격리 테스트가 실 허브 brain을 오염시키는 경로는 없다.** 잔여 관찰 2건(값 기반이 아닌 타입 기반 판별의 의미 비대칭, `ingest-scan` 읽기 루트 허브 고정)은 GC-008(Info)로 기록했다.

---

## 8. 시크릿 스캔 · 위생 확인

| 항목 | 결과 |
|------|------|
| 하드코딩 API 키·토큰·비밀번호·개인키 | **0건** — 25파일 전건 정규식 스캔(`api_key`·`secret`·`password`·`token`·`private key`·`sk-`·`ghp_`·`xox[baprs]-`·`Bearer …`·`BEGIN … PRIVATE KEY`). 적중 전건이 오탐(shard 라벨 코드의 `token` 식별자, 캐시 키 문자열, 테스트 변수명) |
| 홈 절대경로 하드코딩 | 소스 0건. 신규 4파일 포함 전건 무적중 |
| 신규 파일 4건 | `dashboard/backend/paths.py`, `dashboard/backend/tests/test_paths.py`, `opal/core/references/hub-root-cases.json`, `opal/tools/code-scan/tests/test-hub-root.js` — 시크릿·자격증명 0건 |
| `.gitignore` 변경 | **0건** (`git diff --stat HEAD~2 HEAD -- .gitignore '**/.gitignore'` 무출력) — 확인 완료 |
| `.env`류 신규 파일 | **0건** (`.env`·`secret`·`credential`·`.pem`·`.key`·`id_rsa` 패턴 무적중) — 확인 완료 |
| 네트워크 바인딩 | `main.py:144` `host="127.0.0.1"` 유지 (외부 노출 금지 H-7/S-5 준수, 이 태스크 무변경) |
| CORS | `main.py:76-79` `localhost:5173`·`127.0.0.1:5173` 한정, `allow_credentials=False` (이 태스크 무변경) |

---

## 9. 판정 요약

1. **경로 이탈 반증 결과: 통과(우회) 0건.** `resolve_task_dir`의 `realpath` + `root + os.sep` 접두 검사는 유니코드 정규화·전각·다중 URL 인코딩·오버롱 UTF-8·널 바이트 절단·대소문자·형제 디렉터리 경계·트리 밖 심볼릭 링크 전건을 차단한다. 접두 검사 형태는 `+ os.sep`을 포함해 정확하다.
2. **착수 시점 취약점은 해소됐다.** `'../'`·`'..'` 200 → 404. 나아가 선재 상태가 `/etc/passwd` 임의 읽기까지 도달했음을 실측했고 그것도 함께 봉쇄됐다.
3. **이번 변경이 새로 만든 문제는 2건이다.** GC-001(High — `code-scan` 스캔 루트가 저장소 경계를 이탈)과 GC-002(Medium — 널 바이트 → 500 회귀). GC-001은 「경로 처리를 손댄 이 태스크에서 봉쇄가 오히려 느슨해진」 유일한 지점이므로 우선 조치를 권고한다.
4. **`hub_root` 3구현은 순수하고 계약이 일치한다** — 신뢰 경계 유지.
5. **`resolve_brain_path` 격리는 보장된다** — 데이터 파괴 경로 없음.

---

<!-- 상태 전이는 후속 //opds 단계에서 기입한다. 본 보고서는 진단 전담(소스 무수정)이다. -->
