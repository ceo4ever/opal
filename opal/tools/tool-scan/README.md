# tool-scan

> capability(OPAL 도구·MCP·스킬) 상황 검색 + 권위 출처(live `--help`) 사용법 확인 CLI
> 소스: `opal/tools/tool-scan/` | 배포: `~/.opal/tools/tool-scan/`
> 의존성: `~/.opal/.venv/bin/python` (표준 라이브러리만 — `argparse`/`json`/`os`/`pathlib`/`re`/`subprocess`/`sys`)

## 개요

`tool-scan`은 "필요한 시점에 도구를 꺼내 정확한 사용법으로 쓴다"를 결정론적으로 집행한다. 5서브명령(`list`/`which`/`usage`/`resolve`/`check`)으로 구성된다.

### 설계 원칙

- **사용법 텍스트를 저장하지 않는다.** `manifest.json`에는 `usage_source` 포인터만 둔다. `usage`는 매 호출 **live `--help`를 셸 실행**해 얻는다(정적 캐시 금지 → drift 0).
- **exit code로 성공을 판정한다.** `--help` 실행 결과는 `returncode == 0`으로만 판정하며, 응답 본문의 `ok` 필드를 판정에 쓰지 않는다(exit 0 + `ok:false`를 내는 도구가 있기 때문).
- **stdout + stderr를 병합한다.** `--help`를 stderr로만 내보내는 외부 CLI가 있어 둘을 합쳐 `usage_text`로 만든다.
- **federation은 읽기 전용이다.** MCP는 `mcps.md`, 스킬은 `opal-skills-registry.json`을 읽기만 한다. 매니페스트 SSOT는 OPAL atomic 도구뿐이다.
- **2단 토큰.** `list`는 전체를 1줄 용도로만(싸게), `usage`는 확정된 1개의 live 사용법만 반환한다 — 전체 사용법을 일괄 주입하지 않는다.
- `subprocess`는 전부 `shell=False`(인자 리스트)다.

### 매니페스트 — 등록된 도구만 조회 대상이다

`manifest.json`의 `tools[]`가 SSOT이며, 현재 등재는 **7개**(`tool-scan`·`xlsx-tool`·`state-tool`·`code-scan`·`cmux-tool`·`test-tool`·`brain-tool`)로 전부 `kind: "tool"`, `usage_source.type: "self-help"`다. **여기 없는 OPAL 도구는 `usage`/`check`가 `tool_not_found`로 거부한다** — 도구가 없다는 뜻이 아니라 매니페스트에 등재되지 않았다는 뜻이다.

### 환경변수 (테스트 격리용)

| 변수 | 대체 대상 |
|------|----------|
| `OPAL_VENV_PYTHON` | `run.sh`가 쓸 python 경로 |
| `TOOL_SCAN_MANIFEST_PATH` | `manifest.json` 절대경로 |
| `TOOL_SCAN_MCPS_PATH` | `mcps.md` 절대경로 |
| `TOOL_SCAN_SKILLS_REGISTRY_PATH` | `opal-skills-registry.json` 절대경로 |
| `TOOL_SCAN_HELP_CMD` | self-help 실행 커맨드(`bash <값>`) |

## 호출 형식

```bash
bash ~/.opal/tools/tool-scan/run.sh <command> [args]
```

## 5개 서브 명령

### 1. `list` — 전체 capability 1줄 용도

```bash
bash ~/.opal/tools/tool-scan/run.sh list
```

**매니페스트 SSOT만** 반환한다(federation은 포함하지 않는다). 항목은 `name`/`kind`/`purpose` 3필드이며 usage 본문은 싣지 않는다.

```json
{"ok": true, "command": "list", "capabilities": [{"name": "code-scan", "kind": "tool", "purpose": "..."}]}
```

---

### 2. `which` — 상황 → capability 후보 목록

```bash
bash ~/.opal/tools/tool-scan/run.sh which <상황 키워드...>
```

여러 인자를 공백으로 이어 하나의 상황 문자열로 만든다. 매니페스트 + MCP + 스킬 전체를 대상으로 점수를 매겨 **결정론적으로 정렬**한 후보 목록을 돌려준다(usage는 붙이지 않는다).

