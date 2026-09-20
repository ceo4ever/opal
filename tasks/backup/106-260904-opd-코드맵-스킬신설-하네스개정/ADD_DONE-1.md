# ADD_DONE-1: code-scan 헤더 읽기 단위 통일 + 창문 상향

> 추가작업 번호: **ADD-1** | 일시: 2026-09-05 00:23 시작 / 00:50 완료 (KST)
> 원본 태스크: 106 (`//opd --agentic`) — DONE.md는 원본 완료 기록으로 보존, 수정하지 않음
> 워커 소요: **16분** (`opal-be-agent`, advanced)
> 판정: **완료** — 결함 해소 실측 · `code-scan` 테스트 **340/0** · 성능 저하 없음

## 사유

태스크 106이 CLOSE 게이트에서 실제로 부딪히고 DONE.md **§8 이월 1번**으로 남긴 결함이다. 106 §9는 캡틴 승인 아래 게이트를 우회했고, 이 추가작업이 그 우회를 불필요하게 만든다.

`code-scan.js`가 **같은 상수 `HEADER_READ_BYTES`를 두 경로에서 다른 단위로 해석**했다.

| 경로 | 코드 | 단위 |
|------|------|------|
| 현재 파일 읽기 | `readFileHead` — `Buffer.alloc` + `readSync` | **바이트** |
| HEAD 비교 읽기 | `classifyUncovered` — `head.content.slice(0, N)` | **문자**(UTF-16) |

한글은 UTF-8 3바이트 / UTF-16 1유닛이므로 한글 `@header`에 대해 바이트 창문이 문자 창문의 약 1/3만 담는다. 블록 종료가 두 창문 **사이**에 놓이면 라이브는 "미보유"·HEAD는 "보유"로 읽어 `classifyUncovered`의 「HEAD에 있었는데 지금 없다 = 회귀」 규칙에 걸리고, **거짓 `newly_uncovered`** 로 `header-rules.md` §갱신 시점 (b) CLOSE 게이트를 차단했다.

## 변경 내용

**교정 2축** (독립 — 하나만으로는 부족하다)

| 축 | 변경 | 근거 |
|----|------|------|
| **(1) 단위 통일** | `classifyUncovered`의 절단을 `Buffer.from(head.content,'utf8').subarray(0, HEADER_READ_BYTES).toString('utf8')`로 교정 (`:1106`) | 라이브 경로가 이미 바이트. 문자 쪽으로 맞추면 **파일 전체 읽기**가 필요해 성능 불리 |
| **(2) 창문 상향** | `HEADER_READ_BYTES` **8192 → 24576** (`:45`) | 레포 `@header` 115건 전수 실측 — p50 683 / p90 3666 / 최대 17810. 8192 초과 3건, **24576 초과 0건**(최대의 1.38배). 32768로 올려도 초과 건수는 동일해 이득 없음 |

- 상수 위에 **단위 계약**(바이트 고정 · 두 소비 경로)과 실측 근거표를 주석으로 고정했다.
- `:1106` 위에 「[정합 조건] HEAD 창문과 라이브 창문이 **같은 단위**여야 성립한다」 주석을 신설했다.
- 부수: 이 파일 자신의 `@header` `description`을 **1문장으로 압축**(1780자 → 238자, 블록 6382 → 3689바이트). `header-standard.md` §description "파일의 역할 한 줄 요약" 규정에 정합.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/tools/code-scan/code-scan.js` | `+17/-3` (3 hunk — `@header` description · 상수 · `classifyUncovered`) |

그 외 파일 무변경 — `code-map-hook.js`·`state_tool.py`·테스트 12파일·`header-standard.md`·`~/.opal/` 전건 미접촉.

## 검증 결과

### RED 증거 (개정 전 코드 실관측)

`git show HEAD:opal/tools/code-scan/code-scan.js` 복원본으로 재현:

```
validate: 1 violation(s) — coverage 0% (0/1)     exit=2
counts.newly_uncovered = 1
violations = [{code:"uncovered", sub:"newly_uncovered", file:"opal/tools/state-tool/tests/test_state_tool.py"}]
```

DONE.md §9가 기록한 차단이 그대로 재현됐다.

### before / after

**재현 케이스** (`validate --changed test_state_tool.py`)

| | covered | newly_uncovered | exit |
|---|---|---|---|
| BEFORE (8192·문자) | 0/1 (0%) | **1** | **2** |
| AFTER (24576·바이트) | 1/1 (100%) | **0** | **0** |

**실제 CLOSE 게이트 (b) 전체** — PM 독립 실측(변경 파일 전체 투입)

| | coverage | newly_uncovered | 차단 위반 | exit |
|---|---|---|---|---|
| BEFORE | 2/12 | **1** | 1 | **2 (차단)** |
| AFTER | 3/11 | **0** | **0** | **0 (통과)** |

→ **106 §9의 캡틴 승인 우회가 이제 불필요하다.** 남은 항목은 전부 `pre_existing`(md 문서·README — 비차단).

**8192 초과 3건 전건 `covered` 전환** (PM `scan --json` 실측)

| 파일 | 블록 종료 (바이트/문자) | BEFORE | AFTER |
|------|----------------------|--------|-------|
| `state_tool.py` | 17811 / 12315 | 미파싱 → `pre_existing` | **covered** (`module=state_tool`) |
| `test_state_tool.py` | 11204 / 8362 | 미파싱 → **`newly_uncovered`** | **covered** (`module=test_state_tool`) |
| `dashboard/backend/tests/test_routers.py` | 8567 / 6649 | 미파싱 → **`newly_uncovered`** | **covered** (`module=tests.test_routers`) |

전 스코프 `validate`: `covered 106 → 109`(정확히 +3) · `newly_uncovered 2 → 0`.

### 멀티바이트 경계 절단 (U+FFFD) — 무해 확인

- **두 창문 바이트 동일성**: 레포 **1629파일 전수** 대조 → `identical=1629 mismatch=0`. 두 경로가 같은 단위·같은 내용의 창문을 본다.
- **U+FFFD는 가상 사례가 아니다** — 실제 발생 파일 **61건**. 61건 전수에서 U+FFFD가 항상 창문 **말미 3자 내**에만 나타난다.
- **오탐·미탐 0건** — 경계가 한글 문자 중간에 놓이도록 정밀 제어한 픽스처 3종 E2E:
  - `c1`(블록이 창문 안에서 종료): 말미 U+FFFD 있어도 정상 파싱 → **covered**. 절단 문자가 `raw` 범위(닫는 `}` 이전) 밖이다
  - `c3`(경계가 JSON 블록 **내부**): 닫는 `}`가 창문 안에 없어 `end === -1`로 정상 null 반환. U+FFFD가 중괄호로 오인되지 않는다
- **구조적 근거**: JSON 구조 문자 `{ } " \`는 전부 1바이트 ASCII이므로 절단으로 생성·소멸·분할될 수 없다. 새 실패 양식을 도입한 것이 아니라 HEAD 경로를 라이브 경로의 기존 동작에 맞춘 것이다.

