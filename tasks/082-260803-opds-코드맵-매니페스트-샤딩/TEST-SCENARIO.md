# TEST SCENARIO: code-scan 매니페스트 샤딩 — 파일 크기 상한 기반 분산 구조

> 작성일: 2026-08-03 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표 기반
> 작성자 분리: PLAN 워커(opal-plan-agent) ≠ 본 문서 작성자(PM) — self-confirming 방지

## 0. 트랙 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| RED-first 트랙 | **적용** | 코드 로직 변경 + 동작검증 필요. `opal/core/references/harness/red-first.md` §하이브리드 분기 — self-confirming 위험 작업 |
| RED 작성 주체 | opal-test-agent (PLAN Step 1~3) | 구현자(opal-task-agent, Step 4~9)와 분리 |
| GREEN 판정 주체 | opal-test-agent (PLAN Step 10) | 생성자≠검증자 |
| M2(E2E 자동화) 의무 | **미발동** | FE 화면·컴포넌트·인증/인가·외부 API 연동 변경 0건 (변경 대상은 로컬 CLI 단일 파일). `test-scenario-guide.md` §Step 3-b 트리거 미해당 |
| 실행 방식 | M1 중심 (CLI 블랙박스 테스트) + M3 1건 | 기존 테스트 10종이 전부 `spawnSync` CLI 블랙박스 방식 (`tests/test-validate.js:56-80`) |

---

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-10)를 승계하고, 시나리오 컬럼을 본 문서 기준으로 재매핑했다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `cmdValidate` 구조 패스 (`code-scan.js:1957-1967`) | 매니페스트별 `files_key_added`/`files_key_removed` 판정 → 샤드마다 전량 오탐 | **P0** | L1 + L2 | S-7, S-8, S-9 |
| H-2 | `cmdScaffold` stale 수집 (`code-scan.js:1724-1732`) | `_shards/*.json` 전량 stale → 소유자가 신뢰해 삭제 시 자산 소실 | **P0** | L2 | S-11 |
| H-3 | `mergeManifest` 파일 배치 (`code-scan.js:1600-1627`) | 샤드 소유 키가 베이스로 흘러 샤드에서 pruned → 워커 기입 서술 소실 | **P0** | L1 + L2 | S-12, S-13, S-14 |
| H-4 | `resolveHeader` `package` 3단 상속 (`code-scan.js:1038,1048`) | `_source`/`_sources` 출력 토큰 변화 → 조회 8커맨드 골든 파손 | **P0** | L2 | S-2, S-19 |
| H-5 | `decideTarget` 매니페스트 로딩 신설 (`code-scan.js:1083-1111`) | 파손 매니페스트에서 `manifest_parse_failed` 신규 노출 → `target` exit 1 | P1 | L2 | S-6 |
| H-6 | 크기 상한 도입 | 차단으로 걸면 초과 보유 프로젝트의 CLOSE 게이트 즉시 전면 봉쇄 | **P0** | L1 + L2 | S-15, S-16, S-24 |
| H-6b | **상한 검사가 샤드 파일을 누락** | 베이스만 측정하고 샤드를 빼면 샤드가 재비대해도 도구가 침묵 — 태스크가 막으려던 사고 경로가 그대로 열린다 | **P0** | L1 | S-25 |
| H-7 | `_shards` 예약어 | 동명 소스 디렉토리 존재 시 하위 디렉토리 매니페스트가 조용히 덮인다 | P1 | L2 | S-18 |
| H-8 | `resolveShards` 모드 게이트 | 게이트 부재 시 inline 모드에서 샤드를 읽어 "inline 무영향" 계약 파손 | P1 | L2 | S-20 |
| H-9 | 샤드 라벨 → 경로 파생 | 라벨에 `/`·`..` 포함 시 code-map 밖으로 쓰기 경로 이탈 (path traversal) | **P0** | L1 | S-3 |
| H-10 | `CODE_MAP_VERSION` 상향 유혹 | 상향 시 기존 전 자산이 `unsupported_version`으로 즉시 차단 | **P0** | L1 | S-4 |
| H-11 | **목표 미달성 — 분산해도 크기가 안 내려감** | 샤드로 쪼갰는데 베이스가 여전히 상한 초과이거나 조회가 깨지면 태스크 목표 자체가 미달성 | **P0** | L2 | **S-23** |
| H-12 | **봉인 훼손** | 소비처마다 샤드 로딩을 인라인 복제 → 판정 지점이 5곳으로 분산되어 080 봉인 구조 붕괴 | 중 | L1 | S-21 |
| H-13 | **다중 스코프 상태 누수** | `visitedShards` 스코프별 리셋 누락·`shardViews` 캐시 교차 오염·`--scope` 필터 오작동 — 단일 스코프 픽스처에서는 발현하지 않는다 | 중 | L2 | S-26 |

