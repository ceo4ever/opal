# PLAN: 커뮤니티 스킬 관리 워크플로우 통일 (검색·설치·제거·업데이트 + `//` 미설치 분기)

> 작성일: 2026-07-17 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature | 실행 모드: 복잡

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

커뮤니티 스킬의 검색·설치·제거·업데이트 4절차를 **clone-copy(A안) 단일 방식**으로 통일하고, 설치 레이아웃 SSOT를 **vendor 중첩**으로 확정한다. flat 잔재 31개를 vendor 중첩으로 옮기는 마이그레이션을 `skill-registry.js migrate` 서브커맨드로 신설(도구 자기완결)하고, `getCommunitySkillPath`는 마이그레이션 전에도 정상 판정하도록 vendor→flat 이중 탐지로 재구현한다. `//xxx` 미설치 분기는 이미 선반영된 skill-commands.md v1.2 라우팅을 유지하고 skill-manager §6을 clone-copy 기준으로 재작성한다. 사용자 수동 설치 등록분은 install이 절대 건드리지 않는 `~/.opal/community-skills/user-registry.json`으로 격리하여 배포 덮어쓰기로부터 보존한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 레이아웃 마이그레이션 (migrate 서브커맨드 + 이중 경로 탐지) | TASK F-1 | P0 | 없음 |
| F-002 | basename alias 매칭 + 충돌 정책 | TASK F-2 | P0 | 없음 |
| F-003 | 미설치 분기 라우팅 정합 (skill-commands v1.2 유지 + §6 재작성) | TASK F-3 | P0 | F-004 |
| F-004 | 설치 방식 A안(clone-copy) 통일 + commit_sha + npx add 제거 | TASK F-4 | P0 | F-006 |
| F-005 | 관리 워크플로우 4절차 재작성 (검색·설치·제거·업데이트) | TASK F-5 | P0 | F-001, F-004, F-006 |
| F-006 | registry 갱신 경로 정의 (user-registry.json 격리 + 병합 로드) | TASK F-6 | P0 | 없음 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-002 (basename 매칭) ──────────────┐
F-006 (user-registry 격리·병합) ──┬─→ F-004 (clone-copy 통일) ─→ F-003 (§6 라우팅 재작성) ─┐
F-001 (migrate + 이중 탐지) ──────┴──────────────────────────────────────────────────────┴─→ F-005 (4절차 재작성)
```

- F-006 (loadAllSkills 병합)·F-002 (matchByAlias)·F-001 (getCommunitySkillPath/migrate)는 모두 `skill-registry.js` 독립 함수 → 병렬 가능하나 동일 파일이므로 단일 에이전트 순차 편집.
- F-004는 F-006의 user-registry 기록 규칙과 match 출력(install_method)을 전제 → F-006 이후.
- F-003·F-005는 문서 재작성으로 JS 동작(F-001/F-002/F-004/F-006)이 확정된 뒤 작성.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `getCommunitySkillPath` 이중 탐지 재구현 (F-001) | 함수 반환 계약 변경 — 기존 호출자(`matchCommand:208`, `validate:364`)가 "존재 경로 or null"을 기대하는데 canonical 경로만 반환하면 미설치 오판 회귀 | P0 | L1(단위: vendor/flat/미설치 3분기) | S-후보1 |
| H-2 | `matchByAlias` basename 확장 (F-002) | 반환 타입 다형화 — 단일 skill → 충돌 시 ambiguous 센티넬. `matchCommand:199`가 단일 객체만 가정하면 TypeError | P0 | L1(단위: 단일/basename/충돌/무매칭 4분기) | S-후보2 |
| H-3 | `loadAllSkills` user-registry 병합 (F-006) | 로드 계약 변경 — user-registry.json 부재/파손 시 throw하면 전체 CLI 다운(match/list/validate 전멸) | P0 | L1(단위: 부재·정상·파손 JSON) + L2(실 파일) | S-후보3 |
| H-4 | migrate 이동 로직 (F-001) | 파일시스템 무결성 — 미등재/basename 충돌 flat 디렉토리를 삭제·오이동하면 사용자 데이터 소실 (142 D-4 위반) | P0 | L2(실 fs fixture: 등재 flat·미등재 flat·이미 중첩·충돌) | S-후보4 |
| H-5 | user-registry.json 기록 경로 (F-004/F-006) | 배포 경계 — install이 `references/`를 rm+cp로 덮어쓰므로 references에 사용자 항목을 쓰면 재설치 시 소실 | P0 | L2(install 재실행 후 user-registry 잔존 실측) | S-후보5 |
| H-6 | clone-copy source_repo 파싱 (F-004) | 계약 — `source_repo`가 `owner/repo@subdir` 형식인데 파싱 오류 시 잘못된 repo clone 또는 빈 subdir 복사 | P1 | L1(파싱 단위: `anthropics/skills@pdf`, `obra/superpowers@brainstorming`) | S-후보6 |
| H-7 | commit_sha 업데이트 감지 (F-005/R-6) | 운영 — `git ls-remote` 실패(네트워크/repo 삭제) 또는 commit_sha=null(레거시) 시 업데이트 판정 오류 | P2 | L2(ls-remote mock/실 repo) | S-후보7 |
| H-8 | npx add 제거 (F-004) | 문서 정합 — 잔존 `npx skills add` 설치 지시가 §6 clone-copy와 모순 → 라우팅 따라가도 오동작(D4 재발) | P1 | L1(grep 산출물 검사: 설치 지시 0건) | S-후보8 |
| H-9 | skill-commands.md ↔ §6 라우팅 (F-003) | 계약 — skill-commands v1.2가 가리키는 §6이 clone-copy로 동작하지 않으면 `//` 미설치 흐름 단절 | P0 | L3(E2E: 미설치 `//pdf` → 자동 설치 → 실행) | S-후보9 |

---

## 2. 기능별 분석

