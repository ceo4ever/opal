# TASK: community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills)

> 작성일: 2026-05-10 | 작업 유형: 개선 (구조 변경) | 적용 스킬: opp | 모드: semi-agentic
> 입력: 캡틴 결정 (141 태스크 진행 중 도출, 2026-05-10) — community-skills의 third-party 라이선스 책임 회피 + 유지보수 부담 0
> 출력: TASK.md / PLAN.md / DONE.md + 실제 구조 변경(번들 제거, install/registry/skill-manager 갱신)

## 작업 목표

OPAL repo에 통째 번들된 community-skills(30개 SKILL.md / 6개 조직)를 제거하고, vercel-labs/skills 표준(`skills.sh` 카탈로그 + `npx skills` CLI)을 통해 사용자가 자신의 환경에서 fetch하는 구조로 전환한다. (1) 라이선스 책임 회피 — third-party 코드 재배포 안 함, (2) 유지보수 부담 0 — 원본 업데이트는 사용자가 `npx skills check`로 받음, (3) 표준 정합 — vercel-labs/skills 생태계와 일관.

## 배경

현재 OPAL은 `community-skills/` 폴더에 6개 조직(anthropics, getsentry, google-labs-code, openai, trailofbits, vercel-labs) 30개 SKILL.md를 통째 번들로 보유하고 install이 `~/.opal/community-skills/`에 통째 복사한다. 그러나:

1. **라이선스 정합 결함**: 4개 조직(getsentry / google-labs-code / trailofbits / vercel-labs)의 LICENSE 파일이 우리 번들에 누락 — 미국 저작권법상 명시 라이선스 없는 코드는 "All Rights Reserved" 간주, 재배포 위험. anthropics + openai는 Apache-2.0 LICENSE.txt 보존되어 있으나 NOTICE 의무 미이행.
2. **유지보수 부담**: third-party 코드 30개를 OPAL이 동기화 책임 — 원본 업데이트 시 우리 repo도 수동 갱신 필요.
3. **OPAL repo 비대화**: 30개 폴더 + 부록이 tarball 크기 + install 시간 증가 요인.
4. **이미 fetch 메커니즘 보유**: `opal-skill-manager` 스킬이 이미 `npx skills find`/`add`/`check` 통합 + git clone 설치 흐름을 정의 — **번들 + 온디맨드의 모순 상태**.

캡틴 결정(2026-05-10): "왜 굳이 30개를 번들로 가지고 다니지? skills.sh에서 검색해서 받아 쓰면 라이선스 문제도 없고 더 깔끔하지 않아?"

## 배경 분석 (대화에서 도출)

### 현 상태 실측

| 영역 | 현 위치 | 동작 |
|---|---|---|
| 소스 번들 | `community-skills/` (저장소 루트, 6 조직 / 30 SKILL.md) | tarball 포함 → archive 다운로드 시 함께 옴 |
| install 복사 | `install-mac.sh:906-910` / `windows.ps1:506` | `community-skills/` → `~/.opal/community-skills/` 통째 복사 |
| 레지스트리 | `opal/core/references/community-skills-registry.json` | 30개 항목 (name / triggers / paths) — 사용자 머신의 `~/.opal/community-skills/`를 가리킴 |
| 인덱싱 | `skill-registry.js:47, 185-199` | community-skills-registry.json 로드 → `//` 매칭에 사용 |
| 사용 흐름 | `//` 커맨드 trigger 매칭 → 사용자 머신의 SKILL.md를 Read → 알투가 그 절차를 따름 | LLM 직접 사용 (워커 디스패치 X) |
| 관리 스킬 | `opal/skills/opal-skill-manager/SKILL.md` | `npx skills find/add/check` 통합 + git clone 설치 / `~/.opal/community-skills/` 직접 관리 / 레지스트리 항목 추가·제거 |
| 라이선스 보존 | anthropics/openai만 LICENSE.txt 보유 (Apache-2.0). 4개 조직 누락. | NOTICE 의무 미이행 |

### vercel-labs/skills 생태계 정합성

- `https://skills.sh` = vercel-labs/skills 프로젝트의 웹 카탈로그 (검색·발견용)
- 표준 CLI: `npx skills find <query>` / `npx skills add <owner/repo@skill>` / `npx skills check`
- OPAL의 `opal-skill-manager`가 이 CLI를 이미 활용하는 코드 보유

