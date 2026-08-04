# PLAN: 샤드 분할 파이프라인 — 2축 판정 + 분할 집행 + 유도

> 작성일: 2026-08-03 | 입력: TASK.md (ANALYSIS.md 없음 — opds Short Task, 코드 분석을 본 PLAN에서 직접 수행)
> 모드: Multi-Feature (기능 10개)
> 출력 범위: PLAN.md 단독. TEST-SCENARIO.md는 PM+소유자 페어가 별도 작성한다 (self-confirming 방지)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

태스크 082는 "쪼개진 상태를 도구가 이해한다"까지 만들었고, 탐지 다음이 비어 있다 — `manifest_oversize` 위반 1줄이 찍히는 것이 전부이며(`opal/tools/code-scan/code-scan.js:2150`) 분할을 수행하는 서브명령은 0건이다. 083은 (a) 판정을 2축(바이트 상한 10240 **AND** 엔트리 수 하한 40)으로 정교화하고, (b) 탐지 → 제안(`split --plan`) → 집행(`split --groups`) → 검증(`validate`) 경로를 도구 안에 완성한다.

정책 값의 거처는 3단(코드 상수 → `~/.opal/setting.json` → `{프로젝트}/.opal/code-scan.json`)으로 재정의되며, 이를 읽는 지점은 **코드에 1곳**(`resolveShardPolicy`)으로 봉인된다 — 080 `resolveHeaderSource`(`code-scan.js:263`)·082 `resolveShards`(`code-scan.js:1002`)가 세운 봉인 구조를 계승·확장하는 것이지 새 구조를 세우는 것이 아니다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 정책 스키마 2축화 + 3단 해석 (`resolveShardPolicy` 봉인 1곳) | TASK F-1 | P0 | F-002 |
| F-002 | 전역 설정 로더 신설 (`loadGlobalSetting` + `OPAL_HOME` 주입) | TASK F-1b | P0 | 없음 |
| F-003 | 2축 판정 — 바이트 초과 AND 엔트리 수 이상 | TASK F-2 | P0 | F-001 |
| F-004 | 분할 제안 `split --plan` — **단계 사다리(S1~S5) 분류 엔진 + 검토 장치 3종**(`--trace`·`--stop-after`·엔트리별 `stage`) | TASK F-4 | P0 | F-001, F-011 |
| F-005 | 분할 집행 `split --groups` (원자적 2-phase commit) | TASK F-3 | P0 | F-004 |
| F-006 | 유도 경로 — 위반 페이로드에 권고 조각 수 + 다음 명령 | TASK F-5 | P1 | F-003, F-004 |
| F-007 | 구 위치 `index.json manifestMaxBytes` 이전 처리 (무시 + 1회 안내) | TASK F-6 | P0 | F-001 |
| F-008 | 회귀 가드 + 전역 설정 격리 (테스트·픽스처) | TASK F-7 | P0 | F-001~F-007 |
| F-009 | 문서·배포 반영 (버전·변경이력·tools.md·header-rules.md·docs/) | TASK F-8 | P1 | F-001~F-007 |
| F-010 | 전역 설정 시드 (`setting.default.json` + `install-mac.sh` 머지 안전) | TASK F-8b | P1 | F-001 |
| F-011 | **용어사전 로더** — 3단 탐색 + 헤더 기반 md 표 파싱 + 전량 비차단 폴백 | TASK F-4 (U-2 개정) | P1 | F-001 |
| F-012 | **`code-scan init` 서브명령** — `.opal/code-scan.json` 초안 추론·생성 (비대화형, `--header-source` 필수) + 잘못된 설정 복구 창구 | 범위 확장 (2026-08-04 소유자 승인) | P1 | 없음 |

> **F-012 번호 배정 근거**: 디스패치는 `init`을 "F-011"로 지칭했으나, F-011은 **직전 U-2 개정에서 용어사전 로더에 이미 배정**되어 본문 38곳에서 참조 중이다. 재번호는 지시된 "기존 ID 재번호 금지" 원칙에 어긋나고 유실 위험이 크므로 **`init`을 F-012로 배정**한다. 총 기능 수는 12개다.

> **F-011을 F-004에서 분리한 근거**: ① 사전 로더는 code-scan이 **처음으로 `.opal/` 밖 문서**(`docs/PROJECT.md`·`{설계}/사전/표준단어사전.md`)를 읽는 신규 외부 의존이며, 탐색 3단·파싱 실패·부재 3분기의 **실패 계약이 사다리 엔진과 독립**이다. ② F-002(전역 설정 로더)를 F-001에서 분리한 것과 동일 논리 — "값을 읽어 오는 층"과 "값으로 판정하는 층"을 나눠 각각 폴백을 검증한다. ③ 사다리 S4·S5는 사전 없이 동작하므로 F-011이 전부 실패해도 F-004는 성립한다 — 두 기능의 Pass 조건이 다르므로 QA 매트릭스에서 별도 행이어야 한다.

### 1.3 기능 의존 그래프 (ASCII)

```
F-002 ─ F-001 ─┬─ F-003 ─┐
               │         ├─ F-006 ─┐
               ├─ F-011 ─ F-004 ─── F-005 ─┤
               ├─ F-007 ──────────────────┼─ F-008 (테스트·픽스처)
               └─ F-010 ──────────────────┴─ F-009 (문서·배포)

F-012 (init) ──────────────────────────────┘   ← 독립 (선행 의존 0)
```

- **F-012가 독립인 이유**: `init`은 `.opal/code-scan.json`이 **없는 상태를 고치는** 명령이므로 정책 해석(F-001)·전역 설정(F-002) 어느 것도 선행 조건이 아니다. 오히려 반대 방향의 관계다 — `init`이 만든 파일이 F-001의 1순위 소스가 된다. 다만 **F-001의 `fix` 문구 보강**(§3.12.2 (F))이 F-012의 산출물을 가리키므로 문구 반영만 같은 Step에서 처리한다.
- F-002가 최선행인 이유: F-001의 3단 해석 중 2단(전역)이 F-002의 반환 계약에 의존한다.
- F-011이 F-004보다 선행하는 이유: 사다리 S1~S3이 사전 조회 결과를 `signal` 해석의 입력으로 받는다. **단, 실패 시 F-004가 멈추지 않는다** — 사전이 `null`이면 `dict: true` 단계가 자동 skip되고 S4·S5만 실행된다(U-2 (4) 폴백 판정표).
- F-004가 F-005보다 선행하는 이유: `--plan` 출력 스키마 = `--groups` 입력 스키마 **동일 문서**로 설계되므로(→ §1.6 U-1 채택안), 스키마 정의가 제안 쪽에서 확정된 뒤 집행이 소비한다.
- F-008·F-009는 전 기능 완료 후 수렴 — 단, RED-first 테스트 픽스처는 코드 변경보다 **선행**한다(§4.1 Phase 1).

### 1.4 [MUST] 계승 제약 (원문 인용)

> [MUST] `docs/CONVENTIONS.md` §Guards: 금지(승인 전) — 소스 코드 파일 생성·수정, 패키지 설치, 설정 파일 수정. → **PLAN 단계는 설계 문서만 작성하며 코드를 수정하지 않는다.**
> [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 스킬·에이전트·참조 문서를 변경하면 "## 변경이력" 표에 행을 추가한다. 일시(KST)를 포함한다.
> [MUST] `docs/CONVENTIONS.md` §문서 본문: 한국어 (기술 용어는 영어 병기).
> [MUST] `.opal/AGENT.md` §금지사항: 하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층에서만 수행한다. → F-002의 홈 경로 해석에 직접 적용된다(§3.2.2 (A)).
> [MUST] `TASK.md` §제약 조건: 배포 경계 준수 — `~/.opal/tools/code-scan/`를 직접 편집하지 않는다. `opal/tools/code-scan/`만 수정하고 install로 배포한다.
> [MUST] `TASK.md` §제약 조건: 골든 재캡처 절대 금지 — `fixtures/golden/*` 8파일은 회귀 기준선이다.
> [MUST] `TASK.md` §제약 조건: 판정 지점 봉인 유지 — 정책 값을 읽는 지점 1곳, 샤드 해석은 `resolveShards` 1곳. 3단 우선순위(`code-scan.json` > `~/.opal/setting.json` > 코드 상수)도 그 1곳 안에서만 해석한다.
> [MUST] `TASK.md` §제약 조건: 엔트리 유실 0건 — `split`은 매니페스트를 쓰는 명령이다. 실행 전후 엔트리 총합이 반드시 같아야 하며, 실패 시 부분 상태를 남기지 않는다.
> [MUST] `TASK.md` §제약 조건: 기존 픽스처 단언 완화 금지 — 기본값 변경으로 깨지면 픽스처에 정책 오버라이드를 명시해 흡수한다. 단언 삭제·skip·조건 완화는 금지한다.
> [MUST] `TASK.md` §제약 조건: 워커 파괴적 git 명령 금지 — `stash`/`checkout`/`reset`/`clean`/`restore`/`rm`/`commit`/`add`/`gc`. 읽기 전용(`status`/`diff`/`log`/`show`)만 허용한다.
> [MUST] `opal/core/references/harness/citation-rules.md` §0: 상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/URL + 섹션/줄번호)를 인용해야 한다.

### 1.5 082 brain 결정 승계 (뒤집지 않는 것)

`.opal/brain/pages/concept/code-scan-manifest-sharding-design.md` 및 `tasks/082-…/PLAN.md`에서 확정된 아래 4항은 083이 **유지**한다.

| # | 승계 사항 | 083에서의 의미 |
|---|----------|--------------|
| 1 | 베이스 매니페스트의 진입 경로 계산 규칙은 불변, 새로 생긴 것은 예약 폴더 `_shards/` 아래 샤드뿐 | `split`은 `mirrorPathForDir`(`code-scan.js:917`)를 건드리지 않는다 — 대상 경로를 인자로 받는다 |
| 2 | 샤드는 베이스와 완전히 같은 형태를 재사용 (신규 스키마 없음, 베이스에 추가된 것은 라벨 배열 1개) | `split`이 쓰는 샤드 객체는 `{version, scope, dir, files}` — 신규 필드 0개 |
| 3 | 새 파일이 어느 샤드에 속하는지 패턴 추측(글롭 라우팅) 불채택 — 의미 경계는 소유자의 몫 | `split --plan`은 **후보 제시**에 머물고, 미분류를 임의 배분하지 않는다 (→ §2 U-2) |
| 4 | 샤드 미선언 자산은 해석 경로 전체가 우회되어 바이트 무변화 보증(옵트인) | `resolveShards`의 null 반환 4조건(`code-scan.js:1003-1007`)을 훼손하지 않는다 |

### 1.6 미확정 사항(U-1~U-7) 결정

> TASK.md §미확정 사항 전 7항에 대한 결정. 각 항은 대안 비교 → 채택안 → 근거(코드 경로:줄번호) 순으로 기재한다.

#### U-1. `split` 입력 형식 — **그룹 정의 JSON 문서 단일 입력 (`--groups <path|->`)**

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) 엔트리 목록 CLI 인자 (`--group pricing=A.ts,B.ts` 반복) | 소규모에서 파일 없이 즉시 실행 | 292 엔트리를 표현하려면 인자 문자열 약 6KB + 다중 그룹 문법을 **새로 발명**해야 하고, 그 문법은 `--plan` 출력 형태와 달라 제안→집행 왕복이 끊긴다. 검증·오류 처리가 2벌이 된다 | 불채택 |
| (b) 그룹 정의 JSON 파일 입력 | 292 엔트리 규모를 그대로 담고, `--plan` 출력과 **같은 스키마**를 쓰면 왕복이 성립 | 소규모에서 파일 생성 1단계가 늘어난다 | **채택** |
| (c) (a)+(b) 병행 | 양쪽 편의 | 입력 경로 2개 = 스키마 검증 2벌 + "어느 쪽이 이기는가" 규칙 신설. TASK 확정 방향 #7-b가 같은 이유로 프로젝트 설정 소스를 1개로 못 박았다 | 불채택 |

**채택안**: `code-scan split <manifest-path> --groups <path|->`. 입력 문서는 `split --plan --json`의 **출력과 동일한 스키마**이며, `-`를 주면 stdin에서 읽는다.

**근거**:
- 소규모 편의는 별도 문법이 아니라 **stdin 파이프**로 흡수한다 — `--changed <csv|->`가 이미 같은 관용(stdin 개행 목록)을 갖고 있고 테스트 하네스도 `input`을 지원한다 (`code-scan.js:180`, `tests/test-shard.js:75-83`).
- "제안 출력 = 집행 입력" 동일 스키마는 U-2가 요구하는 "후보 제시 → 사람이 경계 확정 → 집행" 3단을 **신규 표면 0개**로 성립시킨다. 새 왕복 포맷을 만들면 사람이 손으로 변환해야 하고, 그 변환이 엔트리 유실의 새 원인이 된다(제약 ⑥).
- 스키마 검증을 1곳(`parseGroupsDoc`)에만 두어 080이 `resolveHeaderSource`(`code-scan.js:263`)로, 082가 `resolveShards`(`code-scan.js:1002`)로 세운 "판정 1곳" 원칙을 입력 계층에도 적용한다.

#### U-2. `split --plan` 제안 알고리즘 — **단계 사다리(cascade) + 용어사전 대조**

> **PM Gate 정정(083)**: 소유자 검토에서 초안의 "단일 축(1차 토큰 단독)" 결정이 **교체**되었다. 아래는 교체 후 확정안이며, 불채택 사유를 대안 표에 보존한다. 다른 결정(U-1·U-3·U-4·U-5·U-6·U-7)은 불변이다.

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) 서술(`description`) 기반 군집 (TF-IDF·임베딩) | 이름이 무의미한 자산에서도 의미 경계를 잡을 수 있다 | code-scan은 **의존성 0 단일 파일 Node CLI**다(`code-scan.js:29-31` — `fs`/`path`/`child_process`만). 군집 라이브러리를 넣을 수 없고 자체 구현은 결정론·검증 비용이 크며, 결과가 흔들리면 `--plan`→`--groups` 왕복이 재현 불가해진다(H-10) | 불채택 |
| (b) 이름 1차 토큰 + 서술 힌트 혼합 | 커버리지 상승 | "서술 힌트"의 가중치가 곧 의미 판단이며, brain 승계 #3(패턴 추측 라우팅 불채택)을 우회로 되살린다 | 불채택 |
| (c) **이름 1차 토큰 단독** (초안 채택안) | 결정론·구현 소형 | **단일 축이라 한 번 걸러 남은 것을 더 볼 방법이 없다.** 실측에서 90/288(31%)이 `unassigned`로 남고, 그 잔여를 줄일 후속 수단이 설계에 없다. 또 프로젝트가 이미 보유한 **표준단어사전이라는 의미 SSOT를 전혀 쓰지 않는다** | **불채택 (소유자 검토)** |
| (d) **단계 사다리 + 용어사전 대조** | 잔여를 단계마다 다시 거르므로 커버리지가 누적 상승한다. 사전이라는 **프로젝트 자산의 의미 경계**를 재사용하므로 도구가 의미를 발명하지 않는다. 단계 순서가 고정이라 결정론이 유지된다 | 단계 정의·사전 파서·검토 장치가 늘어난다 | **채택** |

##### (1) 사다리 구조 — 잔여만 흘려보낸다

- 분류는 **단계(stage) 배열**로 수행한다. 각 단계는 **직전 단계의 `unassigned`만** 입력으로 받는다.
- 이미 배정된 엔트리는 후속 단계가 **재배정하지 않는다** — 앞 단계 결과 불변.
- 단계 순서가 고정이므로 결정론 계약(H-10: 2회 실행 stdout 바이트 동일)이 그대로 유지된다. 사다리는 결정론을 늘리지도 줄이지도 않는다 — 단계 내부 정렬 규칙만 각 단계에 동일하게 적용하면 된다.
- **구조적 귀결**: 한 그룹의 모든 엔트리는 **정확히 한 단계**에서 배정된다. (5)의 엔트리별 `stage` 필드가 그룹 단위로도 성립하는 근거다.

##### (2) 단계 정의 4요소

| 요소 | 의미 |
|------|------|
| `signal` | 무엇을 보는가 — 파일명 첫 토큰 / 1~2번째 토큰 결합 / 전체 토큰 / 마지막 토큰 / `depends` |
| `dict` | 무엇에 대조하는가 — 표준단어사전(영문·약어) / 없음(빈도) |
| `accept` | 그룹 채택 조건 — 최소 엔트리 수 |
| `label` | 그룹 이름 — 사전 매칭 시 **사전 영문명 정규형**, 미사용 시 토큰 소문자 |

##### (3) 내장 기본 사다리 (이번 범위)

| # | signal | dict | accept | 예 |
|---|--------|------|--------|---|
| S1 | 첫 토큰 | 표준단어사전 | ≥2건 | `OrderRepository` → `order` |
| S2 | 1~2번째 토큰 결합 | 표준단어사전 | ≥2건 | `OrderPricing` → `order-pricing` |
| S3 | 전체 토큰 중 사전 매칭 | 표준단어사전 | ≥2건 | `TaxOrderTable` → `order` |
| S4 | 마지막 토큰(역할축) | 없음(빈도) | ≥3건 | `*Repository` → `repository` |
| S5 | `depends` 공유 | 없음 | ≥3건 | 같은 모듈 의존끼리 |
| — | 잔여 | — | — | `unassigned` — 임의 배분·"기타" 그룹 생성 **금지** |

- **`shardPolicy.ladder` 설정 노출은 이번 범위에서 제외한다 — 내장 고정으로 시작하고 후속 태스크로 이관한다.** 근거: 사다리는 단계 정의 4요소 × 5단계의 스키마를 새로 여는 일이며, 검증해야 할 조합이 정책 2키와 차원이 다르다. 내장 고정으로 실사용 데이터를 한 번 받아본 뒤 노출 형태를 정하는 편이 스키마를 되돌릴 위험이 낮다.
- S1~S3 매칭 규칙: **대소문자 무시** + 사전의 **`영문`·`약어` 두 컬럼 모두**를 후보로 삼는다. 매칭은 **연속 토큰 스팬**(1개 이상)을 이어붙인 문자열과 사전 값의 완전 일치로 판정하고, 여러 스팬이 매칭되면 **① 스팬 길이(토큰 수) 큰 것 우선 → ② 동률이면 사전 등재 순서(행 인덱스 오름차순)**로 결정한다. 이 규칙이 S2(첫 2토큰 스팬)를 S3(임의 위치 스팬)의 특수 케이스로 포함하므로 매칭 구현이 1벌이다.
- **`unassigned`는 그대로 남긴다** — brain 승계 #3(§1.5 "새 파일이 어느 샤드에 속하는지 패턴으로 추측하는 방식은 채택하지 않았다")은 사다리에서도 유지된다. 사다리는 **거르는 체를 여러 겹 두는 것**이지 못 거른 것을 억지로 채우는 장치가 아니다.

##### (4) 용어사전 — **옵셔널. 없으면 스킵 폴백**

- 사전은 **있으면 참고하고 없으면 건너뛴다.** 어떤 경우에도 명령을 차단하지 않는다.
- 탐색 3단 (앞 단계가 성공하면 뒤는 보지 않는다):
  1. `shardPolicy.dictPath` 명시값
  2. `docs/PROJECT.md`의 `{설계}` 경로 변수 해소 → `{설계}/사전/표준단어사전.md`
  3. 기본 경로 `200.설계/210.사전/표준단어사전.md`
- [MUST] `opal/skills/op-data-dictionary/SKILL.md:21`: "사전 저장 경로는 하드코딩하지 않는다. `docs/PROJECT.md`에 등록된 `{설계}` 변수(설계 산출물 루트)를 읽어 `{설계}/사전/`으로 해소한다." → 이 규칙을 계승하여 2단을 3단보다 **먼저** 본다.
- **폴백 판정표 (전부 비차단)**:

| 상황 | 동작 |
|------|------|
| 3단 탐색 전부 실패 (사전 없음) | S1~S3 **자동 skip**, S4·S5만 실행. **침묵**(부재는 정상 상태) — 단 `--trace`에 "사전 미발견 — S1~S3 건너뜀"을 명시 |
| 파일은 있으나 표 파싱 실패·컬럼 불일치 | "사전 없음"과 **동일 취급** + `noticeOnce('shard_dict_unparsable', …)` 안내 1줄 |
| 사전은 있으나 매칭 0건 | 정상 동작. S1~S3이 0건 걷고 다음 단계로 |

- **선례 계승**: `resolveHeader`의 `manifest_index_missing` fail-soft(`code-scan.js:1142-1148` — "차단 조건을 늘리지 않고 사유만 stderr 1줄로 노출하는 fail-soft를 택한다")와 **동일한 창구**를 쓴다. 새 차단 조건을 만들지 않는다.
- **신규 외부 의존 경고**: code-scan은 지금까지 `.opal/` 밖 문서를 읽은 적이 없다(읽는 파일은 `.opal/code-scan.json`·`.opal/code-map/index.json`·`~/.opal/setting.json` 3종). 사전 md 파싱은 **신규 외부 형식 의존**이므로 파서를 의존성 0으로 구현하고 실패를 전량 폴백으로 흡수한다(H-17).

##### (5) 단계별 검토 장치 3종

| # | 장치 | 계약 |
|---|------|------|
| 1 | `--trace` | 단계별 `입력 → 걷음 → 잔여` 표를 출력한다. 사전 미발견 시 "사전 미발견 — S1~S3 건너뜀"을 **명시**한다 |
| 2 | `--stop-after <stage>` | 지정 단계까지만 실행하고 결과를 낸다(예: `--stop-after S2`). 잔여는 전부 `unassigned` |
| 3 | 엔트리별 `stage` | `--plan` 출력의 각 배정 엔트리에 "몇 단계에서 배정됐는지"를 싣는다 |

- `stage`는 `--groups` 입력 스키마에도 **선택 필드로 허용**하되 집행 시에는 **무시**한다 — U-1의 왕복 계약(제안 출력 = 집행 입력)이 흔들리지 않는다. `trace`·`assignments`도 같은 취급이다(H-18).

##### (6) 유지되는 초안 규칙 3개

1. **입력 집합**: 대상 베이스의 `files` 키 중 **베이스에 남아 있는 엔트리만**. 이미 샤드가 보유한 엔트리는 후보에서 제외한다(재분할 시 기존 경계를 흔들지 않는다).
2. **크기 목표 점검**: 그룹 예상 바이트가 `targetBytes`(= `maxBytes × 0.75`, → U-5 (F))를 넘으면 `oversizeGroup: true`로 **표시만** 한다. 초안의 "2차 토큰 재분할 1회 시도"는 **삭제한다** — 사다리 S2·S3이 더 정밀한 분할을 이미 담당하므로 중복이다([MUST] `opal/core/PRINCIPLES.md` §2: "Remove a duplicated existing pattern before introducing a new one.", `code-scan.js:343` 인용).
3. **쓰기 금지**: `--plan`은 매니페스트를 **한 바이트도** 쓰지 않는다. `--out <path>`를 주면 groups 문서 1개만 쓴다.

##### (7) 결정론 보장 규칙 (H-10 검증 지점)

| 축 | 규칙 |
|----|------|
| 단계 순서 | `SHARD_PLAN_LADDER` 배열 순서 고정 (S1→S5) |
| 사전 다중 매칭 | 스팬 길이 내림차순 → 사전 등재 순서(행 인덱스) 오름차순 |
| 단계 내 그룹 순서 | 엔트리 수 내림차순 → 라벨 사전순 |
| 최종 그룹 순서 | **단계 순서 우선** → 단계 내 위 규칙 |
| `files` / `unassigned` | 사전순 |

#### U-3. 유도 진입점 형태 — **위반 페이로드 + stderr 안내 1줄. 전용 스킬·커맨드는 신설하지 않는다**

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) 위반 페이로드에 다음 행동만 싣기 | 신규 배포 표면 0개. `split --plan` 자체가 이미 진입점 | 사람이 문서를 한 번 봐야 한다 | **채택** |
| (b) 전용 스킬·커맨드(`//opsh` 등) 신설 | 대화형 유도 | 스킬 디렉토리·`install-mac.sh` 배포 목록·변경이력·에이전트 라우팅 표가 모두 늘어난다. 083 범위는 "도구"이며 스킬 신설은 범위 이탈이다 | 불채택 |

**채택안**: `manifest_oversize` 위반 객체에 `recommendedShards`(권고 조각 수)와 `next`(그대로 실행 가능한 명령 문자열)를 **추가 필드로** 싣고, `scaffold`의 기존 stderr 경고 1줄(`code-scan.js:1916-1918`)에도 같은 명령을 병기한다. 절차 문서는 `opal/core/references/tools.md` code-scan 절에 "분할 절차 4단"으로 기록한다.

**근거**:
- 082가 만든 stderr 경고는 이미 "`_shards/` 의미 단위 분할을 검토하세요"까지 말하고 있는데(`code-scan.js:1918`) **검토 수단이 없었다**. 083이 `split --plan`을 만들면 같은 자리에 실행 가능한 명령을 넣는 것으로 유도가 완성된다 — 새 진입점이 필요한 것이 아니라 기존 문장이 가리킬 대상이 없었던 것이다.
- `detail` 문자열 포맷은 **바꾸지 않고** 필드를 추가한다 — 082 S-15가 `assert.strictEqual(v.detail, \`${size}/200\`)`로 포맷을 고정 단언하고 있어(`tests/test-shard.js:415`) 포맷 변경은 단언 완화 없이는 흡수 불가하다(H-8).

#### U-4. 원자성·롤백 — **사전 불변식 검증 → tmp 전량 작성 → rename 커밋 → 사후 재검증, 실패 시 백업 복원**

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) 순차 직접 쓰기 | 단순 | 중간 실패 시 "베이스는 지워졌고 샤드는 안 만들어진" 상태 = 엔트리 유실. 제약 ⑥ 위반 | 불채택 |
| (b) 디렉토리 전체 복사 후 스왑 | 강한 원자성 | 스왑 대상 디렉토리 경로 조립이 `_shards/` 구조와 겹쳐 늘고, 스코프 매핑 디렉토리 전체를 복사하므로 대규모 자산에서 비용이 크다 | 불채택 |
| (c) `.bak` 백업 파일 잔존 | 복원 단순 | 잔존 파일이 `_shards/` 아래 `.json`이면 `listManifestFiles`(`code-scan.js:1780`)에 잡혀 `shard_undeclared` 오탐을 만든다 | 불채택 |
| (d) 4단 파이프라인 (아래) | 커밋 전 실패를 전량 흡수 + 커밋 중 실패도 복원 + 잔존물 없음 | 구현 단계가 4개 | **채택** |

**채택안 4단**:

| 단계 | 내용 | 실패 시 |
|------|------|--------|
| ① 사전 검증 | groups 문서 스키마·라벨 정규식·라벨 중복·파일 키 실재·파일 2중 지정 → 그리고 **불변식**: `Σ(샤드 엔트리) + 베이스 잔존 엔트리 === 실행 전 총 엔트리` && 합집합 키 중복 0 | exit 1, **쓰기 0건** |
| ② tmp 작성 | 대상 경로마다 `{path}.tmp-split` 전량 작성 (`mkdirSync` recursive 포함) | 작성된 tmp 전량 unlink → exit 1 `split_write_failed`, 원본 무변화 |
| ③ rename 커밋 | 기존 파일 내용을 메모리에 백업(신규는 `null`) → `fs.renameSync` 루프 | 이미 rename된 경로를 백업으로 복원(백업이 `null`이면 unlink), 남은 tmp unlink → exit 1 `split_rollback` |
| ④ 사후 재검증 | `ctx.codeMap.manifests`·`shardViews` 캐시 `.clear()` → 대상 베이스 재로딩 → `resolveShards`로 합집합 재구성 → 엔트리 총합·중복 0 재확인 | ③의 백업으로 복원 → exit 1 `split_verify_failed` |

**근거**:
- 동일 디렉토리 내 `rename`은 POSIX에서 원자적이므로 "전량 작성 후 일괄 rename"이 부분 상태 창구를 ②→③ 사이 한 지점으로 좁힌다. ②에서 디스크·권한 실패가 흡수되므로 ③에 도달할 확률 자체가 낮다.
- tmp 접미가 `.tmp-split`이라 `.json`으로 끝나지 않는다 — `listManifestFiles`가 `e.name.endsWith('.json')`만 수집하므로(`code-scan.js:1780`) 잔존 시에도 매니페스트로 오인되지 않는다(H-7 완화).
- ④의 캐시 무효화는 `resolveShards` 봉인을 훼손하지 않는다 — 해석 로직을 복제하는 것이 아니라 **같은 함수를 비운 캐시로 다시 호출**하는 것이다(제약 ③ 준수).
- `--dry-run`은 ①까지 수행하고 결과만 출력한다(쓰기 0건) — TASK F-3 AC "`--dry-run`으로 결과를 미리 볼 수 있다" 충족.

#### U-5. 스키마 형태·키 이름·타입 위반 처리 — **`shardPolicy` 객체, 전역·프로젝트 동일 형태, 레이어별 비대칭 처리**

**(A) 형태**: 객체 1개.

```json
{ "shardPolicy": { "maxBytes": 10240, "minFiles": 40 } }
```

| 대안 | 판정 근거 |
|------|----------|
| 평평한 키 2개 (`manifestMaxBytes` + `manifestMinFiles`) | 082 `manifestMaxBytes`와 연속적이지만, **전역 `~/.opal/setting.json` 최상위**에 code-scan 전용 키 2개가 `bootstrap`·`models`와 같은 층에 흩어진다. 값이 늘 때마다 전역 최상위가 오염된다 | 불채택 |
| `shardPolicy` 객체 1개 | 전역에서 code-scan 소유 영역이 **1키로 닫히고**, F-1 AC의 "적은 키만 덮어쓴 값이 적용된다(셀 단위 머지)"가 객체 구조에서 자연스럽다. `models`가 이미 같은 패턴(전역 1키 + 내부 셀 머지 + `setting.local.json` 셀 오버라이드)으로 존재한다(`opal/core/setting.default.json`) | **채택** |

**(B) 전역·프로젝트 키 형태**: **동일**. 두 파일 모두 최상위 `shardPolicy` 객체를 쓴다. 근거 — 형태가 다르면 소유자가 "어느 파일에선 어떻게 쓰는지"를 두 번 외워야 하고, 정규화 함수가 2벌이 된다. 확정 방향 #6이 프로젝트 오버라이드 위치를 `code-scan.json` 최상위로 정한 이유(“`headerSource`가 같은 최상위에 있어 연속적”)가 전역에도 동일하게 적용된다.

**(C) 알 수 없는 키**: **무시**(거부하지 않는다). `setting.default.json`의 `models._help` 관용이 같은 파일에 이미 존재하므로 `shardPolicy._help`도 허용되어야 하고, 미래 키 추가 시 구버전 도구가 전 명령을 차단하면 배포 순서 의존이 생긴다. 검증 대상은 알려진 2키(`maxBytes`·`minFiles`)의 **타입**뿐이다 — 각각 `> 0`인 유한 정수.

**(D) 타입 위반 처리 — 레이어별 비대칭 (결정론적)**:

| 소스 | 타입 위반 시 동작 | 근거 |
|------|-----------------|------|
| `{프로젝트}/.opal/code-scan.json` | `configError = 'shard_policy_invalid'` → `main()`에서 **`code_scan_config_invalid` exit 1** | 프로젝트 설정은 소유자가 방금 손으로 쓴 파일이다. 조용히 무시하면 "왜 안 먹지"가 된다. `scopes` 스키마 위반이 이미 같은 창구로 exit 1이다(`code-scan.js:2373-2380`) — **새 에러 코드를 만들지 않고 기존 창구에 합류**한다 |
| `~/.opal/setting.json` | **무시 + `noticeOnce` 1회 안내 → 하위 단계(코드 상수)로 폴백**, exit 0 | [MUST] `TASK.md` §제약 조건: "전역 설정 부재·파싱 실패·키 부재는 모두 하위 단계로 폴백한다. `headerSource`식 전 명령 차단으로 승격하지 않는다." 전역 파일은 code-scan 소유가 아니라 OPAL 공용이며(`bootstrap`·`models`), 남이 쓴 키가 깨졌을 때 code-scan이 전 명령을 죽이면 안 된다 |

**(E) 셀 단위 머지**: `maxBytes`와 `minFiles`는 **각각 독립적으로** 3단을 내려간다. 프로젝트에 `maxBytes`만 적으면 `minFiles`는 전역 → 상수 순으로 별도 해석된다(F-1 AC).

**(F) 파생값**: `targetBytes = max(1, floor(maxBytes × 0.75))`. 설정 키로 노출하지 않고 `resolveShardPolicy` 내부에서 파생한다 — TASK 확정 방향 #9("분할 트리거와 조각 목표는 다른 값이다")를 상수 1개로 충족하면서 설정 표면을 늘리지 않는다. 86.4KB 자산에 대해 `ceil(86400 / 7680) = 12`조각 권고 → 조각당 약 7.2KB로 p99(10.7KB) 아래에 안착한다(TASK §배경 분석 (4) 목표와 정합).

#### U-6. 구 위치 `index.json manifestMaxBytes` 처리 — **무시 + `deprecationOnce` 1회 안내, 타입 게이트도 함께 제거**

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) 하위 우선순위로 계속 해석 | 기존 자산 무중단 | 우선순위가 **4단**이 되어 확정 방향 #7-c("3단이며 읽는 지점은 1곳")를 위반한다. 사용 프로젝트가 0건이라 지킬 자산도 없다 | 불채택 |
| (b) 무시 + `deprecationOnce` 1회 안내 | 3단 유지. 080 F-002가 세운 선례와 동일 창구 | 픽스처·테스트 주소 이전이 필요하다 | **채택** |

**채택안**: `loadCodeMap`의 `manifestMaxBytes` 스키마 게이트(`code-scan.js:869-876`)를 **제거**하고, 해당 키가 존재하면 `deprecationOnce('index_manifest_max_bytes', …)`로 실행당 1회 stderr 안내한 뒤 값을 읽지 않는다. `invalid_index` 승격은 하지 않는다(비차단, F-6 AC).

**근거**:
- 080 F-002는 폐기된 키를 **타입 검증 없이** 무시 + `deprecationOnce`한다(`code-scan.js:430`·`:451`·`:460`). 무시할 키를 타입 검증해 전 명령을 차단하는 것은 "무시한다"와 모순이므로, 게이트를 남기는 절충은 선례와 어긋난다.
- 안내 문구에 **새 주소를 명시**한다: `.opal/code-map/index.json`의 `manifestMaxBytes`는 폐기 → `.opal/code-scan.json`의 `shardPolicy.maxBytes`. 080의 마이그레이션 안내(`code-scan.js:311-314`)가 "자동 변환하지 않는다"를 명시한 선례를 따라 **자동 이전은 하지 않는다**.
- **단언 이전 규칙(제약 ⑤ 준수 방식)**: 082 S-16 (a)~(e)는 삭제·완화하지 않고 **주소만 이전**한다. 단언 1건당 이전 후 최소 1건의 대응 단언이 존재해야 하며, 매핑 표는 §3.7.2 (C)에 싣는다. 이것은 "기본값 변경으로 깨진 것"이 아니라 F-6이 명시적으로 요구한 "읽는 파일이 바뀌는 변경"이므로 주소 이전이 정당한 대응이다.

#### U-7. 전역 설정 의존 테스트 격리 — **`OPAL_HOME` 환경변수(프로젝트 기존 관용) + 함수 파라미터 주입 병행**

| 대안 | 장점 | 단점 | 판정 |
|------|------|------|------|
| (a) `HOME` 오버라이드 | 선례 존재(`tests/test-regression.js:467`) | `HOME`은 자식 프로세스 전체(brain-tool·python 등)에 광범위 영향을 주고, 그 선례는 **brain-tool 격리 목적**으로 이미 쓰이고 있어 code-scan 격리와 목적이 얽힌다 | 보조 |
| (b) 홈 경로 파라미터 주입만 | 가장 명시적 | 현행 테스트 11종이 **전량 `spawnSync` 블랙박스**다(`tests/test-shard.js:75-83`). 별도 프로세스에 함수 인자를 줄 수 없으므로 **파라미터 주입만으로는 블랙박스 테스트를 격리할 수 없다** | 단독 불가 |
| (c) 전용 환경변수 `OPAL_HOME` | 좁은 창구. **이 프로젝트에 이미 확립된 관용** | 없음 | **채택** |

**채택안**: 홈 경로 해석을 `resolveOpalHome()` 1곳에 두고 `process.env.OPAL_HOME || path.join(os.homedir(), '.opal')`로 결정한다. `loadGlobalSetting(opalHome)`은 경로를 **파라미터로 받고**(단위 테스트·향후 재사용용), 호출자가 `resolveOpalHome()`을 넘긴다.

