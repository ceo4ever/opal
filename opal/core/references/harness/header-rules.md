# EXECUTE @header 규칙

> 출처: opal-harness.md §8
> 로드 시점: EXECUTE 단계에서 코드 파일 생성/수정 시
> 역할: @header 작성 규칙 + code-scan 활용 가이드

---

## 8. EXECUTE @header 규칙

> **트리거**: 코드 파일 생성/수정 시. code-scan 지원 확장자 파일에만 적용.
> **작성 주체**: 워커(LLM)가 값을 기입한다. `code-scan`(`discover`/`scaffold`/`target`/`validate`)이 초안 생성·기록 위치 판정·기입 검증을 보조한다 — 도구는 구조를 만들고 워커는 내용을 채운다.

### 기록 위치 판정 (3단)

파일을 생성·수정할 때 어디에 @header를 기록할지는 `code-scan target <file>`이 판정한다. 판정 순서는 아래 표를 따르며, 조건 ①→②→③ 순으로 첫 매칭이 승리한다.

| # | 조건 | `write_to` | `reason` |
|---|------|-----------|----------|
| ① | 소속 스코프의 `include`/`exclude` 필터에서 탈락 (관리 대상 아님) — **모드 판정보다 먼저 평가된다** | `none` | `out_of_scope` |
| ② | 프로젝트 모드(CLI `--header-source` > 전역 `.opal/code-scan.json`, 우선순위 2층) = `inline` | `inline` | `header_source_inline` |
| ③ | 프로젝트 모드 = `manifest` | `manifest` | `header_source_manifest` |

- ①이 모드 판정보다 먼저인 이유는 반환 계약과 같다 — 관리 대상이 아닌 파일에는 기록 위치 자체가 존재하지 않는다. 스코프 미설정 · `include`/`exclude` 미사용 · 스코프 root 밖 파일에서는 ①이 발동하지 않는다.
- `reason`은 이 **3값**(`out_of_scope`/`header_source_inline`/`header_source_manifest`) 외를, `write_to`는 이 **3값**(`none`/`inline`/`manifest`) 외를 반환하지 않는다. 실제 조합은 위 3행으로 닫히며, 파일 존재 여부·인라인 보유 여부는 판정 근거가 아니다.
- 기록 소스를 결정하는 키는 `.opal/code-scan.json`의 **전역 `headerSource`** 하나뿐이다. 스코프 단위 모드 선언 키는 존재하지 않으며(설정 시 무시 + stderr 안내 1줄), 스코프 단위 쓰기금지 플래그도 제거되었다.
- code-map이 없는 프로젝트는 `headerSource: inline`으로 설정하며, 결과는 항상 `inline`이다 — 현행 규칙(파일 인라인 작성)과 동일하게 동작한다. `manifest` 모드인데 `.opal/code-map/index.json`이 없으면 조회 결과가 비고 stderr에 사유 1줄이 나온다(비차단).
- `write_to`가 `manifest`인 경우에만 `scope`·`manifest`·`key` 부가 필드가 함께 실린다 — 워커는 그 매니페스트의 `files[key]` 항목에 값을 기입한다.
- 베이스 매니페스트가 `shards`를 선언한 파일은 `manifest`가 보유 샤드 경로를 가리킨다(부가 필드 `shard`에 라벨 동반) — 보유 샤드가 없으면 베이스로 라우팅된다("보유 샤드 → 없으면 베이스").
- 전역 `headerSource`가 미설정이거나 유효 2택(`inline` 또는 `manifest`) 밖의 값이면 `target`을 포함한 **전 명령이 exit 1로 거부**된다(`header_source_unset` \| `header_source_invalid` \| `code_scan_config_invalid`). 판정 이전 단계이므로 이때는 기록 위치가 반환되지 않는다.

### 갱신 시점 (3단)

@header는 "작업 완료 후 일괄 갱신"하지 않는다 — 아래 3개 시점에서만 갱신한다.

| # | 시점 | 주체 | 수단 |
|---|------|------|------|
| (a) | 파일 변경과 **같은 자리에서** | 워커 | `target` 판정 결과에 따라 인라인 또는 매니페스트를 즉시 기록 |
| (b) | **CLOSE 진입 전** 게이트 | PM | `validate --changed <changed_files>` — exit≠0(`counts.newly_uncovered` ≥1건 또는 다른 위반 존재)이면 CLOSE 진입을 차단. `uncovered:pre_existing`(HEAD 버전에도 원래 헤더가 없던 레거시 파일)만 있으면 비차단(exit 0) — 레거시 소급 부여는 이 게이트가 아니라 `discover`/`scaffold`의 몫이다 |
| (c) | **PostToolUse hook** | 도구 | 파일 변경 감지 시 기록 위치 미갱신을 경고로 감지 |

