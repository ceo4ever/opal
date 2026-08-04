# OPAL Tools

> OPAL 에이전트가 파일 처리, 데이터 변환 등 특정 작업 시 호출하는 CLI 도구 레지스트리.
> 새 도구 추가 시 이 파일에 등록하고 install-mac.sh의 `install_opal_venv()`를 통해 배포한다.

---

## xlsx-tool

**용도**: xlsx 파일 읽기, 쓰기, 검색, 메타데이터 조회  
**실행 경로**: `~/.opal/tools/xlsx-tool/run.sh`  
**소스 경로**: `opal/tools/xlsx-tool/`  
**의존성**: `~/.opal/.venv` (openpyxl, pandas)

### 커맨드

```bash
# 시트 목록, 행/열 수, 헤더 메타데이터 조회
~/.opal/tools/xlsx-tool/run.sh info <file>

# 데이터 읽기 (JSON 출력)
~/.opal/tools/xlsx-tool/run.sh read <file> [--sheet <name|index>] [--range <A1:Z100>] [--header-row <n>]

# 키워드 검색
~/.opal/tools/xlsx-tool/run.sh search <file> --keyword <text> [--sheet <name>] [--range <A1:Z100>]

# 데이터 쓰기 (신규 또는 수정)
~/.opal/tools/xlsx-tool/run.sh write <file> --data '<json>' [--sheet <name>] [--mode new|update] [--format]
~/.opal/tools/xlsx-tool/run.sh write <file> --data-file <path.json> [--sheet <name>] [--mode new|update] [--format]
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다.

```json
// 성공
{ "ok": true, "command": "read", "data": [...] }

// 실패
{ "ok": false, "command": "read", "error": "Sheet 'foo' not found" }
```

### 사용 예시

```bash
# 파일 구조 파악
~/.opal/tools/xlsx-tool/run.sh info project.xlsx

# 특정 시트 읽기
~/.opal/tools/xlsx-tool/run.sh read data.xlsx --sheet "2026"

# 키워드로 셀 찾기
~/.opal/tools/xlsx-tool/run.sh search wbs.xlsx --keyword "백엔드"

# JSON 데이터로 새 파일 생성 (서식 포함)
~/.opal/tools/xlsx-tool/run.sh write output.xlsx \
  --data '[{"이름":"홍길동","부서":"개발"}]' \
  --format

# 기존 파일의 특정 시트 업데이트
~/.opal/tools/xlsx-tool/run.sh write report.xlsx \
  --mode update --sheet "요약" \
  --data '[{"항목":"완료","수":"12"}]'
```

---

## state-tool

**용도**: STATE.md 파이프라인 현황판 JSON SSOT 관리 — 9개 서브 명령으로 행 상태 갱신, 검증, 추가작업 삽입  
**실행 경로**: `~/.opal/tools/state-tool/run.sh`  
**소스 경로**: `opal/tools/state-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `json`, `argparse`, `pathlib`, `subprocess`, `re`, `sys`, `datetime`, `os`)

### 커맨드

```bash
# state.json + STATE.md 신규 생성 (TASK 단계 시작 시)
~/.opal/tools/state-tool/run.sh init <task-path> \
  --skill <opp|opd|opds|opdw|opwt|opgc|oppd|opsdd> \
  --mode <interactive|agentic> \
  [--task-title <text>] [--next-action <text>] \
  [--rows-spec <inline-json>] [--rows-from <path-to-skill.md>] \
  [--force] [--note <text>] [--import-existing]

# 파이프라인 현황판 출력 (md/json/full)
~/.opal/tools/state-tool/run.sh show <task-path> [--format md|json|full]

# ⬜→🔄 전환 한정 (단계 시작 시)
~/.opal/tools/state-tool/run.sh advance <task-path> --row <N> [--note <text>]

# ⬜/🔄→✅ 전환 (단계 완료, Gate, 워커 Step 완료)
~/.opal/tools/state-tool/run.sh mark <task-path> \
  --row <N> --done \
  [--note <text>] \
  [--as-worker --worker-stage <stage>] \
  [--step <N/M>] \
  [--owner <PM|worker|user|auto>] \
  [--auto-pass] [--force]

# any→❌ + current_status=blocked
~/.opal/tools/state-tool/run.sh block <task-path> --row <N> --reason <text>

# 정합성 검증 (PM Gate 전 필수)
~/.opal/tools/state-tool/run.sh validate <task-path>

# 추가작업 행 삽입 (행 N 직후)
~/.opal/tools/state-tool/run.sh add-row <task-path> \
  --after <N> --stage <단계> --item <항목명> [--note <text>]

# current_status 명시 전환
~/.opal/tools/state-tool/run.sh status <task-path> \
  --set <in_progress|done|blocked|additional_work|additional_work_done> \
  [--note <text>]

# [deprecated] gate-pass — 레거시 전용. 신규 태스크는 PM Gate 통과 후 단일 mark 사용
# (State Gate/QA Gate 행이 제거되어 4행 패턴 성립 안 함 — Phase4 완료)
~/.opal/tools/state-tool/run.sh gate-pass <task-path> --start <N> [--note <text>]
```

### 출력 형식

모든 커맨드는 단일 라인 JSON으로 출력한다.

```json
// 성공
{"ok": true, "command": "mark", "row_id": 5, "stage": "PLAN", "item": "작업", "timestamp": "2026-05-01 18:00"}

// validate 성공
{"ok": true, "command": "validate", "violations": [], "violations_count": 0}

// 실패
{"ok": false, "command": "mark", "error": "worker_scope_violation", "message": "..."}

// 실패 (violations 포함)
{"ok": false, "command": "validate", "violations": [{"code": "marker_missing", "row_id": null, "detail": "..."}], "violations_count": 1}
```

### 사용 예시

```bash
# TASK 단계 시작 — state.json + STATE.md 생성 (opp 표준 20행 외부 주입)
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --task-title "파이프라인 state-tool 도입" \
  --rows-spec '[{"stage":"TASK","item":"작업"},{"stage":"TASK","item":"사용자 확인"},...]'

# SKILL.md에서 행 구성 자동 파싱
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive \
  --rows-from ~/.opal/skills/opal-pilot-project/SKILL.md

# 단계 시작 (⬜→🔄)
~/.opal/tools/state-tool/run.sh advance tasks/134-.../ --row 4

# 단계 완료 (→✅)
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ --row 4 --done

# 워커 EXECUTE Step 완료 (→✅, 권한 게이트 적용)
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --row 12 --done --as-worker --worker-stage EXECUTE --step 3/8

# [deprecated] gate-pass — 레거시 전용 (PLAN Gate 행이 6번부터 시작하는 예시, 신규 사용 금지)
~/.opal/tools/state-tool/run.sh gate-pass tasks/134-.../ --start 6

# PM Gate 전 정합성 검증
~/.opal/tools/state-tool/run.sh validate tasks/134-.../

# 현황판 출력 (기본 마크다운)
~/.opal/tools/state-tool/run.sh show tasks/134-.../

# 사용자 확인 행 처리
~/.opal/tools/state-tool/run.sh mark tasks/134-.../ \
  --row 11 --done --owner user --note "{owner_name} 확인: PLAN 단계 검토 완료"

# 추가작업 행 삽입
~/.opal/tools/state-tool/run.sh add-row tasks/134-.../ \
  --after 19 --stage CLOSE --item "추가 검증" --note "추가작업 진입"

# 추가작업 완료 상태 전환
~/.opal/tools/state-tool/run.sh status tasks/134-.../ \
  --set additional_work_done --note "추가작업 완료"

# 기존 STATE.md 흡수 (회귀 마이그레이션)
~/.opal/tools/state-tool/run.sh init tasks/134-.../ \
  --skill opp --mode interactive --import-existing
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위반 / 스코프 오류 / 검증 실패 (`worker_scope_violation`, `marker_missing`, `state_not_initialized` 등) |
| `2` | 내부 오류 (`date_tool_failed`, `rows_acts_not_implemented` 등) |

> 근거: `tasks/134-260501-opp-pipeline-state-tool/TASK.md` T-3 / `PLAN.md` §2.18 에러 코드 카탈로그 23종 SSOT

---

## code-scan

**용도**: 코드 파일의 `@header` 메타블록 스캔 — 15서브명령. 도메인/레이어/의존 관계 조회 8종 + `.opal/code-map/` 외부 매니페스트 기반 헤더 작성층(discover/scaffold/target/validate/feature) + 매니페스트 분할층(split) + 설정 초안 창구(init)  
**실행 경로**: `~/.opal/tools/code-scan/run.sh <command>` (권장) · `node ~/.opal/tools/code-scan/code-scan.js <command>` (하위호환)  
**소스 경로**: `opal/tools/code-scan/`  
**의존성**: Node.js (외부 패키지 없음)

### 커맨드

```bash
# 전체 스캔 (scope 미지정 시 프로젝트 전체)
node ~/.opal/tools/code-scan/code-scan.js scan [path] [--scope <name>]