### F-001: 레이아웃 마이그레이션 (migrate 서브커맨드 + 이중 경로 탐지)

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` | `getCommunitySkillPath` 이중 탐지 + `migrate` 서브커맨드 신설 | 수정 |
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | migrate 트리거(관리 진입 시 1회 실행) 명시 | 수정 |
| 도구/테스트 | `opal/tools/skill-registry/tests/test-migrate.js` | migrate + 경로 탐지 단위 테스트 신설 | 신규 |

#### 2.1.2 현재 구현
`getCommunitySkillPath(skillName)`는 `~/.opal/community-skills/{skillName}/SKILL.md`를 무조건 반환한다 (`skill-registry.js:75-77`). 인자가 `anthropics/pdf`면 `anthropics/pdf/SKILL.md`를 기대하나, 실제 flat 잔재는 `pdf/SKILL.md`에 있어 `fs.existsSync`가 항상 false (D1, ANALYSIS §4(2)). migrate 기능은 부재 — CLI 라우터는 `match|get|list|validate` 4종만 지원 (`skill-registry.js:461-495`).

#### 2.1.3 영향 범위
- 호출자: `matchCommand`의 community 분기 (`skill-registry.js:208-209`), `validate`의 설치 여부 확인 (`skill-registry.js:364-367`). 반환 계약 변경 시 양쪽 정합 필요 (H-1).
- flat 31개 전량이 registry basename과 매칭됨 → 미등재 flat 0개 (ANALYSIS §4(7)). 그러나 미등재 보존 로직은 142 D-4 준수를 위해 필수 구현.

---

### F-002: basename alias 매칭 + 충돌 정책

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` | `matchByAlias` basename 매칭 + 충돌 시 후보 목록 반환, `matchCommand` ambiguous 처리 | 수정 |
| 도구/테스트 | `opal/tools/skill-registry/tests/test-match.js` | matchByAlias 4분기 단위 테스트 신설 | 신규 |

#### 2.2.2 현재 구현
`matchByAlias(skills, alias)`는 정식명(`s.name`) 또는 `s.alias` 필드만 소문자 정확 비교하여 단일 skill 또는 null 반환 (`skill-registry.js:129-135`). `//pdf`는 alias 실패 후 triggers 정규식 폴백으로 우연히 매칭(`matchCommand:201-203`), `//pdf 문서 만들어줘`는 cleanInput 기반 triggers로 매칭되나 basename alias 경로는 부재 (D2, ANALYSIS §4(3)).

#### 2.2.3 영향 범위
- `matchCommand:199`가 `matchByAlias` 반환을 단일 skill로 가정 → 충돌 시 다형 반환을 처리하도록 수정 (H-2).
- 현행 registry 32개 basename 전수 유일(충돌 0) → 충돌 정책은 전방 안전장치. `obra/brainstorming` 등 vendor 접두 없는 `//brainstorming` 호출이 신규 지원됨.

---

### F-003: 미설치 분기 라우팅 정합 (skill-commands v1.2 유지 + §6 재작성)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 참조 | `opal/core/references/harness/skill-commands.md` | v1.2 라우팅 유지, 문구 미세 정합(§6이 clone-copy로 동작함 반영) | 수정(미세) |
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §6 자동 설치·실행을 clone-copy 기준으로 재작성 | 수정 |

#### 2.3.2 현재 구현
skill-commands.md는 이미 v1.2로 선반영됨 — `installed:false` 시 `skill-manager §6` 라우팅 + "라이선스 확인 스킬 자동 설치·실행, Unknown만 게이트" 정책 명시 (`skill-commands.md:24,35,47`). **ANALYSIS §4(4)의 "분기 부재" 서술은 이 편집 이전 스냅샷이므로 무효** (오케스트레이터 지시). skill-manager §6도 자동 설치 정책·Unknown 게이트·commit_sha 노출을 이미 보유하나(`SKILL.md:127-157`), 설치 명령이 `npx skills add {source_repo}`(`SKILL.md:141,152`)라 D4로 오동작.

#### 2.3.3 영향 범위
- skill-commands.md 라우팅은 유지(SSOT는 §6 절차) → 문구만 정합. `.opal/AGENT.md` 배포본의 `//` 흐름이 §6을 따라가므로 §6 clone-copy 전환이 E2E 성패를 결정 (H-9).

---

### F-004: 설치 방식 A안(clone-copy) 통일 + commit_sha + npx add 제거

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` | match 출력 `install_command`(npx) → clone-copy 지시로 교체 + `install_method` 필드 | 수정 |
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | §2·§6 설치 절차 clone-copy 단일화, `npx skills add` 제거 | 수정 |
| 참조 | `opal/core/references/community-skills-registry.json` | `schema_notes`에 clone-copy·commit_sha 기록 규칙 반영 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | `npx skills add` 설치 명령 언급 제거·clone-copy로 갱신 | 수정 |

#### 2.4.2 현재 구현
match 출력의 `install_command`는 `sourceRepo ? \`npx skills add ${sourceRepo}\` : null` (`skill-registry.js:212`). skill-manager §2는 이미 git clone 절차를 서술하나(`SKILL.md:58-72`) §6·검색 테이블·업데이트는 여전히 npx 기반(`SKILL.md:36,44,98,141,152`). ARCHITECTURE.md도 npx add를 설치 명령으로 명시(`ARCHITECTURE.md:178,226`, 카탈로그 find는 `:177`).

#### 2.4.3 영향 범위
- `install_command` 소비처: skill-commands 흐름·skill-manager §6가 이 필드로 설치 안내 구성. 값 변경 시 문서 정합 필요 (H-8).
- `source_repo` 형식 `owner/repo@subdir` (예: `anthropics/skills@pdf`, `obra/superpowers@brainstorming` — `registry.json:12,51`)에서 clone repo·subdir·설치 vendor 경로 파생 (H-6).

---

### F-005: 관리 워크플로우 4절차 재작성

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | 검색·설치·제거·업데이트 4절차 clone-copy 기준 재작성 + migrate 트리거 | 수정 |

#### 2.5.2 현재 구현
§1 검색(`SKILL.md:16-56`)·§2 설치(`:58-72`)·§4 삭제(`:86-93`)·§5 업데이트(`:96-101`)가 존재하나 npx/디렉토리 규칙이 혼재. §5 업데이트는 `npx skills check`만 있고 commit_sha 비교 미정의 (R-6).

#### 2.5.3 영향 범위
- 4절차 상호 모순 문구 0건이 AC. 검색=find+대조, 설치=clone-copy(F-004), 제거=vendor 디렉토리 삭제+user-registry 항목 제거, 업데이트=commit_sha 비교(F-006 user-registry 기록 전제).

---

### F-006: registry 갱신 경로 정의 (user-registry.json 격리 + 병합 로드)

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/skill-registry/skill-registry.js` | `loadAllSkills`가 user-registry.json 병합 로드 | 수정 |
| 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | 사용자 설치 등록분은 user-registry.json에 기록·보존 규칙 명문화 | 수정 |
| 참조 | `opal/core/references/community-skills-registry.json` | `schema_notes`에 프레임워크 카탈로그 vs 사용자 등록분 경계 명시 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` / `docs/CONVENTIONS.md` | 커뮤니티 스킬 registry 이원(카탈로그/사용자) 경계 반영 | 수정 |

