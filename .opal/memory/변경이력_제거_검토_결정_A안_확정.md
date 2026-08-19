# 변경이력 제거 검토 결정 — A안 확정

> 등록일시: 2026-08-14 16:49 KST
> 태스크: (미개시 — `//opd` 태스크 개시 예정)
> 결정자: 캡틴 (2026-08-14 검토 대화)

## 결정 내용

프레임워크 내부 문서의 `## 변경이력` 표와 버전 표기를 제거한다 (A안 = 프레임워크 md 한정).

| 구분 | 대상 | 규모 |
|------|------|------|
| 제거 | 프레임워크 md의 `## 변경이력` 표 | 137파일 / 1,849행 (해당 문서 총량의 5.3%) |
| 제거 | 문서 상단 인용주 버전 표기 (`> 작성일 … \| 버전: v2.0`) | 3건 |
| 제거 | frontmatter `version:` 필드 | 19건 |
| **유지** | 코드 `@header`의 `변경이력:` 필드 + `header-standard.md` 규정 | 코드 축은 불변 |
| **유지** | 산출물 템플릿 버전 (`op-sdd-*`, `opal-pilot-sdd`의 SPEC 버전) | PLAN·VERIFY가 대조 근거로 소비 |
| **유지** | `opal-doc-standard.md` §3 정책서 필수 구성요소 행 | 산출물 축 |

## 결정 근거

**추적성은 이미 3중으로 대체됨** — git 커밋이 태스크 번호를 포함하고(`feat(091):` 형태),
`DONE.md` + `.opal/MEMORY.json` 히스토리 + `.opal/brain/`이 변경 맥락을 더 깊게 보관한다.
변경이력 표는 이 정보의 네 번째 사본이며 유일하게 수기 갱신 의무가 붙어 있다.

**런타임 토큰 이익은 0** — `scripts/install-mac.sh:222` `strip_deploy_md`가 배포 시 이미 제거하므로
이 작업은 순수 소스 위생이다. "토큰 경감"을 명분으로 삼으면 오판이다
(기존 교훈: `.opal/brain/pages/concept/strip-deploy-runtime-token-neutral.md`).

**실질 이익은 갱신 의무와 그 부작용 소멸** — 동시 태스크가 같은 문서 버전을 선점하는 충돌이
실제 발생했다(079 vs 077, `v2.7` 중복 → TS-030 오탐. 교훈:
`.opal/brain/pages/concept/literal-version-test-expectation-fragility.md`).

**규칙이 이미 78% 미준수** — 변경이력 보유 126건 중 버전 표기를 동반한 건 28건(22%)뿐이다.
버전 채번의 SSOT가 변경이력 표이므로, 표만 지우고 필드를 남기면 워커가 근거 없이 임의 증가시킨다.

## 동반 개정 필수 지점 (생성·검증 측)

표만 지우면 재생성되거나 반대로 위반 판정이 난다.

| 축 | 지점 | 내용 |
|----|------|------|
| 검증 | `opal/skills/opal-pilot-gc/references/base-convention-checklist.md:69` | "변경이력 섹션 누락"을 **위반으로 감지** — 미제거 시 137개 문서가 전부 지적 대상 (최우선) |
| 생성 | `opal/skills/opal-skill-creator/SKILL.md:162-175, 202` | 신규 모드 표 삽입 + 개선 모드 Major/Minor 채번 + 완료 체크리스트 |
| 생성 | `opal/skills/opal-agent-creator/SKILL.md:143-150, 179, 189, 196` | §2-4 버전 태깅 + 에이전트 문서 템플릿 자체에 `## 변경이력` 포함 |
| 생성 | `opal/core/references/opal-doc-standard.md` §6-3, §7 | 두 creator가 참조하는 상위 규칙 SSOT |
| 규범 | `.opal/AGENT.md:24, 43, 62` | PM 검토기준 · 업무지침 · 금지사항 3중 강제 |
| 규범 | `docs/CONVENTIONS.md:126-130, 215, 240-244` | 형식 규정 + @header 절 언급 + 「변경이력 작성 의무」 절 |
| 게이트 | `opal/skills/op-dev-plan/references/plan-guide.md:405` | PLAN 산출물 체크리스트 행 |
| 배포 | `scripts/install-mac.sh:217-231, 1570` | `strip_deploy_md` — **잔존 누출 안전망으로 유지 권고**, 존폐는 PLAN에서 확정 |

## 부수 관찰

- 헤딩 형식 6종 편차: `## 변경이력`(135) / `### 변경이력`(3) / `## Changelog`(1) / `## 8. 변경이력`(1) 등.
  strip은 `^## 변경이력$`만 잡으므로 배포본에 8건이 새어 나가고 있다 — 제거로 함께 소멸한다.
- frontmatter `version:`은 소비자가 없다: `skill-registry.js`에 `version` 참조 0건,
  `install-mac.sh` 미사용, `opal-skills-registry.json`에는 registry 자체 버전만 있고 스킬별 필드가 없다.

## 상태

범위 확정 완료 · `//opd` 태스크 개시 대기 (캡틴 "진행" 승인 시)
