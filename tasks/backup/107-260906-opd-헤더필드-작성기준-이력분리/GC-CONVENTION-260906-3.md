# GC 컨벤션 재진단 보고서 (3차)

**Critical 0 / High 0 / Medium 0 / Low 1 / Info 0**

## §1 헤더

- 실행 일시: 2026-09-06 (KST), 3차 재진단 — Step 6f 델타 한정
- 범위: Step 6f가 만진 2파일의 델타만 — `opal/tools/code-scan/code-scan.js`의 `MANIFEST_ONLY_HEADER_FIELDS` 상수(:75 부근) + 판정 루프 mode 게이트(`!isInlineMode && MANIFEST_ONLY_HEADER_FIELDS.has(key)) continue;`, `:3361` 부근), `opal/tools/code-scan/tests/test-header-history.js`의 TS-057(a)(b). 1차·2차가 훑은 49파일 전수 재검사는 하지 않음.
- 코드 루트: `.opal-worktrees/task_107` (브랜치 `feat/OP-TASK-107`).
- 기준 문서: `docs/CONVENTIONS.md`(단일 진입점, 워크트리 사본, 개정 후) + `opal/core/references/header-standard.md`(§2, §7.2 원문 소유) + `opal/core/references/harness/header-rules.md`(집행 절차). 프레임워크 내장 기본값 미적용.
- 1차 보고서(`GC-CONVENTION-260906.md`), 2차 보고서(`GC-CONVENTION-260906-2.md`)는 감사 기준선으로 보존, 수정하지 않음.

## §2 요약 지표

| 심각도 | 건수 |
|--------|------|
| Critical | 0 |
| High | 0 |
| Medium | 0 |
| Low | 1 |
| Info | 0 |

(내역: GC-C004 해소 확인 — 신규 위반 없음 / GC-C003 미해소 Low 1건 이월(변동 없음, 재확인만))

## §3 GC-C004 해소 재현 확인 (재판정 아닌 직접 재실행 결과)

`tests/fixtures/violations/draft` 픽스처(manifest 모드, `svc/mod/Draft.java`에 `draft:true`)를 대상으로 직접 실행:

```
$ cd opal/tools/code-scan/tests/fixtures/violations/draft
$ node <code-scan.js> validate --json
exit 2
{"counts":{"orphan":0,"uncovered":0,"conflict":0,"draft":1,"exports_not_found":0,
  "worker_scope_violation":0,"newly_uncovered":0,"pre_existing":0,
  "manifest_oversize":0,"header_history":0},
 "violations":[{"code":"draft","file":"svc/mod/Draft.java",...}],
 "headerSource":"manifest"}
```

`draft` 위반(의도된 기존 위반, counts.draft=1)은 그대로 남고, `header_history`/`undeclared_field` 오탐(2차 GC-C004가 지적한 것)은 counts.header_history=0으로 완전히 사라졌다. **GC-C004는 실제로 해소되었다** — "Step 6f가 했다니 됐다"는 진술이 아니라 직접 재현한 결과다.

전체 스위트: `node --test tests/*.js` → **369 / 369 pass, 0 fail** (PM 실측치와 일치). `--version` → `code-scan v1.6.0` (불변). 실 저장소 전수(`headerSource:"inline"`) → `header_history` **2건**, 전부 `('undeclared_field','track')` — `opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/tool-scan/tests/test_tool_scan.py`. `counts` 9키 불변. 모두 PM 실측과 정확히 일치한다.

## §4 mode 게이트 정밀도 판정 — 과잉/과소 검토

### 과소 (manifest 모드에서 `draft` 말고 오탐할 키가 더 있는가) — **없음, 직접 대조 확인**

`resolveHeader()`(code-scan.js:1533-1584)를 직접 읽어 `resolved` 객체에 실제로 주입되는 키를 전수 대조했다:

- `WORKER_FIELDS`(`code-scan.js:125`) = `['description', 'exports', 'depends', 'note', 'feature']` — `for (const field of WORKER_FIELDS)` 루프(:1563)로만 주입.
- `module`(:1568, `hasOwn(fe, 'module')`일 때만) / `layer`(:1569, layerMatch 존재 시) / `domain`(:1570, domainMatch 존재 시).
- `draft`(:1572, `hasOwn(fe, 'draft')`일 때만).
- `_source`(:1580) / `_sources`(:1581) — `_`-prefix로 판정 루프에서 이미 스킵(`key.startsWith('_')`, :3355).

이 8종(WORKER_FIELDS 5 + module/layer/domain 3) + draft + `_`-prefix 2종이 `resolved`에 실릴 수 있는 키의 전부다. `manifest.files[].{임의 필드}`를 아무리 추가해도 `resolveHeader`가 화이트리스트 방식으로만 복사하므로 `resolved`에 실리지 않는다 — 워커 보고 내용과 코드가 정확히 일치한다. **manifest 모드에서 `draft` 외에 추가로 예외 처리가 필요한 키는 없다.**

### 과잉 (`!isInlineMode` 조건 때문에 inline 모드에서 `draft`라는 이름의 필드가 여전히 탐지되는가) — **맞다, 그리고 이것이 옳은 판정이다(동의)**

