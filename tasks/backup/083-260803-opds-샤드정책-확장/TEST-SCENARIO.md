# TEST SCENARIO: 샤드 분할 파이프라인 — 2축 판정 + 분할 집행 + 유도

> 작성일: 2026-08-04 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 리스크 가설 표(H-1~H-22) 기반
> 구조: **기능축 시나리오 묶음** — TS-ID 122개를 기능(F-001~F-012) 단위 S 그룹 16개로 묶고, 각 TS의 세부 조건·기대결과는 PLAN.md §3 해당 절을 참조로 연결한다(중복 서술 금지 — `opal/core/PRINCIPLES.md` §2).
> RED-first: **적용**. 본 문서는 PLAN.md §4.2 Step 5(RED 작성)의 입력이며, 구현(Step 6a·6b)보다 선행 확정된다.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표를 승계하고 **시나리오(S-ID) 매핑을 확정**한다. 가설 문언·우선순위는 변경하지 않는다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 기본값 20480 → 10240 인하 | 082 픽스처 5종이 구 위치로 상한을 설정 중 — 구 위치가 무시되면 상한이 되돌아가 초과 판정이 사라진다 | **P0** | L1 + L2 | S-13, S-14 |
| H-2 | F-003 엔트리 수 하한 40 도입 | 082 픽스처는 엔트리 2~6개 — 하한 40 적용 시 기존 초과 단언 전부가 0건이 되어 FAIL | **P0** | L1 + L2 | S-3, S-13, S-14 |
| H-3 | F-001 `manifestMaxBytes(ctx)` 헬퍼 제거 | 소비 지점 2곳(scaffold/validate)이 살아 있는 상태에서 함수만 바뀌면 참조 오류 | P1 | L1 + L2 | S-1, S-3 |
| H-4 | F-002 전역 파일 신규 읽기 | 개발자 실제 홈 내용이 테스트 결과에 유입 → 로컬 GREEN·CI RED | **P0** | L1 + L2 | S-2, S-14 |
| H-5 | F-002 fail-safe | 전역 파일 파싱 실패가 전 명령 차단으로 승격되면 도구가 죽는다(제약 ⑪) | **P0** | L1 | S-2 |
| H-6 | F-005 `split` 쓰기 | 엔트리 유실 — 지운 엔트리가 샤드에 안 들어가거나 부분 쓰기로 중간 상태가 남는다 | **P0** | L1 + L2 | S-10, S-11, S-16 |
| H-7 | F-005 원자성 | `*.tmp-split` 잔존 시 `_shards/` 오염 | P2 | L2 | S-11 |
| H-8 | F-006 위반 페이로드 확장 | `detail` 포맷 변경 시 082 S-15 고정 단언이 깨진다 — 완화 금지 제약과 충돌 | P1 | L1 | S-12 |
| H-9 | F-007 구 위치 게이트 제거 | 타입 게이트 제거 시 082 S-16 (e) `invalid_index` 단언이 깨진다 | P1 | L1 | S-13 |
| H-10 | F-004 제안 결정론 | 그룹 순서·라벨이 흔들리면 `--plan` → 수정 → `--groups` 왕복이 재현 불가 | P1 | L1 | S-4, S-5 |
| H-11 | F-010 install 시드 | `if 'models' in existing: sys.exit(0)` 조기 종료로 기존 설치 환경에 정책 키가 영구히 시드되지 않는다 | P1 | L1 + L2 | S-15 |
| H-12 | F-001 봉인 | 정책 값을 읽는 지점이 2곳 이상이면 3단 우선순위가 지점별로 갈린다(제약 ③) | **P0** | L1 | S-1 |
| H-13 | 전 기능 | 골든 8파일 바이트 diff — 조회 경로에 전역 파일 읽기가 끼어들어 부수효과 발생 | **P0** | L2 | S-14 |
| H-14 | F-005 `split` 모드 게이트 | inline 모드에서 `split`이 조용히 성공하면 거짓 신호 | P2 | L1 | S-10 |
| H-15 | F-011 사전 md 파싱 | 표준단어사전에 컬럼 수가 다른 표 2개 — 위치 기반 파서는 `약어` 자리에 `도메인`을 읽는다 | P1 | L1 | S-7 |
| H-16 | F-011 사전 부재 | S1~S3 skip으로 커버리지가 급락하는데 사용자는 이유를 알 수 없다(조용한 저품질) | P2 | L1 | S-7 |
| H-17 | F-011 외부 문서 의존 신설 | code-scan이 처음으로 `.opal/` 밖을 읽는다 — "읽는 파일 3종" 계약이 깨진다 | P1 | L1 + L2 | S-7, S-14 |
| H-18 | F-004 검토 장치 3종 | `--trace`·`--stop-after`·`stage`가 출력 스키마를 흔들면 U-1 왕복이 깨진다 | P2 | L1 + L2 | S-6 |
| H-19 | F-011 경로 해소 | `{설계}` 해소 규칙이 SKILL.md 안에서 자기모순 — 어느 쪽을 기본으로 잡느냐에 따라 사전을 못 찾는다 | P2 | L1 | S-7 |
| H-20 | F-012 초안 추론 | 추론 결과가 규약과 어긋나면 생성 주체에 따라 설정이 달라진다 | P1 | L1 + L2 | S-9 |
| H-21 | F-012 `--force` | 소유자가 손으로 조정한 값이 추론 초안으로 덮여 유실된다 | P1 | L1 + L2 | S-9 |
| H-22 | F-012 게이트 순환 | `init`이 차단 게이트 뒤에 있으면 설정이 없어 `init`이 거부되고 `init`을 못 돌려 설정을 못 만든다 | **P0** | L1 | S-8 |

### 1.1 P0 가설 우선 처리 원칙

P0 6건(H-1·H-2·H-4·H-5·H-6·H-12·H-13·H-22 — 총 8건)은 **하나라도 RED면 EXECUTE 완료로 판정하지 않는다.** 나머지 가설의 GREEN으로 상쇄하지 않는다.

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크는 DB가 없는 CLI 도구다. "테이블" 축 대신 **픽스처 트리** 축으로 기재한다.

