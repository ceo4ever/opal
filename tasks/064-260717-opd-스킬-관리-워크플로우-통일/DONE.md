# DONE: 커뮤니티 스킬 관리 워크플로우 통일

> 완료일: 2026-07-17 | 적용 스킬: opd | 모드: agentic | 판정: **All Pass (S-1~S-10)**

## 요약

커뮤니티 스킬의 검색·설치·제거·업데이트를 **clone-copy 단일 방식**으로 통일하고, `//xxx` 미설치 분기의 라우팅↔절차를 정합시켰다. 설치 레이아웃 SSOT를 vendor 중첩으로 확정하고 flat 잔재 30건을 `migrate` 서브커맨드로 정규화했으며, 사용자 설치 등록분을 install 불가침 영역(`community-skills/user-registry.json`)으로 격리해 배포 덮어쓰기 소실 경로를 제거했다.

## 해소된 결함 (진단 D1~D4 + 검증 중 발견 2건)

| # | 결함 | 해소 |
|---|------|------|
| D1 | flat 설치본을 미설치로 오판 | `resolveCommunitySkillPath` 이중 탐지 + `migrate`(30건 이동·멱등·미등재 보존) |
| D2 | `//pdf 텍스트` 매칭 실패 | basename alias 매칭 + 충돌 시 ambiguous 후보 목록 |
| D3 | 미설치 분기 문서 이원화 | skill-commands v1.2 라우팅 유지 + §6 clone-copy 4분기 재작성(v1.4/v1.4.1) |
| D4 | `npx skills add` OPAL 디렉토리 설치 불가 | 설치 지시 전량 제거, npx는 find/check 전용 |
| 검증 발견 | `list --group=community` 항상 빈 배열 | `_source` 기반 필터 수정 |
| 검증 발견 | anthropics upstream `skills/{name}` 중첩 레이아웃 | 카탈로그 18건 `@skills/{name}` 정정 + §2 탐지 폴백 4단계 |

## 변경 파일

- `opal/tools/skill-registry/skill-registry.js` — resolve 이중 탐지·basename 매칭·user-registry 병합·migrate·parse-source-repo·match 출력 clone-copy (+265/-23)
- `opal/tools/skill-registry/tests/test-match.js`·`test-migrate.js` — 신규 RED-first 테스트 20케이스
- `opal/core/references/community-skills-registry.json` — schema_notes 이원 registry 규칙 + anthropics source_repo 18건 정정
- `opal/skills/opal-skill-manager/SKILL.md` — 4절차 재작성 + §6 4분기 + migrate 진입 훅 (v1.4/v1.4.1)
- `opal/core/references/harness/skill-commands.md` — clone-copy 명시·ambiguous 분기 (v1.3)
- `docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md`·`docs/architecture-diagram/opal_framework_architecture.html` — 설치 방식·이원 registry 경계 반영

## 검증 증거

- 자동 테스트 25/25 GREEN (RED→GREEN, 테스트 불변성 유지) + red-check 게이트 Pass
- S-9 실네트워크 E2E: 미설치→clone-copy→commit_sha(40hex)→user-registry→installed:true 전 구간 실증 (1차 Fail→fix→Pass)
- S-10 캡틴 실환경 확인: 자동 설치·즉시 실행 PASS + install 재실행 후 user-registry 잔존 PASS
- 실PC 정규화 실측: migrate 30건 이동·멱등·32/32 installed (modern-python 레거시 번들은 수동 정규화, 원본 보존)
- 컨벤션 진단 Critical/High 0 (Medium 2건은 PM 재검증으로 오탐 기각)

## 후속 항목

1. **커밋 + 배포 검증** — 캡틴 지시 대기 (배포는 이미 1회 수행·검증됨)
2. `trailofbits/modern-python` 카탈로그 `source_repo`/`license` 보강 (현재 null/Unknown — 업데이트 감지 불가)
3. 레거시 번들 폴더 `~/.opal/community-skills/modern-python/` 정리 여부 캡틴 판단
4. (별도 태스크 후보) 커뮤니티 스킬 내재화(bundled) 옵션 — 사전 논의만 존재

## 산출물

TASK.md / ANALYSIS.md / PLAN.md / TEST-SCENARIO.md / AGENTIC-LOG.md / GC-CONVENTION-260717.md / STATE.md
