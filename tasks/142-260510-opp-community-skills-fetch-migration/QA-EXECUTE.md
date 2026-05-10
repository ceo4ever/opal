# QA: EXECUTE — community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills)

> 검토일: 2026-05-10 | 판정: Pass (with Info)

## 1. 요약

OPAL repo의 `community-skills/` 번들을 완전 제거하고 vercel-labs/skills(`npx skills`) 온디맨드 fetch 방식으로 전환하는 구조 변경 태스크(142)의 정적 EXECUTE QA다. 검증 범위는 8개 변경 파일 + git rm 산출물이며, Step 10/11(mac/Windows install 회귀)은 캡틴 환경 실행 대기 상태로 정적 검증만 수행한다. R-1~R-7 모든 정적 검증 항목 통과. 변경이력 4개 파일 완비. Warning 1건(C-1 Windows Step 11 비대칭) — 정적 검증 범위 내 Info 수준.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | community-skills 폴더 제거 | Pass | 저장소 루트 디렉토리 부재 확인. git status: 553개 파일 D(staged delete). `ls community-skills` → No such file. |
| R-2-mac | install-mac.sh community-skills 분기 제거 | Pass | `bash -n install-mac.sh` SYNTAX_OK. `clean_dirs` 배열에서 community-skills 제거 확인 (L733). `install_opal_community_skills` 함수·호출부 0건. 사용자 데이터 보존 코멘트 L732. |
| R-2-mac-d4 | clean_dirs에 community-skills 미포함 (D-4 정합) | Pass | `clean_dirs=("skills" "agents" "references" "templates" "tools")` — community-skills 없음 확인. `~/.opal/community-skills/` 파괴 없음. |
| R-2-win | windows.ps1 community-skills 분기 제거 | Pass | `cleanDirs` 배열에서 community-skills 제거 확인 (L414). 복사 블록 0건. `.SYNOPSIS` 표현 갱신 (L395). 종료 안내 L1321 존재. |
| R-2-win-d4 | cleanDirs에 community-skills 미포함 (D-4 정합) | Pass | `@('skills', 'agents', 'references', 'templates', 'tools')` — community-skills 없음 확인. |
| R-3 | community-skills-registry.json 스키마 v2 | Pass | `$schema: "opal-community-skills-registry-v2"`, `version: "2.0.0"`. 전체 31개 항목에 `name`/`triggers`/`source_repo`/`license` 필드 완비. `paths` 필드 0건. |
| R-3-dist | 그룹별 source_repo/license 분포 | Pass | anthropics 18(Apache-2.0, non-null), openai 1(Apache-2.0, non-null), vercel-labs 5(Unknown, non-null). getsentry 1 + trailofbits 1 + google-labs-code 5 = 7건 null/Unknown. PLAN P-3/P-4 설계 정합. |
| R-4 | skill-registry.js v2 스키마 지원 + 변경이력 신설 | Pass | v1.0 헤더 신설(L12-17). `getCommunitySkillPath` + `isCommunitySkill` 헬퍼 추가. `matchCommand` 응답에 `installed`/`source_repo`/`license`/`install_command` 4필드 추가. 미설치 시 `path: null`. |
| R-4-validate | skill-registry.js validate() v2 인식 + paths 폴백 | Pass | v2 스키마에서 paths 부재 정상 처리. source_repo null → warning. v1 스키마 시 paths 필수 에러. 코드 분기 확인 (L266-290). |
| R-4-match | match "//pdf" 응답 구조 확인 | Pass | `installed`/`source_repo`/`license`/`install_command` 4필드 응답 확인. 미설치 시 `path: null` 동작. (참고: 테스트 환경에서 deployed v1 레지스트리 로드 → source_repo:null 응답. 소스 파일 자체는 v2 정합. install 재실행 후 해소 예정.) |
| R-5 | opal-skill-manager v1.1 번들 표현 제거 + fetch 흐름 | Pass | "기본 번들" 표현 본문 0건 (변경이력 행 언급만 존재). §6 자동 fetch 흐름(D-1) 추가. 변경이력 v1.1 완비. |
| R-6 | README L39 + L732 갱신 | Pass | L39: `skills.sh` 카탈로그 + `//skill-manager` 표현으로 갱신. L732: "사용자 fetch 시 채워짐 (skills.sh 카탈로그)" 표현. "30개 / 6개 조직" 0건. |
| R-7 | ARCHITECTURE.md §커뮤니티 스킬 + §배포 모델 갱신 | Pass | Global Layer 표 L66: fetch 방식 재서술. §커뮤니티 스킬 표(L156-167): SSOT/설치명령/위치/레지스트리/라이선스 5행 완비. §배포 모델 다이어그램: community-skills 배포 라인 0건 + fetch 안내 라인(L211) 추가. 디렉토리 구조 트리: 저장소 루트 community-skills/ 행 0건. |
| Step-9 | PROJECT.md §폴더 구조맵 community-skills/ 행 제거 | Pass | `community-skills/` 행 0건 확인. |
| CL-1 | 변경이력 4파일 완비 | Pass | install-mac.sh v2.0 (2026-05-10 17:00 KST, 142). windows.ps1 v1.6.0 (2026-05-10 17:00, 142). skill-registry.js v1.0 (2026-05-10 17:00 KST, 142). opal-skill-manager v1.1 (2026-05-10 17:00 KST, 142). |
| C-1 | Windows Step 11 비대칭 보완 | Info | PLAN Step 11(Windows 검증)에 `match "//pdf" → installed:false` 항목 미포함. Mac Step 10에는 포함. 비대칭이나 Windows 회귀가 캡틴 환경 대기 상태이므로 CLOSE 전 캡틴이 추가 검증 가능. 차단 요인 아님. |
| GE-1 | PLAN §3 체크리스트 완료율 | Pass | Step 1~9: 모두 [x]. Step 10~11: [ ] (캡틴 환경 대기 — 본 태스크 특성상 정적 검증 범위 외). |
| GE-2 | 산출물 존재 | Pass | 9개 파일 변경 확인 (registry.json, skill-registry.js, opal-skill-manager/SKILL.md, install-mac.sh, windows.ps1, README.md, ARCHITECTURE.md, PROJECT.md) + community-skills/ git rm. |
| GE-3 | TASK R-1~R-8 충족 | Pass | R-1~R-7 정적 검증 완료. R-8(회귀)는 캡틴 환경 실행 대기. |

