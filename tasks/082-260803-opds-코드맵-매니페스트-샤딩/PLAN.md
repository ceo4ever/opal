# PLAN: code-scan 매니페스트 샤딩 — 파일 크기 상한 기반 분산 구조

> 작성일: 2026-08-03 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Multi-Feature (기능 8개)
> 대상 버전: `code-scan.js` v1.4.0 → **v1.5.0**

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

`code-scan`은 "소스 디렉토리 1개 = 매니페스트 1개"를 고정 규칙으로 삼아 매니페스트가 무한정 비대해진다. 이를 **베이스 매니페스트가 선언하는 의미 단위 샤드**로 분산하고, **매니페스트 파일당 바이트 상한**을 도구가 감지·보고하도록 한다.

진입 경로(`mirrorPathForDir` 산출 경로)는 그대로 두고 그 파일에 샤드 선언을 실으며, 샤드 로딩·중복 판정은 신설 헬퍼 `resolveShards` **1곳에 봉인**한다. 샤드 미선언 자산에서는 헬퍼가 `null`을 돌려주어 모든 소비처가 오늘과 동일한 코드 경로를 탄다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 샤드 해석 봉인 헬퍼 + 조회 경로 배선 | TASK F-1 | P0 | 없음 |
| F-002 | 기록 위치 라우팅 (`decideTarget`) | TASK F-2 | P0 | F-001 |
| F-003 | `validate` 샤드 정합 (합집합 기준 재구성) | TASK F-3 | P0 | F-001 |
| F-004 | `scaffold` 샤드 보존·배치·stale 차단 | TASK F-4 | P0 | F-001 |
| F-005 | 크기 상한 집행 (감지·보고) | TASK F-5 | P0 | F-003, F-004 |
| F-006 | `_shards` 예약어 가드 | TASK F-6 | P1 | F-003, F-004 |
| F-007 | 하위호환 회귀 가드 + 테스트 자산 | TASK F-7 | P0 | F-001~F-006 |
| F-008 | 문서·배포 반영 | TASK F-8 | P1 | F-007 |

### 1.3 기능 의존 그래프

```
F-001 ─┬─ F-002 ──────────────┐
       ├─ F-003 ─┬─ F-005 ─┐  │
       └─ F-004 ─┴─ F-006 ─┴──┴─ F-007 ─ F-008
```

### 1.4 [MUST] 제약 (재해석 금지 — 원문 인용)

- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다."
- [MUST] `opal/core/references/opal-harness.md` §1 커밋 규칙: "커밋은 사용자가 명시적으로 요청할 때만 수행한다."
- [MUST] `opal/core/PRINCIPLES.md` §2 Simplicity First: "Solve only the current requirement. No speculative abstraction or unrequested flexibility."
- [MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes: "Touch only what the plan names. Don't improve adjacent code."
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, `agents/`, `community-skills/`, `scripts/`)에서 수행한다."
- [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리: "Claude / Cursor / Gemini / Antigravity 등 플랫폼별 차이는 어댑터 계층에서만 흡수한다. 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다."
- [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함."
- [MUST] `docs/CONVENTIONS.md` §@header 규칙: "기록 소스는 `.opal/code-scan.json`의 전역 `headerSource` 단일 키가 결정한다 — `inline` | `manifest` 2택이며 스코프별 오버라이드는 없다."
- [MUST] `docs/CONVENTIONS.md` §Citation Rules: "TASK.md / PLAN.md / ANALYSIS.md / QA 산출물 등을 작성할 때 모든 주장은 근거를 인용한다 (`{경로}:{라인}` 또는 `docs/문서명 §섹션`)."
- [MUST] `opal/core/references/harness/citation-rules.md` §0: "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거(경로/줄번호 + 섹션)를 인용해야 한다."
- [MUST] `opal/core/references/harness/header-rules.md` §워커 권한 경계: "금지 (파일 단위) `.opal/code-map/index.json` 전체 — 소유자·PM 관할 — 워커 직접 편집 금지"

### 1.5 미확정 사항(U-1~U-4) 결정

| # | 쟁점 | **결정** | 근거 |
|---|------|---------|------|
| **U-1** | 크기 상한 기본값 | **20480 바이트 (20 KiB)**. 내장 기본값이며 `.opal/code-map/index.json` 최상위 `manifestMaxBytes`로 프로젝트별 상향 가능 | ① 실측에서 이 값이 위험군 5개를 정확히 분리한다 (TASK §배경 분석 (1)) ② 20KB JSON은 열람 시 대략 5~6K 토큰으로, 사고를 낸 86.4KB와 한 자릿수 배율의 여유가 있다 (TASK §배경 — 292엔트리 86.4KB 열람 중 600초 워치독 초과) ③ U-2가 비차단이므로 과탐 비용이 "차단"이 아니라 "알림"이다 ④ 상한 근거가 1개 프로젝트 실측뿐이라는 약점은 설정 키로 흡수한다 |
| **U-2** | 차단 vs 경고, 적용 범위 | **전면 비차단(열거·경고) 단일 단계**. `validate`가 `manifest_oversize`를 `violations[]`에 열거하되 차단 위반에서 제외하고, `scaffold`는 stderr 1줄로 알린다. 샤드 선언 보유 여부와 무관하게 동일 적용 | ① 실측상 이미 초과 5개가 존재하므로 차단하면 도입 즉시 `validate`가 exit 2가 되어 CLOSE 게이트(`opal/core/references/harness/header-rules.md` §갱신 시점 (b))가 전면 봉쇄된다 ② 이번 범위는 도구 개선까지이고 실제 자산 분할은 별도 작업이다 (TASK 확정 방향 #10) ③ "샤드 선언 보유 스코프 한정 차단"은 샤딩을 도입할수록 불리해지는 역인센티브를 만들고 분기 1종을 더한다 ④ F-5 AC는 "경로와 실제 크기를 포함해 열거"만 요구한다 |
| **U-3** | 신규 파일 라우팅 글롭 채택 | **미채택**. 샤드 미보유 파일의 라우팅 대상은 **베이스 매니페스트**다 (라우팅 규칙 = "보유 샤드 → 없으면 베이스") | ① [MUST] `opal/core/PRINCIPLES.md` §2 — 글롭 채택은 스키마 필드 1개 + 글롭 충돌 위반 1종 + 매칭 엔진 표면을 더한다 ② 분할 경계는 의미이고 그 판단은 소유자 몫이다 (TASK 확정 방향 #8·#10) — 글롭은 신규 파일의 의미를 도구가 추측하게 만든다 ③ 베이스로 모으면 신규 파일이 `scaffold`의 `added[]`와 크기 상한 경고에 즉시 드러나 소유자가 의미 배치를 하게 된다 ④ 샤드 미선언 자산에서 `decideTarget` 반환이 오늘과 완전히 동일해진다 |
| **U-4** | 중복 키 조회 결정론 | **선언 순서 우선 + 첫 승리(first-wins)**. 순서는 `베이스 → shards[] 배열 순`이며 베이스가 언제나 첫 번째다. 조회는 승자 엔트리로 계속 동작하고, `validate`가 `worker_scope_violation:shard_duplicate_key`로 별도 차단 보고한다 | ① 샤딩 이전 자산은 전량 베이스에 있으므로 베이스 선행이 마이그레이션 중 안정적이다 ② `shards[]`는 소유자가 쓴 배열이라 순서가 이미 결정적이다 ③ "조회는 계속 동작해야 한다"는 TASK U-4 전제를 충족하면서 중복 자체는 차단 위반으로 남는다 |

> **U-4 파생 결정 (데이터 손실 방지)**: `scaffold`는 중복 키를 **자동 해소하지 않는다**. 중복이 검출된 디렉토리는 통째로 건너뛰고 `skipped[]`에 사유를 남긴다. 자동 해소하면 승자가 아닌 쪽(샤드)의 워커 기입 서술이 소리 없이 삭제된다.

### 1.6 문서/코드 불일치 (발견 사항 — PM 보고)

| # | 항목 | 문서 | 실제 코드 | 이번 처리 |
|---|------|------|----------|----------|
| M-1 | inline 모드에서 매니페스트를 읽지 않는다 | TASK §제약 조건: "inline 모드 무영향 — `headerSource=inline`에서는 매니페스트를 읽지도 쓰지도 않으므로" | `cmdValidate`가 inline 모드에서도 `resolveManifestContext`를 호출해 매니페스트를 읽는다 (`opal/tools/code-scan/code-scan.js:1850-1851`) — `conflict:inline_shadowed` 판정(`code-scan.js:1874`)에 필요하기 때문 | **코드 기준**으로 작업한다. 단 **샤드 해석만은 inline에서 발동시키지 않는다** (§3.1.2 (A) 모드 게이트). 결과적으로 inline 모드에서 `inline_shadowed`는 베이스 엔트리만 본다 — 설계된 트레이드오프이며 §9 R-6에 기재 |
| M-2 | 하위호환 범위 | TASK §제약 조건: "샤드 선언이 없는 매니페스트에서는 **모든 명령**의 출력이 변경 전과 바이트 단위로 동일" ↔ TASK §명확화 제약 ④: "**조회 8커맨드** 외부 계약 무변경" ↔ F-7 AC: "샤드 미선언 스코프의 **조회 명령** 출력의 골든 차이가 0" | `validate` 결과 스키마는 이미 태스크마다 확장돼 왔다 — 080이 `result['headerSource']`를 무조건 추가했다 (`code-scan.js:2020-2022`) 및 그에 맞춰 골든을 재캡처했다 | **바이트 동일성 보증 대상을 명시 확정**한다 — 조회 8커맨드 + `target` + `scaffold` stdout JSON. `validate`는 `counts.manifest_oversize` 키 1개와 신규 `violations[]` 항목이 **추가**된다(기존 필드 의미 불변). §9 R-1에 기재하며 PM 승인 대상 |

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `cmdValidate` 구조 패스 (`code-scan.js:1957-1967`) | 매니페스트별 `files_key_added`/`files_key_removed` 판정 → 샤드마다 "디스크에 있는데 내 files에 없다"로 전량 오탐. 정상 샤드 구성이 수십 건 위반으로 뒤덮인다 | **P0** | L1(단위 로직) + L2(실 픽스처 CLI 블랙박스) 의무 | S-1: 정상 샤드 3구성에서 위반 0건 |
| H-2 | `cmdScaffold` stale 수집 (`code-scan.js:1724-1732`) | `validManifestPaths`에 샤드가 없어 `_shards/*.json` 전량 stale. 소유자가 stale을 신뢰해 삭제하면 **자산 소실** | **P0** | L2(CLI) 의무 | S-2: `scaffold` 재실행 시 `stale` 0건 |
| H-3 | `mergeManifest` (`code-scan.js:1600-1627`) 파일 배치 | 샤드 소유 키가 베이스 버킷으로 흘러 샤드에서 `pruned`됨 → **워커 기입 서술 소실**. 특히 중복 키 자동 해소 시 승자 아닌 쪽이 삭제 | **P0** | L1 + L2(재실행 멱등·내용 보존 바이트 대조) 의무 | S-3: `scaffold` 2회 실행 후 샤드 내용 바이트 동일 / S-4: 중복 시 디렉토리 skip |
| H-4 | `resolveHeader` `package` 3단 상속 (`code-scan.js:1038,1048`) | `_source`/`_sources` 출력 토큰이 바뀌면 조회 8커맨드 골든이 깨진다 (`tests/fixtures/golden/*`) | **P0** | L2(골든 바이트 대조) 의무 | S-5: 샤드 미선언 스코프 골든 diff 0 |
| H-5 | `decideTarget`에 매니페스트 로딩 추가 (`code-scan.js:1083-1111`) | 오늘은 파일 I/O가 없다. 파손 매니페스트에서 `manifest_parse_failed`가 새로 발생해 `target`이 exit 1이 된다. hook 경로는 try/catch(`code-map-hook.js:145-149`)로 흡수되지만 CLI는 노출 | P1 | L2(파손 픽스처) + L2(hook 무출력 계약) | S-6: 파손 베이스에서 hook 무출력 exit 0 |
| H-6 | 크기 상한 도입 | 차단으로 걸면 실측 초과 5개 보유 프로젝트의 CLOSE 게이트가 즉시 전면 봉쇄 | **P0** | L1(비차단 판정) + L2(exit code) 의무 | S-7: 초과 존재 + 다른 위반 0건 → exit 0 |
| H-7 | `_shards` 예약어 | 동명 소스 디렉토리가 있으면 진짜 하위 디렉토리 매니페스트가 샤드 네임스페이스와 겹쳐 **조용히 덮인다** | P1 | L2(전용 에러 코드 + exit≠0) | S-8: `_shards` 소스 디렉토리에서 scaffold 거부 |
| H-8 | `resolveShards` 모드 게이트 | 게이트가 없으면 inline 모드에서 샤드 파일을 읽어 "inline 무영향" 계약이 깨진다 | P1 | L2(inline 모드 픽스처 stdout·stderr 양축) | S-9: inline + 샤드 자산에서 출력 무변화 |
| H-9 | 샤드 라벨 문자열 → 경로 파생 | 라벨에 `/`·`..`가 들어가면 code-map 밖으로 쓰기 경로가 벗어난다 (경로 traversal) | **P0** | L1(라벨 정규식) + L2(악성 라벨 픽스처 exit 1) 의무 | S-10: 비정상 라벨에서 `shard_declaration_invalid` |
| H-10 | `CODE_MAP_VERSION` 상향 유혹 | 상향하면 기존 전 자산이 `unsupported_version`으로 차단된다 (`code-scan.js:849-851`, `code-scan.js:1922-1924`) | **P0** | L1(상수 불변 검사) | S-11: `CODE_MAP_VERSION === 1` 고정 |

---

## 2. 기능별 분석

### F-001: 샤드 해석 봉인 헬퍼 + 조회 경로 배선

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | 상수·`loadCodeMap`·`resolveManifestContext`·`resolveHeader` + 신설 `resolveShards` | 수정 |

#### 2.1.2 현재 구현
- `loadCodeMap`(`code-scan.js:834-865`)이 `index.json`을 읽고 `{present, index, manifests: new Map()}`를 돌려준다. 스코프는 `normalizeIndexScope`(`code-scan.js:436-471`)로 `{root, anchors, stripPrefix, include, exclude}` 단일 형태로 정규화된다. 최상위에 크기 상한 개념은 없다.
- `loadManifest`(`code-scan.js:874-886`)가 `ctx.codeMap.manifests` Map에 절대 경로 키로 캐시한다. JSON 파싱 실패는 `CodeMapFatalError('manifest_parse_failed')`.
- `resolveManifestContext`(`code-scan.js:944-956`)는 `resolveScope` → `mirrorPathForDir` → `manifestRel = ${CODE_MAP_DIR}/${scopeName}/${mirrorRel}.json`을 **계산**하고 그 1개만 로드한다 (`code-scan.js:952-954`). 형제 매니페스트를 탐색하는 코드는 없다.
- `resolveHeader`(`code-scan.js:1018-1074`)는 inline 모드에서 `extractHeader`로 즉시 이탈하고(`code-scan.js:1022`), manifest 모드에서 `mctx.manifest.files[basename]`(`code-scan.js:1037`)과 `mctx.manifest.package`(`code-scan.js:1038`)를 단일 참조한 뒤 `WORKER_FIELDS` 5필드를 `file → package` 2단으로 상속한다(`code-scan.js:1046-1049`). 출처 토큰은 `'file' | 'package' | 'rule' | 'domain'` 4값으로 닫혀 있다(`code-scan.js:1062`).

#### 2.1.3 영향 범위
- **상위 의존**: `scanAll`(`code-scan.js:1117-1133`) → 조회 8커맨드 전부. `cmdValidate`(`code-scan.js:1850,1867`). `decideTarget`은 현재 `resolveManifestContext`를 쓰지 않는다.
- **하위 의존**: `loadManifest`, `mirrorPathForDir`, `hasOwn`, `deriveStem`.
- **공유 상태**: `ctx.codeMap.manifests` 캐시. `code-map-hook.js:143`이 `ctx`를 **직접 조립**하므로(`{projectRoot, config, codeMap, headerSource}`) `ctx`에 새 필수 키를 추가하면 hook이 깨진다 → 신규 캐시는 **지연 초기화**해야 한다.
- **관련 테스트**: `tests/test-resolve-header.js`, `tests/test-header-source.js`, `tests/test-regression.js`(골든 8커맨드, `tests/fixtures/golden/`).

---

### F-002: 기록 위치 라우팅 (`decideTarget`)

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `decideTarget` 반환 경로 산출 | 수정 |
| 공통 | `opal/tools/code-scan/code-map-hook.js` | `decideTarget` 소비처 | **무변경** (자동 정합) |

#### 2.2.2 현재 구현
`decideTarget`(`code-scan.js:1083-1111`)은 3단이다 — ① 스코프 필터 탈락 → `{write_to:'none', reason:'out_of_scope'}`(`code-scan.js:1091-1093`) ② inline → `{write_to:'inline', reason:'header_source_inline'}`(`code-scan.js:1097`) ③ manifest → 미러 경로를 계산해 `out.manifest`/`out.scope`/`out.key`를 싣는다(`code-scan.js:1100-1109`). **파일 I/O가 전혀 없다.**

`cmdTarget`(`code-scan.js:1745-1754`)은 결과를 그대로 출력하며 human 출력은 `write_to`/`reason`/`manifest` 3줄이다.

#### 2.2.3 영향 범위
- **상위 의존**: `cmdTarget`, `code-map-hook.js:146`. hook은 `decision.manifest`와 `decision.key`만 읽어 매니페스트 엔트리 청결도를 판정한다(`code-map-hook.js:77-85`) → `manifest`가 샤드 경로를 가리키면 자동으로 정합한다 (TASK §배경 분석 (2) D-2 판정과 일치).
- `reason` 도메인은 3값으로 닫혀 있다고 문서에 명문화돼 있다 (`opal/core/references/harness/header-rules.md` §기록 위치 판정, `opal/core/references/tools.md:241-247`) → **`reason`에 4번째 값을 추가하지 않는다.**
- **관련 테스트**: `tests/test-target.js`, `tests/test-hook.js`.

---

### F-003: `validate` 샤드 정합 (합집합 기준 재구성)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdValidate` 구조 패스 | 수정 |

#### 2.3.2 현재 구현
구조 패스(`code-scan.js:1908-1992`)는 `listManifestFiles(scopeMapDir)`(`code-scan.js:1629-1642`, 재귀 walk)로 **모든 `.json`을 평면 열거**하고 각각을 독립 매니페스트로 취급한다:
- `version` 불일치 → `CodeMapFatalError('unsupported_version')` (`code-scan.js:1922-1924`)
- `scope` 불일치 → `worker_scope_violation:scope_mismatch` (`code-scan.js:1927-1929`)
- `mirrorPathForDir(manifest.dir)` 결과 ≠ 실제 미러 경로 → `worker_scope_violation:dir_mismatch` (`code-scan.js:1931-1935`)
- `manifest.dir` 부재 → `orphan:dir_missing` (`code-scan.js:1938-1942`)
- **`files` 키 ↔ 디스크 대조** (`code-scan.js:1957-1967`) — 키에만 있으면 `orphan:file_missing` + `worker_scope_violation:files_key_added` 2건, 디스크에만 있으면 `worker_scope_violation:files_key_removed` 1건
- `package`/엔트리의 `layer`/`domain`/`module` 침범 검사 (`code-scan.js:1969-1989`)

파일 루프(`code-scan.js:1845-1897`)는 `resolveManifestContext`로 얻은 `mctx.manifest.files[basename]`(`code-scan.js:1851`)로 커버 판정하고, 위반의 `manifest` 필드에 `mctx.manifestRel`을 싣는다(`code-scan.js:1875,1882,1893`).

차단 정책은 `uncovered:pre_existing`만 비차단(`code-scan.js:2006-2009`), `counts`는 8키 고정(`code-scan.js:1994-2003`).

#### 2.3.3 영향 범위
- **가장 실수 나기 쉬운 지점**은 `code-scan.js:1957-1967`이다. 샤드 도입 시 이 판정을 **베이스 + 전 샤드 합집합**으로 바꾸지 않으면 샤드마다 전량 오탐한다 (H-1, P0).
- `orphan:dir_missing`(`code-scan.js:1938-1942`)도 위험하다 — 샤드마다 반복하면 디렉토리 1개 부재가 `1+N`건으로 부풀어 오른다.
- **관련 테스트**: `tests/test-validate.js`(1,000줄 규모, 077·080 자산 승계 구조), `tests/fixtures/violations/*`.

---

### F-004: `scaffold` 샤드 보존·배치·stale 차단

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `mergeManifest` / `cmdScaffold` | 수정 |

#### 2.4.2 현재 구현
- `mergeManifest`(`code-scan.js:1600-1627`)는 디스크 파일 목록(`entry.files`)을 기준으로 `files{}`를 재구성하고, 기존 엔트리는 보존하되 `description` 공백이면 `draft: true`를 붙인다(`code-scan.js:1607-1617`). **보존 대상은 `existing.package` 단 하나**다(`code-scan.js:1623`). 출력 키 순서는 `version → scope → dir → [package] → files`.
- `cmdScaffold`(`code-scan.js:1644-1741`) 흐름: inline no-op 이탈(`:1650-1661`) → `index_missing` 게이트(`:1663`) → 스코프별 `collectDirsWithCodeFiles`로 디렉토리 열거(`:1679`) → `mirrorPathForDir`로 매니페스트 경로 산출 + `mirror_collision` 검출(`:1681-1696`) → 디렉토리마다 1개 매니페스트 병합·쓰기(`:1701-1722`) → **stale 수집**(`:1724-1732`) → 결과 출력(`:1734-1740`).
- stale 판정은 `validManifestPaths = new Set(perDir.map(e => e.manifestAbs))`(`code-scan.js:1724`)에 없는 모든 `.json`이다. `listManifestFiles`가 재귀이므로 `_shards/*.json`이 전량 여기 걸린다 (H-2, P0).
- `skipped[]`는 현재 inline no-op 사유 1건만 싣는 배열이다(`code-scan.js:1652-1656`, 정상 경로에서는 `[]` — `code-scan.js:1737`).

#### 2.4.3 영향 범위
- **상위 의존**: 없음(터미널 커맨드). 하지만 파일 **쓰기**를 수행하므로 오동작 시 자산이 파괴된다 (H-3, P0).
- **하위 의존**: `collectDirsWithCodeFiles`(`code-scan.js:1552-1577`), `mergeManifest`, `orderFilesObject`(`code-scan.js:1592-1598`), `listManifestFiles`.
- **관련 테스트**: `tests/test-scaffold.js`(멱등·pruned·`mirror_collision` 회귀).

---

### F-005: 크기 상한 집행 (감지·보고)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | 상수·`loadCodeMap` 스키마·`cmdValidate`·`cmdScaffold` | 수정 |

#### 2.5.2 현재 구현
크기 개념이 코드 어디에도 없다. `loadCodeMap`(`code-scan.js:846-863`)은 `version`/`scopes`만 검증하고 나머지 최상위 키(`domains`/`layerRules`/`exclude`/`origin`/`status`/`note`)는 통과시킨다. `cmdScaffold`는 직렬화 문자열 `serialized`를 이미 손에 쥐고 있고(`code-scan.js:1707`), `cmdValidate` 구조 패스는 매니페스트 절대 경로를 이미 순회한다(`code-scan.js:1917`) → 두 지점 모두 크기 측정에 추가 I/O가 거의 필요 없다.

#### 2.5.3 영향 범위
- `counts` 객체(`code-scan.js:1994-2003`)와 차단 필터(`code-scan.js:2008`)가 변경 대상이다.
- 상한 검사 대상에서 **`index.json`은 제외**한다 — TASK §명확화 범위 "제외: 스코프 레지스트리 `index.json` 자체의 경량화". 구조 패스는 `${CODE_MAP_DIR}/${scopeName}` 하위만 순회하므로(`code-scan.js:1914-1917`) 구조적으로 이미 제외된다.

---

### F-006: `_shards` 예약어 가드

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | `cmdScaffold` 충돌 검출 / `cmdValidate` 구조 패스 | 수정 |

#### 2.6.2 현재 구현
`cmdScaffold`는 동일 매니페스트 경로를 두 소스 디렉토리가 가리키는 경우만 `mirror_collision`으로 거부한다(`code-scan.js:1685-1696`, `errorExit`로 exit 1). 예약 이름 개념은 없다.

소스에 `_shards` 디렉토리가 있으면 `mirrorPathForDir` 산출 `mirrorRel`에 `_shards` 세그먼트가 섞이고, 그 하위 디렉토리 매니페스트가 `{mirrorRel}/_shards/{name}.json`이 되어 **샤드 네임스페이스와 정확히 겹친다**.

#### 2.6.3 영향 범위
- `errorExit`(`code-scan.js:800-805`)는 stdout에 기계 판독 JSON + stderr에 사람용 안내를 내고 exit 1 한다 — 신규 에러 코드는 이 계약을 그대로 쓴다.
- **관련 테스트**: `tests/test-scaffold.js`(`mirror_collision` 패턴 준용).

---

### F-007: 하위호환 회귀 가드 + 테스트 자산

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/tests/test-shard.js` | 샤드 계약 전용 테스트 | 신규 |
| 공통 | `opal/tools/code-scan/tests/fixtures/shard-repo/` | 정상 샤드 구성 픽스처 | 신규 |
| 공통 | `opal/tools/code-scan/tests/fixtures/shard-violations/` | 샤드 위반 4종 + 예약어 + 상한 픽스처 | 신규 |
| 공통 | `opal/tools/code-scan/tests/test-regression.js` | 골든 8커맨드 바이트 대조 | **무변경** (GREEN 유지가 목표) |

#### 2.7.2 현재 구현
테스트 10종은 전부 `spawnSync`로 `code-scan.js`를 띄우는 **CLI 블랙박스** 방식이며, 픽스처를 tmp로 복사한 뒤 실행하는 패턴을 공유한다(`tests/test-validate.js:56-80`). 골든은 `tests/fixtures/golden/`의 8개 파일(`scan.json`/`domain.txt`/`layer.txt`/`search.json`/`exports.json`/`summary.txt`/`depends.txt`/`missing.txt`)과 바이트 동일성을 단언한다(`tests/test-regression.js:90-97,507-509`).

RED-first 규약이 파일 헤더에 명문화돼 있다 — "`~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지" (`tests/test-validate.js` 헤더 주석).

#### 2.7.3 영향 범위
샤드 미선언 스코프에서 코드 경로가 오늘과 동일해야 골든이 유지된다 → `resolveShards`의 `null` 반환 계약이 회귀 방어의 **구조적 근거**다 (H-4).

---

### F-008: 문서·배포 반영

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 공통 | `opal/tools/code-scan/code-scan.js` | 파일 `@header` + 하단 변경이력 | 수정 |
| 문서 | `opal/core/references/tools.md` | code-scan 도구 레지스트리 절 (`:202-343`) | 수정 |
| 문서 | `opal/core/references/harness/header-rules.md` | 기록 위치 판정 · 워커 권한 경계 | 수정 |
| 문서 | `docs/PROJECT.md` | 변경이력 1행 | 수정 |
| 문서 | `docs/ARCHITECTURE.md` | `tools/` 표 code-scan 행(`:82`) + 변경이력 1행 | 수정 |
| 문서 | `docs/CONVENTIONS.md` | — | **무변경** |
| 환경 | `scripts/install-mac.sh` | 배포 스크립트 | **무변경** |

#### 2.8.2 현재 구현
- `code-scan.js` 상단 `@header`는 인라인 블록이며(`code-scan.js:2-11`) `note`에 "code-scan.js 자신은 프로젝트 `.opal/code-map/index.json` 부재로 인라인 전용 모드로 스캔됨"이 기록돼 있다 — **기록 위치는 인라인 유지**다.
- 하단 변경이력은 주석 블록이다(`code-scan.js:2145-2180`, 마지막 항목 v1.4.0).
- `tools.md`의 code-scan 절은 커맨드 블록(`:211-256`)·옵션 표(`:260-272`)·에러 코드 표(`:284-289`)·프로젝트 설정(`:302-342`)으로 구성된다.
- `header-rules.md`는 기록 위치 판정 3단 표(`:16-29`)와 워커 권한 경계 표(`:45-51`)를 갖는다. 금지 필드 목록은 `dir`·`files` 키 목록·`layer`·`domain`·`scope`·`module`·`version`이다(`:48`).
- `install-mac.sh`는 `opal/tools/` 디렉토리를 통째로 배포하고 `code-scan/run.sh`에 실행 권한만 별도로 준다(`scripts/install-mac.sh:1177-1181`) → **신규 파일이 없으므로 스크립트 변경 불요**.

#### 2.8.3 영향 범위
`docs/CONVENTIONS.md` §@header 규칙(`:171-177`)은 "기록 위치는 `code-scan target <file>` 판정을 따른다"고만 서술하므로 샤딩으로 문장이 거짓이 되지 않는다 → 무변경 판정.

---

## 3. 기능별 설계

### F-001: 샤드 해석 봉인 헬퍼 + 조회 경로 배선

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | 상수 3개 추가(`code-scan.js:58-65` 블록) / `loadCodeMap`에 `manifestMaxBytes` 스키마 + `shardViews` 캐시(`:846-864`) / `resolveShards`·`isShardManifestPath`·`baseManifestAbsForShard` 신설(`:956` 직후) / `resolveManifestContext`에 `shardView` 부착(`:944-956`) / `resolveHeader` 3단 상속(`:1036-1049`) | (→ D-1) TASK F-1 |

#### 3.1.2 함수 시그니처 · 데이터 모델

##### (A) 신규 상수

```js
// ── shard constants (082) ────────────────────────────────────────────────
const SHARDS_DIR = '_shards';                              // 예약 폴더명 (확정 방향 #2)
const SHARD_LABEL_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;       // 사람이 읽는 kebab 라벨 (확정 방향 #8)
const DEFAULT_MANIFEST_MAX_BYTES = 20480;                  // 20 KiB (U-1)
```

- [MUST] `docs/CONVENTIONS.md` §네이밍 규칙: "**kebab-case** 사용" — 샤드 라벨은 파일명이 되므로 동일 규칙을 정규식으로 집행한다.
- `SHARD_LABEL_RE`는 **보안 요구**다 — 라벨이 그대로 경로가 되므로 `/`·`.`·`..`를 차단하지 않으면 `.opal/code-map/` 밖으로 쓰기가 나간다 (H-9, P0).
- **`CODE_MAP_VERSION`은 `1`로 고정 유지한다** — 상향하면 기존 전 자산이 `unsupported_version`으로 차단된다 (`code-scan.js:849-851`, `code-scan.js:1922-1924`). 샤드 미선언 매니페스트의 포맷은 바뀌지 않았으므로 상향 근거도 없다 (H-10).

##### (B) 샤드 경로 규칙 — 진입점 무변경

```
베이스 매니페스트 (진입점, 무변경) : .opal/code-map/{scope}/{mirrorRel}.json
샤드                               : .opal/code-map/{scope}/{mirrorRel}/{SHARDS_DIR}/{label}.json
```

- `mirrorRel`은 `mirrorPathForDir`(`code-scan.js:898-942`) 산출값을 **그대로** 쓴다. 새 경로 계산 규칙을 추가하지 않으며, 샤드 경로는 베이스 절대 경로에서 **순수 문자열 파생**으로만 얻는다.
  ```js
  function shardAbsFor(baseManifestAbs, label) {
    const dir = path.dirname(baseManifestAbs);
    const stem = path.basename(baseManifestAbs, '.json');
    return path.join(dir, stem, SHARDS_DIR, label + '.json');
  }
  ```
- `{mirrorRel}/` 미러 하위 폴더는 이미 진짜 하위 디렉토리 매니페스트를 담는다 — 그 안의 **예약 폴더 `_shards/`** 로 분리하므로 육안 구분이 성립한다 (TASK 확정 방향 #2, 배경 분석 (1) "초과 5개 중 3개는 미러 하위 폴더 기존재").

##### (C) 샤드 파일 스키마 — 최소 집합

베이스 매니페스트에 **키 1개만** 추가한다:

```jsonc
{
  "version": 1,
  "scope": "svc",
  "dir": "svc/order-api/src/main/java/com/acme/order/service",
  "shards": ["order-core", "order-pricing"],   // ← 신규. 라벨 문자열 배열, 선언 순서가 곧 우선순위
  "package": { "description": "..." },
  "files": { ... }
}
```

샤드 파일은 **베이스와 동일한 형태**를 재사용한다 (신규 스키마 0개):

```jsonc
{
  "version": 1,
  "scope": "svc",                                            // 베이스와 동일해야 함
  "dir": "svc/order-api/src/main/java/com/acme/order/service", // 베이스와 동일해야 함
  "package": { "description": "..." },                        // 선택 — 소유 샤드 package 티어
  "files": { ... }
}
```

- [MUST] `opal/core/PRINCIPLES.md` §2: "Solve only the current requirement. No speculative abstraction or unrequested flexibility." — **분할 축·샤드별 리뷰 상태·샤드별 출처·글롭 라우팅 필드를 넣지 않는다** (TASK 확정 방향 #6).
- 샤드가 `shards`를 선언하는 중첩은 **지원하지 않는다**. 별도 위반 코드를 신설하지 않으며, 중첩 위치의 파일은 디스크 스윕에서 `shard_undeclared`로 잡힌다 (§3.3.2 (D) Phase C).
- `shards`는 도구·소유자 관할 필드다 → `header-rules.md` §워커 권한 경계 금지 목록에 추가한다 (F-008).

##### (D) `resolveShards` — 봉인 지점 1곳

> 태스크 080이 `resolveHeaderSource`(`code-scan.js:258`)·`isInScope`(`code-scan.js:479`)를 각 1곳에 봉인한 선례를 따른다 (→ D-5).

```js
/**
 * 샤드 해석의 **유일한** 지점. 샤드 로딩·byKey 구성·중복 판정은 이 함수 밖에 존재하지 않는다.
 * @param {string} baseManifestAbs  베이스 매니페스트 절대 경로 (mirrorPathForDir 산출 경로)
 * @param {string} baseManifestRel  프로젝트 루트 기준 POSIX 상대 경로
 * @param {object|null} baseManifest
 * @param {object} ctx  {projectRoot, config, codeMap, headerSource}
 * @returns {ShardView|null}
 * @throws {CodeMapFatalError} 'shard_declaration_invalid'
 */
function resolveShards(baseManifestAbs, baseManifestRel, baseManifest, ctx)
```

```
ShardView = {
  baseRel:  string,
  shards:   Array<{ label: string, manifestRel: string, manifestAbs: string, manifest: object|null }>,  // 선언 순서
  byKey:    Map<basename, {
              owner: 'base' | 'shard',
              label: string|null,
              manifestRel: string,
              entry: object,
              shardPackage: object|null      // owner==='shard' 이고 그 샤드에 package가 있을 때만 non-null
            }>,
  duplicates: Array<{ key: string, winner: string, losers: string[] }>   // manifestRel 값
}
```

**`null`을 반환하는 4조건 (= 옵트인·바이트 동일성의 구조적 보증)**:
1. `ctx.headerSource !== 'manifest'` — **inline 모드 무영향 게이트**. 모드를 읽는 지점은 이 1곳뿐이며, 확정값 읽기이므로 080의 판정 지점 봉인을 훼손하지 않는다 (`code-scan.js:1019`·`:1096`·`:1803`과 동일한 형태).
2. `!baseManifest`
3. `!hasOwn(baseManifest, 'shards')`
4. `Array.isArray(baseManifest.shards) && baseManifest.shards.length === 0`

**`CodeMapFatalError('shard_declaration_invalid')`를 던지는 조건**:
- `baseManifest.shards`가 배열이 아님
- 라벨이 문자열이 아니거나 `SHARD_LABEL_RE`에 불일치
- 라벨 중복 (같은 라벨 2회 선언)

> 검증을 이 1곳에 몰아넣으면 `scaffold`·`validate`·`target`에 같은 검사를 복제할 필요가 없다. hook 경로는 `decideTarget`을 try/catch로 감싸므로(`code-map-hook.js:145-149`) fail-safe가 유지된다.

**합집합 구성 순서 (U-4)**:
```
① 베이스 files{} 키를 Object.keys 순서대로 byKey에 넣는다 (owner: 'base')
② shards[] 배열 순서대로, 각 샤드의 files{} 키를 Object.keys 순서대로 순회
   - byKey에 이미 있으면  → duplicates에 {key, winner: 기존 manifestRel, losers: [...현재]} 누적 (첫 승리)
   - 없으면              → byKey에 넣는다 (owner: 'shard', shardPackage = 그 샤드의 package || null)
```
`files{}`는 `orderFilesObject`(`code-scan.js:1592-1598`)가 basename 사전순으로 정렬해 쓰므로 `Object.keys` 순회는 결정론적이다.

**캐시**: `ctx.codeMap.shardViews` Map (키 = `baseManifestAbs`). `loadCodeMap` 성공 반환(`code-scan.js:864`)에 `shardViews: new Map()`을 추가하되, `code-map-hook.js:143`이 `ctx`를 직접 조립하므로 `resolveShards` 내부에서 **지연 초기화**한다:
```js
const cache = ctx.codeMap.shardViews || (ctx.codeMap.shardViews = new Map());
```
샤드 매니페스트 자체는 기존 `loadManifest`(`code-scan.js:874-886`)로 읽어 `ctx.codeMap.manifests` 캐시를 공유한다 — 새 로더를 만들지 않는다.

##### (E) 경로 판별 보조 2함수 (`resolveShards` 인접 배치)

```js
// 샤드 파일 := 직속 부모 디렉토리 이름이 SHARDS_DIR인 .json
function isShardManifestPath(manifestAbs) {
  return path.basename(path.dirname(manifestAbs)) === SHARDS_DIR;
}
// 샤드 → 소유 베이스 매니페스트 절대 경로 (…/{stem}/_shards/{label}.json → …/{stem}.json)
function baseManifestAbsForShard(shardAbs) {
  return path.dirname(path.dirname(shardAbs)) + '.json';
}
```
이 단순 규칙 1개로 중첩 `_shards`·고아 샤드·미선언 샤드가 전부 동일하게 분류된다.

##### (F) `resolveManifestContext` 배선 (`code-scan.js:944-956`)

`manifest` 로드 직후 1줄을 추가하고 반환 객체에 키 1개를 더한다:
```js
const manifest = loadManifest(manifestAbs, ctx);
const shardView = resolveShards(manifestAbs, manifestRel, manifest, ctx);   // ← 추가
return { scopeName, scope, dirRel, mp, manifestRel, manifestAbs, manifest, shardView };
```
`mp.skipped` 조기 반환 분기(`code-scan.js:949-951`)에도 `shardView: null`을 채워 반환 형태를 통일한다.

##### (G) `resolveHeader` 3단 상속 (`code-scan.js:1036-1049`)

```js
const basename = path.basename(filePath);
const basePkg = (mctx.manifest && mctx.manifest.package) || null;
const owned   = mctx.shardView ? mctx.shardView.byKey.get(basename) : null;

const fe = owned
  ? owned.entry
  : ((mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null);

// package 3단: files > 소유 샤드 package > 베이스 package
const pkgChain = (owned && owned.shardPackage) ? [owned.shardPackage, basePkg] : [basePkg];
```
상속 루프(`code-scan.js:1046-1049`)를 필드별 체인 순회로 바꾼다:
```js
for (const field of WORKER_FIELDS) {
  if (hasOwn(fe, field)) { result[field] = fe[field]; sources[field] = 'file'; contributed = true; continue; }
  for (const p of pkgChain) {
    if (hasOwn(p, field)) { result[field] = p[field]; sources[field] = 'package'; contributed = true; break; }
  }
}
```

- **[MUST] 출처 토큰을 늘리지 않는다** — 두 package 티어 모두 `sources[field] = 'package'`다. `order` 배열(`code-scan.js:1062`)과 `_source`/`_sources` 출력 형태가 불변이므로 조회 8커맨드 골든이 보존된다 (H-4).
- 샤드 미선언 시 `pkgChain === [basePkg]`이므로 루프가 오늘의 `else if (hasOwn(pkg, field))`와 **의미상 동일**하다.
- `hasOwn`(`code-scan.js:807-809`)은 `null` 안전이므로 `basePkg === null`에서도 안전하다.
- `module` 처리(`code-scan.js:1050`)와 `draft` 처리(`code-scan.js:1053`)는 `fe`만 보므로 변경 없다.

#### 3.1.3 환경 변경
해당 없음 (의존성 없는 단일 파일 Node.js CLI).

#### 3.1.4 배치/마이그레이션
해당 없음 — 기존 자산은 `shards` 키가 없으므로 `resolveShards`가 `null`을 돌려 오늘과 동일하게 동작한다 (TASK 확정 방향 #9).

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | F-1 AC | 기능 테스트 | 베이스+샤드 2개 구성에서 `scan --json`이 3개 매니페스트에 흩어진 전 파일의 헤더를 해석한다 |
| TS-002 | F-1 AC | 기능 테스트 | `package` 3단 상속 — 샤드 `package`가 있는 키는 샤드 값, 없는 필드는 베이스 `package` 값이 상속된다 |
| TS-003 | F-1 AC | 회귀 테스트 | 샤드 미선언 매니페스트에서 `_source`/`_sources` 값이 변경 전과 동일하다 (`'file'`/`'package'`/`'rule'`/`'domain'` 4값 유지) |
| TS-004 | F-1 AC / H-9 | 보안 테스트 | 라벨 `"../escape"` / `"a/b"` / `"Core"` 선언 시 `shard_declaration_invalid`로 exit 1하고 code-map 밖에 파일이 생기지 않는다 |
| TS-005 | H-10 | 산출물 검사 | `CODE_MAP_VERSION === 1`이고 기존 매니페스트가 `unsupported_version`으로 차단되지 않는다 |

---

### F-002: 기록 위치 라우팅 (`decideTarget`)

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `decideTarget` ③ 분기(`:1100-1109`)에 샤드 라우팅 3단 추가 | (→ D-1) TASK F-2 |

#### 3.2.2 함수 시그니처 · 데이터 모델

`decideTarget(fileRel, ctx)` **시그니처 무변경**. ③ 분기 내부만 확장한다:

```js
const out = { write_to: 'manifest', reason: 'header_source_manifest' };
const scoped = ctx.codeMap.present ? resolveScope(relPath, ctx.codeMap.index) : null;
if (scoped) {
  const mp = mirrorPathForDir(posixDirname(relPath), scoped.name, scoped.scope);
  if (!mp.skipped) {
    const baseRel = `${CODE_MAP_DIR}/${scoped.name}/${mp.mirrorRel}.json`;
    const baseAbs = path.join(ctx.projectRoot, baseRel);
    const key     = path.basename(relPath);

    out.scope = scoped.name;
    out.key   = key;

    // 샤드 라우팅 2단 (U-3: 글롭 미채택)
    const view  = resolveShards(baseAbs, baseRel, loadManifest(baseAbs, ctx), ctx);
    const owned = view ? view.byKey.get(key) : null;
    if (owned && owned.owner === 'shard') {
      out.manifest = owned.manifestRel;   // ① 보유 샤드
      out.shard    = owned.label;         // TASK F-2 "반환값에 샤드명을 싣는다"
    } else {
      out.manifest = baseRel;             // ② 베이스 보유 · ③ 미보유 신규 파일 (기본 라우팅 대상)
    }
  }
}
return out;
```

- **`reason` 도메인은 3값으로 유지한다** — `header-rules.md` §기록 위치 판정과 `tools.md:241-247`이 폐쇄 도메인으로 명문화했다. 샤드 정보는 기존 `manifest` 필드 + 신규 선택 필드 `shard`에만 실린다.
- `out.shard`는 **샤드로 라우팅될 때만** 존재한다 → 샤드 미선언 자산의 반환 JSON이 바이트 동일하다.
- `code-map-hook.js`는 `decision.manifest`/`decision.key`만 소비하므로(`code-map-hook.js:79-80`) **무변경으로 자동 정합**한다 (TASK §배경 분석 (2) D-2 판정과 일치).
- `cmdTarget` human 출력(`code-scan.js:1750-1753`)은 `manifest` 줄이 이미 있으므로 무변경한다 — `--json`으로 `shard`를 얻을 수 있다 ([MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes).
- **새 I/O 노출**: `decideTarget`이 처음으로 매니페스트를 읽는다. 파손 매니페스트에서 `manifest_parse_failed`(exit 1)가 새로 노출된다 — 파손된 지도에서 기록 위치를 판정할 수 없으므로 이는 올바른 응답이며, hook은 try/catch로 흡수한다 (H-5, §9 R-4).

#### 3.2.3 환경 변경 / 3.2.4 배치·마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | F-2 AC | 기능 테스트 | 샤드가 보유한 키에 대해 `target <file> --json`이 `manifest`=샤드 경로, `shard`=라벨을 반환한다 |
| TS-007 | F-2 AC / U-3 | 기능 테스트 | 어느 샤드도 보유하지 않은 신규 파일은 `manifest`=베이스 경로를 반환하고 `shard` 키가 없다 |
| TS-008 | F-2 AC | 통합 테스트 | `code-map-hook.js`가 샤드 경로를 읽어 미갱신을 감지한다(엔트리 청결 시 무출력, 미갱신 시 경고에 샤드 경로 포함) |
| TS-009 | F-7 AC | 회귀 테스트 | 샤드 미선언 스코프에서 `target --json` 출력이 변경 전과 바이트 동일하다 |

---

### F-003: `validate` 샤드 정합 (합집합 기준 재구성)

> **이번 변경에서 가장 실수 나기 쉬운 지점이다** (H-1, P0). 현행 `code-scan.js:1957-1967`은 매니페스트별로 디스크와 대조하므로, 샤드를 독립 매니페스트로 취급하는 순간 **샤드마다 전량 오탐**한다.

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | 파일 루프의 소유 매니페스트 귀속(`:1851,1875,1882,1893`) / 구조 패스 전면 재구성(`:1908-1992`) | (→ D-1) TASK F-3 |

#### 3.3.2 함수 시그니처 · 데이터 모델

##### (A) 파일 루프 — 소유 매니페스트 귀속 (`code-scan.js:1845-1897`)

```js
const mctx  = ctx.codeMap.present ? resolveManifestContext(relPath, ctx) : null;
const owned = (mctx && mctx.shardView) ? mctx.shardView.byKey.get(basename) : null;
const fe = owned ? owned.entry
                 : ((mctx && mctx.manifest && mctx.manifest.files && mctx.manifest.files[basename]) || null);
// 위반의 manifest 필드가 "고치러 갈 파일"을 가리키게 한다
const ownerRel = owned ? owned.manifestRel : (mctx ? mctx.manifestRel : undefined);
```
`code-scan.js:1875`(`conflict:inline_shadowed`) · `:1882`(`draft`) · `:1893`(`exports_not_found`)의 `manifest:` 값을 `ownerRel`로 교체한다. 샤드 미선언 시 `ownerRel === mctx.manifestRel`이므로 출력 불변이다.

`managedByManifest`(`code-scan.js:1860`)는 `!!(mctx && mctx.manifest)` 그대로 둔다 — 샤드가 있으면 선언을 담은 베이스가 반드시 존재하므로 판정이 유지된다.

##### (B) 구조 패스 재구성 — 3 Phase

기존 "평면 열거 후 각각 독립 검사"(`code-scan.js:1917-1990`)를 **베이스 그룹 단위**로 바꾼다.

```
Phase A — 분류
  all = listManifestFiles(scopeMapDir)                  // 기존 재귀 walk 재사용
  bases  = all.filter(p => !isShardManifestPath(p))
  shards = all.filter(p =>  isShardManifestPath(p))
  visitedShards = new Set()                              // Phase C용

Phase B — 베이스 그룹 검사 (bases만 순회)
Phase C — 미방문 샤드 스윕
```

##### (C) Phase B — 베이스 그룹 1개당 검사 순서

`B` = 베이스 매니페스트, `view = resolveShards(...)`.

| # | 검사 | 위반 | 귀속 매니페스트 | 비고 |
|---|------|------|---------------|------|
| 1 | `B.version !== CODE_MAP_VERSION` | `CodeMapFatalError('unsupported_version')` | — | 기존 `:1922-1924` 불변 |
| 2 | `B.scope !== scopeName` | `worker_scope_violation:scope_mismatch` | B | 기존 `:1927-1929` 불변 |
| 3 | `mirrorPathForDir(B.dir)` ≠ 실제 미러 경로 | `worker_scope_violation:dir_mismatch` | B | 기존 `:1931-1935` 불변 |
| 3b | 실제 미러 경로에 `_shards` 세그먼트 포함 | `worker_scope_violation:reserved_name` | B | **F-006 신규** |
| 4 | `B.dir` 디렉토리 부재 | `orphan:dir_missing` | B | 기존 `:1938-1942`. **베이스에서 1회만** — 샤드마다 반복하면 1건이 1+N건으로 부풀어 오른다 |
| 5 | 선언된 샤드 파일 부재 | `orphan:shard_missing` (detail = 라벨) | B | **신규**. `orphan` 계열 재사용 → `counts` 키 증가 없음 |
| 6 | 존재하는 샤드 S: `S.version` 불일치 | `CodeMapFatalError('unsupported_version')` | — | 베이스와 동일 처리 |
| 7 | 존재하는 샤드 S: `S.scope !== scopeName` | `worker_scope_violation:scope_mismatch` | S | 기존 sub 재사용 |
| 8 | 존재하는 샤드 S: `S.dir !== B.dir` | `worker_scope_violation:shard_dir_mismatch` | S | **신규 sub**. 기존 `dir_mismatch`를 쓰면 안 된다 — 그 판정은 `dir`에서 미러 경로를 역산하는데 샤드는 미러 경로가 베이스이므로 **항상 위반**이 된다 |
| 9 | `view.duplicates`의 각 항목 | `worker_scope_violation:shard_duplicate_key` (detail = `winner → losers`) | 승자 매니페스트 | **신규 sub**. 중복 키 1개당 **정확히 1건** (F-3 AC) |
| 10 | **합집합 ↔ 디스크 대조** | 아래 (D) | — | **핵심 수정 지점** |
| 11 | `package`/엔트리의 `layer`·`domain`·`module` 침범 | 기존 4종 sub | 해당 엔트리를 담은 매니페스트 | 기존 `:1969-1989`를 **베이스 + 각 샤드에 대해 반복** |

##### (D) 합집합 ↔ 디스크 대조 (H-1 해소)

```js
// 합집합 키 = 베이스 files ∪ 선언·존재하는 각 샤드 files  (= view.byKey, 샤드 미선언 시 베이스 files)
const unionKeys = view ? view.byKey : baseOnlyMap;

// 디스크 목록은 그룹당 1회만 계산한다 (기존 로직·필터 그대로: :1946-1953)
const diskBasenames = dirExists
  ? listCodeFilesInDir(dirAbs, B.dir || '', config, structExcludeDirs, structExcludePatterns, scopeObj)
  : [];
const diskSet = new Set(diskBasenames);

// ① 합집합에 있는데 디스크에 없음 → 소유 매니페스트에 귀속, 키 1개당 2건 (기존과 동일 쌍)
for (const [key, o] of unionKeys) {
  if (!diskSet.has(key)) {
    violations.push({ code: 'orphan', sub: 'file_missing',
                      manifest: o.manifestRel, key, file: `${B.dir}/${key}`, detail: '' });
    violations.push({ code: 'worker_scope_violation', sub: 'files_key_added',
                      manifest: o.manifestRel, key, detail: '' });
  }
}

// ② 디스크에 있는데 합집합에 없음 → **베이스에 1건** (U-3: 미보유 파일의 라우팅 대상이 베이스이므로)
for (const bn of diskBasenames) {
  if (!unionKeys.has(bn)) {
    violations.push({ code: 'worker_scope_violation', sub: 'files_key_removed',
                      manifest: baseRel, key: bn, detail: '' });
  }
}
```

- **불변식**: 정상 샤드 구성에서 `unionKeys`의 키 집합 === `diskSet`이므로 ①②가 모두 0건이다 (F-3 AC "정상 샤드 구성에서 위반 0건").
- 샤드 미선언 시 `unionKeys`는 베이스 `files{}`와 동일하고 귀속 매니페스트도 베이스뿐이므로 **출력이 오늘과 동일**하다.

##### (E) Phase C — 미방문 샤드 스윕

```js
for (const shardAbs of shards) {
  if (visitedShards.has(shardAbs)) continue;
  violations.push({
    code: 'worker_scope_violation', sub: 'shard_undeclared',
    manifest: toPosixRel(projectRoot, shardAbs),
    detail: toPosixRel(projectRoot, baseManifestAbsForShard(shardAbs)),   // 선언해야 할 베이스
  });
}
```
이 1개 규칙이 **베이스 부재 / `shards` 미선언 / 라벨 누락 / 중첩 `_shards`** 4상황을 전부 덮는다. 별도 위반 코드를 만들지 않는다 ([MUST] `opal/core/PRINCIPLES.md` §2).

##### (F) 신규 위반 요약 — `counts` 스키마 영향

| code | sub | 신규 여부 | 차단 | `counts` 키 증가 |
|------|-----|---------|------|----------------|
| `orphan` | `shard_missing` | 신규 sub | 차단 | 없음 (기존 `orphan` 집계) |
| `worker_scope_violation` | `shard_undeclared` | 신규 sub | 차단 | 없음 |
| `worker_scope_violation` | `shard_duplicate_key` | 신규 sub | 차단 | 없음 |
| `worker_scope_violation` | `shard_dir_mismatch` | 신규 sub | 차단 | 없음 |
| `worker_scope_violation` | `reserved_name` | 신규 sub (F-006) | 차단 | 없음 |
| `manifest_oversize` | — | 신규 code (F-005) | **비차단** | **+1** |

> 기존 `code` 2종의 sub만 늘려 `counts` 스키마를 5/6 케이스에서 불변으로 유지했다. 유일하게 늘어나는 키는 F-005의 `manifest_oversize` 1개다 (§1.6 M-2).

#### 3.3.3 환경 변경 / 3.3.4 배치·마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | F-3 AC | 기능 테스트 | 정상 샤드 구성(베이스+샤드 2, 디스크 파일 전량 커버)에서 `validate` 위반 0건 + exit 0 |
| TS-011 | F-3 AC | 기능 테스트 | 중복 키 1개 → `worker_scope_violation:shard_duplicate_key` **정확히 1건**, `manifest`=승자, detail에 패자 경로 |
| TS-012 | F-3 AC | 기능 테스트 | 선언됐으나 파일 없음 → `orphan:shard_missing` **정확히 1건**, detail=라벨 |
| TS-013 | F-3 AC | 기능 테스트 | 디스크에 미선언 샤드 파일 존재 → `worker_scope_violation:shard_undeclared` **정확히 1건** |
| TS-014 | F-3 AC / H-1 | 기능 테스트 | 샤드가 보유한 키가 `files_key_removed`로 오탐되지 않는다 (정상 구성에서 해당 sub 0건) |
| TS-015 | F-3 AC | 기능 테스트 | 샤드 `dir`이 베이스와 다르면 `shard_dir_mismatch` 1건이고, `dir_mismatch`는 발생하지 않는다 |
| TS-016 | F-3 AC | 기능 테스트 | `B.dir` 디렉토리 부재 시 `orphan:dir_missing`이 **1건**이다 (샤드 수만큼 늘지 않는다) |
| TS-017 | F-3 AC | 기능 테스트 | 샤드 엔트리의 `layer`/`domain`/`module` 침범이 그 샤드 경로에 귀속돼 검출된다 |

---

### F-004: `scaffold` 샤드 보존·배치·stale 차단

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `mergeManifest`에 `shards` 보존(`:1622-1624`) / `cmdScaffold` 버킷 분배·쓰기 루프·stale 집합 재구성(`:1701-1732`) | (→ D-1) TASK F-4 |

#### 3.4.2 함수 시그니처 · 데이터 모델

##### (A) `mergeManifest` — 시그니처 유지, 보존 필드 1개 추가

```js
function mergeManifest(existing, entry)   // 시그니처 무변경
```
`entry.files`의 의미만 "그 디렉토리의 전체 디스크 파일"에서 **"이 매니페스트가 소유할 파일 부분집합"** 으로 좁힌다. 함수 본체 변경은 키 보존 1줄뿐이다:

```js
const manifest = { version: CODE_MAP_VERSION, scope: entry.scopeName, dir: entry.dirRel };
if (existing && hasOwn(existing, 'shards'))  manifest.shards  = existing.shards;   // ← 추가
if (existing && hasOwn(existing, 'package')) manifest.package = existing.package;  // 기존 :1623
manifest.files = orderFilesObject(files);
```
출력 키 순서는 `version → scope → dir → [shards] → [package] → files`. `shards`는 샤드 선언 자산에만 존재하므로 기존 매니페스트의 직렬화가 바이트 동일하다.

##### (B) `cmdScaffold` 버킷 분배 (`code-scan.js:1701-1722` 교체)

```
디렉토리 entry 1개당:
  existingBase = 기존 베이스 매니페스트 (없으면 null)
  view = resolveShards(baseAbs, baseRel, existingBase, ctx)

  ── 가드 1: 중복 키 (U-4 파생 결정 — 자동 해소 금지)
  if (view && view.duplicates.length > 0) {
      skipped.push({ reason: 'shard_duplicate_key', manifest: baseRel,
                     detail: view.duplicates.map(d => d.key).join(',') });
      continue;                       // 이 디렉토리는 쓰지 않는다
  }

  ── 가드 2: 선언됐으나 파일 없음 (샤드를 새로 만들지 않는다)
  for (const s of (view ? view.shards : [])) if (!s.manifest) {
      skipped.push({ reason: 'shard_missing', manifest: s.manifestRel, detail: s.label });
  }

  ── 버킷 분배 (U-3: 보유 샤드 → 없으면 베이스)
  buckets = { [baseAbs]: [] };  for each 존재 샤드 s: buckets[s.manifestAbs] = []
  for (const bn of entry.files) {
      const o = view ? view.byKey.get(bn) : null;
      if (o && o.owner === 'shard' && buckets[o.manifestAbs]) buckets[o.manifestAbs].push(bn);
      else buckets[baseAbs].push(bn);
  }

  ── 쓰기 (기존 :1706-1721 루프를 버킷마다 반복)
  for each (manifestAbs, files) of buckets:
      { manifest, pruned, added } = mergeManifest(해당 기존 매니페스트, { ...entry, files })
      기존과 동일하게 serialize → isNew/changed 판정 → 쓰기 → created/updated/unchanged/added/pruned 집계
```

- **`added`는 언제나 베이스에만 발생한다** (U-3) → 소유자가 `added[]`를 보고 의미 배치를 수행한다.
- **삭제 파일**은 해당 버킷에서 빠지므로 `mergeManifest`의 기존 prune 로직(`code-scan.js:1618-1620`)이 소유 샤드에서 제거한다.
- 존재하지 않는 샤드는 버킷을 만들지 않는다 → **빈 샤드 파일을 새로 생성하지 않는다** ([MUST] `opal/core/PRINCIPLES.md` §2 — F-4 AC가 생성을 요구하지 않는다).
- `skipped[]`는 이미 존재하는 배열이다(`code-scan.js:1652-1656,1737`) → 신규 결과 필드 0개.

##### (C) stale 집합 재구성 (`code-scan.js:1724-1732`) — H-2 해소

```js
const validManifestPaths = new Set();
for (const e of perDir) {
  validManifestPaths.add(e.manifestAbs);              // 베이스 (기존)
  for (const s of (e.view ? e.view.shards : [])) {
    validManifestPaths.add(s.manifestAbs);            // ← 선언된 샤드 (파일 존재 여부 무관)
  }
}
```
- TASK F-4 "무엇을"은 "`_shards/*.json`을 stale 수집에서 제외"라고 적었으나, **선언된 샤드만 제외**하는 이 규칙이 더 정확하다 — 미선언 샤드 파일은 실제로 참조되지 않는 자산이므로 stale로 드러나야 하고, `validate`의 `shard_undeclared`와 신호가 일치한다. F-4 AC("stale 목록에 샤드가 0건")는 그대로 충족된다.
- 파일이 아직 없는 선언 샤드도 집합에 넣어야 한다 — 넣지 않아도 `listManifestFiles`가 못 찾으므로 결과는 같지만, 의도를 코드로 남긴다.

#### 3.4.3 환경 변경 / 3.4.4 배치·마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | F-4 AC / H-2 | 기능 테스트 | 샤드 구성에서 `scaffold` 재실행 시 `stale` 배열에 샤드가 **0건** |
| TS-019 | F-4 AC / H-3 | 회귀 테스트 | `scaffold` 2회 실행 후 베이스의 `shards` 선언과 각 샤드 파일 내용이 **바이트 동일**(멱등) |
| TS-020 | F-4 AC / U-3 | 기능 테스트 | 신규 디스크 파일이 베이스 `files{}`에 `draft:true`로 추가되고 `added[]`에 베이스 경로로 보고된다 |
| TS-021 | F-4 AC | 기능 테스트 | 샤드 소유 키의 디스크 파일 삭제 시 그 **샤드**에서 pruned되고 베이스는 무변화 |
| TS-022 | U-4 파생 / H-3 | 기능 테스트 | 중복 키 존재 시 그 디렉토리를 건너뛰고 `skipped[]`에 `shard_duplicate_key`를 남기며, **샤드 파일 내용·mtime이 무변화** |
| TS-023 | F-7 AC | 회귀 테스트 | 샤드 미선언 스코프에서 `scaffold --json` 출력이 변경 전과 바이트 동일하다 |

---

### F-005: 크기 상한 집행 (감지·보고)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `loadCodeMap` 스키마 검증 추가(`:846-863`) / `cmdValidate` 구조 패스에 크기 검사 + `counts` 키(`:1994-2003`) + 차단 필터(`:2008`) / `cmdScaffold` stderr 경고 | (→ D-1) TASK F-5, U-1·U-2 |

#### 3.5.2 함수 시그니처 · 데이터 모델

##### (A) 설정 필드 — `index.json` 최상위 `manifestMaxBytes`

```jsonc
{
  "version": 1,
  "manifestMaxBytes": 20480,     // 선택. 미설정 시 DEFAULT_MANIFEST_MAX_BYTES(20480)
  "scopes": { ... }
}
```

**배치 근거**: 크기 상한은 code-map 자산에 대한 **소유자 정책**이고, `index.json`은 그 자산 레지스트리이자 소유자·PM 관할 파일이다 — [MUST] `opal/core/references/harness/header-rules.md` §워커 권한 경계: "금지 (파일 단위) `.opal/code-map/index.json` 전체 — 소유자·PM 관할 — 워커 직접 편집 금지". 워커가 상한을 임의로 올려 경고를 끄는 경로가 구조적으로 막힌다.

**검증** (`loadCodeMap`, `code-scan.js:846-863` 계열에 추가):
```js
if (hasOwn(index, 'manifestMaxBytes')) {
  const v = index.manifestMaxBytes;
  if (typeof v !== 'number' || !Number.isFinite(v) || v <= 0) {
    return { present: true, error: 'invalid_index', index, manifests: new Map() };
  }
}
```
기존 스키마 게이트와 동일 처리이며 **신규 에러 코드를 만들지 않는다** ([MUST] `opal/core/PRINCIPLES.md` §2).

접근 헬퍼(값 읽기 1곳):
```js
function manifestMaxBytes(ctx) {
  const v = ctx.codeMap.index && ctx.codeMap.index.manifestMaxBytes;
  return typeof v === 'number' ? v : DEFAULT_MANIFEST_MAX_BYTES;
}
```

##### (B) `validate` — 비차단 열거 (U-2)

구조 패스에서 순회 중인 매니페스트마다(베이스·샤드 공통, `index.json` 제외):
```js
const size = fs.statSync(manifestAbs).size;
if (size > limit) {
  violations.push({ code: 'manifest_oversize', manifest: manifestRel,
                    detail: `${size}/${limit}` });      // 경로 + 실제 크기 (F-5 AC)
}
```
- `counts`에 `manifest_oversize` 키 1개 추가 (`code-scan.js:1994-2003`).
- 차단 필터에서 제외 (`code-scan.js:2008`):
  ```js
  const blockingViolations = violations.filter(v =>
    !(v.code === 'uncovered' && v.sub === 'pre_existing') &&
    v.code !== 'manifest_oversize');
  ```
- **측정 단위는 파일 1개의 바이트 크기**다 — 합산이 아니다. 워커가 실제로 여는 단위가 파일 1개이기 때문이며, 이것이 확정 방향 #1("매니페스트 파일당 크기 상한 관리")·#5(바이트 단위)의 직역이다.
- inline 모드에서는 구조 패스 자체가 스킵되므로(`code-scan.js:1908`) 크기 검사도 발동하지 않는다 (inline 무영향).

##### (C) `scaffold` — 알림 (U-2)

`serialized`를 이미 계산하는 지점(`code-scan.js:1707`) 직후:
```js
const bytes = Buffer.byteLength(serialized);
if (bytes > limit) {
  process.stderr.write(
    `code-scan: [oversize] ${entry.manifestRel} — ${bytes} bytes > ${limit} 상한. ` +
    `_shards/ 의미 단위 분할을 검토하세요\n`);
}
```
- **stdout JSON은 건드리지 않는다** → `scaffold --json` 계약 바이트 동일 (TS-023).
- 쓰기 직전 직렬화 크기로 판정하므로 "초과를 유발하는 시점"이 정확히 잡히고 `--dry-run`에서도 동작한다.

##### (D) 이행 경로 (U-2 — 차단은 이번 태스크에서 도입하지 않는다)

| 단계 | 내용 | 담당 | 시점 |
|------|------|------|------|
| ① | 도구가 초과를 **보이게** 만든다 (비차단 열거 + stderr 알림) | 이번 태스크 | 지금 |
| ② | 적용 프로젝트가 `_shards/`로 의미 분할을 수행한다 | 적용 프로젝트 (TASK 확정 방향 #10) | 별도 작업 |
| ③ | 초과 0건 달성 후 차단 전환 여부를 별도 태스크에서 결정한다 | 소유자 | 후속 |

> **③을 위한 설정 스위치를 지금 만들지 않는다** — [MUST] `opal/core/PRINCIPLES.md` §2: "No speculative abstraction or unrequested flexibility." 차단 전환은 `blockingViolations` 필터 1줄 수정으로 충분하다.

#### 3.5.3 환경 변경 / 3.5.4 배치·마이그레이션
해당 없음. 기존 프로젝트는 `manifestMaxBytes` 미설정 → 기본값 20480 적용 → 초과분이 **비차단으로 보고만** 된다.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-024 | F-5 AC | 기능 테스트 | 초과 매니페스트가 `violations[]`에 `{code:'manifest_oversize', manifest, detail:'{bytes}/{limit}'}`로 열거되고 `counts.manifest_oversize`가 일치한다 |
| TS-025 | U-2 / H-6 | 기능 테스트 | 초과가 있고 다른 위반이 0건이면 `ok:true` + **exit 0** (비차단) |
| TS-026 | F-5 AC | 기능 테스트 | `index.json`의 `manifestMaxBytes`가 기본값을 덮어쓴다 (작은 값 설정 시 초과 검출, 큰 값 설정 시 0건) |
| TS-027 | F-5 AC | 기능 테스트 | `scaffold`가 초과 매니페스트에 대해 stderr 1줄을 내고 **stdout JSON은 무변경**이다 |

---

### F-006: `_shards` 예약어 가드

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | `cmdScaffold` 충돌 검출 자리(`:1685-1696`)에 예약어 검사 / `cmdValidate` Phase B 3b | (→ D-1) TASK F-6 |

#### 3.6.2 함수 시그니처 · 데이터 모델

`cmdScaffold`의 `perDir` 수집 루프(`code-scan.js:1680-1691`) 내부, `mirror_collision` 수집과 **같은 자리**에서:
```js
if (mp.mirrorRel.split('/').includes(SHARDS_DIR)) {
  reserved.push({ dir: d.dirRel, manifest: manifestRel });
  continue;
}
```
루프 종료 후 `mirror_collision` 판정(`code-scan.js:1694-1696`)과 동일한 형태로:
```js
if (reserved.length > 0) return errorExit('reserved_name_collision', { reserved });
```
- `errorExit`(`code-scan.js:800-805`)가 stdout JSON + stderr 안내 + **exit 1**을 처리한다 → F-6 AC "exit 0이 아니다" 충족.
- 세그먼트 검사이므로 소스 디렉토리 `_shards` 자체와 그 **하위** 디렉토리가 모두 잡힌다 (`collectDirsWithCodeFiles`는 코드 파일을 가진 디렉토리만 돌려주므로 두 경우 모두 `mirrorRel`에 세그먼트가 남는다).
- `validate` 쪽은 §3.3.2 (C) 3b — 이미 생성된 자산에서도 조용히 통과하지 않게 한다. 신규 `code`가 아니라 `worker_scope_violation:reserved_name` sub 재사용이다.

**신규 에러 코드 2종 (exit 1)**:

| 코드 | 발생 지점 | 조건 |
|------|---------|------|
| `reserved_name_collision` | `cmdScaffold` | 소스 디렉토리가 `_shards` 예약어와 충돌 |
| `shard_declaration_invalid` | `resolveShards` (전 명령) | `shards`가 배열 아님 / 라벨 형식 위반 / 라벨 중복 |

#### 3.6.3 환경 변경 / 3.6.4 배치·마이그레이션
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-028 | F-6 AC / H-7 | 보안 테스트 | 소스에 `_shards` 디렉토리가 있는 스코프에서 `scaffold`가 `reserved_name_collision`으로 exit 1하고 매니페스트를 쓰지 않는다 |
| TS-029 | F-6 AC | 기능 테스트 | 같은 자산에서 `validate`가 `worker_scope_violation:reserved_name`을 검출한다 |

---

### F-007: 하위호환 회귀 가드 + 테스트 자산

#### 3.7.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/code-scan/tests/fixtures/shard-repo/` | 공통 | 정상 샤드 구성 (베이스 1 + 샤드 2 + 소스 4파일) | TASK F-7 |
| 2 | `opal/tools/code-scan/tests/fixtures/shard-violations/` | 공통 | 위반 픽스처 6종 (중복/미존재/미선언/dir불일치/예약어/초과) | TASK F-3·F-5·F-6 AC |
| 3 | `opal/tools/code-scan/tests/test-shard.js` | 공통 | 샤드 계약 전용 CLI 블랙박스 테스트 (TS-001~TS-029) | TASK F-7 |

**수정**: 없음 — 기존 테스트 10종은 **무변경으로 GREEN 유지**가 목표다 ([MUST] `opal/core/PRINCIPLES.md` §3 Surgical Changes).

#### 3.7.2 설계

##### (A) 픽스처 A — `tests/fixtures/shard-repo/` (정상 구성, 8파일)

```
shard-repo/
  .opal/code-scan.json                            headerSource: manifest, scopes: {svc: "svc/"}
  .opal/code-map/index.json                       version 1, scopes.svc {root:"svc/"}, layerRules, domains
  .opal/code-map/svc/mod.json                     베이스 — shards:["core","pricing"], package, files:{D.ts}
  .opal/code-map/svc/mod/_shards/core.json        files:{A.ts, B.ts}, package(3단 상속 검증용)
  .opal/code-map/svc/mod/_shards/pricing.json     files:{C.ts}  (package 없음 → 베이스 package 상속)
  svc/mod/A.ts  svc/mod/B.ts  svc/mod/C.ts  svc/mod/D.ts
```
- 미러 경로: `svc/mod` → `.opal/code-map/svc/mod.json` (`anchors`/`stripPrefix` 없이 `root` 제거만) — `mirrorPathForDir`(`code-scan.js:898-942`) 규칙 그대로.
- `D.ts`를 베이스에 남겨 "베이스 + 샤드 혼재"를 커버한다.

##### (B) 픽스처 B — `tests/fixtures/shard-violations/` (위반 6종)

각 하위 디렉토리는 픽스처 A를 최소 변형한 독립 트리다.

| 하위 | 변형 | 기대 위반 |
|------|------|----------|
| `duplicate-key/` | `core.json`과 베이스가 동일 키 보유 | `shard_duplicate_key` 1건 |
| `shard-missing/` | `shards:["core","ghost"]`, `ghost.json` 없음 | `orphan:shard_missing` 1건 |
| `undeclared/` | `_shards/extra.json` 존재하나 선언 없음 | `shard_undeclared` 1건 |
| `dir-mismatch/` | `core.json`의 `dir`이 베이스와 다름 | `shard_dir_mismatch` 1건 |
| `reserved-name/` | 소스에 `svc/mod/_shards/X.ts` 디렉토리 | `reserved_name_collision`(scaffold) / `reserved_name`(validate) |
| `oversize/` | `index.json`에 `manifestMaxBytes: 200` | `manifest_oversize`, exit 0 |

> `oversize/`는 상한을 **작게** 설정해 검증한다 — 거대 픽스처 파일을 만들지 않는다.

##### (C) `tests/test-shard.js`

- 기존 관례 준수: `spawnSync`로 `code-scan.js` 실행, 픽스처를 tmp로 복사 후 실행 (`tests/test-validate.js:56-80` 패턴 재사용).
- **RED-first** — 헤더에 `[MUST] ~/.opal/references/harness/red-first.md §3 — GREEN/fix 루핑 중 이 파일 수정 금지`를 명시하고, TC ↔ TS-ID ↔ S-ID 매핑 표를 기존 테스트와 동일 포맷으로 기재한다.
- `@header` 필수 필드 + `layer: test` 선택 필드(`task: "082"`, `scenarios: [...]`) 기재 — [MUST] `opal/core/references/harness/header-rules.md` §테스트 파일 전용 선택 필드.

##### (D) 회귀 방어 근거

`resolveShards`가 샤드 미선언에서 `null`을 돌려주고 모든 소비처가 `view ? 신경로 : 기존경로` 형태를 취하므로, 샤드 미선언 자산의 실행 경로가 **오늘과 동일한 코드**를 탄다 — 골든 8커맨드(`tests/fixtures/golden/*` ↔ `tests/test-regression.js:507-509`) 바이트 동일성의 구조적 근거다 (H-4).

#### 3.7.3 환경 변경 / 3.7.4 배치·마이그레이션
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | F-7 AC | 회귀 테스트 | `node --test opal/tools/code-scan/tests/` 전량 GREEN (기존 10종 무변경) |
| TS-031 | F-7 AC / H-4 | 회귀 테스트 | 골든 8커맨드 출력이 `tests/fixtures/golden/*`와 바이트 동일 |
| TS-032 | F-7 AC / H-8 | 회귀 테스트 | `--header-source inline`으로 샤드 자산을 실행해도 stdout·stderr 양축이 샤드 미도입 시와 동일하다 |
| TS-033 | F-7 AC | 산출물 검사 | `test-shard.js`에 `@header`(`layer:test`, `task:"082"`, `scenarios`)와 TC↔TS 매핑 표가 있다 |

---

### F-008: 문서·배포 반영

#### 3.8.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | 공통 | 상단 `@header` description·note 갱신(`:2-11`) + 하단 변경이력 v1.5.0 행(`:2145-2180` 말미) + `VERSION` 상향(`:37`) | [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 |
| 2 | `opal/core/references/tools.md` | 문서 | code-scan 절(`:202-343`) — 커맨드 설명·에러 코드 표 2행·프로젝트 설정에 `_shards`/`manifestMaxBytes` + 변경이력 행 | (→ D-6) TASK F-8 |
| 3 | `opal/core/references/harness/header-rules.md` | 문서 | §기록 위치 판정에 `manifest` 값이 샤드 경로일 수 있음 1줄 + §워커 권한 경계 금지 필드에 `shards` 추가(`:48`) + 변경이력 행 | (→ D-4) TASK F-8 |
| 4 | `docs/PROJECT.md` | 문서 | 변경이력 1행 (Task 082) | [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 |
| 5 | `docs/ARCHITECTURE.md` | 문서 | `tools/` 표 code-scan 행(`:82`) 1문장 + 변경이력 1행 | 시스템 구조 변경 반영 |

**무변경 확정** (근거를 남겨 EXECUTE가 손대지 않게 한다 — [MUST] `opal/core/PRINCIPLES.md` §3):
| 경로 | 무변경 근거 |
|------|-----------|
| `opal/tools/code-scan/code-map-hook.js` | `decision.manifest`/`decision.key`만 소비하므로 자동 정합 (`code-map-hook.js:79-80`). `@header` 서술도 여전히 참이다 |
| `docs/CONVENTIONS.md` | §@header 규칙(`:171-177`)이 "기록 위치는 `code-scan target <file>` 판정을 따른다"고만 서술 — 샤딩으로 거짓이 되지 않는다 |
| `scripts/install-mac.sh` | `opal/tools/` 통째 배포 + `run.sh` chmod만 수행(`scripts/install-mac.sh:1177-1181`), 신규 배포 파일 없음 |
| `opal/tools/code-scan/tests/fixtures/golden/*` | 골든 재캡처 **금지** — 차이가 나오면 회귀다 (`tests/test-regression.js:509`) |

#### 3.8.2 버전 정책

| 항목 | 현재 | 변경 후 | 근거 |
|------|------|--------|------|
| `VERSION` (`code-scan.js:37`) | `1.4.0` | **`1.5.0`** | 기능 추가 + 하위호환 유지 → semver **minor**. 신규 스키마 키(`shards`/`manifestMaxBytes`)가 전부 선택적이고, 조회 8커맨드 외부 계약이 불변이며, 샤드 미선언 자산의 동작이 바이트 동일하다 (TASK 확정 방향 #9). `validate` 결과에 필드가 추가되지만 이는 080이 `headerSource`를 추가할 때와 동일한 확장 성격이다 (`code-scan.js:2020-2022`) |
| `CODE_MAP_VERSION` (`code-scan.js:59`) | `1` | **`1` 유지** | 상향하면 기존 전 매니페스트가 `unsupported_version`으로 즉시 차단된다 (`code-scan.js:849-851`, `:1922-1924`). 샤드 미선언 매니페스트 포맷은 불변이므로 상향 근거가 없다 (H-10) |

#### 3.8.3 환경 변경 / 3.8.4 배치·마이그레이션
배포는 `./scripts/install-mac.sh` 재실행으로 수행한다 — [MUST] `docs/CONVENTIONS.md` §배포 경계: "변경 후 `./scripts/install-mac.sh`(또는 후속 `opal install`)로 재배포하여 검증한다." 배포 실행은 **소유자 승인 후**다.

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-034 | F-8 AC | 산출물 검사 | `code-scan version`이 `code-scan v1.5.0`을 출력하고 하단 변경이력에 태스크 번호 `(082)` 포함 행이 있다 |
| TS-035 | F-8 AC | 산출물 검사 | `tools.md` code-scan 절에 `_shards`·`manifestMaxBytes`·신규 에러 코드 2종이 반영되고 변경이력 행이 추가됐다 |
| TS-036 | F-8 AC | 산출물 검사 | `header-rules.md` §워커 권한 경계 금지 필드에 `shards`가 있고 변경이력 행이 `YYYY-MM-DD HH:mm` (KST) + `(082)` 포맷이다 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-007 (RED) | 1, 2, 3 | opal-test-agent | 순차 (픽스처 → 테스트) | 구현 전 RED 작성 — 생성자≠구현자 |
| 2 | F-001~F-006 | 4~9 | opal-task-agent | **단일 배치 내 순차** | 전 Step이 `code-scan.js` 1파일 — 동시 편집 시 후행 저장이 선행을 덮어쓴다 |
| 3 | F-007 (GREEN) | 10 | opal-test-agent | 순차 | 전량 GREEN + 골든 diff 0 확인 |
| 4 | F-008 | 11, 12 | opal-task-agent / PM 직접 | 11 → 12 순차 | 12는 `docs/` 갱신 |

### 4.2 실행 체크리스트

> 총 12개 Step | Phase 4개 | 실행 모드: **복잡**

#### Step 1: 정상 샤드 픽스처 생성
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/shard-repo/` (신규 디렉토리 1개 = 8파일 — 트리 1개가 원자 단위이므로 분할 시 깨진 중간 상태가 남는다)
- **작업 내용**: §3.7.2 (A) 구성대로 `.opal/code-scan.json`·`index.json`·베이스 1·샤드 2·소스 4파일 생성. 샤드 `core.json`에 `package`를 두어 3단 상속을 검증 가능하게 한다
- **완료 기준**: `mirrorPathForDir` 규칙상 `svc/mod` → `.opal/code-map/svc/mod.json`이 성립하고, 디스크 4파일이 베이스+샤드 합집합과 정확히 일치
- **테스트**: TS-001, TS-002, TS-010
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: 위반·목표 픽스처 생성
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/fixtures/shard-violations/`, `.../shard-multi-scope/`, `.../shard-goal/` (신규 디렉토리 3개)
- **작업 내용**: §3.7.2 (B) 표 + **[MUST] `TEST-SCENARIO.md` §2.1 사전 조건 데이터 표(픽스처 SSOT)** 대로 생성한다 — `duplicate-key`/`shard-missing`/`undeclared`/`dir-mismatch`/`reserved-name`/`oversize`/`bad-label`/`broken-base`/**`oversize-shard`**(베이스는 상한 이하·샤드만 초과) + **`shard-multi-scope`**(스코프 2개) + **`shard-goal`**(분산 전 트리 + 중간 상태 2종). `oversize` 계열은 `manifestMaxBytes: 200`으로 작게 설정. **`shard-goal`의 분산 후 트리는 픽스처로 수작성하지 않고 Step 3 테스트 내 스크립트가 분산 전에서 파생 생성한다**
- **완료 기준**: 각 트리가 정확히 1종의 위반만 유발하도록 나머지 조건은 정상 (교차 오염 없음). `oversize-shard`는 베이스가 상한 이하임을 확인
- **테스트**: TS-011~TS-015, TS-024~TS-029 + S-23·S-25·S-26
- **실행 방법**: sub-agent
- **의존**: Step 1

> **픽스처 SSOT는 `TEST-SCENARIO.md` §2.1이다.** 목표-커버 게이트 1회차 gaps(G-1 강권·G-3·G-4)로 `oversize-shard`·`shard-multi-scope`·`shard-goal` 중간 상태가 추가되었고, PLAN §3.7.2 (B)는 그 이전 시점 목록이다. 충돌 시 TEST-SCENARIO.md를 따른다.

#### Step 3: RED 테스트 `test-shard.js` 작성
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/test-shard.js` (신규 1파일)
- **작업 내용**: **[MUST] `TEST-SCENARIO.md` §3 시나리오 S-1~S-26 전량**을 CLI 블랙박스로 작성한다(PLAN TS-001~TS-036은 그 하위 케이스로 흡수). 기존 `tests/test-validate.js:56-80` 헬퍼 패턴(`run`/`copyDirRecursive`) 재사용. `shard-goal` 분산 후 트리를 분산 전에서 파생 생성하는 헬퍼를 포함한다. `@header`(`layer:test`, `task:"082"`, `scenarios`) + TC↔S 매핑 표 + red-first [MUST] 주석 기재
- **완료 기준**: 전 케이스가 **RED**(현행 v1.4.0에서 실패)이고, 실패 사유가 "미구현"이지 "테스트 오류"가 아님을 확인
- **테스트**: TS-033
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: 상수 · 스키마 게이트 · 캐시 슬롯
- [x] 완료
- **소속 기능**: F-001, F-005
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.1.2 (A) 상수 3개 추가(`code-scan.js:58-65` 블록 말미) / `loadCodeMap`에 `manifestMaxBytes` 타입 검증(§3.5.2 (A)) + 성공 반환에 `shardViews: new Map()`(`code-scan.js:864`) / `manifestMaxBytes(ctx)` 헬퍼 추가. **`CODE_MAP_VERSION`은 건드리지 않는다**
- **완료 기준**: 기존 테스트 10종 GREEN 유지. `manifestMaxBytes` 타입 위반이 `invalid_index`로 처리됨
- **테스트**: TS-005, TS-026
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: `resolveShards` 봉인 헬퍼 + 경로 보조 2함수
- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.1.2 (D)(E) — `resolveShards`/`isShardManifestPath`/`baseManifestAbsForShard`를 `resolveManifestContext`(`code-scan.js:956`) 직후에 신설. `null` 반환 4조건, `shard_declaration_invalid` 3조건, `byKey` 구성 순서(베이스 → shards[] 순, 첫 승리), `duplicates` 누적, 지연 초기화 캐시. **샤드 로딩·byKey 구성 로직을 이 함수 밖에 만들지 않는다**
- **완료 기준**: 함수가 존재하고 TS-004(악성 라벨 3종)가 GREEN. 다른 소비처는 아직 미배선이므로 기존 테스트 10종 GREEN 유지
- **테스트**: TS-004
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: 조회 경로 배선 — `resolveManifestContext` + `resolveHeader`
- [x] 완료
- **소속 기능**: F-001
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.1.2 (F) `resolveManifestContext`(`:944-956`) 두 반환 경로에 `shardView` 부착 / §3.1.2 (G) `resolveHeader`(`:1036-1049`) `fe`·`pkgChain` 산출 + 필드별 체인 상속 루프. **`sources[field]`에 새 토큰을 만들지 않는다**(`'package'` 유지)
- **완료 기준**: TS-001~TS-003 GREEN, 골든 8커맨드 diff 0
- **테스트**: TS-001, TS-002, TS-003, TS-031
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: `decideTarget` 샤드 라우팅
- [x] 완료
- **소속 기능**: F-002
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.2.2 — `decideTarget` ③ 분기(`:1100-1109`)에 베이스 매니페스트 로드 + `resolveShards` + 2단 라우팅. `out.shard`는 샤드 라우팅 시에만 부여. **`reason` 도메인 3값 유지**, `cmdTarget` human 출력 무변경
- **완료 기준**: TS-006~TS-009 GREEN, `tests/test-target.js`·`tests/test-hook.js` GREEN
- **테스트**: TS-006, TS-007, TS-008, TS-009
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: `scaffold` — 보존·버킷 분배·stale·예약어·크기 알림
- [x] 완료 (TS-020/TS-021 = S-13(a)/(b) 잔여 RED — `shard-repo` 픽스처가 손으로 작성된 비정규 JSON이라 scaffold의 기존(082 이전) 재직렬화 동작이 무변경 샤드도 재포맷한다. 코드 결함이 아니라 픽스처 포맷 이슈이며 상세는 EXECUTE 반환의 blockers 참조)
- **소속 기능**: F-004, F-005, F-006
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.4.2 (A) `mergeManifest` `shards` 보존 1줄(`:1622-1624`) / (B) `cmdScaffold` 버킷 분배 + 중복 가드(디렉토리 skip) + 미존재 샤드 `skipped` 기록(`:1701-1722` 교체) / (C) stale 집합에 선언 샤드 포함(`:1724-1732`) / §3.6.2 예약어 검사 + `reserved_name_collision`(`:1680-1696`) / §3.5.2 (C) oversize stderr 1줄(`:1707` 직후)
- **완료 기준**: TS-018~TS-023, TS-027, TS-028 GREEN. `tests/test-scaffold.js` GREEN. **중복 키 픽스처에서 샤드 파일 mtime·내용 무변화**
- **테스트**: TS-018~TS-023, TS-027, TS-028
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: `validate` — 합집합 구조 패스 재구성 + 크기 열거
- [x] 완료
- **소속 기능**: F-003, F-005, F-006
- **영역**: 공통
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`
- **작업 내용**: §3.3.2 (A) 파일 루프 `ownerRel` 귀속(`:1851,1875,1882,1893`) / (B)(C)(D)(E) 구조 패스를 Phase A·B·C로 재구성(`:1908-1992`) — **`files_key_added`/`files_key_removed`/`orphan:file_missing`을 합집합 기준으로 산출** / `orphan:dir_missing`은 베이스 1회 / (F) `counts.manifest_oversize` 추가(`:1994-2003`) + 차단 필터 제외(`:2008`) / §3.5.2 (B) 크기 열거 / §3.3.2 (C) 3b 예약어 검사
- **완료 기준**: TS-010~TS-017, TS-024~TS-026, TS-029 GREEN. `tests/test-validate.js` GREEN. **정상 샤드 픽스처에서 위반 0건**
- **테스트**: TS-010~TS-017, TS-024, TS-025, TS-026, TS-029
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 9b: 기존 테스트 기준선 보수 (PM 계획 보정 — Step 3 관측)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `opal/tools/code-scan/tests/test-scope-filter.js`, `opal/tools/code-scan/tests/test-regression.js` (2파일, **각 1줄**)
- **작업 내용**: Step 1~3 산출물이 기존 테스트의 하드코딩 기대값을 무효화했다. 두 값만 사실에 맞게 갱신한다 — ① `test-scope-filter.js:183` 문자열 scopes 픽스처 개수 `20` → 실제값 ② `test-regression.js:908` 테스트 파일 `@header.task` 허용 목록 `['077','080']`에 `'082'` 추가
- **완료 기준**: 두 파일 각 1줄 변경. `test-scope-filter.js`·`test-regression.js`가 GREEN(단 `test-regression.js` TS-062 전체 GREEN 메타 검사는 Step 10 이후 해소)
- **테스트**: 해당 2파일 자체
- **실행 방법**: sub-agent
- **의존**: Step 3 (Step 4~9와 **파일 비중첩이므로 병렬 가능**)

> **왜 계획 보정인가**: 두 단언은 "픽스처가 몇 개인가"·"어느 태스크가 테스트 파일을 소유하는가"라는 **사실**을 고정한 트립와이어다. 이번 태스크가 픽스처 16종과 테스트 파일 1개를 정당하게 추가했으므로 사실이 바뀌었다. 단언의 **의도(루프가 조용히 축소되지 않게 함 / 테스트 파일도 @header 자산임)는 그대로 유지**되며, 임계값만 현재 사실로 갱신한다 — 테스트 약화가 아니다. 근거: `opal/core/references/harness/red-first.md` §3은 "GREEN/fix 루핑 중 **RED 테스트 파일** 수정 금지"이며, 본 2파일은 이번 태스크의 RED 자산이 아니다.

#### Step 9c: 픽스처 사양 보정 (PM 계획 보정 — Step 7~9 관측)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `tests/fixtures/shard-repo/.opal/code-map/` 매니페스트 3개, `tests/fixtures/shard-multi-scope/.opal/code-map/index.json` (4파일)
- **작업 내용**: PM 실측으로 확인된 **픽스처 사양 미비 2건** 보정 — ① `shard-repo`의 베이스·샤드2 매니페스트가 비정규 압축 JSON이라 `scaffold` 첫 실행이 재포맷·`draft` 부여 → S-13의 "샤드 무변화" 단언이 라우팅과 무관하게 깨진다. 정규 직렬화 형식으로 재작성 ② `shard-multi-scope/index.json`의 `domains`·`layerRules`가 비어 있어 전 파일이 `uncovered:incomplete`로 잡힌다 → `shard-repo` 패턴을 준용해 채운다
- **완료 기준**: `shard-repo`에서 `scaffold`가 **1회차부터 no-op**(`updated:0`). `shard-multi-scope`에서 `uncovered:incomplete` 0건. S-13·S-26 GREEN
- **테스트**: S-12, S-13, S-26
- **실행 방법**: sub-agent
- **의존**: Step 9 (Step 11과 **파일 비중첩이므로 병렬 가능**)

> **왜 구현 결함이 아닌가 (PM 실측 근거)**: ① 원본 픽스처를 tmp에 복사해 `scaffold`를 2회 돌린 결과 **1회차만 재포맷하고 2회차는 diff 0**이었다 — 샤드 라우팅·병합 로직은 정상이며 첫 실행의 정규화는 `mergeManifest`(`code-scan.js:1600-1627`)의 기존 동작이다. ② `shard-repo`(`domains`·`layerRules` 보유)는 `incomplete` 0건인데 `shard-multi-scope`(둘 다 빈 값)만 4건 발생 — 스코프 개수가 아니라 설정 공백이 원인이다.

#### Step 9d: 픽스처 분리 — S-2/S-7 요구 충돌 해소 (캡틴 승인, 2026-08-03)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `tests/fixtures/shard-package/`(신규 트리), `tests/fixtures/shard-repo/.opal/code-map/svc/mod/_shards/core.json`, `tests/test-shard.js`(**1줄**)
- **작업 내용**: 한 픽스처(`shard-repo`)에 상호 배타적인 두 요구가 걸려 있다 — S-2는 `A.ts`에 **자기 `description`이 없어야** 샤드 `package.description` 상속을 검증할 수 있고, S-7은 같은 픽스처에서 **`validate` 위반 0건**을 요구하는데 description 없는 엔트리는 `draft`로 잡힌다. `shard-repo`를 복제해 `shard-package/`(현행 상태 유지 = 상속 검증용)를 만들고, `shard-repo`의 `A.ts`·`B.ts`에 자기 `description`을 부여(+`draft` 제거)한다. `test-shard.js`의 S-2 케이스가 참조하는 픽스처명만 교체
- **완료 기준**: `test-shard.js` **55/55**. 기존 10종 GREEN, 골든 8파일 바이트 diff 0
- **테스트**: S-2, S-7, S-10, S-19
- **실행 방법**: sub-agent
- **의존**: Step 9c

> **왜 테스트 약화가 아닌가**: S-2의 단언 4개(상속 description 값·`_sources.description === 'package'`·`depends` 상속·출처 폐쇄 도메인)는 **한 글자도 바뀌지 않는다**. 바뀌는 것은 그 단언을 **어느 픽스처에서 수행하느냐**뿐이다. 오히려 S-7이 비로소 "정상 구성 위반 0건"을 실제로 검사하게 되어 검증 강도는 증가한다. 대상 자산(`shard-repo`·`test-shard.js`)은 전부 **이번 태스크가 오늘 생성한 신규 파일**(git 이력 0건)이며 기존 자산은 무관하다. `red-first.md` §3의 취지는 "통과시키려 기대를 낮추는 것"(reward hacking) 금지이며, 본 건은 **동시 충족이 불가능한 픽스처 배정의 교정**이다. 캡틴 승인 하에 수행한다.

#### Step 9e: 잔여 충돌 3건 정리 + 픽스처 요구 전수 점검 (캡틴 승인, 2026-08-03)
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: `tests/test-shard.js`(S-6(b) 픽스처 1줄 + S-19 env 처리), `tests/test-scope-filter.js`(카운트 1줄)
- **작업 내용**: ① **S-6(b)** — S-6(a)(청결 엔트리 무출력)와 S-6(b)(미갱신 엔트리 경고)가 같은 `shard-repo`의 같은 `A.ts`에 정반대를 요구한다. Step 9d가 `A.ts`를 청결하게 만들면서 S-6(b)가 깨졌다. S-2와 동일 처방으로 S-6(b)를 `shard-package`(draft 엔트리 보유)로 재지정 ② **S-19** — `test-shard.js`가 `spawnSync` 자식에 `NODE_TEST_CONTEXT`를 물려줘 재귀 가드로 무력화되어 `fail=-1`을 낸다. 이 테스트는 **지금 아무것도 검증하지 못하는 죽은 상태**다. `test-regression.js:584`와 동일하게 env를 제거해 실제로 동작하게 만든다 ③ **TS-010** — 문자열 scopes 픽스처 카운트를 `shard-package` 추가분 반영해 실측값으로 갱신 ④ **전수 점검** — 같은 유형의 충돌이 더 없는지 `shard-repo` 사용 케이스 전부의 요구를 대조
- **완료 기준**: `test-shard.js` **55/55**, 전체 스위트 GREEN, 골든 8파일 바이트 diff 0
- **테스트**: S-6, S-19, TS-010
- **실행 방법**: sub-agent
- **의존**: Step 9d

> **판단 근거**: ①은 캡틴이 Step 9d에서 승인한 원칙("한 픽스처가 상호 배타적 요구를 받으면 분리")의 **동일 유형 재적용**이다. ②는 기대 완화가 아니라 **죽은 테스트를 살리는 것**이므로 검증 강도가 증가한다(`red-first.md` §3의 reward hacking 금지에 저촉되지 않는다). ③은 Step 9b와 동일 패턴의 사실 갱신이다. ④는 같은 문제가 반복 발생하는 것을 끊기 위한 조치다 — 근본 원인은 RED 작성 시 한 픽스처에 요구를 과다 배정한 것이다.

#### Step 10: 전량 GREEN 검증 + 회귀 대조
- [x] 완료
- **소속 기능**: F-007
- **영역**: 공통
- **agent**: opal-test-agent
- **파일**: (검증 전용 — 파일 생성·수정 없음)
- **작업 내용**: `node --test opal/tools/code-scan/tests/` 전량 실행. 골든 8커맨드 바이트 대조. inline 모드 stdout·stderr 양축 대조(TS-032). **골든 파일 재캡처 금지** — 차이가 나오면 GREEN 처리하지 말고 원인을 규명한다
- **완료 기준**: 11개 테스트 파일 전량 GREEN, 골든 diff 0, inline 모드 출력 동일
- **테스트**: TS-030, TS-031, TS-032
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 11: 코드 메타 + 프레임워크 문서 갱신
- [x] 완료
- **소속 기능**: F-008
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/tools/code-scan/code-scan.js`, `opal/core/references/tools.md`, `opal/core/references/harness/header-rules.md` (3파일)
- **작업 내용**: §3.8.1 1~3행 — `VERSION` → `1.5.0`(`:37`), 상단 `@header` description·note 갱신(`:2-11`), 하단 변경이력 v1.5.0 행 추가 / `tools.md` code-scan 절(`:202-343`)에 샤드 구조·`manifestMaxBytes`·에러 코드 2종 반영 + 변경이력 / `header-rules.md` §워커 권한 경계에 `shards` 추가(`:48`) + §기록 위치 판정 1줄 + 변경이력. **`code-map-hook.js`·`docs/CONVENTIONS.md`·`install-mac.sh`·`fixtures/golden/*`는 손대지 않는다**
- **완료 기준**: TS-034~TS-036 충족. 변경이력 일시가 `YYYY-MM-DD HH:mm` (KST) + `(082)` 포맷
- **테스트**: TS-034, TS-035, TS-036
- **실행 방법**: sub-agent
- **의존**: Step 10

#### Step 12: `docs/` 갱신
- [x] 완료
- **소속 기능**: F-008
- **영역**: 문서
- **agent**: **PM 직접**
- **파일**: `docs/PROJECT.md`, `docs/ARCHITECTURE.md` (2파일)
- **작업 내용**: `docs/PROJECT.md` 변경이력 1행 추가 / `docs/ARCHITECTURE.md` `tools/` 표 code-scan 행(`:82`)에 매니페스트 샤딩·크기 상한 1문장 추가 + 변경이력 1행
- **완료 기준**: 두 문서 모두 `(Task 082)` 표기 포함 행이 추가됨
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 11

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → 2 → 3 | 픽스처가 있어야 테스트를 쓸 수 있다. 각 Step의 산출 디렉토리는 비중첩 |
| Step 3 → 4 | RED-first — 구현 전 실패하는 테스트가 존재해야 한다 (생성자≠구현자) |
| Step 4~9 **전부 순차, 단일 배치** | 6개 Step 전부 `opal/tools/code-scan/code-scan.js` **동일 파일**을 수정한다. 병렬 디스패치하면 후행 저장이 선행 편집을 덮어쓴다 |
| Step 5 → 6, 7, 8, 9 | `resolveShards`가 나머지 4지점의 유일한 진입점 — 봉인 헬퍼가 먼저 존재해야 한다 |
| Step 8 → 9 | 둘 다 `_shards` 예약어·크기 상한을 다루므로 순차 편집으로 충돌을 피한다 |
| Step 9 → 10 | 구현 완료 후 전량 검증 |
| Step 10 → 11 → 12 | 동작 확정 후 문서화, 프레임워크 문서 확정 후 `docs/` 반영 |
| Step 11 ∦ Step 12 | 대상 파일이 다르지만 서술 정합을 위해 순차 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 샤드 합집합 해석 + `package` 3단 상속 | TS-001, TS-002 | 베이스+샤드 2 구성에서 전 파일 헤더 해석, 상속 티어가 `files > 소유 샤드 package > 베이스 package` |
| F-001 | 봉인 지점 1곳 | TS-003 | `code-scan.js`에서 샤드 파일 로딩·`byKey` 구성이 `resolveShards` 밖에 존재하지 않음 (grep 검사) |
| F-001 | 라벨 경로 안전 | TS-004 | `../`·`/`·대문자 라벨에서 `shard_declaration_invalid` exit 1, code-map 밖 쓰기 0건 |
| F-002 | 샤드 경로 라우팅 | TS-006, TS-007 | 보유 샤드 → 샤드 경로 + `shard` 라벨 / 미보유 → 베이스 경로 |
| F-002 | hook 자동 정합 | TS-008 | `code-map-hook.js` **무변경**으로 샤드 경로 미갱신을 감지 |
| F-003 | 정상 구성 무위반 | TS-010, TS-014 | 위반 0건 + exit 0. `files_key_removed` 0건 |
| F-003 | 샤드 고유 위반 3종 | TS-011, TS-012, TS-013 | 각 상황에서 **정확히 1건**씩 검출 |
| F-003 | 오탐 증폭 차단 | TS-016 | `orphan:dir_missing`이 샤드 수와 무관하게 1건 |
| F-004 | stale 오탐 차단 | TS-018 | `stale[]`에 샤드 0건 |
| F-004 | 멱등 + 자산 보존 | TS-019, TS-021, TS-022 | 재실행 바이트 동일, 삭제는 소유 샤드에서만, 중복 시 무쓰기 |
| F-005 | 상한 감지·비차단 | TS-024, TS-025 | 경로+실제 크기 열거, 다른 위반 0건이면 exit 0 |
| F-005 | 설정 오버라이드 | TS-026 | `manifestMaxBytes`가 기본값 20480을 덮어쓴다 |
| F-006 | 예약어 거부 | TS-028, TS-029 | `scaffold` exit 1 + `validate` 검출 |
| F-007 | 전량 GREEN + 골든 diff 0 | TS-030, TS-031 | 11개 테스트 파일 GREEN, 골든 8파일 바이트 동일 |
| F-007 | inline 무영향 | TS-032 | inline 모드 stdout·stderr 양축 동일 |
| F-008 | 버전·변경이력 | TS-034~TS-036 | v1.5.0 + `(082)` 표기 + KST 일시 포맷 |

### 5.2 회귀 테스트
- [ ] `node --test opal/tools/code-scan/tests/` 전량 GREEN (기존 10종 **무수정**)
- [ ] `tests/fixtures/golden/*` 8파일 바이트 동일 (**재캡처 금지**)
- [ ] 샤드 미선언 스코프에서 `target --json` / `scaffold --json` stdout 바이트 동일
- [ ] `code-map-hook.js` 무변경 + 무출력 계약(stdout·stderr 양축 0바이트) 유지
- [ ] `CODE_MAP_VERSION === 1` — 기존 매니페스트가 `unsupported_version`으로 차단되지 않음
- [ ] `resolveHeaderSource`·`isInScope` 봉인 구조 훼손 없음 (모드 판정 함수 신설 0개)

### 5.3 코드/문서 품질
- [ ] `code-scan.js` 상단 `@header` description·note가 샤딩 동작을 반영 (기록 위치는 **인라인** 유지 — `code-scan.js:9` note 근거)
- [ ] 하단 변경이력에 v1.5.0 행 + 태스크 번호 `(082)` — [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무
- [ ] `tools.md`·`header-rules.md` 변경이력 일시가 `YYYY-MM-DD HH:mm` (KST) + semver
- [ ] 신규 상수·함수가 English 네이밍 — [MUST] `docs/CONVENTIONS.md` §언어 규칙: "코드/변수/필드명 English"
- [ ] 샤드 라벨이 kebab-case 정규식으로 집행됨 — [MUST] `docs/CONVENTIONS.md` §네이밍 규칙
- [ ] 스키마에 미래 확장 훅 필드 0개 — TASK 확정 방향 #6 / [MUST] `opal/core/PRINCIPLES.md` §2
- [ ] 인접 코드 리팩터링 0건 — [MUST] `opal/core/PRINCIPLES.md` §3
- [ ] 플랫폼 조건문 추가 0건 — [MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리

### 5.4 보안
- [ ] 샤드 라벨 → 경로 파생에 path traversal 차단 (`SHARD_LABEL_RE`, TS-004)
- [ ] `_shards` 예약어 충돌 시 자산 덮어쓰기 차단 (TS-028)
- [ ] `~/.opal/` 배포 파일 직접 편집 0건 — [MUST] `docs/CONVENTIONS.md` §배포 경계
- [ ] `scaffold`가 중복 키에서 데이터를 자동 삭제하지 않음 (TS-022)
- [ ] 하드코딩된 토큰·시크릿 0건, `.env`·인증 파일 미포함 (신규 파일은 픽스처 JSON·테스트뿐)
- [ ] 커밋·스테이징 0건 — [MUST] `opal/core/references/opal-harness.md` §1 커밋 규칙

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 12개 | 복잡 |
| 변경 파일 수 | 8개 (코드 1 · 테스트 1 · 픽스처 2트리 · 문서 4) | 복잡 |
| 모듈 범위 | 다중 (도구 코드 + 테스트 + 프레임워크 문서 + `docs/`) | 복잡 |
| 작업 유형 | 대규모 개선 — 공용 CLI 도구의 해석·라우팅·검증·생성 4경로 동시 변경 | 복잡 |
| 외부 의존성 | 없음 (의존성 없는 단일 파일 Node.js) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 ── A1: opal-test-agent  (Step 1 → 2 → 3)        RED 자산
                     │
Batch 2 ── A2: opal-task-agent  (Step 4→5→6→7→8→9)      code-scan.js 단독 소유
                     │
Batch 3 ── A3: opal-test-agent  (Step 10)               전량 GREEN + 골든 회귀
                     │
Batch 4 ── A4: opal-task-agent  (Step 11)  →  PM 직접 (Step 12)
```

**그룹핑 근거**:
1. **파일 충돌 방지 (최우선)** — Step 4~9는 전부 `code-scan.js`를 수정하므로 **A2 단일 에이전트가 독점**한다. 이 파일을 다른 배치·에이전트가 동시에 건드리지 않는다.
2. **생성자 ≠ 검증자** — RED 작성(A1)과 구현(A2)을 분리해 self-confirming을 막는다. GREEN 판정(A3)도 구현자와 분리한다.
3. **병렬 없음** — 모든 Step이 선행 산출물에 의존하거나 동일 파일을 다룬다. 병렬화 여지가 없으므로 강제하지 않는다.

**산출 파일 수 점검** (단일 디스패치 3개 초과 금지 규칙):

| Step | 산출 파일 | 개수 | 비고 |
|------|---------|------|------|
| 1 | `fixtures/shard-repo/` 트리 | 8 | 픽스처 트리 1개 = 원자 단위. 분할하면 참조 불가한 중간 상태가 남는다 (PM 판단 사항) |
| 2 | `fixtures/shard-violations/` 트리 | 6 트리 | 동일 |
| 3 | `test-shard.js` | 1 | ✅ |
| 4~9 | `code-scan.js` | 1 | ✅ (6 Step이 같은 1파일 → 반드시 같은 배치·순차) |
| 10 | 없음 (검증 전용) | 0 | ✅ |
| 11 | `code-scan.js`, `tools.md`, `header-rules.md` | 3 | ✅ |
| 12 | `PROJECT.md`, `ARCHITECTURE.md` | 2 | ✅ |

> Step 1·2만 3파일을 초과한다. 픽스처 트리는 부분 생성 시 테스트가 참조할 수 없는 깨진 상태가 되므로 트리 단위를 원자로 유지하고, 대신 **트리별로 Step을 분리**해 비중첩을 보장했다.

### C-2. 스킬 요구사항
| 요구 | 기존 스킬 매칭 | 갭 |
|------|--------------|---|
| RED-first 테스트 작성 | `~/.opal/references/harness/red-first.md` §2·§3 | 없음 |
| 구현 | `op-dev-execute` | 없음 |
| 코드 헤더 작성 | `opal/core/references/harness/header-rules.md` | 없음 — 신규 파일 `test-shard.js`는 인라인 `@header` (이 프로젝트는 `.opal/code-map/index.json` 부재로 인라인, `code-scan.js:9`) |

동일 패턴이 3개 이상 Step에서 반복되지 않으므로 **신규 스킬 생성 없음**.

### C-3. 도구 요구사항
| 항목 | 값 |
|------|---|
| 런타임 | Node.js (프로젝트에 이미 존재) |
| 테스트 러너 | `node --test opal/tools/code-scan/tests/` — 내장 `node:test`, 신규 패키지 0개 |
| 배포 | `./scripts/install-mac.sh` — **소유자 승인 후** 실행 |
| MCP | 사용 없음 |

### C-4. 테스트 전략
| 계층 | 대상 | 명령 | 기대 |
|------|------|------|------|
| L1 | 판정 로직 (라벨 정규식·합집합·차단 필터) | `node --test opal/tools/code-scan/tests/test-shard.js` | TS-004, TS-011~TS-017, TS-025 |
| L2 | CLI 블랙박스 (4명령 × 샤드 구성) | `node --test opal/tools/code-scan/tests/` | TS-001~TS-029 |
| L2 회귀 | 골든 8커맨드 바이트 대조 | `node --test opal/tools/code-scan/tests/test-regression.js` | diff 0 (**재캡처 금지**) |
| L2 회귀 | hook 무출력 계약 | `node --test opal/tools/code-scan/tests/test-hook.js` | stdout·stderr 양축 |
| L3 | 배포본 실동작 | `~/.opal/tools/code-scan/run.sh version` → `v1.5.0` | 소유자 승인 후 |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 코드 | Node.js (의존성 없는 단일 파일 CLI, 2,180줄) | `op-dev-execute` |
| 테스트 | `node:test` + `spawnSync` CLI 블랙박스 + 파일 픽스처 | `red-first.md`, `opal-test-agent` |
| 배포 | `scripts/install-mac.sh` → `~/.opal/tools/code-scan/` | — |
| 훅 | PostToolUse (`code-map-hook.js`, `claude-hooks.json` 등록) | — |

> FE 화면 없음 — ui-designer / shadcn / context7 미사용. React·Python 커뮤니티 스킬 해당 없음.

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| — | 사용하지 않음. 외부 라이브러리 의존이 0이고 Node.js 표준 API(`fs`/`path`/`child_process`)만 사용하므로 context7 조회 대상이 없다 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | code-scan.js | `opal/tools/code-scan/code-scan.js` | 변경 본체 (v1.4.0, 2,180줄) — 전 설계 결정의 1차 근거 |
| D-2 | 소스 | code-map-hook.js | `opal/tools/code-scan/code-map-hook.js` | `decideTarget` 소비처 — 무변경 판정 근거(`:79-80`, `:145-149`) |
| D-3 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 배포 경계·변경이력 의무·네이밍·@header·Citation 규칙 |
| D-4 | 설계 | @header 규칙 | `opal/core/references/harness/header-rules.md` | 기록 위치 판정 3단 폐쇄 도메인 / 워커 권한 경계 / 테스트 파일 선택 필드 |
| D-5 | 설계 | 선행 태스크 080 | `tasks/080-260801-opd-헤더소스-단일화/PLAN.md` | 판정 지점 1곳 봉인 설계 선례 (`resolveHeaderSource`·`isInScope`) |
| D-6 | 설계 | 도구 레지스트리 | `opal/core/references/tools.md` | code-scan 절 갱신 대상 + `reason`/`write_to` 폐쇄 도메인 명문(`:241-247`) |
| D-7 | 설계 | 헌법 | `opal/core/PRINCIPLES.md` | §2 Simplicity First(U-3 미채택·스키마 최소화) / §3 Surgical Changes |
| D-8 | 기획 | 태스크 요구사항 | `tasks/082-260803-opds-코드맵-매니페스트-샤딩/TASK.md` | 확정 방향 #1~#10, 미확정 U-1~U-4, F-1~F-8 AC |
| D-9 | 소스 | 테스트 자산 | `opal/tools/code-scan/tests/` | 회귀 가드 기준 — 골든 8커맨드(`test-regression.js:90-97,507-509`), 픽스처 패턴(`test-validate.js:56-80`) |
| D-10 | 소스 | 배포 스크립트 | `scripts/install-mac.sh` | 무변경 판정 근거(`:1177-1181`) |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | **하위호환 범위 해석 차이** — TASK §제약 조건은 "모든 명령 바이트 동일"이라 하지만 F-5는 `validate` 출력 확장을 요구한다 (§1.6 M-2) | F-005, F-007 | 중 | 바이트 동일성 보증 대상을 **조회 8커맨드 + `target` + `scaffold` stdout**으로 명시 확정. `validate`는 `counts.manifest_oversize` 1키만 추가. 080이 `headerSource`를 무조건 추가한 선례(`code-scan.js:2020-2022`)와 동일 성격. **PM 승인 대상** |
| R-2 | **합집합 판정 누락 시 대규모 오탐** — `code-scan.js:1957-1967`을 매니페스트별로 남겨두면 샤드마다 전량 오탐 (H-1) | F-003 | **높음** | 구조 패스를 베이스 그룹 단위 3 Phase로 **재구성**(§3.3.2). TS-010·TS-014로 "정상 구성 위반 0건"을 직접 단언 |
| R-3 | **자산 소실** — scaffold 버킷 분배 오류나 중복 자동 해소 시 워커 기입 서술이 삭제 (H-3) | F-004 | **높음** | 중복 검출 시 디렉토리 전체 skip(§3.4.2 (B) 가드 1). TS-022가 mtime·내용 무변화를 단언. `--dry-run` 우선 검증 권고 |
| R-4 | **`target` 신규 실패 표면** — `decideTarget`이 처음으로 매니페스트를 읽어 파손 자산에서 exit 1 (H-5) | F-002 | 중 | 파손된 지도에서 기록 위치를 판정할 수 없으므로 exit 1이 올바른 응답. hook은 try/catch로 흡수(`code-map-hook.js:145-149`). `tools.md`에 명시 |
| R-5 | **상한 기본값 근거 부족** — 실측 1개 프로젝트뿐 (U-1) | F-005 | 중 | 비차단 채택(U-2)으로 오탐 비용을 알림 수준으로 제한 + `manifestMaxBytes` 설정 키로 프로젝트별 흡수. ③ 차단 전환은 별도 태스크 |
| R-6 | **inline 모드 `inline_shadowed` 축소** — inline에서 샤드 해석을 막으므로 샤드에 든 엔트리는 `conflict` 판정에서 빠진다 (§1.6 M-1) | F-001, F-003 | 낮음 | TASK §제약 "inline 모드 무영향"을 우선한다. inline + 샤드 자산 병존은 이미 `code-scan.js:1904-1907`이 stderr로 경고하는 설정 불일치 상황이다 |
| R-7 | **`_shards` 조용한 덮어쓰기** — 동명 소스 디렉토리 (H-7) | F-006 | 중 | `scaffold` 전용 에러 코드 exit 1 + `validate` `reserved_name`. TS-028·TS-029 |
| R-8 | **`CODE_MAP_VERSION` 오상향** — 상향 시 전 자산 즉시 차단 (H-10) | F-001 | **높음** | PLAN §3.8.2에 "1 유지"를 명문화하고 TS-005로 단언. Step 4 작업 내용에 "건드리지 않는다" 명시 |
| R-9 | **봉인 훼손** — 급할 때 소비처마다 샤드 로딩을 인라인으로 복제할 유혹 | F-001 | 중 | 봉인 검사를 QA 항목화(§5.1 F-001 2행) — `code-scan.js`에서 샤드 파일 로딩·`byKey` 구성이 `resolveShards` 밖에 없는지 grep 검사 |
| R-10 | **문서-코드 drift** — 도구 동작 변경이 `tools.md`·`header-rules.md`에 반영되지 않음 | F-008 | 낮음 | Step 11·12를 별도 Step으로 분리하고 TS-034~TS-036으로 산출물 검사 |

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-03 | PLAN.md 최초 작성 — 기능 8종 설계, U-1~U-4 결정(20480 바이트 / 비차단 / 글롭 미채택·베이스 기본 / 선언 순서 첫 승리), 리스크 가설 10종, 실행 체크리스트 12 Step (Task 082) |
| 2026-08-03 | 목표-커버 게이트 gaps 반영 — Step 2 픽스처 SSOT를 `TEST-SCENARIO.md` §2.1로 이관(`oversize-shard`·`shard-multi-scope`·`shard-goal` 추가), Step 3 작성 범위를 시나리오 S-1~S-26 전량으로 확정. R-1(하위호환 보증 범위) PM 승인 (Task 082) |
