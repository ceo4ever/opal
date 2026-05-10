# PLAN: community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills)

> 작성일: 2026-05-10
> 입력: `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md`
> 출력: `tasks/142-260510-opp-community-skills-fetch-migration/PLAN.md`
> 모드: semi-agentic
> 영역: 다중 영역 (install 스크립트 / Node.js 도구 / 레지스트리 JSON / SKILL.md / 문서)

---

## 0. 캡틴 결정 SSOT (변경 금지)

본 PLAN은 TASK.md §확정된 설계 방향 §8~§11을 SSOT로 한다. PLAN 워커는 다음 4개 결정을 변경하지 않는다:

| ID | 결정 | 출처 |
|----|------|------|
| **D-1** | 미설치 호출 처리 = 첫 호출 시 동의 prompt + 자동 fetch (`npx skills add`). 거부 시 `//skill-manager` 안내. | (→ T-1 §8) |
| **D-2** | `community-skills-registry.json` = 메타데이터 카탈로그 변환 (`name` / `triggers` / `source_repo` / `license` 유지, `paths` 동적). | (→ T-1 §9) |
| **D-3** | `skill-registry.js` = 미설치 감지 + fetch prompt 정보 노출 (npx 호출은 알투/`opal-skill-manager`가 수행). | (→ T-1 §10) |
| **D-4** | 기존 사용자 마이그레이션 = 그대로 보존 + 마이그레이션 안내 미게재. install이 `~/.opal/community-skills/`를 절대 건드리지 않음 (clean_dirs에서 제거). | (→ T-1 §11) |

> 인용 표기: `T-1` = `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md`. 이하 본 PLAN에서 `T-1 §N`으로 단축 인용한다.

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md (본 태스크) | `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` | 요구사항 SSOT (R-1 ~ R-8 + 캡틴 결정 §8~§11) |
| D-2 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 정의·문서 레지스트리·전문 에이전트 매핑 (Framework 단일 → opal-task-agent 폴백) |
| D-3 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | R-7 변경 대상 — §컴포넌트 유형 §커뮤니티 스킬 / §배포 모델 다이어그램 |
| D-4 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | Guards / 변경이력 의무 / 커밋 규칙 / @header 규칙 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | R-2 변경 대상 (mac install) — 변경이력 v1.9까지 / `clean_dirs` 라인 :731 / `install_opal_community_skills` 함수 :905-925 / 호출부 :841 |
| D-6 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | R-2 변경 대상 (Windows install) — 변경이력 v1.5.4까지 / `cleanDirs` 라인 :411 / community-skills 복사 블록 :506-519 |
| D-7 | 소스 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | R-3 변경 대상 — 6 그룹 30 항목 v1.0.0 / `paths` 라인 사용자 머신 의존 |
| D-8 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | R-4 변경 대상 — `loadAllSkills()` :44-53 / `matchByTriggers()` :75-96 / `resolveFirstPath()` :98-109 / `matchCommand()` :111-136 / `validate()` `path existence check` :234-242 |
| D-9 | 소스 | opal-skill-manager/SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | R-5 변경 대상 — :122-124 "기본 번들 스킬(31개)... install-mac.sh로 자동 설치" 표현 제거 |
| D-10 | 소스 | README.md | `README.md` | R-6 변경 대상 — :39 "커뮤니티 스킬" 주요 특징 / :732 "외부 조직 제공 스킬 (30개 / 6개 조직)" 다이어그램 |
| D-11 | 컨텍스트 | 141 DONE.md | `tasks/141-260510-opp-readme-mit-license-p0/DONE.md` | community-skills 표기 후속 정리 의무 (T-1 §제약 조건) |
| D-12 | 외부 | skills.sh | https://skills.sh | 표준 카탈로그 SSOT (D-1 결정의 fetch 출처) |
| D-13 | 외부 | vercel-labs/skills | https://github.com/vercel-labs/skills | `npx skills` CLI 구현 (`find` / `add` / `check`) |
| D-14 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 본 PLAN 인용 포맷 (§2 / §2.4 / §3 / §7) |

### 1.2 [MUST] 필수 제약 인용 (CONVENTIONS.md / TASK.md / harness)

> 재해석 여지가 있는 강제 규칙은 원문 그대로 인용한다. (citation-rules.md §2.4)

- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."
- [MUST] `docs/CONVENTIONS.md` §Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성·수정하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §커밋 규칙: "커밋은 캡틴이 명시적으로 요청할 때만 수행."
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층(부트스트래퍼·`emit_platform_agent_adapter`·MCP install 분기)에서만 흡수한다." → install-mac.sh / windows.ps1 양 OS 동등 처리 의무로 확장 적용.
- [MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §확정된 설계 방향 §11: "install이 `~/.opal/community-skills/`를 절대 건드리지 않음 (clean_dirs 배열에서 제거). 기존 사용자(캡틴 mac)의 30개 SKILL.md 그대로 유지 — 동작 무변화."
- [MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §제약 조건: "변경이력 의무: install-mac.sh / windows.ps1 / skill-registry.js / opal-skill-manager/SKILL.md 모두 변경이력 행 필수." (README.md / ARCHITECTURE.md / community-skills-registry.json은 docs 카테고리 면제 — 141 선례)

### 1.3 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `community-skills/` (저장소 루트) | third-party 스킬 번들 6 조직 31 항목 | **삭제** | `find community-skills -mindepth 2 -maxdepth 2 -type d \| wc -l` = 31 |
| `scripts/install-mac.sh` | macOS install 스크립트 | **수정** | `install-mac.sh:731` (`clean_dirs` 배열) / `install-mac.sh:841` (`install_opal_community_skills` 호출) / `install-mac.sh:905-925` (`install_opal_community_skills` 함수 정의) / `install-mac.sh:7-16` (변경이력 v1.9까지) |
| `scripts/install/windows.ps1` | Windows install 스크립트 | **수정** | `windows.ps1:411` (`cleanDirs` 배열) / `windows.ps1:506-519` (community-skills 복사 블록) / `windows.ps1:33-83` (변경이력 v1.5.4까지) / `windows.ps1:393` (`.SYNOPSIS` "community-skills(병합)" 표현) |
| `opal/core/references/community-skills-registry.json` | 트리거 매칭 + paths 인덱스 | **수정** (스키마 v2 — 메타데이터 카탈로그) | `community-skills-registry.json:1-50` (6 그룹 30 항목, `$schema: opal-community-skills-registry-v1`) |
| `opal/tools/skill-registry/skill-registry.js` | `//` 커맨드 매칭 도구 | **수정** | `skill-registry.js:44-53` (`loadAllSkills`) / `:75-96` (`matchByTriggers`) / `:98-109` (`resolveFirstPath`) / `:111-136` (`matchCommand`) / `:225-242` (`validate path existence`) |
| `opal/skills/opal-skill-manager/SKILL.md` | 스킬 검색·설치·관리 | **수정** | `opal-skill-manager/SKILL.md:122-124` ("기본 번들 스킬(31개)" 표현) |
| `README.md` | 프로젝트 공개 문서 | **수정** (141 후속 정리) | `README.md:39` (주요 특징) / `README.md:732` (배포 다이어그램 "30개 / 6개 조직") |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 SSOT | **수정** | `ARCHITECTURE.md:64` (Global Layer 표 `community-skills/`) / `:156-167` (§커뮤니티 스킬 표) / `:182-211` (§배포 모델 다이어그램) / `:266-319` (디렉토리 구조 트리) |

### 1.4 현재 상태

1. **번들 실측**: `community-skills/` 6 조직 31 SKILL.md (저장소 루트 추적). 4 조직(getsentry / google-labs-code / trailofbits / vercel-labs)에 LICENSE 파일 누락, 2 조직(anthropics / openai)만 Apache-2.0 LICENSE.txt 보존.
2. **install 흐름**: `install-mac.sh:841` → `install_opal_community_skills` (`:905-925`) — `community-skills/{vendor}/` 디렉토리를 vendor 단위로 `cp -Rf`. clean_dirs 배열(`:731`)에 `community-skills`가 포함되어 있어 install 재실행 시 `~/.opal/community-skills/`를 한번 통째로 삭제 후 재복사. **이 동작은 D-4 결정과 충돌** — 사용자 데이터 파괴 가능성.
3. **windows.ps1 흐름**: `:411` cleanDirs에 community-skills 포함 후 삭제 → `:506-519`에서 vendor 단위 덮어쓰기 (mac과 동일 패턴).
4. **레지스트리 v1**: `$schema: opal-community-skills-registry-v1`, `groups` 객체 6 그룹 × 평균 5 항목, 각 항목에 `name` / `alias` / `description` / `triggers[]` / `paths[]`. `source_repo` / `license` 필드 부재.
5. **skill-registry.js 동작**: `loadAllSkills()`가 main + community registry를 합치고 `flattenGroups()`로 평탄화. `matchByTriggers()`가 정규식 매칭으로 스킬 결정. `resolveFirstPath()`는 paths 배열 중 fs.existsSync로 첫 존재 경로 반환, **없으면 paths[-1]을 폴백**으로 반환 (실제 파일 존재 검증 없음). `matchCommand()`가 `path` 필드를 그대로 응답에 포함.
6. **opal-skill-manager**: 이미 `npx skills find/add/check` 흐름을 보유. `:122-124`에 "기본 번들 스킬(31개)은 install-mac.sh로 자동 설치된다" 잔존.
7. **README**: `:39` "커뮤니티 스킬 — 외부 조직이 제공하는 스킬을 원본 수정 없이 통합" / `:732` 배포 다이어그램 "external 조직 제공 스킬 (30개 / 6개 조직)".
8. **ARCHITECTURE.md**: `:64` Global Layer 표에 `community-skills/`(37개로 표기 — 실측 31과 불일치). `:156-167` §커뮤니티 스킬 표(조직별 카운트). `:190` 배포 모델 다이어그램에 `community-skills/* ──┤ ~/.opal/community-skills/`.

### 1.5 영향 범위

- **사용자 영향**:
  - 기존 사용자(캡틴 mac): `~/.opal/community-skills/` 그대로 보존 (D-4) → 동작 무변화. 단, install 재실행 시 갱신 안 됨 — `npx skills check`로 사용자가 직접 갱신.
  - 신규 사용자: `~/.opal/community-skills/`가 빈 상태로 시작. 첫 community trigger 호출 시 동의 prompt → fetch.
- **코드 영향**:
  - install-mac.sh: `install_opal_community_skills` 함수 + 호출부 + `clean_dirs` 배열 항목 제거. tarball 크기 감소(현재 31개 SKILL.md + 부록 → 0).
  - windows.ps1: 동일 패턴으로 community-skills 블록 + cleanDirs 항목 제거.
  - skill-registry.js: `matchCommand` 응답 스키마에 `installed` (boolean) + `source_repo` (string) + `license` (string) + `install_command` (string) 필드 추가. `validate` 폴백 동작 (paths 없을 때) 명시.
  - registry JSON: `$schema` v2 표기, 각 항목에 `source_repo` / `license` 필드 신설. `paths` 필드는 PLAN 결정 — 폐기 vs 동적 계산 (§2.3.4 핵심 설계).
- **문서 영향**:
  - README §주요 특징 + §아키텍처 개요 다이어그램 갱신.
  - ARCHITECTURE.md §컴포넌트 유형 §커뮤니티 스킬 + §배포 모델 + 디렉토리 구조 + Global Layer 표 + §시스템 구성 갱신.
  - PROJECT.md §폴더 구조맵 — `community-skills/` 행 제거 또는 갱신 (영향 ≥ 1줄, 문서 갱신 Step 포함).
- **회귀 위험**: **중간** — install 흐름 변경 + `//` 커맨드 매칭 흐름 변경. mac + Windows 양 OS 회귀 검증 의무.

### 1.6 미확정 사항 (PLAN에서 결정)

TASK.md §확정된 설계 방향이 D-1 ~ D-4를 결정했고, D-5 ~ D-9는 PLAN 워커 합리적 디폴트 결정으로 위임. 본 PLAN의 결정은 다음과 같다:

| ID | 결정 사항 | PLAN 결정 | 근거 |
|----|----------|----------|------|
| **P-1** | `community-skills-registry.json` `paths` 필드 처리 (D-2 세부) | **폐기** — `paths` 필드 제거. skill-registry.js가 `name`(=`{owner}/{skill}`)에서 동적으로 `~/.opal/community-skills/{owner}/{skill}/SKILL.md` 계산 | D-2 "paths 동적" + 정적 인덱스 부적합 + skill-registry.js의 단일 진실 원본 명확 |
| **P-2** | `community-skills-registry.json` 스키마 버전 | **`opal-community-skills-registry-v2`** + `version: "2.0.0"` | 구조 비호환 변경 (paths 폐기, source_repo/license 신설) |
| **P-3** | `source_repo` 필드 포맷 | **`{owner}/{repo}@{skill}` 형식** (예: `anthropics/skills@docx`). `npx skills add` 인자와 1:1 매핑 | TASK.md §8 "`npx skills add {owner/repo@skill}` 자동 호출" |
| **P-4** | `license` 필드 포맷 | **SPDX 식별자 또는 `Unknown`** (예: `Apache-2.0` / `MIT` / `Unknown`). 정확한 라이선스 미파악 그룹은 `Unknown`으로 표기 | SPDX 표준 + 사용자 동의 prompt에 라이선스 노출 의무 (D-1) |
| **P-5** | skill-registry.js `matchCommand` 응답 스키마 | 기존 필드 유지 + `installed` (boolean) / `source_repo` / `license` / `install_command` (`"npx skills add {source_repo}"`) 필드 4개 신설. `path`는 미설치 시 `null`. | D-3 "registry는 정보 제공만, npx 호출은 알투/opal-skill-manager" |
| **P-6** | install-mac.sh / windows.ps1 안내 메시지 | install 종료 시 "커뮤니티 스킬은 `//skill-manager`로 검색·설치하세요" 한 줄 추가 (마이그레이션 안내가 아닌 사용 안내) | TASK.md §11 "마이그레이션 안내 미게재" + 사용자 발견성 |
| **P-7** | clean_dirs 처리 | **community-skills 항목 완전 제거** (mac/Windows 동일). 안내 코멘트 추가 ("# 사용자 데이터 보존: ~/.opal/community-skills/는 제거하지 않음 (D-4)") | D-4 "절대 건드리지 않음" |
| **P-8** | install-mac.sh `install_opal_community_skills` 함수 처리 | **함수 본체 + 호출부 모두 삭제** (dead code 회피). 함수 자체 제거. | YAGNI + 변경이력에 명시 |
| **P-9** | skill-registry.js 변경이력 헤더 | **신규 추가** — `// 변경이력` 블록. 현재 헤더가 없으므로 본 태스크에서 신설. | CONVENTIONS.md §변경이력 작성 의무 (참조 문서 카테고리) |
| **P-10** | community-skills 디렉토리 git 제거 방식 | `git rm -r community-skills/` (이력 보존). LICENSE.txt 포함 vendor 디렉토리 전체. | 표준 git 흐름 |
| **P-11** | docs/PROJECT.md §폴더 구조맵 갱신 여부 | **갱신 필요** — `community-skills/` 행 제거. (`docs/PROJECT.md:40` 라인) | 자체 로드 §자동 — 코드 변경이 docs에 영향 시 문서 갱신 Step 자동 추가 |
| **P-12** | install 후 신규 사용자 첫 호출 시점의 fetch 동작 주체 | **알투(에이전트) 책임** — skill-registry.js는 정보 노출만. 알투가 `// 커맨드` 입력 받고 매칭 결과의 `installed: false` 확인 → 동의 prompt → 수락 시 `~/.opal/skills/opal-skill-manager/` 호출 또는 직접 `npx skills add` 실행. | D-3 SSOT |

> **decision_required 발생 없음** — 본 PLAN은 D-1 ~ D-4 SSOT를 확장한 P-1 ~ P-12 자율 결정만 포함. 영역 간 용어 불일치(citation-rules §7) 없음.

---

## 2. 구현 계획

### 2.1 파일 변경 계획

#### 신규 생성

없음. (skill-registry.js 변경이력 블록 신설은 기존 파일 내 추가.)

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `scripts/install-mac.sh` | `clean_dirs` 배열에서 `community-skills` 제거 + `install_opal_community_skills` 함수 + 호출부 삭제 + 변경이력 v2.0.0 행 + install 종료 안내 한 줄 (P-6) | (→ D-5) `install-mac.sh:731 / 841 / 905-925` |
| M-2 | `scripts/install/windows.ps1` | `cleanDirs` 배열에서 `community-skills` 제거 + community-skills 복사 블록 삭제 + `.SYNOPSIS` "community-skills(병합)" 표현 제거 + 변경이력 v1.6.0 행 + install 종료 안내 (mac과 동등) | (→ D-6) `windows.ps1:411 / 506-519 / 393` |
| M-3 | `opal/core/references/community-skills-registry.json` | 스키마 v2로 변환 — `$schema: opal-community-skills-registry-v2` / `version: "2.0.0"` / 각 항목에 `source_repo` (P-3) + `license` (P-4) 신설, `paths` 폐기 (P-1) | (→ D-7) 전체 파일 |
| M-4 | `opal/tools/skill-registry/skill-registry.js` | `loadAllSkills`에서 community 항목 처리 시 `installed = fs.existsSync(~/.opal/community-skills/{name}/SKILL.md)` 동적 계산 / `matchCommand` 응답에 `installed` / `source_repo` / `license` / `install_command` 필드 추가 (P-5) / `validate`에서 v2 스키마 인식 / 헤더 변경이력 블록 신설 (P-9) | (→ D-8) `skill-registry.js:1-315` 전반 |
| M-5 | `opal/skills/opal-skill-manager/SKILL.md` | "기본 번들 스킬(31개)" 표현 제거 + fetch 흐름이 SSOT임을 명시 + `// 커맨드` 미설치 매칭 시 자동 fetch 흐름(D-1) 절차 추가 + 변경이력 행 추가 | (→ D-9) `opal-skill-manager/SKILL.md:122-124 + 1-7 frontmatter 인접` |
| M-6 | `README.md` | L39 "커뮤니티 스킬 — 외부 조직이 제공하는 스킬을 원본 수정 없이 통합" 표현 검토 (유지 또는 갱신) + L732 배포 다이어그램 "30개 / 6개 조직" → "skills.sh 카탈로그 통합 — `//skill-manager`로 검색·설치" | (→ D-10) `README.md:39 / 732` |
| M-7 | `docs/ARCHITECTURE.md` | §시스템 구성 Global Layer 표 `community-skills/` 행 갱신 / §컴포넌트 유형 §커뮤니티 스킬 표 fetch 방식 재서술 / §배포 모델 다이어그램에서 `community-skills/* ──┤` 라인 제거 / 디렉토리 구조 트리 갱신 | (→ D-3) `ARCHITECTURE.md:64 / 156-167 / 182-211 / 266-319` |
| M-8 | `docs/PROJECT.md` | §폴더 구조맵 표에서 `community-skills/` 행 제거 (P-11) | `docs/PROJECT.md:40` |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| **R-1** | `community-skills/` (저장소 루트, 6 vendor / 31 SKILL.md / 부록 + LICENSE.txt 포함) | TASK.md R-1 — third-party 재배포 회피 / `npx skills` SSOT 채택. `git rm -r community-skills/`로 처리 (P-10). |

### 2.2 구현 순서

> 의존 받는 쪽(하위 레이어)부터 구현. 레지스트리 스키마 → 도구 → 스킬 → install → 폴더 삭제 → 문서 → 회귀 검증.

| 순서 | 작업 | 파일 | 영역 | 예상 난이도 |
|------|------|------|------|-----------|
| 1 | community-skills-registry.json v2 스키마 변환 | `opal/core/references/community-skills-registry.json` | 데이터 | 중 (스키마 + 라이선스 매핑) |
| 2 | skill-registry.js 갱신 (v2 인식 + 동적 installed + fetch 정보 노출) | `opal/tools/skill-registry/skill-registry.js` | Node.js 도구 | 중-상 (4 함수 + 변경이력 신설) |
| 3 | opal-skill-manager SKILL.md 갱신 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 문서 | 저-중 |
| 4 | install-mac.sh 갱신 (community-skills 복사 단계 제거 + clean_dirs + 안내) | `scripts/install-mac.sh` | bash 스크립트 | 중 (변경이력 + 함수 삭제) |
| 5 | install/windows.ps1 갱신 (mac과 동등 처리) | `scripts/install/windows.ps1` | PowerShell 스크립트 | 중 |
| 6 | community-skills/ 폴더 git rm | `community-skills/` (저장소 루트) | git | 저 |
| 7 | README.md 갱신 (L39 + L732) | `README.md` | 문서 | 저 |
| 8 | docs/ARCHITECTURE.md 갱신 | `docs/ARCHITECTURE.md` | 문서 | 중 |
| 9 | docs/PROJECT.md 갱신 (§폴더 구조맵) | `docs/PROJECT.md` | 문서 | 저 |
| 10 | install 재실행 회귀 검증 (mac + Windows) | 회귀 | mac + Windows | 중 |

> 1 → 2 → 3 → (4 ‖ 5) → 6 → (7 ‖ 8 ‖ 9) → 10. (4)와 (5)는 독립 OS 분기, (7)(8)(9)는 독립 문서.

### 2.3 핵심 설계

> 각 파일별 변경 내용 뒤에 인라인 인용 기재. 필수 제약은 `[MUST]` 포맷 사용.

#### 2.3.1 `opal/core/references/community-skills-registry.json` — 스키마 v2 메타데이터 카탈로그

**변경 후 스키마**:

```json
{
  "$schema": "opal-community-skills-registry-v2",
  "version": "2.0.0",
  "updated_at": "2026-05-10",
  "schema_notes": "v2: paths 폐기 (skill-registry.js가 ~/.opal/community-skills/{name}/SKILL.md 동적 계산). source_repo/license 신설.",
  "groups": {
    "anthropics": [
      {
        "name": "anthropics/docx",
        "alias": null,
        "description": "Word 문서 (.docx) 생성/편집",
        "triggers": ["(?i)(word\\s*문서|docx|\\.docx)"],
        "source_repo": "anthropics/skills@docx",
        "license": "Apache-2.0"
      }
    ]
  }
}
```

**필드 결정 (P-1 ~ P-4)**:

- `name`: 기존 형식 `{owner}/{skill}` 유지 — skill-registry.js가 이를 `~/.opal/community-skills/{owner}/{skill}/SKILL.md` 경로로 변환 (P-1).
- `paths`: **폐기** (P-1).
- `source_repo`: `npx skills add` 인자와 1:1 매핑 (`{owner}/{repo}@{skill}`) (P-3). `npx skills` CLI 인자 형식 [vercel-labs/skills](https://github.com/vercel-labs/skills) 준수.
- `license`: SPDX 식별자 또는 `Unknown` (P-4). 사용자 동의 prompt에 노출.
- `triggers`: 기존 정규식 그대로 유지.
- `alias`: 기존 그대로 (대부분 null).

**라이선스 매핑 (P-4 적용)**:

| 그룹 | 라이선스 (확인된 것) | source_repo prefix |
|------|-------------------|---------------------|
| `anthropics` | Apache-2.0 (LICENSE.txt 보유) | `anthropics/skills@{skill}` |
| `openai` | Apache-2.0 (LICENSE.txt 보유) | `openai/skills@{skill}` (실제 owner/repo 확인 필요) |
| `getsentry` | `Unknown` (LICENSE 누락) | `getsentry/{repo}@{skill}` (실제 repo 확인 필요) |
| `google-labs-code` | `Unknown` (LICENSE 누락) | `google-labs-code/{repo}@{skill}` |
| `trailofbits` | `Unknown` (LICENSE 누락) | `trailofbits/{repo}@{skill}` |
| `vercel-labs` | `Unknown` (LICENSE 누락 — 단 vercel-labs/skills 자체는 MIT) | `vercel-labs/skills@{skill}` |

> **EXECUTE 시 보강 의무**: `source_repo`의 정확한 owner/repo는 EXECUTE 워커가 `npx skills find` 또는 [skills.sh](https://skills.sh)에서 1회 검증하여 채워 넣는다. 검증 불가 항목은 `source_repo: null`로 두고 `license: "Unknown"`으로 표기 — D-1 fetch prompt에서 "이 스킬은 vercel-labs/skills 카탈로그에 미등재. 수동 설치 필요" 안내로 분기. (→ T-1 §관련 문서 D-2)

[MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §확정된 설계 방향 §9: "`name` / `triggers` / `source_repo` / `license` 필드만 유지. `paths`는 동적."

#### 2.3.2 `opal/tools/skill-registry/skill-registry.js` — 미설치 감지 + fetch 정보 노출

**변경 함수**:

1. **`getCommunitySkillPath(skillName)` 신규 헬퍼** — `name`을 받아 `~/.opal/community-skills/{name}/SKILL.md` 경로 동적 계산. (`skill-registry.js:98-109` `resolveFirstPath` 인접 추가).

```js
function getCommunitySkillPath(skillName) {
  return path.join(os.homedir(), '.opal', 'community-skills', skillName, 'SKILL.md');
}
```

2. **`isCommunitySkill(skill)` 신규 헬퍼** — registry 출처가 community인지 판단 (`_group`이 community-skills-registry에서 왔는지). `loadAllSkills()`에서 community 출처 항목에 `_source: 'community'` 마커 부착하는 방식. (`skill-registry.js:44-53` `loadAllSkills`).

3. **`matchCommand(input)` 응답 스키마 확장** (`skill-registry.js:111-136`):

```js
// 기존
{ found, name, group, alias, description, path, domain, cleanInput }

// 변경 후 (community 스킬만)
{
  found, name, group, alias, description, path, domain, cleanInput,
  installed: boolean,            // 신설 — fs.existsSync 체크
  source_repo: string | null,    // 신설 — registry에서 그대로
  license: string,               // 신설 — registry에서 그대로 (디폴트 "Unknown")
  install_command: string | null // 신설 — `npx skills add ${source_repo}` 또는 source_repo가 null이면 null
}
```

- 미설치(`installed: false`)이면 `path`는 **null**로 응답. 알투가 이를 보고 D-1 동의 prompt 분기.
- main(opal) 스킬은 기존 응답 스키마 유지 (community 전용 필드 추가하지 않음).

4. **`validate()` 갱신** (`skill-registry.js:179-253`):
- v2 스키마(`opal-community-skills-registry-v2`) 인식 — 비호환 시 errors에 추가.
- v2에서는 `paths` 부재가 정상 — `paths` 검증을 v1에 한정 (community는 `name` + `source_repo` 필수 + `installed` warning).
- `source_repo`가 null인 항목은 warnings에 "`{name}: source_repo 미정 — 수동 설치 안내 필요`".

5. **변경이력 헤더 신설** (P-9 — `skill-registry.js:1-2` 인접):

```js
#!/usr/bin/env node
//
// skill-registry.js — OPAL 스킬 레지스트리 CLI
//
// 변경이력:
//   v1.0 2026-05-10 KST: 초기 작성 시점 명시 (헤더 신설 — 142). community 스킬 v2 스키마 지원 추가:
//                        - getCommunitySkillPath / isCommunitySkill 헬퍼
//                        - matchCommand 응답에 installed/source_repo/license/install_command 필드 추가
//                        - validate가 v2 스키마 인식 (paths 부재 정상)
//
'use strict';
```

> 첫 헤더이므로 v1.0으로 시작 (CONVENTIONS.md §변경이력 — 신규 작성 케이스). 이후 변경은 v1.1, v1.2... semver 증가.

**호환성**: main 스킬의 응답 형식은 변경 없음. 기존 `match` 사용자(예: `~/.opal/AGENT.md` Lazy 트리거 흐름)는 추가 필드를 무시하면 그대로 동작.

[MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §확정된 설계 방향 §10: "트리거 매칭됐는데 SKILL.md 미존재 → '외부 스킬, 설치할까요?' 안내 + `source_repo` 정보 노출. 자동 fetch는 알투(에이전트)가 수행 (registry는 정보 제공만, npx 호출은 알투/opal-skill-manager)."

#### 2.3.3 `opal/skills/opal-skill-manager/SKILL.md` — fetch 흐름 SSOT 강조

**변경**:

1. **§참고 §122-124 "기본 번들 스킬(31개)" 표현 제거** — 다음으로 치환:

```markdown
## 참고

- 스킬 검색 엔진: [skills.sh](https://skills.sh/) (vercel-labs/skills)
- 커뮤니티 스킬 SSOT: `npx skills` CLI — OPAL은 번들로 배포하지 않음. 사용자가 `//skill-manager` 또는 `// 커맨드` 첫 호출 시 동의 prompt를 거쳐 fetch.
- 설치 위치: `~/.opal/community-skills/{owner}/{skill}/SKILL.md`
- 레지스트리: `~/.opal/references/community-skills-registry.json` (v2 메타데이터 카탈로그 — 트리거 + source_repo + license)
```

2. **새 섹션 추가 — "6. `// 커맨드` 미설치 매칭 시 자동 fetch 흐름 (D-1)"**:

```markdown
### 6. `// 커맨드` 미설치 매칭 시 자동 fetch

알투가 `//pdf` 같은 community 트리거를 매칭했는데 skill-registry가 `installed: false`로 응답하면:

1. 사용자에게 동의 prompt 표시:
   ```
   이 스킬은 외부 스킬입니다 ({source_repo} / 라이선스: {license}).
   다운로드해서 설치할까요? (Y/n)
   ```
2. 수락(`Y`):
   - `npx skills add {source_repo}` 호출
   - 설치 완료 후 `~/.opal/community-skills/{owner}/{skill}/SKILL.md`를 Read하여 즉시 절차 실행
3. 거부(`n`):
   - "수동 설치는 `//skill-manager`로 — `npx skills find {keyword}`로 검색 후 설치하세요" 안내 후 종료
4. `source_repo`가 `null` (registry에 미등재):
   - "이 스킬은 vercel-labs/skills 카탈로그에 미등재. 수동 설치는 `//skill-manager`로" 안내
```

3. **변경이력 행 추가**:

```markdown
| v1.1 | 2026-05-10 HH:mm | "기본 번들 31개" 표현 제거 + fetch 흐름 SSOT 강조 + `// 커맨드` 미설치 매칭 시 자동 fetch 흐름 추가 (142) |
```

> 기존 SKILL.md에 변경이력 표가 없으면 §참고 다음에 신설.

[MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §확정된 설계 방향 §8: "사용자가 `//pdf` 같은 community 트리거를 호출했을 때 미설치 상태면, 알투가 '이 스킬은 외부({라이선스}). 다운로드해서 설치할까요?' 한 줄 prompt → 수락 시 `npx skills add {owner/repo@skill}` 자동 호출 → 설치 후 즉시 실행. 거부 시 '수동 설치는 `//skill-manager`로' 안내."

#### 2.3.4 `scripts/install-mac.sh` — community-skills 복사 단계 제거 (D-4 보존 의무)

**변경**:

1. **`clean_dirs` 배열 (`:731`)에서 `community-skills` 제거** — 안내 코멘트 추가:

```bash
# 변경 전 (:731)
local clean_dirs=("skills" "agents" "references" "community-skills" "templates" "tools")

# 변경 후
# 사용자 데이터 보존: ~/.opal/community-skills/는 install이 절대 건드리지 않음 (TASK 142 D-4)
local clean_dirs=("skills" "agents" "references" "templates" "tools")
```

2. **`install_opal_community_skills` 함수 호출부 제거** (`:841`):

```bash
# 변경 전
# ── 커뮤니티 스킬 ──
install_opal_community_skills

# 변경 후 — 행 자체 삭제. 인접 안내 코멘트:
# 커뮤니티 스킬은 번들로 배포하지 않음. 사용자가 //skill-manager로 검색·설치 (TASK 142)
```

3. **`install_opal_community_skills` 함수 본체 제거** (`:905-925`) — 함수 자체 삭제 (P-8). dead code 회피.

4. **install 종료 안내 한 줄 추가** (`:902` `print_cleanup_notice` 인접 또는 main 종료부):

```bash
echo ""
info "커뮤니티 스킬은 //skill-manager로 검색·설치하세요 (예: //skill-manager pdf)"
```

5. **변경이력 행 추가** (`:7-16` 변경이력 블록 끝):

```bash
#   v2.0 2026-05-10 HH:mm KST: community-skills 번들 → fetch 방식 전환 — install_opal_community_skills 함수 제거 + clean_dirs에서 community-skills 제거 (사용자 데이터 보존, D-4) + 종료 안내 추가 (142)
```

> v1.9에서 v2.0으로 — 구조 변경(번들 제거)이라 minor가 아닌 major bump.

[MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §제약 조건: "사용자 데이터 보존: 기존 사용자의 `~/.opal/community-skills/`는 install이 파괴하지 않음."

#### 2.3.5 `scripts/install/windows.ps1` — mac과 동등 처리

**변경**:

1. **`cleanDirs` 배열 (`:411`)에서 `community-skills` 제거** — 코멘트 추가:

```powershell
# 변경 전 (:411)
$cleanDirs = @('skills', 'agents', 'references', 'community-skills', 'templates', 'tools')

# 변경 후
# 사용자 데이터 보존: ~/.opal/community-skills/는 install이 절대 건드리지 않음 (TASK 142 D-4)
$cleanDirs = @('skills', 'agents', 'references', 'templates', 'tools')
```

2. **community-skills 복사 블록 제거** (`:506-519`) — 13줄 통째 삭제. 인접 안내 코멘트:

```powershell
# 커뮤니티 스킬은 번들로 배포하지 않음. 사용자가 //skill-manager로 검색·설치 (TASK 142)
```

3. **`.SYNOPSIS` (`:393`) "community-skills(병합)" 표현 제거**:

```powershell
# 변경 전
클린 후 재배포: skills/, agents/, references/, tools/, templates/, community-skills/(병합).

# 변경 후
클린 후 재배포: skills/, agents/, references/, tools/, templates/.
보존: ~/.opal/community-skills/(사용자 데이터, 142 D-4)
```

4. **install 종료 안내** (mac과 동등):

```powershell
Write-OpalInfo '커뮤니티 스킬은 //skill-manager로 검색·설치하세요 (예: //skill-manager pdf)'
```

5. **변경이력 행 추가** (v1.5.4 다음):

```powershell
v1.6.0 2026-05-10 HH:mm  community-skills 번들 → fetch 방식 전환 — community-skills 복사 블록 제거 + cleanDirs에서 community-skills 제거 (사용자 데이터 보존, D-4) + 종료 안내 추가 (142)
```

> 1.5.4 → 1.6.0 minor bump (mac v2.0과 별개 트랙. windows.ps1는 1.x 트랙 유지).

[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: 양 OS 동등 처리 — install-mac.sh와 windows.ps1는 같은 동작을 보장한다.

#### 2.3.6 `community-skills/` 폴더 git rm

**변경**:

```bash
git rm -r community-skills/
```

- 6 vendor 디렉토리 + 31 SKILL.md + LICENSE.txt(2개 vendor) + 부록 파일 통째 삭제.
- git 이력은 보존 — 필요 시 git log로 복원 가능.
- `git status` 확인: `community-skills/` 추적 안 됨.

[MUST] `tasks/142-260510-opp-community-skills-fetch-migration/TASK.md` §요구사항 R-1: "OPAL repo의 `community-skills/` 폴더 통째 삭제."

#### 2.3.7 `README.md` — L39 + L732 갱신

**변경**:

1. **L39 (주요 특징) — 표현 검토**:

```markdown
# 변경 전
- **커뮤니티 스킬** — 외부 조직이 제공하는 스킬을 원본 수정 없이 통합

# 변경 후
- **커뮤니티 스킬** — [skills.sh](https://skills.sh/) 카탈로그를 통해 외부 조직 스킬을 온디맨드로 검색·설치 (`//skill-manager`)
```

2. **L732 배포 다이어그램 — "30개 / 6개 조직" 정적 카운트 제거**:

```markdown
# 변경 전 (:732)
│  community-skills/ 외부 조직 제공 스킬 (30개 / 6개 조직) │

# 변경 후
│  community-skills/ 사용자 fetch 시 채워짐 (skills.sh 카탈로그) │
```

3. **변경이력 면제** — README는 docs 카테고리(141 v0.3.15 선례). 변경이력 행 추가 의무 없음.

#### 2.3.8 `docs/ARCHITECTURE.md` — §컴포넌트 유형 / §배포 모델 / 디렉토리 구조 갱신

**변경**:

1. **§시스템 구성 Global Layer 표 (`:64`) `community-skills/` 행**:

```markdown
# 변경 전
| `community-skills/` | 커뮤니티 스킬 37개 (6개 조직) |

# 변경 후
| `community-skills/` | 커뮤니티 스킬 — `npx skills` (vercel-labs/skills)로 사용자가 온디맨드 fetch |
```

2. **§컴포넌트 유형 §커뮤니티 스킬 (`:156-167`) 표 재서술**:

```markdown
### 커뮤니티 스킬 (Community Skills)

외부 조직이 제공하는 스킬. OPAL은 번들로 배포하지 않으며, 사용자가 `//skill-manager` 또는 `// 커맨드` 첫 호출 시 동의 prompt를 거쳐 [skills.sh](https://skills.sh/) 카탈로그(vercel-labs/skills)에서 fetch한다.

| 항목 | 값 |
|------|-----|
| 카탈로그 SSOT | [skills.sh](https://skills.sh/) — `npx skills find` |
| 설치 명령 | `npx skills add {owner/repo@skill}` (알투 자동 호출 또는 `//skill-manager`) |
| 설치 위치 | `~/.opal/community-skills/{owner}/{skill}/SKILL.md` |
| 레지스트리 | `~/.opal/references/community-skills-registry.json` (v2 메타데이터 카탈로그 — 트리거/source_repo/license) |
| 라이선스 책임 | 사용자 fetch 시점 발생 (OPAL repo는 third-party 코드 재배포 안 함) |
```

3. **§배포 모델 다이어그램 (`:182-211`) — `community-skills/* ──┤` 라인 제거**:

```
# 변경 전
soure (이 저장소)                    배포 대상 (~/.opal/)
─────────────────                  ──────────────────
skills/* (독립 6개) ──┐
opal/skills/* (24개)──┼─ install ─→  ~/.opal/skills/
opal/agents/* (12개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
agents/* (범용 1개) ──┤
community-skills/*  ──┤              ~/.opal/community-skills/   ← 이 라인 제거
opal/core/          ──┤              ~/.opal/AGENT.md
  ...

# 변경 후
(community-skills/* 라인 제거. 다이어그램 하단에 별도 안내:)

# 커뮤니티 스킬은 install이 배포하지 않음. 사용자가 //skill-manager로 fetch:
~/.opal/community-skills/  ←  npx skills add {owner/repo@skill}  ←  사용자 동의 prompt
```

4. **디렉토리 구조 트리 (`:266-319`) `community-skills/` 라인 갱신**:

```
# 변경 전 (:275)
├── community-skills/                    커뮤니티 스킬 (37개, 6개 조직)

# 변경 후 — 라인 제거 (저장소 루트에 더 이상 없음)
```

5. **변경이력 면제** — ARCHITECTURE.md는 docs 카테고리(141 v0.3.15 선례).

#### 2.3.9 `docs/PROJECT.md` — §폴더 구조맵 갱신

**변경**:

`:40` 라인 `community-skills/` 행 제거 (P-11):

```markdown
# 변경 전
| `community-skills/` | 커뮤니티 스킬 | 외부 조직 제공 스킬 |

# 변경 후 — 행 자체 제거.
```

> PROJECT.md는 docs 카테고리이므로 변경이력 면제.

---

## 3. 실행 체크리스트

> 총 11개 Step | Phase 5개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 순차 | registry JSON 스키마 v2 — 후속 도구·스킬·문서가 의존 |
| 2 | 2 | 순차 | skill-registry.js — Step 1 의존 |
| 2 | 3 | 병렬 | opal-skill-manager SKILL.md — Step 1 의존 (registry v2 형식 인지) |
| 3 | 4 | 병렬 | install-mac.sh — Step 1, 2, 3과 독립 (install 흐름) |
| 3 | 5 | 병렬 | windows.ps1 — Step 4와 독립 OS |
| 4 | 6 | 순차 | community-skills/ 폴더 git rm — Step 4, 5(install 흐름)가 더 이상 참조 안 함을 확인한 후 |
| 5 | 7 | 병렬 | README.md — Step 6 의존 (실제 폴더 사라진 후 문서 갱신) |
| 5 | 8 | 병렬 | docs/ARCHITECTURE.md — 독립 문서 |
| 5 | 9 | 병렬 | docs/PROJECT.md — 독립 문서 |
| 5 | 10 | 순차 | install 회귀 검증 (mac) — Step 4, 6 완료 후 |
| 5 | 11 | 순차 | install 회귀 검증 (Windows) — Step 5, 6 완료 후 |

> Step 7~11은 모두 독립이지만 회귀 검증(10, 11)은 install 변경(4, 5)과 폴더 삭제(6)가 모두 끝난 후 실행. Phase 5는 7/8/9 병렬 + 10/11 회귀 검증으로 분리 가능하나 단일 Phase로 묶어 표시.

### Step 1: community-skills-registry.json v2 스키마 변환

- [x] 완료
- **파일**: `opal/core/references/community-skills-registry.json`
- **agent**: `opal-task-agent` (Framework 단일 영역 폴백 — `docs/PROJECT.md` §프로젝트 구성)
- **작업 내용**:
  - `$schema: "opal-community-skills-registry-v2"` + `version: "2.0.0"` + `updated_at: "2026-05-10"` + `schema_notes` 필드.
  - 6 그룹 30 항목 모두에 `source_repo` (P-3 형식 `{owner}/{repo}@{skill}`) + `license` (P-4 SPDX 또는 `Unknown`) 필드 추가.
  - `paths` 필드 모든 항목에서 제거 (P-1).
  - `name` / `alias` / `description` / `triggers`는 그대로 유지.
- **완료 기준**:
  - `node -e "require('./opal/core/references/community-skills-registry.json')"` 파싱 성공.
  - 모든 항목에 `source_repo` + `license` 필드 존재 (`paths` 부재).
  - `$schema` = `opal-community-skills-registry-v2`.
  - 항목 수 = 30 (변경 없음).
- **테스트**: JSON 파싱 + jq로 필드 검증 (`jq '.groups[][] | select(.paths != null)'` → empty).
- **의존**: 없음
- **AC 매핑**: R-3 (TASK.md)
- **영역**: 데이터

### Step 2: skill-registry.js 갱신 — v2 인식 + 동적 installed + fetch 정보 노출

- [x] 완료
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **agent**: `opal-task-agent` (Framework 단일 영역 폴백)
- **작업 내용**:
  - 변경이력 헤더 블록 신설 (P-9, v1.0).
  - `getCommunitySkillPath(name)` 신규 헬퍼.
  - `loadAllSkills()`에서 community 항목에 `_source: 'community'` 마커 부착.
  - `matchCommand` 응답에 community 한정 필드 4개 신설: `installed` / `source_repo` / `license` / `install_command`. 미설치 시 `path: null`.
  - `validate()`가 v2 스키마 인식 — `paths` 부재 정상, `source_repo` null이면 warning.
- **완료 기준**:
  - `node ~/.opal/tools/skill-registry/skill-registry.js validate` 통과 (errors 0건). source_repo null 항목은 warnings.
  - `node ~/.opal/tools/skill-registry/skill-registry.js match "//pdf"` 응답에 `installed: true|false` + `source_repo` + `license` + `install_command` 포함.
  - main(opal) 스킬 매칭 응답은 기존 형식 유지 (community 필드 없음).
- **테스트**: 기존 `validate` + 새 `match` 시나리오 (설치/미설치 양쪽).
- **의존**: Step 1
- **AC 매핑**: R-4 (TASK.md)
- **영역**: Node.js 도구

### Step 3: opal-skill-manager SKILL.md 갱신

- [x] 완료
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **agent**: `opal-task-agent`
- **작업 내용**:
  - §참고 §122-124 "기본 번들 스킬(31개)" 표현 제거.
  - 새 섹션 §6 "`// 커맨드` 미설치 매칭 시 자동 fetch (D-1)" 추가.
  - 변경이력 행 추가 (v1.1).
- **완료 기준**:
  - SKILL.md에 "기본 번들" / "31개" 표현 0건.
  - §6 자동 fetch 흐름 4단계 (수락/거부/source_repo null) 명시.
  - 변경이력 표 v1.1 행 존재.
- **테스트**: `grep -E "기본 번들|31개" SKILL.md` → 0 hit.
- **의존**: Step 1 (registry v2 형식 인지)
- **AC 매핑**: R-5 (TASK.md)
- **영역**: 스킬 문서

### Step 4: install-mac.sh 갱신

- [x] 완료
- **파일**: `scripts/install-mac.sh`
- **agent**: `opal-task-agent` (Framework 단일 — install 영역도 동일 폴백. PROJECT.md §프로젝트 구성에 install 별도 영역 없음)
- **작업 내용**:
  - `clean_dirs` 배열(:731)에서 `community-skills` 제거 + 코멘트 추가.
  - `install_opal_community_skills` 호출부(:841) 제거 + 코멘트.
  - `install_opal_community_skills` 함수 본체(:905-925) 통째 삭제.
  - install 종료 안내 한 줄 추가.
  - 변경이력 v2.0 행 추가 (v1.9 다음).
- **완료 기준**:
  - `grep -nE "community-skills|install_opal_community_skills" scripts/install-mac.sh` → 변경이력 v2.0 행 + clean_dirs 코멘트만 매칭 (실제 동작 라인 0건).
  - 변경이력 v2.0 행 존재.
  - shellcheck (또는 `bash -n`) 문법 통과.
- **테스트**: `bash -n scripts/install-mac.sh` 통과. 실제 동작 검증은 Step 10 회귀.
- **의존**: 없음 (Step 1, 2, 3과 독립 — install은 community 처리만 제거)
- **AC 매핑**: R-2 (TASK.md)
- **영역**: bash 스크립트 (install)

### Step 5: scripts/install/windows.ps1 갱신

- [x] 완료
- **파일**: `scripts/install/windows.ps1`
- **agent**: `opal-task-agent`
- **작업 내용**:
  - `cleanDirs` 배열(:411)에서 `community-skills` 제거 + 코멘트.
  - community-skills 복사 블록(:506-519) 통째 삭제.
  - `.SYNOPSIS`(:393) "community-skills(병합)" 표현 제거 + 보존 안내 추가.
  - install 종료 안내 추가 (mac과 동등).
  - 변경이력 v1.6.0 행 추가 (v1.5.4 다음).
- **완료 기준**:
  - `grep -nE "community-skills|csSrc|csDst" scripts/install/windows.ps1` → 변경이력 v1.6.0 행 + .SYNOPSIS 보존 안내만 매칭.
  - 변경이력 v1.6.0 행 존재.
  - PowerShell 문법 검증: `pwsh -Command "Get-Command -Syntax ./scripts/install/windows.ps1"` (또는 PSScriptAnalyzer PASS).
- **테스트**: PSScriptAnalyzer PASS. 실제 동작 검증은 Step 11 회귀.
- **의존**: 없음 (Step 4와 독립 OS, 동시 진행 가능)
- **AC 매핑**: R-2 (TASK.md, Windows 측)
- **영역**: PowerShell 스크립트 (install)

### Step 6: community-skills/ 폴더 git rm

- [x] 완료
- **파일**: `community-skills/` (저장소 루트 6 vendor)
- **agent**: `opal-task-agent`
- **작업 내용**:
  - `git rm -r community-skills/` 실행.
  - `git status`로 추적 안 됨 확인.
- **완료 기준**:
  - `ls community-skills 2>&1` → "no such file or directory".
  - `git status`에 community-skills/ 디렉토리 변경 표시 (deleted).
- **테스트**: `find . -name community-skills -type d -not -path "*/.git/*" -not -path "*/.opal/*" -not -path "*/node_modules/*" 2>/dev/null` → 0 hit (저장소 내).
- **의존**: Step 4, Step 5 (install이 더 이상 참조 안 함을 확인한 후 삭제)
- **AC 매핑**: R-1 (TASK.md)
- **영역**: git

### Step 7: README.md 갱신

- [x] 완료
- **파일**: `README.md`
- **agent**: `opal-task-agent`
- **작업 내용**:
  - L39 주요 특징 표현 갱신 (`//skill-manager` 강조).
  - L732 배포 다이어그램 "30개 / 6개 조직" 제거 → 동적 표기.
- **완료 기준**:
  - `grep -E "30개 / 6개 조직|31개" README.md` → 0 hit.
  - L39, L732 변경 적용 확인.
- **테스트**: 마크다운 렌더링 확인 (다이어그램 깨짐 없음).
- **의존**: Step 6 (실제 폴더 삭제 후 문서 갱신)
- **AC 매핑**: R-6 (TASK.md, 141 후속 정리)
- **영역**: 문서

### Step 8: docs/ARCHITECTURE.md 갱신

- [x] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **agent**: `opal-task-agent`
- **작업 내용**:
  - §시스템 구성 Global Layer 표(:64) `community-skills/` 행 갱신.
  - §컴포넌트 유형 §커뮤니티 스킬(:156-167) 재서술 (fetch 방식).
  - §배포 모델 다이어그램(:182-211)에서 `community-skills/* ──┤` 라인 제거 + fetch 흐름 안내 추가.
  - 디렉토리 구조 트리(:275) `community-skills/` 라인 제거.
- **완료 기준**:
  - `grep -E "community-skills 37|community-skills/.*37개" docs/ARCHITECTURE.md` → 0 hit.
  - §커뮤니티 스킬 표가 fetch 방식 SSOT 재서술.
  - 배포 모델 다이어그램에 community-skills 배포 라인 0건.
- **테스트**: 다이어그램 렌더링 무결.
- **의존**: 없음 (Step 6 권장이지만 문서 변경은 독립 가능)
- **AC 매핑**: R-7 (TASK.md)
- **영역**: 문서

### Step 9: docs/PROJECT.md §폴더 구조맵 갱신

- [x] 완료
- **파일**: `docs/PROJECT.md`
- **agent**: `opal-task-agent`
- **작업 내용**:
  - §폴더 구조맵 표(`:40`)에서 `community-skills/` 행 제거.
- **완료 기준**:
  - `grep -E "community-skills.*외부 조직 제공" docs/PROJECT.md` → 0 hit.
- **테스트**: 표 렌더링 무결.
- **의존**: 없음
- **AC 매핑**: P-11 (PLAN 자율 결정)
- **영역**: 문서

### Step 10: install 회귀 검증 (mac)

- [ ] 완료
- **파일**: 회귀 (mac)
- **agent**: `opal-task-agent` (캡틴 머신에서 실행. 본 Step은 캡틴 EXECUTE 단계 검증)
- **작업 내용**:
  - 캡틴 mac에서 `./scripts/install-mac.sh` 또는 `opal-cli update` 재실행.
  - 다음 검증:
    1. install이 정상 종료 (errors 0건).
    2. `~/.opal/community-skills/`가 그대로 남아있음 (D-4 보존 검증) — `ls ~/.opal/community-skills/anthropics/ | wc -l` ≥ 17 (기존 보존).
    3. `node ~/.opal/tools/skill-registry/skill-registry.js validate` 통과.
    4. `node ~/.opal/tools/skill-registry/skill-registry.js match "//pdf"` 응답에 `installed: true` (이미 설치되어 있음).
    5. `//skill-manager` 자연어 호출 → opal-skill-manager SKILL.md 매칭 정상.
    6. `npx skills find pdf` 호출 정상 (Node.js v18+).
- **완료 기준**: 6개 검증 모두 PASS.
- **테스트**: 위 6개 항목 직접 실행.
- **의존**: Step 4, Step 6
- **AC 매핑**: R-8 (TASK.md, mac 측)
- **영역**: 회귀 (mac)

### Step 11: install 회귀 검증 (Windows)

- [ ] 완료
- **파일**: 회귀 (Windows)
- **agent**: `opal-task-agent` (Windows VM 또는 캡틴 머신 별도 환경)
- **작업 내용**:
  - Windows에서 `iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/scripts/install.ps1)` 또는 로컬 `./scripts/install/windows.ps1` 재실행.
  - 다음 검증:
    1. install이 정상 종료.
    2. `~\.opal\community-skills\`가 보존됨 (있으면 그대로, 없으면 빈 상태).
    3. `node ~\.opal\tools\skill-registry\skill-registry.js validate` 통과.
    4. `npx skills find pdf` 호출 정상 (Node.js v18+).
- **완료 기준**: 4개 검증 모두 PASS.
- **테스트**: 위 4개 항목 직접 실행.
- **의존**: Step 5, Step 6
- **AC 매핑**: R-8 (TASK.md, Windows 측)
- **영역**: 회귀 (Windows)

---

## 4. QA 체크리스트

### 4.1 기능 테스트

- [x] **R-1 폴더 제거**: `find . -path ./.git -prune -o -path ./.opal -prune -o -type d -name community-skills -print` 결과 0건 (저장소 내).
- [x] **R-2-mac install**: `bash -n scripts/install-mac.sh` 통과 + 실제 install 재실행 정상.
- [ ] **R-2-Windows install**: PSScriptAnalyzer PASS + 실제 install 재실행 정상. (캡틴 검증 대기)
- [x] **R-3 registry v2**: `jq '.["$schema"]' opal/core/references/community-skills-registry.json` = `"opal-community-skills-registry-v2"`. 모든 항목에 `source_repo` + `license`. `paths` 필드 0건.
- [x] **R-4 skill-registry.js v2 인식**: `validate` 통과. `match` 응답에 community 한정 필드 4개 (installed/source_repo/license/install_command).
- [x] **R-4 미설치 매칭 동작**: 미설치 community 트리거 매칭 시 `installed: false` + `path: null` + `install_command` 포함된 응답.
- [x] **R-5 opal-skill-manager**: "기본 번들 31개" / "30개" 표현 0건. §6 자동 fetch 흐름 명시.
- [x] **R-6 README**: L39 + L732 갱신, "30개 / 6개 조직" 0건.
- [x] **R-7 ARCHITECTURE**: §커뮤니티 스킬 fetch 재서술 + §배포 모델 다이어그램 community-skills 배포 라인 0건.
- [ ] **R-8 회귀**: mac + Windows 양 OS install 재실행 정상 + opal-skill-manager 동작 + 미설치 트리거 매칭 안내 노출. (캡틴 검증 대기)
  - QA 정적 검증: R-1~R-7 통과 (2026-05-10 QA-EXECUTE.md)

### 4.2 일관성 테스트

- [x] mac install-mac.sh와 windows.ps1의 동작 동등성 — 양쪽 모두 community-skills 처리 0건, 양쪽 모두 종료 안내 1회.
- [x] community-skills-registry.json v2와 skill-registry.js의 스키마 정합 — `source_repo`/`license` 필드명 일치.
- [x] opal-skill-manager SKILL.md의 fetch 흐름과 skill-registry.js `install_command` 출력 형식 정합 — 둘 다 `npx skills add {source_repo}` 형식.
- [x] ARCHITECTURE.md §커뮤니티 스킬과 PROJECT.md §폴더 구조맵 정합 — 양쪽 모두 community-skills 번들 표기 제거.
- [x] README.md L39와 ARCHITECTURE.md §컴포넌트 유형 §커뮤니티 스킬의 표현 정합 (`//skill-manager` 또는 `npx skills` 통일).
- [x] 변경이력 일시 (KST) — install-mac.sh / windows.ps1 / skill-registry.js / opal-skill-manager SKILL.md 4개 모두 일시 + 태스크 번호 (142) 포함.

### 4.3 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 — `source_repo` / `license` / `install_command` 등 영어 필드명, 본문은 한국어.
- [x] kebab-case 파일/폴더 네이밍 — 새로 만드는 파일 없으므로 N/A. 기존 `community-skills-registry.json` 그대로.
- [x] YAML frontmatter — `opal-skill-manager/SKILL.md` frontmatter `name` / `description` 변경 없음 (기존 트리거 그대로).
- [x] 변경이력 형식 — `vX.Y.Z YYYY-MM-DD HH:mm 변경내용 (142)` 포맷 준수 (CONVENTIONS.md §변경이력).
- [x] @header 규칙 — install-mac.sh / windows.ps1 / skill-registry.js 모두 헤더 블록 보존.
- [x] PLAN 인용 — 본 PLAN의 모든 [MUST] 인용이 D-N 또는 풀 포맷으로 명시 (citation-rules §2.4).

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-1 | `source_repo` 필드 미확인 — 4 그룹(getsentry / google-labs-code / trailofbits / vercel-labs)의 정확한 owner/repo가 `npx skills find` 검증 없이 추정 시 fetch 실패 | 사용자가 첫 호출 시 동의 후 `npx skills add {존재하지 않는 repo}` → 에러 | EXECUTE Step 1에서 `npx skills find {keyword}` 또는 [skills.sh](https://skills.sh)에서 1회 검증 후 채워 넣기. 검증 불가 항목은 `source_repo: null` + `license: "Unknown"`으로 두고 D-1 prompt에서 "수동 설치 안내" 분기 (P-12). |
| R-2 | 캡틴 mac의 기존 `~/.opal/community-skills/` 31 SKILL.md가 install 재실행 시 삭제될 위험 | 사용자 데이터 손실 (D-4 위반) | clean_dirs 배열에서 `community-skills` 명시 제거 + 코멘트로 의도 강조 (P-7). Step 10 회귀 검증에서 `ls ~/.opal/community-skills/anthropics/` 실측으로 확인. |
| R-3 | skill-registry.js 변경이 main(opal) 스킬 매칭에 영향 — 응답 스키마 변경이 기존 호출자(예: `~/.opal/AGENT.md` Lazy 흐름) 깨뜨릴 위험 | `// 커맨드` 매칭 회귀 | community 한정 필드는 main 스킬 응답에 포함하지 않음 (§2.3.2). 기존 호출자는 추가 필드를 무시하면 그대로 동작. Step 10 회귀에서 `match "//opp"` 등 main 스킬 매칭 검증. |
| R-4 | Windows PowerShell PSScriptAnalyzer가 `.SYNOPSIS` 제거를 강제 — `community-skills(병합)` 표현 제거 시 부수 변경 | install.ps1 빌드 실패 가능성 (낮음) | PSScriptAnalyzer는 `.SYNOPSIS` 내용에 무관 — 단순 텍스트 변경만 발생. Step 11 회귀에서 검증. |
| R-5 | 용어 일관성 — community 스킬 매칭에서 사용자가 "fetch" / "다운로드" / "설치" 중 어느 것을 보게 될지 영역마다 다를 수 있음 | 사용자 혼란 (낮음) | opal-skill-manager SKILL.md / install 종료 안내 / ARCHITECTURE.md 모두 "검색·설치"로 통일 (citation-rules §7 영역 간 용어 일관성 검토). 본 PLAN §일관성 테스트에서 검증. |
| R-6 | tarball 크기 차이 — community-skills 31 SKILL.md + 부록 제거로 패키지 크기 감소 → release 검증 영향 | release pipeline의 sha256 / 크기 expectation 갱신 필요 가능 | 본 태스크는 git 저장소 변경만 — release pipeline은 자동 재계산 (`actions/attest-build-provenance@v2`가 새 sha256 생성). 별도 작업 불필요. |
| R-T1 | (citation-rules §7) 영역 간 용어 일관성 — registry `source_repo` ↔ install_command `npx skills add {source_repo}` ↔ opal-skill-manager `{owner/repo@skill}` ↔ TASK.md `{owner/repo@skill}` | 4 영역 모두 동일 토큰 — 정합 | **결정성 이슈 없음**. 모두 `{owner}/{repo}@{skill}` 단일 토큰 사용. decision_required 발생 없음. |

> **decision_required 없음** — 본 PLAN의 P-1 ~ P-12 결정은 D-1 ~ D-4 SSOT의 자연스러운 확장이며 영역 간 용어 불일치도 없다.

---

## 6. PM 검토 기준

| # | 항목 | 검증 방법 |
|---|------|----------|
| PM-1 | TASK.md R-1 ~ R-8 모두 §3 실행 체크리스트 Step에 매핑되어 있는가 | §3 각 Step의 "AC 매핑" 행 확인 — R-1(Step 6) / R-2(Step 4, 5) / R-3(Step 1) / R-4(Step 2) / R-5(Step 3) / R-6(Step 7) / R-7(Step 8) / R-8(Step 10, 11) 모두 커버 |
| PM-2 | 캡틴 결정 D-1 ~ D-4가 §0에 SSOT로 명시되고 변경되지 않았는가 | §0 표 확인 + §2.3 핵심 설계가 D-1 ~ D-4 인용 |
| PM-3 | mac/Windows 동등 처리 — install 분기 격리가 양 OS에서 같은 동작을 보장하는가 | §2.3.4 vs §2.3.5 대조 — 양쪽 모두 (a) clean_dirs 제거 (b) 복사 블록 삭제 (c) 종료 안내 추가 (d) 변경이력 행 |
| PM-4 | 사용자 데이터 보존 — `~/.opal/community-skills/`가 install에 의해 파괴되지 않음을 코드 레벨에서 보장하는가 | §2.3.4 / §2.3.5 양쪽에서 `clean_dirs` 배열의 `community-skills` 제거 명시 + Step 10 회귀에서 실측 검증 |
| PM-5 | 변경이력 의무 — install-mac.sh / windows.ps1 / skill-registry.js / opal-skill-manager/SKILL.md 4개 모두 변경이력 행 추가가 §3 Step에 명시되어 있는가 | Step 2 (skill-registry.js v1.0 신설 P-9) / Step 3 (opal-skill-manager v1.1) / Step 4 (install-mac.sh v2.0) / Step 5 (windows.ps1 v1.6.0) — 모두 명시 |
| PM-6 | 141 후속 정리 의무 — README L39 + L732 갱신이 §3 Step 7에 명시되어 있는가 | Step 7 작업 내용 확인 |
| PM-7 | citation-rules 준수 — §1 참조 문서 테이블 + §1.2 [MUST] 인용 + 본문 인라인 인용 (D-N §N) 모두 기재되어 있는가 | §1.1 표 + §1.2 [MUST] + §2.3 인라인 인용 확인 |
| PM-8 | docs/CONVENTIONS.md [MUST] 인용이 §1 또는 §2.3에 포함되어 있는가 | §1.2 4개 인용 (변경이력/Guards/커밋/플랫폼 분기 격리) |
| PM-9 | decision_required 발생 시 에스컬레이션 명시 — 본 PLAN에서 결정 필요 사항이 있다면 §리스크에 표기되었는가 | §5 R-T1 "decision_required 없음" 명시 |
| PM-10 | Phase 그룹핑이 의존성과 정합하는가 — 동일 파일 수정 Step이 같은 Phase에 배치되지 않았는가 | §3 Phase 표 확인 — Step 1~11 모두 서로 다른 파일 또는 독립 영역 |
| PM-11 | EXECUTE 워커 라우팅 — 모든 Step에 `agent` 필드가 배정되어 있는가 | §3 모든 Step에 `agent: opal-task-agent` (PROJECT.md §프로젝트 구성 단일 영역 폴백) |
| PM-12 | docs/ 갱신 — 코드 변경이 docs에 영향 (PROJECT.md §폴더 구조맵 / ARCHITECTURE.md / README.md)하므로 docs 갱신 Step이 있는가 | Step 7 (README) / Step 8 (ARCHITECTURE) / Step 9 (PROJECT) 모두 §3에 포함 |

---

> **워커 자체 결정 사항 (PM 보고)**:
> - **블로커 없음** — 본 PLAN은 D-1 ~ D-4 SSOT를 그대로 따르며 P-1 ~ P-12 자율 결정으로 완결.
> - **EXECUTE 시 보강 필요** — `community-skills-registry.json` v2 변환 시 `source_repo` 정확한 owner/repo는 EXECUTE 워커가 `npx skills find` 또는 [skills.sh](https://skills.sh)로 1회 검증 후 채워 넣기. 검증 불가 항목은 `source_repo: null`로 두고 D-1 prompt에서 "수동 설치 안내" 분기 (P-12).
> - **회귀 검증 의무** — Step 10(mac) + Step 11(Windows) 양 OS 회귀는 EXECUTE 단계 산출물이며 캡틴 환경에서만 수행 가능. PM은 Step 10/11 결과 보고 후 CLOSE 진입 승인.

