# DONE: 헤더 소스 단일화 — `headerSource` 기준 통일 + 스코프 `include`/`exclude`

> 완료일: 2026-08-02 18:04 KST | 스킬: `//opd --agentic` | 선행: 077(코드맵 헤더 작성층)

---

## 1. 무엇을 했나

077이 만든 헤더 작성층은 기록 소스를 **파일마다** 골랐다(`auto`). 파일에 인라인 `@header`가 있으면 인라인, 없으면 매니페스트. 여기에 스코프 단위 `readonly: true`가 겹치면 그 스코프는 무조건 매니페스트였다. 결과적으로 **한 프로젝트 안에 두 소스가 공존**했고, 어느 쪽이 진실인지는 파일별로 달랐다.

080은 이 판정을 **전역 단일 키 하나**로 접었다.

- `.opal/code-scan.json`의 `headerSource` = `inline` \| `manifest` **2택**
- **스코프별 오버라이드 없음** — `index.json`·`code-scan.json` 양쪽 `scopes[].headerSource`는 무시 + 안내 1줄
- **`auto` 완전 제거** — 혼재를 허용하는 값이 남으면 이번 결정이 무력화된다
- **미설정·무효값 = 전 명령 차단**(exit 1) — 암묵 기본값 금지
- 우선순위는 **2층**: CLI `--header-source` > 전역 config

부수로 `scopes`에 객체 형식(`root`/`include`/`exclude`)을 도입해 **파일 집합 필터**를 신설했다. 스코프가 "어느 소스로 쓸지"를 정하던 자리를 "어느 파일이 내 것인지"로 바꾼 것이다.

---

## 2. 완료 산출물

| 구분 | 내용 |
|------|------|
| 도구 | `code-scan` **v1.3.3 → v1.4.0** (`code-scan.js`) · `code-map-hook.js` v1.0 → **v1.1.1** |
| 규칙 문서 5종 | `header-standard.md` · `harness/header-rules.md` · `harness/pm-review-gate.md` · `pm/code-scan-management.md` · `tools.md` |
| `docs/` 3종 | `CONVENTIONS.md`(판정 근거 교체) · `ARCHITECTURE.md` · `PROJECT.md` |
| 저장소 설정 | `.opal/code-scan.json`에 `headerSource: inline` · `.gitignore`에 `!.opal/code-scan.json` 예외 |
| 테스트 | 신규 2파일(`test-header-source.js`·`test-scope-filter.js`) + 기존 8파일 재작성 · 픽스처 20종 + 신규 트리 2종 |
| 검증 | **194 tests / pass 194 / fail 0 / exit 0** |

---

## 3. 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| D-1 | 도구는 비대화형 유지 + `--header-source` 플래그 | OPAL 도구 12종이 전부 비대화형 JSON CLI다. 대화형 프롬프트는 hook·서브에이전트·CI에서 정지를 일으킨다 |
| D-2 | 스코프별 오버라이드 **완전 제거**(전역 단일 키) | 실측 결과 `readonly:true` 실사용 0건. 실사용 없는 예외를 위해 우선순위 3층 + 파일 단위 판정 함수를 유지하는 것은 과설계 |
| D-3 | `auto` 완전 제거 (2택) | 혼재를 허용하는 값이 남으면 "동시 관리 금지" 결정이 무력화된다 |
| D-4·D-5 | 미설정 = 에러 거부, 차단 범위 = **전 명령** | 암묵 기본값 금지. 기존 프로젝트 동시 정지라는 파급을 사전 고지하고 소유자가 그 상태로 선택 |
| D-6 | `readonly`는 **무시 + 안내**(흡수 아님) | `manifest`로 흡수하는 코드가 남으면 전역 단일 키 결정이 조용히 파괴된다(가설 H-8) |
| — | 077 제약②("기존 프로젝트 동작 변화 0") **파기** | D-3~D-5의 직접 결과. 완료기준을 "**명시 설정 후** 동작 변화 0"으로 재정의 |

**봉인 2종** — 판정을 한 곳에 가두고 테스트로 고정했다.
- 모드 판정 = `resolveHeaderSource` **1곳** (TS-070, 화이트리스트 4단계 검사)
- 필터 판정 = `isInScope` **1곳** + 적용 5지점 (TS-013)

---

## 4. 목표 달성 실증

이 태스크의 성공은 "전역 값 하나를 뒤집으면 모든 경로가 함께 뒤집힌다"로 정의됐고, 반증 가능한 형태로 고정했다(TS-074 / S-19).

두 트리에 **동일한 편집을 먼저 가해** hook 관측 무대를 만든 뒤 `diff -ru`로 유일 차이가 `headerSource` 한 줄임을 고정하고 측정:

| 경로 | `inline` | `manifest` |
|------|---------|-----------|
| `target` | `write_to:inline` / `header_source_inline` | `write_to:manifest` / `header_source_manifest` + scope·manifest·key |
| `scaffold` | no-op (`skipped`) | `updated:2`, 엔트리 생성 |
| `validate` | coverage 0/4 (0%) | coverage 3/4 (75%) |
| `scan` | 0건 | 4건, `_source` 매니페스트 유래 |
| `hook` | stdout **0바이트** | stdout **433바이트** 경고 |

hook은 재판정하지 않고 `ctx.headerSource`를 공유해 따라온다 — 단일 판정 지점 설계가 실동작으로 확인됐다.

---

## 5. 검증 결과

| 항목 | 결과 |
|------|------|
| 전체 스위트 | **194 / pass 194 / fail 0 / exit 0** (RED 기준선: 191 / pass 111 / **fail 80**) |
| 교차 확인 | `env -u NODE_TEST_CONTEXT`로 10파일 개별 재실행 — 합계도 194/194 (exit-code 마스킹 위양성 배제) |
| 자기 게이트 | `validate --changed` 61경로 `ok:true` · `newly_uncovered` 0 · `worker_scope_violation` 0 |
| 봉인 6종 | 소스 `auto` 1개소(마이그레이션 힌트) · 소스 `readonly` 3건(정규화 입력 키만) · 문서 `auto`/`readonly` 유효값 서술 0 · 판정 지점 각 1곳 |
| 골든 8종 | 077 대비 **차이 0** — mtime·`shasum`·`diff -r` 3중 교차로 "캡처 미실행" 위양성 배제 |
| TEST 시나리오 | **22/22 All Pass** (L1 11 · L2 10 · L3 1) |
| RED 봉인 | Step 3~14 전 구간 `tests/*.js` 편집 0건 (mtime으로 확인) |

**RED-first 준수**: 작성자(`opal-test-agent`) ≠ 구현자(`opal-task-agent`)를 끝까지 분리했다. RED 증거는 `RED-EVIDENCE.md`.

---

## 6. 실제로 잡힌 결함

### (1) 다축 TS ↔ 단축 Step 경계 불일치 — 3회

TS-005/006/069(Step 3) · TS-035/037(Step 5) · TS-030/033(Step 6)이 **한 케이스 안에 축이 다른 단언**(필터 축 + 모드 축, `readonly` 축 + 모드 축)을 담고 있어 어느 Step도 단독 완주가 불가능했다. 세 번 모두 워커가 **테스트를 고치지 않고 블로커로 보고**했고, PM이 PLAN §4.2에서 축별로 재기술해 Step 7(합류 지점)로 이관했다. 이관 7종은 Step 7에서 전량 GREEN.

### (2) hook 조기이탈 stderr 누출 — **픽스처는 통과했는데 실자산에서 깨졌다**

배포 직전 S-22 사전 점검에서 발견. `code-map-hook.js`의 ⑤ `loadCodeMap`이 모드 게이트보다 **먼저** 돌아 `normalizeIndexScope`의 폐기 키 안내가 stderr로 발화하고, 게이트는 그 뒤에 이탈했다.

- 실측: revup(폐기 키 28회)에서 신규 hook이 **stderr 295바이트/편집**, 배포본 077은 0바이트
- 미검출 사유: **TS-040~043이 stdout만 단언**했고 "폐기 키 보유 index × 조기이탈 모드" 조합 픽스처가 없었다
- 조치: 새 RED 사이클(TS-076, stdout+stderr 양축) → 게이트를 `loadCodeMap` 위로 재배치 → 6케이스 전부 stderr 0바이트, 대조군 `manifest`는 출력 유지

**픽스처 191/191 GREEN 상태에서 실프로젝트가 깨뜨린 사례다.** S-22를 수동 시나리오로 남겨둔 이유가 그대로 입증됐고, 배포 전에 잡혔다.

### (3) RED 작성 중 자체 발견·수정 4건

TS-062 위양성(`NODE_TEST_CONTEXT` 상속으로 fail 76인데 84ms에 exit 0) 등. 상세는 `RED-EVIDENCE.md` §5.

---

## 7. 잔여 미해결 (Known Issue)

### KI-1 `scaffold`가 `scope_ambiguous`를 집행하지 않는다

모호 스코프 트리에서 `target` exit 1 · `validate` exit 1 인데 **`scaffold`만 exit 0**이며 6엔트리를 두 매니페스트에 **교차 등재**한다.

- **읽기·판정 경로는 전부 막는 가드를 유일한 쓰기 경로가 통과시킨다**
- 오염 직후 `validate`가 `scope_ambiguous`로 차단하므로 침묵 오염은 아니다
- TASK F-1~F-13·PLAN 어디에도 배정이 없고, `include` 기반 모호성 자체가 080 신설분 — **설계 시 미인지된 신규 경계**
- RED TS 집합이 닫혀 있어 지금 고치면 테스트 없는 구현이 된다 → **후속 태스크 권고**(RED 먼저)