## 확정된 설계 방향 (대화에서 합의)

1. **번들 완전 제거**: `community-skills/` 폴더를 OPAL repo에서 삭제. 사용자는 빈 상태로 시작.
2. **표준 메커니즘 채택**: `skills.sh` 카탈로그 + `npx skills` CLI를 SSOT로. OPAL 자체 다운로드 로직 신설 X (이미 `opal-skill-manager`가 이 CLI를 활용).
3. **라이선스 책임 회피**: OPAL repo는 third-party 코드를 재배포하지 않음. 사용자가 본인 동의로 fetch.
4. **유지보수 부담 0**: 원본 업데이트는 사용자가 `npx skills check`로 받음.
5. **mac/Windows 동등 처리**: install-mac.sh와 install/windows.ps1 모두 community-skills 복사 단계 제거.
6. **141 후속 정리**: README L729("30개 / 6개 조직") 표기를 본 태스크에서 갱신 — 새 메커니즘에 맞는 표현으로.
7. **mac/Windows 회귀 영향**: install 흐름 변경 + ~/.opal/community-skills/ 비워진 상태 → 사용자 머신에서 PLAN/EXECUTE/회귀 검증 필요.

### 미확정 → 확정 (캡틴 결정 2026-05-10 17:05)

8. **D-1 미설치 호출 처리 = 첫 호출 시 동의 prompt + 자동 fetch**: 사용자가 `//pdf` 같은 community 트리거를 호출했을 때 미설치 상태면, 알투가 "이 스킬은 외부({라이선스}). 다운로드해서 설치할까요?" 한 줄 prompt → 수락 시 `npx skills add {owner/repo@skill}` 자동 호출 → 설치 후 즉시 실행. 거부 시 "수동 설치는 `//skill-manager`로" 안내.
9. **D-2 community-skills-registry.json = 메타데이터 카탈로그 변환 (paths 동적)**: `name` / `triggers` / `source_repo` / `license` 필드만 유지. `paths`는 동적 — 사용자 머신의 `~/.opal/community-skills/{owner}/{skill}/SKILL.md` 존재 여부로 결정. 트리거 매칭 흐름은 변경 없음, 다만 미설치 케이스 분기 추가.
10. **D-3 skill-registry.js = 미설치 감지 + fetch prompt 로직 추가**: 트리거 매칭됐는데 SKILL.md 미존재 → "외부 스킬, 설치할까요?" 안내 + `source_repo` 정보 노출. 자동 fetch는 알투(에이전트)가 수행 (registry는 정보 제공만, npx 호출은 알투/opal-skill-manager).
11. **D-4 기존 사용자 마이그레이션 = 그대로 보존 + 마이그레이션 안내 미게재**: install이 `~/.opal/community-skills/`를 절대 건드리지 않음 (clean_dirs 배열에서 제거). 기존 사용자(캡틴 mac)의 30개 SKILL.md 그대로 유지 — 동작 무변화. 신규 사용자가 압도적이라 install에 마이그레이션 안내 한 줄도 추가하지 않음 — 깔끔한 신규 케이스 흐름 유지.
12. **D-5 ~ D-9는 PLAN 워커 합리적 디폴트 결정**: opal-skill-manager SKILL.md "기본 번들" 표현 제거 / install 분기 제거 / ARCHITECTURE.md §커뮤니티 스킬 재서술 / README L729 표기 — 모두 본 §확정 방향과 정합되는 자연 결정으로 PLAN 워커가 처리.

## 미확정 사항 (PLAN에서 결정)

본 태스크는 구조 변경이라 PLAN 워커가 다음 결정을 내려야 한다:

| ID | 결정 사항 | 옵션 |
|----|----------|------|
| D-1 | 첫 호출 시 자동 설치 vs 명시 install 명령 vs 추천 묶음 미니 번들 | (a) 첫 //커맨드 호출 시 미설치 감지 → "설치하시겠습니까?" prompt → 자동 fetch / (b) `opal-cli skill install <owner/repo@skill>` 명시 명령만 / (c) 기본 install이 추천 5~10개(라이선스 명확한 anthropics 일부)는 자동 fetch + 나머지는 온디맨드 |
| D-2 | community-skills-registry.json 처리 | (a) 완전 제거 / (b) 메타데이터 카탈로그(이름·트리거·source_repo·라이선스)만 유지하고 paths 동적 / (c) 사용자 머신의 설치 상태를 반영하는 동적 인덱스 |
| D-3 | skill-registry.js 동작 | (a) 미설치 감지 + 자동 fetch 로직 추가 / (b) 미설치 시 단순히 "설치 필요" 안내 + opal-skill-manager 호출 권유 |
| D-4 | 기존 사용자 마이그레이션 | (a) install이 ~/.opal/community-skills/ 그대로 두기(보존) / (b) install이 비번들 형태로 갱신 안내(설치된 30개는 사용자가 npx skills check로 갱신) / (c) install이 ~/.opal/community-skills/를 정리하고 빈 상태로 만들기(파괴적, 비추천) |
| D-5 | opal-skill-manager 변경 범위 | (a) 변경 없음 — 이미 npx skills 활용 중 / (b) "기본 번들 31개" 표현 갱신 + fetch 흐름 강조 |
| D-6 | install/windows.ps1 의 community-skills 복사 단계 | 단순 제거 / 또는 빈 디렉토리만 생성 |
| D-7 | mac install-mac.sh 의 community-skills 복사 단계 (`install_opal_mcp` 또는 별도 함수) | 단순 제거 |
| D-8 | ARCHITECTURE.md 갱신 | "커뮤니티 스킬 (Community Skills)" 섹션을 fetch 방식으로 재서술 + 배포 모델 다이어그램에서 community-skills/ 라인 제거 |
| D-9 | README 표기 갱신 | L37 (주요 특징) "커뮤니티 스킬 — 외부 조직이 제공하는 스킬을 원본 수정 없이 통합" 유지 / L729 표기를 "skills.sh 카탈로그 통합 — `//skill-manager`로 검색·설치" 같은 동적 표기로 |

## 요구사항

- [x] **R-1 community-skills 폴더 제거**: OPAL repo의 `community-skills/` 폴더 통째 삭제. 무엇을: 6개 조직 디렉토리 전체 + LICENSE.txt 포함 / 어디에: 저장소 루트 / 왜: third-party 재배포 회피 / AC: `ls community-skills` → no such file (제거 검증). git에서 추적 안 됨.
- [x] **R-2 install 스크립트 community-skills 복사 단계 제거**: 무엇을: install-mac.sh의 `cs_src/cs_dst` 복사 로직 제거 + windows.ps1 :506 부근 vendor 단위 덮어쓰기 로직 제거 + clean_dirs 배열에서 community-skills 항목 제거(로컬 보존을 위해) / 어디에: scripts/install-mac.sh + scripts/install/windows.ps1 / 왜: 번들 사라지면 복사 대상 없음 / AC: 두 스크립트의 community-skills 관련 라인 0건 또는 명시적 "사용자가 opal-skill-manager로 설치" 안내 한 줄
- [x] **R-3 community-skills-registry.json 처리**: PLAN D-2 결정 따름. 무엇을: 완전 제거 또는 메타데이터 카탈로그로 변환 / 어디에: opal/core/references/community-skills-registry.json / 왜: paths가 사용자 머신 의존 — 정적 인덱스 부적합 / AC: PLAN D-2 결정에 따라 (a) 파일 제거 + skill-registry.js 분기 정리 또는 (b) 메타데이터 스키마 재정의
- [x] **R-4 skill-registry.js 갱신**: 무엇을: community-skills-registry.json 처리 분기를 PLAN D-3 결정에 맞게 갱신 / 어디에: opal/tools/skill-registry/skill-registry.js / 왜: 미설치 시 동작 정의 필요 / AC: 미설치 community 스킬을 trigger로 호출 시 fail 대신 의미 있는 안내 (설치 권유 또는 자동 fetch)
- [x] **R-5 opal-skill-manager SKILL.md 갱신**: PLAN D-5 결정 따름. 무엇을: "기본 번들 31개는 install-mac.sh로 자동 설치" 표현 제거 + fetch 흐름이 SSOT임을 명시 / 어디에: opal/skills/opal-skill-manager/SKILL.md / 왜: 번들 사라지면 모순 / AC: SKILL.md에 "번들" 표현 0건, "fetch via npx skills" 흐름 명확
- [x] **R-6 README 갱신**: 무엇을: L37 + L729 + (해당 시) 사전 요구사항 표 — fetch 메커니즘 표현으로 / 어디에: README.md / 왜: 141 결과 후속 정리 / AC: 정적 카운트 표기 제거 또는 "skills.sh 카탈로그 통합"으로 변경
- [x] **R-7 ARCHITECTURE.md 갱신**: 무엇을: §컴포넌트 유형 §커뮤니티 스킬 + §배포 모델 다이어그램 갱신 / 어디에: docs/ARCHITECTURE.md / 왜: 구조 변경 반영 / AC: community-skills 카운트 표기 + 배포 모델에서 번들 라인 제거, fetch 흐름 1줄 추가
- [x] **R-8 회귀 검증**: 무엇을: install 재실행 → ~/.opal에 community-skills/ 비어 있음 / `//` 커맨드 매칭 시 의미 있는 안내 / `//skill-manager`로 검색·설치 흐름 정상 / 어디에: mac + Windows / 왜: 구조 변경의 사용자 영향 검증 / AC: 새 install이 정상 종료 + opal-skill-manager `npx skills find` 호출 통과 + 미설치 community trigger 호출 시 안내 노출