| 픽스처 | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 082 승계 (정책 이전 대상) | `shard-violations/oversize`, `oversize-shard` | 구 위치 키 제거 + `code-scan.json`에 `shardPolicy {maxBytes:200, minFiles:1}` | 기존 fixture 수정 (Step 1) |
| 082 승계 (목표달성) | `shard-goal/{before,mid-undeclared,mid-duplicate}` | 구 위치 키 제거 + `shardPolicy {maxBytes:400, minFiles:1}` | 기존 fixture 수정 (Step 2) |
| 083 정책·전역 | `shard-policy/{axis-bytes-only,axis-both,precedence,legacy-index}` | 2축·셀 머지·구 위치 무시 검증용 | 신규 (Step 3) |
| 083 가짜 홈 | `shard-policy/homes/{absent,valid,broken,nokey,badtype}` | `OPAL_HOME` 주입 대상 5종 | 신규 (Step 3) |
| 083 분할 대상 | `shard-policy/split-target` | 엔트리 12건 — 2건 이상 토큰 4종 + 1건 토큰 2종 | 신규 (Step 4) |
| 083 사전 | `shard-policy/dict/{valid,broken,two-tables,absent}` | 수식어 6열 + 분류어 5열 동시 수록 / 헤더 파손 / 미존재 | 신규 (Step 4) |
| 083 `init` 대상 | `shard-policy/init/{empty,existing,corrupt}` | 설정 부재 / 정상 존재 / JSON 파손 | 신규 (Step 4) |
| 골든 회귀 | `fixtures/golden/*` 8파일 | **무변경 — 재캡처 절대 금지** | 082 기준선 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전 상태) | When (실행) | Then (검증) |
|---------|------------------|------------|------------|
| S-1 | `precedence` + `homes/valid` | `validate --json` (OPAL_HOME 주입) | 셀 단위 3단 해석 결과가 결정 표와 일치 |
| S-2 | `homes/{absent,broken,nokey,badtype}` | `validate --json` × 4 | exit code 불변 · 전역 파일 바이트 동일 |
| S-3 | `axis-bytes-only`, `axis-both` | `validate --json` | 2축 동시 충족만 열거 · 경계 4케이스 일치 |
| S-5 | `split-target` + `dict/two-tables` | `split --plan --json --trace` | 단계별 `input === 직전 remaining` · 5단계 각 1그룹 이상 |
| S-7 | `dict/{valid,broken,absent}` | `split --plan --json` × 3 | 3분기 전부 비차단 · 사전 미발견 명시 |
| S-8 | `init/empty` (설정 없음) | `init --header-source inline` | **exit 0** (게이트 순환 없음) |
| S-9 | `init/existing` | `init --write` → `init --write --force` | exit 1 `config_exists` → `.bak` 원본 바이트 동일 |
| S-10 | `split-target` + groups 문서 | `split --groups <file>` | 엔트리 총합 동일 · `validate` 0건 |
| S-11 | `split-target` + 쓰기 실패 주입 | `split --groups` (실패) | 트리 바이트 동일 · `*.tmp-split` 잔존 0건 |
| S-16 | `split-target` (초과 상태) | `--plan --out` → `--groups --dry-run` → `--groups` → `validate` | `manifest_oversize` 0건 + 유실 0건 (완료기준 ④) |

## 3. 검증 시나리오

> **실행 방식 표기**: 전 시나리오 **M1(테스트 도구 — `node --test` + `spawnSync` 블랙박스)**. 본 태스크는 UI가 없어 M2(E2E)·M3(사용자 협업) 대상이 없다.
> **L3 부재 사유**: 산출물이 CLI 도구이며 화면·사용자 플로우가 없다. 완료기준 ④의 왕복 입증도 픽스처(`split-target`)로 자동 검증되므로 [SUPERVISOR] 수동 확인이 필요한 항목이 없다.

### L1. 기능 단위 (자동, 실 픽스처 입력)

#### S-1: 정책 3단 해석 + 셀 머지 + 판정 지점 봉인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-12 |
| 대상 | F-001 `resolveShardPolicy` — 코드 상수 / `~/.opal/setting.json` / `.opal/code-scan.json` 3단 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-001~TS-008 |
| 조건 | `shard-policy/precedence` + `homes/valid` 주입. 프로젝트에 `minFiles`만 기재한 셀 머지 케이스 포함 |
| 기대 결과 | PLAN §3.1.2 (F) 결정 표 7행 전부 일치. 프로젝트 타입 위반은 exit 1 `code_scan_config_invalid`. `DEFAULT_SHARD_POLICY`가 상수 선언 + `resolveShardPolicy` 본문 밖에 0회, `manifestMaxBytes(` 함수 정의 0개 |
| 도구 | `node --test` (`tests/test-shard-policy.js`) |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F1[acd]" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 8/8 pass, 0 fail, ~0.96s. TS-001~008 전부 통과. `DEFAULT_SHARD_POLICY`(maxBytes 10240/minFiles 40) 무설정 상수 폴백(TS-001), 전역만 있을 때 전역값 적용(TS-002), 프로젝트 `minFiles`만 있을 때 셀 머지(TS-003), 3단 동시 존재 시 `code-scan.json > setting.json > 상수` 결정론(TS-004), 타입 위반 exit 1 `code_scan_config_invalid`(TS-005), 미상 키(`_help`) 무해(TS-006), 정적 grep으로 `manifestMaxBytes(` 함수 소스 0개(TS-007), `loadGlobalSetting(` 호출 정확히 1곳(TS-008) 확인. |

#### S-2: 전역 설정 로더 — 4상태 비차단 폴백 + 홈 주입

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-5 |
| 대상 | F-002 `resolveOpalHome` / `loadGlobalSetting` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-010~TS-016 |
| 조건 | `homes/{absent,broken,nokey,badtype,valid}` 5종을 `OPAL_HOME`으로 주입 |
| 기대 결과 | 부재·깨진 JSON·키 부재·타입 위반 4상태에서 **exit code 불변**(전 명령 차단으로 승격하지 않음). 서로 다른 `OPAL_HOME` 2개로 정책이 다르게 적용됨. 실행 전후 `setting.json` 바이트 동일 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F1b" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 7/7 pass, 0 fail, ~1.77s(누적, 개별 케이스는 118~583ms). `OPAL_HOME` 부재 홈은 stderr 무출력 + 상수 폴백(TS-010), 깨진 JSON·키 부재·타입 위반 3상태 전부 비차단 + exit code 불변(TS-011~013, TS-016), 서로 다른 `OPAL_HOME` 2개 주입 시 정책이 실제로 달라짐(TS-014), 실행 전후 전역 `setting.json` 바이트 동일 확인(TS-015). exit 1로 승격된 케이스 0건 — H-5(fail-safe) 성립 실측. |

#### S-3: 2축 판정 + 경계 규칙

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-3 |
| 대상 | F-003 `isOversizeManifest` — 바이트 `>` AND 엔트리 `>=` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-020~TS-025 |
| 조건 | `axis-bytes-only`(바이트 초과·엔트리 미달) / `axis-both`(2축 충족, `minFiles` 경계 변형 포함) / 샤드 자신 측정 케이스 |
| 기대 결과 | 바이트만 초과하면 `counts.manifest_oversize === 0`. 2축 동시 충족만 1건 열거 + **exit 0(비차단)**. `size === limit`은 초과 아님(082 off-by-one 계약 보존). 샤드 파일도 동일 판정(`manifest` 필드가 샤드 경로) |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F2" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 7/7 pass, 0 fail, ~1.24s. 바이트만 초과·엔트리 미달은 0건(TS-020), 2축 동시 충족만 1건 열거 + exit 0(TS-021), 바이트 미달·엔트리 충족은 0건(AND 조건, TS-022), `entries===minFiles` 경계 대상·`minFiles-1` 비대상(TS-023), `size===maxBytes` 비대상·`+1` 대상(082 off-by-one 계약 보존, TS-024), 샤드 파일 자신 측정 시 `manifest` 필드가 샤드 경로(TS-025), scaffold stdout 바이트 동일 + 초과 시만 stderr 1줄(TS-026) 확인. |

