# DONE: opal-start 스킬을 opal-next로 개명

> 완료일: 2026-06-21 | 적용 스킬: opds | 모드: agentic | 태스크: 030

## 요약

재진입 가이드 스킬 `opal-start`(`//start`)를 **`opal-next`(`//next`)**로 개명했다. 이름이 기능("현재 상태 진단 → 다음 액션 안내")과 어긋나 `//opi`·`//onboarding`과 혼동되던 문제를 해소하고, 곧 만들 `//help`(능력 카탈로그)와 역할 경계를 명확히 했다. **기능·진단 로직·라우팅 분기는 완전 불변**인 순수 rename + 참조 정합 작업이다. `//start` alias·트리거는 완전 제거(하위호환 미유지)했다.

## 변경 파일 (7개 지점)

| 파일 | 변경 |
|------|------|
| `opal/skills/opal-start/` → `opal/skills/opal-next/` | git mv 폴더 rename (이력 보존) |
| `opal/skills/opal-next/SKILL.md` | name·triggers·제목·references 경로·진단 표 헤더·변경이력(v2.0.0) |
| `opal/skills/opal-next/references/start-flow.md` → `next-flow.md` | git mv + 내용(`//start`→`//next`)·제목·변경이력 |
| `opal/core/references/opal-skills-registry.json` | opal 그룹 항목(name/alias/triggers/paths/description) + version 3.5.0→3.6.0 + changelog 030 |
| `opal/skills/opal-onboarding/SKILL.md` | L176 `//start`→`//next` (L265 사료 불변) |
| `README.md` | L125 `//start`→`//next` (설명 유지) |

## 검증 결과 (TEST All Pass)

| 항목 | 결과 |
|------|------|
| `//next` 매칭 | found:true → opal-next ✅ |
| `//start` 매칭 | found:false (죽은 alias 제거) ✅ |
| 레지스트리 정합 | unregistered:0 (폴더↔레지스트리 일치) ✅ |
| 단위 테스트 | 5/5 PASS (`tests/test-validate.js` 직접 지정) ✅ |
| 회귀 | //opds·//opbr·//opi 정상, 형제 항목 비훼손 ✅ |
| 사료 보존 | onboarding L265·tasks/029 불변 ✅ |

> **validate exit 1 정체**(개명 결함 아님): ① `opal-next` dangling = 재배포 전 예상(paths가 배포본 경로, 재배포 시 해소) ② pre-existing 4건(`opal-pilot-data-design`·`op-data-*`) = 태스크 019 스킬의 배포 드리프트, 개명 무관·범위 밖.

## PM 강화검토 발견 (agentic)

- PLAN 워커의 TEST-SCENARIO "validate exit 0" 기대가 baseline 미확인 오류 → 검증 기준을 `unregistered:0`+활성 잔존 0 중심으로 보정(AGENTIC-LOG #4·#5).
- 워커 "단위테스트 5 PASS" 보고는 `--test tests/`(디렉토리) 시 MODULE_NOT_FOUND였고, 파일 직접 지정 시 실제 5 PASS.
- 트리거 재설계 승인: `//start`·"시작"·"처음부터" 제거 / "어디서부터 시작"·"다음에 뭐 해야"·"온보딩 다시 보고싶어" 유지.

## 후속 작업

- [ ] **install 재배포** (`bash scripts/install-mac.sh`) — opal-next 실동작 + pre-existing dangling 4건 + 직전 model 변경(opal-be/task-agent) 일괄 반영. **재배포 전엔 `//next`가 런타임에서 동작하지 않음**.
- [ ] **커밋** (캡틴 확인 후) — model 변경 2건 + 본 개명 7지점.
- [ ] (별건) pre-existing dangling 4건은 데이터 설계 스킬의 배포 드리프트 — 재배포로 해소되는지 확인.
