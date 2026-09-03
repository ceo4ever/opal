---
name: skill-manager
description: |
  OPAL 커뮤니티 스킬 검색, 설치, 관리.
  "스킬 검색", "스킬 찾아줘", "○○ 관련 스킬 있어?", "스킬 설치해줘",
  "설치된 스킬 목록", "설치된 스킬", "스킬 삭제해줘" 시 사용.
---

# Skill Manager

커뮤니티 스킬을 검색, 설치, 관리하는 OPAL 전용 스킬이다.
검색은 `npx skills` CLI([vercel-labs/skills](https://github.com/vercel-labs/skills))의 생태계 검색을 보조로 사용하고, 설치는 **clone-copy 단일 방식**(git clone → 복사)으로 수행한다. `npx skills add`는 사용하지 않는다.

## 관리 진입 훅 (4절차 공통 선행)

검색·설치·제거·업데이트 절차를 시작하기 전에, flat 레이아웃 잔재를 vendor 중첩으로 정규화하는 마이그레이션을 1회 멱등 실행한다:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js migrate --dry-run   # 선확인 권장 — 실제 이동 없이 계획만 출력
node ~/.opal/tools/skill-registry/skill-registry.js migrate             # 실행
```

- registry에 등재된 basename과 유일하게 매칭되는 flat 디렉토리만 `{vendor}/{basename}/`로 이동한다.
- registry에 없는(미등재) 디렉토리, basename이 여러 vendor와 충돌하는 디렉토리는 **이동하지 않고 보존**한다 — 사용자 데이터를 삭제·오이동하지 않는다.
- 이미 vendor 중첩 상태거나 flat 잔재가 없으면 아무 것도 이동하지 않는다 (재실행 안전, 멱등).

## 프로세스

### 1. 스킬 검색

사용자가 특정 기능의 스킬을 찾을 때:

**1단계: 설치 여부 대조 — Match 3등급**

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match "{검색어}"
```

판정 입력은 `match` 출력의 기존 필드(`found`·`installed`·`ambiguous`·`name`·`alias`)뿐이며, 아래 표는 **문자열 동일성 비교**로만 등급을 가른다 — 주관 판단을 쓰지 않는다.

| 등급 | 판정 기준 (`match` 출력) | 후속 동작 |
|------|------------------------|----------|
| **Exact Match** | `found:true` && `installed:true` && (`name`이 검색어와 문자열 동일 \|\| `alias`가 검색어에서 추출한 alias와 문자열 동일) | 설치된 스킬 정보를 안내하고 **종료** |
| **Partial Match** | `found:true` && `installed:true` && Exact 조건 불성립(= triggers 정규식 유래 매칭), **또는** `ambiguous:true` | 매칭된 스킬을 안내하고 "찾으시는 것이 맞습니까? 아니면 외부 검색을 진행할까요?"를 묻는다. `ambiguous:true`이면 `candidates` 목록(vendor별 `name`·`source_repo`·`license`·`installed`)을 표시하고 정식명(`vendor/skill`)으로 재호출을 유도한다 — 자동 선택하지 않는다 |
| **No Match** | `found:false`, **또는** `found:true && installed:false` | 2단계(생태계 검색)로 진행한다. `installed:false`이면 해당 후보를 2단계 결과의 우선 후보로 넘긴다(`source_repo` 기지) |

**[MUST] Reuse Before Install** — Exact Match 시 외부 검색(2단계 `npx skills find`)을 수행하지 않는다. 사용자가 **명시적으로** 다른 스킬 검색을 요청하면 그때 2단계로 진입한다(사용자 요청은 등급 판정과 별개 경로).

**2단계: 생태계 검색 + 후보 최대 3 선별**

```bash
npx skills find [query]
```

**[실측]** `npx skills find` 출력 필드는 3개뿐이다 — `owner/repo@skill`(스킬명) · 설치 수 · URL. `license`·`description` 필드는 출력에 없다 — 라이선스는 §2 3단(clone) 이후 저장소 루트 파일로만 확인 가능하다.

실행 결과에서 관련 스킬을 찾아 사용자에게 표시한다:

```
| 스킬명 | 설치 수 | 설치 |
|--------|--------|------|
| owner/repo@skill | 2.5K installs | //skill-manager 로 설치 요청 (clone-copy) |
```

라이선스 미확인 경고("⚠️ 라이선스 미확인")는 이 단계에서는 판정 불가하므로 표시하지 않는다 — §2 3단(clone) 완료 후 라이선스가 확정된 시점에 표시한다.

**후보 최대 3 선별** — 결과가 4건 이상이면 상위 3건만 §2 3단(clone)으로 보낸다. 선별 기준은 결정론적 순서다 — ① `source_repo` 있음 우선 ② `npx skills find` 출력 순서. 「관련성 높은 순」·라이선스 기준처럼 이 단계에서 얻을 수 없는 신호는 쓰지 않는다(라이선스는 `npx skills find` 출력에 없으며 §2 3단에서 clone 이후에만 확정된다). 계획했던 후보 수보다 실제 선별 수가 줄어든 경우(예: 4건 중 상위 3건만 선별) 그 사실을 사용자에게 보고한다 — 전수 비교로 오독되지 않도록 한다.

- 결과가 1~3건이면 그 전건을 후보로 보낸다.
- **결과가 0건이면** §2로 진행하지 않고 「적합 스킬 미발견 시 위임」(§1 말미) 절차로 분기한다.

**폴백 (npx 실행 실패 시):**

Node.js가 설치되어 있지 않으면 아래와 같이 안내한다:

```
npx 명령을 실행할 수 없습니다. 아래 방법으로 스킬을 검색해주세요:

- 웹 카탈로그: https://skills.sh/
- Node.js 설치 후: npx skills find [query]
```

**적합 스킬 미발견 시 위임**

아래 중 하나에서 `opal-skill-creator`로 위임한다:
- 2단계(skills.sh 검색) 결과 0건
- 4단(2층 판정) 후 잔존 후보 0건 (전 후보 `RISKY` 탈락 또는 `목적 적합 == 미달`)
- 사용자가 추천 후보를 전건 거부

[MUST] 위임 대상은 `opal-skill-creator`다. 외부 스펙안이 지칭하는 별도 생성기 컴포넌트를 OPAL에 신설하지 않는다.

**위임 페이로드**

| 필드 | 타입 | 내용 | creator 측 소비 지점 |
|------|------|------|---------------------|
| `requested_capability` | string | 사용자가 요구한 기능을 1~2문으로 정규화한 서술 | Capture Intent — 스킬 목적 |
| `requested_triggers` | string[] | 사용자 발화에서 추출한 트리거 표현 목록 | Capture Intent — 트리거 |
| `requested_output_format` | string | 기대 산출물 형식·경로 규약 | Capture Intent — 출력 형식 |
| `searched_sources` | string[] | 탐색한 소스 목록 (예: `["skills.sh (npx skills find \"{query}\")"]`) + 검색어 원문 | 재탐색 방지 (중복 탐색 억제) |
| `candidates_evaluated` | object[] | 후보별 `{name, source_repo, license, trust, shortfall}` — `shortfall`은 2층 비교 표의 `미달`/`부분` 축과 그 근거 인용(`SKILL.md:줄번호`) | Interview and Research — 에지 케이스·의존성 |
| `security_findings` | object[] | 후보별 `scan-risk` active hit 요약 `{name, verdict, capabilities[]}` | 신규 스킬이 회피해야 할 위험 행위 입력 |
| `skill_type_hint` | string | `"프레임워크 스킬"` \| `"OPAL 전용 스킬"` 중 추정값 (미정이면 `"미정"`) | 스킬 유형 판단 기준 |

**위임 방식**: `opal-skill-creator`의 SKILL.md를 Read하고 위 페이로드를 컨텍스트로 전달하여 Phase 1 신규 생성 모드로 진입한다. skill-manager는 skill-creator를 수정하지 않는다.

### 2. 스킬 설치 (clone-copy 단일 방식)

후보 선별 완료 후 아래 4단(3단~6단)을 순서대로 수행한다.

**[MUST] clone은 임시, 복사가 설치** — `git clone --depth 1`의 대상은 **임시 디렉토리**이며 clone 자체는 설치가 아니다. **설치는 `~/.opal/community-skills/{vendor}/{basename}/`로의 복사 시점에 성립**하므로, 승인 게이트는 6단(복사 직전) 1회를 유지한다.

**3단: 후보별 shallow clone**

후보(최대 3건) 각각에 대해:

1. `source_repo`(`owner/repo@subdir` 형식)를 파싱한다:
   ```bash
   node ~/.opal/tools/skill-registry/skill-registry.js parse-source-repo "{source_repo}"
   # → { owner, repo, subdir }  (`@` 미포함 시 subdir=repo)
   ```
2. 후보별로 별도 임시 디렉토리(`mktemp -d`)에 clone한다:
   ```bash
   git clone --depth 1 https://github.com/{owner}/{repo}.git {tmp}
   ```
3. 복사 원본 디렉토리를 아래 순서로 탐지한다 (upstream repo 레이아웃이 `owner/repo@subdir` 그대로가 아닐 수 있음 — 064 S-9 실증):
   1. `{tmp}/{subdir}/SKILL.md` 존재 → 그 디렉토리를 원본으로 채택
   2. 없으면 `{tmp}/skills/{subdir의 basename}/SKILL.md` 존재 → 그 디렉토리를 원본으로 채택
   3. 그래도 없으면 `find {tmp} -maxdepth 3 -type d -name {basename}` 결과 중 `SKILL.md`를 보유한 디렉토리를 원본으로 채택
   4. 그래도 없으면 해당 후보를 탈락시키고 탐색한 후보 경로 목록을 기록한다 (빈 디렉토리 복사 금지 — 이 후보는 4단 이후로 넘어가지 않는다)
4. commit_sha를 확보한다:
   ```bash
   git -C {tmp} rev-parse HEAD
   ```
5. 저장소 루트의 `LICENSE`/`LICENCE` 파일로 라이선스를 확인한다 — 파일이 있으면 그 내용에서 라이선스명(예: `MIT`, `Apache-2.0`)을 판별해 기록하고, 파일이 없으면 `Unknown`으로 취급한다. 이 값이 4단 「보안 4단 판정」 표의 「라이선스 조건」 열 입력이 된다. `Unknown`으로 확정된 후보에는 이 시점에 "⚠️ 라이선스 미확인" 경고를 표시한다.

**4단: 2층 판정**

3단에서 채택된 후보별 임시 디렉토리를 대상으로 1층 하드 필터 + 보안 4단 판정 + 2층 비교 표를 적용한다.

**1층 하드 필터**

각 후보 임시 디렉토리에 대해 위험 패턴 스캔 도구를 실행한다:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js scan-risk {tmp}
```

반환 JSON의 `verdict`(`SAFE`/`CAUTION`/`RISKY`/`UNKNOWN`)와 `hits[]`(각 `id`·`severity`·`capability`·`file`·`line`·`context`)를 아래 「보안 4단 판정」의 입력으로 쓴다. `context === "active"`인 hit만 판정에 반영하고 나머지(`prose`/`negated`/`comment`/`fixture`)는 억제 태그로만 기록한다. **[MUST] 1층은 필요조건이며 사람 검토를 대체하지 않는다** — 산문 영역(코드펜스·인라인 코드 스팬 밖)의 위험 지시는 이 도구가 탐지하지 못할 수 있으므로, RISKY가 아니라고 해서 무조건 안전을 의미하지 않는다.

**보안 4단 판정 (1층 결과 ↔ 4단 매핑)**

우선순위는 `RISKY` > `UNKNOWN` > `CAUTION` > `SAFE`이며 **가장 높은 단이 최종 판정**이다.

| 판정 | 1층 조건 (`scan-risk` 출력) | 라이선스 조건 | 판정 시 동작 |
|------|---------------------------|-------------|------------|
| **SAFE** | `ok:true` && `verdict == "SAFE"` (active hit 0건) | `license != "Unknown"` | **설치 진행** — 추가 게이트 없음. 6단 승인 1회만 |
| **CAUTION** | `ok:true` && `verdict == "CAUTION"` (active medium ≥1, active high 0) | `license != "Unknown"` | **확인 게이트** — 검출 목록(`id`·`capability`·`file:line`)을 표시하고 설치 여부를 묻는다 (y/N, 디폴트 `N`). **추천 후보에서 제외되지 않는다** — 후보가 1~2건뿐이어도 CAUTION 후보는 5단 추천 대상으로 실거동 승격한다 |
| **RISKY** | `ok:true` && `verdict == "RISKY"` (active high ≥1) | 무관 | **추천 후보에서 제외** — 5단 사다리 1단에서 탈락시키고 설치를 제안하지 않는다. 사용자가 명시적으로 강행을 요구하면 검출 목록 + high 항목을 재표시한 뒤에만 진행한다 |
| **UNKNOWN** | `ok:false` (디렉토리·SKILL.md 부재, 전 파일 skip) **또는** `verdict != "RISKY"`이면서 라이선스 미확인 | `license == "Unknown"` 또는 스캔 불가 | **추가 조사** — 후보로 유지하되 **추천 1순위로 올리지 않는다**. 현행 Unknown 라이선스 게이트 문안(아래 §6 2번)을 그대로 적용하고, 스캔 불가 사유를 함께 표시한다 |

[MUST] 보안 판정이 `RISKY`인 후보는 추천 후보에서 제외한다. 5단 사다리 1단과 동일 규칙이며 SSOT는 이 표다 — 사다리 쪽은 이 표를 참조한다.

**2층 비교 표 규격 (4축)**

RISKY로 제외되지 않은 후보를 아래 4축으로 비교한다. [MUST] 후보 비교는 3단 판정어와 실측값만으로 기술한다 — 수치를 매겨 자동 계산하는 방식은 재현 불가한 판정으로 회귀하므로 쓰지 않는다.

| 축 | 표기 방식 | 판정 기준 | 근거 인용 의무 |
|----|----------|----------|--------------|
| 목적 적합 | 3단 판정어 `충족` / `부분` / `미달` | 요청 capability를 스킬이 수행하는가 — `충족`=전량 / `부분`=일부 또는 우회 필요 / `미달`=미수행 | `SKILL.md:줄번호` |
| 출력 형식 호환 | 3단 판정어 `충족` / `부분` / `미달`, 또는 `해당 없음` | 요청한 출력 형식·경로 규약과 스킬의 산출물이 일치하는가. **사용자 요청에 출력 형식이 명시되지 않은 경우** 이 축은 판정하지 않고 `해당 없음`으로 표기한다(임의로 기본 형식을 가정하지 않는다) | `SKILL.md:줄번호` (해당 없음이면 생략) |
| 유지 활동 | **실측값** — 최신 커밋 ISO 날짜 (`git -C {tmp} log -1 --format=%cI`) | 명령 출력 그대로 | 명령 출력 |
| 부수효과 범위 | **실측값** — `active hit 수 / 최고 severity` (예: `2 / medium`) | `scan-risk` 출력의 `context=="active"` hit 집계 | `scan-risk` JSON |

[MUST] 각 3단 판정어 셀에는 판정 근거를 `SKILL.md:줄번호` 형식으로 병기한다.

**5단: 추천 1개**

4단 결과 위에서 아래 **추천 1개 결정 사다리**로 추천 후보 1건을 선정한다. 동률 시 다음 단으로 내려가는 **순서 있는 사다리**이며 수치를 더하거나 평균 내어 정하지 않는다. 「종합 판단」류 주관 표현은 쓰지 않는다.

| 순위 | 조건 | 처리 |
|------|------|------|
| 1 | 보안 판정이 `RISKY`인 후보 | **추천 후보에서 제외** (탈락, 이후 단 진입 없음) |
| 2 | `목적 적합 == 충족`인 후보가 유일 | 그 후보를 추천 |
| 3 | (2에서 복수) `출력 형식 호환 == 충족`인 후보가 유일 | 그 후보를 추천. **이 축이 `해당 없음`이면(사용자 요청에 출력 형식 미명시) 이 단을 건너뛰고 4단으로 내려간다** |
| 4 | (3에서 복수) `부수효과 범위`의 active hit 수가 최소인 후보가 유일 | 그 후보를 추천 |
| 5 | (4에서 복수) 유지 활동 최신 커밋 날짜가 가장 늦은 후보가 유일 | 그 후보를 추천 |
| 6 | 위 전 단에서 동률 | **자동 선택하지 않는다** — 동률 후보 목록을 표시하고 사용자 선택을 요청한다 |

- `목적 적합 == 미달`인 후보는 2단 이전에 탈락시킨다.
- 전 후보가 1단(RISKY 제외)에서 탈락하면 「적합 스킬 미발견 시 위임」(§1 말미) 절차로 분기한다.

**6단: 승인 → 복사·등록**

1. 추천 후보 1건과 추천 사유(4축 인용), 탈락 후보별 사유를 사용자에게 제시하고 설치 여부를 확인한다.
2. 채택된 원본을 아래 경로로 복사한다 (vendor·basename은 registry `name` 필드 기준이며, source_repo의 owner/subdir과 다를 수 있다):
   ```
   ~/.opal/community-skills/{vendor}/{basename}/
   ```
   3단의 탐지 결과가 빈 디렉토리이면 복사하지 않는다 (빈 디렉토리 복사 금지).
3. `~/.opal/community-skills/user-registry.json`에 설치 항목을 기록한다 (아래 「user-registry.json 기록 규칙」 참조).
4. 임시 디렉토리를 정리한다 — 5단에서 채택되지 않은 후보의 임시 디렉토리는 추천 확정 직후 즉시 삭제하고, 채택된 후보의 임시 디렉토리도 6단 복사·기록 완료 후 삭제한다. [MUST] 삭제 경로가 임시 디렉토리 하위임을 검증한 뒤 `rm -rf`를 수행한다 — §4 삭제 절차와 동일한 경로 검증 규율을 따른다.

**[MUST] `~/.opal/references/community-skills-registry.json`(프레임워크 카탈로그)은 설치 시 수정하지 않는다.** 이 파일은 install이 배포 시 덮어쓰는 파일이라 여기에 기록하면 다음 install 재실행 때 소실된다.

**user-registry.json 기록 규칙**
- 경로: `~/.opal/community-skills/user-registry.json`
- 스키마: 기존 7필드 + 판정 3필드 additive 추가 — `groups[vendor][] = [{ name, alias, description, triggers, source_repo, commit_sha, license, trust, capabilities, scanned_at }]`
- 부재 시 새로 생성, 존재 시 병합한다. 동일 `name` 항목이 이미 있으면 덮어쓴다(override), 없으면 추가한다.
- 이 파일은 `~/.opal/community-skills/` 하위에 있어 install이 절대 건드리지 않는다(카탈로그와 물리적으로 분리된 사용자 등록 영역).

**추가 3필드 정의**

| 필드 | 타입 | 값 | 출처 |
|------|------|----|------|
| `trust` | string | `"SAFE"` \| `"CAUTION"` \| `"RISKY"` \| `"UNKNOWN"` | 4단 판정(§2 4단) 최종값 |
| `capabilities` | string[] | active hit의 `capability` 라벨 중복 제거 목록 (예: `["network:outbound","secret:env"]`). active hit 0건이면 `[]` | `scan-risk` 출력 `hits[].capability` |
| `scanned_at` | string | ISO 8601 UTC (예: `"2026-09-02T04:11:00Z"`) | 4단 판정 확정 시각 |

[MUST] 기록은 `groups[vendor][] = [...]` 형상을 유지한다 — 다른 형상(flat 배열 등)은 `loadAllSkills()`의 병합 로직에서 조용히 무시되어 설치 이력이 유실된다.
[MUST] 위 3필드는 **user-registry.json에만** 기록한다. 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`)는 위 무수정 규칙을 그대로 따른다.

### 3. 설치된 스킬 목록

```bash
ls ~/.opal/community-skills/
```

벤더별로 그룹핑하여 표시한다. registry(카탈로그+user-registry 병합)와 대조하여 보여준다:

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list --group=community
```

### 4. 스킬 삭제

사용자가 삭제를 요청하면:

1. 삭제 대상 확인 (벤더/스킬명)
2. 삭제 대상 경로가 `~/.opal/community-skills/` 하위인지 검증한 뒤 해당 디렉토리(`~/.opal/community-skills/{vendor}/{skill}/`)를 `rm -rf`로 삭제한다
3. `~/.opal/community-skills/user-registry.json`에 해당 항목이 있으면 제거한다
4. 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`)는 수정하지 않는다 — 카탈로그는 "설치 가능 목록"이므로 삭제와 무관하게 유지된다
5. 결과 보고