#### S-4: 분할 제안 기본 계약 — 쓰기 0건 + 미분류 정직성 + 결정론

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-004 `split --plan` |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-030~TS-035, TS-116 |
| 조건 | `split-target`(엔트리 12건 — 2건 이상 토큰 4종 + 1건 토큰 2종). 사전 유/무 2회씩 실행 |
| 기대 결과 | `groups[].estimatedBytes`·`files.length` 존재. `.opal/code-map/` 트리 **바이트 동일**(쓰기 0건). `unassigned` 존재 + **"기타" 라벨 0개**. 사전 유/무 각각 2회 실행 stdout 바이트 동일 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F4[abc]|T083/L1-F4-usage" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 6/6 pass, 0 fail, ~1.28s. `--plan --json` 그룹 후보 + `estimatedBytes`·`files` 존재(TS-030), `--plan` 무쓰기 + `--out` groups 문서 1개만 생성(TS-031/034), `--plan --json` 2회 실행 stdout 바이트 동일 — 사전 유/무 각각(TS-033/116), 1건뿐인 엔트리 unassigned + "기타" 그룹 0개(TS-032/035~037), inline 모드 `split --plan` exit 1 `split_inline_mode`(TS-038), `--plan`+`--groups` 동시 지정 exit 1 `split_usage_invalid`(TS-039) 확인. |

#### S-5: 사다리 5단계 — 잔여만 흘려보내기 + 단계별 동작 + 다중 매칭 결정론

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | F-004 사다리 엔진 (S1 첫 토큰 → S2 2토큰 결합 → S3 중간 토큰 → S4 마지막 토큰 → S5 `depends`) |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-100~TS-108, TS-132 |
| 조건 | `split-target` + `dict/two-tables`. 각 단계가 최소 1그룹을 걷도록 구성된 엔트리 집합 |
| 기대 결과 | `trace[n].input === trace[n-1].remaining` 성립. **앞 단계 배정 불변**(후속 단계가 재배정하지 않음). 미달 버킷이 즉시 `unassigned`로 확정되지 않고 다음 단계로 흐름. 5단계 각 1그룹 이상. 사전 다중 매칭은 스팬 길이 내림차순 → 등재 순서 오름차순이며 `index`가 표 2개에 걸쳐 연속. **채택 효과 단언(추가)**: 사다리 최종 `unassigned` 수가 **S1 단독 실행 시점의 `unassigned`보다 작다** — "5단계 각 1그룹 이상"만으로는 각 단계가 1그룹만 걷어도 통과하므로, 단일 축 불채택 사유(잔여 31%)를 실제로 개선했는지를 겨눈다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F4d" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 5/5 pass, 0 fail, ~0.90s. `trace[n].input === trace[n-1].remaining` 연쇄 확인(TS-100~101), 신호별 배정(S1 첫토큰/S2 첫2토큰/S3 임의토큰/S4 마지막토큰/S5 `depends`, TS-102~106,132), `depends` 공유 엔트리 3건 이상이 S5 그룹 형성(TS-106), 미달 버킷은 다음 단계로 흐르고 다중 매칭은 스팬 길이·등재 순서 결정론(TS-107~108), **채택 효과 단언**: 사다리 최종 `unassigned` 수 < S1 단독 실행 시점 `unassigned` — 실측으로 확인(★S-5 전용 케이스). |

#### S-6: 검토 장치 3종 + 왕복 계약 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-18 |
| 대상 | F-004 `--trace` / `--stop-after` / 엔트리별 `stage` |
| 계층 | L1 + L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-109~TS-114 |
| 조건 | `split-target`. `--stop-after S2` 및 잘못된 stage 값 포함 |
| 기대 결과 | `--trace` 합계 정합. `--stop-after` 이후 단계가 `reason:'stopped'`. 잘못된 stage는 exit 1. `groups[].stage` ↔ `assignments` 일치. **`--trace --stop-after` 출력을 그대로 `--groups -`에 파이프해도 집행 성공**(U-1 왕복 불변). 사전 미발견 시 S1~S3이 `skipped:true, reason:'dict_absent'` |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-F4f" tests/test-shard-policy.js` (+ TS-114는 S-7과 공유, `--test-name-pattern="TS-114"` 별도 확인) |
| 결과 | Pass |
| 상세 | 5/5 pass(F4f 고유분), 0 fail, ~0.76s. `--trace` 합계 정합 assigned+unassigned===total(TS-109), `--stop-after S2` 이후 S3~S5 미실행 + 잔여 전부 unassigned(TS-110), 사다리 id 밖 stage 값 exit 1 `split_usage_invalid`(TS-111), `groups[].stage` ↔ `assignments[key]` 일치(TS-112), `--trace --stop-after` 출력을 그대로 `--groups -`(stdin) 파이프해도 성공 — 왕복 확인(TS-113). 사전 미발견 시 S1~S3 `skipped:dict_absent`(TS-114, 별도 실행 1/1 pass)도 확인. |

#### S-7: 용어사전 — 탐색 3단 + 2표 파싱 + 3분기 폴백 + 읽기 전용

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-15, H-16, H-17, H-19 |
| 대상 | F-011 사전 로더 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-115, TS-120~TS-131 |
| 조건 | `dict/{valid,broken,two-tables,absent}` + `{설계}` 변수 등록/미등록 트리 + 경로 이탈·초대형 파일 케이스 |
| 기대 결과 | `dictPath` → `{설계}` → 기본 경로 순서 동작(앞이 성공하면 뒤를 읽지 않음). **수식어 6열·분류어 5열에서 `영문`·`약어` 정확 추출**, 헤더 없는 표는 무시. 부재·파손 모두 exit code 불변이며 **부재는 stderr 무출력·파손은 1줄(실행당 1회)**. 프로젝트 루트 밖 거부, 크기 상한 초과는 사전 없음 취급. 실행 전후 사전·`docs/PROJECT.md` 바이트 동일. 조회 8커맨드는 사전을 읽지 않음(지연 로딩). 사전 미발견 시 `dict.found === false` + `dict.searched` + `--trace` 문구 명시 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F4e" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 10/10 pass, 0 fail, ~1.46s. `dictPath`→`{설계}`→기본 경로 순서(앞 성공 시 뒤 미탐색, TS-114·TS-120~123), 수식어 6열·분류어 5열 표에서 `영문`·`약어` 헤더 이름 기반 정확 추출(TS-124), 헤더 불일치 표 무시 + 파손 stderr 1줄 + 부재 침묵(TS-125~127), 프로젝트 루트 밖 dictPath 거부(TS-128), 크기 상한 초과 "사전 없음" 취급 + 무정지(TS-129), 실행 전후 사전·`docs/PROJECT.md` 바이트 동일 + 조회 8커맨드 지연 로딩(TS-130~131), 사전 미발견 시 `dict.found===false`+`dict.searched`(TS-115). exit code 승격 0건 — 3분기 전부 비차단 확인. |

