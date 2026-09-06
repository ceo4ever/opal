# GC 컨벤션 체크 보고서

## §1 헤더

- 실행 일시: 2026-09-06 (KST)
- 범위: `docs/CONVENTIONS.md` (기준), 코드 루트 `.opal-worktrees/task_107`(브랜치 `feat/OP-TASK-107`), 변경 파일 49건 전수
- 기준 문서 상태: `docs/CONVENTIONS.md`(워크트리 사본, 개정 후) 단일 진입점 — 허브+링크 모델 미적용(단일 문서 프로젝트, §참고 절 명시). 병행 참조: `opal/core/references/header-standard.md`(§2, §2.1 원문 소유), `opal/core/references/harness/header-rules.md`(집행 절차)

## §2 요약 지표

**Critical 0 / High 1 / Medium 1 / Low 1 / Info 0**

| 심각도 | 건수 |
|--------|------|
| Critical | 0 |
| High | 1 |
| Medium | 1 |
| Low | 1 |
| Info | 0 |

## §3 수정 대상

### [High] GC-C001 — `header_history` 감지기가 "이름 불문" 원칙을 구현하지 않음 (changelog 필드만 검사)

- **파일:라인**: `opal/tools/code-scan/code-scan.js:3328-3338` (신규 코드 블록)
- **위반 절**: `opal/core/references/header-standard.md` §2 — "위 표에 정의된 필드 외의 필드를 `@header`에 신설하지 않는다. 특히 **이력 전용 필드**... **를 두지 않는다. 이름을 불문한다(예: `changelog`·`history`·`revisions`).**"
- **선존 여부**: **신규(이번 태스크 도입)**. `git show HEAD:opal/tools/code-scan/code-scan.js`에 `countTaskTags`/`header_history` 관련 코드가 전혀 없음을 확인 — 이번 태스크가 처음 작성한 감지기다.
- **설명**: 이번 태스크는 header-standard.md §2에 "이력 전용 필드는 이름 불문 금지(`changelog`·`history`·`revisions` 등)" 원칙을 명문화하면서, 이를 자동 관측할 `code-scan validate`의 `header_history` 비차단 경고를 구현했다(문서 §@header 규칙 "Task 107" 각주가 이 감지기를 지목). 그러나 실제 구현(`code-scan.js:3325-3338`)은
  ```js
  const cl = resolved.changelog;
  const clEmpty = cl === undefined || cl === null
    || (Array.isArray(cl) && cl.length === 0)
    || (typeof cl === 'string' && cl.trim() === '');
  if (!clEmpty) { ... violations.push({ code: 'header_history', sub: 'changelog', ... }); }
  ```
  로, 필드명 `changelog` 하나만 리터럴 검사한다. 문서가 예시로 든 `history`·`revisions` 등 **다른 이름의 이력 필드는 이 감지기를 전혀 통과하지 못하고(=경고 없이) 조용히 누락**된다. 즉 문서가 스스로 규정한 "이름을 불문한다"는 원칙에 대해, 구현은 이름 1종만 커버하는 자기 위반 상태다.
  - 참고로 `description`/`note` 필드의 이력 누적(태스크 번호 2개 이상 인용)은 `countTaskTags`로 별도 검사되므로 그쪽은 이름 불문 문제와 무관하다(정상).
- **근거 인용**: `header-standard.md:33`("이름을 불문한다(예: changelog·history·revisions)") vs `code-scan.js:3328`(`resolved.changelog`만 참조).
- **테스트 커버리지 확인**: `opal/tools/code-scan/tests/test-regression.js:963` 주석은 "107: test-header-history.js 신설"을 언급하나, 본 저장소의 diff 대상 테스트 파일(`test-feature.js`/`test-regression.js`/`test-shard-policy.js`/`test-shard.js`/`test-validate.js`) 어디에도 `history`/`revisions`라는 이름의 필드를 넣은 회귀 테스트가 없다 — `changelog` 외 이름에 대한 검증 공백이 테스트로도 확인된다.
- **수정 방안**: `resolved` 객체에서 header-standard.md §2 필드 화이트리스트(`module`/`layer`/`domain`/`description`/`exports`/`depends`/`note`/`feature`, 테스트 파일은 `task`/`scenarios` 추가 허용) **밖의 키를 전수 순회**하여 비어있지 않으면 `header_history`(`sub: 'unknown_field'` 등)로 잡는 방식으로 일반화한다.
- **auto_fixable**: false (감지 로직 재설계 필요)
- **참조 URL**: 참조: TBD — 프로젝트 내부 규칙(header-standard.md §2), 외부 표준 없음