### 5. 스킬 업데이트 확인

1. 대상 스킬의 `source_repo`(`owner/repo@subdir`)에서 owner/repo를 추출한다
2. 업스트림 최신 커밋을 조회한다:
   ```bash
   git ls-remote https://github.com/{owner}/{repo}.git HEAD
   ```
3. `~/.opal/community-skills/user-registry.json`에 기록된 `commit_sha`와 비교한다
   - **불일치** 또는 `commit_sha == null`(레거시 — 고정 기록 없음) → 재설치(§2 clone-copy)를 제안한다
   - 일치 → "최신 상태입니다"로 안내한다
4. `npx skills check`는 보조 확인용으로 계속 사용할 수 있다 (네트워크·CLI 실패 시에도 위 ls-remote 비교가 주 판정 경로).

## 설치 경로 규칙 (이원 registry 경계)

커뮤니티 스킬은 OPAL 내부(`~/.opal/community-skills/`)에만 설치한다. 플랫폼 네이티브 skills/ 디렉토리에는 복사하지 않는다.

```
~/.opal/community-skills/
├── anthropics/
│   ├── docx/SKILL.md
│   └── pdf/SKILL.md
├── vercel-labs/
│   └── react-best-practices/SKILL.md
├── trailofbits/
│   └── modern-python/SKILL.md
└── user-registry.json          ← 사용자 설치 등록분 (install 불가침)
```