#### 2.6.2 현재 구현
`loadAllSkills`는 `~/.opal/references/`에서 `opal-skills-registry.json` + `community-skills-registry.json`만 로드 (`skill-registry.js:84-93`). skill-manager는 설치/삭제 시 `~/.opal/references/community-skills-registry.json`을 직접 갱신(`SKILL.md:72,92`). 그러나 install은 `references/`를 `clean_dirs`에 포함하여 rm 후(`install-mac.sh:1034`, `windows.ps1:433`) `cp -Rf`로 덮어씀(`install-mac.sh:1362`, `windows.ps1:555`) → **사용자 등록분 소실 확정**(F-6/R-3 실측). `community-skills/`는 install이 절대 건드리지 않음(`install-mac.sh:1033`, `windows.ps1:432` — 142 D-4).

#### 2.6.3 영향 범위
- 병합 로드 시 user-registry.json 부재/파손이 CLI 전체를 다운시키면 안 됨 (H-3, 방어적 로드).
- user-registry.json을 `community-skills/` 하위에 두면 install 불가침 영역이라 코드 변경 없이 보존 → install 스크립트 변경 0건(R-3 최소 변경안).

---

## 3. 기능별 설계

> 참조 문서 테이블은 §8.3. 인라인 인용은 `(→ D-N)` 단축 또는 `경로:줄번호`.

### [MUST] 상위 제약 (전 기능 공통 준수)

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." (동일 취지: `docs/CONVENTIONS.md` §배포 경계 `:203`)
- [MUST] `docs/CONVENTIONS.md` §배포 경계 `:203`: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리 `:206-209`: "플랫폼별 차이는 어댑터 계층에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 `:197-198`: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."
- [MUST] `docs/CONVENTIONS.md` §도구 우선 원칙 `:189-192`: 파일 처리·데이터 변환은 OPAL 도구를 우선한다 — 마이그레이션 로직은 `skill-registry` 도구에 귀속(자기완결).
- [MUST] `harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지."
- [MUST] registry `commit_sha`는 옵션 필드로 v2 호환 유지 — 미작성 시 null 간주 (`community-skills-registry.json:5` schema_notes). **스키마 버전 문자열(`opal-community-skills-registry-v2.1`)을 변경하지 않는다** — `validate:340-341`이 v2/v2.1만 인식하므로 하위호환 유지.
- [MUST] 142 D-4 보존 원칙: 마이그레이션은 registry 미등재 사용자 데이터를 삭제·이동하지 않는다 (`install-mac.sh:1033`).

### F-001: 레이아웃 마이그레이션

#### 3.1.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/skill-registry/tests/test-migrate.js` | 도구/테스트 | migrate + 경로 탐지 단위 테스트 | H-1·H-4 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `getCommunitySkillPath` 이중 탐지 + `resolveCommunitySkillPath` 헬퍼 + `migrate` 서브커맨드 + CLI 라우터 등록 | `:75-77`, `:461-495` |
| 2 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | 관리 절차 진입 시 `migrate` 1회 실행 명시 | (→ F-005) |

#### 3.1.2 API·데이터 모델·설계

**(a) 경로 탐지 재구현** — 마이그레이션 전에도 정상 판정 (전환기 안전, H-1):

```js
// canonical(vendor 중첩) 경로 — 설치 타깃 계산용 (기존 시그니처 유지: 하위호환)
function getCommunitySkillPath(skillName) {
  return path.join(os.homedir(), '.opal', 'community-skills', skillName, 'SKILL.md');
}
// 실제 존재 경로 해석 — vendor 우선, flat 폴백, 없으면 null
function resolveCommunitySkillPath(skillName) {
  const home = os.homedir();
  const nested = path.join(home, '.opal', 'community-skills', skillName, 'SKILL.md');       // anthropics/pdf/SKILL.md
  if (fs.existsSync(nested)) return nested;
  const base = skillName.includes('/') ? skillName.split('/').pop() : skillName;
  const flat = path.join(home, '.opal', 'community-skills', base, 'SKILL.md');              // pdf/SKILL.md (레거시)
  if (fs.existsSync(flat)) return flat;
  return null;
}
```

- `matchCommand`(`:208-209`)와 `validate`(`:364`)의 `installed` 계산을 `resolveCommunitySkillPath(skill.name) !== null`로 교체. `path` 반환값도 `resolveCommunitySkillPath` 결과 사용 → flat 잔재 사용자도 `installed:true` (D1 해소, H-1).
- [MUST] `getCommunitySkillPath` 시그니처·반환은 유지(설치 타깃 = canonical vendor 경로). 탐지 전용 로직만 `resolveCommunitySkillPath`로 분리 (기존 호출 계약 파괴 금지).

**(b) `migrate` 서브커맨드** — flat → vendor 중첩 1회 이동, 도구 자기완결 (→ D-6 §도구 우선):

함수 시그니처:
```js
// migrate(dryRun: boolean) -> { moved: [{from,to}], preserved: [{dir,reason}], skipped: [...], errors: [...] }
function migrateCommand(dryRun)
```
알고리즘:
1. `~/.opal/community-skills/` 1-depth 엔트리 순회.
2. 엔트리에 `SKILL.md`가 **직접** 존재 → flat 스킬 디렉토리로 판정. `SKILL.md` 없고 하위 디렉토리만 → vendor 디렉토리(이미 중첩)로 판정 → skip.
3. flat 디렉토리명(basename)을 registry 전체 스킬명의 basename과 대조:
   - 정확히 1개 registry 스킬과 매칭 → `{vendor}/{basename}/`로 `fs.renameSync` 이동 (동일 대상 존재 시 skip+보고).
   - 복수 vendor와 충돌 → **이동 금지**, `preserved`에 `reason:"basename_collision"` 기록 (H-4).
   - 매칭 0 → **이동 금지**, `preserved`에 `reason:"unregistered"` 기록 ([MUST] 142 D-4).
4. `--dry-run`이면 실제 이동 없이 계획만 반환.
5. 결과 JSON 출력. 재실행 시 flat 디렉토리 0 → 멱등.

- CLI 라우터에 `case 'migrate'` 추가 (`:461-495` switch, `--dry-run` 플래그 파싱). usage 문자열 갱신 (`:451-455`).
- [MUST] `renameSync` 대상 경로는 `path.resolve` 후 `~/.opal/community-skills/` 하위인지 검증 (CWE-22 path traversal 방어, 기존 `resolveFirstPath:175-180` 패턴 계승).

#### 3.1.3 환경 변경
해당 없음 (Node.js 내장 fs/path/os만 사용, `skill-registry.js:30-32`).

