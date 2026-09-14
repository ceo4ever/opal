# code-scan

> 코드 파일의 `@header` 메타블록을 스캔·조회·검증·기록하는 15서브명령 CLI
> 소스: `opal/tools/code-scan/` | 배포: `~/.opal/tools/code-scan/`
> 의존성: Node.js 18+ (외부 패키지 0건)

## 개요

`code-scan`은 `@header` 메타블록을 축으로 프로젝트 구조를 조회하고, 헤더 기록 위치를 판정하고, 무결성을 검증한다. 15개 서브명령은 네 층으로 나뉜다.

| 층 | 서브명령 |
|----|---------|
| 조회 8종 | `scan` `domain` `layer` `search` `exports` `summary` `depends` `missing` |
| 헤더 작성층 | `discover` `scaffold` `target` `validate` `feature` |
| 매니페스트 분할층 | `split` |
| 설정 창구 | `init` |

## 호출 형식

```bash
~/.opal/tools/code-scan/run.sh <command> [options]          # 권장
node ~/.opal/tools/code-scan/code-scan.js <command> [options]  # 하위호환
```

`run.sh`는 `OPAL_NODE_BIN`(기본 `node`)으로 `code-scan.js`를 실행하는 얇은 래퍼다. `node`가 PATH에 없으면 `{"ok":false,"error":"node_missing",...}`를 **stdout**에 출력하고 exit 1한다.

메타 출력 2종은 설정 없이도 동작한다.

```bash
~/.opal/tools/code-scan/run.sh help       # 사용법 (현재 v1.6.0)
~/.opal/tools/code-scan/run.sh version    # 버전 문자열
```

`--help`/`-h`는 `help`와, `--version`/`-v`는 `version`과 같다. **인자를 하나도 주지 않으면 사용법을 출력하고 exit 0**으로 끝난다.

## 전 명령 차단 게이트 — 헤더 소스

`headerSource`는 **전역 단일 키**이며 유효값은 `inline`과 `manifest` 2택이다. 설정에도 없고 `--header-source`도 없으면 **조회 명령까지 포함해 전 명령이 exit 1로 거부된다.**

**게이트에서 면제되는 것은 `help`/`version`/`init` 셋뿐이다.** `init`은 "headerSource가 없는 상태를 고치는 명령"이라 게이트 **앞**에 배치돼 있다 — 뒤에 두면 설정이 없어 `init`이 거부되고, `init`을 못 돌려 설정을 못 만드는 순환이 생긴다. 나머지 명령의 차단 동작은 조금도 완화되지 않는다.

실패 시 **stdout에는 기계 판독용 JSON**(`{"ok": false, "error": ..., "detail", "where", "fix", "doc"}`), **stderr에는 사람용 안내**가 함께 나간다.

## 프로젝트 설정 — `.opal/code-scan.json`

```json
{
  "headerSource": "inline",
  "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue"],
  "exclude": ["node_modules", "__pycache__"],
  "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
}
```

`scopes`의 각 값은 경로 문자열 축약형 또는 `{path, include, exclude}` 객체형이다. 객체형은 스코프가 관리하는 **파일 집합**을 좁힐 때 쓴다.

```json
{
  "headerSource": "manifest",
  "scopes": {
    "be": { "path": "workspace/backend/", "include": ["app/**"], "exclude": ["app/legacy/**"] },
    "fe": "workspace/frontend/src/"
  }
}
```

- **스코프별 헤더 소스 재선언은 없다** — `scopes` 안에 헤더 소스 키를 넣어도 무시되며 stderr 안내 1줄만 나온다. `.opal/code-map/index.json`의 스코프에도 두지 않는다. `include`/`exclude`는 파일 집합 필터일 뿐 기록 소스와 무관하다.
- 세 번째 값 `auto`는 제거됐다. 설정에 남아 있으면 `header_source_invalid`로 거부되며 마이그레이션 힌트가 출력된다(**자동 변환은 하지 않는다**).
- 실행 단위로 다르게 쓰려면 설정을 고치지 말고 `--header-source`로 그 실행만 덮어쓴다.

### 모드별 동작