# 도메인별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js domain [name]

# 레이어별 조회 (인자 없으면 목록)
node ~/.opal/tools/code-scan/code-scan.js layer [name]

# 헤더 내 패턴 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js search <pattern>
# 예: search "auth.*service", search "^user", search "login|logout"

# 도메인/레이어 요약
node ~/.opal/tools/code-scan/code-scan.js summary

# 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends <module>

# @header 없는 파일 목록
node ~/.opal/tools/code-scan/code-scan.js missing

# .opal/code-scan.json 설정 초안 생성 (비대화형 — 프롬프트·TTY 의존 0건)
# headerSource는 추론하지 않고 인자로 받는다 — 누락 시 init_header_source_required로 거부하며
# 파일을 만들지 않는다. 차단 게이트 앞에 배치되므로 설정이 없거나 깨진 트리에서도 동작한다
node ~/.opal/tools/code-scan/code-scan.js init --header-source <inline|manifest> [--write] [--force] [--json]

# .opal/code-map/index.json 초안 추론 (헤더 작성층)
node ~/.opal/tools/code-scan/code-scan.js discover [--out <path>] [--dry-run]

# 패키지 매니페스트 생성/갱신 (멱등 보존 merge, 기존 워커 기입값 유지)
# inline 모드에서는 no-op — 매니페스트를 만들지 않고 skipped 사유만 보고하며 exit 0이다
# 베이스가 선언한 샤드(_shards/{label}.json)는 보존·버킷 분배되고, 소스 디렉토리명이 예약 폴더
# _shards와 겹치면 reserved_name_collision으로 exit 1한다. 매니페스트가 상한(manifestMaxBytes)을
# 넘으면 stderr 1줄로 알린다(비차단)
node ~/.opal/tools/code-scan/code-scan.js scaffold [--dry-run]

# 파일의 @header 기록 위치 판정 (전역 headerSource 직결 — 파일 상태·인라인 보유 여부를 보지 않는다)
#   write_to (기록 위치 축) : `inline` / `manifest` / `none`
#   reason   (판정 사유 축) : `header_source_inline` / `header_source_manifest` / `out_of_scope`
#   두 필드는 서로 다른 축이며 한 목록으로 섞어 나열하지 않는다. 실제 조합은 아래 3쌍으로 닫힌다.
#     write_to=inline   일 때 reason=header_source_inline
#     write_to=manifest 일 때 reason=header_source_manifest (이 조합에서만 scope·manifest·key 부가 필드 동반,
#                        보유 샤드가 있으면 manifest가 그 샤드 경로를 가리키고 shard 필드에 라벨이 실린다 —
#                        보유 샤드가 없으면 베이스로 라우팅되어 shard 필드가 없다)
#     write_to=none     일 때 reason=out_of_scope (스코프 include/exclude 필터 탈락, 모드 판정보다 먼저)
#   베이스 매니페스트가 파손돼 있으면 manifest_parse_failed로 exit 1한다(신규 노출 — 이전에는 target이
#   매니페스트를 읽지 않았다)
node ~/.opal/tools/code-scan/code-scan.js target <file>

# code-map 무결성 검증 (5종 위반 + 모드별 단일 소스 커버리지, --changed로 영향 범위 한정)
# uncovered 위반은 git 기준 2분류: newly_uncovered(신규/회귀 — 차단) / pre_existing(레거시 — 비차단, counts만 노출)
# 샤드 선언 시 구조 검사는 베이스+전 샤드 합집합 기준으로 수행되며, 매니페스트 바이트 상한 초과는
# counts.manifest_oversize로 열거만 하고 차단하지 않는다(비차단)
node ~/.opal/tools/code-scan/code-scan.js validate [--changed <csv|->]

# 매니페스트 분할 — 제안(--plan) / 집행(--groups) 2모드 (manifest 모드 전용, inline은 거부)
# --plan은 매니페스트를 한 바이트도 쓰지 않는다(--out을 주면 groups 문서 1개만 쓴다)
# --groups는 4단 원자적 처리(사전 불변식 → tmp 전량 작성 → rename 커밋 → 캐시 비우고 재검증)
node ~/.opal/tools/code-scan/code-scan.js split <manifest> --plan [--out <path>] [--trace] [--stop-after <S1..S5>]
node ~/.opal/tools/code-scan/code-scan.js split <manifest> --groups <path|-> [--dry-run]