**[MUST] 작업 완료 후 일괄 갱신 금지** — 여러 Step을 몰아서 마지막에 한 번에 @header를 채우는 방식은 금지한다. 각 Step에서 파일을 바꾸는 즉시 (a)를 수행한다.

### 워커 권한 경계

| 구분 | 필드 | 집행 |
|------|------|------|
| 허용 (워커 기입) | `description` · `exports` · `depends` · `note` · `feature` | - |
| 금지 (도구 관할) | `dir` · `files` 키 목록(추가/삭제) · `layer` · `domain` · `scope` · `module` · `version` · `shards` | `code-scan validate`가 `worker_scope_violation`으로 거부 |
| 금지 (파일 단위) | `.opal/code-map/index.json` 전체 | 소유자·PM 관할 — 워커 직접 편집 금지 |

워커가 금지 필드를 침범하면 `validate`가 `worker_scope_violation` 위반으로 exit 2를 반환한다. 인라인 `@header`의 `module`/`layer`/`domain`은 기존 규칙대로 워커가 작성하되(파일 단독 소스이므로 도구 관할 개념이 없음), 이 표는 **code-map 매니페스트**에 값을 기입할 때만 적용된다.

### 커버리지 산정 (모드별 단일 소스)

@header 커버리지는 설정된 모드의 **단일 소스**로만 계산한다 — `inline` 모드는 인라인 작성분만, `manifest` 모드는 매니페스트 작성분만 `covered`에 계상한다. 두 소스는 모드에 의해 상호 배타이므로 합산 개념이 없으며, 077의 합산 방식은 폐기되었다. `validate` 결과에는 어느 모드 기준의 커버리지인지가 함께 실린다.

`coverage.percent`(커버리지 %)는 `uncovered`의 `newly_uncovered`/`pre_existing` 2분류(§(b) CLOSE 게이트 참조)와 독립적인 지표다 — 두 서브 모두 "미작성"이므로 `covered`에 포함되지 않으며, 분류는 오직 CLOSE 게이트의 차단 여부에만 영향을 준다.

### 적용 대상 확장자

code-scan.js 기본 지원 확장자와 동일하다:

```
.py  .js  .ts  .jsx  .tsx  .vue  .svelte  .kt  .kts  .java  .swift
```

위 확장자 외 파일(예: `.json`, `.yaml`, `.md`, `.sh`)은 @header 작성 대상이 아니다.
단, 프로젝트 `.opal/code-scan.json`에 `.md`가 추가된 경우 md 파일도 적용 대상이 된다.

### 파일 생성 시

@header가 없는 신규 파일을 생성할 때, 워커는 언어에 맞는 주석 문법으로 @header를 파일 최상단에 작성한다.

- 포맷 표준: `~/.opal/references/header-standard.md` 참조
- 필수 필드: `module`, `layer`, `domain`, `description`, `exports`
- 선택 필드: `depends` (외부 의존 있을 때), `note` (특이사항 있을 때)

#### 테스트 파일 전용 선택 필드 (`layer: test`)

테스트 파일(`layer: test`)은 아래 선택 필드를 추가로 작성한다:

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `task` | string | 이 테스트가 처음 작성된 태스크 번호 | `"016"` |
| `scenarios` | list | 연결된 TEST-SCENARIO.md S-ID 목록 | `["S-1", "S-2", "S-7"]` |

### 파일 수정 시

기존 파일에 @header가 있으면, 변경된 내용에 따라 해당 필드만 갱신한다.

| 변경 내용 | 갱신 대상 필드 |
|----------|-------------|
| 함수/엔드포인트 추가 | `exports` |
| 파일 역할 변경 | `description` |
| 새 의존 모듈 추가 | `depends` |
| 레이어/도메인 이동 | `layer`, `domain` |

기존 파일에 @header가 없으면, 파일 생성 규칙과 동일하게 신규 작성한다.

### 주석 문법

언어별 주석 포맷은 `~/.opal/references/header-standard.md` §3을 따른다.

---

### code-scan 활용 가이드

PM·오케스트레이터·에이전트(비서)는 code-scan을 통해 프로젝트 구조를 파악한 뒤 필요한 파일만 선택적으로 Read한다.

#### 활용 시점

