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

**1단계: 설치 여부 대조**

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match "{검색어}"
```

- `installed: true` → 설치된 스킬 정보를 안내하고, "추가로 다른 스킬도 검색할까요?"를 물어본다
  - 사용자가 원하면: 2단계로 진행
  - 사용자가 불필요하면: 종료
- `ambiguous: true` (basename이 여러 vendor와 충돌) → `candidates` 목록을 표시하고, 정식명(`vendor/skill`)으로 재호출을 유도한다
- `installed: false` 또는 미매칭 → 2단계로 진행

**2단계: 생태계 검색**

```bash
npx skills find [query]
```

실행 결과에서 관련 스킬을 찾아 사용자에게 표시한다:

```
| 스킬명 | 설명 | 설치 |
|--------|------|------|
| owner/repo@skill | 설명 | //skill-manager 로 설치 요청 (clone-copy) |
```

Unknown 라이선스 항목에는 "⚠️ 라이선스 미확인" 경고를 표시한다.

**폴백 (npx 실행 실패 시):**

Node.js가 설치되어 있지 않으면 아래와 같이 안내한다:

```
npx 명령을 실행할 수 없습니다. 아래 방법으로 스킬을 검색해주세요:

- 웹 카탈로그: https://skills.sh/
- Node.js 설치 후: npx skills find [query]
```

### 2. 스킬 설치 (clone-copy 단일 방식)

검색 결과에서 사용자가 설치를 요청하면:

1. `source_repo`(`owner/repo@subdir` 형식)를 파싱한다:
   ```bash
   node ~/.opal/tools/skill-registry/skill-registry.js parse-source-repo "{source_repo}"
   # → { owner, repo, subdir }  (`@` 미포함 시 subdir=repo)
   ```
2. 임시 디렉토리에 clone한다:
   ```bash
   git clone --depth 1 https://github.com/{owner}/{repo}.git {tmp}
   ```
3. 복사 원본 디렉토리를 아래 순서로 탐지한다 (upstream repo 레이아웃이 `owner/repo@subdir` 그대로가 아닐 수 있음 — 064 S-9 실증):
   1. `{tmp}/{subdir}/SKILL.md` 존재 → 그 디렉토리를 원본으로 채택
   2. 없으면 `{tmp}/skills/{subdir의 basename}/SKILL.md` 존재 → 그 디렉토리를 원본으로 채택
   3. 그래도 없으면 `find {tmp} -maxdepth 3 -type d -name {basename}` 결과 중 `SKILL.md`를 보유한 디렉토리를 원본으로 채택
   4. 그래도 없으면 설치를 중단하고 탐색한 후보 경로 목록을 보고한다 (빈 디렉토리 복사 금지)

   채택된 원본을 아래 경로로 복사한다 (vendor·basename은 registry `name` 필드 기준이며, source_repo의 owner/subdir과 다를 수 있다):
   ```
   ~/.opal/community-skills/{vendor}/{basename}/
   ```
4. commit_sha를 확보한다:
   ```bash
   git -C {tmp} rev-parse HEAD
   ```
5. 임시 디렉토리를 정리한다.
6. `~/.opal/community-skills/user-registry.json`에 설치 항목을 기록한다 (아래 참조).

**[MUST] `~/.opal/references/community-skills-registry.json`(프레임워크 카탈로그)은 설치 시 수정하지 않는다.** 이 파일은 install이 배포 시 덮어쓰는 파일이라 여기에 기록하면 다음 install 재실행 때 소실된다.

**user-registry.json 기록 규칙**
- 경로: `~/.opal/community-skills/user-registry.json`
- 스키마: `community-skills-registry.json`과 동일 — `groups[vendor][] = [{ name, alias, description, triggers, source_repo, commit_sha, license }]`
- 부재 시 새로 생성, 존재 시 병합한다. 동일 `name` 항목이 이미 있으면 덮어쓴다(override), 없으면 추가한다.
- 이 파일은 `~/.opal/community-skills/` 하위에 있어 install이 절대 건드리지 않는다(카탈로그와 물리적으로 분리된 사용자 등록 영역).

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

알투가 `//pdf` 같은 community 트리거를 매칭했는데 skill-registry가 `installed: false`로 응답하면,
**라이선스가 확인된 스킬은 동의 대기 없이 자동으로 clone-copy 설치·실행**한다. 문제 있는 라이선스(미확인, Unknown)만 게이트한다.

> 근거: 소유자(캡틴) 확정 — "문제 있는 라이선스만 아니면 무조건 설치·실행" (064).

**분기 판정** (skill-registry `match` 응답의 `license`·`source_repo`·`ambiguous` 기준):

1. `license ≠ "Unknown"`(라이선스 확인됨) + `source_repo` 있음 → **자동 설치·실행** (동의 prompt 없음):
   - 비차단 통지 1줄만 표시:
     ```
     [자동 설치] {source_repo} · {license} · commit {commit_sha || "미고정(HEAD)"}
     ```
   - **§2 clone-copy 절차**를 실행한다 (`git clone` → 복사 → commit_sha 확보 → user-registry.json 기록)
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
