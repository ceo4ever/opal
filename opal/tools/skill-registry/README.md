# skill-registry

> OPAL·커뮤니티·프로젝트 스킬 레지스트리를 로드해 매칭·조회·검증·마이그레이션·위험 스캔을 수행하는 CLI
> 소스: `opal/tools/skill-registry/skill-registry.js` | 배포: `~/.opal/tools/skill-registry/skill-registry.js`
> 의존성: Node.js만 (`fs`/`path`/`os` 표준 모듈, 외부 패키지 0건)

## 개요

`skill-registry`는 레지스트리 JSON들을 병합 로드해 `//커맨드` 입력을 스킬로 해석하고, 스킬 메타데이터를 조회·검증한다. 커뮤니티 스킬 설치 절차의 1층 하드 필터인 `scan-risk`(clone 디렉토리 위험 패턴 스캔)도 같은 CLI에 들어 있다.

- **`run.sh` 래퍼가 없다** — 소스·배포 트리 모두 `skill-registry.js` 단일 파일이며 `node`로 직접 호출한다.
- **출력이 단일 라인 JSON이 아니다.** `JSON.stringify(result, null, 2)`로 들여쓰기된 여러 줄 JSON을 출력한다. 줄 단위로 JSON을 읽는 소비자는 전체를 모아 파싱해야 한다.
- 모든 서브명령이 읽기 전용이다 — **단 하나의 예외가 `migrate`**로, 이것만 파일시스템을 이동시킨다.

## 호출 형식

```bash
node ~/.opal/tools/skill-registry/skill-registry.js <command> [args]
```

개발 중에는 소스 경로로 직접 호출한다.

```bash
node opal/tools/skill-registry/skill-registry.js <command> [args]
```

## 레지스트리 탐색 경로

레지스트리 디렉토리는 아래 순서로 결정되며, `opal-skills-registry.json`의 실재 여부로 판정한다.

```
1) {cwd}/opal/core/references/        ← 소스 레이아웃 (테스트·개발 시 cwd 격리)
2) ~/.opal/references/                ← 배포 환경
3) {스크립트 위치}/../../core/references/  ← 개발 폴백
(전부 실패하면 2)를 그대로 쓴다)
```

이 디렉토리에서 읽는 파일은 `opal-skills-registry.json`(필수)과 `community-skills-registry.json`(선택)이다. 여기에 더해 병합 로드되는 소스가 둘 더 있다.

| 소스 | 경로 | 비고 |
|------|------|------|
| user | `~/.opal/community-skills/user-registry.json` | 부재·파손 시 조용히 무시 |
| project | cwd 기점 walk-up으로 찾은 프로젝트 루트의 레지스트리 | 동일 `name`은 **프로젝트 항목이 최우선 override** |

커뮤니티 스킬의 설치 경로는 `~/.opal/community-skills/` 아래에서 vendor 중첩(`{vendor}/{basename}/SKILL.md`)을 먼저 찾고, 없으면 flat(`{basename}/SKILL.md`)으로 폴백해 해석한다.

## 8개 서브 명령

### 1. `match` — 사용자 입력 → 스킬 해석

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match <input...>
```

`args[1]` 이후 전체를 공백으로 이어 붙여 입력으로 쓴다. alias(`//xxx`) 추출을 먼저 시도하고, 실패하면 trigger 정규식으로 매칭한다.

- **alias basename이 여러 vendor에 걸쳐 충돌하면 자동 선택하지 않는다** — `{found: true, ambiguous: true, alias, candidates: [...]}`를 돌려주고 선택은 호출자에게 맡긴다.
- 매칭 실패는 `{found: false, input}`이다. `error` 키가 없으므로 **exit 0**이다.
- ReDoS 방어: 입력은 256자로 잘라 쓰고, trigger 패턴은 길이 100 초과·`.*` 3개 이상·중첩 수량자 휴리스틱으로 사전 차단한다.

### 2. `get` — 스킬 메타데이터 조회

```bash
node ~/.opal/tools/skill-registry/skill-registry.js get <name>
```

`name`·소문자 `name`·`alias` 중 하나가 일치하는 항목을 찾아 레지스트리 원본 필드를 그대로 돌려주고, `group`과 `resolved_path`(실제 `SKILL.md` 절대경로, 미설치면 `null`)를 덧붙인다. 미발견 시 `{"error": "Skill not found: <name>"}` + exit 1.