### KI-2 깨진 config 경로에 단언 없음

`test-hook.js:228`(`ts040c`)이 지나는 경로도 같은 stderr 누출이 있었고 재배치로 함께 닫혔으나, **아무 단언도 이를 고정하지 않는다**. 실행 증거만 확보(stdout·stderr 양축 0바이트). 회귀 가드가 필요하면 RED 1행 추가.

### KI-3 TS-052의 검사 축이 커밋 후 공허해진다

`git diff HEAD`의 추가 줄을 검사하므로, 커밋되면 그 축이 빈다. 통과는 유지되나 CLOSE 이후 가드 기능은 상실.

---

## 8. 개선 후보 (프레임워크 반영 대상)

**IMP-1 다축 TS 배정 규칙** — TS는 시나리오 단위, PLAN Step은 함수·파일 단위라 다축 TS는 어느 Step도 단독 완주가 불가능하다. 이번 태스크에서 **3회 재발**했다. PLAN 단계에서 "Step 완료 기준에 다축 TS를 배정할 때는 축별 부분 단언으로 쪼개 기재"를 `plan-guide.md`에 넣는 안. 소유자 판단 대상.

**IMP-2 code-scan 자연어 발현이 prose 지침에 머문다** — `opal-pm.md §13`이 상황→명령 매핑을 주지만 도구로 강제되지 않는다. 헌법 *"Enforce, don't just advise"* 기준으로 advise 쪽에 남은 지점. 재발 패턴 관측 시 태스크화.

---

## 9. 배포 및 파급

소유자가 `install-mac.sh`로 배포 완료(`~/.opal` code-scan **v1.4.0**, 프로젝트 소스와 `diff` 동일 확인).

D-4·D-5의 의도된 결과로 **기존 프로젝트가 즉시 차단**된다.

| 프로젝트 | 배포 전 | 조치 |
|---|---|---|
| ai-framework | `inline` | 정상 |
| **revup** | `auto` | ✅ **`manifest`로 전환 완료** — 인라인 0건/매니페스트 1,411건 실측 후 무손실 확인, 전환 후 coverage 100%·위반 0·조회 8커맨드 exit 0 |
| pointail | `auto` | ⏳ **인라인 9건 혼재** — 그냥 전환하면 9건이 조회에서 사라진다. 선등재 후 전환 필요(별건) |
| mams | 미설정 | ⏳ code-map 없음 → `inline` 지정 권고(별건) |

**077 코드맵 자산은 재작성 불요** — 080은 소스 선택 규칙만 바꿨고 매니페스트 스키마는 불변이다(골든 차이 0이 근거).

---

## 10. 커밋 시 주의

**[MUST] `git commit -am` / `git add -A` 금지.** 두 가지 이유로 잘못된 커밋이 된다.

1. **untracked 5경로가 조용히 누락된다** — `.opal/code-scan.json` · `tests/fixtures/mixed-scope/` · `tests/fixtures/mixed-scope-ambiguous/` · `tests/fixtures/golden/README.md` · 신규 테스트 2파일
   - 특히 `.opal/code-scan.json`이 빠지면 신규 clone·CI가 `header_source_unset`으로 즉시 멎는다. TS-046은 `.gitignore`만으로 GREEN이라 **이 누락을 잡지 못한다**
2. **동시 진행 중인 별개 태스크가 딸려간다** — `tasks/081-260802-opds-워커중단-복구프로토콜/`과 `opal/core/references/opal-harness.md`가 활성 상태다(080 파일 집합과는 무겁치지 않음)

또한 `.opal/brain/**`·`.opal/MEMORY.json`은 078/079의 선존 미커밋분이므로 080 커밋에서 제외한다.

---

## 11. 산출물 경로

```
tasks/080-260801-opd-헤더소스-단일화/
├── TASK.md              요구사항 F-1~F-13
├── ANALYSIS.md          독립 분석가 교차 검증 V-1~V-12
├── PLAN.md              설계 F-001~F-007 + 14 Step 실행 체크리스트
├── TEST-SCENARIO.md     시나리오 22종 + 실행 결과 + §7 판정(All Pass)
├── RED-EVIDENCE.md      RED 증거 — 191 tests / fail 80 / exit 1
├── SCENARIO-GATE-1~3.md 목표-커버 게이트 3회 반복
├── AGENTIC-LOG.md       PM 대행 일지 76건
└── DONE.md              이 문서
```

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-02 18:04 | 최초 작성 — 헤더 소스 단일화 완료 기록 (080) |