# 기능(feature) 태그 기준 cross-scope 조회 (기본 전체 스코프 순회, --scope로 단일 스코프 제한)
node ~/.opal/tools/code-scan/code-scan.js feature <id> [--scope <name>]
```

### 주요 옵션

| 옵션 | 설명 |
|------|------|
| `--header-source <inline\|manifest>` | 이 실행의 **전역 모드**를 지정한다. 설정 파일의 전역값보다 우선한다. 전 명령 공통이며, 설정 파일에도 없고 이 옵션도 없으면 명령이 거부된다(`header_source_unset`) |
| `--scope <name>` | 스코프 필터 (`.opal/code-scan.json`의 `scopes` 키) |
| `--domain <name>` | 도메인 필터 |
| `--layer <name>` | 레이어 필터 |
| `--exclude <patterns>` | 제외 패턴 (쉼표 구분, 와일드카드 지원) |
| `--out <path>` | `discover`: 초안 출력 경로 (기본 `.opal/code-map/index.json`) · `split --plan`: groups 문서 출력 경로 (플래그를 새로 만들지 않고 공유) |
| `--dry-run` | `discover`/`scaffold`/`split --groups`: 파일 쓰기 없이 결과만 계산 |
| `--write` | `init`: `.opal/code-scan.json`을 실제로 쓴다 (기본은 stdout 초안만) |
| `--force` | `init`: 기존 설정을 덮어쓴다 (`*.json.bak` 백업 후) |
| `--changed <csv|->` | `validate`: 쉼표 목록 또는 stdin 개행 목록으로 검증 범위 한정 |
| `--plan` | `split`: 분할 그룹 제안 (`--groups`와 배타) |
| `--groups <path|->` | `split`: groups 문서(파일 경로 또는 stdin)로 분할 집행 |
| `--trace` | `split --plan`: 사다리 단계별 표(입력 → 걷음 → 잔여) 출력 |
| `--stop-after <Sn>` | `split --plan`: 사다리를 `S1`~`S5` 중 지정 단계에서 중단 |
| `--brief` | 한 줄 요약 출력 (기본값) |
| `--full` | 전체 헤더 JSON 출력 |
| `--json` | 파이프용 raw JSON 출력 |

### 종료 코드 (전 명령 공통)

| 코드 | 의미 |
|------|------|
| `0` | 정상 종료 (`validate`는 차단 위반 없음 — `uncovered:pre_existing`만 있는 경우도 포함) |
| `1` | 사용법 오류 / 스키마 오류 / **헤더 소스 미해결** — 아래 에러 코드 4종 |
| `2` | `validate` 전용 — 차단 위반 발견 |

헤더 소스는 전 명령의 선행 조건이므로, 미해결이면 조회 명령까지 포함해 **전 명령이 exit 1로 거부**된다. 실패 시 stdout에는 기계 판독용 JSON(`error` 필드), stderr에는 사람용 안내가 함께 출력된다.

| 에러 코드 | 조건 |
|----------|------|
| `header_source_unset` | `.opal/code-scan.json`에 `headerSource`가 없고 `--header-source`도 주어지지 않음 |
| `header_source_invalid` | `headerSource` 값이 유효 도메인(`inline`, `manifest`) 밖 — 설정 파일에 폐기된 `auto`가 남아 있으면 `migration` 힌트가 함께 출력된다(자동 변환은 하지 않는다) |
| `code_scan_config_invalid` | `.opal/code-scan.json` 자체가 파손(파싱 실패·스키마 위반) — 프로젝트 `shardPolicy`의 타입 위반도 여기에 포함된다 |
| `scope_ambiguous` | 스코프 귀속 판정이 모호 — 동률 root에서 둘 이상의 스코프 `include`가 동시에 매칭 |

`header_source_unset`·`header_source_invalid`·`code_scan_config_invalid` 3종의 `fix` 안내에는 `code-scan init` 복구 경로가 함께 실린다(차단 동작 자체는 완화하지 않는다).

`init` 전용 에러 코드는 아래 2종이다. `init`은 **차단 게이트 앞에 배치**되므로 설정이 없거나 깨진 트리에서도 실행된다 — 게이트 뒤에 두면 "설정이 없어 `init`이 거부되고 `init`을 못 돌려 설정을 못 만드는" 순환이 생기기 때문이다. 나머지 명령의 차단 동작은 불변이다.

| 에러 코드 | 조건 |
|----------|------|
| `init_header_source_required` | `--header-source`가 없음 — 도구는 이 2택을 추론하지 않으며 **파일을 만들지 않는다** |
| `config_exists` | `.opal/code-scan.json`이 이미 있고 `--force`가 없음 — 원본은 불변이다 |

매니페스트 샤딩(`shards`) 관련 exit 1 에러 코드는 아래 2종이며, 헤더 소스 미해결과 무관하게 매니페스트를 읽는 명령(`scaffold`/`validate`/`target`/조회 8커맨드)에서 개별 발생한다.

| 에러 코드 | 조건 |
|----------|------|
| `shard_declaration_invalid` | 베이스 매니페스트의 `shards`가 배열이 아니거나, 라벨이 kebab 정규식 불일치·중복 선언 |
| `reserved_name_collision` | `scaffold` 대상 소스 디렉토리 이름이 예약 폴더 `_shards`와 충돌 |

`split`은 자산을 쓰는 유일한 명령이므로 실패 지점별로 쓰기 상태가 다른 에러 코드 **7종**을 갖는다(전부 exit 1).

| 에러 코드 | 조건 | 쓰기 상태 |
|----------|------|----------|
| `split_usage_invalid` | `--plan`/`--groups` 동시 지정·둘 다 없음·매니페스트 인자 누락·`--stop-after` 값 오류 | 무쓰기 |
| `split_inline_mode` | `inline` 모드에서 호출 — 조용한 성공 없이 거부한다 | 무쓰기 |
| `split_target_invalid` | 대상 매니페스트가 부재·파손·샤드 파일 자체를 지목 | 무쓰기 |
| `split_groups_invalid` | groups 문서가 파손·라벨 규칙 위반·중복·베이스에 없는 파일 지목 | 무쓰기 |
| `split_write_failed` | tmp 전량 작성 단계 실패 | 원본 불변(tmp만 정리) |
| `split_rollback` | rename 커밋 단계 실패 → 원상 복구 수행 | 원본 복구 완료 |
| `split_verify_failed` | 커밋 후 재검증에서 정합 붕괴 감지 | 커밋된 상태 + 진단 노출 |

집행의 계약은 **엔트리 유실 0건**이다 — 4단 원자적 처리(사전 불변식 검사 → tmp 전량 작성 → rename 커밋 → 캐시를 비우고 재검증)를 거치며, 재검증은 `resolveShards`를 다시 호출해 해석 로직을 복제하지 않는다.

### `uncovered` 2분류 (git 기준)

`@header`가 인라인·code-map 어디에도 없는 파일(`code:'uncovered'`)은 매니페스트가 관리하지 않는 디렉토리에 한해 git 상태로 재분류된다. 매니페스트가 해당 디렉토리를 관리(scaffold) 중인데 파일이 `files{}` 키에서 빠진 경우는 git과 무관하게 항상 `sub:'no_entry'`(차단)로 유지된다.

| `sub` | 조건 | 차단 여부 |
|-------|------|----------|
| `newly_uncovered` | git 기준 신규 파일(untracked/added) 또는 HEAD 버전엔 `@header`가 있었으나 현재 없음(회귀) | 차단(exit 2) |
| `pre_existing` | HEAD 버전에도 `@header`가 없던 기존 파일 | 비차단(exit 0) — `counts.pre_existing`·`violations[]`에 목록만 노출 |

git을 쓸 수 없는 환경(git 미설치·비git 트리)에서는 전량 `pre_existing`으로 처리하고 stderr에 경고 1줄을 출력한다(비차단). `counts.newly_uncovered`/`counts.pre_existing`으로 각각 집계되며, 다른 5종 위반(`orphan`/`conflict`/`draft`/`exports_not_found`/`worker_scope_violation`)의 차단 성격은 이 재분류와 무관하게 그대로 유지된다.

### 프로젝트 설정

프로젝트 루트의 `.opal/code-scan.json`으로 헤더 소스·스코프·필터를 정의한다.

```json
{
  "headerSource": "inline",
  "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
  "extensions": [".py", ".js", ".ts", ".vue"],
  "exclude": ["node_modules", "__pycache__"],
  "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
}
```

`scopes`의 각 값은 경로 문자열 축약형 또는 `{path, include, exclude}` 객체형으로 쓴다. 객체형은 스코프가 관리하는 **파일 집합**을 좁힐 때 사용한다.

```json
{
  "headerSource": "manifest",
  "scopes": {
    "be": { "path": "workspace/backend/", "include": ["app/**"], "exclude": ["app/legacy/**"] },
    "fe": "workspace/frontend/src/"
  },
  "extensions": [".py", ".ts"],
  "exclude": ["node_modules"]
}
```

- **`headerSource`는 전역 단일 키다** — 유효값은 `inline`과 `manifest` 2택이며, 프로젝트당 한 번만 정한다. 미설정이면 전 명령이 `header_source_unset`으로 거부된다.
- **스코프별 재선언은 없다** — `scopes` 객체 안에 헤더 소스 키를 넣어도 무시되며 stderr 안내 1줄만 출력된다. 같은 이유로 `.opal/code-map/index.json`의 스코프에도 헤더 소스 키를 두지 않는다. `include`/`exclude`는 파일 집합 필터일 뿐 기록 소스와 무관하다.
- 세 번째 값 `auto`는 제거되었다(Task 080). 설정에 남아 있으면 `header_source_invalid`로 거부되며 마이그레이션 힌트가 출력된다.
- 실행 단위로 다르게 쓰려면 설정을 고치지 말고 `--header-source`로 그 실행만 덮어쓴다.

**모드별 동작 요약**

| 모드 | 조회(`scan`/`domain`/`layer` 등) | `scaffold` | `validate` |
|------|-----------------------------------|-----------|-----------|
| `inline` | 파일 내 인라인 @header 단독 | no-op (매니페스트 미생성, exit 0 + skipped 사유) | 인라인 커버리지만 계상. 매니페스트 구조 검사 스킵 — `.opal/code-map/` 자산이 있으면 stderr 안내 1줄 |
| `manifest` | `.opal/code-map/` 매니페스트 4단 상속 (`files` → `package` → `layerRules` → `domains`) | 매니페스트 생성/갱신 | 매니페스트 커버리지만 계상 + 구조 검사 수행. `index.json` 부재 시 결과가 비고 stderr 안내 1줄(비차단) |

두 모드는 상호 배타이므로 인라인·매니페스트를 더한 합산 커버리지는 존재하지 않는다.

**매니페스트 샤딩** (`manifest` 모드 전용)

베이스 매니페스트(`mirrorPathForDir` 산출 경로, 진입점 무변경)가 `shards` 배열로 라벨을 선언하면, 예약 폴더 `_shards/`(`{베이스 경로 stem}/_shards/{label}.json`) 아래로 파일 엔트리를 의미 단위로 분산할 수 있다. 조회·기록 위치·구조 검증은 베이스+전 샤드 합집합을 단일 소스로 취급하며(첫 선언 우선·중복은 위반), `shards`를 선언하지 않은 매니페스트는 오늘과 완전히 동일하게 동작한다(하위호환, 옵트인).

```jsonc
// 베이스 매니페스트 — shards 키 1개만 추가
{
  "version": 1,
  "scope": "svc",
  "dir": "svc/order-api/src/...",
  "shards": ["order-core", "order-pricing"],
  "files": { "...": "..." }
}
```

**샤드 정책 (`shardPolicy`) — 설정 3단 우선순위**

분할 판정 값은 아래 순서로 해석되며, 읽는 지점은 코드에 `resolveShardPolicy` **1곳**으로 봉인돼 있다(실행당 1회 확정).

```
{프로젝트}/.opal/code-scan.json 최상위 shardPolicy
  > ~/.opal/setting.json 전역 shardPolicy
  > 코드 내장 상수 (maxBytes 10240 / minFiles 40)
