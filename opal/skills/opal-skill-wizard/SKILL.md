---
name: opal-skill-wizard
description: |
  **프로젝트 스킬 위저드 — 프로젝트에 적합한 커뮤니티 스킬 제안 + 프로젝트 스코프 설치**. 프로젝트 컨텍스트를 인터뷰·문서 재사용으로 파악해 후보를 도출하고, 승인분을 `{project}/.opal/community-skills/`에 설치한 뒤 프로젝트 registry에 기록한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-skill-wizard", "osw", "프로젝트에 맞는 스킬 추천", "이 프로젝트에 쓸 스킬 찾아줘", `//` 커맨드 매칭 결과가 `scope:"project"` && `installed:false`인 경우.
  모드: 신규(인터뷰) | 기존(`docs/PROJECT.md` 재사용 + 결측 인터뷰). 모드는 §0 판별 기준으로 자동 결정한다.
  필수 입력: 프로젝트 루트(`{project}/.opal/` 디렉토리 마커로 확정). 보장 출력: 제안 목록 + (승인 시) 설치된 스킬 본체 + `{project}/.opal/skills-registry.json` 기록.
alias: osw
triggers:
  - "^osw$"
  - "^opal-skill-wizard$"
  - "(?i)(스킬\\s*위저드|프로젝트\\s*스킬\\s*추천)"
version: "1.0"
domain: skill
pipeline: "MODE: 신규 | 기존"
---

# opal-skill-wizard (프로젝트 스킬 위저드)