#### 3.1.4 배치/마이그레이션
migrate는 사용자 PC 1회 실행 배치. 트리거 = skill-manager 관리 절차 진입 시(§검색·목록·설치 전) `node ~/.opal/tools/skill-registry/skill-registry.js migrate` 멱등 호출. install 훅 아님 — 142 D-4(install은 community-skills 불가침) 유지 (R-1 결정, §하단 결정 요약).

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-101 | F-1 AC | 기능(L1) | `resolveCommunitySkillPath`: vendor 존재→vendor, flat만 존재→flat, 둘 다 없음→null |
| TS-102 | F-1 AC | 기능(L2 실 fs) | migrate: 등재 flat→vendor 이동, 이미 중첩→skip, 재실행 멱등 |
| TS-103 | F-1 AC(142 D-4) | 기능(L2 실 fs) | migrate: 미등재 flat·basename 충돌 flat→preserved(무이동), errors 0 |
| TS-104 | F-1 AC | 회귀(L2) | migrate 후 `list --group=community` 전수 `installed:true` |

---

### F-002: basename alias 매칭 + 충돌 정책

#### 3.2.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/skill-registry/tests/test-match.js` | 도구/테스트 | matchByAlias 4분기 + ambiguous 단위 테스트 | H-2 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `matchByAlias` basename 매칭 추가 + 충돌 시 후보 목록, `matchCommand` ambiguous 처리 | `:129-135`, `:193-243` |

#### 3.2.2 API·데이터 모델·설계

**(a) `matchByAlias` 확장** (R-2 결정 = 후보 목록 반환):
```js
function matchByAlias(skills, alias) {
  const lower = alias.toLowerCase();
  // 1순위: 정식명(vendor/skill) 또는 alias 필드 정확 매칭 (기존 계약 — 단일 반환)
  const exact = skills.find(s =>
    s.name.toLowerCase() === lower || (s.alias && s.alias.toLowerCase() === lower));
  if (exact) return exact;
  // 2순위: basename 매칭 (vendor 무관)
  const byBase = skills.filter(s => {
    const base = s.name.includes('/') ? s.name.split('/').pop() : s.name;
    return base.toLowerCase() === lower;
  });
  if (byBase.length === 1) return byBase[0];
  if (byBase.length > 1) return { __ambiguous: true, candidates: byBase };  // 충돌
  return null;
}
```

**(b) `matchCommand` ambiguous 처리** (`:197-243`, H-2):
```js
skill = matchByAlias(skills, alias);
if (skill && skill.__ambiguous) {
  return {
    found: true, ambiguous: true, alias,
    candidates: skill.candidates.map(s => ({
      name: s.name, source_repo: s.source_repo || null,
      license: s.license || 'Unknown',
      installed: isCommunitySkill(s) ? resolveCommunitySkillPath(s.name) !== null : true
    })),
    cleanInput
  };
}
```
- 정식명 정확 매칭·단일 basename 매칭은 기존 단일 응답 형식 유지 (하위호환).
- `cleanInput`은 `//pdf 문서 만들어줘` → `문서 만들어줘` 정상 추출 (`extractAlias:119-127` 재사용, D2 AC 충족).
- 현행 32개 basename 유일 → ambiguous 미발생. 전방 안전장치 + `//brainstorming`(vendor 생략) 신규 지원.

#### 3.2.3 환경 변경 / 3.2.4 배치
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-201 | F-2 AC | 기능(L1) | `match "//pdf 문서 만들어줘"` → `anthropics/pdf` + `cleanInput:"문서 만들어줘"` |
| TS-202 | F-2 AC | 기능(L1) | `match "//brainstorming"` → `obra/brainstorming` (basename 매칭) |
| TS-203 | F-2 AC | 기능(L1) | 정식명 `//anthropics/pdf` → 정확 매칭 단일 반환 (하위호환) |
| TS-204 | F-2 AC(충돌) | 기능(L1 합성 fixture) | 동일 basename 2벤더 → `ambiguous:true` + candidates 2건 |

---

### F-003: 미설치 분기 라우팅 정합

#### 3.3.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §6 자동 설치·실행을 clone-copy 절차로 재작성 (npx add → git clone) | `:127-157` |
| 2 | `opal/core/references/harness/skill-commands.md` | 참조 | v1.2 라우팅 유지, 문구 미세 정합(설치 방식=clone-copy 반영) | `:24,35` |

#### 3.3.2 설계
- skill-commands.md `:24,35`의 "skill-manager §6 자동 설치·실행" 라우팅·정책 문구는 **유지**(SSOT는 §6). "라이선스 확인 스킬 자동 설치·실행, Unknown만 게이트" 정책 원문 보존 (F-3 AC②).
- §6 재작성 (F-3 AC①③, D4 해소):
  - 분기1 (`license ≠ Unknown` + `source_repo` 있음): 비차단 통지 1줄 → **clone-copy 절차 실행**(§2 참조) → 설치 완료 후 `~/.opal/community-skills/{vendor}/{skill}/SKILL.md` Read·즉시 실행. `npx skills add` 문구 제거.
  - 분기2 (`license == Unknown`): 확인 게이트(기본 N) 유지 → 수락 시 clone-copy → SKILL.md Read·실행.
  - 분기3 (`source_repo == null`): 수동 안내 유지.
  - ambiguous 응답(F-002) 수신 시: 후보 목록 표시 → 정식명 재호출 유도 (신규 분기 추가).
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리 `:206-209` 준수 — §6은 git/fs 행위를 플랫폼 독립적으로 기술.

#### 3.3.3~3.3.4 환경/배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-301 | F-3 AC① | 통합(L3 E2E) | 미설치 `//pdf 문서` → §6 clone-copy 설치 → SKILL.md Read → 실행 |
| TS-302 | F-3 AC② | 산출물 검사 | skill-commands.md 정책 원문 ↔ §6 분기 모순 0건 |
| TS-303 | F-3 AC③ | 산출물 검사 | §6에 "설치 후 SKILL.md 즉시 Read·실행" 단계 명시 |

---

### F-004: 설치 방식 A안(clone-copy) 통일 + commit_sha + npx add 제거

#### 3.4.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | match 출력 `install_command`(npx) → clone-copy 지시 + `install_method:"clone-copy"` | `:210-212,226` |
| 2 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | §2·§6 clone-copy 단일화, commit_sha 기록, npx add 전량 제거 | `:36,44,98,123,141,152` |
| 3 | `opal/core/references/community-skills-registry.json` | 참조 | schema_notes에 clone-copy·commit_sha 기록 규칙 반영 | `:5` |
| 4 | `docs/ARCHITECTURE.md` | 문서 | 설치 명령 npx add → clone-copy 갱신 | `:178,226` (find는 `:177` 유지) |

#### 3.4.2 설계