| 역할 | 활용 시점 | 권장 커맨드 |
|------|---------|-----------|
| 에이전트(비서) | 구조 파악 요청 / 파일 탐색 / 소유자 질문 응답 | `scan`, `domain`, `layer`, `search`, `exports` |
| PM(오케스트레이터) | TASK/PLAN 수립 전 도메인 파악, 디스패치 전 범위 확인 | `scan`, `domain`, `depends` |
| PM Gate | EXECUTE 완료 후 @header 검증 | `scan <file> --json` |

#### 활용 절차

1. `.opal/code-scan.json` 존재 여부 확인 → 없으면 PM이 자동 생성 (`code-scan-management.md §생성 시점` 참조) 후 진행
2. `code-scan scan <scope>` 로 전체 개요 파악
3. 필요 시 `code-scan domain <name>` / `code-scan layer <name>` 으로 범위 좁히기
4. 특정 기능 탐색: `code-scan exports <pattern>` (exports 필드 전용, 정규식 지원) 또는 `code-scan search <pattern>` (전체 필드, 정규식 지원)
5. 식별된 파일만 선택적으로 Read

#### 빈 결과 폴백

code-scan 결과가 충분하지 않을 때 아래 3분기 기준으로 대응한다.

| 분기 | 조건 | 대응 |
|------|------|------|
| ① 매칭 0건 | `search`/`exports` 결과 0건 | Glob/Grep **보강** (code-scan 결과 + 추가 탐색 병행) |
| ② 저커버리지 | `coverage.percent`(§커버리지 산정 — 설정된 모드의 단일 소스 기준) 30% 미만 | code-scan **+ Glob/Grep 동시** 활용 |
| ③ 정상 | 그 외 | code-scan 결과만 사용 |

**STATE 기록 규약**: 폴백(①②) 발동 시 STATE.md **자유 텍스트 영역**(블로커/다음 액션 — **현황판 표 행 아님, state-tool 비경유**)에 `code-scan 폴백: {사유}` 1줄을 기록한다.

[MUST] TASK §제약: "STATE.md 폴백 기록은 자유 텍스트 영역만 사용, 현황판 행 직접 편집 금지."

#### 적용 조건

`.opal/code-scan.json`이 존재하지 않으면 PM이 `code-scan-management.md §생성 시점`에 따라 즉석 자동 생성한 뒤 활용한다 — 미생성 상태로 직행 Glob/Grep 사용 금지. 이 파일은 PM이 디스패치 전 Read할 수 있는 경로: `opal/core/references/harness/header-rules.md`.

---

변경이력:

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "알투(비서)" → "에이전트(비서)" 치환 (139) |
| v1.1 | 2026-06-10 10:13 | 테스트 파일 선택 필드 task/scenarios 정의 추가 (016) |
| v1.2 | 2026-06-11 22:36 | §code-scan 활용 가이드 — 빈 결과 폴백 3분기 표 신설 + STATE 자유 텍스트 기록 규약 + §적용 조건 자동 생성 정합 (010) |
| v1.3 | 2026-07-28 14:20 | §8 작성 주체 문구를 도구 보조 + 워커 기입 구조로 교체 + 4단 기록 위치 판정 표·3단 갱신 시점 표(일괄 갱신 금지 명문화)·워커 권한 경계 표·커버리지 합산 정의 신설 + 빈 결과 폴백 저커버리지 기준을 합산 커버리지로 재정의 (077) |
| v1.5 | 2026-08-02 14:47 | 기록 위치 판정 4단 → **3단**으로 재정의 — `write_to` 3값(`none`/`inline`/`manifest`) × `reason` 3값(`out_of_scope`/`header_source_inline`/`header_source_manifest`) 폐쇄 도메인, 스코프 필터가 모드 판정보다 선행, 미설정·무효값 전 명령 거부 명시. `readonly` 판정 근거 서술 제거. §커버리지 합산 → §커버리지 산정(모드별 단일 소스)로 교체 + 빈 결과 폴백 ② 기준을 `coverage.percent`로 교정 (080) |
| v1.4 | 2026-07-28 23:28 | 3단 갱신 시점 표 (b) CLOSE 게이트 항목 — `uncovered` 2분류(`newly_uncovered` 차단/`pre_existing` 비차단) 반영, 레거시 소급 부여는 discover/scaffold 몫임을 명시. §커버리지 합산에 `coverage.percent`가 2분류와 독립 지표임을 명시하는 문단 추가 — Step 19 CLOSE 게이트 레거시 파일 차단 결함 재작업 (077) |
| v1.6 | 2026-08-03 13:20 | 매니페스트 샤딩 반영 — §워커 권한 경계 금지 필드에 `shards` 추가(도구·소유자 관할), §기록 위치 판정에 보유 샤드 경로 라우팅 1줄 추가("보유 샤드 → 없으면 베이스") (082) |