### 3. `list` — 스킬 목록

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list [--group=<X>] [--domain=<X>]
```

- 옵션은 `--group=X` / `--domain=X` **등호 결합 형태만** 인식한다(`--group X`처럼 공백으로 띄우면 무시된다).
- `--group=community`는 그룹명이 아니라 **출처가 community인 스킬 전체**를 반환하는 특수 분기다. 그 외 값은 `_group`이 정확히 같거나 `<값>/`로 시작하는 항목을 고른다.
- 반환값이 객체가 아니라 **배열**이다. 항목은 `name`/`group`/`alias`/`description`/`domain`이며, community 스킬에만 `installed`가 추가로 붙는다.
- 배열에는 `error` 키가 없으므로 결과가 비어도 exit 0이다.

### 4. `validate` — 레지스트리 정합성 검증

```bash
node ~/.opal/tools/skill-registry/skill-registry.js validate
```

반환 필드는 `valid`/`total`/`groups`/`communityGroups`/`communitySchema`/`errors`/`warnings`/`unregistered`다.

- `SKILL.md`가 없는 등재 항목은 **error("dangling")**로 계상한다(warning이 아니다).
- 역방향 검사(`unregistered`)는 **소스 환경에서만** 수행한다 — 탐색된 레지스트리 디렉토리 경로가 `opal/core/references`를 포함할 때만 `opal/skills/`·`skills/`를 스캔한다. 배포 환경에서는 false positive를 피하려고 건너뛴다.
- `errors`가 하나라도 있으면 `valid: false`가 되고 **exit 1**이다.

### 5. `migrate` — flat → vendor 중첩 레이아웃 이동

```bash
node ~/.opal/tools/skill-registry/skill-registry.js migrate [--dry-run]
```

`~/.opal/community-skills/` 아래 flat 레이아웃을 vendor 중첩으로 1회 이동한다. **이 CLI에서 파일을 옮기는 유일한 명령이다.**

- basename이 레지스트리 전체 스킬명 중 **정확히 1개**와 매칭될 때만 이동한다.
- 미등재(0개 매칭)·충돌(2개 이상 매칭)은 이동하지 않고 `preserved`에 사유와 함께 기록한다 — 사용자 데이터를 삭제하거나 잘못 옮기지 않는다.
- 반환 필드는 `moved`/`preserved`/`skipped`/`errors`이며 멱등하다.
- `--dry-run`은 **위치 무관 플래그**다(`args.includes('--dry-run')`). 계획만 계산하고 이동하지 않는다.

### 6. `parse-source-repo` — `owner/repo@subdir` 파싱

```bash
node ~/.opal/tools/skill-registry/skill-registry.js parse-source-repo <source_repo>
```

`{owner, repo, subdir}`를 돌려준다. `@`가 없으면 `subdir`은 `repo`와 같은 값이 된다. 형식이 어긋나면 해당 필드가 `null`이 될 뿐 오류를 내지 않는다.

### 7. `scan-risk` — clone 디렉토리 위험 패턴 스캔

```bash
node ~/.opal/tools/skill-registry/skill-registry.js scan-risk <dir>
```

디렉토리를 읽기 전용으로 재귀 순회하며 위험 패턴 10종을 매칭하고 4단 `verdict`를 판정한다.

반환: `{ok, verdict, dir, scanned, hits, skipped}` (실패 시 `{ok: false, verdict: "UNKNOWN", dir, error}`).

**위험 패턴 10종**

| id | severity | capability |
|----|----------|-----------|
| `RP-01` | high | `fs:destructive` (루트·홈·와일드카드 대상 `rm -rf` 계열) |
| `RP-02` | high | `system:privilege` (`sudo`) |
| `RP-03` | high | `exec:remote` (`curl`/`wget` → 셸 파이프) |
| `RP-04` | high | `secret:credential` (ssh 개인키·aws credentials·netrc·npmrc) |
| `RP-05` | medium | `secret:env` (`.env`) |
| `RP-06` | medium | `exec:dynamic` (`eval`) |
| `RP-07` | medium | `obfuscation:base64` (`base64 -d`) |
| `RP-08` | medium | `network:outbound` (`curl` POST/데이터 전송) |
| `RP-09` | medium | `fs:permission` (`chmod 777`) |
| `RP-10` | medium | `system:persistence` (crontab·launchctl·LaunchAgents) |

**verdict 판정**: active hit 중 high가 하나라도 있으면 `RISKY`, medium만 있으면 `CAUTION`, 없으면 `SAFE`. 디렉토리 자체를 읽지 못하면 `UNKNOWN`이다.

**스캔 범위와 억제 규칙**

- 스캔 확장자: `.md` `.sh` `.bash` `.zsh` `.js` `.mjs` `.cjs` `.py` `.rb` `.ts` — 그 외는 `skipped`에 사유와 함께 기록한다.
- 제외 디렉토리: `.git` `node_modules` `dist` `build`.
- 파일 1MB 초과, 줄 길이 2000자 초과는 `skipped`로 건너뛴다(ReDoS·성능 방어).
- 매칭된 줄은 `negated`(부정 토큰 포함) / `comment`(주석 줄) / `fixture`(픽스처 경로) / `active`로 분류되며, **verdict를 올리는 것은 `active`뿐이다.** 나머지는 `hits`에 남지만 판정에 반영되지 않는다.

### 8. `verify-bundle` — registry canonical set ↔ skills-root 폴더 set 양방향 대조

```bash
node ~/.opal/tools/skill-registry/skill-registry.js verify-bundle --registry=<path> --skills-root=<path> [--skills-root=<path> ...]
```

주어진 `--registry`(JSON 파일 경로) 하나와 `--skills-root`(반복 가능, `list`의 `--flag=value` 관례와 동일) 하나 이상을 받아, 배포 환경 고정 경로(`validate`/`validateUnregistered`가 쓰는 `opal/skills`·`skills`)와 무관하게 **인자로 받은 경로만** 대조한다. cwd나 배포 여부에 의존하지 않으므로 배포 번들 검증 등 외부 호출 맥락에서 쓴다(태스크 140 W-4, PLAN DEC-2·DEC-3·DEC-5).

- registry JSON은 실제 `opal-skills-registry.json`과 동일한 `groups`(그룹명 → 엔트리 배열, community처럼 중첩 그룹도 가능) 스키마를 기대한다 — 평탄 `skills` 배열이 아니다. 내부적으로 `flattenGroups()`(다른 서브명령과 공유하는 정본 처리기)로 평탄화한 뒤 대조한다. `groups` 키가 없거나 객체가 아니면 `registry_not_found`다.
- canonical identity는 registry 엔트리의 `name` = 폴더 basename이다.
- registry에만 있는 `name`(대응 폴더 없음) → `missing_source`.
- 폴더에만 있는 basename(레지스트리 미등재) → `unregistered`. 여러 `--skills-root`는 합집합으로 본다.
- 같은 `alias`(scalar) 값이 서로 다른 두 개 이상의 canonical `name`을 가리키면 그 alias가 `ambiguous_alias`에 담긴다.
- 반환: `{ ok, total, missing_source: [], unregistered: [], ambiguous_alias: [] }`. `total`은 registry canonical 수(중복 제거)다.
- 셋 중 하나라도 비어있지 않으면 `ok: false`이고 **exit 1**이다. 정합이면 `ok: true`, 세 배열 모두 `[]`, **exit 0**이다.
- 인자 누락(`--registry` 또는 `--skills-root` 부재), registry 파일 부재·파싱 실패는 `error`(안정 코드 식별자: `missing_registry_arg`/`missing_skills_root_arg`/`registry_parse_error`/`registry_not_found`)와 `message`(사람이 읽는 설명)로 분리해 반환하고 exit 1이다 — 다른 서브명령의 자유 문자열 `error` 관례와 달리 이 서브명령의 `error`는 안정 식별자다.
- stdout은 항상 **단일 라인** JSON이다(다른 서브명령의 들여쓰기된 다중 라인 출력과 다르다) — 자동화 파서가 줄 수로 실패를 검증할 수 있게 한다.



**선언 목록 없음.** 이 도구는 오류 코드 카탈로그를 정의하지 않는다. 실패는 `error` 필드에 **사람이 읽는 자유 문자열**로 담기므로(`Skill not found: ...`, `Not a directory: ...`, `Directory not found or inaccessible: ...`), 호출자는 `error` 문자열을 키로 분기하지 말고 존재 여부만 본다.

`validate`는 `error` 대신 `errors[]`(문자열 배열)와 `valid`(boolean)로 결과를 보고한다.

## 종료 코드

| 코드 | 조건 |
|------|------|
| `0` | 결과 JSON 출력 후 `result.error`가 없고 `result.valid !== false` |
| `1` | ① 결과에 `error` 키가 있음 ② `validate`의 `valid === false` ③ 서브명령 자체 누락 ④ 알 수 없는 서브명령 ⑤ `match`/`get`/`parse-source-repo`/`scan-risk`의 필수 인자 누락 |

①②는 JSON을 stdout에 출력한 **뒤** exit 1하고, ③~⑤는 JSON 없이 usage/오류 문구를 stderr에 출력하고 exit 1한다. 즉 **exit 1이라고 stdout에 JSON이 있다고 가정할 수 없다.**

`match`의 미발견(`found: false`)과 `list`의 빈 결과는 실패가 아니므로 exit 0이다.

`verify-bundle`은 자체 exit 로직을 쓴다 — `ok === true`면 exit 0, 그 외(`ok: false`, 인자 누락, registry 파싱 실패 포함)는 모두 exit 1이며, 다른 서브명령과 달리 인자 누락 시에도 usage 문구가 아니라 stdout에 단일 라인 JSON(`error`/`message` 포함)을 출력한다.

## 제약

- `--help`/`-h` 플래그가 없다. 인자 없이 호출하면 usage를 **stderr**에 출력하고 exit 1한다.
- `list`의 반환이 배열이라 `ok`/`error` 필드 자리가 없다 — 다른 OPAL 도구와 응답 골격이 다르다.
- 프로젝트 스코프 해석과 `resolveFirstPath`는 경로 traversal 방어를 위해 홈·cwd·프로젝트 루트 하위 여부를 검증한다. 그 밖을 가리키는 경로는 `null`로 떨어진다(오류가 아니다).