registry는 **이원 구조**다:

| 구분 | 경로 | SSOT | install과의 관계 |
|------|------|------|------------------|
| 프레임워크 카탈로그 | `~/.opal/references/community-skills-registry.json` | OPAL 배포 | install이 배포 시 항상 덮어씀 — 직접 수정 금지(설치/삭제 시 이 파일을 갱신하지 않는다) |
| 사용자 등록분 | `~/.opal/community-skills/user-registry.json` | 사용자 설치 이력 | install이 절대 건드리지 않음(142 D-4) — §2 설치, §4 삭제 시 이 파일만 갱신 |

`loadAllSkills()`(skill-registry.js)가 두 파일을 병합 로드하여 `match`/`list`/`validate`에 반영한다 (동일 `name`은 사용자 항목 우선).

## 참고

- 스킬 검색 엔진: [skills.sh](https://skills.sh/) (vercel-labs/skills) — `npx skills find`/`npx skills check`는 검색·업데이트 확인 보조 용도로 유지한다
- 설치: **clone-copy 단일 방식** (§2) — `npx skills add`는 사용하지 않는다
- 설치 위치: `~/.opal/community-skills/{vendor}/{skill}/SKILL.md`
- 레지스트리: 카탈로그(`~/.opal/references/community-skills-registry.json`) + 사용자 등록분(`~/.opal/community-skills/user-registry.json`) 병합 (위 이원 구조 참조)

### 6. `// 커맨드` 미설치 매칭 시 자동 설치·실행

PM이 `//pdf` 같은 community 트리거를 매칭했는데 skill-registry가 `installed: false`로 응답하면,
**라이선스가 확인된 스킬은 동의 대기 없이 자동으로 clone-copy 설치·실행**한다. 문제 있는 라이선스(미확인, Unknown)만 게이트한다.

> 근거: 소유자 확정 — "문제 있는 라이선스만 아니면 무조건 설치·실행" (064).

**분기 판정** (skill-registry `match` 응답의 `license`·`source_repo`·`ambiguous` 기준):

1. `license ≠ "Unknown"`(라이선스 확인됨) + `source_repo` 있음 → **자동 설치·실행** (동의 prompt 없음):
   - **§2 clone-copy 절차**의 clone 직후·복사 직전에 `node ~/.opal/tools/skill-registry/skill-registry.js scan-risk {tmp}`를 1회 실행한다. `verdict == "RISKY"`이면 자동 설치를 중단하고 검출 목록(`id`·`capability`·`file:line`)을 표시한다.
   - RISKY가 아니면 비차단 통지 1줄만 표시:
     ```
     [자동 설치] {source_repo} · {license} · commit {commit_sha || "미고정(HEAD)"} · trust {verdict}
     ```
   - **§2 clone-copy 절차**를 실행한다 (`git clone` → `scan-risk` → 복사 → commit_sha 확보 → user-registry.json 기록)
   - 설치 완료 후 `~/.opal/community-skills/{vendor}/{skill}/SKILL.md`를 Read하여 즉시 절차 실행
2. `license == "Unknown"`(라이선스 미확인) → **설치 전 확인 게이트 유지** (자동 우회 금지):
   ```
   이 스킬은 라이선스가 확인되지 않았습니다 (Unknown License) — proceed at your own risk.
   - 출처: {source_repo}
   - commit SHA: {commit_sha || "미고정 (HEAD 가변)"}

   정말로 설치하시겠습니까? (y/N)
   ```
   - 디폴트는 `N` (입력 없이 Enter 시 거부)
   - 수락(`y`): **§2 clone-copy 절차** 실행 → SKILL.md Read → 즉시 절차 실행
   - 거부(`N`): "수동 설치는 `//skill-manager`로 — `npx skills find {keyword}`로 검색 후 설치하세요" 안내 후 종료
   - §1 스킬 검색 결과에서도 Unknown 라이선스 항목에는 "⚠️ 라이선스 미확인" 경고를 표시한다.
3. `source_repo`가 `null` (registry에 미등재):
   - "이 스킬은 vercel-labs/skills 카탈로그에 미등재. 수동 설치는 `//skill-manager`로" 안내
4. `ambiguous: true` (basename이 여러 vendor와 충돌, F-002):
   - `candidates` 목록(vendor별 name·source_repo·license·installed)을 표시하고, 정식명(`vendor/skill`)으로 재호출을 유도한다. 자동 선택하지 않는다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.1 | 2026-05-10 17:00 KST | "기본 번들 31개" 표현 제거 + fetch 흐름 SSOT 강조 + `// 커맨드` 미설치 매칭 시 자동 fetch 흐름 추가 (142) |
| v1.2 | 2026-05-10 21:00 KST | Unknown 라이선스 두 번째 확인 + commit_sha 노출 + 빨간 경고 메시지 추가 (144) |
| v1.3 | 2026-07-16 14:59 KST | §6 미설치 매칭 → 자동 설치·실행 (라이선스 확인 스킬 동의 게이트 제거, Unknown만 게이트 유지) (064) |
| v1.4 | 2026-07-17 09:17 KST | 검색·설치·제거·업데이트 4절차를 clone-copy 단일 방식으로 재작성 + 관리 진입 시 `migrate` 훅 명시 + user-registry.json 이원 registry 경계 명문화 + `npx skills add` 전량 제거(find/check는 보조 유지) + §6 ambiguous 분기 추가 (064) |
| v1.4.1 | 2026-07-17 09:26 KST | §2 설치 절차 3단계에 복사 원본 탐지 폴백 추가 — `{tmp}/{subdir}/SKILL.md` → `{tmp}/skills/{basename}/SKILL.md` → `find` 탐색 → 실패 시 후보 목록 보고하고 중단(빈 설치 금지). anthropics/skills 카탈로그가 `skills/{name}/` 중첩 레이아웃임을 실 clone으로 확인(064 S-9 fix) |
| v1.4.2 | 2026-09-02 17:22 KST | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |
| v1.5 | 2026-09-03 00:52 KST | §1·§2를 6단 흐름(skills.sh 검색 → 후보 최대 3 선별 → shallow clone → 2층 판정 → 추천 1개 → 승인 → 복사·등록)으로 재작성 + 보안 4단 판정(SAFE/CAUTION/RISKY/UNKNOWN) 신설 + 1층 하드 필터 `scan-risk` 서브명령 도구화 + 2층 비교 표 4축(3단 판정어·실측값 기반, 수치 채점 방식 폐기) + Match 3등급화(Exact/Partial/No Match) + user-registry `trust`/`capabilities`/`scanned_at` additive 추가 + `opal-skill-creator` 위임 계약 (105) |
| v1.5.1 | 2026-09-03 22:56 KST | §1 2단계 후보 선별 기준에서 실행 불가한 `license` 조건 제거(`npx skills find` 출력에 license 필드 없음을 실측 명시) + 라이선스 확인 시점을 §2 3단(clone 이후 LICENSE/LICENCE 파일 확인)으로 이동 + 2단계 표시 템플릿에서 미출력 `설명` 열 제거 + 2층 비교 표 「출력 형식 호환」 축에 요청 미명시 시 `해당 없음` 규칙 추가 + 추천 사다리 3단에 `해당 없음`일 때 4단으로 스킵하는 처리 명시 (105) |