**(a) match 출력 필드** (`:210-212`, H-8):
```js
const sourceRepo = skill.source_repo || null;
const license = skill.license || 'Unknown';
// npx add 제거 → clone-copy 절차 지시. source_repo가 clone 소스, 절차는 skill-manager §2/§6
const installMethod = sourceRepo ? 'clone-copy' : null;
const installCommand = sourceRepo ? `opal-skill-manager §설치 (clone-copy: ${sourceRepo})` : null;
```
반환 객체에 `install_method` 추가, `install_command`는 clone-copy 지시 문자열로 교체(npx 문구 제거). 기존 필드 존재는 유지 → 소비처 파괴 없음.

**(b) clone-copy 절차** (source_repo `owner/repo@subdir` 파싱, H-6):
1. `source_repo` = `anthropics/skills@pdf` → owner=`anthropics`, repo=`skills`, subdir=`pdf`. `@` 미포함 시 subdir=repo.
2. 설치 vendor 경로 = registry `name`의 vendor 부분 + basename (예: `obra/brainstorming`은 clone `obra/superpowers@brainstorming`이나 설치 경로는 `obra/brainstorming/`).
3. `git clone --depth 1 https://github.com/{owner}/{repo}.git {tmp}`.
4. `{tmp}/{subdir}/` → `~/.opal/community-skills/{vendorFromName}/{basenameFromName}/` 복사.
5. `git -C {tmp} rev-parse HEAD` → commit_sha 확보.
6. tmp 정리 → user-registry.json에 항목 기록 (F-006, commit_sha 포함).

- [MUST] 설치 지시로서 `npx skills add`는 전 소스에서 0건 (F-4 AC). `npx skills find`/`check`는 검색·업데이트 확인 전용으로 잔존 허용 (C-3). 잔존 grep 대상: `SKILL.md:36,44,98,141,152`, `ARCHITECTURE.md:178,226`, `skill-registry.js:212`.
- brain 페이지(`.opal/brain/pages/concept/skill-opal-skill-manager.md`)의 npx 언급은 brain 자산(설명 맥락)이며 설치 지시 아님 → §4 AC "설명·변경이력 제외"에 해당, 본 태스크 범위 밖(선택적 정합).

#### 3.4.3 환경 변경
git CLI 의존 (clone). 신규 npm 패키지 0.

#### 3.4.4 배치/마이그레이션
해당 없음 (설치 시점 동작).

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-401 | F-4 AC | 기능(L1) | match 출력에 npx 문구 없음, `install_method:"clone-copy"` |
| TS-402 | F-4 AC | 기능(L1) | source_repo 파싱: `anthropics/skills@pdf`→(anthropics,skills,pdf), `obra/superpowers@brainstorming`→(obra,superpowers,brainstorming) |
| TS-403 | F-4 AC | 산출물 검사 | 소스 전체 `npx skills add` 설치 지시 0건 (grep, 설명·변경이력 제외) |
| TS-404 | F-4 AC | 통합(L3) | clone-copy 설치 후 user-registry 항목에 commit_sha 기록 |

---

### F-005: 관리 워크플로우 4절차 재작성

#### 3.5.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | 검색·설치·제거·업데이트 4절차 재작성 + migrate 트리거 명시 | `:16-101` |

#### 3.5.2 설계 (4절차, 상호 모순 0건 — F-5 AC)
- **관리 진입 훅**: 4절차 시작 전 `skill-registry.js migrate` 멱등 실행 (F-001 트리거).
- **① 검색**: `node skill-registry.js match "{검색어}"`로 설치 여부 대조 → 미설치 시 `npx skills find [query]` 생태계 검색(C-3 find 유지). Unknown 라이선스 항목에 경고 표시.
- **② 설치**: clone-copy(F-004 §3.4.2(b)) → commit_sha 기록 → user-registry.json 등록(F-006). `npx skills add` 제거.
- **③ 제거**: `~/.opal/community-skills/{vendor}/{skill}/` 디렉토리 삭제(path 검증 후) + user-registry.json 항목 제거. 프레임워크 카탈로그(references)는 미변경.
- **④ 업데이트** (R-6): `git ls-remote https://github.com/{owner}/{repo}.git HEAD`로 upstream HEAD sha 조회 → user-registry.json 기록 commit_sha와 비교. 불일치 또는 commit_sha=null(레거시) → 재설치(clone-copy) 제안. `npx skills check`는 보조 확인용 유지 (H-7).

#### 3.5.3~3.5.4 환경/배치
git CLI(clone, ls-remote). 신규 패키지 0.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-501 | F-5 AC | 산출물 검사 | 4절차가 각각 단계 목록으로 기재, 상호 모순 문구 0건 |
| TS-502 | F-5 AC④ | 산출물 검사 | 업데이트 절차에 commit_sha 비교 로직 명시 |
| TS-503 | F-5 AC③ | 통합(L2) | 제거: vendor 디렉토리 삭제 + user-registry 항목 제거, 카탈로그 불변 |

---

### F-006: registry 갱신 경로 정의 (user-registry.json 격리 + 병합 로드)

#### 3.6.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/skill-registry/skill-registry.js` | 도구 | `loadAllSkills`가 `~/.opal/community-skills/user-registry.json` 병합 로드(방어적) | `:84-93` |
| 2 | `opal/skills/opal-skill-manager/SKILL.md` | 스킬 | 사용자 등록분=user-registry.json, 프레임워크 카탈로그=references 경계 명문화 | `:103-125` |
| 3 | `opal/core/references/community-skills-registry.json` | 참조 | schema_notes에 이원 registry 경계 명시 | `:5` |
| 4 | `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` | 문서 | 커뮤니티 registry 이원 경계·install 덮어쓰기 관계 반영 | `ARCH:180`, `CONV:203` |

#### 3.6.2 설계 (R-3 결정 = 사용자 등록분 격리 + 최소 install 변경)

**핵심 결정**: 사용자 수동 설치 등록분을 install이 절대 건드리지 않는 `~/.opal/community-skills/user-registry.json`에 기록한다. 프레임워크 카탈로그(`~/.opal/references/community-skills-registry.json`)는 install이 계속 덮어써 카탈로그 업데이트를 전파한다.

