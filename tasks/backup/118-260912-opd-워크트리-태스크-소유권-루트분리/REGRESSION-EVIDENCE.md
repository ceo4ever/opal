# REGRESSION-EVIDENCE — OP-TASK-118 비워크트리 바이트 동일 회귀 증거와 배포 검증

> W-14 (실행 그룹 P5) 산출물. 완료 기준 연결: AC-15, C-1, C-2 / 담당 시나리오 S-23, S-24.
> 측정 일시: 2026-09-12 KST. 측정자: EXECUTE 워커(opal-task-agent).
> **이 문서는 측정·판정만 기록한다. W-14는 소스 코드를 수정하지 않았다.**

---

## 0. 측정 대상과 좌표

| 항목 | 값 |
|---|---|
| 허브 (데이터 루트) | `/Volumes/Data/AIStudio/workspace/ai-framework` |
| 변경 전 기준 | `e8b6c4f` (disposable clone `/private/tmp/op118w14/base`) |
| 변경 후 작업본 | `.opal-worktrees/task_118` (`feat/OP-TASK-118`, base `e8b6c4f` + 미커밋 변경) |
| 진입 계약 | `state-tool verify --plan-contract-check` → `pass` (W-1~W-14 14건 인식) |
| 진입 계약 | `state-tool verify --code-scan-citation-check` → `pass` |

### 0.1 실험 설계 — 왜 "데이터 고정 · 코드만 스왑"인가

PLAN §Release and recovery의 원문 절차(base clone에서 실행 ↔ 작업본에서 실행)를 그대로 쓰면
**코드 차이와 데이터 차이가 동시에 개입한다**. `code-scan scan`은 저장소의 소스 파일을 읽고,
`event-loader`는 `opal/core/references/`를 읽는데, 이 태스크는 그 파일들 자체를 변경했기 때문이다.
그 상태의 diff는 "코드 변경이 출력을 바꿨는가"(C-1이 묻는 것)를 판정하지 못한다.

따라서 아래 2단 설계로 측정했다.

- **대조 A (정규화 1회)** — 데이터 루트를 **허브로 고정**하고, 도구 코드만 base clone ↔ 워크트리로 바꿔 실행.
  두 도구 루트의 절대경로 프리픽스만 정규화한다.
- **대조 B (정규화 0회, 주 증거)** — `/private/tmp/op118w14/run`이라는 **단일 절대경로**에 base 트리를 두고
  capture → 같은 경로에 변경된 코드 파일만 덮어쓴 뒤 재capture. 도구 루트 절대경로가 양쪽 동일하므로
  **`sed` 정규화 없이 `cmp`로 바이트 동일을 직접 판정**한다. 데이터 루트는 역시 허브로 고정.

대조 B가 C-1의 상위 증거다. 대조 A는 PLAN 원문 절차와의 접점을 유지하기 위해 병기한다.

### 0.2 [MUST] C-1 대조 범위에서 제외한 표면 (PM 확정 해석)

이 태스크는 설계상 **신규 CLI 표면**을 추가했다 — `worktree-tool finalize`,
`state-tool finalize-attribution`, `memory-tool --task-path`/`--body-sha256`, `brain-tool --allocator-root`.
argparse는 서브명령·플래그가 늘면 `usage:` 줄과 `--help` 출력이 필연적으로 달라진다.

따라서 아래는 대조 대상에서 **제외**한다. 근거: C-1의 "바이트 동일"은 **기존 동작 경로의 출력**을 뜻하며,
의도적으로 신설한 인터페이스 표면의 증가를 회귀로 판정하면 AC-6·AC-10·AC-11 자체와 모순된다.

- argparse `usage:` 줄과 `--help` 출력
- 인자 없는 호출 및 오용(잘못된 서브명령·누락 인자) 호출

제외하지 않은 것: **기존 서브명령을 기존 인자로 호출했을 때의 stdout·stderr·exit code 전부.**

---