#### S-8: `init` 게이트 순환 부재 + 비대화형 계약 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-22** |
| 대상 | F-012 `code-scan init` — `main()` 차단 게이트 앞 분기 배치 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-140~TS-144, TS-158 |
| 조건 | `init/empty`(설정 부재 트리) / `init/corrupt`(JSON 파손 트리) / TTY 없는 `spawnSync` |
| 기대 결과 | 설정이 **없는** 트리에서 `init --header-source inline`이 **exit 0**. **깨진** 트리에서도 `init --force` 동작. 나머지 13 명령의 게이트 차단 동작은 **불변**. TTY 없이 동작하고 프롬프트 0건. `--header-source` 누락 시 exit 1 + **파일 미생성**. 구형 값 `auto`는 마이그레이션 안내 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-X-[ab]" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 6/6 pass, 0 fail, ~0.85s. **설정 부재 트리**에서 `init --header-source inline`이 **exit 0**으로 초안 생성(TS-140) — 게이트 순환 실측 부재 확인(H-22). **JSON 파손 트리**에서도 `init --write --force`가 exit 0으로 복구(TS-141). TTY 없이 프롬프트 0건(TS-142). `--header-source` 누락 exit 1 `init_header_source_required` + 파일 미생성(TS-143). 구형 값 `auto`는 exit 1 `header_source_invalid`(TS-144). **나머지 13개 기존 명령의 게이트 차단 동작 불변** — `init` 추가로 15서브명령 확인(TS-158). P0(H-22) GREEN. |

#### S-9: `init` 쓰기 3분기 + 백업 + 규약 일치 추론

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-20, H-21 |
| 대상 | F-012 `cmdInit` 추론·쓰기 |
| 계층 | L1 + L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-145~TS-157, TS-160 |
| 조건 | `init/{empty,existing,corrupt}` + 이 저장소 재현 케이스(`--write` 미부여) |
| 기대 결과 | 없음·`--write` 없음 → 쓰기 0건 / 있음·force 없음 → exit 1 `config_exists` + 원본 불변 / 있음·`--force` → `.bak`이 원본과 **바이트 동일**. 추론이 규약과 일치(`scopes` 요소→kebab, `extensions` 실재 + `.md` 강제, `exclude` 10종 정확 일치, 키 순서). **이 저장소 재현 시 스코프 3종(`framework`·`console-fe`·`console-be`) 일치**. `shardPolicy`는 초안에 **부재**(3단 폴백 보존). stderr에 생성 보고 1줄 + stdout JSON 무오염. `header_source_unset`·`header_source_invalid`·`code_scan_config_invalid`의 `fix`에 `init` 명령 포함. md 표 파싱은 `parseMdTable` 1곳. 실행 전후 `{OPAL_HOME}/setting.json` 바이트 동일 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-X-[cd]" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 9/9 pass, 0 fail, ~1.26s. 없음+`--write` 없음 → stdout 초안 + 쓰기 0건(TS-145). 있음+`--write`(force 없음) → exit 1 `config_exists` + 원본 바이트 동일(TS-146). 있음+`--force` → `.bak`이 원본과 바이트 동일 + stderr 보고 1줄(TS-147/153). `docs/PROJECT.md` 표 기반 scopes 추론 + 표 없으면 디렉토리 스캔 폴백(TS-148~149). `extensions`에 `.md` 강제 포함 + `exclude` 10종 정확 일치 + 키 순서(TS-150~151). `shardPolicy` 키가 초안에 **부재**(3단 폴백 보존, TS-152). 이 저장소 재현 시 scopes 3종이 실제 `.opal/code-scan.json`과 일치(TS-154). 3종 에러의 `fix`에 `init` 명령 포함 + `parseMdTable` 1곳(TS-155~156). 실행 전후 전역 `setting.json` 바이트 동일 + `pm/code-scan-management.md` 반영(TS-157/160). |

#### S-12: 유도 페이로드 — 권고 조각 수 + 다음 명령 + `detail` 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | F-006 `manifest_oversize` 위반 확장 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-060~TS-062 |
| 조건 | `axis-both`(2축 충족 초과 매니페스트) |
| 기대 결과 | `recommendedShards`가 2 이상 정수, `next`가 문자열. `next` 명령을 그대로 실행하면 exit 0 + `--plan` 출력. **`detail` 포맷이 `{bytes}/{maxBytes}`로 불변**(082 S-15 고정 단언 보존) |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L1-F5" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 4/4 pass, 0 fail, ~0.68s. `recommendedShards`가 2 이상 정수 + `next`가 문자열(TS-060). `next` 명령을 그대로 실행하면 exit 0 + `--plan` 출력(TS-061). `detail` 포맷 `{bytes}/{maxBytes}` 불변 — 082 S-15 고정 단언 보존, H-8 완화 없음 실측(TS-062). scaffold stderr 경고에 `split ... --plan` 명령 포함(TS-063). |