```

```jsonc
// {프로젝트}/.opal/code-scan.json — 최상위에 둔다 (code-map/index.json이 아니다)
{
  "headerSource": "manifest",
  "shardPolicy": { "maxBytes": 10240, "minFiles": 40 }
}
```

- 키는 `maxBytes`(기본 10240) · `minFiles`(기본 40)이며 **셀 단위 머지**다 — 프로젝트에 한 키만 적으면 나머지 키는 하위 단계(전역 → 코드 상수)에서 온다.
- 전역 설정 부재·파싱 실패·키 부재·타입 위반은 **전부 비차단 폴백**(무시 + stderr 안내 후 하위 단계 값 사용)이다. **프로젝트** 설정의 타입 위반만 `code_scan_config_invalid`로 exit 1한다.
- code-scan은 `~/.opal/setting.json`을 읽는 **첫 도구**다. 홈 경로는 `OPAL_HOME` 환경변수로 주입할 수 있다(테스트 격리용).
- `shardPolicy.dictPath`(선택)는 표준단어사전 경로 명시값이다. **`shardPolicy.ladder` 설정 노출은 이번 범위에서 제외했고 후속 태스크로 이관했다** — 사다리 임계값은 현재 코드 상수다.

**폐기 안내** — 구 위치 `.opal/code-map/index.json`의 `manifestMaxBytes`는 폐기됐다. 도구는 그 **값을 읽지 않고** 실행당 1회 안내만 하며(비차단, exit 승격 없음), **자동 변환도 하지 않는다** — 새 주소 `shardPolicy`로 직접 옮겨 적어야 한다.

**2축 판정** — `manifest_oversize` 열거 조건은 **바이트 초과 AND 엔트리 수 이상**이다. 경계 규칙이 비대칭이다: 바이트는 `>`(초과), 엔트리는 `>=`(이상).

- 상한 초과는 `validate`/`scaffold` 모두 **전면 비차단**(감지·열거·경고만) — `validate`는 `counts.manifest_oversize`에 집계하고 차단 위반에서 제외한다. 초과가 있어도 다른 위반이 없으면 exit 0이다.
- 위반 페이로드에는 `entries`·`minFiles`·`recommendedShards`·`next`(다음에 실행할 `split --plan` 명령) 4필드가 실린다. `detail` 포맷(`{bytes}/{maxBytes}`)은 불변이다.

**분할 절차 4단** (`split`)

| 단계 | 명령 | 수행자 |
|------|------|--------|
| ① 탐지 | `code-scan validate` → `counts.manifest_oversize` + 위반의 `next` 확인 | 도구 |
| ② 제안 | `code-scan split <manifest> --plan --out <groups.json>` | 도구 |
| ③ 편집 | `groups.json`의 라벨·파일 배분을 확정한다 (의미 경계는 사람의 몫) | 사람/워커 |
| ④ 집행 | `code-scan split <manifest> --groups <groups.json>` (선행 `--dry-run` 권장) | 도구 |
| ⑤ 재검증 | `code-scan validate` — 집행 직후 도구가 자동 재검증하며, 절차상 한 번 더 확인한다 | 도구 |

`--plan`의 출력 스키마 = `--groups`의 입력 스키마다(왕복 성립) — 제안 문서를 편집만 하고 그대로 집행에 넣을 수 있다.

**제안 사다리 5단계** (`split --plan`)

각 단계는 **직전 단계의 미분류분만** 입력으로 받으며, 앞 단계의 배정은 재배정되지 않는다.

| 단계 | 신호 | 사전 대조 | 채택 임계 |
|------|------|----------|----------|
| S1 | 파일명 첫 토큰 | 표준단어사전 | 2건 이상 |
| S2 | 1~2번째 토큰 결합 | 표준단어사전 | 2건 이상 |
| S3 | 전체 토큰 중 매칭 | 표준단어사전 | 2건 이상 |
| S4 | 마지막 토큰(역할축) | 없음(빈도) | 3건 이상 |
| S5 | `depends` 공유 | 없음 | 3건 이상 |

- 잔여는 `unassigned`로 남긴다 — 도구는 **임의 배분도, "기타" 그룹 생성도 하지 않는다.** 의미 경계 확정은 사람의 몫이다.
- 검토 장치 3종: `--trace`(단계별 입력 → 걷음 → 잔여 표) · `--stop-after <S1..S5>`(사다리 중단) · 엔트리별 `stage` 필드(어느 단계가 걷었는지).

**표준단어사전 연동** (옵셔널, `split --plan` 전용)

S1~S3이 표준단어사전(`표준단어사전.md`)을 대조한다. **있으면 참고하고 없으면 건너뛴다** — 사전은 분할의 전제조건이 아니다.

- 탐색 3단: ① `shardPolicy.dictPath` 명시값 → ② `docs/PROJECT.md`의 `{설계}` 변수 해소(`{설계}/사전/표준단어사전.md`) → ③ 기본 경로.
- 폴백 3분기가 전부 **비차단**이다: **부재는 침묵**(S1~S3 skip) · **파싱 실패는 안내 1줄** · **매칭 0건은 정상 통과**. 프로젝트 루트 밖 경로와 크기 상한 초과 사전은 "사전 없음"으로 취급한다.
- 사전 md는 `## 수식어`(6열) · `## 분류어`(5열) 두 표를 **헤더 이름 기반**으로 읽는다(컬럼 위치를 가정하지 않는다 — 열 수가 다른 두 표를 위치로 읽으면 조용히 오분류된다).
- **읽기 전용**이며 호출 지점은 `split --plan` 경로 **1곳**뿐이다 — 조회 8커맨드의 출력이 사전 유무로 흔들리지 않는다.

### PM 관리 방안

`{프로젝트}/.opal/code-scan.json`은 PM이 생성하고 관리한다.

- **생성 시점**: code-scan 도구를 처음 사용하려 할 때 파일이 없으면 PM이 생성 — 산문 추론 대신 `code-scan init --header-source <inline|manifest> --write`가 결정론적으로 집행한다. `headerSource` 2택은 도구가 추론하지 않으므로 PM이 소유자에게 확인해 **인자로 넘긴다**.
- **갱신 트리거**: 신규 도메인/폴더 추가, 대규모 리팩토링, 신규 언어 도입
- **복구**: 설정이 깨졌으면 `code-scan init --header-source <...> --write --force` (원본은 `.bak`로 백업된다)
- **PM Gate 확인**: EXECUTE 완료 후 PM Gate에서 신규 scope/domain 반영 여부 확인

상세 관리 절차: `~/.opal/references/opal-pm.md` §9 참조

### 사용 예시

```bash
# BE 스코프 도메인 요약
node ~/.opal/tools/code-scan/code-scan.js summary --scope be

# auth 모듈 의존 관계 추적
node ~/.opal/tools/code-scan/code-scan.js depends auth

# @header 누락 파일 확인
node ~/.opal/tools/code-scan/code-scan.js missing --scope fe

# exports 필드 전용 검색 (정규식 지원, 대소문자 무시)
node ~/.opal/tools/code-scan/code-scan.js exports "issueToken"
# 예: exports "^get[A-Z]", exports "Token$", exports "create|update"

# @header 검증 (PM Gate용)
node ~/.opal/tools/code-scan/code-scan.js scan src/auth/auth.service.ts --json
```

---

## cmux-tool

**용도**: cmux browser 자동화 래퍼 — 12+1종 서브명령으로 웹 자동화·추출·상호작용을 단일 도구로 처리  
**실행 경로**: `bash ~/.opal/tools/cmux-tool/run.sh`  
**소스 경로**: `opal/tools/cmux-tool/`  
**의존성**: `cmux` 0.64.3 이상 (macOS 전용, 선택 설치) + Python 3.x (JSON 직렬화, 내장)  
**환경 변수**: `$CMUX_SURFACE_ID` (cmux 터미널 내 자동 설정)

### 트리거 조건

알투가 아래 사용자 문장을 수신하면 cmux-tool을 우선 선택한다.  
cmux 미설치 시 wtm-agent 경유 호출은 silent fallback → playwright-tool. 단독 호출 시 에러 JSON 반환.

| 사용 시점 | 대표 사용자 문장 | 우선 명령 (cmux-tool) | 폴백 |
|----------|----------------|----------------------|------|
| **웹 크롤링** (HTML 본문 추출) | "URL 읽어줘", "사이트 내용 정리", "이 페이지 마크다운" | `bash run.sh extract <url>` | playwright-tool |
| **정보 수집** (구조화된 데이터 조회) | "스냅샷 떠줘", "현재 페이지 구조 보여줘" | `bash run.sh snapshot --surface <h>` | (정보 조회만 — 폴백 없음) |
| **웹 테스트** (단일 상호작용) | "로그인 버튼 눌러", "이메일 칸에 입력해" | `bash run.sh click <sel>` / `bash run.sh fill <sel> --text <v>` | playwright-tool |
| **E2E 자동화** (다단계 시나리오) | "회원가입 폼 테스트", "결제 흐름 자동화" | `examples/e2e-form-fill.sh` 또는 fill + click + wait + snapshot 조합 | playwright-tool |
| **로컬 SPA·동적 페이지** | "localhost:3000 분석", "Next.js 화면 확인" | `bash run.sh extract <url>` (localhost URL 자동 감지) | playwright-tool |

### 커맨드 (12+1종)

```bash
# 레거시 호환: 첫 인자가 URL이면 extract 자동 라우팅
bash ~/.opal/tools/cmux-tool/run.sh https://example.com

# 서브명령 직접 지정
bash ~/.opal/tools/cmux-tool/run.sh extract https://example.com [--mode full|clean] [--wait <ms>]
bash ~/.opal/tools/cmux-tool/run.sh extract --surface <h> [<url>]  # B/C 모드
bash ~/.opal/tools/cmux-tool/run.sh snapshot [--surface <h>] [--compact]
bash ~/.opal/tools/cmux-tool/run.sh eval --script "<js>" [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh wait --load-state complete [--surface <h>] [--timeout-ms N]
bash ~/.opal/tools/cmux-tool/run.sh wait --selector "<sel>" [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh navigate <url> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh click <selector> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh fill <selector> --text <value> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh open <url>
bash ~/.opal/tools/cmux-tool/run.sh open-split <url>
bash ~/.opal/tools/cmux-tool/run.sh reload [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh press <key> [--surface <h>]
bash ~/.opal/tools/cmux-tool/run.sh get <selector> [--attr <name>] [--surface <h>]

# 사용법 보기
bash ~/.opal/tools/cmux-tool/run.sh --help
```