## 1. 대조 B — 비워크트리 바이트 동일 (S-23 / AC-15 / C-1) · 근거 등급 E1

**실행 스코프**: 모든 명령의 cwd = 허브 루트(`/Volumes/.../ai-framework`), `--wt` 미사용, 비워크트리 경로.
도구 루트 = `/private/tmp/op118w14/run`(양쪽 동일). 데이터 인자는 전부 허브 절대경로.

판정 방법: `cmp -s <base> <new>` (stdout·stderr 각각) + exit code 일치.
**정규화 0회.**

| # | 실행 명령 (cwd = 허브) | stdout | stderr | exit(전/후) | stdout 바이트 |
|---|---|---|---|---|---|
| 1 | `node <R>/opal/tools/code-scan/code-scan.js scan` | IDENTICAL | IDENTICAL | 0 / 0 | 81,189 |
| 2 | `node <R>/opal/tools/code-scan/code-scan.js search worktree` | IDENTICAL | IDENTICAL | 0 / 0 | 3,536 |
| 3 | `node <R>/opal/tools/code-scan/code-scan.js summary` | IDENTICAL | IDENTICAL | 0 / 0 | 1,424 |
| 4 | `node <R>/opal/tools/code-scan/code-scan.js depends state_tool` | IDENTICAL | IDENTICAL | 0 / 0 | 134 |
| 5 | `<R>/opal/tools/event-loader/run.sh load --event session.assistant --project-root <HUB>` | IDENTICAL | IDENTICAL | 0 / 0 | 23,972 |
| 6 | `<R>/opal/tools/event-loader/run.sh load --event session.project --project-root <HUB>` | IDENTICAL | IDENTICAL | 0 / 0 | 844 |
| 7 | `<R>/opal/tools/event-loader/run.sh load --event pm.activate --project-root <HUB>` | IDENTICAL | IDENTICAL | 0 / 0 | 119,588 |
| 8 | `<R>/opal/tools/brain-tool/run.sh search worktree --brain-path <HUB>/.opal/brain` | IDENTICAL | IDENTICAL | 0 / 0 | 3,512 |
| 9 | `<R>/opal/tools/brain-tool/run.sh search 루트 --brain-path <HUB>/.opal/brain` | IDENTICAL | IDENTICAL | 0 / 0 | 4,876 |
| 10 | `<R>/opal/tools/brain-tool/run.sh search 태스크 --brain-path <HUB>/.opal/brain` | IDENTICAL | IDENTICAL | 0 / 0 | 5,045 |
| 11 | `<R>/opal/tools/state-tool/run.sh show <HUB-task-118>` | IDENTICAL | IDENTICAL | 0 / 0 | 1,639 |
| 12 | `<R>/opal/tools/state-tool/run.sh show <HUB-task-118> --format json` | IDENTICAL | IDENTICAL | 0 / 0 | 6,130 |
| 13 | `<R>/opal/tools/state-tool/run.sh show <HUB-task-118> --format full` | IDENTICAL | IDENTICAL | 0 / 0 | 463 |
| 14 | `<R>/opal/tools/state-tool/run.sh boot-summary <HUB>` | IDENTICAL | IDENTICAL | 0 / 0 | 180 |
| 15 | `<R>/opal/tools/memory-tool/run.sh show --file <HUB>/.opal/MEMORY.json` | IDENTICAL | IDENTICAL | 0 / 0 | 3,055 |
| 16 | `<R>/opal/tools/memory-tool/run.sh show --file <HUB>/.opal/MEMORY.json --brief` | IDENTICAL | IDENTICAL | 0 / 0 | 1,746 |
| 17 | `<R>/opal/tools/memory-tool/run.sh show --file <HUB>/.opal/MEMORY.json --boot-brief` | IDENTICAL | IDENTICAL | 0 / 0 | 692 |
| 18 | `<R>/opal/tools/worktree-tool/run.sh list --project-root <HUB>` | IDENTICAL | IDENTICAL | 0 / 0 | 609 |
| 19 | `<R>/opal/tools/worktree-tool/run.sh status --project-root <HUB> --task 118` | IDENTICAL | IDENTICAL | 0 / 0 | 502 |