## 3. 지적 사항

### Info: C-1 — Windows Step 11 match 테스트 비대칭

- **항목**: PLAN Step 11(Windows 회귀 검증) 4개 항목 중 `match "//pdf" → installed:false` 테스트 미포함
- **현황**: Mac Step 10에는 6번 항목으로 포함됨. Windows는 미포함.
- **영향**: 정적 검증 범위 내에서는 차단 없음. CLOSE 전 캡틴이 Windows 환경 회귀 시 `node skill-registry.js match "//pdf"` 추가 검증 권장.
- **심각도**: Info — 진행에 영향 없음.

### Info: 배포 전 deployed registry v1 잔존

- **항목**: `~/.opal/references/community-skills-registry.json`이 v1(설치된 버전). install 재실행 전까지 skill-registry.js가 배포된 v1을 우선 로드.
- **현황**: 소스(`opal/core/references/`)는 v2 정합. install 재실행(Step 10/11) 후 자동 해소.
- **영향**: 개발 환경 직접 실행 시 source_repo:null 응답. 사용자 환경에선 install 재실행 후 정상.
- **심각도**: Info — 예상된 상태. 진행에 영향 없음.

### Info: PLAN Step 1 "항목 수 = 30" vs 실측 31

- **항목**: PLAN.md Step 1 완료 기준에 "항목 수 = 30 (변경 없음)"으로 기재. 실제 레지스트리(v1/v2 모두) 31개.
- **현황**: TASK.md 배경에 "30개 SKILL.md"로 기재되어 있으나 실측은 31개. anthropics 18(+1 template 포함 등). v2 전환 후에도 31개 유지.
- **영향**: 문서 카운트 불일치. 기능적 영향 없음.
- **심각도**: Info — 문서 정확도 보완 권장.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | community-skills/ 폴더 삭제 AC | Pass |
| TASK.md R-2 | install 스크립트 community-skills 제거 AC | Pass |
| TASK.md R-3 | registry JSON 스키마 v2 전환 AC | Pass |
| TASK.md R-4 | skill-registry.js 미설치 감지 + fetch 정보 노출 AC | Pass |
| TASK.md R-5 | opal-skill-manager "번들" 표현 제거 AC | Pass |
| TASK.md R-6 | README L39 + L732 갱신 AC | Pass |
| TASK.md R-7 | ARCHITECTURE.md §커뮤니티 스킬 + §배포 모델 갱신 AC | Pass |
| TASK.md D-4 | 기존 사용자 데이터 보존 — clean_dirs에서 community-skills 제거 | Pass |
| PLAN.md P-3 | source_repo 포맷 `{owner}/{repo}@{skill}` | Pass |
| PLAN.md P-4 | license SPDX 또는 Unknown | Pass |
| PLAN.md P-5 | matchCommand 응답 4필드 신설 | Pass |
| PLAN.md P-9 | skill-registry.js 변경이력 헤더 신설 | Pass |
| CONVENTIONS.md §변경이력 | 4개 파일 변경이력 행 + 일시(KST) + 태스크 번호(142) | Pass |
| PLAN.md §3 실행 체크리스트 | Step 1~9 [x], Step 10~11 [ ] (캡틴 환경 대기) | Pass |
| PLAN.md §4 QA 체크리스트 | 4.1 기능(8/10항 Pass), 4.2 일관성(6/6 Pass), 4.3 문서(6/6 Pass) | Pass |

## 5. 판정

**Pass (with Info)**

R-1~R-7 모든 정적 검증 항목 통과. 변경이력 4개 파일(install-mac.sh v2.0 / windows.ps1 v1.6.0 / skill-registry.js v1.0 / opal-skill-manager v1.1) 모두 일시(KST) + 태스크 번호(142) 완비. D-4(사용자 데이터 보존) mac/Windows 양 OS 동등 처리 확인. Critical/Warning 0건. Info 3건(C-1 Windows Step 11 비대칭, deployed v1 잔존, 항목 수 카운트 불일치) — 모두 진행 차단 없음. Step 10/11(캡틴 환경 회귀)은 본 QA 범위 외이며 CLOSE 진입 전 캡틴 수행 예정.