| 모드 | 조회 8종 | `scaffold` | `validate` |
|------|---------|-----------|-----------|
| `inline` | 파일 내 인라인 `@header` 단독 | **no-op** — 매니페스트를 만들지 않고 `skipped` 사유만 보고하며 exit 0 | 인라인 커버리지만 계상. 매니페스트 구조 검사 스킵(자산이 있으면 stderr 안내 1줄) |
| `manifest` | `.opal/code-map/` 매니페스트 4단 상속(`files` → `package` → `layerRules` → `domains`) | 매니페스트 생성/갱신 | 매니페스트 커버리지만 계상 + 구조 검사 수행. `index.json` 부재 시 결과가 비고 stderr 안내 1줄(비차단) |

두 모드는 상호 배타이므로 **인라인 + 매니페스트 합산 커버리지는 존재하지 않는다.**

## 15개 서브 명령

```bash
# ── 조회 8종 ────────────────────────────────────────────────
scan [path] [--scope <name>]   # 전체 스캔 (scope 미지정 시 프로젝트 전체)
domain [name]                  # 도메인별 조회 (인자 없으면 목록)
layer [name]                   # 레이어별 조회 (인자 없으면 목록)
search <pattern>               # 헤더 내 패턴 검색 (정규식, 대소문자 무시)
exports <pattern>              # exports 필드 전용 검색 (정규식, 대소문자 무시)
summary                        # 도메인/레이어 요약
depends <module>               # 의존 관계 추적
missing                        # @header 없는 파일 목록

# ── 설정 창구 ───────────────────────────────────────────────
init --header-source <inline|manifest> [--write] [--force] [--json]

# ── 헤더 작성층 ─────────────────────────────────────────────
discover [--out <path>] [--dry-run]     # .opal/code-map/index.json 초안 추론
scaffold [--dry-run]                    # 패키지 매니페스트 생성/갱신 (멱등 보존 merge)
target <file>                           # 파일의 @header 기록 위치 판정
validate [--changed <csv|->]            # code-map 무결성 검증
feature <id> [--scope <name>]           # 기능 태그 기준 cross-scope 조회

# ── 매니페스트 분할층 ───────────────────────────────────────
split <manifest> --plan [--out <path>] [--trace] [--stop-after <S1..S5>]
split <manifest> --groups <path|-> [--dry-run]
```

`search`/`exports`/`depends`/`target`/`feature`는 인자가 없으면 `Usage: ...`를 stderr에 출력하고 exit 1한다.

### `init` — 설정 초안 (비대화형)

프롬프트·TTY 의존이 0건이다. **`headerSource`를 추론하지 않고 인자로 받는다** — `--header-source`가 없으면 `init_header_source_required`로 거부하며 **파일을 만들지 않는다.** 기본은 stdout 초안 출력이고, `--write`를 줘야 실제로 쓴다. 기존 설정이 있으면 `--force` 없이는 `config_exists`로 거부하며, `--force` 시 `*.json.bak`로 백업한 뒤 덮어쓴다.

### `scaffold` — 매니페스트 생성/갱신

기존 워커 기입값을 유지하는 멱등 보존 merge다. `inline` 모드에서는 no-op(exit 0 + `skipped` 사유). 베이스가 선언한 샤드(`_shards/{label}.json`)는 보존·버킷 분배되고, 소스 디렉토리명이 예약 폴더 `_shards`와 겹치면 `reserved_name_collision`으로 exit 1한다. 여러 디렉토리가 같은 매니페스트 경로로 미러되면 `mirror_collision`으로 exit 1한다. `manifest` 모드인데 `index.json`이 없으면 `index_missing`이다.

### `target` — 기록 위치 판정

**전역 `headerSource`에 직결된다** — 파일 상태나 인라인 보유 여부를 보지 않는다. 두 필드는 서로 다른 축이며 한 목록으로 섞어 나열하지 않는다.

| `write_to`(기록 위치 축) | `reason`(판정 사유 축) | 비고 |
|--------------------------|------------------------|------|
| `inline` | `header_source_inline` | |
| `manifest` | `header_source_manifest` | **이 조합에서만** `scope`·`manifest`·`key` 부가 필드가 동반된다. 보유 샤드가 있으면 `manifest`가 그 샤드 경로를 가리키고 `shard` 필드에 라벨이 실린다 — 없으면 베이스로 라우팅되어 `shard` 필드가 없다 |
| `none` | `out_of_scope` | 스코프 `include`/`exclude` 필터 탈락. **모드 판정보다 먼저** 적용된다 |