**정렬 규칙**: `(-점수, kind 우선순위, 이름 알파벳)`. kind 우선순위는 `tool`(0) > `mcp`(1) > `op-skill`(2) > `pilot-skill`(3)이다.

**점수 규칙**: `when` 키워드와의 정확 매칭 또는 2자 이상 접두어 부분 매칭이 각 1점. 스킬(`op-skill`/`pilot-skill`)은 `triggers` 정규식이 상황 문자열에 걸리면 2점(첫 매칭에서 중단)을 더한다. 점수 0인 항목은 후보에서 빠진다.

응답의 `matched_on`은 **정확 매칭된 토큰만** 담는다 — 부분 매칭으로 점수를 얻어도 여기에는 나타나지 않으므로 `score > 0`인데 `matched_on`이 비는 경우가 정상적으로 존재한다.

---

### 3. `usage` — 권위 출처 live 사용법

```bash
bash ~/.opal/tools/tool-scan/run.sh usage <도구> [서브명령]
```

매니페스트에서 `name`이 일치하는 엔트리를 찾아 `usage_source.type`에 따라 사용법을 해석한다.

| `type` | 동작 | `live` |
|--------|------|--------|
| `self-help`(기본) | `~/.opal/tools/<name>/run.sh --help`를 셸 실행 | `true` |
| `inline` | 매니페스트의 `text`를 그대로 반환 | `false` |
| `doc` | `ref` 경로의 파일을 읽어 반환(`freshness`가 있으면 `(as of ...)` 부기) | `false` |
| `context7` / `url` | 본문 없이 `pointer: {type, ref}`만 반환 | `false` |

`self-help` 경로에서 stdout이 `{` 또는 `[`로 시작하면 JSON 파싱을 시도해 `usage_json`으로, 실패하거나 평문이면 stdout+stderr 병합 텍스트를 `usage_text`로 싣는다. 매니페스트 엔트리에 `fallback`이 있으면 응답에 동봉한다.

> **`[서브명령]` 인자는 받기만 하고 사용하지 않는다.** argparse에 정의돼 있으나 핸들러가 참조하지 않으므로, 넘겨도 반환되는 사용법은 도구 전체의 `--help`로 동일하다.

---

### 4. `resolve` — 상황 → top-1 capability + invoke 방법

```bash
bash ~/.opal/tools/tool-scan/run.sh resolve <상황 키워드...>
```

`which`와 같은 라우팅을 돌린 뒤 **1위 하나만** kind별 호출 형태와 함께 돌려준다.

| kind | `invoke` | 동봉 필드 |
|------|---------|----------|
| `tool` | `shell` | `exec`(`~/.opal/tools/<name>/run.sh`), `fallback`, live `usage_text` 또는 `usage_json` |
| `mcp` | `ToolSearch` | `exec`(`ToolSearch query "select:<name>"`), `description` — **`parameters`는 싣지 않는다**(파라미터 스키마는 런타임 ToolSearch의 몫) |
| `pilot-skill` | `alias` | `exec`(`//<alias>`), `skill_path` |
| `op-skill` | `dispatch` | `skill_path`, `stage`(있으면), `dispatched_by`(있으면) |

`kind: tool`인데 매니페스트에서 엔트리를 다시 찾지 못하면 `fallback: null`만 싣고 usage는 붙지 않는다.

---

### 5. `check` — 설치·실행 가능 여부

```bash
bash ~/.opal/tools/tool-scan/run.sh check <도구>
```

`~/.opal/tools/<name>/run.sh`의 존재와 실행 권한(`os.X_OK`)을 확인한다. 배포 경로에 없으면 `{cwd}/opal/tools/<name>/run.sh`(소스 환경)로 폴백해 다시 본다. `fallback_allowed`는 매니페스트 `fallback` 계약에서 도출한다(`on == "usage"` 항목은 제외).

```json
{"ok": true, "command": "check", "tool": "code-scan", "installed": true, "detail": null, "fallback_allowed": false}
```

> `kind`가 `tool`이 아닌 엔트리는 검사 자체를 하지 않아 항상 `installed: false`, `detail: null`로 응답한다(오류는 아니다).

## 사용 예시