**판정: 19/19 명령에서 stdout·stderr 모두 바이트 동일, exit code 전부 일치. 정규화 0회. 차이 0줄. → C-1 충족.**

스왑한 코드 파일(총 11건): `code-scan.js`, `event_loader.py`, `brain_tool.py`, `state_tool.py`,
`state.schema.json`, `memory_tool.py`, `worktree_tool.py`, `dashboard/backend/{scanner.py, routers/doctor.py,
routers/tasks.py}`, 그리고 `dashboard/backend/paths.py` **삭제** 반영.

### 1.1 대조 A (PLAN 원문 절차 접점, 정규화 1회)

같은 19개 중 15개 명령을 base clone 도구 루트 ↔ 워크트리 도구 루트로 실행하고
**두 도구 루트 절대경로 프리픽스만** `sed` 정규화했다. 결과: **15/15 diff 0줄, exit code 전부 일치.**

`event-loader load --event session.assistant`만 정규화 전 바이트 수가 달라(17,970 → 18,322 chars, +352)
정규화가 실차이를 가리는지 산술 검증했다.

```
도구 루트 길이 차: 70 - 26 = 44 bytes/occurrence
출력 내 출현 횟수: base 8회, new 8회
예측 델타: 8 × 44 = 352  ==  실측 델타 352
정규화 후 문자열 동일: True
```

**+352 바이트가 경로 프리픽스 치환으로 전량 설명된다. 경로 외 차이 0.**

### 1.2 선행 워커 개별 증거 (재검증 아님 — 인용)

각 축의 C-1은 담당 워커가 이미 개별 실증했고, W-14는 전 축 통합 대조를 담당한다.

| 축 | 선행 증거 | W-14 대조 B 결과 |
|---|---|---|
| event-loader | 허브 cwd 파일 스왑 `session.assistant` BYTE-IDENTICAL(25,010B), `pm.activate`·`session.project`·`pilot.start` 동일 | #5·#6·#7 IDENTICAL |
| code-scan | `scan`·`search` stdout·stderr 4개 diff exit 0 | #1~#4 IDENTICAL |
| brain-tool | 허브 `search` 3키워드 `cmp` 바이트 동일(3,512 / 4,357 / 4,123 B) | #8~#10 IDENTICAL |
| memory-tool | 허브 16개 명령 diff 0 | #15~#17 IDENTICAL |
| state-tool | base/현재 코드 동일 fixture 6명령 diff 0 | #11~#14 IDENTICAL |
| worktree-tool | — | #18·#19 IDENTICAL |

---

## 2. install 경유 source→installed 동치 (S-24 / AC-15 / C-2) · 근거 등급 E1

### 2.1 [MUST] 실행 방식과 그 사유 — 실 `~/.opal/` 미배포

**실행한 것**: 워크트리 소스에서 `scripts/install-mac.sh`를 **격리 HOME**
(`HOME=/private/tmp/op118w14/home`, `OPAL_AUTO_INSTALL=1`)으로 실제 실행 → exit 0.
배포본은 `/private/tmp/op118w14/home/.opal/`.

**실 `~/.opal/`에 배포하지 않은 사유 (릴리스 선결 조건 — PM 판단 필요)**:

- 워크트리 브랜치 base는 `e8b6c4f`이고, **허브 `main`은 `5227f65`로 이미 앞서 있다**.
- 그 델타에 **OP-TASK-117**이 포함되며, 117은 `opal/tools/event-loader/event_loader.py`를 **+146줄** 변경했다.
- 현재 배포본 `~/.opal/tools/event-loader/event_loader.py`의 md5는 `fdcbb20d…`로 **`main`(5227f65) 판본과 일치**한다.
  워크트리 판본은 `6fa5b342…`, base 판본은 `1d04c256…`로 **셋이 모두 다르다**.