실제 조합은 위 3쌍으로 닫힌다. 베이스 매니페스트가 파손돼 있으면 `manifest_parse_failed`로 exit 1한다.

### `validate` — 무결성 검증

위반 5종(`orphan`/`conflict`/`draft`/`exports_not_found`/`worker_scope_violation`) + `uncovered` + 모드별 단일 소스 커버리지를 본다. `--changed`로 영향 범위를 한정할 수 있다(쉼표 목록 또는 `-`로 stdin 개행 목록).

**`uncovered` 2분류 (git 기준)** — 인라인·code-map 어디에도 `@header`가 없는 파일은, **매니페스트가 관리하지 않는 디렉토리에 한해** git 상태로 재분류된다. 매니페스트가 해당 디렉토리를 scaffold 중인데 파일이 `files{}` 키에서 빠진 경우는 git과 무관하게 항상 `sub: 'no_entry'`(차단)다.

| `sub` | 조건 | 차단 여부 |
|-------|------|----------|
| `newly_uncovered` | git 기준 신규 파일(untracked/added), 또는 HEAD엔 `@header`가 있었는데 현재 없음(회귀) | 차단(exit 2) |
| `pre_existing` | HEAD 버전에도 `@header`가 없던 기존 파일 | **비차단**(exit 0) — `counts.pre_existing`·`violations[]`에 목록만 노출 |

git을 쓸 수 없는 환경(git 미설치·비git 트리)에서는 전량 `pre_existing`으로 처리하고 stderr에 경고 1줄을 낸다(비차단). 다른 5종 위반의 차단 성격은 이 재분류와 무관하게 유지된다.

샤드 선언 시 구조 검사는 **베이스 + 전 샤드 합집합** 기준으로 수행되며, 매니페스트 바이트 상한 초과는 `counts.manifest_oversize`로 열거만 하고 차단하지 않는다.

### `split` — 매니페스트 분할 (manifest 모드 전용)

`inline` 모드에서 호출하면 조용한 성공 없이 `split_inline_mode`로 거부한다.

- `--plan`은 **매니페스트를 한 바이트도 쓰지 않는다**(`--out`을 주면 groups 문서 1개만 쓴다).
- `--groups`는 4단 원자적 처리를 거친다: 사전 불변식 검사 → tmp 전량 작성 → rename 커밋 → 캐시를 비우고 재검증. 재검증은 `resolveShards`를 다시 호출해 해석 로직을 복제하지 않는다. 집행의 계약은 **엔트리 유실 0건**이다.
- `--plan`의 출력 스키마 = `--groups`의 입력 스키마다(왕복 성립) — 제안 문서를 편집만 해서 그대로 집행에 넣을 수 있다.

**분할 절차**

| 단계 | 명령 | 수행자 |
|------|------|--------|
| ① 탐지 | `validate` → `counts.manifest_oversize` + 위반의 `next` 확인 | 도구 |
| ② 제안 | `split <manifest> --plan --out <groups.json>` | 도구 |
| ③ 편집 | `groups.json`의 라벨·파일 배분 확정 | 사람/워커 |
| ④ 집행 | `split <manifest> --groups <groups.json>` (선행 `--dry-run` 권장) | 도구 |
| ⑤ 재검증 | `validate` — 집행 직후 도구가 자동 재검증하며, 절차상 한 번 더 확인 | 도구 |

**제안 사다리 5단계** — 각 단계는 직전 단계의 미분류분만 입력으로 받고, 앞 단계의 배정은 재배정되지 않는다.

| 단계 | 신호 | 사전 대조 | 채택 임계 |
|------|------|----------|----------|
| S1 | 파일명 첫 토큰 | 표준단어사전 | 2건 이상 |
| S2 | 1~2번째 토큰 결합 | 표준단어사전 | 2건 이상 |
| S3 | 전체 토큰 중 매칭 | 표준단어사전 | 2건 이상 |
| S4 | 마지막 토큰(역할축) | 없음(빈도) | 3건 이상 |
| S5 | `depends` 공유 | 없음 | 3건 이상 |

잔여는 `unassigned`로 남긴다 — **도구는 임의 배분도, "기타" 그룹 생성도 하지 않는다.** 검토 장치 3종: `--trace`(단계별 입력 → 걷음 → 잔여 표), `--stop-after <S1..S5>`, 엔트리별 `stage` 필드.