**(a) 병합 로드** (`:84-93`, H-3):
```js
function loadUserRegistry() {
  const p = path.join(os.homedir(), '.opal', 'community-skills', 'user-registry.json');
  try {
    if (!fs.existsSync(p)) return null;
    return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) { return null; }   // 파손 시 무시 — CLI 전체 다운 방지 (H-3)
}
function loadAllSkills() {
  const refDir = getReferencesDir();
  const main = loadJsonFile(path.join(refDir, 'opal-skills-registry.json'));
  const community = loadJsonFile(path.join(refDir, 'community-skills-registry.json'));
  const userReg = loadUserRegistry();
  const skills = [];
  if (main) skills.push(...flattenGroups(main, 'main'));
  if (community) skills.push(...flattenGroups(community, 'community'));
  if (userReg) {
    // 사용자 항목 병합 — 동일 name은 사용자 항목 우선(override), 신규 name은 추가
    const userSkills = flattenGroups(userReg, 'community');
    const names = new Set(skills.map(s => s.name));
    for (const us of userSkills) {
      const idx = skills.findIndex(s => s.name === us.name);
      if (idx >= 0) skills[idx] = us; else skills.push(us);
    }
  }
  return skills;
}
```
- user-registry.json 스키마 = community-skills-registry.json과 동일(`groups[vendor][]`) → `flattenGroups`(`:42-58`) 재사용. [MUST] 스키마 버전 문자열 불변(하위호환).
- 부재/파손 시 null 반환 → 기존 동작과 완전 동일(신규 사용자 무영향, H-3).

**(b) install 경계** (R-3 근거):
- install-mac.sh/windows.ps1 **코드 변경 0건**. `community-skills/`는 이미 clean_dirs 제외(`install-mac.sh:1033-1034`, `windows.ps1:432-433`)이므로 user-registry.json은 install이 절대 삭제·덮어쓰지 않음(142 D-4). references 덮어쓰기(`:1362`)는 프레임워크 카탈로그에만 영향 → 사용자 데이터 소실 경로 제거.
- [MUST] `docs/CONVENTIONS.md` §배포 경계 `:203`: 사용자 설치 등록분 기록은 "사용자 요청 기반 런타임 데이터 쓰기"로 개발 시 `~/.opal/` 프레임워크 파일 직접 편집과 구분됨을 문서에 명시(오해 방지). skill-manager는 기존에도 런타임에 registry를 갱신함(`SKILL.md:72,92`) — 대상만 references→community-skills/user-registry.json으로 이전.

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-601 | F-6 AC | 기능(L1) | user-registry.json 부재→기존 동작 동일, 정상→병합, 파손→무시(CLI 정상) |
| TS-602 | F-6 AC | 기능(L2) | 동일 name 사용자 항목 override, 신규 name 추가 |
| TS-603 | F-6 AC | 통합(L2 install 실측) | install 재실행 후 user-registry.json 잔존 + references 카탈로그 갱신 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-002, F-006, F-001 | 1, 2, 3 | opal-task-agent | 순차(동일 파일 skill-registry.js) | RED-first 테스트 선행 |
| 2 | F-004 | 4 | opal-task-agent | 순차 | skill-registry.js match 출력 + 문서 |
| 3 | F-003, F-005 | 5, 6 | opal-task-agent | 순차 | skill-manager/skill-commands 재작성 (JS 확정 후) |
| 4 | F-004, F-006 | 7 | PM 직접 | 순차 | docs/ 갱신 |
| 5 | 전 기능 | 8 | opal-test-agent | 최종 | 테스트 GREEN + E2E |

### 4.2 실행 체크리스트
> 총 8개 Step | Phase 5개 | 실행 모드: 복잡