`header-standard.md` §2 필드 정의 표(라인 15-23)에는 `draft`가 없다 — §2가 규정하는 것은 인라인 `@header`의 8필드(module/layer/domain/description/exports/depends/note/feature)뿐이다. `draft`는 §7.2가 정의한 **매니페스트 파일 엔트리 스키마 전용** 필드(`files[].draft | 선택 | boolean | description 공란이면 true | 도구 | 골격 미기입 마커`, header-standard.md §7.2)이며, resolveHeader()의 manifest 분기에서만 `hasOwn(fe, 'draft')` 조건으로 주입된다. inline 모드는 애초에 `extractHeader()`를 그대로 반환하므로(:1541) `fe`/`files[]` 개념 자체가 없고, 이 층위 구분과 무관하게 사용자가 인라인 `@header`에 임의로 `draft`라는 이름의 필드를 적으면 그것은 §2가 정의하지 않은 "미정의 필드"일 뿐이다. 따라서 mode 게이트가 inline에서 `draft`를 계속 탐지하는 것은 **과잉이 아니라 §2/§7.2 층위 분리를 정확히 반영한 것**이다. 동의한다.

### TS-057(b)의 대체 증명 타당성 — **타당, 우회 아님**

워커는 "manifest 엔트리에 §2 화이트리스트 밖 임의 필드(예: changelog)를 넣어도 `resolveHeader`가 화이트리스트 방식으로 복사하므로 `resolved`에 아예 실리지 않아, undeclared_field 판정 대상 자체가 될 수 없다"고 판단하고, 대신 inline 모드에 `draft`라는 이름을 넣어 mode 게이트가 실제로 작동하는지 증명했다. 이는 §4 "과소" 검토에서 직접 확인한 사실(resolveHeader가 화이트리스트로만 필드를 복사)과 일치한다 — manifest 모드에서 "진짜 미정의 필드가 resolved에 실려 undeclared_field로 잡히는" 시나리오는 이 코드 구조상 애초에 실행 불가능하므로, 이를 재현하는 테스트를 요구하는 것 자체가 불가능한 것을 요구하는 셈이다. TS-057(b)가 증명하는 것은 "mode 게이트 조건(`!isInlineMode`)이 값이 아니라 모드로 정확히 게이트되어 있다"는 다른 각도의 명제이며, 이것으로 mode 게이트의 정밀도를 검증하는 것은 타당한 대체다. 검증 공백의 우회가 아니라, 공백 자체가 코드 구조상 존재하지 않음을 (화이트리스트 주입 경로 직접 대조로) 확인했다.

## §5 상수 분리 근거 검토 — header-standard.md 원문 대조

코드 주석(code-scan.js:68-74)이 인용하는 문구를 §7.2 원문과 대조:

- 코드 주석: `"files[].draft | 선택 | boolean | description 공란이면 true | 도구 | 골격 미기입 마커"`
- header-standard.md §7.2 원문(표 마지막 행): `| files[].draft | 선택 | boolean | description 공란이면 true | 도구 | 골격 미기입 마커 |`

일치한다. §2 원문("다만 task·scenarios처럼... 이 금지의 대상이 아니다")과 `HEADER_FIELD_EXCEPTIONS` 주석도 1차·2차에서 이미 대조 확인된 바 변동 없음(재확인). `DECLARED_HEADER_FIELDS`(8필드)도 §2 표(라인 15-23)와 1:1 일치, 변동 없음. **layer 분리 근거 주석은 문서 원문과 정확히 일치한다.**

## §6 1차·2차 지적 최종 상태 정리

- **GC-C001**(1차 High, changelog 이름 하나만 검사) → **해소**(2차 확인, 3차 변동 없음).
- **GC-C002**(1차 Medium, 비차단 결합 약화) → **해소**(2차, GC-C001 해소로 전제 소멸).
- **GC-C003**(1차 Low, CONVENTIONS.md 변경이력 v1.6.0 중복 기재) → **미해소, 3차 이월**(재확인만, 조치 없음 — 진단자 권한 밖 이력 재작성이므로 정당한 이월).
- **GC-C004**(2차 High, `draft` 오탐) → **해소**(3차 직접 재현 확인 — §3 참조).

## §7 문서 업데이트 제안

- **[빈도 트리거]**: 미해당.
- **[새 카테고리 트리거]**: 미해당.
- **[심각도 트리거]**: 미해당 — 이번 차수 신규 Critical/High 없음. 1차·2차가 제안한 "문서 개정과 도구 구현 동시성 담보 장치" 제안은 여전히 유효하나(연쇄가 2차까지 이어졌던 사실), 3차에서 그 연쇄가 끊긴 것이 확인되었으므로 신규 제안은 추가하지 않는다.

## §8 문서 작성 유도

해당 없음 — `docs/CONVENTIONS.md` 존재.

---

**신규 지적 0건.** 3차의 목적은 "수정이 새 High를 낳는" 연쇄가 끊겼는지 확인하는 것이었다 — 확인 결과 **연쇄가 끊겼다**. GC-C004를 고친 Step 6f는 새로운 오탐을 도입하지 않았다. 지적 총 1건(GC-C003 이월 Low, 변동 없음), Critical 0 / High 0 / Medium 0 / Info 0.
