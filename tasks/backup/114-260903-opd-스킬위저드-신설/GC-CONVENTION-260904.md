# GC CONVENTION REPORT — 2026-09-04

## 1. 헤더

- 실행 일시: 완료 2026-09-04 (opal-convention-checker 워커 실행)
- 범위: `changed` / 대상 파일 6개 (신규 2 + 수정 4)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` (존재 — v1.8.0, 유일 기준으로 적용. 프레임워크 내장 공통 컨벤션 기본값 미적용)
- APPLY 수행 여부: N (진단 전담 — 파일 미수정)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 1 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 3 |
| 파일별 상위 | `opal/tools/skill-registry/skill-registry.js` (1건) / `opal/skills/opal-skill-wizard/SKILL.md` (1건) / `docs/ARCHITECTURE.md` (1건) |
| 카테고리별 빈도 | 문서화(변경이력) 2건 / 네이밍·포맷 1건 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 트리거 미달 — 각 이슈가 서로 다른 근본원인이며 동일 fingerprint 3파일 이상 미발생) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [`opal/tools/skill-registry/skill-registry.js`:1-16] `.js` 코드 파일 대폭 수정(+102/-2, 신규 함수 4개 + `matchCommand`/`getCommand`/`validate` 3개 분기 추가)에도 파일 상단 `@header` 블록의 "변경이력:" 라인이 갱신되지 않음 — 최신 항목이 여전히 태스크 105의 `v1.4 2026-09-03 00:45 KST`이며 태스크 114 관련 신규 버전 행(예: `v1.5`)이 없음
  - 카테고리: 문서화 / 변경이력
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §구현 규칙 §@header 규칙, "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다")
  - 설명: `docs/CONVENTIONS.md`는 스킬·에이전트·참조 문서는 "## 변경이력" 표로, 코드 파일(`.js` 등)은 파일 상단 @header 내 "변경이력:" 라인으로 갱신 의무를 명시한다. 이번 태스크에서 `skill-registry.js`에 `isProjectSkill`·`findProjectRoot`·`loadProjectRegistry`·`resolveProjectSkillPath` 4개 함수가 신설되고 `matchCommand()`/`getCommand()`/`validate()`에 project 분기가 추가됐으나(태스크 114 F-001), 헤더의 변경이력 라인에는 이 변경이 전혀 기록되지 않았다. 같은 태스크에서 나머지 4개 문서(`skill-commands.md` v1.4, `docs/ARCHITECTURE.md` 변경이력 행, wizard `SKILL.md` v1.0, `opal-skills-registry.json` changelog)는 모두 정상적으로 갱신됐다는 점에서, 이 파일만 누락된 것으로 판단된다.
  - 해결 방안: 헤더 "변경이력:" 블록에 `v1.5 2026-09-04 KST: 프로젝트 스코프 registry 4번째 병합 소스 추가 — isProjectSkill/findProjectRoot/loadProjectRegistry/resolveProjectSkillPath 신설, loadAllSkills() 4번째 병합, matchCommand() project 분기, getCommand() resolved_path 추가, validate() project 분기 (114)` 형태의 행을 최상단에 추가한다.
  - 자동 수정: N (내용 요약 판단 필요)
  - 참조: `docs/CONVENTIONS.md` §구현 규칙 §@header 규칙 (근거: `opal/core/references/harness/header-rules.md`)

### Low (1건)

- [ ] GC-C002 [`opal/skills/opal-skill-wizard/SKILL.md`:13] frontmatter `version: "1.0"`이 `docs/CONVENTIONS.md`가 규정하는 `version: {X.Y.Z}`(semver, 예 `1.0.0`) 형식과 불일치
  - 카테고리: 네이밍/포맷 (YAML frontmatter)
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §파일 구조 §YAML Frontmatter, `version: {X.Y.Z}     # 스킬만`)
  - 설명: CONVENTIONS.md는 스킬 frontmatter의 `version`을 semver(X.Y.Z) 형식으로 규정하나, 신설된 `opal-skill-wizard`는 2-세그먼트("1.0")를 사용한다. 다만 실측상 `opal-brain`(`version: "2.0"`)·`opal-improve`(`version: "1.0"`)·`opal-eli5`(`version: 1.0`) 등 최근 신설 스킬 다수가 동일한 2-세그먼트 패턴을 이미 사용하고 있어, 이번 태스크에서 새로 도입된 이탈이 아니라 기존 관행을 그대로 따른 것이다. 심각도를 Low로 제한하는 근거이며, 위반 자체는 성립한다.
  - 해결 방안: `version: "1.0.0"`으로 교정하거나, 다수 기존 스킬의 실제 관행에 맞춰 `docs/CONVENTIONS.md` §YAML Frontmatter의 `version` 표기 규칙을 "MAJOR.MINOR 허용" 등으로 갱신하는 쪽을 캡틴이 선택.
  - 자동 수정: Y (단순 문자열 치환, 단 CONVENTIONS.md 쪽 개정 여부는 소유자 판단 필요)
  - 참조: `docs/CONVENTIONS.md` §파일 구조 §YAML Frontmatter

### Info (1건)