### 출력 형식

공통 5필드 + 명령별 특화 필드로 JSON 출력.

```json
// extract 성공 (기존 8필드 + command 필드 — R-2 호환)
{
  "ok": true, "command": "extract", "method": "cmux", "mode": "A",
  "surface": "surface:3", "user_owned": false,
  "title": "Example", "final_url": "https://example.com",
  "content": "<html>...", "bytes": 315209, "wait_ms": 2000
}

// snapshot 성공
{"ok":true,"command":"snapshot","surface":"surface:3","user_owned":true,"snapshot_text":"...","length":4096}

// 실패 (공통 5필드)
{"ok":false,"command":"click","surface":"surface:3","user_owned":true,"error":"eval_failed","detail":"..."}

// 폴백 트리거 실패 (fallback 필드 포함)
{"ok":false,"command":"extract","error":"cmux_not_installed","fallback":"phase2","install_url":"https://cmux.com/"}
```

### 에러 코드 (SSOT: run.sh / lib/dispatch.sh)

| 코드 | 종료값 | wtm-agent 처리 |
|------|--------|---------------|
| `not_in_cmux` | 2 | 자동 폴백 (phase2) |
| `cmux_not_installed` | 3 | 자동 폴백 (phase2) |
| `surface_parse_failed` | 5 | 자동 폴백 (phase2) |
| `open_failed` | 5 | 자동 폴백 (phase2) |
| `usage` | 1 | 폴백 금지 — 호출자 수정 |
| `invalid_surface` | 4 | 폴백 금지 — 핸들 수정 |
| `goto_failed` | 6 | 폴백 금지 — URL 오류 |
| `wait_failed` | 7 | 폴백 금지 — 네트워크/셀렉터 |
| `eval_failed` | 8 | 폴백 금지 — 명령 오류 |

> 에러 코드 신규 추가 순서: (1) run.sh / lib/dispatch.sh → (2) README.md → (3) tools.md → (4) AGENT.md

### 사용 예시

```bash
# URL 추출 (extract A 모드)
bash ~/.opal/tools/cmux-tool/run.sh https://docs.example.com

# 사용자 surface 현재 페이지 스냅샷 (B 모드)
bash ~/.opal/tools/cmux-tool/run.sh snapshot --surface surface:3

# 폼 자동화 (click + fill + wait)
bash ~/.opal/tools/cmux-tool/run.sh fill "#email" --text "user@example.com" --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh click "[type=submit]" --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh wait --load-state complete --surface surface:3

# E2E 레시피 실행
bash ~/.opal/tools/cmux-tool/examples/e2e-form-fill.sh https://example.com/login \
  --email user@example.com --password secret

# 분기 자동 결정
bash ~/.opal/tools/cmux-tool/examples/e2e-branch-auto.sh https://localhost:3000
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 사용법 오류 / 알 수 없는 서브명령 |
| `2` | 환경 오류 (CMUX_SURFACE_ID 미설정) |
| `3` | cmux 미설치 |
| `4` | surface 핸들 형식 오류 |
| `5` | browser open / surface 파싱 실패 |
| `6` | URL 이동 실패 |
| `7` | 로드 타임아웃 |
| `8` | 명령 실행 실패 |

---

## test-tool

**용도**: 테스트 단계별 도구 결정론적 집행 — 4서브명령(`resolve`/`check`/`unit`/`integration`)으로 `test-tools.yaml`을 읽어 단계(단위=EXECUTE / 통합=TEST)별 도구를 실행·판정하고 JSON 증거를 반환  
**실행 경로**: `bash ~/.opal/tools/test-tool/run.sh`  
**소스 경로**: `opal/tools/test-tool/`  
**의존성**: `~/.opal/.venv/bin/python` + PyYAML + cmux-tool (E2E 어댑터)

### 트리거 조건

테스트 단계 진입 시 호출한다 — 단위(EXECUTE 자가검증) 또는 통합(TEST). test-tool은 1회 실행·판정만 수행하며, 재시도 루프 한도는 보유하지 않는다(SSOT: `opal-harness.md §1`).

| 서브명령 | 용도 | 단계 |
|---------|------|------|
| `resolve` | `test-tools.yaml` resolution_order(project→global→추론) 해석 → tier×scope 도구셋 JSON 반환 | 단위/통합 공통 |
| `check` | required/optional 게이트 — required 미설치 차단, optional 미설치 skip | 단위/통합 공통 |
| `unit` | lint→build/type→unit 계층 stop-on-fail 단발 실행 | 단위 (EXECUTE) |
| `integration` | cmux-tool 호출→에러코드 소비→playwright 폴백 결정 + 실DB API 통합 | 통합 (TEST) |

### 커맨드

```bash
# test-tools.yaml 해석 → tier×scope 도구셋 JSON
bash ~/.opal/tools/test-tool/run.sh resolve [--stack py|ts] [--project-root PATH]

# required/optional 설치 게이트
bash ~/.opal/tools/test-tool/run.sh check [--category C] [--tier unit|integration] [--project-root PATH]

# 단위 계층 stop-on-fail 단발 실행 (lint→build→unit)
bash ~/.opal/tools/test-tool/run.sh unit [--scope fe|be] [--changed-files ...] [--project-root PATH]

# 통합 — cmux 1순위→playwright 폴백 (E2E) + 실DB API
bash ~/.opal/tools/test-tool/run.sh integration [--scope fe|be] [--url URL] [--project-root PATH]
```

### 출력 형식

모든 서브명령은 JSON으로 출력한다.

```json
// resolve 성공
{ "ok": true, "command": "resolve", "tiers": { "unit": {...}, "integration": {...} }, "source": "...", "stack": "ts" }

// 실패
{ "ok": false, "command": "unit", "error": "layer_failed", "stopped_at": "lint" }
```

---

## brain-tool

**용도**: 프로젝트 브레인 지식 위키 결정론적 집행 — 8 서브명령으로 index·log·링크 무결성을 집행하고 `@header` 단방향 시드를 관리  
**실행 경로**: `bash ~/.opal/tools/brain-tool/run.sh`  
**소스 경로**: `opal/tools/brain-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리 우선)

### 트리거 조건

`//opbr` 호출 또는 brain 참조(과거 결정·설계 맥락 조회) 시. `.opal/brain/` 부재 프로젝트에서는 no-op.

### 커맨드 (8 서브명령)

```bash
bash ~/.opal/tools/brain-tool/run.sh init <project-root>        # brain 디렉토리·index 초기화
bash ~/.opal/tools/brain-tool/run.sh add-page <args>            # 신규 페이지(entity/concept/flow 등) 추가 — --related로 관련 페이지 슬러그 CSV 지정 가능
bash ~/.opal/tools/brain-tool/run.sh index                      # index.md 재생성(링크 그래프 갱신)
bash ~/.opal/tools/brain-tool/run.sh log <args>                 # 변경 로그 기록
bash ~/.opal/tools/brain-tool/run.sh search <키워드>            # 후보 목록(page·title·score·snippet) 반환
bash ~/.opal/tools/brain-tool/run.sh sync-header <args>         # code-scan @header → entity 단방향 시드
bash ~/.opal/tools/brain-tool/run.sh lint                       # 링크 무결성·구조 린트
bash ~/.opal/tools/brain-tool/run.sh validate                   # frontmatter·평탄성 검증 — 링크필드(related) 값이 '[[', ']]', '.md'를 포함하면 거부

# 서브명령별 상세 플래그
bash ~/.opal/tools/brain-tool/run.sh <subcommand> --help
```

### 출력 형식

모든 커맨드는 JSON으로 출력한다 (`{"ok": true/false, ...}`). 상세 사용법은 `run.sh <subcommand> --help`(live)로 확인한다.

---

## tool-scan

**용도**: capability(OPAL/외부 CLI 도구·MCP·스킬) 상황 검색 + 권위 출처(live) 사용법 확인 — PM이 "필요 시점에 도구를 꺼내 정확한 사용법으로 사용"하도록 결정론적으로 집행  
**실행 경로**: `bash ~/.opal/tools/tool-scan/run.sh`  
**소스 경로**: `opal/tools/tool-scan/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/subprocess/re)

### 설계 원칙

- **사용법 텍스트를 저장하지 않는다** — `manifest.json`엔 `usage_source` 포인터만. `usage`는 매 호출 **live `--help`를 셸 실행**해 반환(drift 0).
- **federation(읽기)** — MCP는 `mcps.md`, 스킬은 `opal-skills-registry.json`을 읽기 전용으로 조회(원본 불파괴). OPAL atomic 도구만 매니페스트 SSOT.
- **2단 토큰** — `list`(전체 1줄 용도, 쌈) / `usage`(확정 1개의 live 사용법). 전체 사용법 일괄 주입 안 함.

### 커맨드 (5 서브명령)

```bash
bash ~/.opal/tools/tool-scan/run.sh list                       # 전체 capability 1줄 용도 (kind별)
bash ~/.opal/tools/tool-scan/run.sh which <상황>               # 상황→capability 후보 (가벼움)
bash ~/.opal/tools/tool-scan/run.sh resolve <상황>             # top capability + kind별 invoke + live usage + fallback
bash ~/.opal/tools/tool-scan/run.sh usage <도구> [서브명령]     # 권위 출처 live 사용법 (OPAL=exit0 판정 / 외부=stdout+stderr)
bash ~/.opal/tools/tool-scan/run.sh check <도구>               # 설치/실행 가능 여부
```

### 출력 형식

모든 서브명령은 JSON으로 출력한다.

```json
// resolve — kind별 invoke 형태
{"ok":true,"command":"resolve","situation":"browser check localhost",
 "resolved":{"name":"cmux-tool","kind":"tool","invoke":"shell","exec":"~/.opal/tools/cmux-tool/run.sh ...",
   "usage":{...},"fallback":{...}}}

