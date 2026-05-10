# DONE: community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills)

> 시작: 2026-05-10 17:02 | 완료: 2026-05-10 18:36 | 모드: semi-agentic | 적용 스킬: opp

## 작업 결과

OPAL repo에 통째 번들된 community-skills(31 SKILL.md / 6개 조직)를 제거하고, vercel-labs/skills 표준(`skills.sh` 카탈로그 + `npx skills` CLI)을 통해 사용자가 자신의 환경에서 fetch하는 구조로 전환했다. **(1) 라이선스 책임 회피** — third-party 코드 재배포 안 함 / **(2) 유지보수 부담 0** — `npx skills check`로 사용자가 직접 갱신 / **(3) 표준 정합** — vercel-labs/skills 생태계와 일관 / **(4) 사용자 데이터 보존** — 기존 `~/.opal/community-skills/`를 install이 절대 건드리지 않음.

## 캡틴 결정 SSOT (변경 없이 유지)

| ID | 결정 |
|----|------|
| D-1 | 미설치 호출 → 첫 호출 시 동의 prompt + 자동 fetch (`npx skills add`) |
| D-2 | community-skills-registry.json = 메타데이터 카탈로그 v2 (`name` / `triggers` / `source_repo` / `license`, paths 동적) |
| D-3 | skill-registry.js = 미설치 감지 + fetch prompt 정보 노출 |
| D-4 | 기존 사용자 보존 — install이 `~/.opal/community-skills/` 절대 건드리지 않음 |

## 최종 변경 파일

### 삭제

| # | 경로 | 내용 |
|---|------|------|
| D-1 | `community-skills/` (저장소 루트) | 6 vendor 31 SKILL.md 포함 553 파일 통째 git rm |

### 수정

| # | 경로 | 변경 |
|---|------|------|
| M-1 | `opal/core/references/community-skills-registry.json` | 스키마 v2.0.0 (`opal-community-skills-registry-v2`) — 31 항목 모두 `source_repo` + `license` 필드, paths 폐기 |
| M-2 | `opal/tools/skill-registry/skill-registry.js` | v1.0 헤더 신설 + `match` 응답에 `installed` / `source_repo` / `license` / `install_command` 4 필드 추가 + `validate` v2 인식 + `getCommunitySkillPath` / `isCommunitySkill` 헬퍼 |
| M-3 | `opal/skills/opal-skill-manager/SKILL.md` | v1.1 — "기본 번들 31개" 표현 제거 + §6 자동 fetch 흐름 추가 |
| M-4 | `scripts/install-mac.sh` | v2.0 (major) — `clean_dirs` 배열에서 `community-skills` 제거 + `install_opal_community_skills` 함수/호출부 통째 삭제 |
| M-5 | `scripts/install/windows.ps1` | v1.6.0 (minor) — `cleanDirs` 배열에서 `community-skills` 제거 + 복사 블록 :506-519 제거 + `.SYNOPSIS` 표현 갱신 |
| M-6 | `README.md` | L39 (주요 특징) `[skills.sh](https://skills.sh/)` 카탈로그 통합 표현 + L732 배포 다이어그램 갱신 |
| M-7 | `docs/ARCHITECTURE.md` | Global Layer 표 / §컴포넌트 유형 §커뮤니티 스킬 fetch 방식 재서술 / §배포 모델 다이어그램 community-skills 라인 제거 / 디렉토리 구조 트리 갱신 |
| M-8 | `docs/PROJECT.md` | community-skills 행/표현 갱신 |

## 요구사항 매핑

| ID | 핵심 | 결과 |
|----|------|------|
| R-1 | community-skills 폴더 제거 | ✅ |
| R-2 | install 분기 제거 (mac+Windows) | ✅ |
| R-3 | community-skills-registry.json 스키마 v2 | ✅ |
| R-4 | skill-registry.js 미설치 감지 + fetch 정보 노출 | ✅ |
| R-5 | opal-skill-manager 정합 (번들 표현 제거) | ✅ |
| R-6 | README 갱신 (141 후속 정리) | ✅ |
| R-7 | ARCHITECTURE.md 갱신 | ✅ |
| R-8 | 회귀 검증 (mac+Windows) | ✅ mac 캡틴 검증 통과 / Windows는 push 후 검증 |

## QA / 게이트 결과