**표준단어사전 연동**(옵셔널, `split --plan` 전용): 탐색 3단은 ① `shardPolicy.dictPath` → ② `docs/PROJECT.md`의 `{설계}` 변수 해소(`{설계}/사전/표준단어사전.md`) → ③ 기본 경로다. 폴백 3분기가 전부 비차단이다 — **부재는 침묵**(S1~S3 skip), **파싱 실패는 안내 1줄**, **매칭 0건은 정상 통과**. 프로젝트 루트 밖 경로와 크기 상한 초과 사전은 "사전 없음"으로 취급한다. 사전 md는 `## 수식어`(6열)·`## 분류어`(5열) 두 표를 **헤더 이름 기반**으로 읽는다(열 수가 다른 두 표를 위치로 읽으면 조용히 오분류되기 때문). 읽기 전용이며 호출 지점은 `split --plan` 1곳뿐이라 조회 8커맨드의 출력이 사전 유무로 흔들리지 않는다.

## 매니페스트 샤딩 (manifest 모드 전용)

베이스 매니페스트가 `shards` 배열로 라벨을 선언하면, 예약 폴더 `{베이스 경로 stem}/_shards/{label}.json` 아래로 파일 엔트리를 의미 단위로 분산할 수 있다. 조회·기록 위치·구조 검증은 **베이스 + 전 샤드 합집합을 단일 소스**로 취급한다(첫 선언 우선, 중복은 위반). `shards`를 선언하지 않은 매니페스트는 기존과 완전히 동일하게 동작한다(하위호환, 옵트인).

```jsonc
// 베이스 매니페스트 — shards 키 1개만 추가
{ "version": 1, "scope": "svc", "dir": "svc/order-api/src/...",
  "shards": ["order-core", "order-pricing"], "files": { "...": "..." } }
```

### 샤드 정책 `shardPolicy` — 3단 우선순위

읽는 지점은 코드에 `resolveShardPolicy` **1곳**으로 봉인돼 있다(실행당 1회 확정).

```
{프로젝트}/.opal/code-scan.json 최상위 shardPolicy
  > ~/.opal/setting.json 전역 shardPolicy
  > 코드 내장 상수 (maxBytes 10240 / minFiles 40)
```

- **셀 단위 머지**다 — 프로젝트에 한 키만 적으면 나머지는 하위 단계에서 온다.
- 전역 설정의 부재·파싱 실패·키 부재·타입 위반은 **전부 비차단 폴백**(무시 + stderr 안내 후 하위 단계 값 사용). **프로젝트** 설정의 타입 위반만 `code_scan_config_invalid`로 exit 1한다.
- 홈 경로는 `OPAL_HOME` 환경변수로 주입할 수 있다(테스트 격리용).
- `shardPolicy.dictPath`(선택)는 표준단어사전 경로 명시값이다. **`shardPolicy.ladder` 설정 노출은 범위에서 제외됐고 사다리 임계값은 현재 코드 상수다.**

**2축 판정** — `manifest_oversize` 열거 조건은 **바이트 초과 AND 엔트리 수 이상**이며 경계 규칙이 비대칭이다(바이트는 `>`, 엔트리는 `>=`). 상한 초과는 `validate`/`scaffold` 모두 **전면 비차단**이다 — 다른 위반이 없으면 exit 0이다. 위반 페이로드에는 `entries`·`minFiles`·`recommendedShards`·`next`(다음에 실행할 `split --plan` 명령) 4필드가 실리고 `detail` 포맷(`{bytes}/{maxBytes}`)은 불변이다.

**폐기 안내** — 구 위치 `.opal/code-map/index.json`의 `manifestMaxBytes`는 폐기됐다. 도구는 그 **값을 읽지 않고** 실행당 1회 안내만 하며(비차단), **자동 변환도 하지 않는다** — 새 주소 `shardPolicy`로 직접 옮겨 적어야 한다.