// resolve — op-skill (워커 디스패치 형태)
{"ok":true,"command":"resolve","resolved":{"name":"op-data-model","kind":"op-skill",
   "invoke":"dispatch","skill_path":"~/.opal/skills/op-data-model/SKILL.md","dispatched_by":["opal-pilot-data-design"]}}

// 실패
{"ok":false,"command":"resolve","error":"no_match","detail":"..."}
```

> kind별 invoke: `tool`=셸 실행 / `mcp`=ToolSearch 포인터(파라미터 스키마는 런타임 ToolSearch) / `pilot-skill`=`//alias` 진입 / `op-skill`=워커 디스패치(SKILL.md 주입).

---

## memory-tool

**용도**: 프로젝트 메모리 인덱스·히스토리 결정론적 집행 — MEMORY.json 단독 SSOT, 9서브명령 init/append/update/promote/prune/show/review/delete/task-number. 메모리→docs/brain 졸업 워크플로우·히스토리 FIFO5·요약 길이캡·라이프사이클·lazy 자동 마이그레이션(md→json, `.bak` 보존)·매 변경 후 자가검토(review)·dead/superseded 정리(delete 무손실 가드)·히스토리 오기재 정정(update --kind history)·task-number(태스크 번호 채번 SSOT)  
**실행 경로**: `~/.opal/tools/memory-tool/run.sh`  
**소스 경로**: `opal/tools/memory-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/re/sys/datetime/os)

### 트리거 조건

메모리 등록·정리·이관 시 — append(신규 지식), update(상태 전이), promote(졸업), review(health 점검), task-number(태스크 번호 발급).

### 커맨드 (9 서브명령)

```bash
# MEMORY.json 생성 (create-if-absent)
~/.opal/tools/memory-tool/run.sh init --file <MEMORY.json 경로> [--force]

# 메모리 행 추가 (kind=memory: 지식 인덱스 / kind=history: 작업 히스토리 FIFO5)
~/.opal/tools/memory-tool/run.sh append --file <path> --kind {memory,history} --title <제목> \
  [--type {project,architecture,feedback,preferences,issues,task,improvement}] \
  [--status {active,promoted,superseded,dead,candidate}] \
  [--summary <요약 ≤80자>] \
  [--stage <단계>] [--path <경로>]  # history 전용

# 메모리 상태/요약/제목 수정 (라이프사이클 전이: active→superseded/dead 등)
# --kind history: 작업 히스토리 행 오기재 정정(FIFO 미적용·행 수 불변) — --stage/--result/--path/--new-title 사용
~/.opal/tools/memory-tool/run.sh update --file <path> --title <제목> \
  [--kind {memory,history}] \
  [--status <새 상태>] [--summary <새 요약 ≤80자>] [--new-title <새 제목>] \
  [--stage <새 단계>] [--result <새 핵심결과>] [--path <새 경로>]  # 뒤 3개는 --kind history 전용

# 메모리 → 영구 거처 졸업 (이전 확인 후 행+파일 삭제 + provenance 기록)
~/.opal/tools/memory-tool/run.sh promote --file <path> --title <제목> \
  [--to {docs,brain}] [--ref <영구 거처 위치 예: AGENT.md#금지사항>]

# 히스토리 FIFO=5 결정론 정리 (이미 ≤5이면 no-op)
~/.opal/tools/memory-tool/run.sh prune --file <path>

# 인덱스/히스토리 현황 출력 (read-only)
~/.opal/tools/memory-tool/run.sh show --file <path>
~/.opal/tools/memory-tool/run.sh show --file <path> --brief          # active 메모리만 5필드 축약 + 히스토리 최신 3건
~/.opal/tools/memory-tool/run.sh show --file <path> --history <N>   # 히스토리 반환 건수 재정의(단독 지정 가능)

# 자가검토 단독 health 명령 — violations[] + 라이프사이클 후보 반환
~/.opal/tools/memory-tool/run.sh review --file <path>

# dead/superseded 메모리 정리(인덱스 행 제거) — 무손실 가드(active/promoted 거부)
~/.opal/tools/memory-tool/run.sh delete --file <path> --title <제목> [--with-file]  # --with-file: memory/<file>.md도 삭제

# last_task_number 조회·원자적 채번 (태스크 번호 발급 SSOT)
~/.opal/tools/memory-tool/run.sh task-number --file <path>            # 조회(파일 무변경)
~/.opal/tools/memory-tool/run.sh task-number --file <path> --bump     # 원자적 +1
~/.opal/tools/memory-tool/run.sh task-number --file <path> --set <N>  # 복구·보정 (현재값보다 작으면 역행 거부)
```

`<file>`이 없고 동일 이름 `.md`만 있으면 `init` 없이도 최초 호출에서 **lazy 자동 마이그레이션**(md→json)이 발동한다 — 상세는 `opal/tools/memory-tool/README.md` §lazy 마이그레이션 참조.

### 출력 형식

모든 서브명령은 단일라인 JSON으로 출력한다.

```json
// 성공 (변경 명령은 review 블록 자동 첨부)
{"ok": true, "command": "append", "kind": "memory", "title": "...", "active_count": 3,
 "review": {"promote_candidates": [], "cleanup_candidates": [], "violations": [], "history_status": {...}}}

// 실패
{"ok": false, "command": "append", "error": "summary_too_long", "message": "요약 85자 > 80자 제한"}

// lazy 마이그레이션 발동 시 (성공 응답의 migration 키, 미발동 시 migration: null)
{"ok": true, "command": "show", ...,
 "migration": {"performed": true, "source": ".opal/MEMORY.md", "backup": ".opal/MEMORY.md.bak",
   "memories": 12, "history": 5, "review_flagged": 0,
   "unmapped_statuses": [], "last_task_number": 78, "last_task_number_source": "MEMORY.md 파싱",
   "empty_source_regions": [], "dropped_history": [], "backup_failed": false}}
```

### 주요 에러 코드 (SSOT: memory_tool.py ERROR_CODES)

| 코드 | 의미 |
|------|------|
| `memory_json_not_found` | MEMORY.json도 MEMORY.md도 없음 — init 먼저 실행 |
| `invalid_json` | MEMORY.json 파싱 실패 (손상된 JSON) |
| `schema_validation_failed` | 문서가 스키마 위반(파일 변경 없음, violations[] 참조) |
| `migration_failed` | md→json 변환 실패 — 원본 .md 무변경, .json 미생성 |
| `lock_timeout` | 메모리 락 획득 시간 초과 — 다른 프로세스 점유 중 |
| `summary_too_long` | 요약 >80자 제한 위반 |
| `promote_ref_missing` | promote 시 --ref(영구 거처 위치) 미지정 — 무손실 가드 |
| `row_not_found` | --title 에 해당하는 인덱스 행 없음 |
| `memory_file_not_found` | 메모리 파일(memory/*.md) 없음 |
| `already_initialized` | MEMORY.json 이미 존재 — --force로 재초기화 |
| `delete_requires_dead_or_superseded` | active/promoted 행 delete 시도 — dead/superseded만 제거 가능(무손실 가드) |
| `task_number_regression` | --set이 현재값보다 작음 — 채번 역행 거부(무손실) |
| `invalid_args` | 인자 조합이 올바르지 않음 (예: --bump와 --set 동시 지정) |
| `invalid_kind` | --kind가 memory 또는 history 중 하나가 아님 |
| `invalid_type` | --type이 유형 enum(project/architecture/feedback/preferences/issues/task)에 없음 |
| `invalid_status` | --status가 라이프사이클 enum(active/promoted/superseded/dead)에 없음 |
| `title_required` | --title은 필수 비공백 문자열 |
| `invalid_promote_target` | --to가 docs 또는 brain 중 하나가 아님 |
| `date_tool_failed` | node date.js 호출 실패 — MEMORY.md 변경 없음(원자성) |
| `unsupported_version` | 지원하지 않는 문서 version — 지원 상한 초과 |
| `schema_load_failed` | 스키마 파일을 로드할 수 없음(부재·파손) — 전 서브명령 결정론 거부 (H-13 관측 지점) |
| `schema_unsupported_keyword` | 검증기가 지원하지 않는 스키마 키워드 |
| `invalid_date` | 날짜 형식 오류 — YYYY-MM-DD가 아님 |

### 사용 예시

```bash
# 새 MEMORY.json 초기화
~/.opal/tools/memory-tool/run.sh init --file .opal/MEMORY.json

# 피드백 지식 등록
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json \
  --kind memory --title "배포 경계 직접편집 금지" \
  --type feedback --summary "~/.opal/ 배포 파일 직접편집 금지, 소스만 수정"

# 작업 히스토리 등록 (6번째부터 자동 FIFO 정리)
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json \
  --kind history --title "045 메모리 관리 개선" \
  --stage "완료" --path "tasks/045-260626-opd-메모리-관리-개선/" \
  --summary "memory-tool 신설 + SSOT 개정"

# 메모리 → docs 졸업 (이전 완료 확인 후)
~/.opal/tools/memory-tool/run.sh promote --file .opal/MEMORY.json \
  --title "배포 경계 직접편집 금지" \
  --to docs --ref "AGENT.md#금지사항"

# health 점검
~/.opal/tools/memory-tool/run.sh review --file .opal/MEMORY.json

# 신규 태스크 번호 채번
~/.opal/tools/memory-tool/run.sh task-number --file .opal/MEMORY.json --bump
```

---

## git-sync-tool

**용도**: 워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전 일괄 최신화 — 결정론적 집행. clean + fast-forward 가능한 저장소만 `git pull --ff-only`로 자동 최신화하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 건드리지 않고 skip 사유와 함께 보고한다. 자율 조치(stash/rebase/force/commit/push) 일절 없음 — 헌법 user sovereignty.  
**실행 경로**: `~/.opal/tools/git-sync-tool/run.sh`  
**소스 경로**: `opal/tools/git-sync-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/sys/subprocess) + 로컬 **git 2.22+** (`git rev-list --left-right --count` 사용)  
**호출자**: `opal-workspace-sync` 스킬(alias `opws`) — 대상 결정·5섹션 보고서·승인 게이트는 스킬이 담당, 도구는 순회·판정·pull만 집행.