프로젝트에 적합한 커뮤니티 스킬을 제안하고, 승인분을 **프로젝트 스코프**에 설치한다.
검색은 `npx skills find`([skills.sh](https://skills.sh/)) 단일 소스를 직접 사용하고, 설치는 **clone-copy 단일 방식**으로 수행한다.
절차 순서는 고정이다 — **검색 → 임시 디렉토리 clone → `scan-risk` 보안 게이트(§4) → 승인 → 프로젝트 경로 복사(§5)**.

> **스코프 경계**: 이 스킬은 **프로젝트 스코프 전용**이다. 전역(`~/.opal/community-skills/`) 설치·삭제·업데이트는 이 스킬의 범위가 아니며 `opal-skill-manager`가 계속 담당한다. 상세는 §9.

## 진입 훅 (전 절차 공통 선행)

아래 4항을 순서대로 확인한 뒤에만 §0으로 진입한다.

| # | 확인 | 방법 | 실패 시 |
|---|------|------|--------|
| 1 | Node.js 가용 | `node --version` | 검색·검사 도구를 쓸 수 없다 — 웹 카탈로그(https://skills.sh/)와 Node.js 설치를 안내하고 종료 |
| 2 | `git` 가용 | `git --version` | clone 불가 — 사실을 알리고 종료(수동 다운로드를 유도하지 않는다) |
| 3 | `skill-registry.js` 경로 확인 | `ls ~/.opal/tools/skill-registry/skill-registry.js` | 보안 검사 도구 부재 → **§4 [MUST]에 따라 설치를 진행하지 않는다**. 사실을 알리고 종료 |
| 4 | **프로젝트 루트 확정** | `process.cwd()`부터 부모 방향으로 **`{project}/.opal/` 디렉토리**가 존재하는 최초 디렉토리를 루트로 확정한다. 홈 디렉토리(`os.homedir()`)에 도달하면 홈 자체는 검사하지 않고 중단하며, 파일시스템 루트 도달·32단 초과 시에도 중단한다 | **`null`(비프로젝트 디렉토리)** → 아래 「비프로젝트 진입 규칙」 |

- **[MUST] 탐색 마커는 `.opal/` 디렉토리이며 `.opal/skills-registry.json` 파일이 아니다.** registry는 이 스킬이 최초 설치 시 생성하므로 **부재가 정상 상태**이며, 파일을 마커로 삼으면 최초 설치 전에 루트를 찾지 못하는 순환이 생긴다. 이 마커는 `opal/tools/skill-registry/skill-registry.js`의 `findProjectRoot()`가 쓰는 마커와 **동일**해야 한다 — 설치 루트와 해석 루트가 갈리면 설치분이 발동하지 않는다.
- **[MUST] 홈 경계 정지** — 전역 `~/.opal/`을 프로젝트 스코프로 오인하지 않는다.

### 비프로젝트 진입 규칙 (프로젝트 루트 = `null`)

**[MUST] 임의 경로에 설치하지 않는다.** 프로젝트 루트를 확정하지 못하면 아래를 수행하고 종료한다.

1. **대상 부재를 사용자에게 알린다** — "현재 위치에서 OPAL 프로젝트 루트(`.opal/` 디렉토리)를 찾지 못해 프로젝트 스코프 설치 대상이 없습니다"를 명시한다. **[MUST] 침묵 종료 금지** — 사유를 밝히지 않고 끝내면 「정상 차단」과 「조용한 실패」가 구분되지 않는다.
2. 다음 2개 경로를 안내한다 — ① 프로젝트 루트로 이동해 재실행 ② 전역 설치가 목적이면 `opal-skill-manager`가 전역 스코프를 담당한다는 사실 안내(안내일 뿐이며 이 스킬이 대신 실행하지 않는다).
3. **[MUST] 부작용 부재** — 이 분기에서는 cwd·홈·전역 어디에도 **파일·디렉토리를 생성하지 않는다**. registry 스켈레톤 생성도 하지 않는다.

## 0. 모드 판별

프로젝트 루트 기준 `docs/PROJECT.md`의 **존재 여부 단일 축**으로 판별한다.

| 조건 | 모드 | 진행 |
|------|------|------|
| `docs/PROJECT.md` **부재** | **신규 모드** | §1 (인터뷰) |
| `docs/PROJECT.md` **존재** | **기존 모드** | §2 (재사용 + 결측 인터뷰) |

- 판별 결과를 사용자에게 **1줄로 통지**한 뒤 진행한다 (예: "`docs/PROJECT.md`가 없어 신규 모드(인터뷰)로 진행합니다").
- 판별은 파일 존재 여부라는 사실 판정이며 주관 해석을 쓰지 않는다.

## 1. 신규 모드 — 인터뷰

`docs/PROJECT.md`가 없으므로 스킬 제안에 필요한 최소 컨텍스트를 인터뷰로 수집한다.

**[MUST] `opal-project-init`을 대체하지 않는다.** 이 절의 인터뷰는 *스킬 후보 도출에 필요한 최소 항목*에 한정한다. 전면 온보딩(`docs/`·`.opal/` 문서 생성)이 필요하다고 판단되면 `opal-project-init`을 **안내만** 하고, 이 스킬에서 온보딩 문서를 작성하지 않는다.

**질문 항목 (4항 고정)**

| # | 질문 | 후보 도출에서의 쓰임 |
|---|------|--------------------|
| 1 | 이 프로젝트의 기술 영역은 무엇입니까 (언어·프레임워크·런타임) | 검색어 구성의 1차 키워드 |
| 2 | 반복적으로 수행하는 작업은 무엇입니까 | 검색어 구성의 2차 키워드 |
| 3 | 자동화를 원하는 작업 범주는 무엇입니까 | **결측 판정의 핵심 항목** — 후보 적합 판단의 기준 |
| 4 | 제약이 있습니까 (라이선스·외부 네트워크·의존성 등) | §4·§5의 승인 판단 입력 |

- 답변은 사용자 발화 그대로 기록하고, 추정으로 채우지 않는다. 미응답 항목은 「미상」으로 두고 §3 검색어에서 제외한다.

## 2. 기존 모드 — `docs/PROJECT.md` 재사용 + 결측 인터뷰

### 2.1 재사용 항목 목록

`docs/PROJECT.md`에서 아래 항목을 **읽기 전용**으로 재사용한다. 이 스킬은 `docs/PROJECT.md`를 수정하지 않는다.

| # | 재사용 항목 | 위치 | 후보 도출에서의 쓰임 |
|---|-----------|------|--------------------|
| 1 | 폴더 구조맵 | §프로젝트 구조 | 프로젝트 형태(모노레포·단일 앱 등) 파악 |
| 2 | 기술 스택 | §프로젝트 구성 4열 표의 기술 스택 컬럼 | 검색어 구성의 1차 키워드 |

### 2.2 결측 판정 기준

| 판정 | 기준 |
|------|------|
| **결측** | 해당 절이 **부재**하거나, 절은 있으나 값이 **비어 있음**(플레이스홀더 `_{채움}_`·`TBD`·빈 표 포함) |
| **유효** | 절이 존재하고 값이 1건 이상 기재됨 |

- 결측으로 판정된 항목만 사용자에게 되묻는다. 유효 항목을 다시 묻지 않는다(중복 질문 억제).

### 2.3 결측 항목 (구조화 필드 부재로 항상 인터뷰)

| 항목 | 사유 |
|------|------|
| **원하는 스킬의 기능 범주**(= 자동화 대상 작업 유형) | `docs/PROJECT.md`에 대응하는 구조화 필드가 없다 — 문서에서 도출 불가하므로 항상 인터뷰한다 |

### 2.4 `docs/PROJECT.md` 부재 시 폴백

기존 모드로 진입했으나 실제 읽기 시점에 파일이 없거나 읽을 수 없으면(삭제·권한 오류 등) **§1 신규 모드로 전환**하고, 전환 사실을 사용자에게 1줄 통지한다. **부재를 이유로 절차를 중단하지 않는다.**

## 3. 후보 도출 + skills.sh 직접 검색

§1·§2에서 수집한 항목으로 검색어를 구성한 뒤, 아래 순서로 후보를 준비한다.
**순서 고정: ① 검색 → ② 임시 디렉토리 clone → ③ §4 `scan-risk` 게이트 → ④ §5 승인 후 복사.**

### 3.1 검색

```bash
npx skills find "{query}"
```

- 출력 필드는 `owner/repo@skill`(스킬명)·설치 수·URL 3개다. 라이선스·설명은 이 출력에 없으며 clone 이후에만 확정된다.
- 결과가 4건 이상이면 상위 3건만 다음 단계로 보낸다. 선별 기준은 결정론적 순서다 — ① `source_repo` 있음 우선 ② `npx skills find` 출력 순서.
- **결과 0건이면 §7(`opal-skill-creator` 위임)로 분기한다.** **[MUST] 빈 목록을 제안으로 제시하지 않는다.**
- `npx` 실행 실패 시: 웹 카탈로그(https://skills.sh/)를 안내하고 종료한다.

### 3.2 clone 대상 = 임시 디렉토리

후보별로 **별도 임시 디렉토리**(`mktemp -d`)에 shallow clone한다.

```bash
git clone --depth 1 https://github.com/{owner}/{repo}.git {tmp}
```

- **[MUST] clone은 임시이며 설치가 아니다.** clone 결과는 검사·비교의 입력일 뿐이며, 프로젝트 경로로 **복사되는 시점**에만 설치가 성립한다.
- `git -C {tmp} rev-parse HEAD`로 `commit_sha`를 확보하고, 저장소 루트 `LICENSE`/`LICENCE`로 라이선스를 판별한다(파일 부재 시 `Unknown`).
- 원본 디렉토리 탐지가 실패해 `SKILL.md`를 찾지 못한 후보는 **탈락**시킨다(빈 디렉토리 복사 금지).

### 3.3 설치 대상 경로 (복사 목적지)

```
{project}/.opal/community-skills/{vendor}/{skill}/SKILL.md
```

- 이 경로로의 복사 **실행은 §5**에서 수행하며, **반드시 §4 `scan-risk` 게이트를 통과한 후보에 한정**한다.
- `{vendor}`/`{skill}`은 registry `name` 필드(`{vendor}/{skill}`) 기준이며 `source_repo`의 owner/subdir과 다를 수 있다.

> **참조 근거**: 「clone은 임시, 복사가 설치」 원리와 clone-copy 4단 절차의 원본은 `opal/skills/opal-skill-manager/SKILL.md` §2다. 본 절은 그 **원리를 프로젝트 경로에 적용**한 것이며, 절차 실행을 다른 스킬에 넘기지 않는다 — 이 스킬이 검색·clone·검사·복사·기록을 직접 수행한다.

## 4. 설치 전 보안 검사 (`scan-risk` 게이트)

**[MUST] 호출 지점 = 복사 직전**(clone 이후, 복사 이전). 후보별 임시 디렉토리를 대상으로 실행한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js scan-risk {clone된 경로}
```

- 반환 JSON의 `verdict`(`SAFE`/`CAUTION`/`RISKY`/`UNKNOWN`)와 `hits[]`를 판정 입력으로 쓴다. `context === "active"`인 hit만 판정에 반영한다.
- **[MUST] 게이트는 도구 호출 결과로 판정한다.** 문서를 읽어본 인상·산문 판단으로 이 판정을 대체하지 않는다 — [MUST] `~/.opal/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."
- 판정 축·명칭은 `docs/ARCHITECTURE.md` §커뮤니티 스킬의 4단(SAFE / CAUTION / RISKY / UNKNOWN)을 그대로 따른다 — 신규 판정 체계를 만들지 않는다.

### 4.1 판정별 동작

| `scan-risk` 판정 | wizard 동작 |
|-----------------|------------|
| `SAFE` | 승인 게이트 없이 제안 목록에 포함, 사용자 승인 후 복사 진행 |
| `CAUTION` | 제안 목록에 포함하되 **확인 게이트 필수** — hit 요약을 제시하고 명시 승인 시에만 복사 |
| `RISKY` | **추천 후보에서 제외** — 복사하지 않는다 |
| `UNKNOWN`(라이선스 미확인 포함) | **확인 게이트 필수** — 라이선스·출처 불명 사실을 고지하고 명시 승인 시에만 복사 |
| 도구 실행 실패 / 미실행 | **[MUST] 설치를 진행하지 않는다** |

### 4.2 게이트 [MUST] 3항

1. **[MUST] `RISKY` 판정 후보는 추천 후보에서 제외하고 복사하지 않는다.** 제외 사유(판정값 + active hit의 `id`·`capability`·`file:line`)를 사용자에게 표시한다.
2. **[MUST] 검사 실패(도구 비정상 종료·미실행·경로 부재) 시 설치를 진행하지 않는다.** 검사되지 않은 후보가 조용히 통과하는 경로를 두지 않는다 — 실패 사실과 사유를 표시하고 해당 후보를 탈락시킨다.
3. **[MUST] 판정 결과는 §6 registry의 `trust`·`capabilities`·`scanned_at` 필드로 기록한다.** 기록되지 않은 설치는 성립하지 않는다.

- 전 후보가 이 게이트에서 탈락하면 §7(위임)로 분기한다.

## 5. 제안 → 승인 → 설치

3단을 **이 순서로** 수행한다. 단계를 건너뛰거나 순서를 바꾸지 않는다.

### 5.1 제안

§4를 통과한 후보를 표로 제시한다.

| 열 | 내용 |
|----|------|
| 스킬명 | `{vendor}/{skill}` |
| 출처 | `source_repo` URL |
| 라이선스 | `LICENSE` 판별값 (미확인 시 `Unknown` + "⚠️ 라이선스 미확인") |
| 보안 판정 | `scan-risk` `verdict` + active hit 수 |
| 설치 위치 | `{project}/.opal/community-skills/{vendor}/{skill}/` |

- 후보가 0건이면 제안 단계를 수행하지 않고 §7로 분기한다. **[MUST] 빈 표를 제안으로 제시하지 않는다.**

### 5.2 승인

- **[MUST] 승인 게이트는 복사 직전 1회다.** clone·검사에는 별도 승인을 요구하지 않으며(설치가 아니므로), 복사 시점에만 사용자 명시 승인을 받는다.
- `CAUTION`·`UNKNOWN` 후보는 이 승인에 더해 §4.1의 확인 게이트를 별도로 통과해야 한다.
- **[MUST] 사용자가 후보를 전건 거부하면 설치를 강행하지 않는다** — §7(위임)로 분기하거나, 사용자가 위임도 원하지 않으면 사유를 알리고 종료한다. 이 분기에서 **파일을 만들지 않는다**(본체 복사·registry 기록 모두 없음).

### 5.3 설치 (복사)

승인된 후보의 원본 디렉토리를 아래로 복사한다.

```
{project}/.opal/community-skills/{vendor}/{skill}/
```

- 원본이 빈 디렉토리이면 복사하지 않는다.
- 복사가 성공한 시점에 **설치가 성립**한다 → 즉시 §6으로 진행한다.

## 6. 프로젝트 registry 기록

**[MUST] 기록 시점 = 복사 성공 직후.** 복사 전에 기록하지 않는다(설치되지 않은 항목이 등재되어 발동 실패를 유발한다).

**대상 파일**: `{project}/.opal/skills-registry.json`

**절차**

1. 파일이 없으면 아래 **스켈레톤을 생성**한 뒤 append한다.

```json
{ "version": "1.0.0", "updated_at": "{ISO8601}", "groups": { "project": [] } }
```

2. `groups.project` 배열에 §8 스키마를 따르는 항목을 append한다. 동일 `name`이 이미 있으면 항목을 교체한다(중복 등재 금지).
3. `updated_at`을 갱신한다.
4. **기록 후 자가 확인** — 발동 가능 여부를 즉시 검증한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match "{name}"
```

   - `found:true` && `installed:true`이면 설치 완료를 보고한다.
   - `installed:false`이면 본체 경로와 registry `name`의 불일치를 점검한다(경로는 `name`에서 계산되므로 `name`이 실제 디렉토리 구조와 일치해야 한다).

## 7. 적합 스킬 미발견 시 `opal-skill-creator` 위임

### 7.1 위임 트리거 (3조건)

| # | 조건 |
|---|------|
| 1 | §3.1 검색 결과 **0건** |
| 2 | §4 게이트 후 **잔존 후보 0건**(전 후보 `RISKY` 탈락 또는 검사 실패 탈락) |
| 3 | 사용자가 추천 후보를 **전건 거부** |

> 트리거 3조건은 `opal/skills/opal-skill-manager/SKILL.md:85-88`의 위임 조건을 프로젝트 스코프에 그대로 적용한 것이다(참조 근거).

- **[MUST] 위임 대상은 `opal-skill-creator`다.** 별도 생성기 컴포넌트를 신설하지 않는다.
- **[MUST] 이 분기에서 파일을 만들지 않는다** — registry 기록·본체 복사·스켈레톤 생성 모두 수행하지 않는다.

### 7.2 위임 페이로드 (7필드)

| 필드 | 타입 | 내용 |
|------|------|------|
| `requested_capability` | string | 사용자가 요구한 기능을 1~2문으로 정규화한 서술 |
| `requested_triggers` | string[] | 사용자 발화에서 추출한 트리거 표현 목록 |
| `requested_output_format` | string | 기대 산출물 형식·경로 규약 |
| `searched_sources` | string[] | 탐색한 소스 목록 (예: `["skills.sh (npx skills find \"{query}\")"]`) + 검색어 원문 |
| `candidates_evaluated` | object[] | 후보별 `{name, source_repo, license, trust, shortfall}` |
| `security_findings` | object[] | 후보별 `scan-risk` active hit 요약 `{name, verdict, capabilities[]}` |
| `skill_type_hint` | string | `"프레임워크 스킬"` \| `"OPAL 전용 스킬"` \| `"미정"` |

> 7필드 정의의 원본은 `opal/skills/opal-skill-manager/SKILL.md:92-102`이며, creator 입력과 1:1 대응한다(참조 근거).

**위임 방식**: `opal-skill-creator`의 SKILL.md를 Read하고 위 페이로드를 컨텍스트로 전달하여 신규 생성 모드로 진입한다. 이 스킬은 `opal-skill-creator`를 수정하지 않는다.

## 8. 프로젝트 registry 스키마

**파일**: `{project}/.opal/skills-registry.json`

**최상위 구조** — 기존 registry들과 동일하게 `groups` 맵을 갖는다. 로더가 `groups`를 순회하므로 이 형태를 벗어나면 병합되지 않는다.

```json
{ "$schema": "...", "version": "1.0.0", "updated_at": "...", "groups": { "project": [ { "...": "항목" } ] } }
```

**항목 필드 (12)**

| 필드 | 필수 | 타입 | 내용 |
|------|------|------|------|
| `name` | ✅ | string | `{vendor}/{skill}` 정식명 — 병합 override 키 |
| `alias` | | string | 약어 (미지정 가능) |
| `description` | ✅ | string | 1줄 설명 |
| `triggers` | ✅ | string[] | 정규식 배열 — 트리거 매칭이 소비 |
| `domain` | | string | 도메인 라벨 |
| `source_repo` | ✅ | string | clone 출처 URL (**출처**) |
| `commit_sha` | ✅ | string | clone 시점 commit (**commit**) |
| `license` | ✅ | string | 라이선스 (미확인 시 `"Unknown"`) (**라이선스**) |
| `trust` | ✅ | string | `SAFE`/`CAUTION`/`RISKY`/`UNKNOWN` (**보안 판정**) |
| `capabilities` | | string[] | `scan-risk` active hit 요약 |
| `scanned_at` | ✅ | string | 스캔 시점 ISO8601 (**스캔 시점**) |
| `installed_at` | ✅ | string | 복사 성립 시점 ISO8601 |

- **[MUST] `paths` 필드를 두지 않는다** — 프로젝트 스킬 경로는 `name`에서 동적 계산한다(§3.3 경로 규약).
- 판정·출처 필드는 카탈로그 스키마에 없는 필드이나, `validate`가 미지 필드를 무시하는 성질을 이용한 **additive 기록** 방식을 따른다.

## 9. 설치 경로 규칙 (스코프 경계)

이 스킬은 **프로젝트 스코프 전용**이다.

```
{project}/.opal/
├── skills-registry.json                  ← 프로젝트 설치 등록분 (이 스킬이 기록)
└── community-skills/
    └── {vendor}/{skill}/SKILL.md         ← 프로젝트 설치 본체 (이 스킬이 복사)
```

- **[MUST] 전역(`~/.opal/community-skills/`, `~/.opal/community-skills/user-registry.json`)에 쓰지 않는다.** 전역 스코프는 `opal-skill-manager`가 소유하며, 이 스킬은 전역 경로 규칙을 개정하지 않고 프로젝트 스코프를 **추가**할 뿐이다.
- **[MUST] 플랫폼 네이티브 `skills/` 디렉토리에 복사하지 않는다.** 커뮤니티 스킬은 OPAL 내부 경로에만 설치한다 — `opal/skills/opal-skill-manager/SKILL.md` §설치 경로 규칙("커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다. 플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다.")과 **동일 금지**를 프로젝트 스코프에도 적용한다.
- **[MUST] 플랫폼 분기를 두지 않는다.** Claude/Cursor/Gemini 등 플랫폼별 분기는 어댑터 계층(install·plugin)의 책임이며 이 문서에 두지 않는다.
- **범위 밖**: 설치분의 업데이트·삭제, 전역 설치, 스코프 간 이동은 이 스킬이 수행하지 않는다.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-09-04 08:32 KST | 최초 작성 — 프로젝트 적합 커뮤니티 스킬 제안 + 프로젝트 스코프 설치 스킬 신설. 2모드(신규 인터뷰 / 기존 `docs/PROJECT.md` 재사용 + 결측 인터뷰) · skills.sh 직접 검색 · `scan-risk` 보안 게이트(복사 직전, 4단 판정) · 제안→승인→설치 3단 · 프로젝트 registry 기록 · `opal-skill-creator` 위임(트리거 3조건·페이로드 7필드) (114) |
