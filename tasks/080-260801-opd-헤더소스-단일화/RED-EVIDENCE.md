# RED-EVIDENCE: 헤더 소스 단일화 (080)

> 기록일: 2026-08-02 13:18 KST | 기록 주체: PM(오케스트레이터)
> 근거 규칙: `~/.opal/references/harness/red-first.md` §1 — "RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지."

## 1. 실행 증거

```
$ node --test "opal/tools/code-scan/tests/*.js"

ℹ tests 191
ℹ suites 0
ℹ pass 111
ℹ fail 80
ℹ skipped 0

EXIT=1
```

**exit code 1 ≠ 0 → RED 성립.**

## 2. 파일별 분포

| 테스트 파일 | tests | pass | fail | 성격 |
|------------|-------|------|------|------|
| `test-header-source.js` | 12 | 1 | **11** | 신규 — 게이트·2택·우선순위 2층 |
| `test-scope-filter.js` | 24 | 2 | **22** | 신규 — 단일 필터 계약·스코프 우선순위·목표 검증(TS-072~074) |
| `test-target.js` | 13 | 2 | **11** | 재작성 — 모드 직결·`out_of_scope`·`readonly` 반전 |
| `test-regression.js` | 36 | 22 | **14** | 재작성 — 문서 산출물 검사·골든·`auto` 잔존·TS-070 봉인 |
| `test-hook.js` | 15 | 9 | **6** | 재작성 — fail-safe 3케이스 + 양성 대조군 |
| `test-discover.js` | 12 | 7 | **5** | 재작성 — 산출물 `readonly`/`headerSource` 0건 |
| `test-validate.js` | 34 | 29 | **5** | 재작성 — 모드별 커버리지·검출기 필터 |
| `test-feature.js` | 9 | 6 | **3** | 재작성 — 게이트 차단·인자 소비 |
| `test-scaffold.js` | 9 | 7 | **2** | 재작성 — `inline` no-op |
| `test-resolve-header.js` | 27 | 26 | **1** | 재작성 — 077 자산 승계·`manifest` 부재 경고 |
| **합계** | **191** | **111** | **80** | |

## 3. 실패 분류 — 80건 전량 "구현 부재"

RED는 "구현이 아직 없어서" 실패해야 하며, "테스트가 잘못 짜여서" 실패하면 안 된다. 각 배치가 실패 사유를 코드 레벨로 확인했고 PM이 표본 검증했다.

| 실패 원인 | 대표 증거 |
|----------|----------|
| 전 명령 차단 게이트 부재 | 미설정 트리에서 13커맨드가 `exit 0` |
| `--header-source` 미파싱 | 플래그가 `commandArg`로 흡수되어 `targetPath='inline'`이 됨 |
| 객체 형식 `scopes` 미지원 | `getSearchPaths`(`code-scan.js:294`)에서 `ERR_INVALID_ARG_TYPE` |
| `isInScope` 미존재 | 정의 0곳 · `scaffold`가 `VendorLegacy.java`를 양쪽 매니페스트에 등재 |
| `resolveScopeIn` 부재 | 4파일 전부 사전순 `order-svc` 귀속 · `scope_ambiguous` 미발동 |
| `decideTarget` 구계약 | `{"write_to":"manifest","reason":"legacy_no_header"}` 반환 |
| `resolveHeaderSource` 부재 | TS-070 화이트리스트가 판정 지점 0곳을 확인 못 함 |
| hook 조기 이탈 미구현 | 미설정에서 `legacy_no_header` 경고를 그대로 출력 |
| `warnOnce` 미구현 | `manifest` + index 부재 시 경고 0줄 |
| `auto` 리터럴 잔존 | `code-scan.js:45`·`:108`·`:198-201` |
| 문서 미갱신 | 규칙 문서 5종·`docs/` 3종 변경이력·`reason` 3값·`auto` 서술 |
| `.gitignore` 예외 미채택 | `git check-ignore .opal/code-scan.json` → `exit 0` |

## 4. 통과 111건의 성격

통과가 결함이 아니다. 세 부류다.

1. **의도된 회귀 가드** — 이번 변경으로 **깨지면 안 되는** 기존 계약. 예: TS-007(`--help`/`--version` exit 0) · TS-010(문자열 `scopes` 20종 무수정 동작) · TS-018(tiebreak 사전순 판정 불변) · TS-047(`.opal/code-map/index.json` 무시 유지) · TS-060(골든 8종 바이트 동일 — 기준선 유효성).
2. **봉인용 부정 단언** — 아직 존재하지 않는 것이 없음을 확인. 예: TS-071(`discover` 산출물에 `headerSource` 키 0건).
3. **077 자산 중 신 계약과 무관한 부분** — 그룹 A 오버레이 이전분 등.