- `install_opal()`은 `clean_dirs=(skills agents references templates tools dashboard-server)`를
  `rm -rf` 한 뒤 복사한다. 즉 워크트리에서 install하면 **117이 배포한 event-loader가 조용히 롤백된다.**
- 이는 그 자체로 실행 환경의 C-1 위반(= `session.assistant` 출력 변화)을 만든다.

→ **릴리스 선결 조건: `feat/OP-TASK-118`을 `main`(5227f65) 위로 rebase/merge한 뒤에만 실 `~/.opal/` install을 수행한다.**
이 조건이 충족되기 전의 실 배포는 회귀를 만든다. W-14는 이 조건을 검증 결과로 보고하며,
소스 수정·rebase·커밋은 수행하지 않았다(커밋 금지 · PLAN 범위 밖).

> 참고: `install_opal()`은 `opal_home`을 `"$USER_HOME/.opal"`로 **하드코딩**하므로 `OPAL_HOME` 환경변수로는
> 대상 경로를 바꿀 수 없다(`OPAL_HOME`은 `record_installed_version()`에서만 참조된다).
> 격리는 `HOME` 치환으로만 가능하다 — 이 사실 자체가 install 스크립트의 관찰된 동작이다.

### 2.2 배포 누락 파일 — 0건

| 검사 | 결과 |
|---|---|
| **신설 `harness/done-template.md` 배포** | **배포됨** — `<deploy>/references/harness/done-template.md`, 소스와 내용 동일 |
| `harness/worktree.md` 배포 | 배포됨, 소스와 내용 동일 |
| `opal/core/references/harness/` 파일 목록 소스 ↔ 배포본 | `diff` 0줄 (**완전 동일**) |
| `opal/tools/` 전체 파일 목록 소스 ↔ 배포본 (`find -type f`) | `diff` 0줄 (**완전 동일**) |

`install_opal_references()`는 `cp -Rf "$ref_src"/. "$ref_dst"/`로 **`references/` 트리를 통째로 복사**한다.
파일 목록을 명시하지 않으므로 `harness/` 하위 신규 파일은 자동으로 배포된다 —
**`done-template.md` 배포 누락은 발생하지 않는다. blocker 아님.**

### 2.3 삭제 파일 2건의 배포본 반영 — stale 잔존 0건

| 삭제된 소스 파일 | 배포본 상태 | 판정 |
|---|---|---|
| `opal/core/references/hub-root-cases.json` | `<deploy>/references/hub-root-cases.json` **부재** | 삭제 전파됨 |
| `dashboard/backend/paths.py` | `<deploy>/dashboard-server/dashboard/backend/paths.py` **부재** | 삭제 전파됨 |

전파 메커니즘: `clean_dirs`가 `references`·`dashboard-server`를 `rm -rf` 후 재복사하므로
소스에서 사라진 파일은 배포본에도 남지 않는다. **stale 잔존 0건.**

> 참고(현행 실 배포본): 실 `~/.opal/references/hub-root-cases.json`과
> `~/.opal/dashboard-server/dashboard/backend/paths.py`는 아직 존재한다 — 118이 실 배포되지 않았기 때문이며
> (§2.1), 정상이다. 실 install 시점에 위 메커니즘으로 함께 제거된다.

### 2.4 source→installed 출력 동치

배포본 경로(`<deploy>/tools/*/run.sh`)로 §1과 같은 명령 15개를 허브 cwd에서 재실행하고
소스 실행 출력과 `cmp`했다.

| 결과 | 건수 |
|---|---|
| stdout **바이트 동일** | 13 / 15 |
| 구조적 동치 (경로 프리픽스·토큰 라벨만 상이) | 2 / 15 (`event-loader load` 2건) |
| exit code 불일치 | 0 |