```bash
# 전체 capability 목록
bash ~/.opal/tools/tool-scan/run.sh list

# 상황으로 후보 찾기
bash ~/.opal/tools/tool-scan/run.sh which 엑셀 읽기

# 1위 하나와 호출 방법 + live 사용법
bash ~/.opal/tools/tool-scan/run.sh resolve browser check localhost

# 확정된 도구의 현재 사용법
bash ~/.opal/tools/tool-scan/run.sh usage code-scan

# 설치 여부 확인
bash ~/.opal/tools/tool-scan/run.sh check brain-tool
```

## 오류 코드 (ERROR_CODES SSOT)

`tool_scan.py`의 `ERROR_CODES` 딕셔너리가 SSOT다. 모든 `error` 값은 이 키를 쓰며 임의 변형하지 않는다.

| 코드 | 의미 | 방출 지점 |
|------|------|----------|
| `venv_missing` | `~/.opal/.venv` 부재 | `run.sh` 선검사 |
| `manifest_missing` | `manifest.json` 없음 — 설치 손상 | 전 명령(매니페스트 로드) |
| `manifest_parse_failed` | `manifest.json` JSON 문법 오류 | 전 명령(매니페스트 로드) |
| `tool_not_found` | 매니페스트에 해당 도구 엔트리 없음 | `usage` / `check` |
| `usage_unavailable` | `usage_source` 해석 실패 — `doc` 파일 읽기 불가 등 | `usage` |
| `help_exec_failed` | self `--help` 셸 실행 실패(비-0 종료·실행 파일 부재) | `usage` |
| `no_match` | 상황 키워드 매칭 후보 없음 | `which` / `resolve` |
| `registry_read_failed` | federation 입력 읽기 실패 | — (아래 참조) |

두 가지를 명시해 둔다.

- **`registry_read_failed`는 카탈로그에 선언돼 있으나 현재 소스의 어느 경로에서도 방출되지 않는다.** `_load_federation()`이 `mcps.md`·`opal-skills-registry.json` 로드 실패를 예외로 흡수해 빈 목록으로 대체하기 때문이다. 즉 **federation 입력이 깨져 있어도 실패가 아니라 "후보가 줄어든 성공"으로 나타난다.**
- **`no_match`는 인자 오류에도 재사용된다.** 알 수 없는 서브명령, 서브명령 누락, argparse 파싱 실패가 모두 `no_match`로 응답되므로, `no_match`만으로 "매칭 실패"와 "호출 오류"를 구분할 수 없다 — `detail` 문자열과 종료 코드를 함께 봐야 한다.

```json
{"ok": false, "command": "resolve", "error": "no_match", "detail": "매칭 없음: '...'"}
```

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 |
| `1` | 위 오류 코드로 거부(`manifest_*`·`tool_not_found`·`usage_*`·`help_exec_failed`·매칭 실패 `no_match`), 서브명령 누락·미지 서브명령, `run.sh`의 `venv_missing` |
| `2` | argparse 파싱 실패 — `_JsonErrorParser`가 `no_match` JSON으로 바꿔 출력한 뒤 2로 종료 |

**exit 1과 exit 2 모두 `error: "no_match"`를 낼 수 있다.** 종료 코드가 둘을 가르는 유일한 신호다.

`run.sh`의 `venv_missing` JSON은 stderr가 아닌 **stdout**으로 나간다.

## 제약

- **매니페스트에 등재된 도구만 `usage`/`check` 대상이다**(현재 7개). 미등재 도구는 실재해도 `tool_not_found`다.
- `usage`의 `[서브명령]` 인자는 무시된다(위 §3 참조).
- `self-help`는 매 호출 실제로 `--help` 프로세스를 띄운다 — 캐시가 없으므로 반복 호출 비용이 그대로 든다. 또한 타임아웃을 걸지 않으므로 대상 `run.sh`가 멈추면 `tool-scan`도 함께 멈춘다.
- `list`는 federation을 포함하지 않는다 — MCP·스킬을 보려면 `which`/`resolve`로 조회해야 한다.
- 라우팅 점수가 단순 키워드/정규식 기반이므로 동점 후보는 kind 우선순위와 이름 알파벳으로만 갈린다. `resolve`의 1위 선택에 의미론적 판단은 들어가지 않는다.