#### S-13: 구 위치 키 이전 — 무시 + 1회 안내 + 082 단언 이전

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2, H-9 |
| 대상 | F-007 `index.json manifestMaxBytes` 폐기 처리 |
| 계층 | L1 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-070~TS-074 |
| 조건 | `legacy-index`(구 위치만) / 구·신 동시 존재 트리 |
| 기대 결과 | 구 위치 값 무영향 + stderr 1줄(실행당 1회) + **새 주소 포함**. `invalid_index` exit 1로 **승격하지 않음**. 구·신 동시 존재 시 신 위치 승. **082 단언이 완화 없이 이전됨** — PLAN §3.7.2 (C) 매핑 표 전행 일치, 단언 수가 이전 전보다 적지 않음 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="S-16 \(e" tests/test-shard.js` |
| 결과 | Pass |
| 상세 | 3/3 pass, 0 fail, ~0.57s. `code-scan.json` shardPolicy 타입 위반(문자열/음수) → exit 1 `code_scan_config_invalid`. 구 위치(`index.json manifestMaxBytes`) 타입 위반은 무시 + exit 승격 없음 + 폐기 안내 stderr **정확히 1줄**(신 주소 `shardPolicy` 포함) — `invalid_index`로 승격되지 않음 확인. 전역 `setting.json` shardPolicy 무효는 무시 + 기본값(10240/40) 폴백 + stderr 1줄. **주의(투명 보고)**: TEST-SCENARIO §2.1·§3 S-13 항목이 명시한 `TS-070~074` 리터럴 ID는 실제 테스트 소스(`test-shard.js`, `test-shard-policy.js`) 어디에도 존재하지 않는다 — grep 검색 결과 0건. 대응 실측은 위 3개 케이스(`[T082/L1-F5]`+`[T083/L1-F7]`+`[T083/L1-F2]`, TS-070~074 5개 ID 대비 3개 케이스)이며, 매핑 표(§4)의 `test-shard.js:[T083/L1-F6a]`·`[T083/L1-F6b]` 라벨도 소스 내 실제 라벨(`[T083/L1-F7]`·`[T083/L1-F2]`)과 문자열이 다르다. 동작은 GREEN이나 **TS-ID·라벨 표기 정합성은 미확인 상태로 보고**(구현·문서 수정은 범위 밖). |

### L2. 프로세스 통합 (자동, 실 파일 read → write → re-read)

#### S-10: `split` 집행 — 엔트리 유실 0건 + 사후 정합 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6**, H-14 |
| 대상 | F-005 `cmdSplit` 정상 경로 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-040~TS-045, TS-053 |
| 조건 | `split-target` + groups 문서. inline 모드 트리 / 라벨 경로 이탈(`../evil`·`_shards`·대문자) 케이스 포함 |
| 기대 결과 | 실행 전후 **엔트리 총합 동일**(실제 파일 재로딩 기준). 실행 후 `validate` 0건 + `scaffold` no-op(`created=0 updated=0`). `--dry-run`은 출력 존재 + 쓰기 0건. 라벨 경로 이탈은 exit 1. **inline 모드 `split`은 exit 1 + 사유 표면화**(조용한 성공 금지). **손편집 집행(추가)**: `--plan` 출력을 사람이 편집한 문서(라벨 개명 + 그룹 간 엔트리 이동)를 집행해도 성공하고 엔트리 유실 0건이다 — 무수정 왕복만으로는 실제 사용 형태를 덮지 못한다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-F3[abcd]|T083/L2-F3-손편집|T083/L1-라벨" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 6/6 pass, 0 fail, ~0.87s. `--groups` 실행 후 `_shards/` 생성 + 베이스 `shards` 선언 배열 추가 + 후속 `validate` 0건 + `scaffold` no-op(`created=0 updated=0`, TS-040/043/044). 실행 전후 엔트리 총합 동일(실제 파일 재로딩 기준, 유실 0건 — H-6 핵심 단언, TS-041). groups 미지정 엔트리(`legacy`/`temp`/`quirky`)는 베이스에 그대로 잔류(TS-042). `--dry-run`은 출력 존재 + `.opal/code-map/` 트리 바이트 동일(쓰기 0건, TS-045). 라벨 경로 이탈(`../evil`·`_shards`·대문자)은 exit 1 `split_groups_invalid`(TS-053). **손편집 집행**: `--plan` 산출물을 사람이 편집(라벨 개명 + 그룹 간 엔트리 이동)한 문서를 그대로 집행해도 성공 + 유실 0건(★S-10 전용 채택 케이스, 무수정 왕복만이 아닌 실사용 형태 검증). inline 모드 `split --plan` exit 1 `split_inline_mode`(TS-038)는 S-4 실행에서 이미 실측 확인됨 — 교차 참조, 중복 실행 생략. **표기 불일치(투명 보고)**: 실제 테스트 소스 라벨은 `[T083/L1-라벨]`(TS-053)이며, TEST-SCENARIO §1 조건표·본문이 언급한 대상 명칭과 문자열이 다르다(§4 매핑 표에는 이 라벨 자체가 별도 행으로 등재되어 있지 않음) — 동작은 GREEN이나 라벨 표기 정합은 미확인 상태로 보고(구현·문서 수정은 범위 밖). |

#### S-11: `split` 원자성 — 중도 실패 시 부분 상태 0건 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6**, H-7 |
| 대상 | F-005 4단 파이프라인(사전 검증 → tmp 작성 → rename 커밋 → 사후 재검증) |
| 계층 | L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-046~TS-049 |
| 조건 | 각 단계에 쓰기 실패를 주입한 4케이스 |
| 기대 결과 | 실패 후 `_shards/` 트리가 실행 전과 **바이트 동일**. `*.tmp-split` 잔존 **0건**. 단계별 에러 코드(`split_write_failed`·`split_rollback`·`split_verify_failed`)가 구분되어 반환 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-F3e" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 3/3 pass, 0 fail, ~0.31s. 존재하지 않는 그룹 키 참조·한 엔트리 2개 그룹 동시 지정(사전 검증 단계) → exit 1 `split_groups_invalid` + 쓰기 0건 + 트리 바이트 동일(TS-046~047). tmp 작성 단계 쓰기 실패 주입(부모 `svc` 디렉토리 쓰기 권한 제거) → exit 1 + `_shards/` 트리 바이트 동일 + `*.tmp-split` 잔존 0건(TS-048). 사후 재검증 총합 불일치(스테일 샤드 사전 삽입) 시 exit 1 `split_verify_failed` + 트리가 실행 전(스테일 상태 포함) 그대로 롤백(TS-049). **독립 재현 검증(추가)**: TS-048은 테스트 코드상 `exitCode===1`만 단언하고 구체 에러 코드는 미검증이라, 동일 조건(부모 디렉토리 555 권한)을 스크래치 디렉토리에 별도 재현하여 실측 — `{"error":"split_write_failed","detail":"EACCES: permission denied, mkdir '.../svc/mod/_shards'"}` + `find`로 `*.tmp-split` 잔존 0건 직접 확인. 3단계(사전검증→tmp작성→사후재검증)의 에러 코드(`split_groups_invalid`/`split_write_failed`/`split_verify_failed`) 구분 반환을 모두 실측 확인. **주의(투명 보고)**: 기대 결과가 명시한 3개 에러 코드 중 `split_rollback`(rename 커밋 단계 실패)을 트리거하는 케이스는 4단 파이프라인 중 TS-046~049 어디에도 존재하지 않는다 — `code-scan.js:2894`에 코드 자체는 정의돼 있으나 이 시나리오의 테스트 스위트로는 도달 경로가 커버되지 않음(코드 존재 확인, 테스트 커버리지 갭으로 보고). |

#### S-14: 회귀 가드 — 전량 GREEN + 골든 불변 + 홈 비의존 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-1, H-2, H-4, H-13**, H-17 |
| 대상 | F-008 전체 회귀 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-080~TS-085 |
| 조건 | 12 테스트 스크립트 전량 + 골든 8파일 + 가짜 홈 5종 대조 |
| 기대 결과 | 12 스크립트 실패 **0건**. `git diff --stat -- fixtures/golden/`이 **빈 결과**. 가짜 홈 5종 대조 결과 동일 + `OPAL_HOME` 주입 정적 검사 PASS. 샤드 미선언 자산 출력 불변. `resolveShards`·`resolveHeaderSource` 로직 무수정. `counts` 9키 불변. **`.opal/` 밖 읽기가 `split --plan` 경로에만 존재** |
| 도구 | `node --test` + `git diff` |
| 실행 명령 | `for f in tests/test-{discover,feature,header-source,hook,regression,resolve-header,scaffold,scope-filter,shard,target,validate}.js; do node --test "$f"; done` (11개 개별 독립 실행) + `node --test tests/test-shard-policy.js`(12번째, 자체 메타테스트 TS-080이 나머지 11개를 재차 자식 프로세스로 실행) + `git diff --stat -- opal/tools/code-scan/tests/fixtures/golden/` |
| 결과 | Pass |
| 상세 | **독립 실측**(EXECUTE 자기보고 "340/340 GREEN, 골든 diff 0"과 별개로 opal-test-agent가 직접 재실행): 11개 스크립트를 개별 독립 프로세스로 실행 — discover 12, feature 9, header-source 12, hook 18, regression 36, resolve-header 27, scaffold 9, scope-filter 24, shard 57, target 13, validate 34 = **소계 251/251 pass, 0 fail**. 12번째 `test-shard-policy.js` 단독 실행(내부 TS-080이 위 11개를 자식 프로세스로 재실행 포함) = **89/89 pass, 0 fail**(~40.5s, TS-080의 재귀 실행 포함). **합계 340/340 pass, 0 fail** — EXECUTE 자기보고 수치와 독립 실측 결과 일치 확인. `git diff --stat -- opal/tools/code-scan/tests/fixtures/golden/` 직접 실행 결과 **빈 문자열**(골든 8파일 바이트 diff 0, 재캡처 없음) 확인. **정적 코드 검증(추가 실측)**: `grep -n "function resolveShards"`로 `code-scan.js` 전체 diff(`git diff -- opal/tools/code-scan/code-scan.js`)를 대조한 결과 `resolveShards` 함수 본문에는 diff 매치 **0건**(무수정 확인). `resolveHeaderSource`는 `header_source_unset`/`header_source_invalid` 두 에러의 `fix` 문자열에 `INIT_CREATE_FIX` 안내가 **추가**됐으나 분기 조건·에러 코드 등 판정 로직 자체는 무변경(F-012 AC 의도된 변경, 로직 훼손 아님) — 완전 무수정은 아니므로 "무수정" 표현을 정정 보고. `counts` 객체(`code-scan.js:3420`) 키 9개(`orphan/uncovered/conflict/draft/exports_not_found/worker_scope_violation/newly_uncovered/pre_existing/manifest_oversize`) 불변 확인. `loadWordDictionary(` 호출부는 `cmdSplit`(2969행 인근) **1곳뿐**(grep 실측) — `docs/PROJECT.md` 표준단어사전 대조가 `split --plan` 경로에만 존재함을 확인(조회 8커맨드 비영향). 단, `resolveShardPolicy`(및 내부 `loadGlobalSetting` 전역 `~/.opal/setting.json` 읽기)는 `cmdScaffold`·`cmdSplit`·`cmdValidate` **3곳**에서 호출됨 — 이는 "`.opal/` 밖(프로젝트 외부) 문서 읽기"가 아니라 "전역 홈 파일 읽기"(H-4 별도 축)이며, TS-082(샤드 미선언 자산 출력 불변)·TS-083(가짜 홈 5종 스캔 결과 동일 + 정책 활성 시 홈 실제 소비 확인)에서 별도로 검증됨 — 두 축을 혼동하지 않도록 구분 보고. |

#### S-15: 문서·배포 — 버전·변경이력·시드 머지 안전

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | F-009 문서 반영 / F-010 install 시드 |
| 계층 | L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-090~TS-097, TS-160 |
| 조건 | `setting.json` 3형태(`models`만 / 둘 다 / 빈 파일)를 `cp` 임시 복사본으로 준비. **실 `~/.opal/setting.json` 변조 금지** |
| 기대 결과 | `VERSION === '1.6.0'` + 일시(KST)+`(083)` 변경이력 행. `tools.md`·`header-rules.md`·`pm/code-scan-management.md` 반영(`init` 등재 + `shardPolicy` 행 + `exclude` 불일치 해소). `setting.default.json`에 정책 2키. 3형태 시드 후 **기존 값 바이트 동일** + 2회 실행 멱등. 시드 없는 환경에서 코드 상수 폴백 동작 |
| 도구 | `node --test` + `python3` JSON 검증 |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-F8" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 6/6 pass, 0 fail, ~0.34s. `VERSION==='1.6.0'` + 변경이력 표 `(083)` 행 존재 + 대상 파일 `@header` 갱신 확인(TS-090/097). `tools.md`에 `split`·2축 판정·`shardPolicy`·3단 우선순위·에러 코드 7종 반영(TS-091). `header-rules.md`에 `split` 집행 1줄 + 변경이력 v1.7 반영(TS-092). `opal/core/setting.default.json`에 `shardPolicy.maxBytes===10240`·`minFiles===40` 2키 존재(TS-093). **install 시드 멱등·무손실**: `install-mac.sh`의 `PYEOF` 히어독 중 `SEED_KEYS` 포함 시드 스크립트 1개를 정적 추출해 `python3 -c`로 스크래치 디렉토리(`s15-seed`, **실 `~/.opal/setting.json` 미접촉**) 대상 3형태(`models`만/`shardPolicy` 둘 다/빈 파일)에 실행 — 3형태 모두 exit 0, `shardPolicy` 부재 시 시드됨, 기존 `shardPolicy` 값 보유 시 1바이트도 변경 없음(`deepStrictEqual`), 2회 연속 실행 결과 바이트 동일(멱등) 확인(TS-094~095). 시드 없는 환경(`homes/absent`)에서도 코드 상수(10240/40) 폴백으로 `manifest_oversize` 정상 판정(TS-096). `pm/code-scan-management.md`의 `init` 반영은 S-9(TS-157/160)에서 이미 실측 확인됨 — 교차 참조, 중복 실행 생략. |

#### S-16: 완료기준 ④ 왕복 입증 — 탐지 → 제안 → 집행 → 검증 [P0]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | **H-6**, H-10, H-18 |
| 대상 | 전 기능 통합 — TASK.md 완료기준 ④ |
| 계층 | L2 |
| **실행 방식** | **M1** |
| TS 묶음 | TS-054 |
| 조건 | `split-target`을 초과 상태로 준비 |
| 기대 결과 | **① 사전 상태 단언(필수)**: 시작 시 `validate`가 `manifest_oversize === 1`임을 먼저 단언한다 — 이 단언이 없으면 픽스처 정책이 잘못 잡혔을 때 "0건이 되었다"가 공허하게 참이 되어 false green이 된다. **② 전 궤 관통**: `validate`(탐지) → `--plan --out`(제안) → `--groups --dry-run`(예행) → `--groups`(집행) → `validate`(재검증) 순으로 처리한다. **③ 종료 상태**: `manifest_oversize`가 **0건**이 되고 엔트리 유실이 **0건**이다. **④ 왕복**: 중간 산출 groups 문서를 수정 없이 그대로 집행에 넣어 왕복이 성립한다 |
| 도구 | `node --test` |
| 실행 명령 | `node --test --test-name-pattern="T083/L2-DONE4" tests/test-shard-policy.js` |
| 결과 | Pass |
| 상세 | 1/1 pass, 0 fail, ~0.47s. **① 사전 상태 단언**: `split-target`(policy `maxBytes=512`/`minFiles=8`, manifest 1942B/10entries) 시작 시 `validate --json`이 `manifest_oversize===1`(exit 0, 2축 충족 1942>512 && 10>=8)임을 먼저 확인 — 이 단언 없이 "종료 0건"만 보면 픽스처 정책 오설정도 공허하게 참이 되는 false green을 사전 차단(H-6 관련). **② 전 궤 관통**: `validate`(탐지) → `split --plan --out groups-s16.json`(제안, exit 0 + 파일 생성) → `split --groups groups-s16.json --dry-run`(예행, exit 0) → `split --groups groups-s16.json`(집행, exit 0) → `validate`(재검증) 순서로 실행. **③ 종료 상태**: 실행 전후 `totalManifestEntries`(베이스+`_shards/*.json` 합산) 값이 동일(유실 0건) + 재검증 `manifest_oversize===0`. **④ 왕복**: `--out` 산출 groups 문서가 `--dry-run`·집행 구간을 통과하는 동안 바이트 변경 없음(수정 없이 그대로 재사용) 확인. P0(H-6) GREEN — 완료기준 ④ 왕복 입증 성립. |

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

> AC는 `TASK.md` §요구사항의 각 F-N AC를 원문 기준으로 인용한다. 테스트 파일 기본값은 `opal/tools/code-scan/tests/test-shard-policy.js`(신규)이며, 082 단언 이전분만 `test-shard.js`다.

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| F-1 (a) 설정 없으면 코드 상수, 전역만 있으면 전역값, 프로젝트 일부 키만 적으면 그 키만 덮어씀 | H-3, H-12 | L1 | S-1 | `test-shard-policy.js`:`[T083/L1-F1a]` | 결정 표 7행 |
| F-1 (b) 우선순위가 `code-scan.json` > `setting.json` > 상수로 결정론적 | H-12 | L1 | S-1 | `test-shard-policy.js`:`[T083/L1-F1a]` TS-004 | 셀 단위 독립. 구 기재 `[T083/L1-F1b]`는 **소스에 부재**하며 F-1b(전역 로더) 라벨 `[T083/L1-F1b-a/b/c]`와 접두사 충돌 |
| F-1 (c) 타입 위반이 결정론적으로 거부됨 | H-12 | L1 | S-1 | `test-shard-policy.js`:`[T083/L1-F1c]` | `code_scan_config_invalid` |
| F-1 (d) 정책을 읽는 지점이 코드에 1곳 | **H-12** | L1 | S-1 | `test-shard-policy.js`:`[T083/L1-F1d]` | 정적 grep |
| F-1b (a) 홈 경로가 주입 가능 | **H-4** | L1 | S-2 | `test-shard-policy.js`:`[T083/L1-F1b-a]` | `OPAL_HOME` |
| F-1b (b) 부재·파싱 실패·키 부재 모두 비차단 폴백 | **H-5** | L1 | S-2 | `test-shard-policy.js`:`[T083/L1-F1b-b]` | exit code 불변 |
| F-2 (a) 바이트 초과·엔트리 미달은 열거되지 않음 | **H-2** | L1 | S-3 | `test-shard-policy.js`:`[T083/L1-F2a]` | `counts === 0` |
| F-2 (b) 2축 모두 만족하는 것만 열거 | **H-2** | L1 | S-3 | `test-shard-policy.js`:`[T083/L1-F2b]` | exit 0 유지 |
| F-2 (c) 샤드 파일도 동일 판정 | H-3 | L1 | S-3 | `test-shard-policy.js`:`[T083/L1-F2c]` | 082 S-25 계승 |
| F-4 (a) 그룹 후보 + 예상 바이트·엔트리 수 출력 | H-10 | L1 | S-4 | `test-shard-policy.js`:`[T083/L1-F4a]` | — |
| F-4 (b) 자동으로 파일을 쓰지 않음 | H-10 | L1 | S-4 | `test-shard-policy.js`:`[T083/L1-F4b]` | 트리 바이트 동일 |
| F-4 (c) 미분류 엔트리를 명시 | H-16 | L1 | S-4, S-7 | `test-shard-policy.js`:`[T083/L1-F4c]` | "기타" 그룹 0개 |
| F-4 (d) 사다리가 잔여만 흘려보냄 (U-2 개정) | H-10 | L1 | S-5 | `test-shard-policy.js`:`[T083/L1-F4d]` | `trace` 연쇄 정합 |
| F-4 (e) 사전 3분기 폴백이 전부 비차단 (U-2 개정) | H-15, H-16, H-17, H-19 | L1 | S-7 | `test-shard-policy.js`:`[T083/L1-F4e]` | 2표 파싱 포함 |
| F-4 (f) 검토 장치가 왕복을 깨지 않음 (U-2 개정) | H-18 | L1+L2 | S-6 | `test-shard-policy.js`:`[T083/L2-F4f]` | 파이프 집행 |
| F-3 (a) 실행 후 `validate` 0건 + `scaffold` no-op | **H-6** | L2 | S-10 | `test-shard-policy.js`:`[T083/L2-F3a]` | — |
| F-3 (b) 엔트리 총합이 실행 전후 동일 (유실 0건) | **H-6** | L2 | S-10, S-16 | `test-shard-policy.js`:`[T083/L2-F3b]` | **절대 조건** |
| F-3 (c) 미지정 엔트리는 베이스에 남음 | H-6 | L2 | S-10 | `test-shard-policy.js`:`[T083/L2-F3c]` | — |
| F-3 (d) `--dry-run`으로 결과를 미리 볼 수 있음 | H-6 | L2 | S-10 | `test-shard-policy.js`:`[T083/L2-F3d]` | 쓰기 0건 |
| F-3 (e) 실패 시 부분 상태를 남기지 않음 | **H-6**, H-7 | L2 | S-11 | `test-shard-policy.js`:`[T083/L2-F3e]` | 4단계 실패 주입 |
| F-5 (a) 초과 위반에 권고 조각 수 + 다음 명령 포함 | H-8 | L1 | S-12 | `test-shard-policy.js`:`[T083/L1-F5a]` | — |
| F-5 (b) 그 명령을 그대로 실행하면 F-4 제안이 나옴 | H-8 | L1 | S-12 | `test-shard-policy.js`:`[T083/L1-F5b]` | — |
| F-6 (a) 구 위치 키가 정의대로 유지(무시 + 1회 안내) | H-9 | L1 | S-13 | `test-shard.js`:`[T083/L1-F7]` S-16 (e2) | 비차단 |
| F-6 (b) 구·신 동시 존재 시 우선순위 결정론적 | H-9 | L1 | S-13 | `test-shard.js`:`[T082/L1-F5]` S-16 (a)~(d2) + `[T083/L1-F2]` S-16 (e3) | 신 위치 승 |
| F-7 (a) 전체 테스트 전량 GREEN | **H-1, H-2** | L2 | S-14 | 12 스크립트 전량 | — |
| F-7 (b) 골든 8파일 바이트 diff 0 | **H-13** | L2 | S-14 | `git diff --stat` | 재캡처 금지 |
| F-7 (c) 샤드 미선언 자산 출력 불변 | **H-13** | L2 | S-14 | `test-shard.js` 기존 케이스 | 082 계약 |
| F-7 (d) 개발자 홈을 바꿔도 전체 결과 동일 | **H-4** | L2 | S-14 | `test-shard-policy.js`:`[T083/L2-F7]` TS-083·TS-084 | 가짜 홈 5종 |
| F-8 (a) 변경이력에 일시(KST)+`(083)` 행 추가 | — | L2 | S-15 | `test-shard-policy.js`:`[T083/L2-F8]` TS-090/097 | 문서 검사 |
| F-8 (b) `tools.md`가 2축·`split`·3단 우선순위 반영 | — | L2 | S-15 | `test-shard-policy.js`:`[T083/L2-F8]` TS-091 | 정규식 |
| F-8b (a) 신규 설치에 정책 키 생성 | H-11 | L2 | S-15 | `test-shard-policy.js`:`[T083/L2-F8b]` TS-093 | — |
| F-8b (b) 기존 사용자값 무손실 + 멱등 | **H-11** | L2 | S-15 | `test-shard-policy.js`:`[T083/L2-F8b]` TS-094~095 | 3형태 시드 |
| 확장 (a) 설정 부재·파손 트리에서 `init` 동작 | **H-22** | L1 | S-8 | `test-shard-policy.js`:`[T083/L1-X-a]` | **게이트 순환 부재** |
| 확장 (b) 비대화형 + `--header-source` 필수 | H-22 | L1 | S-8 | `test-shard-policy.js`:`[T083/L1-X-b]` | 프롬프트 0건 |
| 확장 (c) 쓰기 3분기 + `.bak` 백업 | H-21 | L1+L2 | S-9 | `test-shard-policy.js`:`[T083/L2-X-c]` | 유실 방지 |
| 확장 (d) 추론이 규약과 일치 | **H-20** | L1+L2 | S-9 | `test-shard-policy.js`:`[T083/L2-X-d]` | 1:1 대조 13행 |
| 완료기준 ④ 왕복 입증 | **H-6**, H-10 | L2 | S-16 | `test-shard-policy.js`:`[T083/L2-DONE4]` | 단일 시나리오 |

### 4.1 커버리지 확인

| 축 | 총계 | 매핑됨 | 미매핑 |
|----|------|--------|--------|
| 리스크 가설 (H-1~H-22) | 22 | 22 | **0** |
| TASK 요구사항 AC | 37행 | 37 | **0** |
| PLAN TS-ID | 122 | 122 (S-1~S-16 묶음) | **0** |
| P0 가설 | 8 | 8 (S-2·S-8·S-10·S-11·S-14·S-16 집중) | **0** |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 구문 검사 | `node --check` | Pass | `node --check`를 083 변경 대상 13개 JS 파일 전체(`code-scan.js` + `tests/test-{discover,feature,header-source,hook,regression,resolve-header,scaffold,scope-filter,shard,shard-policy,target,validate}.js`)에 개별 실행 — 13/13 구문 오류 0건. `scripts/install-mac.sh`(bash, `node --check` 대상 외)는 `bash -n`으로 추가 확인 — 구문 오류 0건. 린터 미도입 프로젝트(의존성 0 단일 파일 CLI) 전제 유지. |
| 2 | 타입 체크 | N/A | N/A | 순수 JS, 타입 시스템 미사용 — TASK.md·PLAN.md에도 타입 도입 요구 없음 |
| 3 | 포맷터 | N/A | Pass | 별도 포맷터 미도입. 083 diff(`git diff -- opal/tools/code-scan/code-scan.js`) 육안 검토 — 들여쓰기(2스페이스)·따옴표(단일 인용부호)·세미콜론 사용이 기존 코드 스타일과 일관됨(수동 검토, 스타일 이탈 0건) |
| 4 | `@header` 갱신 | `code-scan scan <file>` | Pass | `node opal/tools/code-scan/code-scan.js scan opal/tools/code-scan/code-scan.js --json` 실행 결과 `note` 필드에 "샤드 정책 확장(태스크 083): 정책 판정은 resolveShardPolicy 밖에 복제하지 않으며..." 문단이 반영됨(TS-090에서 검증한 @header 갱신과 별개로 실제 scan 출력 재확인). 프로젝트 전체 `validate --json` 실행 결과 `counts.newly_uncovered === 0`(083 변경으로 인한 신규 커버리지 회귀 0건, `orphan/conflict/exports_not_found/worker_scope_violation/manifest_oversize` 전부 0) 확인 |
| 5 | 변경이력 | 수동 검토 | Pass | `docs/PROJECT.md` §변경이력에 `2026-08-04 \| 코드맵 샤드 정책 확장 ... (Task 083)` 행 존재(확인: 파일 상단부 §변경이력 표 최상단 행). `code-scan.js:3633` 자체 변경이력 주석에 `v1.6.0 — 2026-08-04 (083) — 샤드 정책 2축화 + split 서브명령 신설` 행 존재. TS-090/097(VERSION==='1.6.0' + `(083)` 표기)·TS-092(`header-rules.md` v1.7 변경이력)는 S-15에서 이미 실측 완료 — 교차 참조 |

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-04 22:35 | **N-1 라벨 정합 정정 (PM 직접)** — §4 매핑 표의 케이스 라벨 8행을 테스트 소스 실측값으로 교체. `[T083/L2-F7d]`→`[T083/L2-F7]`(TS-083·084) / `[T083/L2-F8a]`→`[T083/L2-F8]`(TS-090/097) / F-8(b)→`[T083/L2-F8]`(TS-091) / `[T083/L2-F8b-a]`→`[T083/L2-F8b]`(TS-093) / `[T083/L2-F8b-b]`→`[T083/L2-F8b]`(TS-094~095) / F-6(a) `[T083/L1-F6a]`→`test-shard.js`:`[T083/L1-F7]`(S-16 (e2)) / F-6(b) `[T083/L1-F6b]`→`[T082/L1-F5]`(S-16 (a)~(d2))+`[T083/L1-F2]`(S-16 (e3)) / F-1(b) `[T083/L1-F1b]`(소스 부재·F-1b 접두사 충돌)→`[T083/L1-F1a]`(TS-004). **문서→소스 방향 단방향 정정이며 테스트 코드·단언은 무수정**(동작 판정 불변, 전량 340/340 GREEN 유지). TEST PM Gate에서 발견한 표기 정합 결함(N-1) 해소 (Task 083) |
| 2026-08-04 (TEST) | opal-test-agent가 L2 미실행분(S-10·S-11·S-14·S-15·S-16) + §5 코드 품질 5행을 독립 실측으로 채움. 실행 명령은 §4 매핑 표의 라벨 불일치(`[T083/L2-F7d]`→`[T083/L2-F7]` 등)를 소스 grep 실측으로 정정해 도출. P0 4종(S-10·S-11·S-14·S-16) 전부 GREEN — S-14는 EXECUTE 자기보고("340/340 GREEN, 골든 diff 0")를 독립 재실행(12스크립트 개별+메타테스트)으로 재확인(합계 340/340 일치, 골든 diff 빈 결과). 종합 판정 **All Pass**. 표기 불일치 2건(TS-053 라벨 `[T083/L1-라벨]`, `split_rollback` 에러 코드 트리거 케이스 테스트 커버리지 부재)을 투명 보고(수정은 범위 밖) (Task 083) |
| 2026-08-04 11:55 | 목표-커버 게이트 1회차 통과 후 advisory 4건 흡수 — S-16에 **사전 상태 단언**(`manifest_oversize === 1`, false green 차단)과 `validate` 시작 링크 추가(탐지→검증 전 궤 관통) / S-5에 **채택 효과 단언**(최종 `unassigned` < S1 단독 시점) 추가 / S-10에 **손편집 groups 문서 집행** 케이스 추가. 게이트 판정(도구 exit 0 + 평가자 2·2·2 pass)은 흡수 이전 시점에 성립했으며 본 보강은 임계 미달 대응이 아니다 (Task 083) |
| 2026-08-04 | 최초 작성 — PLAN.md 리스크 가설 22건 승계 + 기능축 시나리오 16종(S-1~S-16) + AC 37행 매핑. 알투(PM)+캡틴 페어 작성(PLAN 워커와 작성자 분리 — self-confirming 방지) (Task 083) |