### 트리거 조건

워크스페이스(여러 저장소 컨테이너)의 여러 git을 한 번에 최신화할 때. opal-workspace-sync 스킬 STEP 2에서 호출.

### 커맨드 (단일 서브명령)

```bash
# 지정 경로 순회 + 안전 최신화 → JSON 결과
~/.opal/tools/git-sync-tool/run.sh sync <workspace_path>
```

- `<path>/.git` 존재 → 그 1개를 단일 저장소로 처리. 아니면 `<path>` 직속 자식 1단계만 순회(재귀 안 함).
- 저장소별 판정 순서: detached → no-upstream → dirty → fetch → diverged/ff (detached HEAD에서 `@{u}` 조회가 fatal이라 no-upstream보다 선행).

### 출력 형식 (JSON)

```json
{"ok": true, "command": "sync", "workspace": "<절대경로>",
 "repositories": [{"name","branch","upstream","status","reason","ahead","behind","prev_head","new_head","pulled_commits"}],
 "summary": {"total","updated","skipped","failed"}, "error": null}
```

- `status`: `updated` | `skipped` | `failed` | `already-current`
- `reason`: `dirty` | `diverged` | `detached` | `no-upstream` | `fetch-failed` (정상이면 `null`)
- `already-current`는 `total`에 포함되나 updated/skipped/failed 카운트에는 미포함.
- `ok: false` + `error`(예: `PATH_NOT_FOUND`, `NOT_A_DIRECTORY`)는 치명 오류 시. exit 0(ok)/1(에러).

---

## improve-tool

**용도**: PM 개선 루프 결정론 집행 도구 — 3서브명령(`record`/`list`/`show`)으로 개선 후보를 로컬(프로젝트 `.opal/`)/FW(`~/.opal/fw-inbox/`) 2원 분기로 기록. 분류(로컬/FW 판단)는 호출자(opal-improve 스킬·CLOSE 회고 하드스텝)가 수행하고, 이 도구는 확정된 scope를 결정론적으로 집행만 한다  
**실행 경로**: `~/.opal/tools/improve-tool/run.sh`  
**소스 경로**: `opal/tools/improve-tool/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — json/argparse/pathlib/re/socket/subprocess/sys/datetime/os) + 형제 도구 `memory-tool`(local scope 위임)

### 트리거 조건

개선 후보(로컬 PM 개선 또는 프레임워크 개선)를 기록할 때 — `//opim`(opal-improve 스킬) 온디맨드 호출 또는 태스크 CLOSE 회고 하드스텝(4 pilot)에서 호출.

### 커맨드 (3 서브명령)

```bash
# 개선 후보 기록 — scope local: <project-root>/.opal/MEMORY.json 존재 시 memory-tool append 위임
#                  (구 MEMORY.md만 있으면 memory-tool이 lazy 변환 후 위임)
#                  (--type improvement --status candidate). 부재 시 graceful no-op.
#                  scope fw: ~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md 결정론 write.
~/.opal/tools/improve-tool/run.sh record --scope {local|fw} --title <제목> \
  [--body <제안 본문>] [--situation <retrospective|feedback|conversation>] \
  [--source-task <NNN|task-path>] [--project-root <경로>]

# 개선 후보 목록 조회 (read-only)
~/.opal/tools/improve-tool/run.sh list --scope {local|fw} [--project-root <경로>]

# 단일 개선 후보 조회 (read-only)
~/.opal/tools/improve-tool/run.sh show --scope {local|fw} [--id <id>] [--path <경로>] [--project-root <경로>]
```

- 환경변수 `IMPROVE_FW_INBOX`: 설정 시 fw scope의 기본 write 목적지(`~/.opal/fw-inbox/`) 대신 그 경로를 최우선 사용 — 테스트 격리 훅.

### 출력 형식

모든 서브명령은 단일라인 JSON으로 출력한다 (`{"ok": true/false, ...}`).

```json
// record 성공 — scope fw
{"ok": true, "scope": "fw", "path": "/Users/.../fw-inbox/20260717-095231-host-slug.md", "id": "20260717-095231-host-slug.md"}

// record 성공 — scope local (memory-tool 위임)
{"ok": true, "scope": "local", "delegated": "memory-tool", "file": "/path/.opal/MEMORY.json", "title": "..."}

// record no-op — scope local, 메모리 인덱스 부재
{"ok": true, "scope": "local", "skipped": true, "reason": "no MEMORY.json"}

// 실패 (인자 오류 — 크래시·traceback 없이 graceful)
{"ok": false, "error": "--scope must be one of ('local', 'fw'), got 'wrong'"}
```

### 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 (no-op 포함) |
| `1` | 인자 오류 / write 실패 / memory-tool 위임 실패 |

> 근거: `tasks/058-260713-opd-학습루프-도구화-개선수집/PLAN.md` §3.1.2(F-001 서브명령 스펙) / §3.2.2(F-002 fw-inbox 항목 스키마)

---

## opal-action-monitor

**용도**: 루프 액션 에이전트(opal-agent 채널)의 `<task_folder>/.oppl-run/` 산출물을 파싱해 단계(phase) × 축(axis) 진행 현황판을 렌더하는 읽기 전용 CLI  
**실행 경로**: `~/.opal/tools/opal-action-monitor/run.sh`  
**소스 경로**: `opal/tools/opal-action-monitor/`  
**의존성**: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `json`/`argparse`/`pathlib`/`os`/`time`/`datetime`/`sys`)

> 관련 도구: opal-agent(비동기 축 stream-json 실행 경로)는 도구 레지스트리에 등록되어 있지 않다 — 소스 경로 `opal/tools/opal-agent/`로만 참조한다. opal-action-monitor는 `.oppl-run/` 산출물만 읽는 독립 리더이며 opal-agent와 직접 import/호출 관계가 없다(파일 계약으로만 연결).

### 커맨드

```bash
# 텍스트 현황판 (1회성)
~/.opal/tools/opal-action-monitor/run.sh <task_folder>

# JSON 출력 (스킬/도구 파싱용)
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --json

# 주기적 재렌더 (기본 2초 폴링, 상한 --watch-timeout 기본 1800초)
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch
~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch 5 --watch-timeout 600
```

### 출력 형식

텍스트 현황판(`축(phase) | 상태 | 경과 | 최근 이벤트 요약 | 비용/세션` + journal tail + blocked 배너) 또는 `--json`으로 구조화 JSON 출력. 상태 판정(6종)·`--json` 스키마·에러 계약(`{"ok":false,"error":"<메시지>"}` + exit 1) 등 상세는 도구 README가 SSOT — 수치·규칙을 여기에 복제하지 않는다.

```json
// --json 성공 (요약 발췌)
{ "ok": true, "task_folder": "<abs>", "blocked": false,
  "phases": [{"phase":"t1","axis":"stream","status":"done", "...":"..."}] }

// 에러
{ "ok": false, "error": "<메시지>" }
```