## 제약 조건

- **변경이력 의무**: install-mac.sh / windows.ps1 / skill-registry.js / opal-skill-manager/SKILL.md 모두 변경이력 필수 (`docs/CONVENTIONS.md` §변경이력 작성 의무).
- **CONVENTIONS.md / Guards 준수**: 사용자 명시 승인 후에만 EXECUTE. 자동 커밋 금지.
- **mac/Windows 동등 처리**: install 분기 격리 — 같은 동작이 양 OS에서 보장되어야.
- **사용자 데이터 보존**: 기존 사용자의 `~/.opal/community-skills/`는 install이 파괴하지 않음 (D-4 (a) 또는 (b) 채택). install-mac.sh는 v0.3 시리즈에서 "사용자 데이터 보존" 원칙 확립.
- **mac/Windows 회귀 검증 의무**: 본 태스크는 구조 변경이라 단순 텍스트 정정과 다름 — 양 OS에서 install 재실행 + opal-skill-manager 동작 확인 필요.
- **141 후속 정리 의무**: 141의 R-7(community-skills 카운트 표기)은 본 태스크 완료 시점에 다시 갱신.

## 기술 스택

- **install 스크립트**: bash (mac) / PowerShell (Windows)
- **CLI 도구**: Node.js v18+ (`npx skills` 의존)
- **레지스트리**: JSON 스키마 v1 또는 v2 (PLAN 결정)
- **Skill 관리**: `npx skills` (vercel-labs/skills) — 외부 의존성
- **Git**: third-party clone (npx skills 내부 동작)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 외부 | skills.sh | https://skills.sh | 표준 카탈로그 SSOT |
| D-2 | 외부 | vercel-labs/skills | https://github.com/vercel-labs/skills | `npx skills` CLI 구현 |
| D-3 | 소스 | install-mac.sh | `scripts/install-mac.sh` | R-2 변경 대상 (mac) |
| D-4 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | R-2 변경 대상 (Windows) |
| D-5 | 소스 | community-skills-registry.json | `opal/core/references/community-skills-registry.json` | R-3 변경 대상 |
| D-6 | 소스 | skill-registry.js | `opal/tools/skill-registry/skill-registry.js` | R-4 변경 대상 |
| D-7 | 소스 | opal-skill-manager | `opal/skills/opal-skill-manager/SKILL.md` | R-5 변경 대상 (이미 fetch 메커니즘 보유) |
| D-8 | 소스 | README.md | `README.md` | R-6 (141 후속 정리) |
| D-9 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | R-7 (구조 갱신) |
| D-10 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력 / Guards / 커밋 규칙 |
| D-11 | 컨텍스트 | 141 DONE.md | `tasks/141-260510-opp-readme-mit-license-p0/DONE.md` | community-skills 표기 후속 정리 의무 + 캡틴 결정 §0 근거 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