`event-loader`의 2건은 **코드가 아니라 루트 해석 표면의 차이**이며, 관찰 가능한 산출물은 전부 일치한다.

```
document_count      3 == 3
payload_bytes   10335 == 10335
missing_optional   [] == []
manifest_sha256      동일
receipt documents (id, bytes, sha256):
  agent-kernel  6679 == 6679   8ef356710f02 == 8ef356710f02   MATCH
  principles    2695 == 2695   daf7d5c45c26 == daf7d5c45c26   MATCH
  identity       961 ==  961   6f258405dbca == 6f258405dbca   MATCH
문서 id 집합 동일: True
전체 문서 content 바이트 동일: True
```

남는 차이는 2종뿐이다.

1. `manifest_path`·`path` 필드의 **루트 프리픽스** (`<source>/opal/core/references` ↔ `<deploy>/references`).
2. `token` 라벨 `{source_root}/opal/core/AGENT.md` ↔ `{deployed_root}/AGENT.md`
   — event-loader의 **설계된 이중 루트 해석**이다. 소스 체크아웃에서 실행하면 `{source_root}`,
   배포본에서 실행하면 `{deployed_root}`로 해석한다. base 코드와 변경 후 코드가 이 동작에서
   동일함은 §1 #5~#7(IDENTICAL)로 이미 실증됐다. **배포 결함이 아니다.**

측정 중 관찰된 fixture 한계 1건: 격리 HOME에는 사용자 데이터인 `identity.md`가 없어
최초 실행에서 `missing_optional_documents: ['identity']`가 나왔다. `identity.md`는 install이 생성하지 않고
**보존**하는 사용자 데이터이므로(실 `~/.opal/identity.md` 961B 존재 확인), 실 `~/.opal` 상태를 모사하기 위해
시드한 뒤 재측정했고 위 표가 그 결과다. **배포 누락이 아니다.**

### 2.5 `~/.opal/` 직접 편집 흔적 — 0건

W-14는 배포본을 한 건도 손으로 편집하지 않았다. 배포본 갱신은 `install-mac.sh` 실행 경로로만 수행했다.
실 `~/.opal/`은 이 Work item에서 **읽기만** 했다(md5 대조·`identity.md` 복사·존재 확인).

### 2.6 install 부작용 1건 — 조치 완료

`OPAL_AUTO_INSTALL=1` 경로가 `install_dashboard` → `console_autostart`까지 수행해
격리 HOME의 Console 데몬이 **127.0.0.1:7823을 점유**했다(PID 7153).
install 로그상 기동 전 실행 중인 데몬은 없었으므로 사용자 데몬을 교체하지는 않았다.
측정 종료 후 **종료 처리했고 포트 해제를 `lsof`로 확인**했다.

---

## 3. 스위트 재확인과 "실패처럼 보이는 것" 판별

PM 제공 기준선과 대조했다. 스위트 소유권은 W-4~W-13에 있고 W-14는 측정·판정만 한다.

| 스위트 | 실행 위치 | 결과 | 판정 |
|---|---|---|---|
| `state-tool` | 워크트리 | **425 passed / 3 skipped** | green (기준선 404보다 증가, 실패 0) |
| `memory-tool` | 워크트리 | **202 passed** | green, 기준선 일치 |
| `brain-tool` | 워크트리 | **156 passed** | green, 기준선 일치 |
| `code-scan test-hub-root.js` | 워크트리 | exit 0 | green |
| `code-scan test-scan-root-landing.js` | 워크트리 | exit 0 | green |
| `worktree-tool` | 워크트리 | **74 passed / 1 failed** | 기준선 일치 — 선존재 실패, 범위 밖(아래 3.1) |
| `event-loader` | 워크트리 | 1 failed / 11 passed | **환경 인공물** — 118 무관(아래 3.2) |
| Console BE | `/private/tmp` fixture | 36 failed / 340 passed | **fixture 제약** — base와 실패 집합 완전 동일(아래 3.3) |