### [Medium] GC-C002 — 비차단(exit 0) 경고이므로 실질 집행력 없음 (설계 의도상 위 High와 연계)

- **파일:라인**: `opal/core/references/harness/header-rules.md:107`("`code-scan validate`가 ... `header_history` **비차단 경고**를 낸다(exit code 불변)")
- **위반 절**: 해당 없음(문서 자체 설계 — 위반이 아니라 설계 특성). 다만 GC-C001과 결합 시 실효성 우려를 Medium으로 별도 표기한다.
- **선존 여부**: 신규(107 도입 설계) — 비차단 자체는 의도된 설계(경고만, exit 불변)이므로 "위반"은 아니다.
- **설명**: `header_history` 위반은 exit code에 영향을 주지 않는 비차단 경고로 설계되어 있다. GC-C001의 커버리지 공백(changelog 외 이름 누락)과 겹치면, "이름 불문 금지" 원칙이 사실상 `changelog`라는 이름을 쓴 경우에만, 그것도 경고 수준으로만 관측되는 이중 약화 상태가 된다. 정책 문서(header-standard.md §2)가 표방하는 강도와 실제 관측 강도 사이 괴리를 Medium으로 기록해둔다.
- **근거 인용**: `header-rules.md:107`, `code-scan.js:3529,3533,3537`(`header_history`를 `EXIT_BLOCKING_CODES`에서 제외)
- **auto_fixable**: false
- **참조 URL**: 참조: TBD — 내부 설계 문서

### [Low] GC-C003 — `docs/CONVENTIONS.md` 변경이력 표에 버전 `v1.6.0`이 두 행(238행대, 287행)에 중복 기재, 최신 v1.9.0 앞에 위치

- **파일:라인**: `docs/CONVENTIONS.md:278`(첫 v1.6.0), `docs/CONVENTIONS.md:287`(둘째 v1.6.0, 태스크 106), `docs/CONVENTIONS.md:288`(v1.9.0, 태스크 107)
- **위반 절**: `docs/CONVENTIONS.md` §변경이력 작성 의무 — "버전은 semver" (암묵적으로 단조 증가 기대), §변경이력 표 자체의 정합성
- **선존 여부**: 선존 결함(106에서 발생) + **이번 태스크가 알면서 재확인만 하고 정정하지 않음**(287행 자체 각주: "직전 행이 v1.8.0 뒤에 v1.6.0으로 기재된 것은 106의 버전 표기 오류이며 본 행은 실제 최신인 v1.8.0을 기준으로 채번했다"). 즉 107은 자신의 신규 행(v1.9.0)의 채번 근거만 정정했을 뿐, 106이 남긴 표기 오류(중복 버전 번호, 순서 역전) 자체는 그대로 두었다.
- **설명**: 변경이력 표가 자기완결적 참조로 기능하려면 버전 번호가 유일·단조 증가해야 하는데, `v1.6.0`이 두 번 등장(238행대 vs 287행)하고 그 사이에 v1.7.0/v1.8.0이 끼어 있어 표만 봐서는 어떤 v1.6.0이 최신인지 혼동을 준다. 107이 이 표에 새 행을 추가하는 시점에 106의 오기를 정정(예: 106 행을 v1.9.0으로 재채번하고 107을 v1.10.0으로)하지 않은 점을 근거 있는 지적으로 남긴다(107 자신이 문제를 인지하고 각주로 설명했다는 사실 자체가 근거).
- **auto_fixable**: false (버전 재채번은 소유자 판단 필요)
- **참조 URL**: 참조: TBD — semver.org (버전 단조성 일반 관례, CONVENTIONS.md 자체는 단조성을 명문화하지 않음 — 그래서 Low)

## §4 문서 업데이트 제안

- **[빈도 트리거]**: 미해당(N=3 기준 반복 fingerprint 없음 — 지적 3건이 서로 다른 근본 원인이며 동일 위반 패턴의 파일 간 반복이 아님)
- **[새 카테고리 트리거]**: 미해당(GC-C001~003 모두 기존 헤더/변경이력 절 하에서 다룰 수 있는 사안)
- **[심각도 트리거]**: High 1건(GC-C001) 발생 — §4에 분리 표기. header-standard.md §2에 "이름 불문" 명문화 시점(107)에 감지기 구현을 동시에 완결하지 못한 점은, 향후 §@header 규칙 절이나 header-rules.md에 "감지기 구현 완료"를 게이트 조건으로 명시하는 보완을 제안한다(문서 개정과 도구 구현의 동시성 담보 장치 부재).

## §5 문서 작성 유도

해당 없음 — `docs/CONVENTIONS.md` 존재.

---

지적 총 3건(High 1 / Medium 1 / Low 1), Critical 0, Info 0.