- [ ] GC-C003 [`docs/ARCHITECTURE.md`:519] 이번 태스크가 추가한 변경이력 신규 행이 시각(HH:mm) 없이 날짜만 기재되어 있고, 표 자체도 `docs/CONVENTIONS.md`가 규정하는 "버전 | 일시 | 변경내용" 3열이 아니라 "날짜 | 변경 내용" 2열(버전 컬럼 없음) 구조
  - 카테고리: 문서화 / 변경이력
  - 위반 기준: 프로젝트(`docs/CONVENTIONS.md` §파일 구조 §변경이력, "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)" + "버전 | 일시 | 변경내용" 3열 표)
  - 설명: 실측 결과 `docs/ARCHITECTURE.md`의 "## 변경이력" 표는 파일 신설 이래(2026-06-18 이전부터) 계속 "날짜 | 변경 내용" 2열·시각 생략 다수 형태를 사용해 왔다(예: 528행 "2026-08-10", 530행 "2026-08-07" 등 시각 없는 행 다수, 버전 컬럼은 전 이력에 걸쳐 부재). 이번 태스크가 추가한 519행은 이 문서의 기존 관행과 완전히 동일한 형식이며, 이번 태스크가 새로 도입한 이탈이 아니다. Critical/High 판단 대상이 아니며 PM Gate 통과에 영향 없음 — 참고 목적으로만 기록한다.
  - 해결 방안: (선택) 문서 전체 변경이력 표를 CONVENTIONS.md 표준 3열로 일괄 이관하거나, `docs/ARCHITECTURE.md`가 표준과 다른 자체 변경이력 표기를 쓴다는 예외를 CONVENTIONS.md에 명문화. 이번 태스크 범위에서 조치 불요.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §파일 구조 §변경이력

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 (빈도 트리거: 동일 fingerprint 3개 이상 파일 조건 미충족 — 3건 모두 서로 다른 근본원인·파일 1건씩. 새 카테고리 트리거: 없음 — 전 이슈가 CONVENTIONS.md 기존 절 안에서 판정됨).

참고(비트리거, 정보용): `docs/CONVENTIONS.md` §배포 경계는 커뮤니티 스킬 레지스트리를 "이원 경계"(프레임워크 카탈로그 + 사용자 등록분)로만 서술한다. 이번 태스크가 도입한 `opal-skill-wizard`는 `docs/ARCHITECTURE.md`에 "스코프 3원"(+ 프로젝트 스코프 `{project}/.opal/skills-registry.json`)으로 이미 반영됐으나, `docs/CONVENTIONS.md` §배포 경계 원문은 대상 파일 범위 밖이라 이번 검사에서 갱신 여부를 판정하지 않았다. 캡틴 참고용으로만 남긴다(위반 판정 아님, 대상 파일 아님).

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.

---

## 부록: CONVENTIONS.md 조항 없어 판정 보류한 항목

| 확인 요청 항목 | 판정 |
|---------------|------|
| Citation(§3) — 문서 산출물 인용 형식 | 판정 보류 아님, **해당 없음**. `docs/CONVENTIONS.md` §Citation Rules는 "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물"에 한정 적용되며, 이번 대상 파일(SKILL.md·js·참조문서·registry) 중 이 범주에 속하는 파일이 없다. |
| 들여쓰기·탭/스페이스 혼용 | 판정 보류. `docs/CONVENTIONS.md`에 들여쓰기 규칙 절 자체가 없다(base-convention-checklist 카테고리 2에 해당하나 프로젝트 문서 미규정) — 지적하지 않음. |
| 테스트 케이스 명명 규칙(`[T114/L2-NNN]`) | 판정 보류. `docs/CONVENTIONS.md`에 테스트 케이스 명명 규칙 조항이 없다(테스트 파일명 자체는 kebab-case로 기존 파일과 정합 확인함). |
| 커밋 메시지 형식·단위 | 해당 없음 — 오케스트레이터 지시대로 커밋 미수행 상태이므로 판정 제외(캡틴 권한 영역). |

---

## 배포 경계 / 플랫폼 분기 확인 결과 (참고 — 위반 없음)

- 배포 경계: 대상 6개 파일 모두 프로젝트 소스(`opal/`, `docs/`) 내에서만 수정·생성됐으며 `~/.opal/` 배포 경로 직접 편집 없음 확인 (`docs/CONVENTIONS.md` §배포 경계 준수).
- 플랫폼 분기: `opal-skill-wizard/SKILL.md` §9가 "Claude/Cursor/Gemini 등 플랫폼별 분기는 어댑터 계층 책임이며 이 문서에 두지 않는다"를 [MUST]로 명시하고 있고, 실제 diff에서도 Claude/Cursor/Gemini/codex 하드코딩 분기가 발견되지 않음 (`docs/CONVENTIONS.md` §플랫폼 분기 격리 준수).
- 변경이력 작성 의무(4문서): `skill-commands.md`(v1.3→v1.4), `docs/ARCHITECTURE.md`(변경이력 행 추가), `opal-skill-wizard/SKILL.md`(v1.0 최초 작성), `opal-skills-registry.json`(changelog 배열 3.14.0 항목)까지 4건 모두 정상 이행 확인. 코드 파일(`skill-registry.js`)만 헤더 변경이력 라인 누락 — 위 GC-C001 참조.