### 사용 예시

```bash
# 태스크 진행 현황 1회 확인
~/.opal/tools/opal-action-monitor/run.sh tasks/067-260717-opd-루프액션-스트림-모니터링/

# 루프 액션 에이전트 실행 중 실시간 관측
~/.opal/tools/opal-action-monitor/run.sh tasks/067-260717-opd-루프액션-스트림-모니터링/ --watch
```

> 상세 사용법·입력 계약·상태 판정 표·`--json` 전체 스키마: `opal/tools/opal-action-monitor/README.md`

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-03 | xlsx-tool 등록 (076) |
| v1.1 | 2026-04-11 | code-scan 등록 |
| v1.2 | 2026-04-12 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 + exports 커맨드 사용 예시 추가 (109) |
| v1.3 | 2026-05-01 | state-tool 섹션 신규 추가 — 파이프라인 현황판 JSON SSOT 관리 CLI 9개 서브 명령 등록 (134) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — note 예시 "캡틴 확인" → "{owner_name} 확인" placeholder 치환 (139) |
| v1.5 | 2026-05-22 10:00 KST | cmux-tool 섹션 신규 추가 — 12+1종 서브명령 + 트리거 조건 5행 매트릭스 + 에러 코드 9종 + fallback 4종 (007) |
| v1.6 | 2026-06-07 | state-tool gate-pass deprecated 표기 — 사용법 블록·예시 2곳에 [deprecated] 레거시 전용 안내 추가. 신규는 PM Gate 통과 후 단일 mark 사용. Phase4 완료 반영 (014 Phase 4) |
| v1.7 | 2026-06-23 | test-tool 섹션 신규 추가 — 테스트 단계별 도구 결정론적 집행 4서브명령(resolve/check/unit/integration) + 트리거 조건 + 커맨드 + 출력 형식. cmux-tool 포맷 답습. 루프 한도 수치 비복제(harness §1 포인터) (039) |
| v1.8 | 2026-06-26 | brain-tool 섹션 신설(8 서브명령) + tool-scan 섹션 신설(5 서브명령 — capability 검색·live 사용법) + harness §9 drift 정합(code-scan·cmux-tool·tool-scan 행 추가). tools.md ↔ harness §9 도구 집합 7종 동일화 (044) |
| v1.9 | 2026-06-26 | memory-tool 섹션 신설(9 서브명령 init/append/update/promote/prune/migrate/show/review/delete) — 프로젝트 메모리 인덱스·히스토리 결정론적 집행, 메모리→docs/brain 졸업 워크플로우·히스토리 FIFO5·요약 길이캡·마커 직접편집 금지·매 변경 후 자가검토·delete(dead/superseded 무손실 정리)·update --new-title(제목 보정). harness §9 drift 정합 (045) |
| v2.0 | 2026-07-02 | git-sync-tool 섹션 신설(단일 서브명령 sync) — 워크스페이스 git 저장소 일괄 동기화, 직속 자식 순회 + ff-only pull + 5종 skip 판정 + JSON 출력. opal-workspace-sync 스킬이 호출. harness §9 drift 정합 (052) |
| v2.1 | 2026-07-10 13:11 | brain-tool validate 설명에 링크필드(related) 값 검사('[[', ']]', '.md' 거부) 반영 + add-page에 `--related` 플래그 설명 추가 (053) |
| v2.2 | 2026-07-17 19:58 KST | oppl-monitor 섹션 신규 추가 — `.oppl-run/` 파싱·단계×축 현황판 렌더(텍스트/`--json`/`--watch`), 상세 수치·규칙은 도구 README 포인터. opal-agent는 레지스트리 항목이 아니라 소스 경로로만 표기(R-REG) (067) |
| v2.3 | 2026-07-17 23:04 KST | 도구명 리네임 — `oppl-monitor` → `opal-action-monitor`(향후 oppd·opsdd 액션 에이전트 공통 관측 도구로 확장 예정이라 이름 중립화). 섹션 제목·경로·본문 명칭 전체 갱신, 로직 무변경 (067) |
| v2.4 | 2026-07-17 | improve-tool 섹션 신설(3 서브명령 record/list/show) — PM 개선 루프 결정론 집행, 로컬(memory-tool 위임)/FW(fw-inbox write) scope 분기, IMPROVE_FW_INBOX 테스트 격리 훅. memory-tool VALID_TYPES/VALID_STATUSES에 improvement/candidate additive 확장 반영 (058) |
| v2.5 | 2026-07-28 21:40 | code-scan 섹션 — 실행 경로를 `run.sh`(권장)·`node code-scan.js`(하위호환) 병기로 갱신, 헤더 작성층 신규 5서브명령(discover/scaffold/target/validate/feature) + 신규 옵션(`--out`/`--dry-run`/`--changed`) + `validate` 종료 코드 표 추가 (077) |
| v2.6 | 2026-07-28 | memory-tool 섹션 — MEMORY.json 단독 SSOT 전환 반영: `migrate` 서브명령 삭제 + `task-number` 서브명령 신설, `show --brief`/`--history N` 추가, lazy 자동 마이그레이션(md→json) 안내, 에러 코드 표를 현행 ERROR_CODES(`memory_json_not_found`/`schema_validation_failed`/`migration_failed`/`lock_timeout`/`task_number_regression`/`invalid_args` 등)로 정정, `marker_missing`·`import_failed` 제거, 모든 사용 예시 `--file`을 `.opal/MEMORY.json`으로 갱신 (078) |
| v2.7 | 2026-07-28 23:28 | code-scan `validate` — `uncovered` 위반 git 기준 2분류(`newly_uncovered` 차단 / `pre_existing` 비차단) 절 신설 + 종료 코드 표에 `pre_existing`-only 시 exit 0 명시 — Step 19에서 CLOSE 게이트가 레거시 파일에 막히던 결함 재작업 (077) |
| v2.8 | 2026-07-30 | memory-tool `update`에 `--kind history` 정정 경로 반영 — `--stage`/`--result`/`--path` 옵션 추가, 용도 1줄에 히스토리 오기재 정정 명시(FIFO 미적용·행 수 불변, 삭제 아님) (079) |
| v2.9 | 2026-08-02 14:50 | code-scan 섹션 헤더 소스 단일화 반영 — `target` 판정 주석의 구 4단 표기를 전역 `headerSource` 직결로 교체하고 `write_to` 3값과 `reason` 3값을 축별로 분리 서술(M-2 교정), `--header-source` 옵션 행 추가, 종료 코드 표를 `validate` 전용에서 전 명령 공통으로 확장 + 에러 코드 4종(`header_source_unset`/`header_source_invalid`/`code_scan_config_invalid`/`scope_ambiguous`) 등재, 프로젝트 설정 예시에 `headerSource` + `scopes` 객체형 추가 및 모드별 동작 요약 신설, `scaffold` inline no-op 1줄 추가, `auto` 유효값 서술 제거(폐기 표기만 유지) (080) |
| v2.10 | 2026-08-03 13:20 | code-scan 섹션 — 매니페스트 샤딩 반영: `scaffold`/`target`/`validate` 커맨드 주석에 `_shards/` 예약 폴더·샤드 라우팅·`manifestMaxBytes` 비차단 상한 서술 추가, 신규 에러 코드 2종(`shard_declaration_invalid`/`reserved_name_collision`) 표 신설, `target`의 신규 실패 표면 `manifest_parse_failed` 명시, §매니페스트 샤딩 서브섹션(`shards` 스키마 + `manifestMaxBytes` 설정 예시) 신설 (082) |
| v2.11 | 2026-08-04 17:18 | code-scan 섹션 — 샤드 정책 확장 반영(v1.6.0 / 13→15서브명령): `split`(제안 `--plan`·집행 `--groups`)·`init`(비대화형 설정 초안, 차단 게이트 앞 배치) 커맨드 등재, 옵션 표에 `--write`/`--force`/`--plan`/`--groups`/`--trace`/`--stop-after` 6행 추가 및 `--out`/`--dry-run` 설명 확장, 에러 코드 `init` 2종(`init_header_source_required`/`config_exists`)·`split` 7종(쓰기 상태 열 포함) 표 신설, §샤드 정책 신설 — `shardPolicy` 설정 3단 우선순위(프로젝트 > 전역 `~/.opal/setting.json` > 코드 상수 10240/40, 셀 단위 머지)·구 위치 `manifestMaxBytes` 폐기 안내(값 미독·자동 변환 없음)·2축 판정(바이트 `>` AND 엔트리 `>=`, 비차단 + 페이로드 4필드)·분할 절차 4단·제안 사다리 S1~S5 표·표준단어사전 탐색 3단/폴백 3분기(부재 침묵·파손 안내 1줄·매칭 0건 통과) 서술, `ladder` 설정 노출 후속 이관 명시, PM 관리 방안에 `init` 생성·`init --force` 복구 경로 반영 (083) |