- **PLAN QA**: pass_with_minor (Warning C-1 — Windows Step 11 검증 비대칭, EXECUTE 자체 보완)
- **EXECUTE QA**: pass_with_minor (Critical/Warning 0, Info 3건 차단 없음)
  - Info: Windows Step 11 //pdf 테스트 비대칭 (CLOSE 전 보완 권장 — 워커 자체 보완 적용)
  - Info: deployed v1 잔존 (install 재실행 후 자동 해소)
  - Info: PLAN Step 1 카운트 30 vs 실측 31 (기능 영향 0)
- **PM Gate**: TASK R-1~R-8 + D-1~D-4 모두 충족, 변경이력 4파일 완비, D-4 정합 확인
- **mac 회귀 검증**: 캡틴 직접 검증 통과 (2026-05-10 18:36)

## source_repo 검증 분류 (D-1 자동 fetch 가능 여부)

| 그룹 | 카운트 | source_repo | license | D-1 prompt 동작 |
|------|-------|-------------|---------|----------------|
| anthropics | 18 | `anthropics/skills@{skill}` | Apache-2.0 | 자동 fetch 가능 |
| openai | 1 | `openai/skills@security-best-practices` | Apache-2.0 | 자동 fetch 가능 |
| vercel-labs | 5 | `vercel-labs/skills@{skill}` | Unknown | 자동 fetch 가능 (license 불명, prompt에 표시) |
| getsentry | 1 | `null` | Unknown | 수동 설치 안내 분기 (`//skill-manager`) |
| google-labs-code | 5 | `null` | Unknown | 수동 설치 안내 분기 |
| trailofbits | 1 | `null` | Unknown | 수동 설치 안내 분기 |
| **합계** | **31** | 24 형식 명시 / 7 null | - | - |

## 알려진 미해결 / 후속 분리

| ID | 내용 | 분리 대상 |
|----|------|----------|
| **`//skill-manager` 매칭 결함** | `match "//skill-manager"` → `found: false`. 142 워커가 SKILL.md를 변경하면서 alias/trigger 영향 가능. 별도 추가작업 또는 P1 태스크에서 alias 추가/매칭 로직 확인 | 별도 태스크 (143+) |
| **null source_repo 7건** | getsentry / google-labs-code / trailofbits 7개 스킬은 `npx skills find`로 정확한 owner/repo 검증 불가. 사용자가 //skill-manager로 수동 검색·설치. 추후 vercel-labs/skills 카탈로그가 보강되면 자동 fetch로 승급 | 외부 의존 — 모니터링 |
| **Windows 회귀 검증** | push 후 캡틴 Windows 환경에서 install.ps1 재실행 + match 동작 확인. Step 11 검증 명령(워커 자체 보완 포함) 사용 | push 후 별도 추가작업 |
| **141 후속 (Warning C-1)** | ARCHITECTURE.md §에이전트 GC 체커 별도 서브섹션 분리 | P1 README 보강 |

## 검증 상태

- source community-skills-registry.json: `$schema: opal-community-skills-registry-v2`, source_repo 31, paths 0 ✅
- source skill-registry.js: `validate` v2 인식 + communitySchema 출력 + paths 부재 → v1 마이그레이션 권장 warning ✅
- ~/.opal/community-skills/ (deployed): 보존 (D-4 정합) ✅
- bash -n install-mac.sh: SYNTAX_OK ✅
- mac 회귀: 캡틴 직접 검증 통과 ✅
- 변경이력 4파일: 모두 행 추가 + 일시 + 태스크 번호(142) ✅

## STATE 최종

| Phase | 행 수 | 상태 |
|-------|------|------|
| TASK | 1~3 | ✅ (사용자 확인 owner=user) |
| PLAN | 4~11 | ✅ (사용자 확인 owner=user) |
| EXECUTE | 12~18 | ✅ (사용자 확인 owner=user, mac 회귀 검증 통과) |
| CLOSE | 19~20 | 진행 중 (DONE.md 생성 → State Gate) |

## 후속 액션

1. **즉시**: 캡틴 명시 시 commit + push (옵션 2 흐름 마무리)
2. **push 후**: Windows 환경에서 install.ps1 재실행 + 회귀 검증
3. **별도 태스크**: `//skill-manager` 매칭 결함 fix
4. **장기**: P1 (Quick Start / mini-glossary / opal-cli 표 / 트러블슈팅 강화 / 141 Warning C-1) — 별도 세션