> H-11·H-12는 PM이 추가했다. H-11은 PLAN TS-001~TS-036이 전부 컴포넌트 단위여서 "목표를 달성했는가"를 직접 단언하는 시나리오가 없었기 때문이고(scenario-gate ①축), H-12는 PLAN §9 R-9가 리스크로만 있고 시나리오가 없었기 때문이다.
>
> **H-6b·H-13은 목표-커버 게이트 1회차(`SCENARIO-GATE-1.md`, verdict pass 2/2/2) 평가자 gaps 반영으로 추가했다.** H-6b(G-1 강권)는 상한 픽스처가 베이스 초과만 다뤄 "샤드 재비대"라는 태스크의 주적(TASK 확정 방향 #4)이 검증 사각이었기 때문이고, H-13(G-4)은 전 픽스처가 단일 스코프여서 스코프 간 상태 누수가 발현하지 않기 때문이다. 게이트 재호출은 하지 않았다 — 판단축이 이미 만점(각 2/2)이고 본 반영은 시나리오 **추가**뿐이라 커버리지가 단조 증가하므로 재채점이 verdict를 낮출 수 없다.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 이 태스크는 DB가 없다. "테이블" 자리에 **픽스처 트리**를 둔다.

| 픽스처 트리 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| `tests/fixtures/shard-repo/` | 정상 샤드 구성 | 베이스 1(`shards:["core","pricing"]`) + 샤드 2 + 소스 4파일. 샤드 `core.json`에 `package` 보유 | fixture (Step 1 신규) |
| `tests/fixtures/shard-violations/duplicate-key/` | 중복 키 | 같은 basename이 베이스와 샤드에 각 1회 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/shard-missing/` | 선언·파일 부재 | `shards`에 라벨 선언, 해당 `_shards/*.json` 미존재 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/undeclared/` | 미선언 샤드 | `_shards/orphan.json` 존재, 베이스 `shards`에 없음 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/dir-mismatch/` | 샤드 dir 불일치 | 샤드 `dir`이 베이스와 다른 값 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/reserved-name/` | 예약어 충돌 | 소스에 `_shards` 디렉토리 존재 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/oversize/` | 상한 초과 | `index.json`에 `manifestMaxBytes: 200`, 베이스가 200바이트 초과 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/bad-label/` | 악성 라벨 | `shards: ["../escape"]`, `["a/b"]`, `["Core"]` 3변형 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/broken-base/` | 파손 베이스 | 베이스 JSON 문법 오류 | fixture (Step 2 신규) |
| `tests/fixtures/shard-violations/oversize-shard/` | **샤드 자신 상한 초과** | `manifestMaxBytes:200`, **베이스는 상한 이하이고 샤드 1개가 초과** | fixture (Step 2 신규 — **게이트 gaps G-1**) |
| `tests/fixtures/shard-multi-scope/` | 다중 스코프 샤드 | 스코프 2개가 각각 샤드를 보유. 한쪽에만 미선언 샤드 배치 | fixture (Step 2 신규 — **게이트 gaps G-4**) |
| `tests/fixtures/shard-goal/` | **목표달성 검증용** | 상한 초과 베이스 1개(엔트리 다수) → 샤드 3개로 분산한 사후 상태 + 분산 전 상태. **분산 후 트리는 분산 전 트리에서 테스트 내 스크립트로 파생 생성**한다(수작성 2벌 금지 — 동일성 단언이 도구가 아닌 픽스처 작성자를 시험하는 것을 막는다, 게이트 gaps G-3) | fixture (Step 2 신규 — **PM 추가**) |
| `tests/fixtures/shard-goal/` 중간 상태 2종 | 전이 도중 상태 | (a) 엔트리를 샤드로 옮겼으나 베이스 `shards` 선언 누락 (b) 옮겼으나 베이스에서 제거 안 함(중복) | fixture (Step 2 신규 — **게이트 gaps G-3**) |
| `tests/fixtures/golden/` | 회귀 골든 8파일 | 기존 자산 **무변경** | 기존 (재캡처 금지) |
| 기존 픽스처 전체 | 샤드 미선언 자산 | `shards` 키 0건 — 옵트인 미적용 대조군 | 기존 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | `shard-repo/` 베이스+샤드 2 | `scan --json` | 소스 4파일 전부 헤더 해석, 누락 0 |
| S-2 | `shard-repo/`, 샤드 `core.json`에 `package` | `scan --json --full` | 샤드 소유 키는 샤드 `package`, 미소유 키는 베이스 `package` 상속. `_sources` 토큰은 `'package'` 단일 |
| S-3 | `bad-label/` 3변형 | `scan` / `validate` | `shard_declaration_invalid` exit 1, `.opal/code-map/` 밖 신규 파일 0건 |
| S-4 | 기존 픽스처(샤드 미선언) | `validate` | `unsupported_version` 0건, 소스 상수 `CODE_MAP_VERSION === 1` |
| S-5 | `shard-repo/` | `target <샤드소유파일> --json` / `target <신규파일> --json` | 전자 = 샤드 경로 + `shard` 라벨 / 후자 = 베이스 경로 + `shard` 키 부재 |
| S-6 | `shard-repo/` 및 `broken-base/` | `code-map-hook.js`에 Edit 이벤트 주입 | 엔트리 청결 시 stdout·stderr 0바이트 exit 0 / 미갱신 시 경고에 샤드 경로 / 파손 시 무출력 exit 0 |
| S-7 | `shard-repo/` (디스크 = 합집합) | `validate --json` **및** `validate --changed --json` | 두 모드 모두 `violations` 0건, exit 0 |
| S-8 | `duplicate-key`/`shard-missing`/`undeclared`/`dir-mismatch` | 각 트리에서 `validate --json` | 해당 sub 각 **정확히 1건**, 타 sub 0건. `dir-mismatch`에서 `dir_mismatch`는 0건 |
| S-9 | `shard-repo/`에서 `dir` 디렉토리 제거 | `validate --json` | `orphan:dir_missing` **1건** (샤드 수와 무관) |
| S-10 | `shard-repo/` 샤드 엔트리에 `layer` 주입 | `validate --json` | `layer_in_manifest`가 **그 샤드 경로**에 귀속 |
| S-11 | `shard-repo/` | `scaffold --json` | `stale[]`에 `_shards/*.json` **0건** |
| S-12 | `shard-repo/` | `scaffold` 2회 연속 | 베이스 `shards` 선언·샤드 파일 내용 **바이트 동일** |
| S-13 | `shard-repo/`에 신규 소스 파일 1개 추가 | `scaffold --json` | 베이스 `files{}`에 `draft:true` 추가, `added[]`가 베이스 경로. 샤드 무변화 |
| S-14 | `duplicate-key/` | `scaffold --json` | 디렉토리 skip, `skipped[]`에 `shard_duplicate_key`, 샤드 파일 mtime·내용 무변화 |
| S-15 | `oversize/` (`manifestMaxBytes:200`) | `validate --json` | `manifest_oversize` 열거(경로+`{bytes}/{limit}`), 다른 위반 0건이면 `ok:true` **exit 0** |
| S-16 | `oversize/`에서 `manifestMaxBytes` 상·하향 + **정확히 경계값** | `validate --json` | 작은 값 → 검출, 큰 값 → 0건, 기본값 20480 적용. **`size == limit`은 초과가 아니다**(off-by-one) |
| S-25 | `oversize-shard/` — 베이스 이하, 샤드 1개 초과 | `validate --json` | `manifest_oversize` 1건이고 그 `manifest` 필드가 **샤드 경로**를 가리킨다 |
| S-26 | `shard-multi-scope/` — 스코프 2개 | `validate --json` / `validate --scope <A> --json` | 전체 실행 시 스코프별 판정이 교차 오염 없이 각각 산출되고, `--scope` 지정 시 그 스코프만 검사된다 |
| S-17 | `oversize/` | `scaffold --json` | stderr 1줄 경고, **stdout JSON 무변경** |
| S-18 | `reserved-name/` | `scaffold` / `validate` | `scaffold` = `reserved_name_collision` exit 1 + 매니페스트 미기록 / `validate` = `reserved_name` 검출 |
| S-19 | 기존 픽스처 전체 (샤드 미선언) | 조회 8커맨드 + `target --json` + `scaffold --json` | `tests/fixtures/golden/*` 8파일 및 `target`·`scaffold` stdout **바이트 동일** |
| S-20 | `shard-repo/` + `--header-source inline` | 조회·`validate`·`scaffold` | stdout·stderr **양축**이 샤드 미도입 시와 동일 |
| S-21 | 구현 완료된 `code-scan.js` | 소스 정적 검사(grep) | `_shards` 경로 조립·`byKey` 구성이 `resolveShards` **밖에 0건** |
| S-22 | 구현 완료된 소스·문서 | `code-scan version` + 문서 grep | v1.5.0, 변경이력 `(082)` + KST 포맷, `tools.md`·`header-rules.md` 반영 |
| **S-23** | `shard-goal/` 분산 전(상한 초과 베이스 1개) | 분산 전 트리에서 **스크립트로 파생**한 분산 후 트리 + 중간 상태 2종에서 `validate`·`scan`·`target` 실행 | **① `manifest_oversize` 0건 ② 분산 전후 `scan --json` 엔트리 집합·헤더 값 동일 ③ 전 파일이 소유 샤드로 라우팅 ④ 위반 0건 exit 0 ⑤ 중간 (a)선언 누락에서 `scan`이 엔트리를 조용히 누락하지 않음 ⑥ 중간 (b)중복에서 조회는 승자로 동작** |
| **S-24** | 대규모 code-map 보유 실사용 프로젝트 | 캡틴이 `validate --json` 직접 실행 | 초과 매니페스트 열거가 실제 초과분과 일치하고, 기존 CLOSE 게이트가 봉쇄되지 않음(exit 0 유지) |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 샤드 합집합 해석

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `resolveShards` + `resolveManifestContext` + `resolveHeader` 합집합 경로 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `shard-repo/` — 베이스가 `shards:["core","pricing"]` 선언, 소스 4파일이 베이스·샤드에 분산 등재 |
| 기대 결과 | `scan --json`이 소스 4파일 전부의 헤더를 반환한다. 샤드에 등재된 키가 `uncovered`로 빠지지 않는다 |
| 도구 | `node --test` + `spawnSync` CLI 블랙박스 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test --test-name-pattern="S-1:"` |
| 결과 | Pass |
| 상세 | `[T082/L1-F1] S-1` 1건 GREEN. `shard-repo` fixture로 `scan --json` 실행 — `svc/mod/{A,B,C,D}.ts` 4파일 전부 결과에 존재하고 각 `exports`가 기대값(`['A']`~`['D']`)과 일치. uncovered 누락 0건 확인 |

#### S-2: `package` 3단 상속 + 출처 토큰 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `resolveHeader` `pkgChain` 상속 (`files > 소유 샤드 package > 베이스 package`) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 샤드 `core.json`에 `package.description` 존재, 베이스 `package`에 `depends` 존재 |
| 기대 결과 | 샤드 소유 키는 `description`을 샤드 `package`에서, `depends`를 베이스 `package`에서 상속한다. `_sources` 값은 두 경우 모두 `'package'`이며 새 토큰이 생기지 않는다 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test` (전체 스위트 249건 중 `[T082/L1-F1] S-2` 1건) |
| 결과 | Pass |
| 상세 | `shard-package` 전용 fixture(S-2·S-7 픽스처 분리) — 샤드 `package.description` 우선 상속, 미보유 `depends`는 베이스 `package`에서 상속, `_sources` 값은 두 필드 모두 `'package'` 단일 토큰으로 확인(전체 실행 로그: pass 249/fail 0) |

#### S-3: 샤드 라벨 경로 안전 (path traversal 차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | `SHARD_LABEL_RE` 집행 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `bad-label/` 3변형 — `"../escape"` / `"a/b"` / `"Core"`(대문자) |
| 기대 결과 | 3변형 모두 `shard_declaration_invalid`로 exit 1. `.opal/code-map/` 디렉토리 밖에 신규 파일이 **0건** 생성된다 |
| 도구 | `node --test` + 실행 전후 파일 트리 diff |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F1] S-3 (escape/slash/uppercase)` 3건) |
| 결과 | Pass |
| 상세 | `"../escape"` / `"a/b"` / `"Core"` 3변형 전부 `shard_declaration_invalid`로 exit 1 확인, `.opal/code-map/` 밖 신규 파일 0건(트리 diff assert 포함) |

#### S-4: `CODE_MAP_VERSION` 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `CODE_MAP_VERSION` 상수 + 기존 자산 호환 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 기존 픽스처(모두 `version:1`) |
| 기대 결과 | 소스에서 `CODE_MAP_VERSION = 1`이고, `validate`가 기존 픽스처에서 `unsupported_version`을 발생시키지 않는다 |
| 도구 | `node --test` + 소스 상수 정적 검사 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F1] S-4` 1건) + `grep "CODE_MAP_VERSION" code-scan.js` |
| 결과 | Pass |
| 상세 | `CODE_MAP_VERSION === 1` 확인, 기존 픽스처(전체 `version:1`)에서 `unsupported_version` 0건 |

#### S-5: 기록 위치 샤드 라우팅

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `decideTarget` 2단 라우팅 (U-3 글롭 미채택) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/` — 샤드 보유 키 1개, 어느 매니페스트에도 없는 신규 소스 파일 1개 |
| 기대 결과 | 보유 키 → `manifest`=샤드 경로 + `shard`=라벨. 신규 파일 → `manifest`=베이스 경로이고 `shard` 키가 **없다**. 양쪽 모두 `reason`은 `header_source_manifest` (3값 도메인 유지) |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F2] S-5` 1건) |
| 결과 | Pass |
| 상세 | 샤드 보유 키 → `manifest`=샤드 경로 + `shard`=라벨. 신규 파일 → `manifest`=베이스 경로 + `shard` 키 부재. 양쪽 모두 `reason`=`header_source_manifest` 확인 |

#### S-8: 샤드 고유 위반 4종 — 각 정확히 1건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `validate` Phase B·C 신규 sub 4종 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `duplicate-key`/`shard-missing`/`undeclared`/`dir-mismatch` 4트리. 각 트리는 나머지 조건이 정상(교차 오염 없음) |
| 기대 결과 | 각각 `shard_duplicate_key` / `orphan:shard_missing` / `shard_undeclared` / `shard_dir_mismatch`가 **정확히 1건**. 특히 `dir-mismatch` 트리에서 기존 `dir_mismatch` sub는 **0건**이어야 한다(샤드는 미러 경로가 베이스이므로 기존 판정을 쓰면 항상 위반) |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F3] S-8 (duplicate-key/shard-missing/undeclared/dir-mismatch)` 4건) |
| 결과 | Pass |
| 상세 | 4트리 각각 `shard_duplicate_key`/`orphan:shard_missing`/`shard_undeclared`/`shard_dir_mismatch`가 정확히 1건. `dir-mismatch` 트리에서 기존 `dir_mismatch` sub 0건 확인(교차 오염 없음) |

#### S-9: 오탐 증폭 차단 (`orphan:dir_missing` 1건)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | Phase B 검사 4 — 베이스 1회 판정 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/`에서 `dir`이 가리키는 소스 디렉토리를 제거 (샤드 2개 존재 상태) |
| 기대 결과 | `orphan:dir_missing`이 **1건**. 샤드 수만큼 늘어나지 않는다 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F3] S-9` 1건) |
| 결과 | Pass |
| 상세 | `dir` 소스 디렉토리 제거(샤드 2개 존재) 상태에서 `orphan:dir_missing`이 정확히 1건(샤드 수만큼 증폭되지 않음) |

#### S-10: 샤드 엔트리 침범 귀속

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | Phase B 검사 11 — `layer`/`domain`/`module` 침범을 각 매니페스트에 반복 적용 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 샤드 `pricing.json`의 한 엔트리에 `layer` 주입 |
| 기대 결과 | `worker_scope_violation:layer_in_manifest`의 `manifest` 필드가 **샤드 경로**를 가리킨다 (베이스가 아님) |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F3] S-10` 1건) |
| 결과 | Pass |
| 상세 | `pricing.json` 샤드 엔트리에 `layer` 주입 시 `worker_scope_violation:layer_in_manifest`의 `manifest` 필드가 샤드 경로를 가리킴(베이스 아님) 확인 |

#### S-15: 크기 상한 감지 + 비차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `manifest_oversize` 열거 + 차단 필터 제외 (U-2) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `oversize/` — `manifestMaxBytes:200`, 베이스가 200바이트 초과, 다른 위반 0건 |
| 기대 결과 | `violations[]`에 `{code:'manifest_oversize', manifest, detail:'{bytes}/{limit}'}`가 실리고 `counts.manifest_oversize`가 일치한다. 그럼에도 `ok:true`이고 **exit 0**이다 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F5] S-15` 1건) + 독립 재현 스크립트(scratchpad) |
| 결과 | Pass |
| 상세 | `oversize/`(`manifestMaxBytes:200`, 베이스 200바이트 초과) — `violations[]`에 `{code:'manifest_oversize', manifest, detail:'{bytes}/{limit}'}` 실림 + `counts.manifest_oversize` 일치, `ok:true` exit 0 확인(비차단) |

#### S-16: 상한 설정 오버라이드

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `index.json` 최상위 `manifestMaxBytes` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | 동일 자산에 `manifestMaxBytes`를 (a) 작게 (b) 크게 (c) 미지정 (d) **파일 크기와 정확히 같은 값** 4변형 |
| 기대 결과 | (a) 검출 (b) 0건 (c) 내장 기본값 20480 적용 (d) **`size == limit`은 초과가 아니므로 0건**(off-by-one, 게이트 gaps G-5). 타입 위반(문자열·음수)은 `invalid_index` 처리 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F5] S-16 (a/b/c/d/d2/e)` 6건) |
| 결과 | Pass |
| 상세 | (a)작은 값→검출 (b)큰 값→0건 (c)미지정→기본값 20480 적용 (d)`size==limit` 경계값→초과 아님(off-by-one 확인, 0건) (d2)`size==limit+1`→검출 (e)문자열/음수→`invalid_index`. 6변형 전부 GREEN |

#### S-17: `scaffold` 상한 알림 — stdout 계약 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `cmdScaffold` stderr 경고 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `oversize/` |
| 기대 결과 | stderr에 초과 경고 1줄. **stdout JSON은 초과가 없을 때와 바이트 동일** |
| 도구 | `node --test` (stdout·stderr 분리 캡처) |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F5] S-17` 1건) |
| 결과 | Pass |
| 상세 | `oversize/`에서 `scaffold` — stderr에 초과 경고 1줄, stdout JSON은 초과 없을 때와 바이트 동일 확인 |

#### S-25: 상한 검사가 샤드 파일 자신도 측정하는가 ⭐

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6b |
| 대상 | 크기 상한 검사 범위 — 베이스 + **샤드** |
| 계층 | L1 |
| **실행 방식** | **M1** |
| 조건 | `oversize-shard/` — `manifestMaxBytes:200`, **베이스는 상한 이하**, 샤드 1개만 200바이트 초과 |
| 기대 결과 | `manifest_oversize`가 **1건** 검출되고 그 `manifest` 필드가 **샤드 경로**를 가리킨다 (베이스가 아님). S-15와 달리 베이스가 정상이므로, 검사가 베이스만 순회하면 0건이 되어 FAIL한다 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F5] S-25` 1건) + 독립 재현 스크립트(scratchpad/verify-s23-s25.js, `oversize-shard` fixture 복제 후 `validate --json` 직접 실행) |
| 결과 | Pass |
| 상세 | **근거 수치(독립 재실행)**: 베이스 매니페스트 90바이트(상한 200 이하), 샤드 `core.json` 441바이트(상한 200 초과) → `validate --json` 결과 `manifest_oversize` **정확히 1건**, `detail:"441/200"`, `manifest:".opal/code-map/svc/mod/_shards/core.json"`(**샤드 경로**, 베이스 아님) 확인. 베이스만 순회했다면 0건이 됐을 케이스가 정확히 1건으로 검출됨 — H-6b 반증 성공 |

> **이 시나리오가 없으면 상한 검사가 샤드를 빠뜨려도 전 시나리오가 GREEN이다.** 그 누락이 여는 구멍이 정확히 이 태스크가 막으려는 "샤드 재비대로 동일 사고 재발"(TASK 확정 방향 #4) 경로다. 목표-커버 게이트 1회차 gaps G-1(강권) 반영.

#### S-21: 봉인 지점 1곳 유지

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `resolveShards` 봉인 (080 `resolveHeaderSource`·`isInScope` 선례) |
| 계층 | L1 |
| **실행 방식** | **M1 (정적 검사)** |
| 조건 | 구현 완료된 `opal/tools/code-scan/code-scan.js` |
| 기대 결과 | `_shards` 경로 조립과 `byKey` Map 구성이 `resolveShards` 함수 본문 **밖에 0건**이다. 모드 판정 함수가 신설되지 않았다(`resolveHeaderSource` 외 0개) |
| 도구 | grep 기반 산출물 검사 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F1] S-21` 1건, 함수 줄 범위 중괄호 깊이 정적 검사) |
| 결과 | Pass |
| 상세 | `_shards` 경로 조립·`byKey Map` 구성이 `resolveShards` 함수 밖에 0건, 모드 판정 함수는 `resolveHeaderSource` 1개뿐임을 정적 검사로 확인 (실제 diff 육안 확인도 일치 — `code-scan.js` §5-4 참조) |

#### S-22: 버전·문서 산출물 검사

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 (문서-코드 정합) |
| 대상 | `VERSION`·`@header`·변경이력·`tools.md`·`header-rules.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (산출물 검사)** |
| 조건 | Step 11·12 완료 후 |
| 기대 결과 | `code-scan version` = `v1.5.0`. 변경이력에 `(082)` + `YYYY-MM-DD HH:mm` KST 포맷 행. `tools.md`에 `_shards`·`manifestMaxBytes`·신규 에러 코드 2종 반영. `header-rules.md` §워커 권한 경계 금지 필드에 `shards` 추가 |
| 도구 | grep 기반 산출물 검사 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L1-F8] S-22 (version/tools.md/header-rules.md)` 3건) + 직접 재실행: `node opal/tools/code-scan/code-scan.js --version` / `grep -n "_shards\|manifestMaxBytes\|shard_declaration_invalid\|reserved_name_collision" opal/core/references/tools.md` / `grep -n "shards" opal/core/references/harness/header-rules.md` |
| 결과 | Pass |
| 상세 | 직접 재실행 확인 — `code-scan v1.5.0` 출력. `tools.md`에 `_shards`·`manifestMaxBytes`·`shard_declaration_invalid`·`reserved_name_collision` 반영 + 변경이력 `v2.10 \| 2026-08-03 13:20 ... (082)` 행 존재. `header-rules.md` §워커 권한 경계 금지 필드에 `shards` 추가 + 변경이력 `v1.6 \| 2026-08-03 13:20 ... (082)` 행 존재 |

---

### L2. 프로세스 통합 (자동, 실 픽스처 트리 read→CUD→re-read)

#### S-6: hook 자동 정합 + 파손 fail-safe

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `code-map-hook.js` **무변경**으로 샤드 경로 소비 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | (a) `shard-repo/` 샤드 엔트리 청결 (b) 샤드 엔트리 미갱신 (c) `broken-base/` 파손 |
| 기대 결과 | (a) stdout·stderr 양축 0바이트 exit 0 (b) 경고 `additionalContext`에 **샤드 경로**와 그 키가 포함 (c) 파손이어도 무출력 exit 0 (try/catch 흡수) |
| 도구 | `node --test` + hook에 PostToolUse 이벤트 JSON 주입 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F2] S-6 (a/b/c)` 3건) |
| 결과 | Pass |
| 상세 | (a) 청결 엔트리(C.ts, pricing 샤드) — hook 무출력 exit 0 (b) 미갱신 엔트리(A.ts, core 샤드) — 경고 `additionalContext`에 샤드 경로 포함 (c) `broken-base` 파손 — hook 무출력 exit 0(try/catch 흡수) 3건 전부 확인 |

#### S-7: 정상 샤드 구성 — 위반 0건 (H-1 직접 반증)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `validate` 합집합 ↔ 디스크 대조 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/` — 디스크 4파일 = 베이스 files ∪ 샤드 2 files (정확히 일치). **full 모드와 `--changed` 모드 2회 실행** |
| 기대 결과 | 두 모드 모두 `violations` **0건**, exit 0. 특히 `files_key_removed`·`files_key_added`가 각 0건. `--changed`를 포함하는 이유는 커버 판정 파일 루프(`code-scan.js:1851`)가 이번 변경 지점이면서 CLOSE 게이트의 주 경로이기 때문이다 (게이트 gaps G-2) |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F3] S-7 (full)` + `[T082/L2-F3] S-7 (--changed)` 2건) |
| 결과 | Pass |
| 상세 | `shard-repo`(디스크 4파일 = 베이스∪샤드2 files 정확 일치) — full 모드·`--changed` 모드 둘 다 `violations` 0건 exit 0, `files_key_removed`/`files_key_added` 각 0건 확인(게이트 G-2 반영 커버) |

#### S-11: stale 오탐 차단

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `cmdScaffold` stale 집합 재구성 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/`에서 `scaffold` 실행 |
| 기대 결과 | `stale[]`에 선언된 `_shards/*.json`이 **0건**. 단 `undeclared/` 트리의 미선언 샤드는 stale로 보고된다(설계 의도 — `shard_undeclared`와 신호 일치) |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F4] S-11` 1건) |
| 결과 | Pass |
| 상세 | `shard-repo`에서 `scaffold` 실행 — 선언된 `_shards/*.json`이 stale 0건 확인 |

#### S-12: `scaffold` 멱등 + 샤드 자산 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `mergeManifest` `shards` 보존 + 버킷 분배 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/`에서 `scaffold` 2회 연속 실행 |
| 기대 결과 | 베이스의 `shards` 선언이 보존되고, 2회차 실행 후 베이스·샤드 파일 내용이 1회차와 **바이트 동일**. `created`/`updated`가 2회차에 0 |
| 도구 | `node --test` + 파일 바이트 대조 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F4] S-12` 1건) |
| 결과 | Pass |
| 상세 | `shard-repo`에서 `scaffold` 2회 연속 — `shards` 선언 보존, 베이스·샤드 파일 내용 바이트 동일, 2회차 `created`/`updated`=0 확인 |

#### S-13: 신규·삭제 파일 처리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | 버킷 분배 — 신규는 베이스, 삭제는 소유 샤드 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | (a) 소스 파일 1개 신규 추가 후 `scaffold` (b) 샤드 소유 키의 소스 파일 삭제 후 `scaffold` |
| 기대 결과 | (a) 베이스 `files{}`에 `draft:true` 추가 + `added[]`가 베이스 경로. 샤드 무변화 (b) 해당 **샤드**에서 pruned되고 베이스는 무변화 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F4] S-13 (a)` + `(b)` 2건) |
| 결과 | Pass |
| 상세 | (a) 소스 파일 신규 추가 후 `scaffold` — 베이스 `files{}`에 `draft:true` 추가 + `added[]` 베이스 경로, 샤드 무변화 (b) 샤드 소유 키 소스 삭제 후 `scaffold` — 해당 샤드에서 pruned, 베이스 무변화 2건 확인 |

#### S-14: 중복 키 무쓰기 가드 (자산 소실 방지)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `cmdScaffold` 가드 1 — 중복 시 디렉토리 skip |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `duplicate-key/`에서 `scaffold` 실행 |
| 기대 결과 | 그 디렉토리를 건너뛰고 `skipped[]`에 `shard_duplicate_key`를 남긴다. **샤드 파일의 내용과 mtime이 실행 전후 무변화** (자동 해소로 패자 서술이 삭제되지 않는다) |
| 도구 | `node --test` + mtime·바이트 대조 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F4] S-14` 1건) |
| 결과 | Pass |
| 상세 | `duplicate-key/`에서 `scaffold` — 해당 디렉토리 skip + `skipped[]`에 `shard_duplicate_key`, 샤드 파일 내용·mtime 실행 전후 무변화(자산 소실 없음) 확인 |

#### S-18: `_shards` 예약어 거부

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `reserved_name_collision`(scaffold) + `reserved_name`(validate) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `reserved-name/` — 소스에 `_shards` 디렉토리 존재 |
| 기대 결과 | `scaffold`가 `reserved_name_collision`으로 **exit 1**하고 매니페스트를 **쓰지 않는다**(실행 전후 code-map 트리 바이트 동일). `validate`는 `worker_scope_violation:reserved_name`을 검출한다 |
| 도구 | `node --test` + 트리 diff |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F6] S-18 (scaffold)` + `(validate)` 2건) |
| 결과 | Pass |
| 상세 | `reserved-name/`(소스에 `_shards` 디렉토리 존재) — `scaffold`가 `reserved_name_collision` exit 1 + code-map 트리 바이트 동일(미기록) 확인, `validate`가 `worker_scope_violation:reserved_name` 검출 확인 |

#### S-19: 하위호환 — 샤드 미선언 자산 바이트 동일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 옵트인 계약 (`resolveShards` `null` 반환 4조건) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | 기존 픽스처 전체 (`shards` 키 0건) |
| 기대 결과 | 조회 8커맨드 출력이 `tests/fixtures/golden/*` 8파일과 **바이트 동일**(재캡처 금지). `target --json`·`scaffold --json` stdout도 변경 전과 바이트 동일. 기존 테스트 10종 전량 GREEN이며 **무수정** |
| 도구 | `node --test` + 골든 바이트 대조 |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F7] S-19` 골든 8커맨드 + 신규 shards:[] 대조 + `[T082/L2-F7] S-19: 기존 테스트 10종 전량 GREEN` 총 11건) |
| 결과 | Pass |
| 상세 | `tests/fixtures/golden/*` 8파일(`scan/domain/layer/search/exports/summary/depends/missing`) 전부 바이트 동일 확인(재캡처 없이). 신규 빈 `shards:[]` 추가가 scan/target/scaffold 출력에 영향 0건. 기존 테스트 10종(test-discover/feature/header-source/hook/regression/scaffold/scope-filter/target/validate/resolve-header) 전량 GREEN — 이 항목이 전체 249건 중 실행시간 23초 최장 항목으로, 회귀 스위트 전체를 포함해 실행함을 확인 |

#### S-20: inline 모드 무영향 (양축)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | `resolveShards` 모드 게이트 (`ctx.headerSource !== 'manifest'` → `null`) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-repo/` 자산에 `--header-source inline` 강제 |
| 기대 결과 | 조회·`validate`·`scaffold`의 **stdout과 stderr 양축**이 샤드 자산이 없을 때와 동일하다. 샤드 파일을 읽은 흔적이 없다 |
| 도구 | `node --test` (양축 캡처) |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F7] S-20` 1건) |
| 결과 | Pass |
| 상세 | `shard-repo` + `--header-source inline` — 조회·`validate`·`scaffold`의 stdout·stderr 양축이 샤드 미도입 시와 동일 확인(샤드 파일 미접촉) |

#### S-26: 다중 스코프 상태 격리

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | `visitedShards` 스코프별 리셋 · `shardViews` 캐시 격리 · `--scope` 필터 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-multi-scope/` — 스코프 2개가 각각 샤드 보유, 한쪽에만 미선언 샤드 1개 배치 |
| 기대 결과 | ① 전체 `validate`에서 `shard_undeclared`가 해당 스코프에만 1건이고 다른 스코프로 번지지 않는다 ② `--scope <A>` 지정 시 A만 검사되고 B의 위반이 나타나지 않는다 ③ 두 스코프에 같은 basename이 있어도 캐시가 교차 오염되지 않는다 |
| 도구 | `node --test` |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-F3] S-26 ①/②/③` 3건) |
| 결과 | Pass |
| 상세 | ① 전체 `validate` — `shard_undeclared`가 svc-b에만 귀속, svc-a로 번지지 않음 ② `--scope svc-a` — svc-a만 검사, svc-b 위반 미출현 ③ 동일 basename(A.ts) 2스코프 존재해도 캐시 교차 오염 없이 스코프별 정확한 description 반환. 3건 전부 확인 |

> 목표-커버 게이트 1회차 gaps G-4 반영 — 전 픽스처가 단일 스코프여서 스코프 간 상태 누수가 구조적으로 발현하지 않았다.

#### S-23: **목표달성 — 분산으로 크기가 실제로 내려가고 조회가 온전한가** ⭐

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 (+ H-1, H-6 종합) |
| 대상 | **태스크 목표 그 자체** — "매니페스트를 의미 단위 샤드로 분산하고 크기 상한을 도구가 집행" |
| 계층 | L2 |
| **실행 방식** | **M1** |
| 조건 | `shard-goal/` — (a) **분산 전**: 상한 초과 베이스 1개에 전 엔트리 집중 (b) **분산 후**: **(a)에서 테스트 내 스크립트로 파생 생성**한 샤드 3개 + 베이스 트리 (c) **중간 상태 2종**: 엔트리를 샤드로 옮겼으나 ①`shards` 선언 누락 ②베이스에서 미제거(중복). 상한은 전 상태에 동일 적용 |
| 기대 결과 | **6항 동시 충족** — ① 분산 후 `manifest_oversize` **0건**(분산 전에는 1건 이상 — 대조군) ② 분산 전후 `scan --json`의 엔트리 집합과 각 헤더 필드 값이 **완전 동일** ③ 분산 후 모든 파일이 `target --json`에서 자기 소유 샤드로 라우팅 ④ 분산 후 `validate` 위반 0건 + exit 0 ⑤ 중간 (a)에서 `scan`이 그 엔트리를 **조용히 누락하지 않고**(누락 시 서술 유실) `validate`가 `shard_undeclared`로 드러낸다 ⑥ 중간 (b)에서 조회는 승자 엔트리로 동작하고 `validate`가 `shard_duplicate_key`로 드러낸다 |
| 도구 | `node --test` (분산 전/후/중간 4상태 대조. **분산 후 트리는 수작성하지 않고 분산 전에서 파생** — 수작성 2벌이면 ②의 동일성 단언이 도구가 아니라 픽스처 작성자를 시험하게 된다, 게이트 gaps G-3) |
| 실행 명령 | `cd opal/tools/code-scan/tests && node --test`(`[T082/L2-GOAL] S-23 ①②③④` + `⑤` + `⑥` 3건) + 독립 재현 스크립트(scratchpad/verify-s23-s25.js, `deriveAfterTree` 로직을 별도 재현해 테스트 코드와 무관하게 재확인) |
| 결과 | **Pass** |
| 상세 | **근거 수치(독립 재실행, 테스트 코드 신뢰가 아닌 별도 스크립트 재확인)**: ① 분산 전(`shard-goal/before`, 상한 400) — 베이스 850바이트 → `manifest_oversize` **1건**(`detail:"850/400"`, `manifest:".opal/code-map/svc/mod.json"`). 분산 후(before에서 스크립트로 파생, 파일당 개별 샤드 6개) — 베이스 188바이트 → `manifest_oversize` **0건**, `validate` 위반 총 **0건** exit 0. ② 분산 전후 `scan --json` 엔트리 6개(`CoreA/CoreB/PricingA/PricingB/ShippingA/ShippingB.ts`) 집합 완전 동일 + 전 엔트리 `description` 동일 확인. ③ 분산 후 6파일 전부 `target --json`에서 자기 소유 샤드(`_shards/{kebab-label}.json`)로 라우팅 확인(불일치 0건). ④ 분산 후 위반 0건 + exit 0(위 ①에 포함). ⑤ 중간상태(a) 선언 누락 — `scan`이 `CoreA.ts`를 누락하지 않고, `validate`가 `shard_undeclared`로 드러냄(node --test 통과). ⑥ 중간상태(b) 베이스 미제거 중복 — 조회는 베이스(선언순 승자) 서술로 동작, `validate`가 `shard_duplicate_key`로 드러냄(node --test 통과). **6항 전부 충족 — 태스크 목표(분산으로 크기 하강 + 조회 무손실) 달성 직접 확인** |

> **이 시나리오가 태스크 목표의 유일한 직접 단언이다.** S-1~S-22는 부품이 동작함을 보이지만, "분산해서 목표(크기 하강 + 조회 무손실)를 달성했다"는 이 시나리오만 증명한다. 나머지 전부 GREEN이어도 S-23이 FAIL이면 태스크는 미달성이다.

---

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-24: 실사용 대규모 자산에서 상한 열거 정확성 확인 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 실제 운영 자산에서의 상한 판정 + CLOSE 게이트 비봉쇄 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)**. M1 자동화 불가 — 픽스처가 아닌 실 자산이 대상이다 |
| 조건 | 대규모 code-map(매니페스트 1,000개 규모, 20KB 초과 다수 보유)을 가진 실사용 프로젝트. 배포된 v1.5.0 `code-scan` |
| 기대 결과 | ① `validate --json`의 `manifest_oversize` 열거가 실제 초과 매니페스트와 정확히 일치한다 ② 초과가 존재해도 다른 위반이 없으면 **exit 0**이며 기존 CLOSE 게이트가 봉쇄되지 않는다 ③ 기존 조회 명령 출력이 체감상 달라지지 않는다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | 대기 — 캡틴 수동 확인 필요 |
| 상세 | opal-test-agent는 L3 `[SUPERVISOR]` 마커 시나리오를 실행하지 않고 PM에 위임한다. 아래 "PM 표준 요청 양식"으로 캡틴에게 전달 필요 |

**PM 표준 요청 양식**

```
[SUPERVISOR 요청] S-24 — 실사용 자산 상한 열거 확인

대상   : 대규모 code-map 보유 프로젝트 (매니페스트 1,000개 규모)
사전   : ./scripts/install-mac.sh 로 code-scan v1.5.0 배포 완료
실행   : 해당 프로젝트 루트에서
         ~/.opal/tools/code-scan/run.sh validate --json | jq '.counts, [.violations[] | select(.code=="manifest_oversize")]'
         echo "exit=$?"
확인 3 : (1) 열거된 초과 매니페스트가 실제 20KB 초과분과 일치하는가
         (2) exit 코드가 0인가 (다른 위반이 없다는 전제)
         (3) 기존 조회 명령(scan/domain/search)이 이전과 동일하게 동작하는가
회신   : 위 3항의 Y/N + jq 출력 원문
```

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 AC — 합집합 해석 | H-1 | L1 | S-1 | `tests/test-shard.js`:`[T082/L1-F1] 합집합 해석` | PLAN TS-001 |
| F-1 AC — `package` 3단 상속 | H-4 | L1 | S-2 | `tests/test-shard.js`:`[T082/L1-F1] package 3단` | PLAN TS-002 |
| F-1 AC — 라벨 안전 | H-9 | L1 | S-3 | `tests/test-shard.js`:`[T082/L1-F1] 악성 라벨` | PLAN TS-004 |
| F-1 AC — 버전 불변 | H-10 | L1 | S-4 | `tests/test-shard.js`:`[T082/L1-F1] CODE_MAP_VERSION` | PLAN TS-005 |
| F-1 AC — 봉인 1곳 | H-12 | L1 | S-21 | `tests/test-shard.js`:`[T082/L1-F1] 봉인 grep` | PLAN §5.1 F-001 2행 |
| F-2 AC — 샤드 경로 반환 | H-5 | L1 | S-5 | `tests/test-shard.js`:`[T082/L1-F2] target 라우팅` | PLAN TS-006·007 |
| F-2 AC — hook 감지 | H-5 | L2 | S-6 | `tests/test-shard.js`:`[T082/L2-F2] hook 정합` | PLAN TS-008 |
| F-3 AC — 정상 구성 위반 0건 | H-1 | L2 | S-7 | `tests/test-shard.js`:`[T082/L2-F3] 무위반` | PLAN TS-010·014 |
| F-3 AC — 위반 3종 각 1건 | H-1 | L1 | S-8 | `tests/test-shard.js`:`[T082/L1-F3] 위반 4종` | PLAN TS-011·012·013·015 |
| F-3 AC — 오탐 증폭 차단 | H-1 | L1 | S-9 | `tests/test-shard.js`:`[T082/L1-F3] dir_missing 1건` | PLAN TS-016 |
| F-3 AC — 침범 귀속 | H-1 | L1 | S-10 | `tests/test-shard.js`:`[T082/L1-F3] 침범 귀속` | PLAN TS-017 |
| F-4 AC — stale 0건 | H-2 | L2 | S-11 | `tests/test-shard.js`:`[T082/L2-F4] stale` | PLAN TS-018 |
| F-4 AC — 선언 보존·멱등 | H-3 | L2 | S-12 | `tests/test-shard.js`:`[T082/L2-F4] 멱등` | PLAN TS-019 |
| F-4 AC — 신규·삭제 배치 | H-3 | L2 | S-13 | `tests/test-shard.js`:`[T082/L2-F4] 신규삭제` | PLAN TS-020·021 |
| F-4 AC — 중복 무쓰기 | H-3 | L2 | S-14 | `tests/test-shard.js`:`[T082/L2-F4] 중복 skip` | PLAN TS-022 |
| F-5 AC — 초과 열거·비차단 | H-6 | L1 | S-15 | `tests/test-shard.js`:`[T082/L1-F5] oversize` | PLAN TS-024·025 |
| F-5 AC — 설정 오버라이드 | H-6 | L1 | S-16 | `tests/test-shard.js`:`[T082/L1-F5] maxBytes` | PLAN TS-026 |
| F-5 AC — scaffold 알림 | H-6 | L1 | S-17 | `tests/test-shard.js`:`[T082/L1-F5] scaffold 경고` | PLAN TS-027 |
| **F-5 AC — 샤드 자신 상한 측정** | **H-6b** | L1 | **S-25** | `tests/test-shard.js`:`[T082/L1-F5] 샤드 oversize` | **게이트 gaps G-1(강권) 반영** |
| **F-3 AC — 다중 스코프 격리** | **H-13** | L2 | **S-26** | `tests/test-shard.js`:`[T082/L2-F3] 다중 스코프` | **게이트 gaps G-4 반영** |
| F-6 AC — 예약어 거부 | H-7 | L2 | S-18 | `tests/test-shard.js`:`[T082/L2-F6] 예약어` | PLAN TS-028·029 |
| F-7 AC — 골든 diff 0 + 전량 GREEN | H-4 | L2 | S-19 | `tests/test-regression.js` (**무수정**) + `tests/test-shard.js`:`[T082/L2-F7] 바이트 동일` | PLAN TS-003·009·023·030·031 |
| F-7 AC — inline 무영향 | H-8 | L2 | S-20 | `tests/test-shard.js`:`[T082/L2-F7] inline 양축` | PLAN TS-032 |
| F-8 AC — 버전·변경이력·문서 | H-12 | L1 | S-22 | `tests/test-shard.js`:`[T082/L1-F8] 산출물` | PLAN TS-033·034·035·036 |
| **목표 (TASK §명확화 목표)** | **H-11** | **L2** | **S-23** | `tests/test-shard.js`:`[T082/L2-GOAL] 분산 목표달성` | **PM 추가 — 목표달성 직접 단언** |
| **목표 (운영 확인)** | H-6 | L3 | S-24 | (수동 — [SUPERVISOR]) | **PM 추가 — 실 자산 검증** |

### 4.1 커버리지 자가 점검

| TASK 요구사항 | 커버 시나리오 | 상태 |
|---|---|---|
| F-1 샤드 해석 | S-1, S-2, S-3, S-4, S-21 | ✅ |
| F-2 기록 위치 라우팅 | S-5, S-6 | ✅ |
| F-3 validate 샤드 정합 | S-7(full+`--changed`), S-8, S-9, S-10, S-26 | ✅ |
| F-4 scaffold 샤드 보존 | S-11, S-12, S-13, S-14 | ✅ |
| F-5 크기 상한 집행 | S-15, S-16(경계 포함), S-17, S-24, **S-25** | ✅ |
| F-6 예약어 가드 | S-18 | ✅ |
| F-7 하위호환 회귀 가드 | S-19, S-20 | ✅ |
| F-8 문서·배포 반영 | S-22 | ✅ |
| **명확화 §목표 (분산 + 상한 집행)** | **S-23, S-24** | ✅ |
| **명확화 §완료기준 ②③④** | S-19(②③), S-7·S-11·S-5·S-18(④ 4명령) | ✅ |

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A | N/A — 미설정 | 프로젝트에 `.eslintrc*`/`eslint.config.*` 부재 확인(`find` 결과 0건) |
| 2 | 타입 체크 | `node --check opal/tools/code-scan/code-scan.js` | Pass | `SYNTAX OK` 출력 확인(exit 0) — 순수 JS 구문 검사로 대체 |
| 3 | 포맷터 | N/A | N/A — 미설정 | `.prettierrc*` 부재 확인 |
| 4 | 인접 코드 리팩터링 0건 (PRINCIPLES §3) | `git diff opal/tools/code-scan/code-scan.js` 육안 | Pass | 368 insertions/73 deletions, 전 hunk가 @header 메타·VERSION·샤드 상수·`resolveShards`(신규 봉인 함수)·`resolveManifestContext`/`resolveHeader`/`decideTarget`/`mergeManifest`/`cmdScaffold`/`cmdValidate`(샤딩·상한 로직)·`module.exports` 변경이력에 한정됨. `cmdValidate` 내 `checkEntryViolations` 함수 추출은 베이스+샤드 공통 재사용을 위한 것으로 샤딩 기능 자체에 직결되며 무관한 리팩터링 아님. 인접 무관 변경 0건 |
| 5 | 스키마 사변 필드 0개 (확정 방향 #6) | grep + diff 육안 | Pass | 베이스 매니페스트 신규 키는 `shards`(선택, 배열) 1개뿐(`mergeManifest`에 `if (existing && hasOwn(existing,'shards')) manifest.shards = existing.shards;` 1줄). `index.json` 신규 키는 `manifestMaxBytes`(선택, 양수) 1개. 그 외 file-entry 레벨 신규 필드 0건 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -rEn "(api[_-]?key\|secret\|token\|password)\s*[:=]"`를 변경 파일 전체(코드·문서·신규 픽스처·test-shard.js) 대상 실행 — 매치 0건(exit 1) |
| 2 | .gitignore 확인 | Pass | `.env`·`.pyc`·`__pycache__`·`.coverage` 등 민감/캐시 파일 정상 제외 확인. 이번 변경(픽스처·code-scan.js·문서)은 `.gitignore` 대상 파일과 무관 |
| 3 | 샤드 라벨 path traversal 차단 (S-3) | Pass | `bad-label/` 3변형(`"../escape"`/`"a/b"`/`"Core"`) 전부 `shard_declaration_invalid` exit 1 + `.opal/code-map/` 밖 신규 파일 0건(S-3 상세 참조) |
| 4 | `_shards` 예약어 덮어쓰기 차단 (S-18) | Pass | `reserved-name/` — `scaffold`가 `reserved_name_collision` exit 1 + 매니페스트 미기록(트리 바이트 동일), `validate`가 `reserved_name` 검출(S-18 상세 참조) |
| 5 | `scaffold` 중복 키 자동 삭제 0건 (S-14) | Pass | `duplicate-key/`에서 `scaffold` — 디렉토리 skip + `skipped[shard_duplicate_key]`, 샤드 파일 내용·mtime 실행 전후 무변화(자동 삭제·자동 해소 0건, S-14 상세 참조) |
| 6 | `~/.opal/` 배포 파일 직접 편집 0건 | Pass | `git status` 변경 파일 목록 전부 프로젝트 소스(`.opal/MEMORY.json`(프로젝트 로컬)·`docs/`·`opal/core/references/`·`opal/tools/code-scan/`·`tasks/`)이며 홈 디렉토리 `~/.opal/` 경로 0건 |

## 7. 판정

**All Pass — 전체 스위트 249/249 GREEN(fail 0), S-1~S-23·S-25·S-26 전량 Pass, §5 코드 품질 5항목 Pass/N-A, §6 보안 6항목 Pass, S-24는 L3 [SUPERVISOR] 수동 대기(Fail 아님)이므로 판정에서 제외한다. 특히 태스크 목표의 유일한 직접 단언인 S-23이 독립 재실행 근거 수치(분산 전 850/400 초과 1건 → 분산 후 188바이트 0건, 엔트리 6개 완전 동일, 전 파일 자기 소유 샤드 라우팅)로 확인됐고, S-25(샤드 자신 상한 측정, 베이스 90바이트/샤드 441바이트→200 초과 1건 검출)도 독립 재실행으로 확인되어 이 태스크가 막으려던 두 핵심 위험(목표 미달성·샤드 상한 누락)이 실제로 봉쇄됐음을 확증한다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인 — 전 시나리오가 실 픽스처 트리 대상 CLI 블랙박스)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-24)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-12 전부 시나리오 보유)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — **미해당** (§0 트랙 판정: FE·인증·외부 API 변경 0건)
- [x] **목표 커버** — TASK 요구사항 F-1~F-8 전체가 §4에 커버되고, 목표달성 시나리오가 §3에 2건 존재 (S-23 자동 / S-24 운영 확인)

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-03 | TEST-SCENARIO.md 최초 작성 — 가설 12종(PLAN 10종 + PM 추가 H-11 목표미달성·H-12 봉인훼손), 시나리오 24종(L1 12 / L2 11 / L3 1), 목표달성 직접 단언 S-23 신설 (Task 082) |
| 2026-08-03 | 목표-커버 게이트 1회차 gaps 반영 — 가설 H-6b(샤드 상한 누락)·H-13(다중 스코프 누수) 추가, S-25(샤드 자신 초과 G-1 강권)·S-26(다중 스코프 G-4) 신설, S-7에 `--changed`(G-2)·S-23에 중간 상태 2종+파생 생성(G-3)·S-16에 경계값(G-5) 보강. 시나리오 24 → 26종 (Task 082) |