## 5. RED 작성 중 발견·수정된 테스트 결함 4건

작성자가 스스로 잡아 고친 것들이다. 남았다면 GREEN 단계에서 **거짓 신호**를 냈을 항목이다.

| # | 결함 | 조치 |
|---|------|------|
| 1 | TS-007(회귀 가드)에 신규 계약 단언이 섞여 구현 부재로 붉어짐 | 별도 케이스로 분리, TS-007은 순수 회귀 가드로 복구 |
| 2 | 077 TS-045의 `module` 단언이 `deriveStem`(파일명 파생)과 **우연 일치**해 인라인 유출과 구분 불가 | `note` 단언으로 교체 + 사유 주석 |
| 3 | **TS-062 위양성** — `node --test`가 심는 `NODE_TEST_CONTEXT`를 손자 러너가 물려받아 실제로는 fail 76인데 **84ms에 exit 0** 반환 | 자식 env에서 변수 제거(6.4초·exit 1로 정상화) + `T080_SUITE_CHILD` 재귀 가드 |
| 4 | TS-052 범위 과대 — 태스크와 무관한 기존 문장(`tools.md:340`)까지 위반으로 잡아 범위 밖 수정을 강요 | AC 문구("**신규** 기재 0건")대로 `git diff HEAD` 추가 줄 + 문맥 줄로 한정 |

## 6. 판별력 보강 2건

"무출력 확인" 계열은 트리가 원래 조용한 것과 구분되지 않는다. 작성자가 **양성 대조군**을 붙였다.

- **TS-036 / TS-040~043(hook)** — 같은 트리·같은 모드에서 매니페스트 엔트리 1개를 삭제해 경고가 실제로 발생함을 먼저 보인 뒤 무출력을 단언한다. TS-042(경고 정상 출력, 077 TS-038 계승)를 앞에 배치해 무출력 3종이 공허해지지 않게 고정했다.
- **TS-074(전역 반전)** — 커밋 4파일이 전부 clean이라 `manifest` 모드에서도 hook이 조용히 이탈해 반전 관측이 불가능했다. 두 임시 복사본에 **동일하게** 미등재 in-scope 파일 1개를 추가했다. 두 트리의 유일한 차이는 여전히 `headerSource` 한 줄이다.

## 7. 테스트 불변성 계약 [MUST]

[MUST] `red-first.md` §3: "GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커."

- Step 3~14 동안 `opal/tools/code-scan/tests/*.js`를 **편집하지 않는다.**
- 테스트를 약화·삭제·조건 완화하여 통과시키는 행위는 reward hacking이며 금지된다.
- 테스트 자체가 틀렸다고 판단되면 **고치지 말고 PM에 블로커로 보고**한다. 수정 여부는 PM이 판정한다.
- 작성자(`opal-test-agent`) ≠ 구현자(`opal-task-agent`) 분리는 Step 14까지 유지된다.

## 8. 구현자에게 전달되는 사전 경고 2건

RED 작성 중 드러난 것으로, 모르면 **테스트 결함으로 오인**할 항목이다.

1. **`headerSource` 변수명 금지** — `main()`의 지역 변수와 중간 전달 함수(`scanAll`·`cmdDiscover`·`cmdScaffold`·`cmdTarget`·`cmdValidate`)의 파라미터는 **`mode`** 등 다른 이름을 쓴다. TS-070 화이트리스트가 허용 3구간(`resolveHeaderSource`·`loadConfig`·`parseArgs`) 밖의 `headerSource` 토큰을 전부 위반으로 잡으며, 이는 의도된 규율이다. PLAN §3.1.2 (C)(D)를 이에 맞춰 갱신했다(PM, 2026-08-02).
2. **`code-scan-management.md:81` 파급** — 이 문서가 도구의 `note` 문자열("OWNER REVIEW REQUIRED — readonly/…")을 인용하고 있어, Step 6(`code-scan.js`에서 `readonly` 0건)과 함께 이 인용도 갱신해야 TS-051이 통과한다.

## 9. PM 판정

| 항목 | 결과 |
|------|------|
| exit code ≠ 0 | ✅ exit 1 |
| 실패가 구현 부재 사유 | ✅ 80건 전량, 표본 검증 완료 |
| 테스트 자체 결함 혼입 | ✅ 4건 발견·수정 완료 |
| 작성자 ≠ 구현자 | ✅ `opal-test-agent` 4배치 / 구현은 `opal-task-agent` 예정 |
| 픽스처·소스 무변경 | ✅ `git status` 확인 — 변경은 `tests/*.js`와 Step 1 픽스처뿐 |

**GREEN(Step 3~) 진입 가능.**

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-02 13:18 | RED 증거 초기 기록 — 191 tests / fail 80 / exit 1, 4배치 통합 (080) |