## 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--header-source <inline\|manifest>` | 이 실행의 **전역 모드**를 지정한다. 설정 파일 값보다 우선하며 전 명령 공통 |
| `--scope <name>` | 스코프 필터 (`.opal/code-scan.json`의 `scopes` 키) |
| `--domain <name>` | 도메인 필터 |
| `--layer <name>` | 레이어 필터 |
| `--exclude <patterns>` | 제외 패턴 (쉼표 구분, `*`·`?` 와일드카드). 설정의 `excludePatterns`와 **병합**된다 |
| `--out <path>` | `discover`: 초안 출력 경로(기본 `.opal/code-map/index.json`) · `split --plan`: groups 문서 출력 경로(플래그를 새로 만들지 않고 공유) |
| `--dry-run` | `discover`/`scaffold`/`split --groups`: 파일 쓰기 없이 결과만 계산 |
| `--write` | `init`: `.opal/code-scan.json`을 실제로 쓴다(기본은 stdout 초안만) |
| `--force` | `init`: 기존 설정을 덮어쓴다(`*.json.bak` 백업 후) |
| `--changed <csv\|->` | `validate`: 쉼표 목록 또는 stdin 개행 목록으로 검증 범위 한정 |
| `--plan` | `split`: 분할 그룹 제안(`--groups`와 배타) |
| `--groups <path\|->` | `split`: groups 문서(파일 경로 또는 stdin)로 분할 집행 |
| `--trace` | `split --plan`: 사다리 단계별 표 출력 |
| `--stop-after <Sn>` | `split --plan`: 사다리를 `S1`~`S5` 중 지정 단계에서 중단 |
| `--brief` | 한 줄 요약 출력 (기본값) |
| `--full` | 전체 헤더 JSON 출력 |
| `--json` | 파이프용 raw JSON 출력 |

제외 패턴은 기본적으로 파일명에 매칭하며, 패턴에 `/`가 들어 있으면 경로에 매칭한다.

## 오류 코드

소스에 단일 `ERROR_CODES` 카탈로그 상수는 없다. 아래는 `errorExit()`과 `CodeMapFatalError`의 실제 방출 지점을 전수 확인한 목록이며 **전부 exit 1**이다.

### 헤더 소스·설정 (전 명령 공통)

| 코드 | 조건 |
|------|------|
| `header_source_unset` | 설정에 `headerSource`가 없고 `--header-source`도 없음 |
| `header_source_invalid` | `headerSource` 값이 `inline`/`manifest` 밖 — 폐기된 `auto`가 남아 있으면 `migration` 힌트 동반(자동 변환 없음) |
| `code_scan_config_invalid` | `.opal/code-scan.json` 파손(파싱 실패·`scopes` 스키마 위반·프로젝트 `shardPolicy` 타입 위반) |
| `scope_ambiguous` | 스코프 귀속 판정이 모호 — 동률 root에서 둘 이상의 스코프 `include`가 동시 매칭 |

`header_source_unset`·`header_source_invalid`·`code_scan_config_invalid` 3종의 `fix` 안내에는 `code-scan init` 복구 경로가 함께 실린다(차단 동작 자체는 완화되지 않는다).

### `init` 전용

| 코드 | 조건 |
|------|------|
| `init_header_source_required` | `--header-source`가 없음 — 2택을 추론하지 않으며 **파일을 만들지 않는다** |
| `config_exists` | `.opal/code-scan.json`이 이미 있고 `--force`가 없음 — 원본 불변 |

### 매니페스트 (`discover`/`scaffold`/`target`/`validate`/조회 8종에서 개별 발생)

| 코드 | 조건 |
|------|------|
| `index_exists` | `discover` — `--dry-run` 없이 출력 경로에 파일이 이미 존재 |
| `index_missing` | `scaffold` — `manifest` 모드인데 `.opal/code-map/index.json`이 없음 |
| `invalid_index` | `index.json`이 파싱 실패·구조 위반 |
| `unsupported_version` | 매니페스트 `version`이 지원 범위 밖 |
| `manifest_parse_failed` | 베이스 매니페스트 파손 |
| `mirror_collision` | 둘 이상의 소스 디렉토리가 같은 매니페스트 경로로 미러됨 |
| `shard_declaration_invalid` | `shards`가 배열이 아니거나, 라벨이 kebab 정규식 불일치·중복 선언 |
| `reserved_name_collision` | `scaffold` 대상 소스 디렉토리 이름이 예약 폴더 `_shards`와 충돌 |

### `split` 전용 — 실패 지점별 쓰기 상태가 다르다