### 3.1 `worktree-tool` 1 failed — 선존재, Phase 2 이연

`test_s24_pipeline_flag_flows_from_create_into_state` — `harness/task-process.md`에 `worktree-tool create`
문안이 없어 실패한다. 제안서 §6.1 순서 재정렬이 Phase 2 이연이므로 이 태스크 범위 밖이다. **수정하지 않았다.**

### 3.2 `event-loader` 1 failed — sparse cone 인공물, 118 회귀 아님

`test_event_loader_extended.py::test_every_event_loads_and_its_receipt_verifies[event='pm.activate']`가
워크트리에서 실행하면 `document_not_found: {project_root}/.opal/AGENT.md`로 실패한다.
이 테스트는 `--project-root REPO_ROOT`를 쓰는데, **워크트리 sparse cone이
`.opal/`·`tasks/`를 제외**하므로(`sparse-checkout list` = cursor-rules, dashboard, docs, opal, scripts, skills)
해당 루트에 `.opal/AGENT.md`가 물리적으로 없다.

코드 회귀가 아님을 통제 실험으로 확정했다 — **project-root를 고정하면 base와 변경 후가 동일 동작**이다.

| 케이스 | base 코드 | 변경 후 코드 | 판정 |
|---|---|---|---|
| A. project-root에 `.opal/AGENT.md` **존재** | exit 0, 119,454 B | exit 0, 119,454 B | **stdout 바이트 동일** |
| B. project-root에 `.opal/` **부재** | exit 1 `document_not_found` | exit 1 `document_not_found` | **동일 실패, 동일 detail** |

그리고 base 코드 + base 테스트를 `.opal/`이 없는 루트에서 돌리면 **같은 실패가 재현된다**
(`1 failed, 8 passed`). → **선존재 환경 제약이며 118이 만든 것이 아니다.**

cone이 완전한 루트에서 118 스위트를 돌리면 **11 passed / 0 failed**다.
같은 루트에서 event-loader만 base 코드로 되돌리면 118의 신규 테스트
`test_project_root_worktree_own_opal_not_hub`가 **실패**한다 — RED→GREEN이 정상 성립한다.

> 운영 함의(W-6 소관, 정보성): 118의 event-loader 스위트는 `.opal/`을 제외한 sparse cone 내부에서는
> 실행할 수 없다. 실행은 cone이 완전한 루트에서 해야 한다.

### 3.3 Console BE 36 failed — fixture 제약, 실패 집합이 base와 완전 동일

워크트리에서는 `tasks/`가 cone 밖이라 **collection 단계에서 error**로 중단된다
(`[FIX-PIN] _t103_find_task_id(prefix='091') 매칭 0건`). 그래서 cone이 완전한 `/private/tmp` fixture에서 측정했다.

| 측정 | passed | failed |
|---|---|---|
| base (`e8b6c4f` pristine clone) | 347 | 36 |
| 변경 후 (동일 fixture, 118 코드·테스트) | 340 | 36 |

**실패 테스트 ID 집합을 정렬해 `diff`한 결과 0줄 — base와 완전히 같은 36건이다.**
이 36건은 `/private/tmp`가 Console `scan_roots`(`$HOME/workspace` 하위) 제약을 벗어나 생기는 fixture 인공물이며
118과 무관하다.

passed 증분 **347 → 340 = −7**은 PM 실측 증분과 정확히 일치한다
(`test_paths.py` 제거 −9 + S-16 신규 +2 = −7). W-9의 shadow cone 실측(**376 passed / 0 failed**)이
Console BE의 green 증거이며, W-14는 그 증분이 산술적으로 설명됨을 확인했다.

---

## 4. 실패 복구 기준 (PLAN §Release and recovery 매핑)

**어느 캡처가 어긋나면 어느 W로 되돌리는가.** P2의 W들은 파일이 겹치지 않으므로 개별 revert가 가능하다.