#### Step 1: skill-registry.js 신규 동작 RED-first 테스트 작성
- [ ] 완료
- **소속 기능**: F-001, F-002, F-006
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/tests/test-match.js`(신규), `opal/tools/skill-registry/tests/test-migrate.js`(신규)
- **작업 내용**: TS-101~104, TS-201~204, TS-601~602를 node:test 블랙박스/함수 단위로 작성. 합성 fixture(임시 community-skills 디렉토리 + HOME 오버라이드) 사용, 기존 `test-validate.js:44-115` makeFixture 패턴 계승. 현행 코드 대비 FAIL(RED) 확인.
- **완료 기준**: 신규 테스트 실행 시 RED(현행 미구현 항목 FAIL) 확인. 기존 `test-validate.js` 5TC는 GREEN 유지.
- **테스트**: TS-101~104, TS-201~204, TS-601~602
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: skill-registry.js — 경로 탐지 + basename 매칭 + 병합 로드 구현
- [x] 완료
- **소속 기능**: F-001, F-002, F-006
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: (F-001) `resolveCommunitySkillPath` 헬퍼 추가 + `matchCommand:208`·`validate:364` installed 계산 교체 (§3.1.2(a)). (F-002) `matchByAlias` basename+ambiguous (§3.2.2(a)), `matchCommand` ambiguous 분기 (§3.2.2(b)). (F-006) `loadUserRegistry`+`loadAllSkills` 병합 (§3.6.2(a)). @header 변경이력 라인 갱신.
- **완료 기준**: Step 1 테스트 중 TS-101~104(경로/migrate 제외분)·TS-201~204·TS-601~602 GREEN. 기존 5TC 회귀 GREEN.
- **테스트**: TS-101, TS-201~204, TS-601, TS-602
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: skill-registry.js — migrate 서브커맨드 구현
- [x] 완료
- **소속 기능**: F-001
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/skill-registry.js`
- **작업 내용**: `migrateCommand(dryRun)` (§3.1.2(b)) + CLI 라우터 `case 'migrate'` + `--dry-run` 파싱 + usage 갱신. path traversal 검증. 미등재/충돌 preserved 처리(142 D-4).
- **완료 기준**: TS-102~104 GREEN. `migrate --dry-run` 무부작용. 재실행 멱등.
- **테스트**: TS-102, TS-103, TS-104
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: skill-registry.js match 출력 clone-copy 전환 + registry schema_notes
- [x] 완료
- **소속 기능**: F-004
- **영역**: 도구 + 참조
- **agent**: opal-task-agent
- **파일**: `opal/tools/skill-registry/skill-registry.js`, `opal/core/references/community-skills-registry.json`
- **작업 내용**: match 출력 `install_command` npx→clone-copy, `install_method:"clone-copy"` 추가 (§3.4.2(a)). registry `schema_notes`에 clone-copy·commit_sha 기록 규칙 + 이원 registry(카탈로그/user-registry) 경계 반영. [MUST] 스키마 버전 문자열 불변.
- **완료 기준**: TS-401 GREEN. `validate` 회귀 GREEN(v2.1 인식 유지). schema_notes 갱신.
- **테스트**: TS-401, TS-402
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 5: opal-skill-manager SKILL.md — 4절차 재작성 + §6 clone-copy
- [x] 완료
- **소속 기능**: F-003, F-004, F-005, F-006
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-skill-manager/SKILL.md`
- **작업 내용**: §1~§5 4절차 재작성(§3.5.2) — 관리 진입 migrate 훅, 검색(find+대조), 설치(clone-copy+commit_sha+user-registry), 제거(디렉토리+user-registry 항목), 업데이트(ls-remote commit_sha 비교). §6 clone-copy 재작성(§3.3.2) + ambiguous 분기. §설치 경로 규칙에 이원 registry 경계 명문화. npx add 전량 제거. 변경이력 v1.4 행 추가.
- **완료 기준**: TS-301~303, TS-501~503 산출물 검사 통과. 소스 내 `npx skills add` 설치 지시 0건. 4절차 모순 0건.
- **테스트**: TS-301, TS-302, TS-303, TS-501, TS-502, TS-503
- **실행 방법**: sub-agent
- **의존**: Step 3, Step 4

#### Step 6: skill-commands.md 문구 미세 정합
- [x] 완료
- **소속 기능**: F-003
- **영역**: 참조
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/skill-commands.md`
- **작업 내용**: v1.2 라우팅·정책 원문 유지. 설치 방식이 clone-copy임을 반영하는 문구 미세 조정(§6 참조 문구 정합). 변경 발생 시에만 변경이력 v1.3 행 추가(무실질변경 시 스킵).
- **완료 기준**: skill-commands 라우팅 ↔ §6 절차 모순 0건 (TS-302).
- **테스트**: TS-302
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: docs/ 갱신 (ARCHITECTURE.md, CONVENTIONS.md)
- [ ] 완료
- **소속 기능**: F-004, F-006
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`
- **작업 내용**: ARCHITECTURE.md 설치 명령 npx add→clone-copy (`:178,226`, find `:177` 유지), 커뮤니티 스킬 registry 이원 경계(`:80,180`) 반영. CONVENTIONS.md 배포 경계 절(`:203`)에 커뮤니티 registry 이원(카탈로그=install 덮어쓰기 / user-registry=community-skills 불가침) 관계 및 런타임 사용자 데이터 쓰기 구분 명시.
- **완료 기준**: 시스템 구조 변경(설치 방식·registry 이원)이 두 문서에 반영. npx add 설치 명령 잔존 0.
- **테스트**: TS-403(문서 포함 grep)
- **실행 방법**: direct
- **의존**: Step 5

#### Step 8: 전체 테스트 GREEN + E2E 검증
- [ ] 완료
- **소속 기능**: 전 기능
- **영역**: 도구/테스트
- **agent**: opal-test-agent
- **파일**: `opal/tools/skill-registry/tests/*.js`
- **작업 내용**: `node test-validate.js`·`test-match.js`·`test-migrate.js` 전량 GREEN 확인(회귀). E2E: 스크래치패드 합성 flat 설치 → migrate → `//pdf 문서` match `installed:true` → clone-copy(§6) → SKILL.md Read 흐름(TS-301, TS-404, TS-603) 실측. `npx skills add` grep 0건(TS-403).
- **완료 기준**: 기존 5TC + 신규 TC 전량 GREEN. E2E PASS. grep 0건.
- **테스트**: 전 TS
- **실행 방법**: sub-agent
- **의존**: Step 6, Step 7

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → 2 → 3 → 4 | 모두 동일 파일 `skill-registry.js` 순차 편집 (파일 충돌 방지) |
| Step 2 → 4 | match 출력 변경이 경로/병합 구현 전제 |
| Step 5 ← Step 3,4 | 문서 재작성은 JS 동작(migrate·install_method) 확정 후 |
| Step 6 ← Step 5 | skill-commands 정합은 §6 재작성 후 |
| Step 7 ∥ Step 6 | docs/(PM)와 skill-commands(참조)는 독립, 단 둘 다 Step 5 이후 |
| Step 8 ← 전체 | 최종 검증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | flat/vendor/미설치 경로 탐지 정확성 | TS-101 | 3분기 정확 반환 |
| F-001 | migrate 이동·멱등·미등재 보존 | TS-102, TS-103, TS-104 | 등재 이동·미등재 보존·재실행 무변화, list 전수 installed:true |
| F-002 | basename 매칭 + cleanInput | TS-201, TS-202 | `anthropics/pdf`+`문서 만들어줘`, `//brainstorming` 매칭 |
| F-002 | 정식명 하위호환 + 충돌 후보 목록 | TS-203, TS-204 | 정확 매칭 단일, 충돌 시 ambiguous+candidates |
| F-003 | 미설치 `//` → clone-copy 설치·실행 | TS-301, TS-303 | E2E 통과, §6 SKILL.md Read 단계 명시 |
| F-003 | skill-commands ↔ §6 모순 0 | TS-302 | 정책 원문 정합 |
| F-004 | npx add 제거 + clone-copy 출력 | TS-401, TS-403 | match npx 문구 0, 소스 설치 지시 0건 |
| F-004 | source_repo 파싱 + commit_sha | TS-402, TS-404 | owner/repo@subdir 파싱, commit_sha 기록 |
| F-005 | 4절차 기재·모순 0·업데이트 비교 | TS-501, TS-502, TS-503 | 4절차 단계 목록, commit_sha 비교, 제거 정합 |
| F-006 | 병합 로드 방어성 + install 보존 | TS-601, TS-602, TS-603 | 부재/파손 안전, override/추가, install 후 잔존 |

### 5.2 회귀 테스트
- [ ] 기존 `test-validate.js` 5TC(TC1~5) GREEN 유지
- [ ] `match`/`get`/`list`/`validate` 기존 응답 형식 하위호환 (main 스킬 응답 불변)
- [ ] registry v2.1 스키마 인식 유지 (`validate:340-341`)

### 5.3 코드/문서 품질
- [ ] `docs/CONVENTIONS.md` 준수 (kebab-case, @header, 인용)
- [ ] 변경이력 기록: skill-registry.js @header, skill-manager SKILL.md 표, community-skills-registry.json(배포 시 strip 대상 아님 — schema_notes만), skill-commands.md 표(변경 시)
- [ ] install 스크립트 코드 변경 0건 확인 (R-3 최소 변경)

### 5.4 보안
- [ ] migrate/제거의 `renameSync`/`rm` 대상 경로가 `~/.opal/community-skills/` 하위로 검증되는가 (CWE-22)
- [ ] clone URL이 source_repo에서 안전하게 구성되는가 (임의 명령 주입 없음)
- [ ] user-registry.json 파손 시 CLI 다운 없이 graceful 무시 (DoS 방어)
- [ ] 하드코딩 시크릿·토큰 0

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 7개(신규 2 + 수정 5, docs 2 포함 시 9) | 복잡 |
| 모듈 범위 | 도구(JS)+스킬(md)+참조(md/json)+문서(md) 다중 | 복잡 |
| 작업 유형 | 대규모 개선(워크플로우 통일) | 복잡 |
| 외부 의존성 | git CLI(clone/ls-remote) — 기존 사용 범위 | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **파일 충돌 방지**: `skill-registry.js`를 만지는 Step 1~4는 반드시 동일 에이전트(opal-task-agent) 순차 배치. `skill-manager/SKILL.md`를 만지는 Step 5도 동일 에이전트.
- **Batch 1**: Step 1(RED 테스트) → **Batch 2**: Step 2→3→4(JS 구현, 순차) → **Batch 3**: Step 5→6(문서, 순차) ∥ Step 7(PM docs) → **Batch 4**: Step 8(opal-test-agent 최종).
- PM 매핑 테이블: 본 태스크 전 영역 Framework(`opal/`, `scripts/`) → opal-task-agent 단일. docs/ 갱신만 PM 직접, 최종 검증만 opal-test-agent.

### C-2. 스킬 요구사항
- 기존 스킬로 충분. skill-manager SKILL.md 자체가 산출물. 신규 스킬 갭 없음.

### C-3. 도구 요구사항
- CLI: `node`(내장), `git`(clone/rev-parse/ls-remote). 신규 npm 패키지 0.
- MCP: 불필요 (외부 라이브러리 조회 없음, ANALYSIS §6.3).

### C-4. 테스트 전략
- **RED-first**: F-001(경로/migrate)·F-002(matchByAlias)·F-006(병합)은 결정론적 순수 함수/CLI → RED-first 적용(Step 1 선행). 기존 `test-validate.js`가 RED-first 트랙(029)이므로 동일 규율 계승.
- **문서(F-003/F-005)**: 단위 테스트 부적합 → 산출물 검사(grep 모순/npx 0건) + E2E로 검증.
- **회귀**: `node test-validate.js` 기존 5TC.
- **E2E**: 스크래치패드 합성 flat 설치 → migrate → `//pdf` 흐름 실측(Step 8).
- **보안**: path traversal(renameSync/rm 경로 검증), grep 하드코딩 시크릿.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 | Node.js (fs/path/os 내장, 의존성 0) | - |
| 테스트 | node:test 내장 | - |
| 스킬/참조 | Markdown | - |
| 설치 | Bash/PowerShell (변경 0건 목표) | - |
| 마이그레이션·설치 | git CLI | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 조회 불필요 (Node 내장만) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | 경로 탐지·매칭·병합·match 출력 수정 대상 |
| D-2 | 소스 | test-validate.js | `opal/tools/skill-registry/tests/test-validate.js` | fixture 패턴·RED-first 규율 계승 |
| D-3 | 참조 | skill-commands.md (v1.2) | `opal/core/references/harness/skill-commands.md` | 미설치 라우팅 SSOT(선반영 유지) |
| D-4 | 스킬 | opal-skill-manager SKILL.md | `opal/skills/opal-skill-manager/SKILL.md` | 4절차·§6 재작성 대상 |
| D-5 | 참조 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | v2.1 스키마·source_repo·commit_sha·schema_notes |
| D-6 | 소스 | install-mac.sh | `scripts/install-mac.sh` | community-skills 불가침(`:1033`)·references 덮어쓰기(`:1362`) 실측 |
| D-7 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | 동등 배포 로직(`:432,555`) |
| D-8 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 배포 경계·플랫폼 분기·변경이력·도구 우선 [MUST] |
| D-9 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | npx 언급 제거(`:178,226`)·registry 이원 경계 |
| D-10 | 참조 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용·[MUST] 포맷 |
| D-11 | 외부 | vercel-labs/skills CLI | [skills.sh](https://skills.sh/) | find/check 전용 축소(add 경로 지정 불가) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 마이그레이션 실행 주체 미결정 | F-001 | 중 | **결정**: skill-registry.js `migrate` 서브커맨드(도구 자기완결) + skill-manager 관리 진입 트리거. install 훅 아님(142 D-4 유지). getCommunitySkillPath 이중 탐지로 마이그레이션 전에도 정상 판정 → 지연 트리거 안전 |
| R-2 | basename 충돌 처리 미정의 | F-002 | 중 | **결정**: 정식명>단일 basename>충돌 시 ambiguous+candidates 목록. 현행 충돌 0(전방 안전) |
| R-3 | registry 사용자 데이터 소실 | F-006 | 높음 | **결정**: user-registry.json을 community-skills/(install 불가침)에 격리 + loadAllSkills 병합. install 코드 변경 0건 |
| R-4 | Windows 어댑터 동등성 | F-006 | 중 | install 코드 변경 0건이므로 동등성 리스크 소거. windows.ps1 clean_dirs·references cp 실측 확인(`:433,555`) |
| R-5 | npx CLI 향후 변경 | F-004 | 낮음 | clone-copy로 add 의존 제거. find/check만 npx 잔존 |
| R-6 | commit_sha 업데이트 감지 미정의 | F-005 | 중 | **결정**: git ls-remote HEAD ↔ user-registry commit_sha 비교, 불일치/null 시 재설치 제안 |
| R-7 | user-registry.json 파손 | F-006 | 중 | 방어적 로드(try/catch null) — CLI 다운 방지(H-3) |
| R-8 | ANALYSIS §4(4) 구스냅샷 오인용 | F-003 | 낮음 | skill-commands.md v1.2 직접 Read로 확인 — 분기 이미 존재, §6 라우팅 선반영. 본 PLAN은 현재 파일 기준 |

---

## 결정 요약 (PLAN 확정 4건)

| 결정 | 내용 | 근거 |
|------|------|------|
| **R-1 마이그레이션 주체** | `skill-registry.js migrate` 서브커맨드(도구 자기완결) + skill-manager 관리 진입 시 멱등 트리거. **install 훅 아님**. `getCommunitySkillPath` 이중 탐지(vendor→flat)로 마이그레이션 전에도 정상 판정 | 142 D-4 install 불가침 유지(`install-mac.sh:1033`), 도구 우선 원칙(CONVENTIONS `:189`), 지연 트리거 안전성 확보 |
| **R-2 basename 충돌** | 정식명 정확 매칭 > 단일 basename > 충돌 시 `ambiguous:true`+candidates 후보 목록 반환(자동 선택 금지) | TASK F-2 AC, 현행 32개 basename 유일(전방 안전) |
| **R-3 사용자 등록분 보존** | user-registry.json을 `~/.opal/community-skills/`(install 불가침)에 격리 + `loadAllSkills` 병합 로드. **install 스크립트 코드 변경 0건** | install references 덮어쓰기 실측(`:1362`), 142 D-4(`:1033`), 최소 변경 우선 |
| **R-6 업데이트 감지** | `git ls-remote {repo} HEAD` ↔ user-registry commit_sha 비교. 불일치/null → 재설치(clone-copy) 제안. npx check 보조 유지 | registry commit_sha 옵션 필드(`registry.json:5`), C-3 |