**근거**:
- `OPAL_HOME`은 이 프로젝트가 이미 쓰는 이름이며 의미도 `~/.opal` 디렉토리 자신이다 — `state_tool.py:242`: `opal_home = os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")`, `doctor/lib/checks.sh:25`: `OPAL_HOME="${OPAL_HOME:-$HOME/.opal}"`. 새 변수를 발명하지 않는다.
- [MUST] `opal/tools/state-tool/state_tool.py:236`: "경로는 OPAL_HOME env 우선(플랫폼 독립, ~/.opal 하드코딩 분기 금지)." — 동일 규칙을 code-scan에 적용한다. `.opal/AGENT.md` §금지사항의 "하드코딩된 플랫폼 분기 추가 금지"와도 정합한다.
- `os.homedir()` 폴백은 POSIX에서 `HOME`을 반영하므로 (a)의 선례도 자동으로 살아 있다 — 두 격리 방식이 공존하며 우선순위는 `OPAL_HOME` > `HOME`(via `os.homedir()`)으로 2단이다.
- **격리 검증 방식**: (i) 전 테스트 하네스의 `spawnSync` 호출에 `env: {...process.env, OPAL_HOME: <픽스처 가짜 홈>}`을 주입하고, (ii) 실 홈의 `~/.opal/setting.json`을 변조한 상태와 원본 상태에서 전체 결과가 동일함을 대조 검증한다(F-7 AC(격리)).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 기본값 20480 → 10240 인하 | 082 픽스처 5종(`shard-violations/oversize`·`oversize-shard`·`shard-goal/{before,mid-undeclared,mid-duplicate}`)이 `index.json manifestMaxBytes`로 상한을 설정 중 — 구 위치가 무시되면 상한이 10240으로 되돌아가 초과 판정이 사라진다 | **P0** | L1(픽스처 오버라이드 흡수) + L2(전량 GREEN) | S-후보: 5픽스처 정책 이전 후 S-15/S-16/S-17/S-23/S-25 전량 GREEN |
| H-2 | F-003 엔트리 수 하한 40 도입 | 082 픽스처는 전부 엔트리 2~6개다(`oversize/mod.json` 2엔트리·`shard-goal/before` 6엔트리) — 하한 40이 적용되면 **기존 초과 단언 전부가 0건이 되어 FAIL** | **P0** | L1(픽스처에 `minFiles:1` 명시) + L2 | S-후보: 픽스처 오버라이드로 흡수하고 단언은 손대지 않음을 정적 검사 |
| H-3 | F-001 `manifestMaxBytes(ctx)` 헬퍼 제거 | 소비 지점 2곳(`code-scan.js:1852` scaffold / `:2148` validate)이 살아 있는 상태에서 함수만 바뀌면 참조 오류 | P1 | L1(단위) + L2(scaffold·validate 실행) | S-후보: 두 명령 정상 exit + 봉인 grep |
| H-4 | F-002 전역 파일 신규 읽기 | 개발자 실제 홈 `~/.opal/setting.json` 내용이 테스트 결과에 유입 → 로컬 GREEN·CI RED (또는 그 반대) | **P0** | L1(로더 단위) + L2(가짜 홈 격리) + L3(실 홈 변조 대조) | S-후보: `OPAL_HOME`을 가짜 홈으로 돌린 상태와 실 홈 변조 상태에서 결과 동일 |
| H-5 | F-002 fail-safe | 전역 파일 파싱 실패가 `headerSource`식 전 명령 차단으로 승격되면 도구가 죽는다 (제약 ⑪ 위반) | **P0** | L1(부재·깨진 JSON·타입 위반 3케이스) | S-후보: 깨진 전역 설정에서 `validate` exit 0/2, exit 1 아님 |
| H-6 | F-005 `split` 쓰기 | 엔트리 유실 — 베이스에서 지운 엔트리가 샤드에 안 들어가거나, 부분 쓰기로 중간 상태가 남는다 | **P0** | L1(사전 불변식) + L2(실 파일 전후 총합) + L2(중도 실패 롤백) | S-후보: 전후 엔트리 총합 동일 / 쓰기 실패 주입 시 바이트 무변화 |
| H-7 | F-005 원자성 | tmp 파일(`*.tmp-split`)이 잔존하면 `listManifestFiles`(`code-scan.js:1780` `.json` 필터)를 통과하진 않으나 `_shards/` 오염 | P2 | L2(실패 주입 후 디렉토리 트리 비교) | S-후보: 실패 후 `_shards/` 트리가 실행 전과 동일 |
| H-8 | F-006 위반 페이로드 확장 | `manifest_oversize`의 `detail` 포맷을 바꾸면 082 S-15의 `assert.strictEqual(v.detail, \`${size}/200\`)`(`tests/test-shard.js:415`)가 깨진다 — 완화 금지 제약과 충돌 | P1 | L1(포맷 불변 + 신규 필드 additive) | S-후보: `detail` 포맷 무변경 확인 + 신규 필드 존재 확인 |
| H-9 | F-007 구 위치 게이트 제거 | `loadCodeMap`의 `manifestMaxBytes` 타입 게이트(`code-scan.js:871-876`)를 없애면 082 S-16 (e)(`tests/test-shard.js:489-501` `invalid_index` exit 1)가 깨진다 | P1 | L1(에러 코드 이전 매핑) | S-후보: 신 위치 타입 위반이 `code_scan_config_invalid` exit 1, 구 위치는 exit 0 + 1회 안내 |
| H-10 | F-004 제안 결정론 | 같은 입력에서 그룹 순서·라벨이 흔들리면 `--plan` → 사람 수정 → `--groups` 왕복이 재현 불가 | P1 | L1(2회 실행 바이트 동일) | S-후보: `--plan --json` 2회 stdout 바이트 동일 |
| H-11 | F-010 install 시드 | 현행 `install_opal_setting`은 `if 'models' in existing: sys.exit(0)`(`scripts/install-mac.sh:937-939`)로 조기 종료 — 이 구조를 그대로 두면 기존 설치 환경에 `shardPolicy`가 **영구히 시드되지 않는다** | P1 | L1(키 목록 루프) + L2(기존 파일 3형태 시드) | S-후보: `models`만 있는 파일·둘 다 있는 파일·빈 파일 3케이스에서 사용자값 무손실 |
| H-12 | F-001 봉인 | 정책 값을 읽는 지점이 2곳 이상으로 늘면 3단 우선순위가 지점별로 갈린다 (제약 ③ 위반) | **P0** | L1(정적 grep 검사) | S-후보: `DEFAULT_SHARD_POLICY` 식별자가 상수 선언 + `resolveShardPolicy` 본문 밖에 0회 등장 |
| H-13 | 전 기능 | 골든 8파일 바이트 diff — 조회 8커맨드 경로에 전역 파일 읽기가 끼어들어 부수효과 발생 | **P0** | L2(골든 바이트 동일) | S-후보: `fixtures/golden/*` 8커맨드 stdout 바이트 동일 + `git diff` 0 |
| H-14 | F-005 `split` 모드 게이트 | inline 모드에서 `split`이 조용히 성공하면 "매니페스트가 없는데 분할됨"이라는 거짓 신호 | P2 | L1(exit code) | S-후보: inline 모드 `split` exit 1 + 사유 표면화 |
| H-15 | F-011 사전 md 파싱 | **표준단어사전.md 안에 컬럼 수가 다른 표 2개가 존재한다** — `## 수식어`는 6열(`한글\|영문\|약어\|규칙\|도메인\|비고`), `## 분류어`는 5열(`한글\|영문\|약어\|도메인\|비고`)로 `규칙` 컬럼이 없다(`opal/skills/op-data-dictionary/SKILL.md:81-89` 실측). **위치(인덱스) 기반 파서는 분류어 표에서 즉시 어긋나 `약어` 자리에 `도메인` 값을 읽는다** | P1 | L1(두 표 동시 파싱) + L1(파싱 실패 폴백) | S-후보: 두 표를 모두 담은 사전에서 `영문`·`약어`가 정확히 추출된다 / 헤더 없는 표는 무시된다 |
| H-16 | F-011 사전 부재 | 사전이 없으면 S1~S3이 통째로 skip되어 커버리지가 급락하는데, 사용자는 **제안이 부실한 이유를 알 수 없다**(조용한 저품질) | P2 | L1(`--trace` 문구) + L1(출력 필드) | S-후보: 사전 미발견 시 `--trace`에 "사전 미발견 — S1~S3 건너뜀" + `--plan` 출력에 `dict.found === false`와 탐색 경로 목록 |
| H-17 | F-011 외부 문서 의존 신설 | code-scan이 **처음으로 `.opal/` 밖**(`docs/PROJECT.md`·`{설계}/사전/*.md`)을 읽는다 — 읽기 실패·거대 파일·경로 이탈이 새 실패 축이며, 지금까지의 "읽는 파일 3종" 계약이 깨진다 | P1 | L1(3분기 폴백) + L1(경로 제한) | S-후보: 읽기 실패·비정상 경로·초대형 파일에서 전부 비차단 폴백하고 exit code가 불변이다 |
| H-18 | F-004 검토 장치 3종 | `--trace`·`--stop-after`·엔트리별 `stage`가 `--plan` 출력 스키마를 흔들면 U-1 왕복(제안 출력 = 집행 입력, TS-050)이 깨진다 | P2 | L1(스키마 선택 필드) + L2(왕복) | S-후보: `--trace`/`--stop-after`를 켠 출력을 그대로 `--groups`에 파이프해도 성공한다 |
| H-19 | F-011 경로 해소 | `{설계}` 변수 해소 규칙이 **SKILL.md 안에서 자기모순**이다 — `:21`은 default를 `200.설계/210.사전/`로, `:72`·`:172`는 `{설계}/사전/`(= `200.설계/사전/`)로 적는다. 어느 쪽을 기본으로 잡느냐에 따라 사전을 못 찾는다 | P2 | L1(경로 후보 다중 탐색) | S-후보: 두 경로 중 어느 쪽에 사전을 두어도 발견된다 |
| H-20 | F-012 초안 추론 | 추론 결과가 **규약(`pm/code-scan-management.md`)과 어긋나면** PM이 손으로 만들던 파일과 도구가 만드는 파일이 갈린다 — 같은 프로젝트에서 생성 주체에 따라 설정이 달라진다. 특히 `exclude` 기본값이 규약 예시(`backup`·`.pytest_cache` 포함)와 코드 `DEFAULT_CONFIG`(`env`·`.output` 포함)에서 **이미 서로 다르다**(`code-scan.js:43` vs `code-scan-management.md:30`) | P1 | L1(규약 1:1 대조표) + L2(실제 저장소 재현) | S-후보: 이 저장소에서 `init`을 돌린 결과가 규약 예시 구조와 키·순서·기본값에서 일치한다 / `scopes` 추론 결과가 실제 `.opal/code-scan.json`의 3종(`framework`·`console-fe`·`console-be`)과 같다 |
| H-21 | F-012 `--force` | `--force`가 **기존 설정을 통째로 날린다** — 소유자가 손으로 조정한 `scopes` include/exclude·`excludePatterns`·(083 이후) `shardPolicy`가 추론 초안으로 덮여 유실된다. 그런데 `--force`는 "잘못된 설정 복구" 창구라 반드시 존재해야 한다 | P1 | L1(백업 생성) + L2(복구 왕복) | S-후보: `--force` 덮어쓰기 직전 `.opal/code-scan.json.bak`이 생성되고 원본과 바이트 동일하다 / `--write`만으로는 기존 파일을 건드리지 않고 exit 1 |
| H-22 | F-012 게이트 순환 | `init`이 `main()`의 **전 명령 차단 게이트**(`code-scan.js:2362-2367`) 뒤에 배치되면, `headerSource`가 없어서 `init`이 거부되고 `init`을 못 돌려서 `headerSource`를 못 만드는 **순환**이 생긴다 — 기능이 통째로 무용지물이 된다 | **P0** | L1(설정 부재 트리 실행) | S-후보: `.opal/code-scan.json`이 **없는** 트리에서 `init --header-source inline`이 exit 0으로 동작한다 / `code-scan.json`이 **깨진** 트리에서도 `init --force`가 동작한다 |

---

## 2. 기능별 분석

> ANALYSIS.md가 없으므로(opds Short Task) 각 기능의 현재 구현을 직접 코드에서 확인해 기재한다. 영역 축은 프레임워크 태스크 축(**도구 / 테스트 / 문서 / 배포**)을 사용한다 (`op-dev-plan/SKILL.md` §영역 태그 규칙 — "프레임워크 문서·스킬 태스크에서는 스킬/가이드/오케스트레이터/에이전트/문서/환경/배치 축을 사용한다"에 따라, 본 태스크의 실체인 CLI 도구·테스트·배포 스크립트로 구체화).

### 2.0 공통 파일 맵 (전 기능)

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/code-scan/code-scan.js` | 본체 2,475줄 · v1.5.0 · 의존성 0 단일 파일 Node CLI · 13 서브명령 | 수정 (F-001~F-007, F-009 일부) |
| 도구 | `opal/tools/code-scan/code-map-hook.js` | PostToolUse hook — `loadConfig`를 직접 호출(fail-safe 경로) | **무수정** (영향 확인만) |
| 테스트 | `opal/tools/code-scan/tests/test-shard-policy.js` | 083 신규 계약 테스트 (2축·3단 해석·`split`·`--plan`·격리) | 신규 |
| 테스트 | `opal/tools/code-scan/tests/test-shard.js` | 082 계약 테스트 1,032줄 — S-15~S-17·S-25 주소 이전 대상 | 수정 |
| 테스트 | `opal/tools/code-scan/tests/fixtures/shard-violations/oversize{,-shard}/` | 크기 상한 픽스처 2종 | 수정 (정책 이전) |
| 테스트 | `opal/tools/code-scan/tests/fixtures/shard-goal/{before,mid-undeclared,mid-duplicate}/` | 목표달성 픽스처 3종 | 수정 (정책 이전) |
| 테스트 | `opal/tools/code-scan/tests/fixtures/shard-policy/` | 083 신규 픽스처 트리 (2축·3단·가짜 홈·split 대상) | 신규 |
| 테스트 | `opal/tools/code-scan/tests/fixtures/golden/*` (8파일) | 회귀 기준선 | **금지 — 바이트 diff 0** |
| 배포 | `opal/core/setting.default.json` | 전역 설정 기본값 원본 | 수정 (F-010) |
| 배포 | `scripts/install-mac.sh` | `install_opal_setting`(`:918-953`) 시드 지점 | 수정 (F-010) |
| 문서 | `opal/core/references/tools.md` | code-scan 절(`:202-343`) + 변경이력 | 수정 (F-009) |
| 문서 | `opal/core/references/harness/header-rules.md` | 워커 권한 경계(`:44-49`) + 변경이력 | 수정 (F-009) |
| 문서 | `docs/ARCHITECTURE.md` · `docs/PROJECT.md` | 도구 구조 서술 | 수정 (F-009, opal-task-agent — PM Gate 정정) |
| 문서(입력) | `{설계}/사전/표준단어사전.md` | 사다리 S1~S3의 대조 사전 (**옵셔널**) | **읽기 전용** (F-011) |
| 설정 | `{프로젝트}/.opal/code-scan.json` | 083 정책 키가 실제로 놓일 파일 (현행: `headerSource: "inline"` + `scopes` 3종) | **본 태스크에서는 무수정** (스키마만 지원, 이 프로젝트 적용은 별건) |

### F-001: 정책 스키마 2축화 + 3단 해석

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:67-70` 샤드 상수 블록 | `SHARDS_DIR`·`SHARD_LABEL_RE`·`DEFAULT_MANIFEST_MAX_BYTES` | 수정 |
| 도구 | `code-scan.js:217-253` `loadConfig` | `.opal/code-scan.json` 로더 + `scopes` 정규화 | 수정 (스키마 게이트 추가) |
| 도구 | `code-scan.js:880-884` `manifestMaxBytes(ctx)` | 082가 봉인한 값 읽기 1곳 | **대체** |
| 도구 | `code-scan.js:2371-2380` config 스키마 게이트 | `config_scope_invalid` → `code_scan_config_invalid` exit 1 | 수정 (조건 확장) |

#### 2.1.2 현재 구현
- 기본값은 상수 1개다 — `DEFAULT_MANIFEST_MAX_BYTES = 20480` (`code-scan.js:70`). 주석에 "20 KiB (U-1)"로 082 결정 흔적이 남아 있다.
- 값 읽기는 함수 1곳에 봉인돼 있다 — `manifestMaxBytes(ctx)`는 `ctx.codeMap.index.manifestMaxBytes`가 숫자면 그 값, 아니면 상수를 돌려준다 (`code-scan.js:881-884`). **2층(index 오버라이드 + 상수)이며 전역 설정 층이 없다.**
- `loadConfig`는 `extensions`/`exclude`/`excludePatterns`/`scopes`/`headerSource` 5키만 읽는다(`code-scan.js:243-252`). `configError`는 단일 문자열 필드로 `config_parse_failed` | `config_scope_invalid` 2값을 갖는다.
- [MUST] `code-scan.js:215-216`: "이 함수는 process.exit / throw 하지 않는다: code-map-hook.js가 main()을 거치지 않고 직접 호출하므로 여기서 종료하면 PostToolUse fail-safe가 붕괴한다" — 083의 스키마 게이트도 이 계약을 지켜야 한다(에러는 `configError`로만 표면화).
- 판정 1곳 봉인 선례: `resolveHeaderSource`(`code-scan.js:263`)가 CLI > 전역 config 2층을 실행당 1회 판정하고, 확정값은 `ctx.headerSource`로만 전파된다(`code-scan.js:886-891`).

#### 2.1.3 영향 범위
- **상류**: `main()`(`code-scan.js:2351`) → `loadConfig` → `resolveHeaderSource` → `buildCtx`. `code-map-hook.js`가 `loadConfig`를 별도로 직접 호출한다(fail-safe).
- **하류**: `manifestMaxBytes(ctx)` 소비 2곳 — `cmdScaffold`(`code-scan.js:1852`), `cmdValidate.checkOversize`(`code-scan.js:2148`).
- **테스트**: `tests/test-shard.js` S-16 (a)~(e)(`:434-501`)가 `index.json` 주소로 이 값을 조작한다. `tests/test-regression.js` TS-063(`:557`)이 픽스처 전량의 `.opal/code-scan.json`을 walk하며 스키마를 단언한다 — 새 키 추가가 이 검사와 충돌하지 않음을 확인해야 한다(현행 검사는 `headerSource` 정규식만 본다, `:565`).

### F-002: 전역 설정 로더 신설

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:29-31` require 블록 | `fs`/`path`/`child_process` | 수정 (`os` 추가) |
| 도구 | `code-scan.js:217` `loadConfig` 인접 | 신규 로더 배치 지점 | 신규 함수 |
| 도구 | `code-scan.js:384-388` `noticeOnce` | 비차단 사유 노출 창구 (1회성·stderr 전용) | 재사용 |

#### 2.2.2 현재 구현
- code-scan이 읽는 설정 파일은 **2개뿐**이다 — `{프로젝트}/.opal/code-scan.json`(`code-scan.js:218`)과 `{프로젝트}/.opal/code-map/index.json`(`code-scan.js:840`). **전역 설정 소비 선례가 0건이다.**
- `require`에 `os`가 없다 (`code-scan.js:29-31`은 `fs`/`path`/`child_process`만). 이 파일은 `node:` 접두 없는 `require('fs')` 스타일을 쓴다 — 신규 require도 같은 스타일을 따른다.
- 비차단 안내 창구가 이미 2종 있다 — `deprecationOnce(key, message)`(폐기 안내, `code-scan.js:376-380`)와 `noticeOnce(key, message)`(비차단 사유 노출, `:384-388`). 둘은 `_deprecationSeen` Set을 공유하여 **키별 실행당 1회**를 보장하고 전량 stderr로만 쓴다 — 그 이유가 주석에 명시돼 있다: "stdout JSON을 오염시키지 않는다 (brain_tool.py:793 json.loads 보호)" (`code-scan.js:373`).
- 전역 설정 파일의 현행 스키마는 최상위 2키다 — `bootstrap`(`"on"`)과 `models`(`platform` + 플랫폼별 `light`/`standard`/`advanced` + `_help`). `~/.opal/setting.json` 및 원본 `opal/core/setting.default.json` 양쪽에서 확인.

#### 2.2.3 영향 범위
- **상류**: F-001의 `resolveShardPolicy`만 호출한다(지연 로딩). 다른 명령 경로는 이 함수를 부르지 않는다.
- **하류**: 없음(순수 읽기).
- **부수효과 위험(H-13)**: `buildCtx`에서 즉시 로딩하면 조회 8커맨드도 전역 파일을 읽게 되어 골든 경로에 새 I/O가 끼어든다 → **지연 로딩으로 회피**(§3.2.2 (B)).
- **테스트**: 신규 격리 하네스가 전 테스트 파일의 `spawnSync` 옵션에 `OPAL_HOME`을 주입해야 한다. 현행 하네스 중 `env`를 명시하는 곳은 4개뿐이다(`test-header-source.js:93`, `test-resolve-header.js:117`, `test-regression.js:467`·`:586`, `test-shard.js:876`, `test-scope-filter.js:103`) — 나머지는 부모 env를 상속한다.

### F-003: 2축 판정

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:2145-2152` `checkOversize` | validate 크기 검사 (베이스·샤드 양쪽 호출) | 수정 |
| 도구 | `code-scan.js:1852` · `:1913-1919` | scaffold 상한 소비 + stderr 경고 | 수정 |

#### 2.3.2 현재 구현
- `checkOversize(manifestAbs, manifestRel)`는 `fs.statSync(manifestAbs).size`만 보고 `size > limit`이면 위반을 push한다 (`code-scan.js:2146-2152`). **엔트리 수를 보지 않는다.**
- 호출 지점 2곳: 베이스(`code-scan.js:2204`, `manifest` 객체가 이미 스코프에 있음)와 각 샤드(`:2225`, `s.manifest`가 이미 스코프에 있음) — **엔트리 수 계산에 필요한 매니페스트 객체가 두 호출 지점에 모두 이미 존재한다**(신규 파일 읽기 불필요).
- scaffold는 직렬화 문자열의 `Buffer.byteLength(serialized)`를 쓰고(`code-scan.js:1914`), 같은 스코프에 `mergeManifest` 결과 `manifest`가 있어 엔트리 수를 즉시 셀 수 있다(`:1896`).
- 비차단 계약: `manifest_oversize`는 `blockingViolations` 필터에서 제외된다 (`code-scan.js:2290-2292`). `counts.manifest_oversize`는 고정 키다(`:2285`).

#### 2.3.3 영향 범위
- **하류**: `counts.manifest_oversize` 집계(`code-scan.js:2285`) · 비차단 필터(`:2290-2292`) — 둘 다 code 값만 보므로 무변경.
- **테스트 파괴 위험(H-2)**: 082 픽스처 엔트리 수 실측 — `shard-violations/oversize/.opal/code-map/svc/mod.json` **2엔트리**(A.ts·B.ts), `shard-goal/before/.opal/code-map/svc/mod.json` **6엔트리**, `oversize-shard`의 베이스는 `files: {}` **0엔트리** + 샤드 `core.json`이 엔트리 보유. 하한 40이 기본값으로 들어가면 이 전부가 판정에서 탈락한다.

### F-004: 분할 제안 `split --plan` (사다리 엔진 + 검토 장치 3종)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:150-194` `parseArgs` | 플래그 파서 | 수정 (`--groups`·`--plan`·`--trace`·`--stop-after` 추가, `--out` 재사용) |
| 도구 | `code-scan.js:72-129` `USAGE` | 도움말 문자열 | 수정 |
| 도구 | `code-scan.js:2382-2396` `commands` 디스패치 표 | 13 서브명령 | 수정 (`split` 1행 추가) |
| 도구 | `code-scan.js` `cmdScaffold` 인접 | 신규 `cmdSplit` + 사다리 엔진 배치 | 신규 함수 |
| 도구 | `code-scan.js:1036-1069` `resolveShards.byKey` | 합집합 엔트리 원천 | **무수정 재사용** |

#### 2.4.2 현재 구현
- 서브명령은 `commands` 객체 1곳에 등록된다 (`code-scan.js:2382-2396`, 13개). 미등록 명령은 `Unknown command` + exit 1(`:2399-2402`).
- 위치 인자는 `opts.commandArg` 1개만 받는다 (`code-scan.js:187`). `scan`만 `targetPath`로 승격한다(`:192`).
- `--out`은 `opts.discoverOut`에 담기고 소비 지점은 `cmdDiscover` 1곳뿐이다 (`code-scan.js:164`·`:178`·`:1634`) — **재사용 시 참조 3곳만 손대면 된다.**
- `--dry-run`은 `opts.dryRun` 공용 플래그다 (`code-scan.js:179`), discover·scaffold가 공유한다.
- 합집합 엔트리 조회는 `resolveShards(...).byKey`가 제공한다 (`code-scan.js:1036-1069`) — `owner: 'base' | 'shard'`와 `label`이 실려 있어 "베이스에 남은 엔트리"를 필터링할 수 있다.
- **사다리 S5의 입력이 이미 존재한다**: `depends`는 워커 기입 필드로 정의돼 있고(`code-scan.js:62` `WORKER_FIELDS = ['description','exports','depends','note','feature']`), 매니페스트 엔트리에 그대로 실린다 — S5는 **신규 데이터 수집 없이** 기존 필드를 읽는다.
- **분류에 쓸 수 있는 엔트리 필드 실측**: `description`(서술) · `exports` · `depends` · `note` · `feature`. 초안이 쓴 것은 **파일명 키 하나뿐**이었고 나머지는 미사용이었다 — 사다리 S5가 `depends`를 추가로 쓰면서 사용 축이 1개에서 2개로 늘어난다.

#### 2.4.3 영향 범위
- **상류**: `main()` 디스패치. `USAGE` 문자열은 `--help` 출력이며 골든 대상이 아니다(골든 8커맨드는 `scan`/`domain`/`layer`/`search`/`exports`/`summary`/`depends`/`missing`, `tests/test-regression.js:89-98`).
- **하류**: F-005 `split --groups`가 이 출력 스키마를 **입력으로 소비**한다(U-1 왕복). 사다리가 추가하는 `stage`·`assignments`·`trace`는 전부 **선택 필드**여야 왕복이 유지된다(H-18).
- **신규 상류 1건**: F-011 사전 로더. 사전이 `null`이면 `dict: true` 단계가 skip되므로 F-004는 **F-011 실패에 대해 무조건 진행 가능**하다 — 의존은 있으나 차단 의존이 아니다.
- **`--out` 재사용 리스크**: `opts.discoverOut` 필드명을 `opts.out`으로 개명하면 `cmdDiscover:1634` 1줄이 따라 바뀐다. 개명하지 않고 필드를 공유해도 동작하지만 이름이 오해를 부른다 → §3.4.2 (A)에서 개명 채택.

### F-011: 용어사전 로더

#### 2.11.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js` `loadGlobalSetting` 인접 | 신규 `resolveDictPath`·`parseWordDictionary`·`loadWordDictionary` | 신규 함수 |
| 도구 | `code-scan.js:384-388` `noticeOnce` | 비차단 사유 노출 창구 | 재사용 |
| 도구 | `code-scan.js:40-46` `DEFAULT_CONFIG` / `normalizeShardPolicy` | `shardPolicy.dictPath` 키 추가 | 수정 (§3.1.2 (A)(B) 개정) |
| 문서(입력) | `docs/PROJECT.md` | `{설계}` 경로 변수 원천 | **읽기 전용** |
| 문서(입력) | `{설계}/사전/표준단어사전.md` | 사전 SSOT | **읽기 전용** |

#### 2.11.2 현재 구현
- **code-scan이 읽는 파일은 3종뿐이다** — `{프로젝트}/.opal/code-scan.json`(`code-scan.js:218`) · `{프로젝트}/.opal/code-map/index.json`(`:840`) · (083 F-002 신설) `{OPAL_HOME}/setting.json`. **`.opal/` 밖 문서를 읽은 전례가 0건**이다(H-17).
- 사전 md 스키마 실측 (`opal/skills/op-data-dictionary/SKILL.md:74-90`) — **한 문서에 컬럼 수가 다른 표 2개**가 있다:
  - `## 수식어` — `| 한글 | 영문 | 약어 | 규칙 | 도메인 | 비고 |` (6열)
  - `## 분류어` — `| 한글 | 영문 | 약어 | 도메인 | 비고 |` (5열, `규칙` 없음)
  - → **위치 기반 파싱은 즉시 깨진다**(H-15). 헤더 이름으로 컬럼 인덱스를 얻어야 한다.
- 경로 규칙 실측 — [MUST] `opal/skills/op-data-dictionary/SKILL.md:21`: "사전 저장 경로는 하드코딩하지 않는다. `docs/PROJECT.md`에 등록된 `{설계}` 변수(설계 산출물 루트)를 읽어 `{설계}/사전/`으로 해소한다. PROJECT.md에 경로가 미등록된 경우: ① 루트에 `200.설계/` 디렉토리 탐색 → ② 없으면 default `200.설계/210.사전/` 제안 후 사용자 확인."
- **자기모순 발견(H-19)**: 같은 SKILL.md가 `:21`에서는 default를 `200.설계/210.사전/`로, `:72`·`:172`에서는 `{설계}/사전/`(`{설계}` default `200.설계` → `200.설계/사전/`)로 적는다. 두 경로가 다르다.
- **이 프로젝트 실측**: `docs/PROJECT.md`에 `{설계}` 변수 등록이 **없고**, `200.설계/` 디렉토리도 **없다** → 083 개발 중에는 사전 탐색이 3단 전부 실패하는 것이 **정상 경로**다. 즉 "사전 없음" 분기가 이 저장소의 기본 상태이며, 옵셔널 설계가 필수인 실증 근거다.

#### 2.11.3 영향 범위
- **상류**: F-004 사다리 S1~S3만. 다른 명령(`scan`·`validate`·`scaffold`·`target` 등)은 사전을 읽지 않는다 — `split --plan` 경로에서만 지연 로딩한다(골든 무영향, H-13과 동일 논리).
- **하류**: 없음(순수 읽기). **쓰기 경로가 존재하지 않는다** — 사전은 `op-data-dictionary`(`opal-db-agent`)의 산출물이며 code-scan은 소비자일 뿐이다.
- **권한 경계**: [MUST] `opal/skills/op-data-dictionary/SKILL.md` §제외 출력 계열 규칙 — 사전 md가 SSOT이고 파생물 역방향 수정은 금지다. code-scan은 **읽기만** 하므로 이 경계를 침범하지 않는다.

### F-012: `code-scan init` 서브명령

#### 2.12.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:2351-2370` `main()` 진입부 | 명령 디스패치 + 전 명령 차단 게이트 | 수정 (**게이트 앞에 `init` 분기**) |
| 도구 | `code-scan.js:1555-1582` `inferScopes` | 디렉토리 스캔 폴백 경로 보유 | **재사용** |
| 도구 | `code-scan.js:1637-1639` `index_exists` 거부 | 기존 파일 보호 관용 | 패턴 계승 |
| 도구 | `code-scan.js:263-320` `resolveHeaderSource` | 값 도메인 판정 1곳 | **재사용** (재검증 로직 신설 금지) |
| 도구 | `code-scan.js` `cmdDiscover` 인접 | 신규 `cmdInit` + 추론 헬퍼 | 신규 함수 |
| 문서(입력) | `docs/PROJECT.md §프로젝트 구성` | `scopes` 추론 소스 | **읽기 전용** |
| 문서 | `opal/core/references/pm/code-scan-management.md` | **규약 SSOT** — `init` 등재 대상 | 수정 (F-009와 같은 Step) |

#### 2.12.2 현재 구현

- **규약이 이미 산문으로 존재한다** (`opal/core/references/pm/code-scan-management.md`) — 083은 **새 규칙을 발명하는 것이 아니라 이 산문을 코드로 이식**한다.
  - [MUST] `:12`: "PM이 code-scan을 첫 호출하는 시점에 `.opal/code-scan.json`이 부재하면, 즉석 추론으로 생성한 뒤 호출을 진행한다. 단 `headerSource`만은 추론 대상이 아니다."
  - [MUST] `:21`: "`headerSource` | **추론 금지** | PM이 소유자에게 2택을 확인해 확정한다. 확인 전에는 파일을 생성하지 않는다."
  - [MUST] `:87`: "**도구는 이 질문을 하지 않는다 — 비대화형을 유지한다.** 도구의 역할은 거부와 안내까지이고, 값의 확정은 소유자, 중개는 PM의 몫이다."
  - → `:87`이 이번 설계의 핵심 근거다. **대화형 프롬프트를 만들지 않고 `--header-source`를 필수 인자로 받는 것**이 규약의 직접 이행이지 이탈이 아니다.
- **추론 소스 규약 표**가 `:16-21`에 4행으로 존재하고, **최소 구조 예시**가 `:25-33`에, **생성 보고 1줄 형식**이 `:44-46`에 있다.
- **현행 도구에는 `init`이 없다** — 13 서브명령(`code-scan.js:2382-2396`)에 설정 파일을 만드는 명령이 0건이다. `discover`는 `.opal/code-map/index.json`(다른 파일)을 만든다.
- **`main()`의 전 명령 차단 게이트** (`code-scan.js:2362-2367`): `resolveHeaderSource`가 실패하면 `errorExit`으로 **모든 명령이 exit 1**이 된다. `help`/`version`만 그 앞에서 반환된다(`:2354-2355`). → **`init`을 게이트 뒤에 두면 순환이 생긴다**(H-22): 설정이 없어서 `init`이 거부되고, `init`을 못 돌려 설정을 못 만든다.
- **재사용 가능한 추론 자산**: `inferScopes`의 디렉토리 스캔 폴백(`code-scan.js:1571-1582`)이 "루트 1-depth 디렉토리 스캔"을 이미 구현한다 — 규약 `:18`의 폴백 규칙과 **동일한 동작**이다. `config.scopes`가 비어 있을 때만 이 경로를 타므로(`:1559`), 설정 부재 상황에서 그대로 쓸 수 있다.
- **기존 파일 보호 관용**: `cmdDiscover`가 `if (!dryRun && fs.existsSync(outPath)) return errorExit('index_exists')`로 거부한다(`code-scan.js:1637-1639`). `init`도 같은 형태를 따른다.

#### 2.12.3 영향 범위

- **상류**: PM(`opal-pm.md` §9 경유 규약), 워커 에이전트, PostToolUse hook. **전부 TTY가 없는 경로**다 — 대화형 프롬프트를 넣으면 이 3경로가 모두 멈춘다.
- **하류**: `.opal/code-scan.json` 1파일. 이 파일이 F-001의 3단 해석 1순위 소스이자 `headerSource` 게이트의 입력이므로, **잘못 쓰면 프로젝트 전체 명령이 막힌다**(H-21).
- **`docs/PROJECT.md` 표 실측** (`:152-160`): 컬럼은 `| 요소 | 경로 | 기술 스택 | 전문 에이전트 |`이고 3행이다 — `Framework`/`` `opal/`, `skills/`, `agents/` `` · `Console FE`/`` `dashboard/frontend/` `` · `Console BE`/`` `dashboard/backend/` ``.
- **추론 검증 가능성(강한 근거)**: 이 저장소의 실제 `.opal/code-scan.json`은 `{"framework": "opal/", "console-fe": "dashboard/frontend/src/", "console-be": "dashboard/backend/"}`다. **요소명을 kebab 소문자로 변환하면 스코프 이름 3종이 정확히 일치한다**(`Framework`→`framework`, `Console FE`→`console-fe`, `Console BE`→`console-be`). 즉 규약대로 추론하면 사람이 만든 결과와 같은 이름이 나온다 — H-20 검증의 실측 기준선이 된다.
- **알려진 한계 2건**(초안이므로 소유자가 보강): ① `경로` 컬럼에 값이 여러 개일 때(`Framework`는 3개) `scopes` 값은 문자열 1개이므로 **첫 경로만** 채택된다 — 실제 파일도 `"opal/"` 하나만 쓰고 있어 동일하다. ② `console-fe`의 실제 값은 `dashboard/frontend/**src/**`인데 표에는 `dashboard/frontend/`까지만 있다 — **추론은 표까지만 하고 `src/` 심화는 소유자 몫**이다.

### F-005: 분할 집행 `split --groups`

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js` `cmdSplit` | F-004와 동일 함수 (mode 분기) | 신규 |
| 도구 | `code-scan.js:1002-1074` `resolveShards` | 샤드 해석 봉인 1곳 | **무수정 재사용** |
| 도구 | `code-scan.js:893-905` `loadManifest` | 매니페스트 캐시 로더 | 재사용 (캐시 clear 필요) |
| 도구 | `code-scan.js:984-991` `isShardManifestPath`·`baseManifestAbsForShard` | 샤드 경로 판별 | 재사용 |

#### 2.5.2 현재 구현
- 매니페스트를 쓰는 명령은 현재 `cmdScaffold` 1개뿐이다. 쓰기 방식은 단순 순차다 — `mkdirSync(recursive) → writeFileSync`, 원자성 장치 없음 (`code-scan.js:1902-1905`).
- 직렬화 포맷이 고정돼 있다 — `JSON.stringify(manifest, null, 2) + '\n'` (`code-scan.js:1897`). `split`도 **같은 포맷**을 써야 이후 `scaffold`가 no-op(`unchanged`)이 된다 (F-3 AC "scaffold가 no-op").
- 샤드 매니페스트 형태는 베이스와 동일하며 `{version, scope, dir, files}` + 선택 `package`다 (`tests/test-shard.js:181-185` `deriveAfterTree`가 만드는 형태, `resolveShards`가 `s.manifest.package`를 3단 상속에 쓴다 `code-scan.js:1066`).
- 베이스의 `shards` 배열은 `mergeManifest`가 보존한다 — `if (existing && hasOwn(existing, 'shards')) manifest.shards = existing.shards;` (`code-scan.js:1765`). 즉 `split`이 `shards`를 심어두면 이후 `scaffold`가 지우지 않는다.
- 샤드 경로 조립 규칙: `{dir}/{stem}/_shards/{label}.json` (`code-scan.js:1027-1029`). 라벨은 `SHARD_LABEL_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/`(`:69`)로 경로 이탈이 차단된다.
- 캐시 2종: `ctx.codeMap.manifests`(경로→파싱 객체, `code-scan.js:894`) · `ctx.codeMap.shardViews`(베이스경로→ShardView, `:1009-1010`). 쓰기 후 재검증에는 **둘 다 비워야** 한다.
- 모드 게이트: `resolveShards`는 `ctx.headerSource !== 'manifest'`면 즉시 null이다 (`code-scan.js:1004`) — inline 모드에서는 샤드 개념 자체가 없다.

#### 2.5.3 영향 범위
- **하류(자산)**: `.opal/code-map/{scope}/…` 매니페스트 파일들. 실패 시 부분 상태 = 엔트리 유실(H-6, 제약 ⑥).
- **후속 명령**: `validate`(위반 0건이어야 함) · `scaffold`(no-op이어야 함) · `target`(보유 샤드 라우팅) — F-3 AC의 검증 3축.
- **워커 권한 경계**: `header-rules.md:49`가 `shards`·`files` 키 목록(추가/삭제)을 **도구 관할**로 분류한다 — `split`이 쓰는 필드가 정확히 이 관할이므로 신규 권한 확장이 아니라 기존 관할의 집행 수단 추가다.

### F-006: 유도 경로

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:2149-2151` 위반 push | `manifest_oversize` 페이로드 | 수정 (필드 추가) |
| 도구 | `code-scan.js:1915-1919` scaffold stderr | 초과 경고 1줄 | 수정 (명령 병기) |
| 문서 | `opal/core/references/tools.md` | 분할 절차 문서화 | 수정 (F-009와 통합) |

#### 2.6.2 현재 구현
- 위반 객체는 `{ code, manifest, detail }` 3필드다 (`code-scan.js:2150`). `detail`은 `` `${size}/${limit}` `` 문자열.
- scaffold의 경고 문구는 이미 분할을 권하지만 **수단을 가리키지 않는다** — "`_shards/` 의미 단위 분할을 검토하세요" (`code-scan.js:1918`).
- 다른 위반 code들은 `sub`·`key`·`file` 선택 필드를 자유롭게 붙인다 (`code-scan.js:2124`·`:2201`·`:2245`) — **위반 객체에 선택 필드를 추가하는 것은 기존 관용이다.**

#### 2.6.3 영향 범위
- **소비자**: `validate --json` 출력을 읽는 brain-tool(`brain_tool.py` json.loads 경로) · CLOSE 게이트(`header-rules.md:40` (b)) · 사람. 필드 추가는 additive이므로 기존 소비자 무영향.
- **단언 충돌(H-8)**: `tests/test-shard.js:415`가 `detail`을 정확히 단언 → **포맷 불변 + 필드 추가**로 회피.

### F-007: 구 위치 키 이전 처리

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:869-876` | `manifestMaxBytes` 스키마 게이트 | **제거** + `deprecationOnce` 대체 |
| 도구 | `code-scan.js:880-884` | `manifestMaxBytes(ctx)` 헬퍼 | **제거** (F-001의 `resolveShardPolicy`가 대체) |

#### 2.7.2 현재 구현
- 게이트는 `hasOwn(index, 'manifestMaxBytes')`일 때 `typeof v !== 'number' || !Number.isFinite(v) || v <= 0`이면 `invalid_index`를 반환한다 (`code-scan.js:871-876`). 주석에 082의 설계 의도가 남아 있다: "신규 에러 코드를 만들지 않고 기존 invalid_index로 합류한다".
- `invalid_index`는 `buildCtx`에서 `CodeMapFatalError`로 승격되어(`code-scan.js:889`) `main()`의 catch → `errorExit` → **exit 1**이 된다 (`:2404-2409`, `:805-810`).
- 폐기 키 무시 선례 3곳: `config_scope_header_source`(`code-scan.js:430`), `index_scope_header_source`(`:451`), `index_scope_readonly`(`:460`) — **전부 타입 검증 없이 무시 + `deprecationOnce`**다.
- 마이그레이션 안내 선례: `resolveHeaderSource`가 구형 값 `auto`에 대해 "자동 변환하지 않습니다"를 명시한다 (`code-scan.js:311-314`).

#### 2.7.3 영향 범위
- **테스트(H-9)**: `tests/test-shard.js:489-501` S-16 (e)가 문자열·음수 값에서 `exit 1` + `error === 'invalid_index'`를 단언한다 → 주소 이전 필요.
- **픽스처**: `manifestMaxBytes`를 보유한 픽스처 5종(실측) — `shard-violations/oversize`(200) · `shard-violations/oversize-shard`(200) · `shard-goal/before`(400) · `shard-goal/mid-undeclared`(400) · `shard-goal/mid-duplicate`(400).
- **자산 위험 0**: 이 프로젝트의 `.opal/code-map/`은 부재하고(`code-scan.js:9` note: "code-scan.js 자신은 프로젝트 .opal/code-map/index.json 부재로 인라인 전용 모드로 스캔됨"), 구 위치 사용 프로젝트는 0건이다(TASK U-6).

### F-008: 회귀 가드 + 전역 설정 격리

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 테스트 | `tests/test-shard-policy.js` | 083 신규 계약 테스트 | 신규 |
| 테스트 | `tests/test-shard.js` | 082 계약 — S-15/S-16/S-17/S-25 주소 이전 | 수정 |
| 테스트 | `tests/fixtures/shard-policy/**` | 083 신규 픽스처 | 신규 |
| 테스트 | `tests/fixtures/shard-violations/oversize{,-shard}/.opal/{code-scan.json,code-map/index.json}` | 정책 주소 이전 | 수정 (4파일) |
| 테스트 | `tests/fixtures/shard-goal/{before,mid-undeclared,mid-duplicate}/.opal/{code-scan.json,code-map/index.json}` | 정책 주소 이전 | 수정 (6파일) |

#### 2.8.2 현재 구현
- 테스트는 11 스크립트 5,928줄이며 전량 `node:test` + `spawnSync` CLI 블랙박스다. 러너 스크립트·`package.json`은 없다 — `node --test` 또는 파일 직접 실행.
- 픽스처 계약 검사가 이미 존재한다 — `tests/test-regression.js:557-569` TS-063이 `fixtures/**/.opal/code-scan.json`을 전량 walk하며 20종 이상 + `headerSource` 2택 명시를 단언한다. **083이 픽스처 설정을 만질 때 이 검사를 깨지 않아야 한다**(정규식이 `headerSource`만 보므로 키 추가는 안전).
- 골든 검증은 `tests/test-regression.js:503-511`에서 8커맨드 stdout을 바이트 비교한다. 캡처 조건이 `fixtures/golden/README.md`에 기록돼 있고 그 기록 자체를 TS-061(`:522-539`)이 단언한다.
- 격리 선례: `tests/test-regression.js:467`이 `env: Object.assign({}, process.env, { HOME: path.join(root, 'fakehome') })`로 가짜 홈을 주입한다 — brain-tool 격리 목적.

#### 2.8.3 영향 범위
- **전 테스트 파일**: `OPAL_HOME` 주입이 필요한 범위 판단 — 전역 정책이 결과에 영향을 주는 명령은 `validate`·`scaffold`·`split` 3종이다. 조회 8커맨드는 정책을 읽지 않으므로(지연 로딩, §3.2.2 (B)) 골든 경로는 주입 없이도 안전하다. 그러나 **결정론을 위해 정책 소비 명령을 실행하는 테스트 파일 전량에 주입**한다(§3.8.2 (B)).
- **RED-first**: 신규 테스트는 구현 전에 작성되어 실패해야 한다 ([MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 테스트 파일 수정 금지, `tests/test-shard.js:19-21`에 선례 기재).

### F-009: 문서·배포 반영 / F-010: 전역 설정 시드

#### 2.9.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `code-scan.js:37` `VERSION` | `'1.5.0'` | 수정 → `1.6.0` |
| 도구 | `code-scan.js:2-11` 상단 `@header` | description·note | 수정 |
| 도구 | `code-scan.js:2429-2474` 변경이력 | v1.0.0~v1.5.0 | 수정 (v1.6.0 행 추가) |
| 문서 | `opal/core/references/tools.md:202-343` | code-scan 절 | 수정 |
| 문서 | `opal/core/references/harness/header-rules.md:44-49` | 워커 권한 경계 | 수정 |
| 배포 | `opal/core/setting.default.json` | 전역 기본값 원본 (`bootstrap`·`models` 2키) | 수정 (`shardPolicy` 추가) |
| 배포 | `scripts/install-mac.sh:918-953` `install_opal_setting` | setting.json 시드 | 수정 |

#### 2.9.2 현재 구현
- `install_opal_setting`은 2경로다 — 파일 부재 시 `cp "$src" "$dst"`(`install-mac.sh:951`), 존재 시 인라인 python으로 `models` 키만 scaffold 병합(`:923-948`).
- **결함(H-11)**: 병합 경로가 `if 'models' in existing: sys.stderr.write(...); sys.exit(0)`로 **조기 종료**한다 (`install-mac.sh:937-939`). 기존 설치 환경은 전부 `models`를 이미 갖고 있으므로(`~/.opal/setting.json` 실측 확인) 이 구조를 그대로 두면 `shardPolicy`가 **영구히 시드되지 않는다**.
- 머지 안전 계약: 실패 시 `warn "setting.json models 병합 실패 — 기존 파일 유지"`로 기존 파일을 보존한다 (`install-mac.sh:923`). `bootstrap` 등 다른 키는 dict를 유지하므로 무손실이다.
- `tools.md` code-scan 절은 `:202-343`이며 커맨드 목록·에러 코드 표·프로젝트 설정 예시·PM 관리 방안(`:388-`) 하위 절을 포함한다. 파일 말미에 `변경이력` 표가 있다(`:956-`).
- `header-rules.md:49`가 금지(도구 관할) 필드에 `shards`를 이미 포함한다(082 v1.6에서 추가, `:157`).

#### 2.9.3 영향 범위
- **`tools.md` 단언**: `tests/test-shard.js:601-604` S-22가 `tools.md`에서 `manifestMaxBytes` 문자열 존재를 정규식으로 단언한다 → **083이 이 문자열을 제거하면 깨진다.** 폐기 안내 맥락으로 문자열을 유지하거나 단언을 083 신규 키로 이전해야 한다(§3.9.2 (C)).
- **배포**: `~/.opal/tools/code-scan/`는 install 산출물이므로 직접 편집 금지(제약 ①). 검증은 소스에서 `node opal/tools/code-scan/code-scan.js …`로 수행한다.

---

## 3. 기능별 설계

### F-001: 정책 스키마 2축화 + 3단 해석

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | 상수 블록 교체(`:70` `DEFAULT_MANIFEST_MAX_BYTES` 제거 → `DEFAULT_SHARD_POLICY` 외 4개 신설) / `DEFAULT_CONFIG`에 `shardPolicy: {}`(`:40-46`) / `normalizeShardPolicy` 신설 / `loadConfig` 반환에 `shardPolicy` + `configError` 3값화(`:243-252`) / `resolveShardPolicy` 신설 / `manifestMaxBytes(ctx)` 제거(`:880-884`) / `main()` config 게이트 조건 확장(`:2373`) | `code-scan.js:70`·`:217-253`·`:880-884`·`:2373-2380` |

#### 3.1.2 설계

##### (A) 상수 블록 — 082 블록(`code-scan.js:67-70`) 말미 교체

```js
// ── shard policy constants (083) ─────────────────────────────────────────
// [MUST] 이 상수는 resolveShardPolicy 본문 밖에서 참조하지 않는다 — 정책 판정 1곳 봉인(제약 ③).
const DEFAULT_SHARD_POLICY = Object.freeze({ maxBytes: 10240, minFiles: 40, dictPath: null });
// 키별 타입 — 값 타입이 섞이므로(정수 2 + 경로 1) 키 배열이 아니라 스키마 표로 둔다 (U-2 개정)
const SHARD_POLICY_SCHEMA = Object.freeze({
  maxBytes: 'positiveInt',      // 바이트 상한
  minFiles: 'positiveInt',      // 엔트리 수 하한
  dictPath: 'nonEmptyString',   // 표준단어사전 명시 경로 (선택, 탐색 3단의 1순위 — U-2 (4))
});
const SHARD_POLICY_KEYS = Object.keys(SHARD_POLICY_SCHEMA);   // 알 수 없는 키는 무시 — U-5 (C)
const SHARD_TARGET_RATIO = 0.75;                      // 조각 목표 = 상한 × 비율 (확정 방향 #9)
const OPAL_HOME_ENV = 'OPAL_HOME';                    // 홈 경로 주입 창구 (U-7)
```

- `DEFAULT_MANIFEST_MAX_BYTES = 20480`(`code-scan.js:70`)은 **삭제**한다 — 값을 한 세트로 묶어 상수 식별자를 1개로 유지하는 것이 봉인 정적 검사(H-12)를 단순하게 만든다.
- `SHARD_PLAN_MIN_GROUP`(초안의 그룹 채택 임계 상수)은 **삭제**한다 — U-2 개정으로 채택 임계가 단계별로 달라졌으므로(S1~S3 = 2, S4~S5 = 3) 사다리 정의(`SHARD_PLAN_LADDER`, §3.4.2 (C))의 `accept` 필드가 그 역할을 대신한다. 전역 상수 1개와 단계별 값이 병존하면 어느 쪽이 이기는지 규칙이 생긴다.
- `dictPath`가 정책에 들어가는 이유: 사전 경로도 **프로젝트가 덮어쓰는 값**이므로 3단 해석·셀 단위 머지의 이점을 그대로 받는다. 별도 최상위 키로 빼면 `shardPolicy`와 `dictPath`의 우선순위 규칙이 2벌이 된다.
- [MUST] `TASK.md` §확정 방향 #1·#2: 트리거 10240 + 파일 수 하한 40은 "한 세트로 함께 들어간다".

##### (B) `normalizeShardPolicy(raw)` — 전역·프로젝트 공용 스키마 검증 1개 (U-5 (B))

```js
/**
 * shardPolicy 객체 정규화 — 두 소스(code-scan.json · setting.json)가 같은 함수를 공유한다.
 * 알 수 없는 키는 무시한다(U-5 (C)). 알려진 2키는 존재하면 **양의 유한 정수**여야 한다.
 * @param {*} raw
 * @returns {{ok:true, value:{maxBytes?:number, minFiles?:number}} | {ok:false, detail:string}}
 */