| 어긋난 캡처 | 소관 W | 되돌릴 대상 | 비고 |
|---|---|---|---|
| §1 #1~#4 `code-scan scan/search/summary/depends` | **W-8** | `opal/tools/code-scan/code-scan.js` + 스위트 | 단독 revert 가능 |
| §1 #5~#7 `event-loader load` | **W-6** | `opal/tools/event-loader/event_loader.py` + 스위트 | 단독 revert 가능 |
| §1 #8~#10 `brain-tool search` | **W-7** | `opal/tools/brain-tool/brain_tool.py` + 스위트 | 단독 revert 가능 |
| §1 #11~#14 `state-tool show/boot-summary` | **W-4** | `opal/tools/state-tool/state_tool.py` + 스키마 | H-1 직결 — CLOSE mark·MEMORY history 동반 확인 |
| §1 #15~#17 `memory-tool show` | **W-5** | `opal/tools/memory-tool/memory_tool.py` | 단독 revert 가능 |
| §1 #18~#19 `worktree-tool list/status` | **W-3 · W-10** | `opal/tools/worktree-tool/worktree_tool.py` | 발급원(W-3)과 재진입 계약(W-10)을 함께 판정 |
| Console BE 스위트 회귀 | **W-9** | `dashboard/backend/{scanner.py, routers/*.py}` + `paths.py` 삭제 되돌림 | AC-14 resolver 화이트리스트 동반 확인 |
| 골든표 관련 실패 (W-11 이후) | **W-11 + 해당 소비 스위트 W** | `hub-root-cases.json` 삭제 되돌림 **및** W-6~W-9 스위트 | **W-11 단독 revert로는 복구되지 않는다** — 소비 스위트가 이미 교체됐기 때문. 반드시 함께 되돌린다 |
| `finalize`가 `attribution_pending`에 갇힘 | **W-10** | revert 아님 | 판정 로그의 위반 경로 목록으로 선언 집합(DONE.md `## 회고적 학습 후보`)을 보정해 재실행. **`--force`로 우회하지 않는다** |
| install 후 문제 발견 | — | **소스를 이전 커밋으로 되돌린 뒤 재-install** | 배포본만 롤백하는 조치는 하지 않는다(C-2) |

추가 복구 기준(W-14 측정으로 확정):

- **§2.1의 rebase 선결 조건이 지켜지지 않은 채 실 install이 수행되면** → `~/.opal`이 117 이전 event-loader로
  롤백된다. 조치는 배포본 수정이 아니라 **`main` 위로 rebase 후 재-install**이다(C-2).
- §2.2 `done-template.md`가 배포본에 없으면 → **W-13** 소관(문서 신설 위치)과 install 참조 복사 경로를 함께 본다.
  현 측정에서는 정상 배포되므로 해당 없음.

---

## 5. fixture 잔여물과 허브 무결성 (C-3)

### 5.1 사용한 임시 자원 — 전부 `/private/tmp` 하위

| 경로 | 용도 |
|---|---|
| `/private/tmp/op118w14/base` | `e8b6c4f` disposable clone (`--no-hardlinks`) |
| `/private/tmp/op118w14/run` | 코드 스왑 대조 B 고정 루트 |
| `/private/tmp/op118w14/sparse` | sparse cone 모사 통제 실험 |
| `/private/tmp/op118w14/home` | 격리 HOME install 대상 |
| `/private/tmp/op118w14/{out,out2,out3,suites}` | 캡처·로그 |

- 모든 git 조작은 **`git -C <dir>`** 형태로만 수행했다. `cd <dir> && git ...` 형태는 쓰지 않았다.
- **운영 `.opal-worktrees/` 하위에 fixture worktree를 만들지 않았다.**
- 운영 허브에 대한 명령은 전부 **읽기 전용**이다(`scan`·`search`·`show`·`list`·`status`·`load`).
  `code-scan scan`이 읽기 전용임은 base clone에서 실행 후 `git status`가 clean인 것으로 확인했다.