### 회귀 · 성능 (opds 검증 규범: lint + build + 관련 테스트)

- **`code-scan` 테스트 12파일: `TOTAL pass=340 fail=0`** — 개정 전 baseline과 완전 동일(PM 독립 재실행). `test-validate.js` git 2분류 회귀 5건 포함 전건 통과 → 단위 통일이 2분류 계약을 깨지 않는다.
- **성능 저하 없음**: `scan` 전 스코프 avg 115ms → **111ms** / `validate --full` avg 4642ms → **4533ms**. 파일당 읽기가 3배(8KB→24KB)지만 node 기동(~70ms)과 `validate`의 `git show` 팬아웃이 지배하며, 24KB 단발 `readSync`는 페이지 캐시에서 8KB와 사실상 동일 비용이다.
- `state-tool` 테스트도 영향 없음 확인(383 passed 유지).

## PM 판단 오류 1건 (기록)

**`VERSION` 상향을 시도해 테스트 5건을 깨뜨렸다가 되돌렸다.**

- 워커는 변경이력 항목 추가를 3가지 근거로 유보하고 PM 판정을 요청했다 — 그중 (ii)가 "이력 행 추가는 `VERSION` 상수 상향을 동반해야 일관되나 지시에 없다"였다.
- PM이 `CONVENTIONS.md` §@header 규칙 `:218`("변경이력은 … **헤더 내 변경이력 라인**으로 갱신한다")을 근거로 워커 판단을 뒤집고 `VERSION` 1.6.0 → 1.7.0 + 변경이력 항목을 추가했다.
- 결과: `test-shard-policy.js:1519` TS-090/097과 `test-shard.js:696` S-22가 **`VERSION === '1.6.0'`을 핀**하고 있어 실패하고, 그 2건에 의존하는 메타 테스트 3건(TS-080·S-19·TS-062)이 연쇄 실패 → **340/0 → 335/5**.
- **되돌렸다.** 워커의 판단이 옳았다 — `VERSION` 상향은 083이 고정한 단언 2건의 갱신을 동반하며, 그것은 Step 15의 `ERROR_CODES` 종수 문제와 같은 계열의 별개 작업이다. 되돌린 후 **340/0 회복** 확인.
- 교훈: **워커가 근거를 들어 유보한 항목을 뒤집을 때는 그 근거를 먼저 반증해야 한다.** (ii)는 실측으로 검증 가능한 주장이었고, 확인하지 않고 진행한 것이 원인이다.

## 이월 (DONE.md §8에 추가)

| # | 항목 | 심각도 |
|---|------|--------|
| 1-a | **이 결함의 회귀 테스트 미신설** — 기존 12파일 어디에도 문자/바이트 비대칭을 검출하는 케이스가 없다(`test-validate.js` git 2분류 테스트는 전부 ASCII 픽스처라 구조적으로 불가). 필요한 RED 명세는 위 c1/c2/c3 형태로 확정되어 있다. **H-9 검증 2원화**에 따라 구현자가 작성하지 않았다 | **높음** |
| 1-b | **`code-scan.js` 변경이력 항목 + `VERSION` 상향** — 083이 `VERSION === '1.6.0'`을 테스트 2건에 핀했으므로 상향은 단언 갱신을 동반한다. DONE.md §8-4(변경이력 A안 충돌)와 함께 다뤄야 한다 | 중 |
| 1-c | **`description` 압축의 대가** — `code-scan search`가 `description` 본문을 검색하므로 1542자를 덜어낸 만큼 이 파일의 키워드 적중면이 줄었다. 계약 불변식은 `note` 필드(1712자)에 남아 유실은 아니나, DONE.md §8-2(헤더 압축 전략)에서 규율로 다룰 사안 | 낮음 |

## 미수행

- **재배포** — `~/.opal/tools/code-scan/code-scan.js`가 개정 전(8192·문자)이다. **CLOSE 게이트와 PostToolUse 훅이 실제로 호출하는 것은 배포본**이므로 재배포 전까지 결함은 런타임에 살아 있다. 106의 Step 17·18·19 + ADD-1이 모두 배포 대기 상태다.
- **커밋** — 캡틴이 "ADD-1 끝나면 커밋"으로 지시했으므로 이 문서 작성 직후 수행한다.