function normalizeShardPolicy(raw) {
  if (raw === undefined || raw === null) return { ok: true, value: {} };
  if (typeof raw !== 'object' || Array.isArray(raw)) {
    return { ok: false, detail: 'shardPolicy must be an object' };
  }
  const value = {};
  for (const k of SHARD_POLICY_KEYS) {
    if (!hasOwn(raw, k) || raw[k] === undefined || raw[k] === null) continue;
    const v = raw[k];
    if (SHARD_POLICY_SCHEMA[k] === 'positiveInt') {
      if (typeof v !== 'number' || !Number.isFinite(v) || !Number.isInteger(v) || v <= 0) {
        return { ok: false, detail: `shardPolicy.${k} must be a positive integer, got ${JSON.stringify(v)}` };
      }
    } else {   // 'nonEmptyString'
      if (typeof v !== 'string' || v.trim() === '') {
        return { ok: false, detail: `shardPolicy.${k} must be a non-empty string, got ${JSON.stringify(v)}` };
      }
    }
    value[k] = v;
  }
  return { ok: true, value };
}
```

- 검증 함수를 **1개만** 두는 것이 U-5 (B)의 "전역·프로젝트 동일 형태" 결정의 실질이다 — 형태가 같으므로 정규화도 1벌이다. `normalizePatternList`(`code-scan.js:392-398`)가 include/exclude 두 필드에 같은 판정을 공유하는 선례와 동일한 구조다.

##### (C) `loadConfig` 확장 (`code-scan.js:217-253`)

```js
// DEFAULT_CONFIG (:40-46)에 1키 추가
const DEFAULT_CONFIG = { ..., headerSource: null, shardPolicy: {} };

// loadConfig 본문 — scopes 정규화(:233-241) 직후
const sp = normalizeShardPolicy(user.shardPolicy);

return {
  extensions: ..., exclude: ..., excludePatterns: ..., scopes: ...,
  headerSource: user.headerSource === undefined ? null : user.headerSource,
  shardPolicy: sp.ok ? sp.value : {},                      // 위반 시 빈 객체 → 하위 단계 폴백
  configPresent: true,
  configError: scopeErrorDetail ? 'config_scope_invalid'
             : (sp.ok ? null : 'shard_policy_invalid'),
  configErrorDetail: scopeErrorDetail || (sp.ok ? null : sp.detail),
};
```

- [MUST] `code-scan.js:215-216`: "이 함수는 process.exit / throw 하지 않는다: code-map-hook.js가 main()을 거치지 않고 직접 호출하므로 여기서 종료하면 PostToolUse fail-safe가 붕괴한다" → **스키마 위반은 `configError`로만 표면화**하고 종료는 `main()`이 한다.
- `configError` 우선순위는 `config_parse_failed` > `config_scope_invalid` > `shard_policy_invalid`다. 기존 2값의 판정 순서를 바꾸지 않고 말미에 1값을 덧붙이므로 기존 테스트 경로가 불변이다.

##### (D) `main()` 게이트 조건 확장 (`code-scan.js:2373-2380`) — 새 에러 코드 없음

```js
if (config.configError === 'config_scope_invalid' || config.configError === 'shard_policy_invalid') {
  return errorExit('code_scan_config_invalid', {
    detail: config.configErrorDetail,
    where: 'config',
    fix: config.configError === 'shard_policy_invalid'
      ? '.opal/code-scan.json의 shardPolicy는 {"maxBytes": <양의 정수>, "minFiles": <양의 정수>} 형식이어야 합니다'
      : '.opal/code-scan.json의 scopes 항목은 문자열 또는 {path, include, exclude} 형식이어야 합니다 (include/exclude는 문자열 배열)',
  });
}
```

- U-5 (D) 채택안의 실행 지점. **기존 `code_scan_config_invalid` 창구에 합류**하며 신규 에러 코드를 만들지 않는다 — 082가 `manifestMaxBytes` 타입 위반을 `invalid_index`에 합류시킨 판단(`code-scan.js:870`)과 같은 원칙이다.

##### (E) `resolveShardPolicy(ctx)` — **유일한 정책 판정 지점** (제약 ③)

```js
/**
 * 이 실행의 샤드 정책을 확정한다 — 도구 전체에서 **유일한** 정책 판정 지점이다.
 * 우선순위(셀 단위, U-5 (E)):
 *   {프로젝트}/.opal/code-scan.json > ~/.opal/setting.json > DEFAULT_SHARD_POLICY
 * 파생값 targetBytes는 설정 키가 아니다 — 여기서만 만든다 (U-5 (F), 확정 방향 #9).
 * [MUST] 이 함수 밖에서 DEFAULT_SHARD_POLICY / loadGlobalSetting을 참조하지 않는다.
 * @param {object} ctx {projectRoot, config, codeMap, headerSource}
 * @returns {{maxBytes:number, minFiles:number, targetBytes:number}}
 */