| 코드 | 조건 | 쓰기 상태 |
|------|------|----------|
| `split_usage_invalid` | `--plan`/`--groups` 동시 지정·둘 다 없음·매니페스트 인자 누락·`--stop-after` 값 오류 | 무쓰기 |
| `split_inline_mode` | `inline` 모드에서 호출 | 무쓰기 |
| `split_target_invalid` | 대상 매니페스트가 부재·파손·샤드 파일 자체를 지목 | 무쓰기 |
| `split_groups_invalid` | groups 문서가 파손·라벨 규칙 위반·중복·베이스에 없는 파일 지목 | 무쓰기 |
| `split_write_failed` | tmp 전량 작성 단계 실패 | 원본 불변(tmp만 정리) |
| `split_rollback` | rename 커밋 단계 실패 → 원상 복구 수행 | 원본 복구 완료 |
| `split_verify_failed` | 커밋 후 재검증에서 정합 붕괴 감지 | 커밋된 상태 + 진단 노출 |

### 래퍼

| 코드 | 조건 |
|------|------|
| `node_missing` | `run.sh`가 `OPAL_NODE_BIN`(기본 `node`)을 찾지 못함 |

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 정상 종료 — `validate`는 **차단 위반 없음**(`uncovered:pre_existing`만 있는 경우와 `manifest_oversize`만 있는 경우 포함) |
| `1` | 사용법 오류 / 스키마 오류 / 헤더 소스 미해결 / 위 오류 코드 전건 / 알 수 없는 서브명령 / 알 수 없는 `--scope` |
| `2` | **`validate` 전용** — 차단 위반 발견 |

exit 2를 내는 명령은 `validate` 하나뿐이다(`process.exit(ok ? 0 : 2)`). 다른 명령은 0 또는 1로만 끝난다.

## 사용 예시

```bash
# BE 스코프 도메인 요약
~/.opal/tools/code-scan/run.sh summary --scope be

# auth 모듈 의존 관계 추적
~/.opal/tools/code-scan/run.sh depends auth

# @header 누락 파일 확인
~/.opal/tools/code-scan/run.sh missing --scope fe

# 헤더 내 패턴 검색 (정규식, 대소문자 무시)
~/.opal/tools/code-scan/run.sh search "auth.*service"
~/.opal/tools/code-scan/run.sh search "login|logout"

# exports 필드 전용 검색
~/.opal/tools/code-scan/run.sh exports "^get[A-Z]"

# 단일 파일 스캔 (파이프용 JSON)
~/.opal/tools/code-scan/run.sh scan src/auth/auth.service.ts --json

# 설정 초안 생성·복구
~/.opal/tools/code-scan/run.sh init --header-source manifest --write
~/.opal/tools/code-scan/run.sh init --header-source manifest --write --force

# 이 실행만 다른 모드로
~/.opal/tools/code-scan/run.sh validate --header-source inline

# 변경 파일로 검증 범위 한정
git diff --name-only | ~/.opal/tools/code-scan/run.sh validate --changed -
```

## 워크트리 실행 안내

cwd가 `.opal-worktrees` 안이고 판정된 프로젝트 루트는 그 밖(허브)이면, 실행당 1회 **stderr로만** 안내를 낸다 — 허브 작업트리의 파일만 읽었으므로 위반 보고도 통과도 그 워크트리 수정에 대한 판정이 아니라는 경고다. **stdout(JSON)에는 한 바이트도 더하지 않는다** — 허브 실행과 워크트리 실행의 stdout이 바이트 동일해야 소비자와 회귀 단언이 유지되기 때문이다.

## 제약

- 헤더 소스 미해결은 **조회 명령까지** 차단한다 — 읽기 전용 명령이라고 통과하지 않는다.
- `inline` 모드에서 `scaffold`는 no-op, `split`은 거부다.
- `--plan`과 `--groups`는 배타다(동시 지정 시 `split_usage_invalid`).
- `discover`는 `--dry-run` 없이 출력 경로에 파일이 있으면 덮어쓰지 않고 `index_exists`로 거부한다.
- 표준단어사전은 분할의 전제조건이 아니다 — 없으면 S1~S3을 건너뛸 뿐 실패하지 않는다.
- `code-scan`은 `~/.opal/setting.json`을 읽는 첫 도구다. 전역 설정 문제는 전부 비차단 폴백이므로, 의도한 `shardPolicy`가 적용됐는지는 stderr 안내를 함께 봐야 한다.