### 5.2 허브 무결성 실증

측정 전후로 `git -C <hub> worktree list` 결과가 동일하다 — **fixture worktree 0건 생성.**

```
/Volumes/Data/AIStudio/workspace/ai-framework                           5227f65 [main]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_115  0806bd0 [feat/OP-TASK-115]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_116  8824419 [feat/OP-TASK-116]
/Volumes/Data/AIStudio/workspace/ai-framework/.opal-worktrees/task_118  e8b6c4f [feat/OP-TASK-118]
```

`.opal-worktrees/` 디렉터리 실체도 `task_115`·`task_116`·`task_118` 3건뿐이다.
워크트리 브랜치는 `feat/OP-TASK-118`, HEAD `e8b6c4f`로 변동 없다.
잔여물 삭제와 0건 실증은 §6에 기록한다.

---

## 6. 잔여물 삭제 실증

측정 종료 후 fixture 루트를 전량 삭제하고 잔여 0건을 확인했다.

```
$ rm -rf /private/tmp/op118w14            # exit 0
$ ls -la /private/tmp/op118w14
ls: /private/tmp/op118w14: No such file or directory

$ ps -ax -o pid,command | grep op118w14 | grep -v grep
(출력 없음 — 잔여 프로세스 0건)

$ lsof -nP -iTCP:7823 -sTCP:LISTEN
(출력 없음 — 포트 해제됨, §2.6 데몬 종료 확인)

$ git -C <hub> worktree list
/Volumes/.../ai-framework                           5227f65 [main]
/Volumes/.../ai-framework/.opal-worktrees/task_115  0806bd0 [feat/OP-TASK-115]
/Volumes/.../ai-framework/.opal-worktrees/task_116  8824419 [feat/OP-TASK-116]
/Volumes/.../ai-framework/.opal-worktrees/task_118  e8b6c4f [feat/OP-TASK-118]

$ ls -1 <hub>/.opal-worktrees
task_115
task_116
task_118
```

허브 worktree 3건·`.opal-worktrees/` 실체 3건으로 **측정 전과 동일**하다.
워크트리 브랜치 `feat/OP-TASK-118`, HEAD `e8b6c4f`도 변동 없다.

> W-14가 만들지 않은 선존재 임시 파일 2건이 `/private/tmp`에 남아 있다 —
> `op118-scen.json`, `op118-scen2.json`. 선행 워커의 산출물이므로 W-14는 삭제하지 않았다.

---

## 7. 최종 판정

| 완료 기준 | 시나리오 | 판정 | 근거 |
|---|---|---|---|
| **C-1** 비워크트리 출력 바이트 동일 | S-23 | **충족** | §1 — 19/19 명령 stdout·stderr 바이트 동일, 정규화 0회, exit 전부 일치 |
| **C-2** `~/.opal/` 직접 편집 금지 · install 경유 배포 | S-24 | **충족(조건부)** | §2.2~§2.5 — 배포 누락 0건, 삭제 전파 확인, 직접 편집 0건. **단, §2.1 rebase 선결 조건 미충족 상태에서 실 배포는 금지** |
| **C-3** disposable fixture · 운영 cone 미활성화 | — | **충족** | §5 — 전부 `/private/tmp` 하위, 허브 worktree 3건 불변 |
| **AC-15** 비워크트리 회귀 증거 제출 | S-23, S-24 | **충족** | 이 문서 |

**C-1 위반 0건. 배포 누락 0건. stale 잔존 0건.**

**PM 결정 필요 1건**: §2.1 — `feat/OP-TASK-118`이 `main`(5227f65, OP-TASK-117 포함)보다 뒤에 있어
현 상태로 실 `~/.opal/` install을 수행하면 117의 event-loader 배포본이 롤백된다.
실 배포 전 rebase/merge가 선결 조건이다. W-14는 커밋·rebase를 수행하지 않았다.