function resolveShardPolicy(ctx) {
  if (ctx._shardPolicy) return ctx._shardPolicy;                  // 실행당 1회
  const project = (ctx.config && ctx.config.shardPolicy) || {};
  const global_ = loadGlobalSetting(resolveOpalHome()).shardPolicy || {};   // 지연 로딩 (F-002)
  const out = {};
  for (const k of SHARD_POLICY_KEYS) {
    out[k] = hasOwn(project, k) ? project[k]
           : hasOwn(global_, k) ? global_[k]
           : DEFAULT_SHARD_POLICY[k];
  }
  out.targetBytes = Math.max(1, Math.floor(out.maxBytes * SHARD_TARGET_RATIO));
  ctx._shardPolicy = out;
  return out;
}
```

- **셀 단위 머지**가 `for (const k of SHARD_POLICY_KEYS)` 루프로 구조적으로 보장된다 — 키마다 독립적으로 3단을 내려가므로 "프로젝트에 `maxBytes`만 적으면 `minFiles`는 전역/상수" (F-1 AC)가 분기 없이 성립한다.
- `manifestMaxBytes(ctx)`(`code-scan.js:880-884`)는 **삭제**한다. 두 함수가 병존하면 정책 읽기 지점이 2곳이 되어 제약 ③ 위반이다(H-3).
- 봉인 정적 검사(H-12): 소스에서 `DEFAULT_SHARD_POLICY`가 상수 선언 1줄 + `resolveShardPolicy` 본문 외에 등장하지 않고, `loadGlobalSetting(` 호출이 `resolveShardPolicy` 본문 1곳에만 있어야 한다 — 082 S-21(`tests/test-shard.js:543`)의 정적 grep 검사와 동일 방식.

##### (F) 3단 해석 결정 표 (결정론 명세)

| `code-scan.json.shardPolicy` | `setting.json.shardPolicy` | 유효 `maxBytes` | 유효 `minFiles` |
|---|---|---|---|
| 부재 | 부재 | 10240 (상수) | 40 (상수) |
| 부재 | `{maxBytes: 8192}` | 8192 | 40 (상수) |
| `{minFiles: 10}` | `{maxBytes: 8192, minFiles: 60}` | 8192 (전역) | **10 (프로젝트 승)** |
| `{maxBytes: 4096, minFiles: 2}` | 무엇이든 | 4096 | 2 |
| `{maxBytes: "big"}` (타입 위반) | 무엇이든 | — | — → **exit 1 `code_scan_config_invalid`** |
| 부재 | `{maxBytes: "big"}` (타입 위반) | 10240 (상수) + `noticeOnce` 1회 | 40 (상수) |
| 부재 | 파일 부재 / 깨진 JSON | 10240 (상수) | 40 (상수) |

#### 3.1.3 환경 변경
해당 없음 (신규 패키지 0개 — 의존성 0 단일 파일 CLI 계약 유지, `code-scan.js:29-31`).

#### 3.1.4 배치/마이그레이션
해당 없음 (F-007이 구 키 이전 안내를 담당하며 자동 변환은 하지 않는다).

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC (상수) | 기능 테스트 | 아무 정책 설정이 없는 트리에서 `maxBytes=10240`·`minFiles=40`이 적용된다 (경계 픽스처로 간접 관측) |
| TS-002 | F-1 AC (전역만) | 기능 테스트 | 가짜 홈 `setting.json`에만 `shardPolicy`가 있으면 그 값이 적용된다 |
| TS-003 | F-1 AC (셀 머지) | 기능 테스트 | 프로젝트에 `minFiles`만 있으면 `maxBytes`는 전역, `minFiles`는 프로젝트 값이 적용된다 |
| TS-004 | F-1 AC (우선순위) | 기능 테스트 | 3층 동시 존재 시 `code-scan.json` > `setting.json` > 상수 순으로 결정론적이다 |
| TS-005 | F-1 AC (타입 위반) | 기능 테스트 | 프로젝트 `shardPolicy` 타입 위반 → exit 1 + `error === 'code_scan_config_invalid'` + `detail`에 위반 키 이름 |
| TS-006 | F-1 AC (알 수 없는 키) | 기능 테스트 | `shardPolicy._help` 문자열이 있어도 거부되지 않고 정상 동작한다 |
| TS-007 | F-1 AC (봉인) | 산출물 검사 | `DEFAULT_SHARD_POLICY`가 상수 선언 + `resolveShardPolicy` 본문 밖에 0회 등장하고, `manifestMaxBytes(` 함수가 소스에 존재하지 않는다 |
| TS-008 | 제약 ③ | 산출물 검사 | `loadGlobalSetting(` 호출이 소스에 정확히 1곳(`resolveShardPolicy` 본문)이다 |

---

### F-002: 전역 설정 로더 신설

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `require('os')` 추가(`:29-31`) / `resolveOpalHome`·`loadGlobalSetting` 신설 (`loadConfig` 인접 `:253` 직후) | `code-scan.js:29-31`·`:217` |

#### 3.2.2 설계

##### (A) `resolveOpalHome()` — 홈 경로 해석 1곳

```js
// [MUST] `opal/tools/state-tool/state_tool.py:236`: "경로는 OPAL_HOME env 우선(플랫폼 독립,
// ~/.opal 하드코딩 분기 금지)." — 같은 규칙을 code-scan에 적용한다. 플랫폼 분기를 만들지 않는다
// (`.opal/AGENT.md` §금지사항 "하드코딩된 플랫폼 분기 추가 금지").
function resolveOpalHome() {
  return process.env[OPAL_HOME_ENV] || path.join(os.homedir(), '.opal');
}
```

- 반환값은 **`.opal` 디렉토리 자신**이다 — `state_tool.py:242`(`os.environ.get("OPAL_HOME") or os.path.expanduser("~/.opal")`)와 `doctor/lib/checks.sh:25`(`OPAL_HOME="${OPAL_HOME:-$HOME/.opal}"`)가 이미 그 의미로 쓰므로 동일 의미를 재사용한다. 새 변수도 새 의미도 만들지 않는다.
- `os.homedir()` 폴백은 POSIX에서 `HOME`을 반영하므로 `tests/test-regression.js:467`의 기존 `HOME` 격리 선례도 자동으로 유효하다 — 우선순위 2단(`OPAL_HOME` > `HOME`).
- `require('os')`를 `code-scan.js:31` 뒤에 추가한다. **파일 스타일에 맞춰 `node:` 접두를 쓰지 않는다** (`code-scan.js:29-31`이 `require('fs')` 형식).

##### (B) `loadGlobalSetting(opalHome)` — 샤드 정책 키만, 전량 비차단

```js
/**
 * ~/.opal/setting.json에서 **샤드 정책 키만** 읽는다.
 * [MUST] `TASK.md` §제약 조건: "전역 설정 파일 부재·파싱 실패·키 부재는 모두 하위 단계로 폴백한다.
 * headerSource식 전 명령 차단으로 승격하지 않는다." → 이 함수는 throw/exit 하지 않는다.
 * 다른 키(bootstrap·models)는 읽지도 쓰지도 않는다 (F-1b AC).
 * @param {string} opalHome  주입 가능 — 테스트 격리 창구 (U-7)
 * @returns {{present:boolean, shardPolicy:object|null, error:string|null}}
 */
function loadGlobalSetting(opalHome) {
  const p = path.join(opalHome, 'setting.json');
  const miss = (error) => ({ present: fs.existsSync(p), shardPolicy: null, error });

  if (!fs.existsSync(p)) return { present: false, shardPolicy: null, error: null };   // 정상 — 침묵

  let parsed;
  try { parsed = JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch {
    noticeOnce('global_setting_unreadable',
      `${p}을 읽거나 파싱할 수 없습니다 — 샤드 정책은 하위 단계(코드 상수)로 폴백합니다`);
    return miss('global_setting_unreadable');
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    noticeOnce('global_setting_unreadable',
      `${p}이 JSON 객체가 아닙니다 — 샤드 정책은 하위 단계로 폴백합니다`);
    return miss('global_setting_unreadable');
  }
  if (!hasOwn(parsed, 'shardPolicy')) return { present: true, shardPolicy: null, error: null };  // 키 부재 — 침묵

  const n = normalizeShardPolicy(parsed.shardPolicy);
  if (!n.ok) {
    noticeOnce('global_shard_policy_invalid',
      `${p}의 shardPolicy가 무효입니다(${n.detail}) — 하위 단계로 폴백합니다. ` +
      `프로젝트 단위로 덮어쓰려면 {프로젝트}/.opal/code-scan.json의 shardPolicy를 사용하세요`);
    return miss('global_shard_policy_invalid');
  }
  return { present: true, shardPolicy: n.value, error: null };
}
```

**설계 결정 4건**:

| # | 결정 | 근거 |
|---|------|------|
| 1 | **지연 로딩** — `buildCtx`(`code-scan.js:887-891`)에서 읽지 않고 `resolveShardPolicy` 첫 호출 시에만 읽는다 | 조회 8커맨드(골든 대상)가 전역 파일을 읽지 않아 새 I/O·새 stderr가 골든 경로에 끼어들지 않는다 (H-13). 정책을 소비하는 명령은 `validate`·`scaffold`·`split` 3종뿐이다 |
| 2 | **부재·키 부재는 침묵**, 파싱 실패·타입 위반만 `noticeOnce` 1회 | 부재는 정상 상태다(F-8b 시드 전 환경). 침묵과 안내의 경계를 파일 상태가 아니라 **"소유자의 의도가 있었는가"**로 가른다 — `noticeOnce`의 목적 주석 "조용한 빈 결과 / 조용한 스킵을 만들지 않기 위한 창구"(`code-scan.js:382-383`)와 정합 |
| 3 | **전량 stderr** — stdout JSON을 절대 오염시키지 않는다 | [MUST] `code-scan.js:373`: "전량 stderr — stdout JSON을 오염시키지 않는다 (brain_tool.py:793 json.loads 보호)" |
| 4 | **읽기 대상 키 한정** — `parsed.shardPolicy` 외에는 접근하지 않는다 | F-1b AC "읽기 대상은 샤드 정책 키로 한정하고 다른 키(`bootstrap`·`models`)는 건드리지 않는다". 쓰기 경로는 이 함수에 존재하지 않는다(전역 파일은 install이 쓴다 — F-010) |

#### 3.2.3 환경 변경
`require('os')` 1줄 추가. 신규 패키지 0개(Node 표준 모듈).

#### 3.2.4 배치/마이그레이션
해당 없음. 전역 파일 시드는 F-010이 담당하며, 시드가 없어도 코드 상수로 동작한다(F-1 AC).

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | F-1b AC (부재) | 기능 테스트 | `OPAL_HOME`이 `setting.json` 없는 빈 디렉토리를 가리키면 상수 폴백 + **stderr 무출력** |
| TS-011 | F-1b AC (파싱 실패) | 기능 테스트 | 깨진 JSON 전역 설정에서 exit 1이 **아니고**(비차단) 상수 폴백 + stderr 1줄 |
| TS-012 | F-1b AC (키 부재) | 기능 테스트 | `bootstrap`·`models`만 있는 전역 설정에서 상수 폴백 + stderr 무출력 |
| TS-013 | F-1b AC (타입 위반) | 기능 테스트 | 전역 `shardPolicy.maxBytes: "big"` → 비차단 + 상수 폴백 + stderr 1줄, exit code 불변 |
| TS-014 | F-1b AC (주입) | 기능 테스트 | 같은 프로젝트를 서로 다른 `OPAL_HOME` 2개로 실행하면 정책이 다르게 적용된다 |
| TS-015 | F-1b AC (다른 키 불간섭) | 기능 테스트 | 실행 전후 전역 `setting.json` 바이트가 동일하다 (code-scan은 전역 파일을 쓰지 않는다) |
| TS-016 | 제약 ⑪ | 기능 테스트 | 전역 설정 4상태(부재·깨짐·키부재·타입위반) 전부에서 `validate` exit code가 정책 없는 정상 실행과 동일하다 |

---

### F-003: 2축 판정

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `manifestEntryCount`·`isOversizeManifest`·`recommendedShardCount` 신설 / `checkOversize` 시그니처에 `manifest` 추가 + 2축 판정(`:2146-2152`) / 호출 2곳 인자 추가(`:2204`·`:2225`) / `cmdScaffold` 상한 소비 교체(`:1852`·`:1913-1919`) | `code-scan.js:2146-2152`·`:2204`·`:2225`·`:1852` |

#### 3.3.2 설계

##### (A) 판정식 3함수 — 판정 로직을 소비 지점에 복제하지 않는다

```js
// 해당 매니페스트 **자신의** 엔트리 수. 합집합이 아니다 — 판정 대상은 "이 파일이 쪼갤 만한가"이므로
// 베이스는 베이스의 files만, 샤드는 샤드의 files만 센다 (S-25가 샤드 자신을 측정하는 계약과 정합).
function manifestEntryCount(manifest) {
  return manifest && manifest.files ? Object.keys(manifest.files).length : 0;
}

// 2축 판정 — 바이트 초과 **AND** 엔트리 수 이상 (확정 방향 #2). 경계: size===maxBytes는 초과 아님
// (082 S-16 (d) off-by-one 계약 보존), entries===minFiles는 **대상**(하한은 "이상").
function isOversizeManifest(bytes, entryCount, policy) {
  return bytes > policy.maxBytes && entryCount >= policy.minFiles;
}

// 권고 조각 수 — 트리거가 아니라 targetBytes로 나눈다 (확정 방향 #9). 최소 2조각.
function recommendedShardCount(bytes, policy) {
  return Math.max(2, Math.ceil(bytes / policy.targetBytes));
}
```

- **경계 규칙 명시**: 바이트는 `>`(초과), 엔트리는 `>=`(이상). TASK 확정 방향 #2 원문("바이트 초과 **AND** 파일 수 이상")을 그대로 코드로 옮긴 것이며, 082가 세운 `size === limit`은 초과가 아니라는 off-by-one 계약(`tests/test-shard.js:467-477`)을 보존한다.
- 실측 검증(TASK §배경 분석 (3)): 10KB 초과 11개 중 40파일 이상 9개만 대상, 26·29파일짜리 2개는 제외 → `entries >= 40` 판정과 일치.

##### (B) `checkOversize` 교체 (`code-scan.js:2145-2152`)

```js
// 크기 상한 열거 — 비차단 (082 F-005 유지). 2축 판정 + 유도 페이로드 (083 F-2·F-5).
// 베이스·샤드 양쪽에서 호출된다 (082 S-25).
function checkOversize(manifestAbs, manifestRel, manifest) {
  const size = fs.statSync(manifestAbs).size;
  const policy = resolveShardPolicy(ctx);
  const entries = manifestEntryCount(manifest);
  if (!isOversizeManifest(size, entries, policy)) return;
  violations.push({
    code: 'manifest_oversize',
    manifest: manifestRel,
    detail: `${size}/${policy.maxBytes}`,          // [MUST] 포맷 불변 — 082 S-15가 정확 단언 (H-8)
    entries,
    minFiles: policy.minFiles,
    recommendedShards: recommendedShardCount(size, policy),   // F-5 (F-006)
    next: `code-scan split ${manifestRel} --plan`,             // F-5 (F-006)
  });
}
```

- 호출 지점 2곳에 인자만 추가한다 — `:2204` → `checkOversize(manifestAbs, manifestRel, manifest)`, `:2225` → `checkOversize(s.manifestAbs, s.manifestRel, s.manifest)`. **두 지점 모두 매니페스트 객체가 이미 스코프에 있으므로 신규 파일 읽기가 0건이다.**
- `counts.manifest_oversize`(`code-scan.js:2285`)·비차단 필터(`:2290-2292`)는 `code` 값만 보므로 **무수정**. 비차단 계약(확정 방향 #8) 유지.

##### (C) `cmdScaffold` 소비 교체

```js
// :1852  const limit = manifestMaxBytes(ctx);  →
const policy = resolveShardPolicy(ctx);

// :1913-1919 크기 상한 알림 — stdout JSON은 건드리지 않는다 (082 S-17 계약 보존)
const bytes = Buffer.byteLength(serialized);
const entries = manifestEntryCount(manifest);
if (isOversizeManifest(bytes, entries, policy)) {
  process.stderr.write(
    `code-scan: [oversize] ${manifestRel} — ${bytes} bytes > ${policy.maxBytes} 상한, ` +
    `엔트리 ${entries}개(하한 ${policy.minFiles}). 권고 ${recommendedShardCount(bytes, policy)}조각 — ` +
    `code-scan split ${manifestRel} --plan\n`);
}
```

- `mergeManifest` 결과 `manifest`가 같은 스코프에 있다(`code-scan.js:1896`) — 엔트리 수 계산에 추가 I/O가 없다.
- S-17 계약(`tests/test-shard.js:507-521`)은 "stdout 바이트 동일 + stderr 비어있지 않음"만 단언하고 문구를 단언하지 않으므로 문구 확장이 안전하다.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음. 단, **기본값 인하(20480→10240)와 하한 도입(40)이 함께 들어가므로 기존 픽스처의 초과 판정이 사라진다** — F-008에서 픽스처 정책 오버라이드로 흡수한다(H-1·H-2, 제약 ⑤).

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | F-2 AC | 기능 테스트 | 바이트 초과 + 엔트리 수 **미달** 매니페스트는 `manifest_oversize`에 **열거되지 않는다** (`counts.manifest_oversize === 0`) |
| TS-021 | F-2 AC | 기능 테스트 | 바이트 초과 + 엔트리 수 충족이면 1건 열거되고 exit 0(비차단) |
| TS-022 | F-2 AC | 기능 테스트 | 바이트 미달 + 엔트리 수 충족이면 0건 (AND 조건) |
| TS-023 | F-2 AC (경계) | 기능 테스트 | `entries === minFiles`는 **대상**(하한은 이상), `entries === minFiles - 1`은 비대상 |
| TS-024 | F-2 AC (경계) | 기능 테스트 | `size === maxBytes`는 비대상, `size === maxBytes + 1`은 대상 (082 off-by-one 계약 보존) |
| TS-025 | F-2 AC (샤드) | 기능 테스트 | 베이스는 상한 이하·샤드만 2축 충족 → 1건이고 `manifest` 필드가 **샤드 경로** (082 S-25 계승) |
| TS-026 | F-2 AC (scaffold) | 기능 테스트 | 2축 미충족이면 scaffold stderr가 비어 있고, 충족이면 1줄 + stdout 바이트 동일 |

---

### F-004: 분할 제안 `split --plan`

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `parseArgs`에 `--groups`·`--plan` 추가 + `opts.discoverOut` → `opts.out` 개명(`:164`·`:178`·`:1634`) / `USAGE`에 `split` 절(`:72-129`) / `commands`에 `split: cmdSplit`(`:2382-2396`) / `splitTokens`·`entryBytes`·`planShardGroups` 신설 / `cmdSplit` 신설 (plan 모드) | `code-scan.js:150-194`·`:2382-2396` |

#### 3.4.2 설계

##### (A) CLI 계약

```
code-scan split <manifest-path> --plan [--out <path>] [--trace] [--stop-after <S1..S5>] [--json]
code-scan split <manifest-path> --groups <path|-> [--dry-run] [--json]
```

| 항목 | 결정 | 근거 |
|------|------|------|
| 위치 인자 | `<manifest-path>` = 프로젝트 루트 기준 상대 경로(절대 경로도 허용). `opts.commandArg`를 그대로 쓴다 | `code-scan.js:187`이 이미 위치 인자 1개를 받는다. `target <file>`(`:1467`)과 같은 관용 |
| `--plan` | 신규 boolean `opts.plan` | 제안 전용 모드 스위치 |
| `--groups` | 신규 `opts.groups` (문자열, `-`면 stdin) | U-1 채택안. `--changed <csv|->`(`:180`)의 stdin 관용 재사용 |
| `--out` | **재사용**. `opts.discoverOut` → `opts.out`으로 개명하고 `cmdDiscover:1634` 1줄을 따라 바꾼다 | 플래그를 새로 만들지 않는다. 개명은 참조 3곳(`:164`·`:178`·`:1634`)뿐이며 이름이 discover 전용으로 오해되는 것을 막는다 |
| `--dry-run` | **재사용** (`opts.dryRun`, `:179`) | discover·scaffold와 공용 관용 |
| `--trace` | 신규 boolean `opts.trace` | 검토 장치 1 (U-2 (5)). `--plan` 전용 — `--groups`와 함께 주면 무시(집행에는 단계가 없다) |
| `--stop-after` | 신규 `opts.stopAfter` (문자열, 대소문자 무시) | 검토 장치 2. 값이 사다리 id(`S1`~`S5`) 밖이면 exit 1 `split_usage_invalid` + 허용값 목록을 `fix`에 싣는다 |
| 모드 게이트 | `ctx.headerSource !== 'manifest'` → exit 1 `split_inline_mode` | inline 모드에는 매니페스트가 없어 대상이 존재하지 않는다. "성공적으로 아무것도 안 함"은 거짓 신호다(H-14). `scaffold`가 inline에서 no-op인 것과 다른 이유: scaffold는 스코프 전체를 대상으로 하는 정기 작업이고, `split`은 **소유자가 특정 파일을 지목한 명령**이므로 대상 부재가 곧 오류다 |
| 모드 배타 | `--plan`과 `--groups` 동시 지정 → exit 1 `split_usage_invalid`. 둘 다 없으면 동일 | 모호한 기본 동작을 만들지 않는다 |

##### (B) groups 문서 스키마 — **`--plan` 출력 = `--groups` 입력** (U-1)

```json
{
  "ok": true,
  "command": "split",
  "mode": "plan",
  "manifest": ".opal/code-map/svc/mod.json",
  "policy": { "maxBytes": 10240, "minFiles": 40, "targetBytes": 7680 },
  "current": { "bytes": 86400, "entries": 292 },
  "recommendedShards": 12,
  "dict": {
    "found": true,
    "path": "200.설계/210.사전/표준단어사전.md",
    "source": "project-var",
    "rows": 214,
    "searched": ["shardPolicy.dictPath(미설정)", "200.설계/사전/표준단어사전.md", "200.설계/210.사전/표준단어사전.md"]
  },
  "ladder": [
    { "id": "S1", "signal": "first-token", "dict": true,  "accept": 2, "skipped": false },
    { "id": "S4", "signal": "last-token",  "dict": false, "accept": 3, "skipped": false }
  ],
  "groups": [
    { "label": "order", "stage": "S1", "files": ["OrderRepository.ts", "OrderService.ts"], "estimatedBytes": 5120, "oversizeGroup": false }
  ],
  "unassigned": ["Misc.ts"],
  "assignments": { "OrderRepository.ts": "S1", "OrderService.ts": "S1" },
  "coverage": { "assigned": 240, "unassigned": 48, "total": 288, "byStage": { "S1": 160, "S2": 28, "S3": 22, "S4": 18, "S5": 12 } },
  "trace": [
    { "stage": "S1", "dict": true, "input": 288, "assigned": 160, "groups": 22, "remaining": 128, "skipped": false, "reason": null }
  ]
}
```

| 필드 | `--plan` 출력 | `--groups` 입력 시 |
|------|--------------|------------------|
| `manifest` | 대상 경로 | **일치 검증** — CLI 인자와 다르면 exit 1 `split_groups_invalid` (다른 매니페스트에 잘못 적용하는 오작동 방지) |
| `groups[].label` | 제안 라벨 (사전 매칭 시 사전 영문명 정규형) | **집행 사용** — `SHARD_LABEL_RE` 통과 필수 |
| `groups[].files` | 제안 파일 목록 | **집행 사용** |
| `groups[].stage` | 그 그룹을 만든 단계 id | **선택 허용 + 무시** (검토 장치 3, U-2 (5)) |
| `assignments` | 엔트리 → 단계 id 맵 | **선택 허용 + 무시** |
| `trace` · `ladder` · `dict` | 검토 정보 (`--trace` 시에만 `trace` 포함) | **선택 허용 + 무시** |
| `policy`·`current`·`recommendedShards`·`estimatedBytes`·`oversizeGroup`·`coverage`·`ok`·`command`·`mode` | 정보 | **무시** (호환을 위해 존재를 허용하되 읽지 않는다) |
| `unassigned` | 미분류 목록 | **무시** — 베이스에 남는 것이 기본 동작이므로 입력에서 의미가 없다 |

- 왜 `unassigned`를 입력에서 무시하는가: `split`의 동작 정의가 "지정된 것만 옮기고 나머지는 베이스에 남긴다"(F-3 AC)이므로 미지정이 곧 잔존이다. 입력에서 해석하면 같은 사실의 표현이 2개가 되어 불일치 가능성이 생긴다.
- **왕복 불변식(H-18)**: `parseGroupsDoc`(§3.5.2 (B))은 **`groups[].label`·`groups[].files` 2필드만 읽는다.** 그 외 최상위·그룹 내 키는 전부 존재를 허용하고 무시한다 → `--trace`·`--stop-after`를 켠 출력도, 끈 출력도, 사람이 손으로 편집한 문서도 동일하게 집행된다. 검토 장치가 늘어도 왕복 계약은 확장되지 않는다.
- **`stage`가 그룹 단위로도 성립하는 근거**: 사다리는 직전 단계의 `unassigned`만 입력받으므로(U-2 (1)) 한 그룹의 모든 엔트리는 **정확히 한 단계**에서 배정된다. `assignments` 맵은 그 사실의 엔트리 단위 뷰이며, 사람이 그룹을 손으로 재편집하면 `assignments`가 낡을 수 있으나 **입력에서 무시되므로 무해**하다.

##### (C) 제안 알고리즘 (U-2 5규칙의 구현)

```js
// 엔트리 1건이 매니페스트에서 차지하는 대략 바이트 (직렬화 후 키 + 값 + 구두점)
function entryBytes(key, entry) {
  return Buffer.byteLength(JSON.stringify({ [key]: entry }, null, 2)) + 2;
}

// 파일명 → 소문자 토큰 배열. 확장자 제거 → camel/Pascal 경계 + `_`·`-`·`.` 분해 → 소문자.
// 'PricingCalculator.ts' → ['pricing','calculator'] / 'order_repo.py' → ['order','repo']
function splitTokens(key) {
  return key.replace(/\.[^.]+$/, '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_\-.]+/g, ' ')
    .split(/\s+/)
    .map(t => t.toLowerCase().replace(/[^a-z0-9]/g, ''))
    .filter(Boolean);
}

// ── 사다리 정의 (U-2 (3)) — 내장 고정. 설정 노출은 후속 이관 ──────────────
const SHARD_PLAN_LADDER = Object.freeze([
  { id: 'S1', signal: 'first-token', dict: true,  accept: 2 },
  { id: 'S2', signal: 'first-two',   dict: true,  accept: 2 },
  { id: 'S3', signal: 'any-token',   dict: true,  accept: 2 },
  { id: 'S4', signal: 'last-token',  dict: false, accept: 3 },
  { id: 'S5', signal: 'depends',     dict: false, accept: 3 },
]);

/**
 * 그룹 후보를 산출한다 — **파일을 쓰지 않는다**. 결정론적이다(H-10).
 * @param {Map<string,object>} baseEntries  베이스에 남아 있는 엔트리만 (샤드 보유분 제외)
 * @param {Set<string>} usedLabels          기존 샤드 라벨 (충돌 회피)
 * @param {{maxBytes,minFiles,targetBytes}} policy
 * @param {{rows:Array<{ko,en,abbr,index}>}|null} dict  null이면 dict:true 단계 자동 skip (U-2 (4))
 * @param {{stopAfter:string|null, shardOverheadBytes:number}} opts
 * @returns {{groups, unassigned, coverage, assignments, trace, ladder}}
 */
function planShardGroups(baseEntries, usedLabels, policy, dict, opts) { /* 아래 사다리 루프 */ }

/**
 * 한 단계의 그룹핑 키를 돌려준다. null이면 이 단계에서 배정하지 않는다.
 * @returns {string|null} 그룹핑 키 (= 라벨 후보)
 */
function stageKeyFor(stage, key, entry, dict, freq) { /* signal별 5분기 */ }

/**
 * 토큰 스팬 ↔ 사전 매칭. 대소문자 무시, 영문·약어 두 컬럼 후보.
 * 다중 매칭 시 ① 스팬 토큰 수 내림차순 → ② 사전 등재 순서(row.index) 오름차순 (U-2 (3)).
 * @returns {{canonical:string, from:number, to:number, index:number}|null}
 */
function dictMatchSpan(tokens, dict, fromIdx, maxSpanTokens) { /* longest-match */ }
```

**사다리 루프 절차**:

1. **초기화**: `remaining = 입력 엔트리 전체`, `groups = []`, `assignments = {}`, `trace = []`.
2. **단계 순회** — `SHARD_PLAN_LADDER`를 순서대로 돈다. 각 단계에서:
   - **(a) skip 판정**: `stage.dict === true && dict === null` → `skipped: true`, `reason: 'dict_absent'`로 `trace`에 기록하고 **입력을 그대로 다음 단계로 흘린다**. `--stop-after`로 이미 중단됐으면 `reason: 'stopped'`.
   - **(b) 버킷 구성**: `remaining`의 각 키에 `stageKeyFor(...)`를 적용해 버킷을 만든다. `null`이면 그 엔트리는 이 단계에서 손대지 않는다.
   - **(c) 채택**: 버킷 크기 `>= stage.accept`인 버킷만 그룹으로 채택한다. 미달 버킷의 엔트리는 `remaining`에 그대로 남아 **다음 단계로 흘러간다** — 초안처럼 즉시 `unassigned`로 확정하지 않는 것이 사다리의 핵심 차이다.
   - **(d) 라벨 확정**: 사전 매칭 단계는 사전 `영문` 컬럼의 정규형(소문자 + `[^a-z0-9]` → `-`), 비사전 단계는 토큰 소문자. `usedLabels`와 충돌하면 `-2`, `-3`… 접미. 확정 라벨을 `usedLabels`에 추가한다.
   - **(e) 배정 기록**: 채택된 엔트리를 `remaining`에서 제거하고 `assignments[key] = stage.id`, 그룹에 `stage: stage.id`를 싣는다.
   - **(f) trace 기록**: `{stage, dict, input, assigned, groups, remaining, skipped, reason}`.
   - **(g) 중단**: `opts.stopAfter === stage.id`면 이후 단계를 전부 `skipped: true, reason: 'stopped'`로 기록하고 루프를 끝낸다.
3. **잔여 확정**: 루프 종료 시 `remaining`이 `unassigned`다. **임의 배분·"기타" 그룹 생성 금지** (brain 승계 #3).
4. **크기 목표 점검**: 각 그룹 `estimatedBytes = shardOverheadBytes + Σ entryBytes`. `> targetBytes`면 `oversizeGroup: true`로 **표시만** 한다 — 초안의 "2차 토큰 재분할 1회"는 삭제했다(U-2 (6) 규칙 2: S2·S3이 이미 담당).
5. **결정론 정렬**: 최종 그룹은 **단계 순서 우선** → 단계 내 `(엔트리 수 내림차순, 라벨 사전순)`. `files`·`unassigned`는 사전순.
6. **출력**: `coverage = {assigned, unassigned, total, byStage}`.

**`signal`별 `stageKeyFor` 5분기**:

| signal | 구현 | 라벨 원천 |
|--------|------|----------|
| `first-token` (S1) | `dictMatchSpan(tokens, dict, 0, 1)` — 첫 토큰 1개 스팬만 | 매칭 사전 행의 `영문` |
| `first-two` (S2) | `dictMatchSpan(tokens, dict, 0, 2)` — 첫 2토큰까지 스팬. 2토큰 매칭이면 `{c0}-{c1}` 형태가 아니라 **사전 행 1개의 정규형**이 되고, 두 토큰이 각각 다른 행에 매칭되면 `{c0}-{c1}` 결합 | 사전 |
| `any-token` (S3) | 위치 0..n에서 `dictMatchSpan`을 시도해 **가장 긴 매칭** 1건 채택 | 사전 |
| `last-token` (S4) | `tokens[tokens.length - 1]` (사전 미사용). 토큰이 1개뿐이면 `null` — S1과 같은 신호를 두 번 세지 않는다 | 토큰 소문자 |
| `depends` (S5) | `entry.depends` 배열을 정규화하고, **잔여 집합 전체에서 항목별 빈도**(`freq`)를 센 뒤 각 엔트리를 **자신의 depends 중 빈도 최대(동률이면 사전순)** 항목에 배정 | 항목 소문자 정규형 |

- S5의 `freq`는 **그 단계 진입 시점의 `remaining`** 기준으로 1회 계산한다 — 배정이 진행되며 빈도가 변하면 순서 의존이 생겨 결정론이 깨진다.
- `entry.depends`는 워커 기입 필드로 이미 정의돼 있다(`code-scan.js:62` `WORKER_FIELDS`) — 신규 데이터 수집이 없다. 값이 없거나 배열이 아니면 `null`(이 단계 미배정).

- `shardOverheadBytes`: 샤드 매니페스트의 `{version, scope, dir, files:{}}` 골격 바이트. 실제 값으로 계산한다 — `Buffer.byteLength(JSON.stringify({version, scope, dir, files:{}}, null, 2) + '\n')`. 추정이 아니라 대상 베이스의 실제 필드값으로 산출하므로 `estimatedBytes`가 집행 후 실제 크기와 근사한다.
- **쓰기 경계**: `--plan`은 매니페스트를 쓰지 않는다. `--out <path>`가 주어지면 groups 문서 1개만 쓴다(`JSON.stringify(doc, null, 2) + '\n'`). `--out`이 없으면 stdout(`--json`)/사람용 요약.

##### (D) 사람용 출력 (`--json` 없을 때) + `--trace`

```
split --plan: .opal/code-map/svc/mod.json (86400 bytes, 292 entries)
  policy: maxBytes=10240 minFiles=40 targetBytes=7680 → 권고 12조각
  dict:   200.설계/210.사전/표준단어사전.md (214행, PROJECT.md {설계} 변수)
  groups (26):
    order        [S1]  46 entries   ~7104 bytes
    settlement   [S1]  40 entries   ~6180 bytes
    repository   [S4]  12 entries   ~2100 bytes
    ...
  unassigned: 48 entries — 라벨을 직접 지정하거나 베이스에 남깁니다
  다음: code-scan split .opal/code-map/svc/mod.json --plan --out /tmp/groups.json
        (파일을 편집한 뒤) code-scan split .opal/code-map/svc/mod.json --groups /tmp/groups.json --dry-run
```

`--trace` 추가 출력:

```
  trace:
    stage  dict  입력   걷음   그룹   잔여   비고
    S1     yes    288    160     22    128
    S2     yes    128     28      9    100
    S3     yes    100     22      8     78
    S4     no      78     18      4     60
    S5     no      60     12      3     48
```

사전 미발견 시 (`dict.found === false`):

```
  dict:   사전 미발견 — S1~S3 건너뜀
          탐색: shardPolicy.dictPath(미설정) → 200.설계/사전/표준단어사전.md → 200.설계/210.사전/표준단어사전.md
  trace:
    stage  dict  입력   걷음   그룹   잔여   비고
    S1     yes      -      -      -      -   skipped (사전 미발견)
    S2     yes      -      -      -      -   skipped (사전 미발견)
    S3     yes      -      -      -      -   skipped (사전 미발견)
    S4     no     288     46      9    242
    S5     no     242     30      7    212
```

- 사람용 출력에 **다음 2단 명령을 그대로 싣는다** — U-3 채택안(전용 스킬 대신 명령 문자열 유도)의 실행 지점.
- **사전 미발견을 침묵하지 않는다** — 부재 자체는 stderr 안내를 내지 않지만(정상 상태), `--plan` 출력에는 `dict.found === false`와 탐색 경로가 항상 실린다. H-16(조용한 저품질)의 해소 지점이다.

#### 3.4.3 환경 변경
해당 없음.

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | F-4 AC | 기능 테스트 | `--plan --json`이 그룹 후보와 각 조각의 `estimatedBytes`·파일 수를 출력한다 |
| TS-031 | F-4 AC (무쓰기) | 기능 테스트 | `--plan` 실행 전후 `.opal/code-map/` 트리 전체가 **바이트 동일**하다 |
| TS-032 | F-4 AC (미분류 명시) | 기능 테스트 | 1건뿐인 토큰 엔트리가 `unassigned`에 나타나고 어떤 그룹에도 배분되지 않는다 |
| TS-033 | H-10 | 기능 테스트 | `--plan --json` 2회 실행 stdout이 **바이트 동일**하다 (결정론) |
| TS-034 | F-4 AC (`--out`) | 기능 테스트 | `--out`을 주면 groups 문서 1개만 생성되고 매니페스트는 무변화다 |
| TS-035 | U-2 (3) 잔여 규칙 | 기능 테스트 | 그룹 라벨에 `misc`·`other`·`etc` 같은 도구 생성 "기타" 그룹이 없다 |
| TS-036 | U-2 (6) 규칙 2 | 기능 테스트 | 목표 초과 그룹이 `oversizeGroup: true`로 **표시만** 되고 도구가 강제 재분할하지 않는다 |
| TS-037 | 라벨 안전 | 기능 테스트 | 생성된 모든 라벨이 `SHARD_LABEL_RE`를 통과하고 기존 샤드 라벨과 충돌하지 않는다 |
| TS-038 | H-14 | 기능 테스트 | inline 모드에서 `split --plan` → exit 1 + `split_inline_mode` |
| TS-039 | CLI 계약 | 기능 테스트 | `--plan`과 `--groups` 동시 지정 → exit 1 `split_usage_invalid`. `--out` 재사용 후 `discover --out`이 회귀 없이 동작한다 |
| TS-100 | U-2 (1) 사다리 | 기능 테스트 | 각 단계가 **직전 단계의 `unassigned`만** 입력으로 받는다 — `trace[n].input === trace[n-1].remaining` |
| TS-101 | U-2 (1) 앞 단계 불변 | 기능 테스트 | 앞 단계에서 배정된 엔트리가 후속 단계에서 **재배정되지 않는다** (`assignments` 값이 단계 진행 중 변하지 않음) |
| TS-102 | U-2 (3) S1 | 기능 테스트 | 사전에 등재된 첫 토큰 2건 이상이 S1 그룹으로 묶이고 라벨이 **사전 영문명 정규형**이다 |
| TS-103 | U-2 (3) S2 | 기능 테스트 | 첫 토큰만으로 안 걸린 엔트리가 1~2번째 토큰 결합으로 S2에서 걸린다 |
| TS-104 | U-2 (3) S3 | 기능 테스트 | 첫 토큰이 사전에 없고 **중간 토큰**이 사전에 있는 엔트리가 S3에서 걸린다 (`TaxOrderTable` → `order`) |
| TS-105 | U-2 (3) S4 | 기능 테스트 | 사전 무관하게 마지막 토큰이 같은 엔트리 3건 이상이 S4 그룹이 된다 (`*Repository` → `repository`) |
| TS-106 | U-2 (3) S5 | 기능 테스트 | `depends`를 공유하는 엔트리 3건 이상이 S5 그룹이 되고, `depends` 부재 엔트리는 영향받지 않는다 |
| TS-107 | U-2 (3) accept | 기능 테스트 | S1~S3은 2건 미만, S4~S5는 3건 미만 버킷이 채택되지 않고 **다음 단계로 흘러간다**(즉시 `unassigned` 확정 아님) |
| TS-108 | U-2 (3) 다중 매칭 | 기능 테스트 | 한 파일명이 여러 사전 항목에 매칭될 때 **스팬 길이 큰 것 우선 → 동률이면 등재 순서**로 결정론적이다 |
| TS-109 | U-2 (5) `--trace` | 기능 테스트 | `--trace`가 단계별 `입력 → 걷음 → 잔여` 표를 출력하고 합계가 정합한다 (`assigned + unassigned === total`) |
| TS-110 | U-2 (5) `--stop-after` | 기능 테스트 | `--stop-after S2`가 S3~S5를 실행하지 않고 잔여를 전부 `unassigned`로 낸다. 이후 단계 `trace`에 `reason: 'stopped'` |
| TS-111 | U-2 (5) `--stop-after` 검증 | 기능 테스트 | 사다리 id 밖 값(`--stop-after S9`)은 exit 1 `split_usage_invalid` + 허용값 목록이 `fix`에 실린다 |
| TS-112 | U-2 (5) `stage` 필드 | 기능 테스트 | 모든 배정 엔트리에 `stage`가 실리고, `groups[].stage`와 `assignments[key]`가 일치한다 |
| TS-113 | H-18 왕복 | 통합 테스트 | `--trace --stop-after S2 --json` 출력을 그대로 `--groups -`에 파이프해도 성공한다 (선택 필드 무시) |
| TS-114 | U-2 (4) skip | 기능 테스트 | 사전 미발견 시 S1~S3이 `skipped: true, reason: 'dict_absent'`로 기록되고 S4·S5만 실행된다 |
| TS-115 | H-16 | 기능 테스트 | 사전 미발견 시 `--plan` 출력에 `dict.found === false` + `dict.searched` 경로 목록, `--trace`에 "사전 미발견 — S1~S3 건너뜀" 문구 |
| TS-116 | H-10 (사다리) | 기능 테스트 | 사전 유/무 각각에서 `--plan --json` 2회 실행 stdout이 바이트 동일하다 |

---

### F-005: 분할 집행 `split --groups`

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `resolveSplitTarget`·`parseGroupsDoc`·`composeSplitPlan`·`commitSplit` 신설 / `cmdSplit`에 groups 모드 추가 (F-004와 같은 함수) | `code-scan.js:1742-1770`·`:1002-1074`·`:1897`·`:1902-1905` |

#### 3.5.2 설계

##### (A) `resolveSplitTarget(manifestArg, ctx)` — 대상 검증

```js
/**
 * @returns {{abs, rel, manifest}} 검증 통과한 **베이스** 매니페스트
 * @throws {CodeMapFatalError} 'split_target_invalid'
 */
```

| # | 검증 | 실패 코드 |
|---|------|----------|
| 1 | 경로가 `{projectRoot}/.opal/code-map/` 하위인가 (`CODE_MAP_DIR` 기준, 상대·절대 모두 정규화 후 판정) | `split_target_invalid` |
| 2 | 파일이 존재하고 JSON 파싱되는가 (`loadManifest` 재사용 — 파싱 실패는 기존 `manifest_parse_failed`) | `split_target_invalid` / `manifest_parse_failed` |
| 3 | **샤드가 아닌가** — `isShardManifestPath(abs)`(`code-scan.js:984-986`)가 true면 거부 | `split_target_invalid` |
| 4 | `manifest.version === CODE_MAP_VERSION`인가 | `unsupported_version` (기존 코드 재사용) |

- 왜 샤드를 대상으로 허용하지 않는가: 샤드의 샤드는 존재하지 않는다(082 `shard_undeclared`가 중첩 `_shards`를 위반으로 잡는다, `code-scan.js:2264`). 대상은 항상 베이스이며 재분할도 베이스에서 시작한다.

##### (B) `parseGroupsDoc(raw, targetRel, base, existingLabels)` — 입력 검증 1곳 (U-1)

```js
/**
 * groups 문서를 검증·정규화한다 — 스키마 검증은 이 함수 1곳에만 존재한다.
 * @returns {{ok:true, groups:Array<{label,files:string[]}>} | {ok:false, detail:string}}
 */
```

| # | 검증 | detail 예 |
|---|------|----------|
| 1 | JSON 객체이고 `groups`가 비지 않은 배열인가 | `groups must be a non-empty array` |
| 2 | `manifest` 키가 있으면 `targetRel`과 일치하는가 | `manifest mismatch: doc=… arg=…` |
| 3 | 각 그룹이 `{label: string, files: string[]}`인가, `files`가 비지 않았는가 | `groups[2].files must be a non-empty array` |
| 4 | `label`이 `SHARD_LABEL_RE`(`code-scan.js:69`)를 통과하는가 | `invalid shard label "…"` |
| 5 | 문서 내 `label` 중복이 없는가 | `duplicate label "…"` |
| 6 | 모든 파일 키가 **베이스 `files`에 실재**하는가 | `unknown entry key(s): …` |
| 7 | 한 파일이 2개 이상 그룹에 지정되지 않았는가 | `entry assigned to multiple groups: …` |

- 위반은 전부 exit 1 `split_groups_invalid` + `detail`. **쓰기 0건.**
- 기존 샤드 라벨과 같은 라벨은 **허용**한다 — 그 샤드에 엔트리를 **추가**하는 정당한 조작이다(재분할·증분 이동). 문서 내 중복만 거부한다.
- `-`(stdin) 입력은 `fs.readFileSync(0, 'utf8')`로 읽는다 — `--changed -`가 stdin을 읽는 기존 관용과 같은 계층.

##### (C) `composeSplitPlan(base, baseRel, groups, ctx)` — 메모리 조립 + 사전 불변식 (U-4 ①)

```js
/**
 * 쓰기 전에 최종 상태 전부를 메모리에서 만들고 불변식을 검증한다.
 * [MUST] `TASK.md` §제약 조건: "엔트리 유실 0건 — 실행 전후 엔트리 총합이 반드시 같아야 하며,
 * 실패 시 부분 상태를 남기지 않는다."
 * @returns {{ok:true, writes:Array<{abs, rel, content, isNew}>, summary:object} | {ok:false, detail}}
 */
```

**조립 규칙**:

1. **샤드 매니페스트**: 기존 샤드가 있으면 그 객체를, 없으면 `{version: CODE_MAP_VERSION, scope: base.scope, dir: base.dir, files: {}}`를 기반으로 지정 엔트리를 추가한다. 기존 `package`는 **보존**한다(3단 상속의 입력, `code-scan.js:1066`).
2. **베이스**: `files`에서 이동 엔트리를 제거하고, `shards`에 신규 라벨을 **선언 순서 말미에 추가**한다(기존 라벨 순서 불변 — `resolveShards`의 "선언 순서 우선 + 첫 승리" 계약이 흔들리지 않게, `code-scan.js:1035`).
3. **키 순서 고정 (F-3 AC "scaffold no-op"의 필수 조건)**: 모든 매니페스트를 `mergeManifest`(`code-scan.js:1764-1767`)와 **동일한 키 순서**로 만든다 — `version` → `scope` → `dir` → (`shards`) → (`package`) → `files`. `files`는 `orderFilesObject(files)`를 통과시킨다. 직렬화도 동일하게 `JSON.stringify(m, null, 2) + '\n'`(`:1897`).
4. **불변식 검증**: `Σ(각 샤드 엔트리 수) + 베이스 잔존 엔트리 수 === 실행 전 베이스+샤드 총 엔트리 수` && 전체 키 집합에 중복 0. 실패 시 `{ok:false}` → exit 1, **쓰기 0건**.

> 왜 키 순서가 AC 조건인가: `scaffold`는 `prevContent !== serialized`로 변경 여부를 판정한다(`code-scan.js:1900`). 키 순서가 다르면 내용이 같아도 `updated`로 잡혀 F-3 AC("`scaffold`가 no-op")가 깨진다.

##### (D) `commitSplit(writes)` — 2-phase commit + 롤백 (U-4 ②③)

```js
/**
 * @param {Array<{abs, rel, content, isNew}>} writes
 * @throws {CodeMapFatalError} 'split_write_failed' | 'split_rollback'
 */
function commitSplit(writes) {
  const TMP = '.tmp-split';   // [MUST] '.json'으로 끝나지 않아야 한다 — listManifestFiles(:1780) 오인 방지
  const tmps = [];
  // Phase 1 — tmp 전량 작성. 여기서 실패하면 원본은 한 바이트도 변하지 않는다.
  try {
    for (const w of writes) {
      fs.mkdirSync(path.dirname(w.abs), { recursive: true });
      const tmp = w.abs + TMP;
      fs.writeFileSync(tmp, w.content);
      tmps.push(tmp);
    }
  } catch (e) {
    for (const t of tmps) { try { fs.unlinkSync(t); } catch { /* best effort */ } }
    throw new CodeMapFatalError('split_write_failed', String(e && e.message));
  }
  // Phase 2 — 백업 확보 후 rename 커밋 (동일 디렉토리 rename은 POSIX 원자적)
  const backups = writes.map(w => ({ abs: w.abs, prev: w.isNew ? null : fs.readFileSync(w.abs, 'utf8') }));
  const done = [];
  try {
    for (const w of writes) { fs.renameSync(w.abs + TMP, w.abs); done.push(w.abs); }
  } catch (e) {
    for (const b of backups) {
      if (!done.includes(b.abs)) continue;
      try { if (b.prev === null) fs.unlinkSync(b.abs); else fs.writeFileSync(b.abs, b.prev); } catch { /* best effort */ }
    }
    for (const t of tmps) { try { if (fs.existsSync(t)) fs.unlinkSync(t); } catch { /* best effort */ } }
    throw new CodeMapFatalError('split_rollback', String(e && e.message));
  }
  return backups;   // 사후 검증 실패 시 복원용 (U-4 ④)
}
```

##### (E) 사후 재검증 (U-4 ④)

```js
// 캐시를 비우고 **같은 resolveShards로** 다시 읽는다 — 해석 로직을 복제하지 않는다(제약 ③).
ctx.codeMap.manifests.clear();
ctx.codeMap.shardViews.clear();
const after = loadManifest(targetAbs, ctx);
const view = resolveShards(targetAbs, targetRel, after, ctx);
const afterTotal = view ? view.byKey.size : manifestEntryCount(after);
if (afterTotal !== beforeTotal || (view && view.duplicates.length > 0)) {
  restoreBackups(backups);          // commitSplit이 돌려준 백업으로 원복
  return errorExit('split_verify_failed', { detail: `entries ${beforeTotal} → ${afterTotal}` });
}
```

- `view.byKey.size`가 합집합 엔트리 수이므로 **엔트리 유실 0건이 실제 파일 기준으로 재확인**된다(제약 ⑥의 2차 방어).
- `duplicates.length > 0`이면 같은 키가 베이스와 샤드에 동시 존재하는 상태 = 이동 누락이므로 롤백한다.

##### (F) 출력 계약

```json
{
  "ok": true, "command": "split", "mode": "apply", "dryRun": false,
  "manifest": ".opal/code-map/svc/mod.json",
  "moved": 198,
  "base": { "entries": 94, "bytes": 30120 },
  "shards": [ { "label": "pricing", "manifest": ".opal/code-map/svc/mod/_shards/pricing.json", "entries": 46, "bytes": 7104, "created": true } ],
  "before": { "entries": 292, "bytes": 86400 },
  "after": { "totalEntries": 292 }
}
```

- `before.entries === after.totalEntries`가 출력에 **명시적으로 실린다** — 소비자(사람·PM)가 유실 0건을 눈으로 확인할 수 있다.
- 실행 후 stderr에 후속 검증 안내 1줄: `code-scan: split 완료 — code-scan validate 로 확인하세요`.
- `--dry-run`은 `mode: "apply"`, `dryRun: true`로 같은 스키마를 내고 `commitSplit`을 호출하지 않는다(쓰기 0건).

##### (G) 에러 코드 요약 (신규 5종, 전부 exit 1)

| 코드 | 발생 조건 | 쓰기 상태 |
|------|----------|----------|
| `split_usage_invalid` | `--plan`/`--groups` 동시 또는 모두 부재, 위치 인자 부재 | 0건 |
| `split_inline_mode` | `headerSource`가 `manifest`가 아님 | 0건 |
| `split_target_invalid` | 대상이 code-map 밖 / 부재 / 샤드 | 0건 |
| `split_groups_invalid` | groups 문서 스키마·라벨·키 실재·중복 위반, 사전 불변식 위반 | 0건 |
| `split_write_failed` | tmp 작성 실패 | 0건 (tmp 정리됨) |
| `split_rollback` | rename 커밋 중 실패 | 백업 복원 시도 후 0건 목표 |
| `split_verify_failed` | 사후 엔트리 총합·중복 불일치 | 백업 복원 후 0건 목표 |

> 기존 에러 코드에 합류시키지 않고 신규 5+2종을 만드는 이유: `split`은 **자산을 쓰는 유일한 신규 명령**이므로 실패 지점별로 "쓰기가 일어났는가"가 다르고, 그 구분이 사람의 다음 행동(재실행 vs 수동 확인)을 가른다. 반면 F-001의 설정 타입 위반은 쓰기와 무관하므로 기존 `code_scan_config_invalid`에 합류시켰다(§3.1.2 (D)).

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음 — `split`은 소유자가 명시적으로 호출하는 명령이며 자동 실행 경로(hook·CLOSE 게이트)에 배선하지 않는다. 근거: brain 승계 #3(의미 경계는 소유자의 몫)이며, 자동 실행은 소유자 확인 없이 자산을 쓰는 것이다.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | F-3 AC | 통합 테스트 | `split --groups` 실행 후 `_shards/{label}.json`이 생성되고 베이스에 `shards` 선언이 추가된다 |
| TS-041 | F-3 AC (유실 0) | 통합 테스트 | **실행 전후 엔트리 총합이 동일**하다 (실제 파일 재로딩 기준) |
| TS-042 | F-3 AC (미지정 잔존) | 통합 테스트 | groups에 없는 엔트리는 베이스에 그대로 남는다 |
| TS-043 | F-3 AC (validate) | 통합 테스트 | 실행 후 `validate` **차단 위반 0건**(exit 0) |
| TS-044 | F-3 AC (scaffold no-op) | 통합 테스트 | 실행 후 `scaffold`가 `created=0 updated=0` (전량 `unchanged`) |
| TS-045 | F-3 AC (`--dry-run`) | 통합 테스트 | `--dry-run`은 결과를 출력하고 `.opal/code-map/` 트리를 **바이트 동일**하게 남긴다 |
| TS-046 | U-4 ① | 기능 테스트 | 존재하지 않는 엔트리 키를 지정하면 exit 1 `split_groups_invalid` + **쓰기 0건**(트리 바이트 동일) |
| TS-047 | U-4 ① | 기능 테스트 | 한 엔트리를 2개 그룹에 지정하면 exit 1 + 쓰기 0건 |
| TS-048 | U-4 ②③ (원자성) | 통합 테스트 | 쓰기 실패를 주입(대상 디렉토리 권한 제거 등)하면 exit 1 + `.opal/code-map/` 트리가 **실행 전과 바이트 동일**하고 `*.tmp-split` 잔존 0건 |
| TS-049 | U-4 ④ | 통합 테스트 | 사후 검증에서 총합 불일치를 만들면 롤백되어 트리가 원상 복구된다 |
| TS-050 | U-1 | 기능 테스트 | `--plan --json` 출력을 그대로 `--groups -`(stdin)로 파이프하면 성공한다 (왕복 성립) |
| TS-051 | U-1 | 기능 테스트 | groups 문서의 `manifest`가 CLI 인자와 다르면 exit 1 `split_groups_invalid` |
| TS-052 | F-3 AC (기존 샤드) | 통합 테스트 | 이미 샤드가 있는 베이스에 새 라벨을 추가하면 기존 샤드 파일이 무변화이고 `shards` 순서가 보존된다 |
| TS-053 | 라벨 안전 | 기능 테스트 | `../evil`·`_shards`·대문자 라벨은 exit 1 `split_groups_invalid` (경로 이탈 차단) |
| TS-054 | 완료기준 ④ | 통합 테스트 | 초과 매니페스트 1개를 `--plan` → `split` → `validate` 순으로 처리해 `manifest_oversize`가 **0건이 되고** 엔트리 유실 0건임이 입증된다 |

---

### F-006: 유도 경로

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `checkOversize` 위반 페이로드에 `entries`·`minFiles`·`recommendedShards`·`next` 4필드 추가 (§3.3.2 (B)에 통합) / scaffold stderr 문구에 명령 병기 (§3.3.2 (C)에 통합) | `code-scan.js:2149-2151`·`:1915-1919` |
| 2 | `opal/core/references/tools.md` | 문서 | code-scan 절에 "분할 절차 4단" 기재 (F-009와 같은 Step) | `tools.md:202-343` |

#### 3.6.2 설계

##### (A) 위반 페이로드 (U-3 채택안)

| 필드 | 값 | 성격 |
|------|---|------|
| `detail` | `` `${size}/${maxBytes}` `` | **불변** — 082 S-15가 정확 단언(`tests/test-shard.js:415`, H-8) |
| `entries` | 해당 매니페스트 자신의 엔트리 수 | 신규(2축의 두 번째 축을 눈에 보이게) |
| `minFiles` | 적용된 하한 | 신규(왜 걸렸는지 자기설명) |
| `recommendedShards` | `max(2, ceil(size / targetBytes))` | 신규(F-5 AC "권고 조각 수") |
| `next` | `` `code-scan split ${manifestRel} --plan` `` | 신규(F-5 AC "다음 명령", 그대로 실행하면 F-004 제안이 나온다) |

- 위반 객체에 선택 필드를 붙이는 것은 기존 관용이다 — `sub`·`key`·`file`이 code별로 다르게 붙는다(`code-scan.js:2124`·`:2201`·`:2245`).

##### (B) 분할 절차 4단 (문서화 대상 — `tools.md` code-scan 절)

| # | 단계 | 명령 | 주체 |
|---|------|------|------|
| 1 | 대상 확인 | `code-scan validate --json` → `violations[].code === 'manifest_oversize'`의 `next` 필드 | 도구 |
| 2 | 후보 제시 | `code-scan split <manifest> --plan --out <groups.json>` | 도구 |
| 3 | **경계 확정** | `groups.json`의 `groups[].label`·`files` 편집, `unassigned` 배분 결정 | **사람/워커** |
| 4 | 집행 + 검증 | `code-scan split <manifest> --groups <groups.json> --dry-run` → 확인 후 `--dry-run` 제거 → `code-scan validate` | 도구 |

- 3단이 사람의 책임임을 문서에 명시한다 — brain 승계 #3(§1.5)과 TASK 확정 방향 #5("의미 판단(1단계)은 사람/워커가 한다")의 문서 반영.

#### 3.6.3 환경 변경 / 3.6.4 배치·마이그레이션
해당 없음.

#### 3.6.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | F-5 AC | 기능 테스트 | `manifest_oversize` 위반에 `recommendedShards`(≥2 정수)와 `next`(문자열)가 포함된다 |
| TS-061 | F-5 AC | 통합 테스트 | `next` 필드의 명령을 **그대로 실행**하면 F-004 제안 출력이 exit 0으로 나온다 |
| TS-062 | H-8 | 기능 테스트 | `detail`이 `` `{bytes}/{maxBytes}` `` 포맷을 유지한다(정확 단언) |
| TS-063 | F-5 AC | 기능 테스트 | scaffold stderr 경고에 `split … --plan` 명령이 포함된다 |
| TS-064 | F-8 AC | 산출물 검사 | `tools.md`에 분할 절차 4단이 기재되고 3단의 주체가 사람/워커로 명시된다 |

---

### F-007: 구 위치 키 이전 처리

#### 3.7.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `loadCodeMap`의 `manifestMaxBytes` 스키마 게이트 제거 → `deprecationOnce` 안내로 교체(`:869-876`) / `manifestMaxBytes(ctx)` 함수 제거(`:880-884`) | `code-scan.js:869-884`·`:430`·`:451`·`:460` |
| 2 | `opal/tools/code-scan/tests/test-shard.js` | 테스트 | S-16 (a)~(e) 주소 이전 + S-15/S-17/S-25 픽스처 대응 (F-008과 같은 Step) | `tests/test-shard.js:426-539` |

#### 3.7.2 설계

##### (A) `loadCodeMap` 게이트 교체 (`code-scan.js:869-876`)

```js
// 구 위치 manifestMaxBytes는 폐기됐다 (083 F-6 / U-6). 값을 읽지 않고 실행당 1회 안내만 한다 —
// 무시할 키를 타입 검증해 차단하는 것은 "무시한다"와 모순이다(080 F-002 선례: :430/:451/:460).
if (hasOwn(index, 'manifestMaxBytes')) {
  deprecationOnce('index_manifest_max_bytes',
    '.opal/code-map/index.json의 manifestMaxBytes는 폐기되었습니다 — ' +
    '{프로젝트}/.opal/code-scan.json의 "shardPolicy": {"maxBytes": <바이트>} 로 이전하세요 ' +
    '(자동 변환하지 않습니다)');
}
```

- `invalid_index` 승격을 하지 않으므로 **비차단**이다 (F-6 AC).
- "자동 변환하지 않습니다"는 080의 구형 값 안내 문구(`code-scan.js:312-313`)와 같은 표현을 재사용한다 — 사용자에게 도구가 자산을 몰래 고치지 않는다는 계약을 일관되게 전달한다.
- `deprecationOnce`(폐기 안내)와 `noticeOnce`(비차단 사유)를 구분해 쓴다 — 구 위치 키는 **폐기**이므로 전자, 전역 설정 파손은 **사유 노출**이므로 후자(§3.2.2 (B)).

##### (B) 우선순위 최종 형태 — 3단 유지 (확정 방향 #7-c)

```
{프로젝트}/.opal/code-scan.json  shardPolicy.{maxBytes,minFiles}   ← 1순위
~/.opal/setting.json             shardPolicy.{maxBytes,minFiles}   ← 2순위
DEFAULT_SHARD_POLICY (코드 상수)  {10240, 40}                       ← 3순위
─────────────────────────────────────────────────────────────────
.opal/code-map/index.json        manifestMaxBytes                  ← 폐기 (해석 경로에 없음)
```

- 구 위치를 하위 순위로 남기면 4단이 되어 확정 방향 #7-c("3단이며 읽는 지점은 1곳")를 위반한다. 사용 프로젝트가 0건(TASK U-6)이므로 지킬 자산도 없다.

##### (C) 단언·픽스처 주소 이전 매핑 표 (제약 ⑤ 준수 방식)

> **[MUST] `TASK.md` §제약 조건: 기존 픽스처 단언 완화 금지 — 기본값 변경으로 깨지면 픽스처에 정책 오버라이드를 명시해 흡수한다. 단언 삭제·skip·조건 완화는 금지한다.**
> 이 표의 규칙: **이전 전 단언 1건 → 이전 후 최소 1건.** 삭제 0건, skip 0건, `strictEqual` → `ok`/`match` 완화 0건.

| 082 단언 | 위치 | 083 이전 후 | 강도 |
|---------|------|-----------|------|
| S-15 `manifest_oversize` 열거 + `detail` 정확 단언 + exit 0 | `test-shard.js:407-420` | **단언 불변**. 픽스처에 `shardPolicy: {maxBytes:200, minFiles:1}` 명시로 흡수 | 동일 |
| S-16 (a) 작은 값 → 검출 | `:434-441` | 헬퍼 `setManifestMaxBytes` → `setShardPolicy(dir, {maxBytes})`(`.opal/code-scan.json` 기록)로 교체. 단언 불변 | 동일 |
| S-16 (b) 큰 값 → 0건 | `:443-452` | 동일 교체, 단언 불변 | 동일 |
| S-16 (c) 미지정 → 내장 기본값 | `:454-465` | 기대 기본값 `20480` → **`10240`**으로 갱신 + 사전조건 단언(`size < 10240`) 갱신. 2축 때문에 `minFiles` 미지정 시 40이 적용되므로 사전조건에 **엔트리 수 조건 1건 추가**(강화) | **강화** |
| S-16 (d) `size===limit` 비초과 | `:467-477` | 동일 교체, 단언 불변 | 동일 |
| S-16 (d2) `size===limit+1` 초과 | `:479-487` | 동일 교체 + 픽스처 `minFiles:1` | 동일 |
| S-16 (e) 타입 위반 → `invalid_index` exit 1 | `:489-501` | **주소 이전**: `.opal/code-scan.json`의 `shardPolicy.maxBytes` 타입 위반 → exit 1 + `error === 'code_scan_config_invalid'`. **추가 2건**: (i) 구 위치 `index.json manifestMaxBytes` 타입 위반은 **exit 0**(비차단) + stderr 폐기 안내, (ii) 전역 타입 위반은 exit 무영향 + 안내 | **강화 (1→3)** |
| S-17 scaffold stderr 1줄 + stdout 동일 | `:507-521` | 대조군 생성 방식을 `setManifestMaxBytes(undefined)` → `setShardPolicy(dir, {maxBytes: 999999})`로 교체. 단언 불변 | 동일 |
| S-25 샤드 자신 측정 | `:527-539` | 픽스처에 `shardPolicy: {maxBytes:200, minFiles:1}` 명시로 흡수. 단언 불변 | 동일 |
| S-23 목표달성 6항 | `:916-` | `shard-goal` 3픽스처에 `shardPolicy: {maxBytes:400, minFiles:1}` 명시로 흡수. 단언 불변 | 동일 |
| S-22 `tools.md`에 `manifestMaxBytes` 반영 | `:601-604` | **정규식 유지 가능** — 폐기 안내 절에 키 이름이 남으므로 GREEN. 추가로 `shardPolicy` 정규식 1건 신설 | **강화 (1→2)** |

- 픽스처 5종에서 `index.json`의 `manifestMaxBytes`를 **제거**한다 — 남겨두면 `deprecationOnce`가 stderr에 1줄을 써서 S-17의 대조군 단언(`withoutRes.stderr.trim() === ''`, `test-shard.js:519-520`)을 깨뜨린다.

#### 3.7.3 환경 변경 / 3.7.4 배치·마이그레이션
자동 변환 없음. 구 위치 사용자는 안내 문구를 보고 수동 이전한다.

#### 3.7.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-070 | F-6 AC | 기능 테스트 | 구 위치에만 `manifestMaxBytes`가 있는 자산에서 값이 **무시**되고 기본값(또는 신 위치 값)이 적용된다 |
| TS-071 | F-6 AC (비차단) | 기능 테스트 | 구 위치 타입 위반(문자열·음수)에서 **exit 0/2**이며 `invalid_index` exit 1로 승격하지 않는다 |
| TS-072 | F-6 AC (안내) | 기능 테스트 | 구 위치 키 존재 시 stderr에 폐기 안내 1줄 + 새 주소가 포함되고, **실행당 1회**만 나온다 |
| TS-073 | F-6 AC (결정론) | 기능 테스트 | 구·신 위치 동시 존재 시 신 위치가 적용되고 구 위치는 결과에 영향이 0이다 |
| TS-074 | 제약 ⑤ | 산출물 검사 | 082 S-15/S-16/S-17/S-23/S-25 단언이 삭제·skip·완화 없이 존재하고, §3.7.2 (C) 매핑 표대로 이전됐다 |
| TS-075 | 확정 방향 #7-c | 산출물 검사 | 소스에 `manifestMaxBytes` 값을 **읽는** 코드가 0곳이다 (안내 문구의 문자열 등장은 허용) |

---

### F-008: 회귀 가드 + 전역 설정 격리

#### 3.8.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/tests/test-shard-policy.js` | 테스트 | 083 계약 테스트 (TS-001~TS-016, TS-020~TS-026, TS-030~TS-039, TS-040~TS-054, TS-060~TS-064, TS-070~TS-075) | TASK F-7 |
| 2 | `tests/fixtures/shard-policy/axis-bytes-only/` | 테스트 | 바이트 초과 + 엔트리 미달 (2축 오탐 차단 검증) | TS-020 |
| 3 | `tests/fixtures/shard-policy/axis-both/` | 테스트 | 2축 충족 (엔트리 다수) | TS-021·TS-023 |
| 4 | `tests/fixtures/shard-policy/precedence/` | 테스트 | 프로젝트·전역 동시 존재 (셀 머지·우선순위) | TS-003·TS-004 |
| 5 | `tests/fixtures/shard-policy/legacy-index/` | 테스트 | 구 위치 `manifestMaxBytes`만 존재 | TS-070~TS-073 |
| 6 | `tests/fixtures/shard-policy/split-target/` | 테스트 | `--plan`/`split` 대상 (다토큰 엔트리 다수 + 1건 토큰 포함) | TS-030~TS-054 |
| 7 | `tests/fixtures/shard-policy/homes/{absent,valid,broken,nokey,badtype}/` | 테스트 | 가짜 `OPAL_HOME` 5종 (`setting.json` 상태별) | TS-010~TS-016 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `tests/test-shard.js` | 테스트 | `setManifestMaxBytes` → `setShardPolicy` 교체 / S-16 (c) 기대 기본값 갱신 / S-16 (e) 에러 코드 이전 + 2건 추가 / S-17 대조군 방식 교체 / S-22 정규식 1건 추가 / `run()` 하네스에 `OPAL_HOME` 주입 | §3.7.2 (C) |
| 2 | `tests/fixtures/shard-violations/oversize/.opal/code-scan.json` + `.opal/code-map/index.json` | 테스트 | `shardPolicy: {maxBytes:200, minFiles:1}` 추가 / `manifestMaxBytes` 제거 | H-1·H-2 |
| 3 | `tests/fixtures/shard-violations/oversize-shard/` 동 2파일 | 테스트 | 동일 | H-1·H-2 |
| 4 | `tests/fixtures/shard-goal/{before,mid-undeclared,mid-duplicate}/` 각 2파일 (6파일) | 테스트 | `shardPolicy: {maxBytes:400, minFiles:1}` 추가 / `manifestMaxBytes` 제거 | H-1·H-2 |
| 5 | `tests/test-validate.js`·`test-scaffold.js`·`test-regression.js`·`test-scope-filter.js`·`test-hook.js` | 테스트 | `spawnSync` 하네스에 `OPAL_HOME` 주입 (정책 소비 명령을 실행하는 파일) | U-7 |

#### 3.8.2 설계

##### (A) 픽스처 정책 오버라이드 규격 (제약 ⑤ 흡수 방식)

```json
// tests/fixtures/shard-violations/oversize/.opal/code-scan.json
{
  "headerSource": "manifest",
  "shardPolicy": { "maxBytes": 200, "minFiles": 1 },
  "scopes": { ... }
}
```

- `minFiles: 1`을 명시하는 이유: 082 픽스처의 엔트리 수는 0~6건이므로(실측: `oversize` 2건, `shard-goal/before` 6건, `oversize-shard` 베이스 0건) 기본 하한 40에서는 전부 판정 탈락한다(H-2). **단언을 고치는 대신 픽스처에 정책을 명시**하는 것이 제약 ⑤의 요구다.
- `tests/test-regression.js:557-569` TS-063(픽스처 전량 `headerSource` 명시 검사)은 `headerSource` 정규식만 보므로 키 추가와 충돌하지 않는다.

##### (B) 전역 설정 격리 하네스 (U-7 실행)

```js
// 각 테스트 파일의 run() 헬퍼에 공통 적용 — 개발자 실제 홈을 절대 읽지 않는다.
const ISOLATED_HOME = path.join(FIX, 'shard-policy', 'homes', 'absent');   // setting.json 부재 트리
function run(cwd, args, input, homeOverride) {
  return spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 10000, input,
    env: Object.assign({}, process.env, { OPAL_HOME: homeOverride || ISOLATED_HOME }),
  });
}
```

| 규칙 | 내용 |
|------|------|
| 기본 격리 | 인자 미지정 시 **`homes/absent`**(빈 트리)를 주입한다 — 전역 정책이 없는 상태가 모든 기존 테스트의 암묵 전제이므로 기본값이 그것이어야 한다 |
| 적용 범위 | 정책 소비 명령(`validate`·`scaffold`·`split`)을 실행하는 테스트 파일 전량. 조회 전용 파일도 **일괄 주입**한다 — 예외를 만들면 나중에 명령이 추가될 때 격리가 새는 지점이 된다 |
| 전역값 경로 검증 | `homes/valid`(정책 있음)·`homes/broken`(깨진 JSON)·`homes/nokey`(`bootstrap`+`models`만)·`homes/badtype`(타입 위반)을 `homeOverride`로 지정해 검증한다 |
| 실 홈 무의존 입증 | 실 홈의 `~/.opal/setting.json`을 **읽기만** 하여 `shardPolicy` 유무를 기록하고, 그 값과 무관하게 전체 결과가 동일함을 단언한다. [MUST] `TASK.md` §제약 조건 배포 경계에 따라 **실 홈 파일을 변조하지 않는다** — 변조 대조는 가짜 홈 2종 비교로 대체한다 |

- `homes/absent`는 빈 디렉토리이므로 git이 추적하지 않는다 → `.gitkeep` 파일 1개를 둔다.

##### (C) 골든 불변 보증 (H-13)

| 축 | 보증 방식 |
|----|----------|
| stdout 바이트 | `tests/test-regression.js:503-511`의 8커맨드 비교를 **그대로 유지**한다. 조회 명령은 `resolveShardPolicy`를 호출하지 않으므로(지연 로딩, §3.2.2 (B)) 전역 파일 I/O가 발생하지 않는다 |
| 파일 바이트 | `git diff --stat -- opal/tools/code-scan/tests/fixtures/golden/` 결과가 빈 문자열이어야 한다. [MUST] 재캡처 금지 |
| stderr | `legacy-repo` 픽스처는 code-map 부재 + `headerSource: inline`이므로 정책·구키 안내 경로에 진입하지 않는다 |

##### (D) RED-first 계약

- [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 테스트 파일 수정 금지. 082가 같은 규칙을 파일 상단에 명문화했다(`tests/test-shard.js:19-21`: "기대값 완화로 통과를 유도하는 것은 reward hacking이다").
- `test-shard-policy.js`는 구현(§4.2 Step 5) **이전에** 작성되어 전량 RED여야 한다. 단, §3.7.2 (C)의 `test-shard.js` 주소 이전은 **구현과 같은 Step**에서 수행한다 — 기존 GREEN 테스트를 미리 깨뜨려 놓으면 RED 신호가 "미구현"과 "이전 미완"으로 섞인다.

#### 3.8.3 환경 변경
해당 없음 (테스트 프레임워크 `node:test` 유지, 신규 패키지 0개).

#### 3.8.4 배치/마이그레이션
해당 없음.

#### 3.8.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-080 | F-7 AC | 회귀 테스트 | `opal/tools/code-scan/tests/` **전량 GREEN** (11 + 1 신규 = 12 스크립트) |
| TS-081 | F-7 AC | 회귀 테스트 | `fixtures/golden/*` 8파일 **바이트 diff 0** (`git diff --stat` 빈 결과) |
| TS-082 | F-7 AC | 회귀 테스트 | 샤드 미선언 자산(`codemap-repo`·`legacy-repo`) 출력 불변 |
| TS-083 | F-7 AC(격리) | 통합 테스트 | 가짜 홈 5종 중 어느 것을 주입해도 **정책 미적용 명령의 결과가 동일**하다 |
| TS-084 | F-7 AC(격리) | 산출물 검사 | 모든 테스트 파일의 `spawnSync` 호출이 `OPAL_HOME`을 주입한다 (정적 grep) |
| TS-085 | 제약 ⑤ | 산출물 검사 | 082 시나리오 26종의 테스트 함수가 전부 존재하고 `skip`·`todo` 마킹이 0건이다 |

---

### F-009: 문서·배포 반영 / F-010: 전역 설정 시드

#### 3.9.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `VERSION` `'1.5.0'` → `'1.6.0'`(`:37`) / 상단 `@header` description·note 갱신(`:2-11`) / 하단 변경이력 v1.6.0 행 추가(`:2474` 뒤) / `USAGE`에 `split`·`shardPolicy` 반영(`:72-129`) | `code-scan.js:37`·`:2-11`·`:2429-2474` |
| 2 | `opal/core/references/tools.md` | 문서 | code-scan 절(`:202-343`) — `split` 커맨드 2모드·2축 판정·설정 3단 우선순위·`shardPolicy` 스키마·에러 코드 7종·분할 절차 4단(§3.6.2 (B)) + 파일 말미 변경이력 행 | `tools.md:202-343`·`:956-` |
| 3b | `opal/core/references/pm/code-scan-management.md` | 문서 | `init` 등재 + 추론 소스 규약 표에 `shardPolicy` 행 + `exclude` 표↔예시 불일치 해소 + 변경이력 v1.5. **[MUST] 배포 경계 — 수정 대상은 `~/.opal/references/…`가 아니라 이 소스 경로다** | `code-scan-management.md:12-46`·`:104-112` |
| 3 | `opal/core/references/harness/header-rules.md` | 문서 | §워커 권한 경계에 "`_shards/` 파일 생성·엔트리 이동은 `code-scan split`이 집행한다(도구 관할)" 1줄 + §기록 위치 판정 무변경 + 변경이력 v1.7 | `header-rules.md:44-49`·`:157` |
| 4 | `opal/core/setting.default.json` | 배포 | 최상위 `shardPolicy` 추가 (`_help` 포함) | F-8b |
| 5 | `scripts/install-mac.sh` | 배포 | `install_opal_setting`(`:918-953`) 병합 python을 **키 목록 루프**로 재작성 | H-11 |
| 6 | `docs/ARCHITECTURE.md` · `docs/PROJECT.md` | 문서 | code-scan 도구 서술에 2축 판정·`split`·설정 3단·사전 연동 반영 (opal-task-agent — PM Gate 정정) | TASK F-8 |

#### 3.9.2 설계

##### (A) 버전 판정 — `1.5.0` → `1.6.0` (semver minor)

| 축 | 판단 |
|----|------|
| 신규 기능 | `split` 서브명령 1개 + `shardPolicy` 설정 3단 → 기능 추가 |
| 파괴적 변경? | 기본 상한이 20480 → 10240으로 **내려가고**, 하한 40이 새로 걸린다. 순 효과는 대상 집합의 변화이며 **전면 비차단**이므로(확정 방향 #8) 어떤 명령도 새로 exit 1이 되지 않는다 |
| 구 키 폐기 | `index.json manifestMaxBytes` 무시 — 사용 프로젝트 0건 + 비차단 안내 |
| 외부 계약 | 조회 8커맨드 stdout 불변(골든), `validate` JSON은 필드 **추가만**, `counts` 키 집합 불변 |
| **결론** | **minor**. 082가 `1.4.0 → 1.5.0`을 같은 논리로 판정한 선례(`tasks/082-…/PLAN.md` §3.8.1)를 따른다 |

##### (B) `setting.default.json` 추가 형태 (F-8b)

```json
{
  "bootstrap": "on",
  "models": { "...": "기존 무변경" },
  "shardPolicy": {
    "_help": "code-map 매니페스트 분할 판정 정책. 2축이며 '바이트 초과 AND 엔트리 수 이상'일 때만 분할 대상이다. 프로젝트별로 바꾸려면 {프로젝트}/.opal/code-scan.json 최상위에 동일 구조로 바꿀 셀만 덮어쓴다(셀 단위 머지). 상세: ~/.opal/references/tools.md code-scan 절",
    "maxBytes": 10240,
    "minFiles": 40
  }
}
```

- `_help`는 `models._help`와 동일한 관용이며, `normalizeShardPolicy`가 알 수 없는 키를 무시하므로(U-5 (C)) 안전하다 — **이 관용을 지키려고 (C)를 결정한 것**이다.
- 문구가 `setting.local.json`을 가리키지 않는다 — 확정 방향 #7-b(프로젝트 소스는 `code-scan.json` 단일, `setting.local.json` 불채택)를 문서 문구에서도 지킨다. `models._help`와 이 부분이 다른 것이 의도된 차이다.

##### (C) `install-mac.sh` 시드 재작성 (H-11)

```python
# install_opal_setting 병합 블록 교체 (:923-948)
import json, sys
src_path, dst_path = sys.argv[1], sys.argv[2]
try:
    with open(src_path, 'r', encoding='utf-8') as f: default = json.load(f)
    with open(dst_path, 'r', encoding='utf-8') as f: existing = json.load(f)
except Exception as e:
    sys.stderr.write(f"warn: setting.json 로드 실패 — {e}\n"); sys.exit(1)

SEED_KEYS = ['models', 'shardPolicy']       # 부재 시에만 시드하는 최상위 키 목록
seeded = []
for k in SEED_KEYS:
    if k in existing:  continue             # 사용자 수정값 절대 보존 (멱등)
    if k not in default: continue
    existing[k] = default[k]; seeded.append(k)

if not seeded:
    sys.stderr.write("info: setting.json 시드 대상 키 전부 존재 — 무변 (멱등)\n"); sys.exit(0)

with open(dst_path, 'w', encoding='utf-8') as f:
    json.dump(existing, f, ensure_ascii=False, indent=2); f.write('\n')
sys.stderr.write(f"info: setting.json에 {', '.join(seeded)} scaffold 병합 완료\n")
```

| 계약 | 보증 방식 |
|------|----------|
| 기존 사용자값 무손실 | `if k in existing: continue` — 존재하는 키는 **읽지도 쓰지도 않는다**. `bootstrap`은 `SEED_KEYS`에 없으므로 dict 유지로 자동 보존 |
| 멱등 | 2회 실행 시 두 번째는 `seeded == []` → 쓰기 0건 |
| 실패 안전 | 예외 시 `sys.exit(1)` → 셸의 `|| warn "…기존 파일 유지"`(`install-mac.sh:923`)가 기존 파일을 보존. warn 문구를 `models` 한정에서 일반 문구로 바꾼다 |
| 부재 경로 | `cp "$src" "$dst"`(`:951`)가 `shardPolicy`를 포함한 원본을 그대로 복사 — 별도 처리 불필요 |
| 시드 없는 환경 | 코드 상수 폴백으로 동작(F-1 AC) — install을 돌리지 않은 환경도 정상 |

##### (D) `tools.md` 갱신 항목 (S-22 단언 대응)

| 항목 | 내용 |
|------|------|
| 커맨드 목록 | `split <manifest> --plan \| --groups <path\|->` + `init --header-source <inline\|manifest> [--write] [--force]` **2행** 추가 (현행 13 → **15 서브명령**) |
| 옵션 표 | `--groups`·`--plan` 추가, `--out`이 `discover`·`split` 공용임을 명시 |
| 에러 코드 표 | `split_usage_invalid`·`split_inline_mode`·`split_target_invalid`·`split_groups_invalid`·`split_write_failed`·`split_rollback`·`split_verify_failed` 7행 + **`init_header_source_required`·`config_exists` 2행** = 9행 추가 |
| 프로젝트 설정 | `.opal/code-scan.json` 예시에 `shardPolicy` 추가 + **3단 우선순위 표** |
| 폐기 안내 | `index.json manifestMaxBytes` 폐기 + 새 주소 1줄 — **`manifestMaxBytes` 문자열이 남으므로 082 S-22 정규식(`test-shard.js:604`)이 GREEN 유지된다** |
| 분할 절차 | §3.6.2 (B) 4단 표 |
| 변경이력 | 파일 말미 표에 행 추가 (일시 KST + `(083)`) |

##### (F) `pm/code-scan-management.md` 갱신 (F-012)

> **[MUST] 배포 경계**: 수정 대상은 **`opal/core/references/pm/code-scan-management.md`**(소스)다. `~/.opal/references/pm/…`는 install 산출물이므로 직접 편집하지 않는다.

| 항목 | 내용 |
|------|------|
| §생성 시점 | "PM이 즉석 추론으로 생성한다"는 산문 옆에 **`code-scan init --header-source <값> --write`가 그 추론을 도구로 수행한다**는 1줄 추가. PM은 `headerSource` 2택 확인(중개)과 명령 실행만 담당한다 |
| §추론 소스 규약 표 | **`shardPolicy` 행 신설** — "추론·생성하지 않음 \| `init`은 이 키를 쓰지 않는다. 미설정이면 `~/.opal/setting.json` → 코드 상수로 3단 폴백되므로, 초안에 기재하면 폴백이 무력화된다" (§3.12.2 (E)) |
| §추론 소스 규약 `exclude` 행 | 표(`:20`)와 예시(`:30`)의 불일치를 해소한다 — **예시 10종을 기준으로 확정**하고 표에서 `tests`를 제거한다. 사유 1줄 병기: "테스트 코드를 제외하면 커버리지 판정이 왜곡된다" (§3.12.2 (D)) |
| §생성 보고 | 보고 1줄이 **도구 stderr에서 나온다**는 사실 명시 (PM이 별도로 조립하지 않는다) |
| §headerSource 필드 관리 | `:87` "도구는 이 질문을 하지 않는다"의 실현 형태가 **`--header-source` 필수 인자**임을 1줄 추가. 잘못된 설정 복구 경로(`init … --write --force`, `.bak` 1세대 백업) 1줄 추가 |
| 변경이력 | v1.5 행 추가 (일시 KST + `(083)`) |

##### (E) `header-rules.md` 갱신

- §워커 권한 경계(`:44-49`)의 금지(도구 관할) 행에 이미 `shards`·`files` 키 목록이 있다 → **권한 경계 자체는 무변경**이고, "이 관할을 집행하는 수단이 `code-scan split`이다" 1줄을 추가한다. 083은 새 권한을 만들지 않고 기존 관할의 집행 수단을 추가했을 뿐임을 문서가 말해야 한다.
- 변경이력 v1.7 행 추가 (일시 KST + `(083)`).

#### 3.9.3 환경 변경
해당 없음 (신규 패키지 0개, python3는 install이 이미 사용 중).

#### 3.9.4 배치/마이그레이션
- 배포는 `bash scripts/install-mac.sh`로 수행하며, 검증은 **소스 경로**에서 실행한다 ([MUST] 배포 경계 — `~/.opal/tools/code-scan/` 직접 편집 금지).
- 기존 설치 환경의 `~/.opal/setting.json`에 `shardPolicy`가 시드되는지는 install 재실행으로 확인한다.

#### 3.9.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-090 | F-8 AC | 산출물 검사 | `code-scan.js` `VERSION === '1.6.0'` + 변경이력에 `(083)` 행 + 일시(KST) |
| TS-091 | F-8 AC | 산출물 검사 | `tools.md`에 `split`·2축 판정·`shardPolicy`·3단 우선순위·에러 코드 7종이 반영되고 변경이력 행이 추가됐다 |
| TS-092 | F-8 AC | 산출물 검사 | `header-rules.md`에 `split` 집행 1줄 + 변경이력 v1.7 |
| TS-093 | F-8b AC | 기능 테스트 | `setting.default.json`에 `shardPolicy.maxBytes === 10240`·`minFiles === 40`이 있고 JSON 파싱된다 |
| TS-094 | F-8b AC (머지 안전) | 통합 테스트 | 가짜 홈 3형태(`models`만 / `models`+`shardPolicy` / `bootstrap`만)에 시드 로직을 적용해 **기존 값이 1바이트도 변하지 않고** 부재 키만 추가된다 |
| TS-095 | F-8b AC (멱등) | 통합 테스트 | 시드 로직 2회 실행 결과가 바이트 동일하다 |
| TS-096 | F-8b AC (폴백) | 기능 테스트 | 시드가 없는 환경(`homes/absent`)에서 코드 상수로 정상 동작한다 |
| TS-097 | F-8 AC | 산출물 검사 | `code-scan.js` 상단 `@header` description·note에 2축·`split`·3단 해석이 반영됐다 |

---

### F-011: 용어사전 로더

#### 3.10.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `resolveDictPath`·`parseWordDictionary`·`loadWordDictionary` 신설 (`loadGlobalSetting` 인접) + `shardPolicy.dictPath` 스키마 반영(§3.1.2 (A)(B) 개정분) | `code-scan.js:253`·`:384-388`·`:1142-1148` |
| 2 | `opal/core/references/tools.md` | 문서 | 사전 탐색 3단 + 옵셔널 폴백 3분기 기재 (F-009와 같은 Step) | §3.9.2 (D) |

#### 3.10.2 설계

##### (A) `resolveDictPath(ctx, policy)` — 탐색 3단, 앞이 성공하면 뒤를 보지 않는다

```js
/**
 * 표준단어사전 경로를 해소한다. **어떤 실패도 throw하지 않는다.**
 * [MUST] `opal/skills/op-data-dictionary/SKILL.md:21`: "사전 저장 경로는 하드코딩하지 않는다.
 * docs/PROJECT.md에 등록된 {설계} 변수(설계 산출물 루트)를 읽어 {설계}/사전/으로 해소한다."
 * @returns {{abs:string|null, rel:string|null, source:'policy'|'project-var'|'default'|null, searched:string[]}}
 */
function resolveDictPath(ctx, policy) {
  const searched = [];
  const tryPath = (rel, source) => { … 존재하면 즉시 반환 … };

  // ① shardPolicy.dictPath 명시값 (3단 해석을 이미 거친 값)
  if (policy.dictPath) { const r = tryPath(policy.dictPath, 'policy'); if (r) return r; }

  // ② docs/PROJECT.md의 {설계} 변수 해소 → {설계}/사전/표준단어사전.md
  const designRoot = readDesignRootFromProjectMd(ctx.projectRoot);   // 실패 시 null (침묵)
  if (designRoot) { const r = tryPath(`${designRoot}/사전/${DICT_FILENAME}`, 'project-var'); if (r) return r; }

  // ③ 기본 경로 — SKILL.md 자기모순(H-19) 흡수: 두 후보를 순서대로 본다
  for (const rel of DICT_DEFAULT_RELS) { const r = tryPath(rel, 'default'); if (r) return r; }

  return { abs: null, rel: null, source: null, searched };
}

const DICT_FILENAME = '표준단어사전.md';
// [주의] op-data-dictionary/SKILL.md가 자기모순이다(H-19):
//   :21  → default `200.설계/210.사전/`
//   :72·:172 → `{설계}/사전/` (= `200.설계/사전/`)
// 어느 쪽이든 발견되도록 **두 후보를 순서대로** 본다. 새 규칙을 만드는 것이 아니라
// 문서가 말하는 두 경로를 모두 존중하는 것이다.
const DICT_DEFAULT_RELS = Object.freeze([
  `200.설계/사전/${DICT_FILENAME}`,
  `200.설계/210.사전/${DICT_FILENAME}`,
]);
```

| 안전 규칙 | 내용 |
|----------|------|
| 경로 제한 | 해소된 절대 경로가 `ctx.projectRoot` **하위**가 아니면 거부하고 다음 후보로 넘어간다 — `dictPath`에 `../../etc/passwd`를 넣어도 프로젝트 밖을 읽지 않는다(H-17) |
| 크기 상한 | 파일 크기가 `DICT_MAX_BYTES`(= 2 MiB)를 넘으면 "사전 없음"으로 취급 + `noticeOnce` — 거대 파일로 도구가 멈추지 않게 한다 |
| 읽기 전용 | 이 경로에 **쓰기 코드가 존재하지 않는다**. 사전 SSOT는 `op-data-dictionary`의 관할이다 |
| 침묵 규칙 | `searched`에는 모든 후보를 기록하되, **부재는 stderr를 내지 않는다**(부재 = 정상). `--plan` 출력의 `dict.searched`로만 노출한다 |

- `readDesignRootFromProjectMd`: `docs/PROJECT.md`를 읽어 `{설계}` 변수 등록을 찾는다. 등록 포맷이 프로젝트마다 다를 수 있으므로 **관대한 탐색**(표 행 `| {설계} | <경로> |` 또는 `- {설계} = <경로>` 또는 `{설계}: <경로>`)을 하고, 못 찾거나 파일 읽기가 실패하면 **`null`을 돌려 조용히 ③으로 넘어간다**. 이 프로젝트는 실제로 미등록이므로(§2.11.2) ③ 경로를 타는 것이 정상이다.

##### (B) `parseWordDictionary(md)` — **헤더 이름 기반** 파싱 (H-15 해소)

```js
/**
 * 표준단어사전.md를 파싱한다. **컬럼 위치를 가정하지 않는다.**
 * 근거: 같은 문서 안에 컬럼 수가 다른 표 2개가 존재한다
 *   `## 수식어`  | 한글 | 영문 | 약어 | 규칙 | 도메인 | 비고 |   (6열)
 *   `## 분류어`  | 한글 | 영문 | 약어 | 도메인 | 비고 |          (5열, `규칙` 없음)
 *   (`opal/skills/op-data-dictionary/SKILL.md:81-89` 실측)
 * 위치 기반 파서는 분류어 표에서 `약어` 자리에 `도메인` 값을 읽어 조용히 오분류한다.
 * @returns {{ok:true, rows:Array<{ko,en,abbr,index}>} | {ok:false, detail:string}}
 */
function parseWordDictionary(md) { … }
```

**파싱 규칙**:

1. 문서의 **모든 md 표**를 훑는다(섹션 헤딩은 보지 않는다 — 헤딩 이름이 바뀌어도 깨지지 않게).
2. 각 표의 **헤더 행**에서 셀을 trim하여 `한글`·`영문`·`약어`가 **전부** 있는 표만 채택한다. 그 3개의 **컬럼 인덱스를 헤더에서 얻는다**.
3. 구분선 행(`|---|---|`)은 건너뛴다. 셀 값은 trim하고 `-`·빈 문자열은 `null`로 둔다.
4. `en` 또는 `abbr` 중 **하나라도 있는 행만** 채택한다(둘 다 없으면 매칭에 쓸 수 없다).
5. `index`는 **채택된 행의 문서 등장 순서**다 — U-2 (3) 다중 매칭 tie-break("동률이면 사전 등재 순서")의 기준이며, 표가 2개여도 연속 번호를 부여해 전역 순서를 만든다.
6. 채택된 표가 **0개**면 `{ok:false, detail:'no table with 한글/영문/약어 header'}` → 호출자가 "사전 없음"과 동일 취급 + `noticeOnce`.

- 이 규칙이 만족하는 것: 수식어 표(6열)와 분류어 표(5열)를 **같은 코드로** 읽고, 향후 컬럼이 추가·재배치되어도 헤더 이름만 유지되면 깨지지 않는다.
- **의존성 0**: 정규식 + `split('|')` 기반. md 파서 라이브러리를 도입하지 않는다.

##### (C) `loadWordDictionary(ctx, policy)` — 폴백 3분기 확정 (U-2 (4))

```js
/**
 * @returns {{found:boolean, path:string|null, source:string|null, rows:Array|null, searched:string[]}}
 */
function loadWordDictionary(ctx, policy) {
  if (ctx._wordDict) return ctx._wordDict;                     // 실행당 1회 (지연 로딩)
  const p = resolveDictPath(ctx, policy);
  let out;
  if (!p.abs) {
    out = { found: false, path: null, source: null, rows: null, searched: p.searched };   // 침묵
  } else {
    let md = null;
    try { md = fs.readFileSync(p.abs, 'utf8'); } catch { md = null; }
    const parsed = md === null ? { ok: false, detail: 'unreadable' } : parseWordDictionary(md);
    if (!parsed.ok) {
      noticeOnce('shard_dict_unparsable',
        `${p.rel}을 표준단어사전으로 읽을 수 없습니다(${parsed.detail}) — 사전 대조 단계(S1~S3)를 건너뜁니다 (비차단). ` +
        `형식: | 한글 | 영문 | 약어 | … (opal/skills/op-data-dictionary/SKILL.md Step 3)`);
      out = { found: false, path: p.rel, source: p.source, rows: null, searched: p.searched };
    } else {
      out = { found: true, path: p.rel, source: p.source, rows: parsed.rows, searched: p.searched };
    }
  }
  ctx._wordDict = out;
  return out;
}
```

| 분기 | `found` | stderr | 사다리 영향 |
|------|---------|--------|-----------|
| 3단 탐색 전부 실패 (사전 없음) | `false` | **없음** (부재는 정상) | S1~S3 자동 skip, S4·S5만 실행 |
| 파일 존재 · 읽기/파싱 실패 · 컬럼 불일치 | `false` | `noticeOnce` **1줄** | 위와 동일 (사전 없음과 동일 취급) |
| 파싱 성공 · 매칭 0건 | `true` | 없음 | S1~S3 정상 실행, 0건 걷고 통과 |

- **[MUST] 비차단**: 이 함수는 `throw`도 `process.exit`도 하지 않는다. 선례 — `code-scan.js:1142-1143`: "차단 조건을 늘리지 않고 (D-5 범위 밖) 사유만 stderr 1줄로 노출하는 fail-soft를 택한다."
- **지연 로딩**: `split --plan` 경로에서만 호출된다. `scan`·`validate`·`scaffold`·`target`은 사전을 읽지 않으므로 골든 8커맨드에 새 I/O가 없다(H-13과 동일 논리).

#### 3.10.3 환경 변경
해당 없음 (신규 패키지 0개 — 정규식 기반 md 표 파서 자체 구현).

#### 3.10.4 배치/마이그레이션
해당 없음. 사전은 **옵셔널**이며 이 저장소에는 존재하지 않는다(§2.11.2) — 083 개발·검증 중에는 "사전 없음" 분기가 기본 경로다.

#### 3.10.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-120 | U-2 (4) 탐색 ① | 기능 테스트 | `shardPolicy.dictPath` 명시값이 최우선으로 사용되고 `dict.source === 'policy'` |
| TS-121 | U-2 (4) 탐색 ② | 기능 테스트 | `docs/PROJECT.md`의 `{설계}` 변수가 해소되어 `{설계}/사전/표준단어사전.md`를 찾고 `dict.source === 'project-var'` |
| TS-122 | U-2 (4) 탐색 ③ / H-19 | 기능 테스트 | 변수 미등록 시 기본 경로 **2후보**(`200.설계/사전/`·`200.설계/210.사전/`) 중 어디에 두어도 발견된다 |
| TS-123 | U-2 (4) 순서 | 기능 테스트 | ①이 성공하면 ②·③을 **읽지 않는다**(앞 단계 성공 시 뒤를 보지 않음) |
| TS-124 | H-15 | 기능 테스트 | **수식어(6열)·분류어(5열) 표를 모두 담은 사전**에서 두 표의 `영문`·`약어`가 정확히 추출된다 (위치 파싱이면 실패) |
| TS-125 | H-15 | 기능 테스트 | 헤더에 `한글`/`영문`/`약어`가 없는 표는 무시되고, 그런 표만 있으면 `found: false` + `noticeOnce` |
| TS-126 | U-2 (4) 폴백 | 기능 테스트 | 깨진 표(구분선 없음·셀 수 불일치)에서 exit code가 불변이고 S4·S5만 실행된다 |
| TS-127 | U-2 (4) 침묵 | 기능 테스트 | 사전 **부재** 시 stderr 무출력, **파손** 시 stderr 1줄 (실행당 1회) |
| TS-128 | H-17 경로 제한 | 보안 테스트 | `dictPath`가 프로젝트 루트 밖(`../../etc/passwd`)이면 읽지 않고 다음 후보로 넘어간다 |
| TS-129 | H-17 크기 상한 | 기능 테스트 | 사전 파일이 `DICT_MAX_BYTES` 초과면 "사전 없음" 취급 + 안내, 도구가 멈추지 않는다 |
| TS-130 | F-011 읽기 전용 | 기능 테스트 | `split --plan`·`split --groups` 실행 전후 사전 md·`docs/PROJECT.md` 바이트가 동일하다 |
| TS-131 | 골든 무영향 | 회귀 테스트 | 조회 8커맨드가 사전·`docs/PROJECT.md`를 읽지 않는다 (지연 로딩 — 골든 바이트 동일) |
| TS-132 | U-2 (3) tie-break | 기능 테스트 | 사전 등재 순서(`index`)가 문서 등장 순서이며 표 2개에 걸쳐 연속 번호다 |

---

### F-012: `code-scan init` 서브명령

#### 3.12.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 도구 | `main()` 게이트 **앞**에 `init` 분기(`:2357-2362`) / `cmdInit`·`inferProjectScopes`·`readProjectStructureTable`·`detectExtensions` 신설 / `parseMdTable` 공용 추출 / `commands`에 `init` 등재 / `USAGE`에 `init` 절 / **U-5 (D)·080 에러의 `fix` 문구 보강** | `code-scan.js:2351-2370`·`:1555-1582`·`:296-309` |
| 2 | `opal/core/references/pm/code-scan-management.md` | 문서 | `init` 등재 + 추론 소스 규약 표에 `shardPolicy` 행 + 변경이력 (F-009와 같은 Step) | §3.9.2 (F) |

#### 3.12.2 설계

##### (A) CLI 계약 — **도구는 절대 묻지 않는다**

```
code-scan init --header-source <inline|manifest> [--write] [--force] [--json]
```

| 항목 | 결정 | 근거 |
|------|------|------|
| `--header-source` | **필수**. 없으면 추론하지 않고 exit 1 `init_header_source_required` | [MUST] `pm/code-scan-management.md:21`: "`headerSource` \| **추론 금지** \| PM이 소유자에게 2택을 확인해 확정한다." + `:87`: "도구는 이 질문을 하지 않는다 — 비대화형을 유지한다." 2택은 추측 대상이 아니다(080 원칙 계승) |
| 값 검증 | **`resolveHeaderSource`를 재사용**한다 — `resolveHeaderSource({headerSource:null, configError:null}, opts)`를 호출해 CLI 분기(`code-scan.js:279-288`)만 타게 한다 | 값 도메인 판정 1곳 봉인(제약 ③). 구형 값 `auto`의 마이그레이션 안내(`:311-314`)까지 공짜로 계승된다. **재검증 로직을 새로 쓰지 않는다** |
| 대화형 | **없음**. TTY 감지·`readline`·프롬프트를 만들지 않는다 | 소비 경로 3종(PM·워커·hook)이 전부 TTY 없이 동작해야 한다(§2.12.3) |
| `--write` | 없으면 stdout 초안 출력(**쓰기 0건**), 있으면 파일 기록 | `--dry-run`의 반대 방향 기본값 — **기본이 안전** |
| `--force` | 기존 파일이 있을 때만 의미. `--write`와 함께여야 한다 | 복구 창구 |
| `--json` | 기존 `opts.output === 'json'` 재사용 | 신규 플래그 0개 |

##### (B) **게이트 예외 — 가장 중요한 설계 지점** (H-22)

```js
// main() — code-scan.js:2354 이후
if (opts.command === 'help')    { console.log(USAGE); return; }
if (opts.command === 'version') { console.log(`code-scan v${VERSION}`); return; }

const projectRoot = findProjectRoot();
const config = loadConfig(projectRoot);

// ── init 게이트 예외 (083 F-012) ───────────────────────────────────────
// [MUST] init은 headerSource가 **없는 상태를 고치는** 명령이다. 전 명령 차단 게이트
// (:2362-2367) 뒤에 두면 "설정이 없어서 init이 거부되고, init을 못 돌려 설정을 못 만드는"
// 순환이 생겨 기능이 통째로 무용지물이 된다 (H-22).
// 게이트를 무력화하는 것이 아니라, **게이트가 요구하는 값을 CLI 인자로 직접 받는다**.
if (opts.command === 'init') { return cmdInit(projectRoot, config, opts); }
// ──────────────────────────────────────────────────────────────────────

const hs = resolveHeaderSource(config, opts);   // 기존 게이트 — 나머지 12 명령 불변
if (!hs.ok) { … }
```

- **차단 정책은 조금도 완화되지 않는다** — `init` 외 모든 명령의 게이트 동작이 바이트 단위로 불변이다. `init`은 게이트가 검사하는 바로 그 값을 **인자로 강제**하므로 우회가 아니다.
- `cmdInit`은 **깨진 config에서도 동작해야 한다**(복구 창구). `config.configError`가 무엇이든 참조하지 않으며, 디렉토리 스캔 필터에 쓰는 `exclude`는 `config.exclude`가 아니라 **규약 고정 목록**을 쓴다(§(C) 대조표 3행).

##### (C) 추론 규약 1:1 대조표 — **규약 SSOT ↔ 083 구현**

| 규약 항목 | 규약 원문 위치 | 083 구현 | 일치 |
|----------|--------------|---------|------|
| `scopes` 추론 소스 | `:18` "`docs/PROJECT.md §프로젝트 구성` 표의 요소·경로 컬럼" | `readProjectStructureTable` — `## 프로젝트 구성` 아래 첫 표에서 **헤더 이름으로** `요소`·`경로` 컬럼 인덱스 획득 | ✅ |
| `scopes` 폴백 | `:18` "부재 시 프로젝트 루트 1-depth 디렉토리 스캔으로 대체" | `inferScopes`의 디렉토리 스캔 경로(`code-scan.js:1571-1582`) **재사용** | ✅ |
| `extensions` | `:19` "프로젝트에 실재하는 코드 확장자 자동 감지" | `detectExtensions` — 스코프 루트를 순회해 실재 확장자 수집, 알려진 목록(`DEFAULT_CONFIG.extensions` ∪ `.md`)과 교집합 | ✅ |
| `extensions` `.md` | `:19` "`.md` **기본 포함** — brain·문서 @header 자산화 목적" | 감지 결과와 무관하게 **항상 포함** | ✅ |
| `exclude` | `:20` 기본값 6종 + "`backup`, `.pytest_cache`, `.next`, `.nuxt`, `tests` 등 보강" / `:30` 예시 10종 | **`:30` 예시 목록을 그대로** 고정 출력: `node_modules, __pycache__, .git, dist, build, .venv, backup, .pytest_cache, .next, .nuxt` | ⚠️ **부분** — 아래 (D) |
| `headerSource` | `:21` "추론 금지" | 추론 0건. CLI 인자 필수 | ✅ |
| `headerSource` 확인 주체 | `:21` "확인 전에는 파일을 생성하지 않는다" | 인자 없으면 **파일을 만들지 않고** exit 1 | ✅ |
| 비대화형 | `:87` "도구는 이 질문을 하지 않는다" | 프롬프트·TTY 의존 0건 | ✅ |
| `excludePatterns` | `:31` 예시 `[]` | `[]` 고정 | ✅ |
| 키 순서 | `:26-32` 예시 순서 | `headerSource` → `scopes` → `extensions` → `exclude` → `excludePatterns` **동일 순서** | ✅ |
| `scopes` 값 형식 | `:35` "문자열 축약형 또는 객체형 두 형식" | **문자열 축약형**으로 출력(예시와 동일). 객체형은 소유자가 필요 시 승격 | ✅ |
| 생성 보고 | `:44-46` `📂 code-scan.json 자동 생성: headerSource={값} · scopes={N}종 · extensions=[...] · exclude=[...]` | **동일 문구**를 stderr로 1줄 | ✅ |
| `shardPolicy` | 규약에 **행 없음** (083 신설 키) | **초안에 넣지 않는다** — 아래 (E) | ➕ 규약 표에 행 추가 (§3.9.2 (F)) |

##### (D) 규약 이탈 1건 — `exclude` 목록 (사유 명시)

규약 안에서 두 곳이 이미 다르고, 코드의 기존 기본값과도 다르다:

| 출처 | 목록 |
|------|------|
| 규약 표 `:20` | `node_modules`, `__pycache__`, `.git`, `dist`, `build`, `.venv` + "`backup`, `.pytest_cache`, `.next`, `.nuxt`, **`tests`** 등 보강" |
| 규약 예시 `:30` | 위 10종 (**`tests` 없음**) |
| 코드 `DEFAULT_CONFIG` (`code-scan.js:43`) | `node_modules`, `__pycache__`, `.git`, `dist`, `build`, `.venv`, **`env`**, `.next`, `.nuxt`, **`.output`** (`backup`·`.pytest_cache` 없음) |

**채택**: **규약 예시 `:30` 목록을 그대로** 쓴다.
**사유**: ① 예시는 "생성되는 산출물"의 구체 명세이므로 표의 서술("등 보강")보다 구속력이 크다. ② `tests`를 넣으면 **테스트 코드가 스캔에서 통째로 빠져** 커버리지 판정이 왜곡된다 — 이 저장소의 실제 설정도 `tests`를 넣지 않았다. ③ 코드 `DEFAULT_CONFIG`와의 차이(`env`·`.output` 누락)는 **`init`이 만드는 것은 초안이고 `DEFAULT_CONFIG`는 설정 부재 시 폴백**이라 역할이 달라 일치시킬 필요가 없다. **이 3항을 §3.9.2 (F)에서 규약 문서에 반영해 표와 예시의 불일치를 해소한다.**

##### (E) `shardPolicy`를 초안에 넣지 않는 이유 (지시 명시 요구)

- 083 F-001의 정책 해석은 **3단 폴백**(`code-scan.json` > `~/.opal/setting.json` > 코드 상수)이다(§3.1.2 (E)).
- `init`이 `shardPolicy`를 초안에 써 넣으면 **1순위가 항상 채워져** 2·3단이 영원히 도달 불가가 된다 — 전역 설정(F-010 시드)과 코드 상수가 무력화되고, 기본값을 중앙에서 조정할 수 없게 된다.
- 따라서 `init` 산출물에 `shardPolicy` 키는 **존재하지 않는다**. 프로젝트가 값을 덮어써야 할 때만 소유자가 추가한다.
- 규약 표에는 이 사실을 **명시적 행으로** 추가한다(§3.9.2 (F)) — "행이 없어서 안 쓴 것"과 "안 쓰기로 정한 것"을 구분하기 위함이다.

##### (F) 쓰기 3분기 + 백업 (H-21)

| 파일 상태 | `--write` 없음 | `--write` | `--write --force` |
|----------|--------------|-----------|------------------|
| **없음** | stdout 초안, 쓰기 0건, exit 0 | 생성 + 보고 1줄, exit 0 | 생성 (force 무해), exit 0 |
| **있음** | stdout 초안, 쓰기 0건, exit 0 | **exit 1 `config_exists`** | `.opal/code-scan.json.bak` 백업 후 덮어쓰기 + 보고 1줄, exit 0 |

```js
// 기존 파일 보호 — cmdDiscover의 index_exists 관용 계승 (code-scan.js:1637-1639)
if (fs.existsSync(cfgPath) && !opts.force) {
  return errorExit('config_exists', {
    detail: '.opal/code-scan.json이 이미 존재합니다',
    where: 'config',
    fix: '덮어쓰려면 --force를 함께 주세요: code-scan init --header-source <inline|manifest> --write --force ' +
         '(기존 파일은 .opal/code-scan.json.bak으로 백업됩니다)',
  });
}
// --force 경로: 1세대 백업 후 덮어쓴다 (H-21)
if (fs.existsSync(cfgPath)) fs.copyFileSync(cfgPath, cfgPath + '.bak');
fs.writeFileSync(cfgPath, JSON.stringify(draft, null, 2) + '\n');
```

- `.bak` 확장자는 `.json`이 아니므로 도구의 어떤 열거에도 잡히지 않는다(`listManifestFiles`는 `.json`만 수집, `code-scan.js:1780`).
- **1세대만** 보관한다 — 세대 관리는 git의 몫이며, 백업 파일이 쌓이면 그 자체가 잡음이다.
- **자동 복구·자동 재실행은 만들지 않는다** — `init`은 소유자/PM이 명시적으로 부르는 명령이다.

##### (G) 산출 초안 형태 (규약 `:25-33` 예시와 동형)

```json
{
  "headerSource": "inline",
  "scopes": { "framework": "opal/", "console-fe": "dashboard/frontend/", "console-be": "dashboard/backend/" },
  "extensions": [".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte", ".kt", ".kts", ".java", ".swift", ".md"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv", "backup", ".pytest_cache", ".next", ".nuxt"],
  "excludePatterns": []
}
```

- 스코프 이름은 `요소` 컬럼을 **kebab 소문자**로 변환한다(`Console FE` → `console-fe`). 이 저장소에서 이 규칙을 적용하면 실제 파일의 3종 이름과 **정확히 일치**한다(§2.12.3) — 추론 정확도의 실측 기준선이다.
- `경로` 컬럼 값은 백틱을 벗기고 **첫 경로만** 채택하며, 끝에 `/`를 보정한다.
- `--json` 시 `{ok:true, command:'init', written:<bool>, path, backup, draft:{…}}` 형태로 stdout에 낸다. `--json`이 아니면 초안 JSON을 그대로 stdout에 낸다(파이프 친화).

##### (H) 공용 md 표 파서 추출 — 중복 신설 금지

F-011의 `parseWordDictionary`(§3.10.2 (B))와 F-012의 `readProjectStructureTable`이 **같은 일**을 한다 — "md에서 표를 찾아 **헤더 이름으로** 컬럼 인덱스를 얻고 행을 뽑는다".

```js
/**
 * md 본문에서 required 헤더를 **모두** 가진 표를 찾아 행을 뽑는다. 위치를 가정하지 않는다.
 * F-011(표준단어사전)·F-012(PROJECT.md 프로젝트 구성)가 공유한다.
 * @param {string} md
 * @param {string[]} requiredHeaders  예: ['한글','영문','약어'] / ['요소','경로']
 * @returns {Array<{cells:Object<string,string|null>, index:number}>}  매칭 표가 없으면 []
 */
function parseMdTable(md, requiredHeaders) { … }
```

- [MUST] `opal/core/PRINCIPLES.md` §2: "Remove a duplicated existing pattern before introducing a new one." (`code-scan.js:343` 인용) → 두 번째 md 표 파서를 만들지 않고 **첫 번째를 공용화**한다.
- `parseWordDictionary`는 `parseMdTable(md, ['한글','영문','약어'])`의 얇은 래퍼가 되고, 사전 고유 규칙(`en`/`abbr` 중 1개 이상 필수, `index` 연속 부여)만 남긴다.
- 이 추출은 **Step 6a에서 수행**한다(F-012 구현 시점). Step 6b의 `parseWordDictionary`는 이미 존재하는 `parseMdTable`을 소비하므로 **6a → 6b 순차 의존**이 성립한다(§4.3).

##### (I) `fix` 문구 보강 — 복구 경로 제시 ((a) 요구)

**차단 동작은 불변**이며 안내 문구만 보강한다.

| 대상 | 위치 | 추가되는 문구 |
|------|------|-------------|
| `code_scan_config_invalid` (`shardPolicy` 타입 위반) | §3.1.2 (D) `main()` 게이트 | 기존 fix + ` 설정을 새로 만들려면: code-scan init --header-source <inline\|manifest> --write --force` |
| `code_scan_config_invalid` (`scopes` 위반) | `code-scan.js:2374-2379` | 동일 문구 추가 |
| `header_source_unset` | `code-scan.js:296-299` | 기존 fix + ` 또는 code-scan init --header-source <inline\|manifest> --write 로 설정 파일을 생성하세요` |
| `header_source_invalid` | `code-scan.js:303-315` | 동일 문구 추가 (구형 값 `auto` 마이그레이션 안내는 **유지**) |

- **자동 복구·자동 재실행은 만들지 않는다** — 도구는 명령 문자열을 제시할 뿐이고 실행은 사람/PM의 몫이다. U-3(유도 진입점)에서 채택한 원칙과 같다.

##### (J) 범위 제외 — 전역 설정 시드 ((c) 요구)

**`~/.opal/setting.json` 시드는 F-010(`install-mac.sh`)이 단일 창구이며, `init`은 프로젝트 설정(`.opal/code-scan.json`)만 다룬다.** 시드 주체가 2개가 되면 "어느 쪽이 만든 값인가"를 추적해야 하고 두 경로의 기본값이 갈릴 수 있다 — 확정 방향 #7-b가 프로젝트 설정 소스를 1개로 못 박은 것과 같은 이유다.

#### 3.12.3 환경 변경
해당 없음 (신규 패키지 0개, 신규 CLI 플래그는 `--write`·`--force` 2개).

#### 3.12.4 배치/마이그레이션
해당 없음. **기존 프로젝트의 `.opal/code-scan.json`을 자동으로 손대지 않는다** — `--write --force`를 명시적으로 줄 때만 덮어쓴다.

#### 3.12.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-140 | H-22 (게이트 예외) | 기능 테스트 | `.opal/code-scan.json`이 **없는** 트리에서 `init --header-source inline`이 **exit 0**으로 초안을 낸다 (`header_source_unset` 차단에 걸리지 않는다) |
| TS-141 | H-22 (복구) | 기능 테스트 | `.opal/code-scan.json`이 **깨진 JSON**인 트리에서도 `init --header-source inline --write --force`가 exit 0으로 복구한다 |
| TS-142 | 비대화형 | 기능 테스트 | stdin을 닫고(TTY 없음) 실행해도 정상 동작하며 프롬프트를 출력하지 않는다 |
| TS-143 | 규약 `:21` | 기능 테스트 | `--header-source` **누락** 시 exit 1 `init_header_source_required` + **파일을 만들지 않는다** |
| TS-144 | 규약 `:21` | 기능 테스트 | `--header-source auto`(구형 값)는 exit 1 `header_source_invalid` + 마이그레이션 안내가 실린다 (`resolveHeaderSource` 재사용 증명) |
| TS-145 | 쓰기 3분기 ① | 기능 테스트 | 파일 없음 + `--write` 없음 → stdout 초안 + **쓰기 0건**(디렉토리 바이트 동일) |
| TS-146 | 쓰기 3분기 ② | 기능 테스트 | 파일 있음 + `--write`(force 없음) → exit 1 `config_exists` + **기존 파일 바이트 동일** |
| TS-147 | 쓰기 3분기 ③ / H-21 | 기능 테스트 | 파일 있음 + `--write --force` → 덮어쓰기 + `.opal/code-scan.json.bak`이 **원본과 바이트 동일** |
| TS-148 | 규약 (C) `scopes` | 기능 테스트 | `docs/PROJECT.md §프로젝트 구성` 표가 있으면 `요소`→kebab, `경로`→첫 값으로 `scopes`가 추론된다 |
| TS-149 | 규약 (C) 폴백 | 기능 테스트 | 표가 없으면 루트 1-depth 디렉토리 스캔으로 대체된다 |
| TS-150 | 규약 (C) `extensions` | 기능 테스트 | 실재 확장자만 감지되고 `.md`는 **항상** 포함된다 |
| TS-151 | 규약 (C) `exclude`·키 순서 | 산출물 검사 | `exclude`가 규약 예시 10종과 **정확히 일치**하고, 키 순서가 `headerSource`→`scopes`→`extensions`→`exclude`→`excludePatterns`다 |
| TS-152 | (E) `shardPolicy` 제외 | 산출물 검사 | 초안에 `shardPolicy` 키가 **존재하지 않는다** (3단 폴백 보존) |
| TS-153 | 규약 `:44-46` | 기능 테스트 | 생성 직후 **stderr**에 `📂 code-scan.json 자동 생성: headerSource=… · scopes=…종 · …` 1줄, stdout JSON 무오염 |
| TS-154 | H-20 (규약 재현) | 통합 테스트 | **이 저장소**에서 `init`을 돌리면 `scopes` 이름 3종이 실제 `.opal/code-scan.json`과 일치한다(`framework`·`console-fe`·`console-be`) |
| TS-155 | (I) `fix` 보강 | 기능 테스트 | `header_source_unset`·`header_source_invalid`·`code_scan_config_invalid` 3종의 `fix`에 `init` 복구 명령이 포함된다 |
| TS-156 | (H) 중복 제거 | 산출물 검사 | md 표 파싱 구현이 `parseMdTable` **1곳**이고 `parseWordDictionary`가 그것을 소비한다 |
| TS-157 | (J) 범위 제외 | 기능 테스트 | `init` 실행 전후 `{OPAL_HOME}/setting.json` 바이트가 동일하다 (전역 설정 비접촉) |
| TS-158 | 회귀 | 회귀 테스트 | `init` 추가 후에도 나머지 13 명령의 게이트 동작이 불변이다 (`header_source_unset` 차단 유지) |
| TS-160 | F-8 AC / §3.9.2 (F) | 산출물 검사 | `opal/core/references/pm/code-scan-management.md`에 `init` 등재 + 규약 표 `shardPolicy` 행 + `exclude` 표↔예시 불일치 해소(`tests` 제거) + 변경이력 v1.5 행(일시 KST + `(083)`)이 존재한다. **`~/.opal/references/…`는 수정되지 않았다**(배포 경계) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 (픽스처) | F-008 | 1, 2, 3, 4 | opal-task-agent | **병렬 가능** | 비중첩 파일 집합. 코드 변경 전 선행 |
| 2 (RED) | F-008 | 5 | opal-test-agent (mode:red) | 순차 | Phase 1 완료 후. 구현 전 전량 RED |
| 3 (구현 1/2) | F-001, F-002, F-003, F-007, **F-012** | **6a** | opal-task-agent | 순차 | 설정·정책·`init` 계열. 편집 지점 (a)~(g) |
| 4 (구현 2/2) | F-004, F-005, F-006, F-011, F-009(코드) | **6b** | opal-task-agent | **엄격 순차** | 사전·사다리·`split` 계열. 편집 지점 (h)~(l). **6a 완료 확인 후에만 디스패치 — 동시 편집 0** |
| 5 (테스트 이전) | F-007, F-008 | 7 | opal-task-agent | 순차 | Step 6b 완료 후. 082 단언 주소 이전 |
| 6 (배포) | F-010 | 8 | opal-task-agent | 순차 | Step 6a와 독립 파일이나 정책 키 확정 후 |
| 7 (문서) | F-009, F-012 | 9 | opal-task-agent | 순차 | 코드·배포 확정 후. **규약 문서 포함 3파일** |
| 8 (docs/) | F-009 | 10 | opal-task-agent | 순차 | Step 9 완료 후 (PM Gate 정정 — 디스패치 의무) |
| 9 (검증) | 전 기능 | 11 | opal-test-agent | 순차 | 전량 GREEN + 골든 바이트 diff 0 |

### 4.2 실행 체크리스트

> 총 **12개** Step | Phase **9개** | 실행 모드: **복잡**
>
> **산출 파일 계수(합집합, 같은 경로는 1개)**: Step 1 = 4파일 / Step 2 = 6파일 / Step 3 = 6파일 / Step 4 = 14파일 / Step 5 = 1파일 / **Step 6a = 1파일** / **Step 6b = 1파일(6a와 동일 경로)** / Step 7 = 1파일 / Step 8 = 2파일 / Step 9 = **3파일** / Step 10 = 2파일 / Step 11 = 0파일(검증).
>
> PM Gate 정정(083): Step 6 계수를 6파일 → 1파일로 교정했다. 해당 Step의 `**파일**` 항목은 `tests/test-shard.js` 단일 파일이며, 6은 Step 2 계수와 중복 기재된 오기였다. **U-2 개정으로 Step 번호가 밀려 이 Step은 현재 Step 7이다** — 계수 1파일은 그대로 유효하다.
>
> **U-2 개정 반영(083)**: 구 Step 3(신규 픽스처 9파일 산출)이 중단 관측 임계(10파일)에 근접하여 **비중첩 2 Step(Step 3·Step 4)으로 분할**했다. 이후 Step 번호가 각각 +1 밀렸다(구 4~10 → 신 5~11).
>
> **F-012 개정 반영(083, 2026-08-04)**: `init` 신설로 `code-scan.js` 편집 지점이 12개 → **13개**가 되어, 구 Step 6을 **6a(설정·정책 계열) → 6b(사다리·분할 계열) 엄격 순차 2 Step으로 분할**했다. Step 번호는 **밀지 않았다**(6a/6b 접미) — Step 7~11의 기존 번호와 PM 정정 기록을 보존하기 위함이다. Step 9는 규약 문서 1개가 추가되어 2 → 3파일이다.
>
> **분할 규칙 적용 근거**: (i) `code-scan.js`를 만지는 작업은 여전히 **동시 편집을 하지 않는다** — 6a 완료 후에만 6b를 디스패치하는 **엄격 순차**이므로 후행 저장이 선행 편집을 덮어쓸 수 없다(상세 근거는 §4.3). (ii) 픽스처 편집은 3개 초과이나 파일당 1~3줄의 JSON 키 추가·제거이므로 **비중첩 4 Step으로 분할**해 디스패치당 산출량을 억제한다. (iii) Step 7은 `test-shard.js` 1파일 + 픽스처가 아닌 단언 이전이므로 단독이다.
>
> **Step 4가 14파일인데도 더 쪼개지 않는 사유**: 14파일 중 **10개가 1줄짜리 동일 템플릿 소스 스텁**(`.ts`)이라 실 산출 토큰은 설정 파일 3~4개 수준이다. 그리고 매니페스트(`svc/mod.json`)와 소스 스텁이 **서로 다른 Step에 갈라지면 `validate` 구조 패스가 `orphan:file_missing`/`files_key_removed`를 내어 중간 상태가 검증 불가**해진다(`code-scan.js:2243-2254`). 파일 수보다 정합 단위를 우선한다.

#### Step 1: `shard-violations` 오버사이즈 계열 픽스처 정책 이전
- [ ] 완료
- **소속 기능**: F-008 (H-1·H-2 흡수)
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일**:
  - `opal/tools/code-scan/tests/fixtures/shard-violations/oversize/.opal/code-scan.json`
  - `opal/tools/code-scan/tests/fixtures/shard-violations/oversize/.opal/code-map/index.json`
  - `opal/tools/code-scan/tests/fixtures/shard-violations/oversize-shard/.opal/code-scan.json`
  - `opal/tools/code-scan/tests/fixtures/shard-violations/oversize-shard/.opal/code-map/index.json`
- **작업 내용**: 각 `code-scan.json` 최상위에 `"shardPolicy": { "maxBytes": 200, "minFiles": 1 }`를 추가하고(§3.8.2 (A)), 각 `index.json`에서 `"manifestMaxBytes": 200` 행을 **제거**한다(§3.7.2 (C) — 남기면 폐기 안내 stderr가 S-17 대조군 단언을 깨뜨린다). `note` 필드에 "(task 083 정책 이전)"을 덧붙인다. 다른 키는 손대지 않는다.
- **완료 기준**: 4파일이 JSON 파싱되고, `code-scan.json`에 `shardPolicy` 2키가 존재하며 `index.json`에 `manifestMaxBytes`가 0회 등장한다. `headerSource` 키는 무변경(`tests/test-regression.js:557-569` TS-063 보호).
- **테스트**: TS-085 (사전) / 이 Step 단독으로는 `test-shard.js`가 RED가 된다 — Step 5·6 완료 후 GREEN
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: `shard-goal` 목표달성 픽스처 정책 이전
- [ ] 완료
- **소속 기능**: F-008 (H-1·H-2 흡수)
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일**:
  - `.../fixtures/shard-goal/before/.opal/code-scan.json` + `.../before/.opal/code-map/index.json`
  - `.../fixtures/shard-goal/mid-undeclared/.opal/code-scan.json` + `.../mid-undeclared/.opal/code-map/index.json`
  - `.../fixtures/shard-goal/mid-duplicate/.opal/code-scan.json` + `.../mid-duplicate/.opal/code-map/index.json`
  (경로 접두: `opal/tools/code-scan/tests/`)
- **작업 내용**: 각 `code-scan.json`에 `"shardPolicy": { "maxBytes": 400, "minFiles": 1 }` 추가, 각 `index.json`에서 `"manifestMaxBytes": 400` 제거. 값 400은 082가 이 픽스처군에 쓴 상한을 그대로 계승한다(`tests/test-shard.js:164` 주석의 "manifestMaxBytes:400 아래에서" 전제 보존).
- **완료 기준**: 6파일 JSON 파싱 정상 + `shardPolicy` 존재 + `manifestMaxBytes` 0회. `deriveAfterTree`(`tests/test-shard.js:169-192`)의 전제(파일당 샤드로 나눠야 400 이하)가 유지된다.
- **테스트**: TS-085 (사전)
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 병렬 — 파일 집합 비중첩)

#### Step 3: 083 신규 픽스처 (A) 정책·전역설정 계열
- [ ] 완료
- **소속 기능**: F-008 (F-001·F-002·F-003·F-007 사전 조건)
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일** (6파일, `opal/tools/code-scan/tests/fixtures/shard-policy/` 하위 신규):
  - `base/.opal/code-scan.json` · `base/.opal/code-map/index.json` · `base/.opal/code-map/svc/mod.json` · `base/svc/mod/{A,B,C,D}.ts`를 담은 **단일 트리 1개** (엔트리 4건) — 실제 파일 수는 트리 내 7개이나 **산출 단위는 픽스처 1종**
  - `homes/absent/.gitkeep` · `homes/valid/setting.json` · `homes/broken/setting.json`(깨진 JSON) · `homes/nokey/setting.json`(`bootstrap`+`models`만) · `homes/badtype/setting.json`(`shardPolicy.maxBytes: "big"`) — 5파일
- **작업 내용**: `base/`는 `codemap-repo`·`shard-repo` 구조를 참조해 만들고 `.opal/code-scan.json`에 `headerSource: "manifest"`를 **필수** 명시한다(TS-063 보호). **2축 변형(`axis-bytes-only`/`axis-both`)·우선순위 변형(`precedence`)·구 위치 변형(`legacy-index`)은 별도 트리로 수작성하지 않고 테스트가 `base/`를 복사해 설정 1~2줄만 바꿔 파생한다** — 082 `deriveAfterTree`(`tests/test-shard.js:169-192`, 게이트 gaps G-3 "수작성 2벌 금지")의 직접 계승이다. `homes/*`는 code-map 없이 `setting.json` 1파일만 둔다.
- **완료 기준**: `base/`에서 `node opal/tools/code-scan/code-scan.js validate --json`이 스키마 오류 없이 실행된다(위반 유무 무관). `homes/valid`·`homes/nokey`·`homes/badtype`이 JSON 파싱되고 `homes/broken`은 파싱 실패한다(의도된 상태). `homes/absent`는 `setting.json`이 없다.
- **테스트**: TS-001~TS-016, TS-020~TS-024, TS-070~TS-073의 사전 조건
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1·2·4와 병렬)

#### Step 4: 083 신규 픽스처 (B) 분할 대상 + 사다리·사전 계열
- [ ] 완료
- **소속 기능**: F-008 (F-004·F-005·F-011 사전 조건)
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일** (14파일, `opal/tools/code-scan/tests/fixtures/shard-policy/split-target/` 단일 트리):
  - `.opal/code-scan.json` · `.opal/code-map/index.json` · `.opal/code-map/svc/mod.json` (3)
  - `svc/mod/*.ts` **10건** — 사다리 5단계가 각각 최소 1그룹씩 만들 수 있는 이름 구성 (아래)
  - `200.설계/210.사전/표준단어사전.md` **1건** — 정상 사전(수식어 표 + 분류어 표 **둘 다** 포함, H-15 검증용)
- **작업 내용**:
  - 소스 이름은 사다리 각 단계가 실제로 걸리도록 구성한다 — 예: S1용 `OrderRepository.ts`·`OrderService.ts`(첫 토큰 `order`가 사전 등재) / S2용 `TaxRuleAlpha.ts`·`TaxRuleBeta.ts`(첫 토큰만으로는 미달, 2토큰 결합으로 매칭) / S3용 `LegacyOrderTable.ts`·`TempOrderView.ts`(중간 토큰 매칭) / S4용 `AlphaHandler.ts`·`BetaHandler.ts`·`GammaHandler.ts`(마지막 토큰 3건) / S5용 `depends` 공유 3건 / `unassigned`용 1건뿐인 토큰 1~2건.
  - 매니페스트 엔트리에 `depends` 값을 채운다(S5 입력, `code-scan.js:62` `WORKER_FIELDS`).
  - 사전 md는 `opal/skills/op-data-dictionary/SKILL.md:74-90` 형식을 그대로 따른다 — `## 수식어`(6열)와 `## 분류어`(5열) **두 표를 모두** 넣어 위치 기반 파서가 실패하도록 만든다(H-15 RED 신호).
  - **깨진 사전·사전 없음 2변형은 픽스처로 수작성하지 않는다** — 테스트가 `copyFixture` 후 사전 md를 지우거나(사전 없음) 표를 훼손해(깨진 표) 파생한다(082 G-3 계승). 이로써 사전 3분기가 전부 검증되면서 산출 파일은 1종에 머문다.
- **완료 기준**: `split-target/`에서 `validate`가 `orphan`·`files_key_removed` 0건(매니페스트 ↔ 디스크 정합)이고, 매니페스트가 정책 기본값(10240)에서 2축 판정에 걸리도록 `shardPolicy`가 명시돼 있다. 사전 md가 두 표를 포함하고 각 표 헤더에 `한글`·`영문`·`약어`가 있다.
- **테스트**: TS-030~TS-039, TS-100~TS-116, TS-120~TS-132, TS-040~TS-054의 사전 조건
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1·2·3과 병렬)

#### Step 5: RED-first 계약 테스트 작성 (`test-shard-policy.js`)
- [ ] 완료
- **소속 기능**: F-008
- **영역**: 테스트
- **agent**: opal-test-agent (mode:red)
- **파일**: `opal/tools/code-scan/tests/test-shard-policy.js` (신규 1파일)
- **작업 내용**: §3.1.5·§3.2.5·§3.3.5·§3.4.5·§3.5.5·§3.6.5·§3.7.5·§3.8.5·§3.9.5·**§3.10.5·§3.12.5**의 TS 전량을 `node:test` + `spawnSync` 블랙박스로 작성한다. 하네스는 `run(cwd, args, input, homeOverride)`에 `OPAL_HOME` 주입을 내장한다(§3.8.2 (B)). `init` 케이스(TS-140~TS-158)는 **설정 파일이 없는/깨진 임시 트리**를 만들어 검증하므로 픽스처를 복사한 뒤 `.opal/code-scan.json`을 지우거나 훼손해 파생한다(082 G-3 계승). 파일 상단에 `@header` + RED-first 경고 블록 + TC↔TS 매핑 표를 `tests/test-shard.js:1-57` 형식으로 기재한다.
- **완료 기준**: 전 케이스가 **RED**(실패 이유가 "미구현"이며 "테스트 자체 오류"가 아님). `--plan`/`split`/`init` 미구현이므로 `Unknown command` 또는 필드 부재로 실패한다.
- **테스트**: 자체
- **실행 방법**: sub-agent
- **의존**: Step 1, 2, 3, 4

#### Step 6a: `code-scan.js` 구현 (1/2) — 설정·정책·`init` 계열
- [ ] 완료
- **소속 기능**: F-001, F-002, F-003, F-007, F-012
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js` (1파일)
- **작업 내용**: 아래 (a)~(g)를 **이 순서대로 순차 편집**한다. **Step 6b는 6a 완료 후에만 디스패치된다 — 동시 편집이 발생하지 않는다.**
  - (a) `require('os')` 추가 (`:31` 뒤) — §3.2.2 (A)
  - (b) 상수 블록: `DEFAULT_MANIFEST_MAX_BYTES`(`:70`) 제거 → `DEFAULT_SHARD_POLICY`(3키)·`SHARD_POLICY_SCHEMA`·`SHARD_POLICY_KEYS`·`SHARD_TARGET_RATIO`·`OPAL_HOME_ENV` 신설. **`SHARD_PLAN_MIN_GROUP`은 만들지 않는다**(사다리 `accept`가 대신) — §3.1.2 (A)
  - (c) `DEFAULT_CONFIG`에 `shardPolicy: {}` (`:40-46`) / `normalizeShardPolicy` 신설(키별 타입 분기) / `loadConfig` 반환·`configError` 확장 (`:217-253`) — §3.1.2 (B)(C)
  - (d) `resolveOpalHome`·`loadGlobalSetting` 신설 (`:253` 직후) / `resolveShardPolicy` 신설 + `manifestMaxBytes(ctx)` 제거(`:880-884`) — §3.2.2 (A)(B)·§3.1.2 (E)
  - (e) `loadCodeMap`의 `manifestMaxBytes` 게이트 → `deprecationOnce` 교체 (`:869-876`) / `manifestEntryCount`·`isOversizeManifest`·`recommendedShardCount` 신설 + `checkOversize` 2축화 + 호출 2곳 인자 추가(`:2204`·`:2225`) + `cmdScaffold` 소비 교체(`:1852`·`:1913-1919`) — §3.7.2 (A)·§3.3.2
  - **(f) `init` (F-012)**: `parseMdTable` **공용 추출** + `readProjectStructureTable`·`inferProjectScopes`·`detectExtensions`·`cmdInit` 신설 (`cmdDiscover` 인접) / `parseArgs`에 `--write`·`--force` / `USAGE`에 `init` 절 / `commands`에 `init` 등재 — §3.12.2 (A)(C)(F)(G)(H)
  - **(g) 게이트·`fix` 문구**: `main()`의 **차단 게이트 앞**에 `init` 분기 배치(`:2357-2362`) / `main()` config 게이트 조건 확장(`:2373`) / `header_source_unset`(`:296-299`)·`header_source_invalid`(`:303-315`)·`code_scan_config_invalid` 2곳의 `fix`에 `init` 복구 경로 병기 — §3.12.2 (B)(I)·§3.1.2 (D)
- **완료 기준**:
  - `.opal/code-scan.json`이 **없는** 임시 트리에서 `node …/code-scan.js init --header-source inline`이 **exit 0**으로 초안을 낸다 (H-22 해소 확인 — 이것이 6a의 핵심 게이트).
  - `init` 3분기(파일 없음 / 있음+force 없음 / 있음+force)가 §3.12.2 (F) 표대로 동작하고 `.bak`이 생성된다.
  - `manifestMaxBytes(` 함수 정의 0회, `DEFAULT_SHARD_POLICY`가 상수 선언 + `resolveShardPolicy` 본문 밖 0회.
  - **나머지 13 명령의 게이트 동작 불변** — 기존 11 테스트 스크립트 중 `test-shard.js`를 제외한 10종 GREEN.
- **테스트**: TS-001~TS-016, TS-020~TS-026, TS-070~TS-073, TS-075, TS-140~TS-158
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 6b: `code-scan.js` 구현 (2/2) — 사전·사다리·`split` 계열
- [ ] 완료
- **소속 기능**: F-004, F-005, F-006, F-011, F-009(코드 부분)
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js` (1파일 — **6a와 동일 경로, 엄격 순차**)
- **작업 내용**: 아래 (h)~(l)을 **이 순서대로 순차 편집**한다.
  - **(h) 사전 로더 (F-011)**: `DICT_FILENAME`·`DICT_DEFAULT_RELS`·`DICT_MAX_BYTES` 상수 + `readDesignRootFromProjectMd`·`resolveDictPath`·`loadWordDictionary` 신설 (`loadGlobalSetting` 인접). `parseWordDictionary`는 **6a가 만든 `parseMdTable`을 소비하는 얇은 래퍼**로 작성한다 — §3.10.2 (A)(B)(C)·§3.12.2 (H)
  - **(i) 사다리 엔진 (F-004)**: `SHARD_PLAN_LADDER` 상수 + `entryBytes`·`splitTokens`·`dictMatchSpan`·`stageKeyFor`·`planShardGroups` 신설 — §3.4.2 (C)
  - **(j) `split` 집행 (F-005)**: `resolveSplitTarget`·`parseGroupsDoc`·`composeSplitPlan`·`commitSplit`·`cmdSplit`(plan/groups 2모드) 신설 (`cmdScaffold` 뒤) / `parseArgs`에 `--groups`·`--plan`·`--trace`·`--stop-after` + `opts.discoverOut` → `opts.out` 개명(`:164`·`:178`·`:1634`) / `USAGE`에 `split` 절 / `commands`에 `split: cmdSplit` — §3.4.2 (A)(D)·§3.5.2
  - **(k) 유도 페이로드 (F-006)**: `checkOversize` 위반에 `entries`·`minFiles`·`recommendedShards`·`next` 4필드 + `cmdScaffold` stderr 문구에 명령 병기 — §3.6.2 (A)
  - (l) `VERSION` → `'1.6.0'`(`:37`) / 상단 `@header` description·note 갱신(`:2-11`) / 하단 변경이력 v1.6.0 행 추가(`:2474` 뒤, 일시 KST + `(083)`) — §3.9.2 (A)
- **완료 기준**:
  - **[MUST] 6a가 만든 함수를 재정의하지 않는다** — `resolveShardPolicy`·`loadGlobalSetting`·`resolveOpalHome`·`normalizeShardPolicy`·`cmdInit`·`parseMdTable`·`isOversizeManifest`·`manifestEntryCount`·`recommendedShardCount`의 정의가 소스에 **각각 1개**임을 정적 검사로 확인한다. 시그니처 변경도 금지 — 필요하면 blocked로 반환한다.
  - `node …/code-scan.js --help`가 `init`과 `split`을 **둘 다** 표시한다.
  - `test-shard-policy.js` **전량 GREEN**, `test-shard.js` 제외 기존 10 스크립트 GREEN.
  - `loadWordDictionary(` 호출이 `split --plan` 경로 1곳뿐이다(골든 무영향).
- **테스트**: TS-030~TS-039, TS-040~TS-054, TS-060~TS-063, TS-100~TS-116, TS-120~TS-132
- **실행 방법**: sub-agent
- **의존**: **Step 6a (엄격 순차 — 6a 완료 확인 후에만 디스패치)**

#### Step 7: 082 단언 주소 이전 (`test-shard.js`)
- [ ] 완료
- **소속 기능**: F-007, F-008
- **영역**: 테스트
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/tests/test-shard.js` (1파일)
- **작업 내용**: §3.7.2 (C) 매핑 표대로 이전한다 — `setManifestMaxBytes` → `setShardPolicy(dir, patch)`(`.opal/code-scan.json` 기록) 교체 / S-16 (c) 기대 기본값 `20480` → `10240` + 엔트리 수 사전조건 1건 추가 / S-16 (e) `invalid_index` → `code_scan_config_invalid` 이전 + 구 위치 비차단 1건·전역 타입 위반 1건 **추가** / S-17 대조군을 `maxBytes: 999999`로 교체 / S-22에 `shardPolicy` 정규식 1건 추가 / `run()` 하네스에 `OPAL_HOME` 주입. 변경이력 주석에 v1.1 행 추가.
- **완료 기준**: **[MUST] 단언 삭제 0건·`skip`/`todo` 0건·`strictEqual`→느슨한 비교 완화 0건.** 082 시나리오 26종 테스트 함수가 전부 존재하고 전량 GREEN. 이전 후 단언 수가 이전 전보다 **적지 않다**.
- **테스트**: TS-074, TS-085
- **실행 방법**: sub-agent
- **의존**: Step 6b

#### Step 7b: 테스트 `OPAL_HOME` 격리 주입 — **PM 신설(083, 2026-08-04, PLAN 갭 폐쇄)**
- [ ] 완료
- **소속 기능**: F-008 (H-4 격리)
- **영역**: 테스트
- **agent**: opal-task-agent × 3 (비중첩 3배치 병렬)
- **파일** (10파일): `test-discover.js`·`test-feature.js`·`test-header-source.js`·`test-hook.js`(배치1) / `test-regression.js`·`test-resolve-header.js`·`test-scaffold.js`(배치2) / `test-scope-filter.js`·`test-target.js`·`test-validate.js`(배치3)
- **신설 사유**: §3.8.1 항목 5가 `spawnSync` 호출부의 `OPAL_HOME` 주입을 요구하는데 **§4.2 어느 Step에도 배정되지 않았다**(Step 7 워커가 발견·보고). 083부터 code-scan이 `~/.opal/setting.json`을 읽으므로, 미주입 파일은 **개발자 실제 홈이 테스트 결과에 유입**된다 — 로컬 GREEN·CI RED가 되는 H-4 구멍이며 TS-084가 정적 grep으로 판정한다. Step 7은 `test-shard.js` 1파일 한정이라 범위 밖이었다.
- **작업 내용**: 각 파일의 공용 헬퍼(`run()`·`runHook()`) 1곳에 `env: {...process.env, OPAL_HOME: <가짜 홈>}` 주입. 가짜 홈은 `fixtures/shard-policy/homes/absent`(설정 부재 → 코드 상수 폴백 = 결정론적 기준선). 경로는 `path.join` 조립 + 파일 상단 상수. 기존 `env` 값은 보존.
- **완료 기준**: `spawnSync` 사용 12파일 전량 `OPAL_HOME` 주입(실측 확인). 각 파일 GREEN + `assert.` 개수 불변 + `skip`/`todo` 0건.
- **실측 결과(PM 검증)**: 12/12 주입 완료. 배치1 12·9·12·18 GREEN / 배치3 24·13·34 GREEN / 배치2 `test-resolve-header`+`test-scaffold` 36 GREEN. `assert.` 전량 불변(73·96·35·36·44·102·43·21·53·52). `test-regression.js`는 전 스위트 집계(TS-062) 포함이라 Step 11에서 최종 판정.
- **실행 방법**: sub-agent (3배치 병렬 — 파일 집합 비중첩)
- **의존**: Step 6b (전역 로더 구현 완료 후)

#### Step 8: 전역 설정 시드 (`setting.default.json` + `install-mac.sh`)
- [ ] 완료
- **소속 기능**: F-010
- **영역**: 배포
- **agent**: opal-task-agent
- **파일**: `opal/core/setting.default.json` · `scripts/install-mac.sh` (2파일)
- **작업 내용**: §3.9.2 (B)대로 `setting.default.json`에 `shardPolicy`(`_help`+2키) 추가. §3.9.2 (C)대로 `install_opal_setting`(`:918-953`)의 병합 python을 `SEED_KEYS = ['models', 'shardPolicy']` 키 목록 루프로 재작성하고, `|| warn` 문구를 `models` 한정에서 일반 문구로 교체. `install-mac.sh` 상단 버전 주석 이력에 행 추가(`:36-41` 형식).
- **완료 기준**: `python3 -c "import json;json.load(open('opal/core/setting.default.json'))"` 성공 + `shardPolicy.maxBytes == 10240`. 임시 복사한 3형태 `setting.json`에 시드 python을 적용해 기존 값 무손실 + 멱등(2회 바이트 동일)이 확인된다. **[MUST] 실 `~/.opal/setting.json`을 변조하지 않는다** — `cp`로 임시 복사본을 만들어 검증한다.
- **테스트**: TS-093, TS-094, TS-095, TS-096
- **실행 방법**: sub-agent
- **의존**: Step 6a (정책 키 이름·기본값 확정 후 — 6b를 기다릴 필요 없다)

#### Step 9: 참조 문서 갱신 (`tools.md` + `header-rules.md` + 규약 문서)
- [ ] 완료
- **소속 기능**: F-009, F-012
- **영역**: 문서
- **agent**: opal-task-agent
- **파일** (3파일): `opal/core/references/tools.md` · `opal/core/references/harness/header-rules.md` · **`opal/core/references/pm/code-scan-management.md`**
- **작업 내용**: §3.9.2 (D) 7항목대로 `tools.md` code-scan 절(`:202-343`) 갱신 + 말미 변경이력 행. **U-2 개정 반영 2항**: (i) 사다리 S1~S5 표 + "설정 노출은 후속 이관" 명시, (ii) 사전 탐색 3단 + 옵셔널 폴백 3분기(§3.10.2 (C) 표) + `--trace`·`--stop-after` 옵션. **F-012 반영 1항**: `init` 커맨드 + `--write`/`--force`/`--header-source` + 에러 코드 2종(`init_header_source_required`·`config_exists`). §3.9.2 (E)대로 `header-rules.md` §워커 권한 경계에 `split` 집행 1줄 + 변경이력 v1.7 행. **§3.9.2 (F)대로 `pm/code-scan-management.md` 갱신** — `init` 등재 / 규약 표에 `shardPolicy` 행 / `exclude` 표↔예시 불일치 해소(`tests` 제거) / 비대화형 실현 형태 1줄 / 복구 경로 1줄 / 변경이력 v1.5. **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 참조 문서를 변경하면 변경이력 표에 행을 추가한다. 일시(KST)를 포함한다.** **[MUST] 배포 경계 — 3파일 모두 `opal/core/references/…` 소스이며 `~/.opal/references/…`를 직접 편집하지 않는다.** 폐기 안내 절에 `manifestMaxBytes` 문자열을 남겨 082 S-22 정규식을 GREEN 유지한다.
- **완료 기준**: TS-091·TS-092·TS-064·TS-160 GREEN + `tools.md`에 사다리·사전 폴백·`init`이 기재됐다. **3파일 전부** 변경이력에 일시(KST) + `(083)` 행 존재.
- **테스트**: TS-064, TS-091, TS-092, TS-160
- **실행 방법**: sub-agent
- **의존**: Step 6b, 8

#### Step 10: `docs/` 갱신
- [ ] 완료
- **소속 기능**: F-009
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `docs/ARCHITECTURE.md` · `docs/PROJECT.md` (2파일)
- **작업 내용**: code-scan 도구 서술에 (i) 2축 판정, (ii) `split`·`init` 서브명령 2종 추가(13개 → **15개**), (iii) 설정 3단 우선순위 + code-scan이 `~/.opal/setting.json`을 읽는 첫 도구가 된 사실, (iv) **code-scan이 `표준단어사전.md`를 옵셔널 입력으로 참조하게 된 사실**(`op-data-dictionary` 산출물과의 신규 연결, 읽기 전용), (v) **`init`이 `.opal/code-scan.json`을 생성하는 도구 창구가 된 사실**(PM 수작업 → 도구 집행)을 반영한다. 두 파일 모두 워킹트리에 이미 미커밋 변경이 있으므로(`git status` 기준) **기존 변경을 보존한 채 추가 편집**한다.
- **완료 기준**: 두 문서에 `split`·2축·3단 우선순위·사전 연동이 언급되고, 기존 미커밋 변경 내용이 유실되지 않았다.
- **테스트**: 산출물 검사 (PM Gate)
- **실행 방법**: sub-agent
- **의존**: Step 9

> PM Gate 정정(083): 본 Step의 agent를 `PM 직접`에서 `opal-task-agent`로 교체했다. 근거 — [MUST] `~/.opal/references/opal-harness.md` §1 디스패치 의무 원칙: "오케스트레이터 SKILL.md에 워커 디스패치로 정의된 단계(ANALYSIS, PLAN, EXECUTE 등)는 반드시 서브에이전트를 디스패치한다. PM이 임의 판단으로 직접 실행하여 대체하지 않는다." EXECUTE 단계 Step은 허용 예외(TASK 단계 / SKILL.md가 직접 수행으로 명시한 경우)에 해당하지 않는다.

#### Step 11: 전량 검증 + 골든 불변 확인
- [ ] 완료
- **소속 기능**: 전 기능
- **영역**: 테스트
- **agent**: opal-test-agent
- **파일**: 없음 (검증 전용)
- **작업 내용**:
  1. `cd opal/tools/code-scan && node --test tests/test-*.js` — 12 스크립트 전량 실행
     > PM 정정(083, 2026-08-04): 원안 `node --test tests/`(디렉토리 인자)는 **Node v25.8.2에서 동작하지 않는다** — 위치인자를 glob으로 취급해 디렉토리를 모듈로 로드하려 하고 `MODULE_NOT_FOUND`로 죽는다(Step 11 실측). 파일 글로브 `tests/test-*.js`로 교체한다.
  2. `git diff --stat -- opal/tools/code-scan/tests/fixtures/golden/` — **빈 결과**여야 한다
  3. 완료기준 ④ 시나리오 실행: `split-target` 픽스처에서 `--plan --out` → `--groups --dry-run` → `--groups` → `validate` 순으로 처리해 `manifest_oversize` 0건 + 엔트리 총합 동일 입증 (TS-054)
  4. 격리 대조: `homes/valid`와 `homes/absent`를 각각 주입해 정책 미적용 명령 결과 동일 확인 (TS-083)
  5. 봉인 정적 검사 (TS-007·TS-008·TS-075·TS-084)
  6. **사전 3분기 대조** (U-2 (4)): 정상 사전 / 깨진 표 / 사전 없음 각각에서 exit code가 동일하고 사다리만 달라짐을 확인 (TS-114·TS-126·TS-127)
  7. **검토 장치 3종 확인**: `--trace` 합계 정합 · `--stop-after` 중단 · `stage` 필드 일치 (TS-109·TS-110·TS-112)
  8. **`init` 게이트 순환 해소 확인** (H-22): `.opal/code-scan.json`이 없는·깨진 임시 트리 2종에서 `init`이 exit 0 (TS-140·TS-141) + **나머지 13 명령의 게이트 동작 불변** (TS-158)
  9. **`init` 규약 재현 대조** (H-20): **이 저장소**에서 `init --header-source inline`(쓰기 없음)을 돌려 `scopes` 3종이 실제 `.opal/code-scan.json`과 일치함을 확인 (TS-154). **[MUST] `--write`를 주지 않는다** — 실제 프로젝트 설정을 변경하지 않는다
  10. **6a/6b 함수 중복 정적 검사**: `resolveShardPolicy`·`loadGlobalSetting`·`resolveOpalHome`·`normalizeShardPolicy`·`cmdInit`·`parseMdTable`·`isOversizeManifest`·`manifestEntryCount`·`recommendedShardCount` 정의가 **각각 1개**
- **완료 기준**: 전량 GREEN + 골든 바이트 diff 0 + TS-054 입증 + 정적 검사 4건 PASS + 사전 3분기 동일 exit code + **`init` 3분기·게이트 예외 확인** + **함수 중복 0건**. **[MUST] 워커 파괴적 git 명령 금지 — 읽기 전용(`status`/`diff`/`log`/`show`)만 사용하고, 깨끗한 상태 확인은 `cp -R` 임시 복사로 한다.**
- **테스트**: TS-080~TS-085, TS-054, TS-090~TS-097, TS-109·TS-110·TS-112, TS-114·TS-126·TS-127, TS-130·TS-131, **TS-140~TS-158, TS-160**
- **실행 방법**: sub-agent
- **의존**: Step 7, 8, 9, 10

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 ∥ Step 3 ∥ Step 4 | 픽스처 디렉토리가 **비중첩** — `shard-violations/` / `shard-goal/` / `shard-policy/{base,homes}/` / `shard-policy/split-target/`. 공유 파일 0개 |
| **Step 3 ∦ Step 4 분리 기준** | 정책·전역설정 계열(Step 3)과 분할·사전 계열(Step 4)은 **소비하는 기능이 다르고**(F-001~F-003·F-007 vs F-004·F-005·F-011) 디렉토리도 겹치지 않는다. 구 Step 3의 9파일 산출을 6 + 14로 나누되, 정합 단위(매니페스트 ↔ 소스)는 쪼개지 않았다 |
| Step 3·4 → Step 5 | 테스트가 픽스처 경로를 참조하므로 픽스처 선행 |
| Step 5 → Step 6a | RED-first — [MUST] `~/.opal/references/harness/red-first.md` §3: 구현 전 작성, GREEN 루핑 중 테스트 수정 금지 |
| **Step 6a → Step 6b (엄격 순차)** | 아래 "동일 파일 분할 규칙 이탈 근거" 참조 |
| Step 6b → Step 7 | 구현 전에 082 단언을 미리 이전하면 RED 신호가 "미구현"과 "이전 미완"으로 섞여 원인 규명이 불가해진다 |
| Step 6a → Step 8 | 정책 키 이름·기본값이 코드에서 확정된 뒤 시드해야 값이 갈린다. **6b를 기다릴 필요는 없다** — 시드 대상 키(`shardPolicy`)는 6a에서 확정된다 |

#### 동일 파일 분할 규칙 이탈 근거 (F-012 개정, 2026-08-04)

> **[MUST] `opal/core/references/pm/dispatch-process.md:157` Step 6 항목 5 산출량 상한**: "단일 디스패치가 생성·수정하는 **산출 파일이 3개를 초과하면** 파일 집합을 비중첩(non-overlapping)으로 분할하여 별도 디스패치로 배치한다. 반대로 **동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다**(동시 편집 시 후행 저장이 선행 편집을 덮어쓰는 충돌 방지)."

| 항목 | 판단 |
|------|------|
| **규칙의 목적** | 괄호가 조건을 명시한다 — **"동시 편집 시"** 후행 저장이 선행 편집을 덮어쓰는 충돌 방지다. 금지 대상은 "분할" 자체가 아니라 **동시 편집**이며, 규칙 본문("같은 디스패치에 묶어 **순차** 편집")도 요구하는 것이 순차성임을 보여준다 |
| **6a/6b 배치가 목적을 충족하는가** | **충족한다.** 6b는 **6a 완료를 확인한 뒤에만** 디스패치된다(§4.2 Step 6b `의존`). 두 워커가 같은 시점에 파일을 들고 있는 구간이 **존재하지 않으므로** 후행 저장이 덮어쓸 선행 편집이 없다. 6b는 6a가 저장을 끝낸 파일을 새로 읽어 이어 쓴다 |
| **왜 이탈이 필요한가** | ① F-012 신설로 편집 지점이 **12개 → 13개**가 되고 신규 함수가 8개 늘어난다. ② 오늘 워커가 **2회 중단**된 이력이 있어(API 연결 종료) 단일 디스패치 부담이 실측으로 과도하다. ③ 중단 시 손실 범위가 13개 지점 전체에서 **최대 7개 지점**으로 절반이 된다 |
| **경계선을 어디에 그었는가** | **의존 방향이 한 방향인 지점**에서 잘랐다 — 6a(설정·정책·`init`)는 6b를 참조하지 않고, 6b(사전·사다리·`split`)만 6a의 산출(`resolveShardPolicy`·`parseMdTable`)을 소비한다. 역참조가 없으므로 6a는 그 자체로 완결·검증 가능하다(6a 완료 기준의 `init` exit 0 확인) |
| **잔여 위험과 방어** | 6b가 6a의 함수를 **재정의**하면 실질적 덮어쓰기가 된다 → 6b 완료 기준에 **[MUST] 9개 함수 정의가 각각 1개임을 정적 검사**로 못박았고, 시그니처 변경이 필요하면 `blocked` 반환을 지시했다 |
| **적용 범위** | 이 이탈은 **`code-scan.js` 1파일·2 Step 한정**이다. 다른 파일·다른 Step에는 규칙이 그대로 적용된다(픽스처 4 Step은 파일 집합이 비중첩이라 애초에 규칙 대상이 아니다) |
| Step 8 → Step 9 | 문서가 시드 형태(`_help` 포함)를 기술하므로 시드 확정 후 |
| Step 9 → Step 10 | `docs/`가 `tools.md` 서술과 정합해야 하므로 참조 문서 확정 후 |
| Step 7·8·9·10 → Step 11 | 전량 검증은 모든 산출물 확정 후 |
| Step 6 ∥ Step 7 (가능) | 파일 집합 비중첩(`test-shard.js` vs `setting.default.json`+`install-mac.sh`). 단 둘 다 Step 5 의존이므로 Phase 4·5로 분리 배치했다 — 순차 실행해도 총 비용 차이가 작고, Step 6이 RED→GREEN 판정을 겸하므로 먼저 확정하는 편이 안전하다 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 3단 우선순위가 셀 단위로 결정론적이다 | TS-001~TS-004 | §3.1.2 (F) 결정 표 7행 전부 일치 |
| F-001 | 프로젝트 타입 위반이 결정론적으로 거부된다 | TS-005 | exit 1 + `code_scan_config_invalid` + `detail`에 위반 키 |
| F-001 | 정책 판정 지점이 1곳이다 | TS-007, TS-008 | `DEFAULT_SHARD_POLICY`·`loadGlobalSetting(` 정적 검사 PASS, `manifestMaxBytes(` 함수 0개 |
| F-002 | 홈 경로가 주입 가능하다 | TS-014 | 서로 다른 `OPAL_HOME` 2개로 정책이 다르게 적용됨 |
| F-002 | 전역 설정 4상태 전부 비차단 폴백 | TS-010~TS-013, TS-016 | 부재·깨짐·키부재·타입위반에서 exit code 불변 |
| F-002 | 전역 파일을 쓰지 않는다 | TS-015 | 실행 전후 `setting.json` 바이트 동일 |
| F-003 | 바이트 초과 + 엔트리 미달은 열거되지 않는다 | TS-020, TS-022 | `counts.manifest_oversize === 0` |
| F-003 | 2축 동시 충족만 열거된다 | TS-021, TS-025 | 1건 열거 + exit 0(비차단) |
| F-003 | 경계 규칙 (`>` 바이트 / `>=` 엔트리) | TS-023, TS-024 | 4경계 케이스 전부 일치 |
| F-004 | 그룹 후보 + 예상 조각 크기를 출력한다 | TS-030 | `groups[].estimatedBytes`·`files.length` 존재 |
| F-004 | 자동으로 파일을 쓰지 않는다 | TS-031, TS-034 | `.opal/code-map/` 트리 바이트 동일 |
| F-004 | 미분류를 명시하고 임의 배분하지 않는다 | TS-032, TS-035 | `unassigned` 존재 + "기타" 라벨 0개 |
| F-004 | 결정론적이다 | TS-033, TS-116 | 사전 유/무 각각 2회 실행 stdout 바이트 동일 |
| F-004 | **사다리가 잔여만 흘려보낸다** | TS-100, TS-101, TS-107 | `trace[n].input === trace[n-1].remaining` + 앞 단계 배정 불변 + 미달 버킷이 즉시 `unassigned`로 확정되지 않음 |
| F-004 | **5단계가 각각 동작한다** | TS-102~TS-106 | S1(첫 토큰)·S2(2토큰 결합)·S3(중간 토큰)·S4(마지막 토큰)·S5(`depends` 공유) 각 1그룹 이상 |
| F-004 | **사전 다중 매칭이 결정론적이다** | TS-108, TS-132 | 스팬 길이 내림차순 → 등재 순서(`index`) 오름차순, `index`는 표 2개에 걸쳐 연속 |
| F-004 | **검토 장치 3종이 계약대로 동작한다** | TS-109~TS-112 | `--trace` 합계 정합 / `--stop-after` 이후 단계 `reason:'stopped'` / 잘못된 stage exit 1 / `groups[].stage` ↔ `assignments` 일치 |
| F-004 | **검토 장치가 왕복을 깨지 않는다** | TS-113 | `--trace --stop-after` 출력을 `--groups -`에 파이프해도 집행 성공 |
| F-004 | 사전 미발견 시 사다리가 축소 실행된다 | TS-114 | S1~S3 `skipped:true, reason:'dict_absent'` + S4·S5만 실행 |
| F-011 | **탐색 3단이 순서대로 동작한다** | TS-120~TS-123 | `dictPath` → `{설계}` 변수 → 기본 경로. 앞이 성공하면 뒤를 읽지 않음 |
| F-011 | **컬럼 수가 다른 표 2개를 모두 읽는다** | TS-124, TS-125 | 수식어(6열)·분류어(5열)에서 `영문`·`약어` 정확 추출 / 헤더 없는 표는 무시 |
| F-011 | **3분기 폴백이 전부 비차단이다** | TS-126, TS-127 | 부재·파손 모두 exit code 불변. 부재는 stderr 무출력, 파손은 1줄(실행당 1회) |
| F-011 | **읽기 전용 + 경로·크기 제한** | TS-128~TS-130 | 프로젝트 루트 밖 거부 / 크기 상한 초과 시 사전 없음 취급 / 실행 전후 사전·PROJECT.md 바이트 동일 |
| F-011 | 골든 경로에 영향이 없다 | TS-131 | 조회 8커맨드가 사전·`docs/PROJECT.md`를 읽지 않는다 (지연 로딩) |
| F-011 | 사전 미발견이 조용하지 않다 | TS-115 | `dict.found === false` + `dict.searched` + `--trace`에 "사전 미발견 — S1~S3 건너뜀" |
| F-012 | **게이트 순환이 없다** | TS-140, TS-141, TS-158 | 설정 부재·파손 트리에서 `init` exit 0 + 나머지 13 명령 게이트 동작 불변 |
| F-012 | **비대화형 + `--header-source` 필수** | TS-142~TS-144 | TTY 없이 동작·프롬프트 0건 / 인자 누락 시 exit 1 + **파일 미생성** / 구형 값 `auto`는 마이그레이션 안내 |
| F-012 | **쓰기 3분기 + 백업** | TS-145~TS-147 | 없음·`--write` 없음 → 쓰기 0건 / 있음·force 없음 → exit 1 `config_exists` + 원본 불변 / 있음·`--force` → `.bak` 원본 바이트 동일 |
| F-012 | **추론이 규약과 일치한다** | TS-148~TS-151, TS-154 | `scopes`(요소→kebab, 경로 첫 값) · 폴백(1-depth 스캔) · `extensions`(실재 + `.md` 강제) · `exclude` 10종 정확 일치 · 키 순서 · **이 저장소 재현 시 스코프 3종 일치** |
| F-012 | **`shardPolicy`를 초안에 넣지 않는다** | TS-152 | 초안에 해당 키 부재 → 3단 폴백 보존 |
| F-012 | 생성 보고 1줄 (규약 형식) | TS-153 | stderr에 `📂 code-scan.json 자동 생성: …` + stdout JSON 무오염 |
| F-012 | **복구 경로가 에러에 실린다** | TS-155 | `header_source_unset`·`header_source_invalid`·`code_scan_config_invalid`의 `fix`에 `init` 명령 포함 (차단 동작 자체는 불변) |
| F-012 | 중복 파서 신설 0건 | TS-156 | md 표 파싱이 `parseMdTable` 1곳이고 `parseWordDictionary`가 소비 |
| F-012 | 전역 설정 비접촉 (범위 제외) | TS-157 | 실행 전후 `{OPAL_HOME}/setting.json` 바이트 동일 |
| F-012 | 규약 문서 반영 | TS-160 | `pm/code-scan-management.md`에 `init` 등재 + `shardPolicy` 행 + `exclude` 불일치 해소 + 변경이력 |
| F-005 | 엔트리 유실 0건 | TS-041, TS-054 | 실행 전후 엔트리 총합 동일 (실제 파일 재로딩 기준) |
| F-005 | 실패 시 부분 상태 0건 | TS-046~TS-049 | 트리 바이트 동일 + `*.tmp-split` 잔존 0건 |
| F-005 | 실행 후 `validate` 0건 + `scaffold` no-op | TS-043, TS-044 | exit 0 + `created=0 updated=0` |
| F-005 | `--dry-run`이 결과를 미리 보여준다 | TS-045 | 출력 존재 + 쓰기 0건 |
| F-005 | 라벨 경로 이탈 차단 | TS-053 | `../evil`·`_shards`·대문자 → exit 1 |
| F-006 | 위반에 권고 조각 수 + 다음 명령이 포함된다 | TS-060 | `recommendedShards` ≥ 2 정수 + `next` 문자열 |
| F-006 | `next` 명령을 그대로 실행하면 제안이 나온다 | TS-061 | exit 0 + `--plan` 출력 |
| F-006 | `detail` 포맷이 불변이다 | TS-062 | `{bytes}/{maxBytes}` 정확 단언 |
| F-007 | 구 위치 값이 무시되고 1회 안내된다 | TS-070, TS-072 | 값 무영향 + stderr 1줄(실행당 1회) + 새 주소 포함 |
| F-007 | 구 위치가 비차단이다 | TS-071 | `invalid_index` exit 1로 승격하지 않음 |
| F-007 | 구·신 동시 존재 시 결정론적이다 | TS-073 | 신 위치 승, 구 위치 영향 0 |
| F-007 | 082 단언이 완화 없이 이전됐다 | TS-074 | §3.7.2 (C) 매핑 표 전행 일치 |
| F-008 | 전량 GREEN | TS-080 | 12 스크립트 실패 0건 |
| F-008 | 골든 바이트 diff 0 | TS-081 | `git diff --stat` 빈 결과 |
| F-008 | 개발자 홈에 의존하지 않는다 | TS-083, TS-084 | 가짜 홈 5종 대조 동일 + `OPAL_HOME` 주입 정적 검사 |
| F-009 | 버전·변경이력·문서 반영 | TS-090~TS-092, TS-097 | `1.6.0` + 일시(KST)+`(083)` 행 + `tools.md`·`header-rules.md` 반영 |
| F-010 | 신규 설치에 정책 키가 생성된다 | TS-093, TS-096 | `setting.default.json`에 2키 + 시드 없는 환경 폴백 동작 |
| F-010 | 기존 사용자값 무손실 + 멱등 | TS-094, TS-095 | 3형태 시드 후 기존 값 바이트 동일 + 2회 실행 동일 |

### 5.2 회귀 테스트

- [ ] `opal/tools/code-scan/tests/` 12 스크립트 전량 GREEN (082 26 시나리오 + 083 신규)
- [ ] `fixtures/golden/*` 8파일 **바이트 diff 0** — 재캡처 절대 금지
- [ ] 샤드 미선언 자산(`codemap-repo`·`legacy-repo`·`mixed-scope`) 출력 불변
- [ ] `resolveShards`(`code-scan.js:1002-1074`) 로직 무수정 — 082 봉인 훼손 0건
- [ ] `resolveHeaderSource`(`:263-320`) 로직 무수정 — 080 봉인 훼손 0건
- [ ] `code-map-hook.js` 무수정 + `loadConfig` fail-safe 계약 유지(throw/exit 0건) — `test-hook.js` GREEN으로 확인
- [ ] `counts` 키 집합 불변 (`manifest_oversize` 포함 9키, `code-scan.js:2276-2286`)
- [ ] 비차단 계약 불변 — `manifest_oversize`만으로는 exit 0 (`:2290-2292`)
- [ ] `discover --out`이 `opts.out` 개명 후에도 동작 (`test-discover.js` GREEN)
- [ ] `CODE_MAP_VERSION === 1` 불변 (상향 시 전 자산 `unsupported_version` 차단)
- [ ] **`.opal/` 밖 읽기가 `split --plan` 경로에만 존재한다** — 조회·검증·작성 명령의 읽는 파일 집합이 083 이전과 동일하다 (F-011 지연 로딩, H-17)
- [ ] **사전 md·`docs/PROJECT.md`에 쓰기 코드가 0곳이다** (정적 검사 — `op-data-dictionary` SSOT 경계 보호)

### 5.3 코드/문서 품질

- [ ] `docs/CONVENTIONS.md` 준수 — 문서 본문 한국어(기술 용어 영어 병기)
- [ ] 변경이력 기재: `code-scan.js`(v1.6.0) · `tools.md` · `header-rules.md` · `install-mac.sh` — 전부 일시(KST) 포함
- [ ] 의존성 0 계약 유지 — 신규 npm 패키지 0개, `require`는 Node 표준 모듈만(`fs`/`path`/`child_process`/`os`)
- [ ] 배포 경계 준수 — `~/.opal/` 직접 편집 0건, 검증은 소스 경로에서 실행
- [ ] 중복 패턴 신설 금지 — [MUST] `opal/core/PRINCIPLES.md` §2: "Remove a duplicated existing pattern before introducing a new one." (`code-scan.js:343` 인용) → `normalizeShardPolicy` 1개를 두 소스가 공유, `deprecationOnce`/`noticeOnce` 재사용, `--out`/`--dry-run` 재사용
- [ ] 판정 1곳 봉인 3종 유지 — `resolveHeaderSource`(모드) / `resolveShards`(샤드) / `resolveShardPolicy`(정책)
- [ ] 하드코딩 플랫폼 분기 0건 — `OPAL_HOME` 경유 홈 해석
- [ ] TS-ID ↔ QA 매트릭스 정합 (§3.N.5 ↔ §5.1)

### 5.4 보안

- [ ] `split`의 라벨이 `SHARD_LABEL_RE`(`code-scan.js:69`)로 검증되어 **경로 이탈(path traversal)이 차단**된다 — `../`·절대경로·`_shards` 전부 거부 (TS-053)
- [ ] `<manifest-path>` 인자가 `{projectRoot}/.opal/code-map/` 하위로 제한된다 — 임의 경로 쓰기 불가 (§3.5.2 (A) 검증 1)
- [ ] `split`이 쓰는 경로가 정규화 후 재확인된다 — symlink·`..` 우회로 code-map 밖에 쓰지 않는다
- [ ] 전역 설정 읽기가 **읽기 전용**이다 — code-scan은 `~/.opal/setting.json`을 쓰지 않는다 (TS-015)
- [ ] 전역 설정에서 `shardPolicy` 외 키를 읽지 않는다 — `bootstrap`·`models` 비접근 (F-1b AC)
- [ ] **사전 경로가 프로젝트 루트 하위로 제한된다** — `shardPolicy.dictPath`에 `../../etc/passwd`·절대 경로를 넣어도 읽지 않고 다음 후보로 넘어간다 (TS-128, H-17)
- [ ] **사전 파일 크기 상한이 걸린다** — `DICT_MAX_BYTES` 초과 시 읽지 않는다 (TS-129, DoS 방어)
- [ ] **사전·`docs/PROJECT.md`가 읽기 전용이다** — 실행 전후 바이트 동일 (TS-130)
- [ ] 코드에 하드코딩된 토큰/시크릿이 없다
- [ ] `.env`·인증 파일이 `.gitignore`에 포함되어 있다 (기존 상태 확인)
- [ ] 픽스처 `homes/*/setting.json`에 실제 자격증명·개인 홈 경로가 들어가지 않는다
- [ ] 픽스처 사전 md에 실제 프로젝트의 도메인 용어·고객사명이 들어가지 않는다 (합성 용어만 사용)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | **12개** (6a/6b 분할 포함) | 복잡 (6개 이상) |
| 변경 파일 수 | **약 41파일** (신규 픽스처 트리 포함, 합집합) | 복잡 (4개 이상) |
| 모듈 범위 | 도구(`code-scan.js`) + 테스트(12) + 배포(`install-mac.sh`·`setting.default.json`) + 문서(**5**) = **다중** | 복잡 |
| 작업 유형 | **신규 서브명령 2개**(`split`·`init`) + 설정 계층 신설 + 판정 로직 변경 + 다단 분류 엔진 + 외부 문서 파서 + **설정 파일 생성기** = **대규모 개선** | 복잡 |
| 외부 의존성 | 신규 패키지 0개. 단 **신규 외부 파일 의존 3건** — `~/.opal/setting.json`(F-002) · `docs/PROJECT.md`(F-011 사전 경로 / **F-012 스코프 추론**) · `{설계}/사전/표준단어사전.md`(F-011). **후자 2건은 `.opal/` 밖 최초 읽기**다 | 복잡 |
| **실행 모드** | **복잡** | |

> U-2 개정 영향: 기능 10개 → 11개(F-011 신설), Step 10개 → 11개, 신규 외부 파일 의존 1건 → 3건.
> F-012 개정 영향: 기능 11개 → **12개**, Step 11개 → **12개**(6a/6b), 문서 대상 4 → **5파일**, 서브명령 14 → **15개**.
> **두 차례 확장에도 판정은 복잡 모드로 불변**이며, 늘어난 것은 복잡도의 정도이지 종류가 아니다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (병렬)  ┌ A1: opal-task-agent  → Step 1 (shard-violations 픽스처)
                ├ A2: opal-task-agent  → Step 2 (shard-goal 픽스처)
                ├ A3: opal-task-agent  → Step 3 (shard-policy 정책·전역설정 픽스처)
                └ A4: opal-task-agent  → Step 4 (split-target + 사전 픽스처)
                              ↓
Batch 2         B1: opal-test-agent(mode:red) → Step 5 (RED-first test-shard-policy.js)
                              ↓
Batch 3         C1: opal-task-agent  → Step 6a (code-scan.js — 설정·정책·init, (a)~(g))
                              ↓   ※ 6a 완료 확인 후에만 진행 (엄격 순차, 동시 편집 0)
Batch 4         C2: opal-task-agent  → Step 6b (code-scan.js — 사전·사다리·split, (h)~(l))
                              ↓
Batch 5         D1: opal-task-agent  → Step 7 (test-shard.js 단언 이전)
                              ↓
Batch 6         E1: opal-task-agent  → Step 8 (setting.default.json + install-mac.sh)
                              ↓
Batch 7         F1: opal-task-agent  → Step 9 (tools.md + header-rules.md + code-scan-management.md)
                              ↓
Batch 8         G1: opal-task-agent  → Step 10 (docs/)
                              ↓
Batch 9         H1: opal-test-agent  → Step 11 (전량 검증 + 골든 불변)
```

**그룹핑 근거**:
1. **파일 충돌 방지 최우선** — `code-scan.js`를 만지는 작업은 C1·C2 **2 에이전트이나 배치가 겹치지 않는다**(Batch 3 → Batch 4 엄격 순차). 이 파일은 2,475줄이고 편집 지점이 F-012 포함 **13곳**이므로 두 에이전트가 **동시에** 손대면 전량 유실 위험이 있으나, 순차 배치에서는 그 구간이 존재하지 않는다(§4.3 이탈 근거).
2. **모듈 응집도** — 픽스처 4 에이전트는 디렉토리가 비중첩이라 안전하게 병렬화된다. A3(정책·전역설정)과 A4(분할·사전)는 소비 기능이 달라 의미상으로도 갈린다.
3. **검증 2원화** — 테스트 작성(B1)과 구현(C1·C2)을 다른 에이전트에 배치해 self-confirming을 막는다. 최종 검증(H1)도 구현 에이전트와 분리한다.
4. **중단 내성** — 편집 지점을 순서대로 **각각 즉시 저장**하며 진행한다. 2분할로 단일 디스패치의 최대 손실 범위가 13개 → **7개 지점**으로 줄었다. 중단 시 PM이 워킹트리 실측으로 잔여 지점만 재배치한다(R-12).
5. **C2 재정의 방어** — C2는 C1이 만든 9개 함수를 재정의하지 않는다(Step 6b 완료 기준 [MUST] 정적 검사). 시그니처 변경이 필요하면 `blocked` 반환.

### C-2. 스킬 요구사항

| 작업 | 스킬 | 갭 판별 |
|------|------|--------|
| Step 1~4, 6~10 | `op-dev-execute` | 기존 스킬로 충분 |
| Step 5 | `op-dev-test` (mode:red) + [MUST] `~/.opal/references/harness/red-first.md` | 기존 |
| Step 11 | `op-dev-test` | 기존 |
| Step 9·10 (문서) | `op-dev-execute` — **PM 직접 아님** (PM Gate 정정: 디스패치 의무) | 기존 |

- **갭 없음**. 신규 스킬 후보 0건 — U-3에서 전용 스킬 신설을 불채택했고, 3개 이상 Step에서 반복되는 신규 패턴이 없다.
- **U-2 개정 후 재확인**: 사다리·사전 파서도 신규 스킬을 요구하지 않는다 — 사전 **형식**의 SSOT는 `op-data-dictionary`(D-20)이고 083은 그 소비자일 뿐이므로, 참조할 문서가 이미 존재한다.

### C-3. 도구 요구사항

| 도구 | 용도 | 상태 |
|------|------|------|
| Node.js (`node --test`) | 테스트 실행 | 기존 |
| `python3` | `install-mac.sh` 시드 검증 | 기존 (install이 이미 사용) |
| `git` (읽기 전용) | 골든 diff 확인 (`diff --stat`) | 기존. **[MUST] `stash`/`checkout`/`reset`/`clean`/`restore`/`rm`/`commit`/`add`/`gc` 금지** |
| `cp -R` | 깨끗한 상태 확인용 임시 복사 (git stash 대체) | 기존 |
| 신규 패키지 | **0개** | 의존성 0 계약 유지 |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 명령 | 기대 |
|------|------|----------|------|
| L1 (단위·계약) | 정책 3단 해석 · 2축 판정 · groups 스키마 · 라벨 안전 · 봉인 정적 검사 | `node --test tests/test-shard-policy.js` | 전량 GREEN |
| L2 (통합) | `--plan` → `split` → `validate` → `scaffold` 왕복 · 원자성·롤백 · 격리 대조 · install 시드 3형태 | 동상 + `tests/test-shard.js` | 전량 GREEN |
| L2 (회귀) | 082 26 시나리오 · 골든 8커맨드 · 샤드 미선언 자산 | `node --test tests/` | 전량 GREEN + 바이트 diff 0 |
| L3 (수동) | 실 `~/.opal/setting.json` 상태와 무관하게 결과 동일함을 사람이 확인 (파일 변조 금지 — 읽기만) | 소유자 확인 | PM Gate |

- **실패 시 원칙**: [MUST] `tests/test-shard.js:19-21` 선례 — "기대값 완화로 통과를 유도하는 것은 reward hacking이다. 실패 이유가 '미구현'이어야 하며 '테스트 자체 오류'여서는 안 된다."
- 골든 diff가 0이 아니면 **GREEN 처리 금지**하고 원인을 규명한다 (`tests/test-regression.js:509` 문구 계승).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Node.js CLI — 의존성 0 단일 파일 2,475줄 (`code-scan.js:29-31`) | 해당 없음 (프레임워크 내부 도구) |
| 테스트 | `node:test` + `node:assert/strict` + `spawnSync` 블랙박스 12 스크립트 | `op-dev-test` (mode:red) |
| 배포 | bash + inline python3 (`scripts/install-mac.sh`) | 해당 없음 |
| 문서 | Markdown (한국어 본문 + 영어 기술 용어) | `docs/CONVENTIONS.md` |

> 프레임워크 내부 도구 태스크이므로 `plan-guide.md` §0의 기술 스택별 추천 스킬(React/Next.js/shadcn/Python 등)은 **해당 대상이 없다**. FE 화면 설계도 없으므로 §3.N.2의 `##### 화면:` 서브섹션은 작성하지 않는다.

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 API 조회 대상이 0건이다 — Node 표준 모듈(`fs`/`path`/`os`)만 사용하며 최신 API 확인이 필요한 서드파티가 없다. context7·shadcn MCP 미사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 변경 대상 본체 (v1.5.0, 2,475줄) — 상수(`:70`)·`loadConfig`(`:217`)·`resolveHeaderSource`(`:263`)·`deprecationOnce`(`:376`)·`noticeOnce`(`:384`)·`loadCodeMap`(`:839`)·`manifestMaxBytes`(`:881`)·`resolveShards`(`:1002`)·`mergeManifest`(`:1742`)·`listManifestFiles`(`:1772`)·`cmdScaffold`(`:1787`)·`checkOversize`(`:2146`)·`main`(`:2351`) |
| D-2 | 소스 | code-map-hook.js | `opal/tools/code-scan/code-map-hook.js` | `loadConfig` fail-safe 계약의 소비자 — 무수정 확인 대상 |
| D-3 | 소스 | test-shard.js | `opal/tools/code-scan/tests/test-shard.js` | 082 계약 단언 26종 — S-15(`:407`)·S-16(`:426-501`)·S-17(`:507`)·S-25(`:527`)·S-22(`:601`)·`deriveAfterTree`(`:169`)·하네스(`:75-83`) |
| D-4 | 소스 | test-regression.js | `opal/tools/code-scan/tests/test-regression.js` | 골든 8커맨드 비교(`:503-511`)·픽스처 전량 검사 TS-063(`:557-569`)·`HOME` 격리 선례(`:467`) |
| D-5 | 설계 | 선행 태스크 082 | `tasks/082-260803-opds-코드맵-매니페스트-샤딩/` (TASK.md·PLAN.md·DONE.md) | 샤딩 구조·비차단 결정(U-2)·`resolveShards` 봉인 방식·`manifestMaxBytes` 도입 근거(PLAN §3.5.2)·버전 판정 논리(§3.8.1) |
| D-6 | 설계 | 선행 태스크 080 | `tasks/080-260801-opd-헤더소스-단일화/` | 구 키 무시 + `deprecationOnce` 선례(F-002)·설정 판정 1곳 봉인 선례(`resolveHeaderSource`)·"자동 변환하지 않습니다" 문구 관용 |
| D-7 | 설계 | brain — 샤딩 설계 결정 | `.opal/brain/pages/concept/code-scan-manifest-sharding-design.md` | 승계 4항(§1.5) — 특히 "패턴 추측 라우팅 불채택"이 U-2의 경계 근거 |
| D-8 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 구현 규칙 — Guards(승인 전 금지)·변경이력 작성 의무·문서 본문 한국어 |
| D-9 | 설계 | 도구 레지스트리 | `opal/core/references/tools.md` | code-scan 절(`:202-343`) 갱신 대상 + 082 S-22 단언 대상 |
| D-10 | 설계 | @header 규칙 | `opal/core/references/harness/header-rules.md` | 워커 권한 경계(`:44-49`) — `shards`·`files` 키가 이미 도구 관할임을 확인(083은 집행 수단 추가) |
| D-11 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | §0 근거 제시 원칙·§2 인용 포맷·§2.4 [MUST] 포맷 |
| D-12 | 소스 | install 스크립트 | `scripts/install-mac.sh` | F-8b 시드 대상 — `install_opal_setting`(`:918-953`), 조기 종료 결함(`:937-939`) |
| D-13 | 설정 | 전역 설정 기본값 원본 | `opal/core/setting.default.json` | 현행 스키마(`bootstrap`·`models`) + `_help` 관용 — U-5 (C) 근거 |
| D-14 | 설정 | 전역 설정 (배포본 — 읽기 전용) | `~/.opal/setting.json` | 실 환경 스키마 확인 (`models` 존재 → H-11 근거). **직접 편집 금지** |
| D-15 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | `OPAL_HOME` 관용 선례(`:236`·`:242`) — U-7 채택 근거 |
| D-16 | 소스 | doctor checks.sh | `opal/tools/doctor/lib/checks.sh` | `OPAL_HOME` 관용 선례(`:25`) — 의미가 `~/.opal` 디렉토리 자신임을 확인 |
| D-17 | 설계 | 원칙 | `opal/core/PRINCIPLES.md` | §2 중복 패턴 제거 원칙 (`code-scan.js:343`에서 [MUST]로 인용된 규칙) |
| D-18 | 설계 | RED-first 하네스 | `~/.opal/references/harness/red-first.md` | §3 GREEN 루핑 중 테스트 수정 금지 — Step 4·6 계약 |
| D-19 | 설정 | 이 프로젝트 code-scan 설정 | `.opal/code-scan.json` | 083 정책 키가 놓일 실제 파일 (현행 `headerSource: "inline"` + `scopes` 3종). 본 태스크에서는 무수정 |
| D-20 | 설계 | 표준사전 스킬 | `opal/skills/op-data-dictionary/SKILL.md` | **U-2 개정 핵심 근거** — `:21` 경로 하드코딩 금지 [MUST] · `:74-90` 사전 md 표 형식(수식어 6열 / 분류어 5열, H-15) · `:72`·`:172` 경로 자기모순(H-19) |
| D-21 | 소스 | `resolveHeader` fail-soft | `opal/tools/code-scan/code-scan.js:1142-1148` | 사전 폴백의 선례 창구 — "차단 조건을 늘리지 않고 사유만 stderr 1줄로 노출하는 fail-soft" |
| D-22 | 소스 | `WORKER_FIELDS` | `opal/tools/code-scan/code-scan.js:62` | 사다리 S5의 입력 `depends`가 이미 정의된 워커 기입 필드임을 확인 — 신규 데이터 수집 0건 |
| D-23 | 소스 | `deriveAfterTree` 픽스처 파생 선례 | `opal/tools/code-scan/tests/test-shard.js:169-192` | 082 게이트 gaps G-3 "수작성 2벌 금지" — Step 3·4의 픽스처 변형을 테스트가 파생 생성하는 근거 |
| D-24 | 설계 | 프로젝트 개요 | `docs/PROJECT.md` | `{설계}` 경로 변수 원천 (**이 저장소에는 미등록** — 사전 탐색 3단이 기본 경로로 떨어지는 것이 정상임을 확인) + **F-012 `scopes` 추론 소스** — `:152-160` §프로젝트 구성 표(`요소`·`경로` 컬럼 3행) |
| D-25 | 설계 | **code-scan.json PM 관리 의무 (F-012 규약 SSOT)** | `opal/core/references/pm/code-scan-management.md` | `:12` 즉석 추론 생성 · `:16-21` 추론 소스 규약 표 · `:25-33` 최소 구조 예시 · `:44-46` 생성 보고 1줄 · `:87` "도구는 이 질문을 하지 않는다(비대화형)" — **F-012는 이 산문을 코드로 이식한다** |
| D-26 | 설계 | 디스패치 프로세스 | `opal/core/references/pm/dispatch-process.md` | `:157` Step 6 항목 5 산출량 상한 — Step 6a/6b 분할의 이탈 근거 판단 기준(§4.3) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 기본값 인하 + 하한 도입이 082 픽스처 5종의 초과 판정을 전부 없앤다 (H-1·H-2) | F-003, F-008 | **P0** — 082 계약 테스트 다수 RED | 픽스처에 `shardPolicy` 오버라이드 명시로 흡수(Step 1·2). **단언은 손대지 않는다** (제약 ⑤) |
| R-2 | 구 위치 게이트 제거로 082 S-16 (e)의 `invalid_index` 단언이 깨진다 (H-9) | F-007 | P1 | §3.7.2 (C) 매핑 표대로 **주소 이전 + 2건 추가**(1→3). 완화 0건 |
| R-3 | 위반 `detail` 포맷 변경 유혹 — 2축 정보를 detail에 넣으면 S-15가 깨진다 (H-8) | F-006 | P1 | **포맷 불변 + 신규 필드 additive**. TS-062가 포맷을 정확 단언으로 고정 |
| R-4 | 전역 파일 읽기가 조회 8커맨드 경로에 부수효과를 만들어 골든이 흔들린다 (H-13) | F-002 | **P0** | `loadGlobalSetting`을 `resolveShardPolicy` 첫 호출 시점으로 **지연 로딩**. 조회 명령은 정책을 읽지 않는다. TS-081이 바이트 diff 0을 고정 |
| R-5 | 테스트가 개발자 실제 홈에 좌우된다 (H-4) | F-002, F-008 | **P0** | `OPAL_HOME` 주입을 전 테스트 하네스 **기본값**으로 두고(`homes/absent`), 예외를 만들지 않는다. TS-084가 정적 grep으로 누락을 잡는다 |
| R-6 | `split` 부분 실패로 엔트리가 유실된다 (H-6·H-7) | F-005 | **P0** | 4단 파이프라인(사전 불변식 → tmp 전량 → rename 커밋 → 사후 재검증 + 백업 복원). TS-041·TS-046~TS-049 |
| R-7 | `split` 출력 키 순서가 `mergeManifest`와 달라 `scaffold`가 no-op이 되지 않는다 | F-005 | P1 | §3.5.2 (C) 규칙 3 — 키 순서 `version→scope→dir→shards→package→files` + `orderFilesObject` + 동일 직렬화. TS-044 |
| R-8 | install 시드가 조기 종료 구조 때문에 기존 환경에 영구히 적용되지 않는다 (H-11) | F-010 | P1 | 병합 python을 `SEED_KEYS` 키 목록 루프로 재작성(§3.9.2 (C)). TS-094가 3형태로 검증 |
| R-9 | 정책 판정 지점이 2곳으로 늘어 3단 우선순위가 갈린다 (H-12·H-3) | F-001 | **P0** | `manifestMaxBytes(ctx)` **제거**(병존 금지) + `DEFAULT_SHARD_POLICY`·`loadGlobalSetting` 정적 grep 검사(TS-007·TS-008) |
| R-10 | `--plan` 제안이 흔들려 왕복이 재현 불가해진다 (H-10) | F-004 | P1 | 정렬 규칙 명시(엔트리 수 내림차순 → 라벨 사전순, files 사전순) + TS-033 2회 실행 바이트 동일 |
| R-11 | `--out` 개명이 `cmdDiscover`를 깨뜨린다 | F-004 | P2 | 참조 3곳(`:164`·`:178`·`:1634`)만 존재함을 grep으로 확인했다. TS-039 + `test-discover.js` GREEN |
| R-12 | Step 6이 단일 Step으로 커서 중단 시 손실이 크다 | F-001~F-007, F-011 | P1 | (a)~(l) **12개** 하위 작업을 **순서대로 즉시 저장**하며 진행한다. 중단 시 PM이 워킹트리 실측으로 잔여 지점만 재배치한다. 파일 분할은 충돌 위험이 더 크므로 채택하지 않는다 |
| R-13 | `tools.md`에서 `manifestMaxBytes`를 지워 082 S-22가 깨진다 | F-009 | P2 | 폐기 안내 절에 키 이름을 **남긴다**(§3.9.2 (D)). 추가로 `shardPolicy` 정규식 1건 신설 |
| R-14 | 용어 불일치 — 설정 키는 `minFiles`(파일 수)인데 코드·위반 페이로드는 `entries`(엔트리 수)를 센다 | F-001, F-003, F-006 | P2 | 의도된 차이다 — 설정 키는 소유자 언어(TASK 전반이 "파일 수"로 서술), 내부·페이로드는 실제 계수 대상(매니페스트 `files` 엔트리)을 정확히 부른다. `tools.md`에 "`minFiles` = 매니페스트 `files` 엔트리 수"를 **1줄로 명시**해 해석 여지를 제거한다. 이름 통일은 하지 않는다(설정 키 변경은 TASK 확정 방향 #2의 용어를 벗어난다) |
| R-15 | `split_*` 신규 에러 코드 7종이 에러 코드 도메인을 늘린다 | F-005 | P2 | 쓰기 여부가 실패별로 다르고 그 구분이 사람의 다음 행동을 가르므로 의도된 확장이다(§3.5.2 (G)). 쓰기와 무관한 설정 위반은 기존 `code_scan_config_invalid`에 합류시켜 증가를 억제했다 |
| R-16 | 사전 md 파서가 위치 기반이면 **분류어 표에서 조용히 오분류**한다 — 예외 없이 잘못된 라벨이 나온다 (H-15) | F-011 | P1 | **헤더 이름 기반 파싱**(§3.10.2 (B)) + 헤더에 `한글`/`영문`/`약어`가 없는 표는 무시. TS-124가 두 표를 동시에 담은 픽스처로 고정 검증한다 |
| R-17 | 사전 부재 시 커버리지가 조용히 떨어져 사용자가 원인을 모른다 (H-16) | F-004, F-011 | P2 | `--plan` 출력에 `dict.found`·`dict.searched`를 **항상** 싣고, `--trace`에 "사전 미발견 — S1~S3 건너뜀"을 명시. 부재 자체는 stderr를 내지 않되(정상 상태) 화면에서는 감추지 않는다 (TS-115) |
| R-18 | `.opal/` 밖 최초 읽기가 새 실패 축을 만든다 — 경로 이탈·거대 파일·읽기 실패 (H-17) | F-011 | P1 | 경로를 `projectRoot` 하위로 제한 + `DICT_MAX_BYTES` 상한 + 전량 `try/catch` 폴백 + **쓰기 코드 0곳**. TS-128·TS-129·TS-130 + §5.2 정적 검사 2건 |
| R-19 | 검토 장치 3종이 `--plan` 출력 스키마를 늘려 U-1 왕복이 깨진다 (H-18) | F-004 | P2 | `parseGroupsDoc`이 **`groups[].label`·`groups[].files` 2필드만** 읽는다(§3.4.2 (B) 왕복 불변식). `trace`·`stage`·`assignments`·`ladder`·`dict`는 전부 선택 + 무시. TS-113이 `--trace --stop-after` 출력을 그대로 파이프해 고정 검증 |
| R-20 | `{설계}` 경로 규칙이 SKILL.md 안에서 자기모순이라 사전을 못 찾는다 (H-19) | F-011 | P2 | 기본 경로를 **2후보**(`200.설계/사전/`·`200.설계/210.사전/`)로 순서 탐색해 문서가 말하는 두 경로를 모두 존중한다(§3.10.2 (A)). 새 규칙을 만들지 않는다. **SKILL.md 자체의 정정은 083 범위 밖 — PM에 보고한다** |
| R-21 | 사다리 도입으로 F-004 구현량이 커져 Step 6(단일 Step)이 더 무거워진다 | F-004, F-011 | P1 | 편집 지점을 (a)~(l) 12개로 **명시적으로 번호화**하고 각 지점마다 즉시 저장한다. 파일 분할은 충돌 위험이 더 크므로 여전히 채택하지 않는다(§4.3). 중단 시 PM이 워킹트리 실측으로 잔여 지점만 재배치 |
| R-22 | `shardPolicy.ladder` 미노출이 "왜 못 바꾸냐"는 요구로 돌아온다 | F-004 | P2 | **의도된 범위 제한**이며 §1.6 U-2 (3)에 "후속 이관"으로 명시했다. 내장 사다리가 실사용 데이터를 한 번 받은 뒤 노출 형태를 정하는 편이 스키마를 되돌릴 위험이 낮다. `--stop-after`·`--trace`가 그 사이의 관측 수단을 제공한다 |
| R-23 | `init`이 게이트 뒤에 배치되어 **기능이 통째로 무용지물**이 된다 (H-22) | F-012 | **P0** | `main()`의 `resolveHeaderSource` 게이트 **앞**에 `init` 분기를 둔다(§3.12.2 (B)). 게이트를 완화하는 것이 아니라 **게이트가 요구하는 값을 CLI 인자로 강제**하는 방식이다. TS-140(설정 부재)·TS-141(설정 파손)·TS-158(나머지 명령 게이트 불변)이 3면으로 고정 |
| R-24 | 추론 결과가 규약과 갈려 **생성 주체(PM 손 vs 도구)에 따라 설정이 달라진다** (H-20) | F-012 | P1 | §3.12.2 (C) **1:1 대조표 13행**으로 규약 항목마다 구현을 대응시키고, 이탈 1건(`exclude`)은 (D)에 사유를 명시했다. TS-154가 **이 저장소 실제 파일과의 재현 일치**로 검증한다 |
| R-25 | `--force`가 소유자 조정값(`scopes` include/exclude·`excludePatterns`·`shardPolicy`)을 통째로 날린다 (H-21) | F-012 | P1 | 덮어쓰기 직전 **`.opal/code-scan.json.bak` 1세대 백업**(§3.12.2 (F)). `--write` 단독은 기존 파일을 건드리지 않고 exit 1. TS-146·TS-147 |
| R-26 | 규약 문서 자체의 `exclude` 불일치(표 `:20` vs 예시 `:30`)가 방치되면 다음 구현자가 또 갈린다 | F-012, F-009 | P2 | 083이 **예시 기준으로 확정**하고 규약 문서의 표에서 `tests`를 제거해 불일치를 해소한다(§3.9.2 (F)). 코드를 규약에 맞추는 데 그치지 않고 **규약 자체의 모순을 닫는다** |
| R-27 | `code-scan.js`를 2 Step이 만져 후행이 선행을 덮어쓴다 | F-001~F-012 | P1 | **엄격 순차 배치**(6a 완료 후에만 6b 디스패치)로 동시 편집 구간을 제거하고, 6b 완료 기준에 **9개 함수 정의 1개씩 정적 검사**를 [MUST]로 못박았다(§4.3 이탈 근거). 규칙 이탈 근거를 원문 인용과 함께 문서화 |

### 용어 일관성 검토 (citation-rules.md §7)

`citation-rules.md` §7.1 영역 쌍 점검 결과 — FE↔BE·ERD↔코드·IA↔라우트 쌍은 **해당 없음**(프레임워크 내부 도구 태스크). 검출된 유일한 항목은 R-14(설정 키 `minFiles` ↔ 내부 계수 `entries`)이며, **의도된 계층 차이 + 문서 1줄 명시**로 해소한다. §7.5의 에스컬레이션 대상(`terminology_mismatch`)에는 해당하지 않는다 — 두 토큰이 같은 계층에서 경합하는 것이 아니라 소유자 언어와 구현 언어가 각자 자기 계층에서 정확한 이름을 쓰는 구조이며, PLAN이 그 사상을 명시했다.

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-03 | PLAN.md 최초 작성 — 기능 10개(F-001~F-010) 식별, 미확정 U-1~U-7 전항 결정, 리스크 가설 H-1~H-14, 실행 체크리스트 10 Step, 복잡 모드 판정 (Task 083) |
| 2026-08-04 17:40 | **EXECUTE 중 PLAN 갭 폐쇄 — Step 7b 신설**(테스트 `OPAL_HOME` 격리 주입 10파일, 3배치 병렬). §3.8.1 항목 5가 요구한 주입이 §4.2 어느 Step에도 배정되지 않아 H-4 격리 구멍이 남아 있었다 — Step 7 워커가 발견·보고하고 PM이 실측 검증 후 신설했다(12/12 주입 완료, `assert.` 전량 불변). 총 12 Step → 13 Step. 함께 EXECUTE 중 PM이 판정한 테스트 결함 3건 정정 기록: `writeManifestBytes` 픽스처 정합(선언 엔트리 ↔ 디스크 소스 불일치로 exit 2 필연) · TS-048 주입 지점 교정(존재하지 않는 디렉토리 chmod → ENOENT 자멸) · TS-082 축 분리(전제 오류 — `codemap-repo`는 code-map **보유** 자산이라 극단 정책 주입 시 영향이 없으면 오히려 미배선). 3건 모두 **단언 완화 0건**, 검증을 더 정밀하게 만드는 방향 (Task 083) |
| 2026-08-04 | **F-012 `code-scan init` 신설 개정 (소유자 승인 — 083 마지막 범위 확장)** — `pm/code-scan-management.md` 산문 규약을 코드로 이식하는 `init` 서브명령 추가. §1.2 F-012 행(디스패치가 지칭한 "F-011"은 직전 개정에서 용어사전 로더에 배정 완료 → 재번호 대신 **F-012 배정**, 총 12기능)·§1.3 독립 노드, §2.12 분석 신설(규약 원문 [MUST] 3건·게이트 순환 발견·`docs/PROJECT.md` 표 실측·추론 재현 가능성), §3.12 설계 신설(**게이트 앞 배치**·`resolveHeaderSource` 재사용·**규약 1:1 대조표 13행**·이탈 1건(`exclude`) 사유·`shardPolicy` 초안 제외 사유·쓰기 3분기+`.bak` 백업·`parseMdTable` 공용 추출·`fix` 문구 보강 4곳·전역 시드 범위 제외), §3.9.2 (F) 규약 문서 갱신 항목 신설(**소스 경로 `opal/core/references/pm/…`**), 리스크 **H-20~H-22 추가**, §4 **Step 6 → 6a/6b 엄격 순차 2분할**(번호 미이동, 총 12 Step) + §4.3 **규칙 이탈 근거 6행**(`dispatch-process.md:157` 원문 인용), §5 QA 10행·§6 재계수·§7 토폴로지 9배치·§8.3 D-25~D-26·§9 R-23~R-27 추가. **U-1~U-7·사다리·사전 폴백 결정은 전부 불변** (Task 083) |
| 2026-08-04 | **U-2 교체 개정 (소유자 검토 반영)** — 분할 제안 알고리즘을 "단일 축(1차 토큰)" → **"단계 사다리(S1~S5) + 용어사전 대조"**로 전면 교체. §1.6 U-2 재작성(대안 표에 단일 축 불채택 사유 보존, 사다리 구조·단계 4요소·내장 사다리·사전 옵셔널 폴백·검토 장치 3종·결정론 규칙 7절), **F-011 용어사전 로더 신설**(F-004에서 분리 — 실패 계약 독립), §2.4 F-004 분석 확장 + §2.11 F-011 분석 신설, §3.1.2 정책 스키마에 `dictPath` 추가(키별 타입 표로 전환·`SHARD_PLAN_MIN_GROUP` 삭제), §3.4 사다리 엔진 설계 전면 재작성(`SHARD_PLAN_LADDER`·`stageKeyFor`·`dictMatchSpan`·`--trace`/`--stop-after` 출력), §3.10 F-011 설계 신설(탐색 3단·헤더 기반 파서·폴백 3분기), 리스크 가설 **H-15~H-19 추가**, §4 Step 3 비중첩 2분할(구 Step 3 → Step 3·4, 이후 +1 재번호, 총 11 Step), §5 QA 15행·회귀 2항·보안 4항 추가, §6 복잡도 재계수, §7 토폴로지 갱신, §8.3 D-20~D-24 추가, §9 R-16~R-22 추가. **U-1·U-3·U-4·U-5·U-6·U-7 결정은 불변** (Task 083) |
