# RED-EVIDENCE — 태스크 077 (코드 헤더 작성층 신설)

> 작성: opal-test-agent (mode: red) | Phase 1 RED — Step 2·3·4
> 작성자≠구현자 원칙(`~/.opal/references/harness/red-first.md` §2) 준수 — 본 파일 작성자는 GREEN(구현)을 수행하지 않는다.

---

## 1. 실행 명령

```bash
# 개별 파일 실행
node --test opal/tools/code-scan/tests/<파일명>.js

# 전체 실행 — 환경 노트 참조(§4)
node --test opal/tools/code-scan/tests/*.js
```

- cwd: 저장소 루트(`/Volumes/Data/AIStudio/workspace/ai-framework`)
- Node 버전: v25.8.2
- 실행 방식: `node:test` + `node:assert/strict` + `spawnSync` CLI 블랙박스(mock/monkeypatch 0건, 실 파일시스템 픽스처 + 실 subprocess만 사용)

---

## 2. 전체 결과 요약 (RED 확인)

| 파일 | 총 테스트 | PASS | FAIL | exit code |
|------|---------|------|------|-----------|
| test-resolve-header.js | 17 | 1 | 16 | 1 |
| test-discover.js | 5 | 1 | 4 | 1 |
| test-scaffold.js | 6 | 1 | 5 | 1 |
| test-target.js | 6 | 0 | 6 | 1 |
| test-validate.js | 17 | 0 | 17 | 1 |
| test-feature.js | 5 | 1 | 4 | 1 |
| test-hook.js | 7 | 0 | 7 | 1 |
| test-regression.js | 18 | 13 | 5 | 1 |
| **합계** | **81** | **17** | **64** | **1 (전체 스위트)** |

**`node --test opal/tools/code-scan/tests/*.js` 전체 실행 exit code = 1 (RED 확인 — 신규 기능 테스트가 실패한다).**

---

## 3. PASS 17건의 성격 — "우연한 통과"가 아님을 확인

Step 4 완료 기준(PLAN §4.2 Step 4): *"`test-regression.js`의 골든 대조는 이 시점에 **통과**해야 한다(기준선 유효성 확인)."* 이에 따라 PASS 17건은 다음 두 그룹으로 전량 설명된다 — 신규 기능(discover/scaffold/target/validate/feature/resolveHeader/code-map-hook)에 대한 assertion은 **단 1건도 PASS하지 않는다**.

### (A) `test-regression.js` 기준선 유효성 그룹 — 13건 PASS (의도된 PASS)
- 8커맨드 골든 바이트 동일 회귀(TS-006/043) 9건 — **변경 전 코드로 캡처한 골든**이므로 변경 전 코드로 재실행하면 당연히 PASS. GREEN 구현 후에도 이 그룹은 계속 PASS해야 한다(제약② 하위호환 보증).
- 픽스처 이중 격리(TS-052/053) 2건 — Step 1(`.opal/code-scan.json` 선결)이 이미 완료되어 있어 PASS.
- `.gitignore` code-map 예외(TS-055) 1건 — Step 1에서 이미 반영되어 PASS.
- 신규 테스트 파일 8종 `@header` 자산화(TS-057) 1건 — 이 RED 테스트 파일들 자체가 이미 `@header` JSON 블록을 보유하므로 PASS.

### (B) 각 파일의 "대조군" 성격 assertion — 4건 PASS
- `test-resolve-header.js` S-17/TS-046: "stdout이 유효 JSON이어야 함" — `scan --json`은 신규 기능과 무관하게 이미 유효 JSON을 출력하므로 자연 PASS(회귀 안전망 성격).
- `test-discover.js` TS-014(dry-run 부분): "`--dry-run` 실행 후 파일이 생성되지 않아야 함" — `discover` 명령 자체가 없어 아무 파일도 안 쓰는 것이 우연히 기대와 일치. TS-011/012/013/014(index_exists)는 모두 FAIL로 핵심 신규 기능은 RED가 정확히 잡힌다.
- `test-scaffold.js` TS-019: "scaffold 실행 후 소스 파일 mtime·내용 무변화" — 명령 부재로 아무것도 안 건드리는 것이 우연히 계약과 일치(이 불변식은 GREEN 이후에도 항상 참이어야 하는 설계 요구사항이라 의도적으로 유지).
- `test-feature.js` TS-037(인자 누락): "`feature` 인자 없이 호출 → exit 1 + usage 메시지" — 미지 커맨드 처리 경로가 우연히 exit 1을 반환. 핵심 기능(TS-035/036/037 cross-scope 조회) 4건은 FAIL로 RED가 정확히 잡힌다.

즉 PASS 17건 전부가 "이미 완료된 선결 작업의 유효성" 또는 "명령 부재로 인해 우연히 계약과 일치하는 무동작 대조군"이며, discover/scaffold/target/validate/feature/resolveHeader(5단 상속·경로 사상·headerSource)/code-map-hook 중 어느 것도 실제로 구현되어 통과한 것이 없다.

---

## 4. 환경 노트 — `node --test <디렉토리>/` 형태 미동작 (Node v25.8.2)

PLAN §3.12.2(H)이 명시한 실행 명령 `node --test opal/tools/code-scan/tests/`(디렉토리 경로, trailing slash)는 **이 환경의 Node v25.8.2에서 `MODULE_NOT_FOUND`로 즉시 실패**한다(디렉토리 인자를 test 파일로 잘못 resolve). 아래 세 변형 모두 동일하게 실패함을 확인했다:
```
node --test opal/tools/code-scan/tests
node --test opal/tools/code-scan/tests/
node --test ./opal/tools/code-scan/tests
```
**동등하게 동작하는 대체 명령**(쉘 glob 전개로 8개 파일을 개별 인자로 전달):
```
node --test opal/tools/code-scan/tests/*.js
```
위 명령으로 8개 파일 전량이 discover되어 정상 실행됨을 확인했다(§2 표). GREEN 워커·Step 19 검증 시 이 환경 노트를 참고할 것 — `code-scan.js` 구현과는 무관한 Node 런타임 동작이며 PLAN 설계를 변경할 필요는 없다(테스트 실행기 호출 관례의 문제일 뿐, 산출물 자체는 PLAN 그대로).

---

## 5. 파일별 실패 상세 (요약 — 전체 스택트레이스는 실행 로그 참조)

### test-resolve-header.js (16 FAIL)
- 스키마 위반 3건(TS-002 ×2, TS-003 ×2, manifest_parse_failed) — `unsupported_version`/`invalid_index`/`manifest_parse_failed` 판정 자체가 없어 전부 실패.
- 5단 상속 5케이스(TS-004) 전부 실패 — `_source` 키 자체가 존재하지 않음.
- 혼재 파일 인라인 단독 승리(TS-005) 실패 — 동일 사유.
- 단일 파일 역매핑(TS-007) 실패 — `scan <file>`이 code-map을 조회하지 않아 결과 0건(PM Gate 8번 파손 재현).
- `mirrorPathForDir` 직접 호출(TS-008) 실패 — `module.exports` 자체가 없음(require 시 `main()`이 즉시 실행됨).
- `layerRules` tie-break(TS-009) 실패 — 동일 사유(code-map 미해석).
- `headerSource` 스위치(S-17) 부분 실패 — 지도 유래 헤더 자체가 없음.
- package tier `depends` 상속 스냅샷(S-20/H-2) 실패 — `depends` 명령이 인라인 헤더만 참조.

### test-discover.js (4 FAIL)
- `discover` 서브명령 자체가 `commands` 테이블에 없어 전부 "Unknown command" exit 1.

### test-scaffold.js (5 FAIL)
- `scaffold` 서브명령 부재로 매니페스트 생성·멱등·보존·pruned·mirror_collision 거부 전부 미검증.

### test-target.js (6 FAIL, 0 PASS)
- `target` 서브명령 부재 — 4단 판정(readonly_repo/inline_exists/new_file/legacy_no_header) 전부 실패.

### test-validate.js (17 FAIL, 0 PASS)
- `validate` 서브명령 부재 — 5종 위반 검출, 커버리지 합산, `--changed`, exports 대조 계약, draft 정책, 워커 권한 경계(F-007) 전부 실패.

### test-feature.js (4 FAIL)
- `feature` 서브명령 부재 — cross-scope 조회, `--scope` 제한 전부 실패.

### test-hook.js (7 FAIL, 0 PASS)
- `opal/tools/code-scan/code-map-hook.js` 파일 자체가 존재하지 않아 `spawnSync`가 `ENOENT`를 반환 — 조기 이탈 9단, fail-safe, `claude-hooks.json` additive 배선 전부 실패.

### test-regression.js (5 FAIL — F-011 문서 그룹만)
- `header-rules.md`에 "별도 도구 없음" 문구 잔존(TS-048), 4단/3단/권한경계 3표 부재(TS-049), 6문서 변경이력 `(077)` 미기재(TS-047), `brain-tool/README.md`·`opal-harness.md` §9 미정합(TS-051), `pm-review-gate.md` 8·14번 항목 미반영(S-21 고유) — Step 15~18(F-011, 문서 갱신)이 아직 수행되지 않았으므로 전부 예상된 RED.

---

## 6. 산출물 목록 (Step 2·3·4)

### Step 2 — 픽스처 트리 (`opal/tools/code-scan/tests/fixtures/`)
- `codemap-repo/` — 6조건 자기완결 픽스처(5단 이상 깊은 경로, stripPrefix 상용구, 앵커 2종(svc pom.xml 기반/web 1-depth 디렉토리), readonly 스코프(legacy), 컴파일 산출물 중복 사본(target/ 제외 확인), 인라인·지도 혼재 파일(AdminHome.tsx))
- `violations/` — `orphan`(file_missing+dir_missing) · `uncovered`(no_entry+incomplete) · `conflict-inline-shadowed` · `conflict-mirror-collision` · `draft` · `exports-missing`(존재/미존재/주석내존재 3케이스) · `worker-scope-dir` · `worker-scope-layer`(layer/domain/module 침범) · `worker-scope-files`(추가/삭제) · `clean`(위반 0 대조군)
- `schema/` — `version-mismatch` · `missing-scopes` · `missing-root` · `manifest-parse-failed` (F-001 스키마 검증용, TS-002/003 + S-4 pt.2)
- `tiebreak/` — `order-a`/`order-b` (H-12 동률 layerRules, 배열 순서만 상이)
- `legacy-repo/` — code-map 부재 트리(인라인 헤더만, 골든 캡처 대상)
- `golden/` — 8커맨드 `--json`/텍스트 출력 골든 8파일(변경 전 코드로 비TTY 캡처, 재현성 확인 완료 — 2회 캡처 바이트 동일)

### Step 3 — 골든 캡처
- `scan.json`, `domain.txt`, `layer.txt`, `search.json`, `exports.json`, `summary.txt`, `depends.txt`, `missing.txt` — 전량 **변경 전(현재) `code-scan.js`**로 `legacy-repo` 픽스처를 대상으로 비TTY 캡처. 재캡처 시 바이트 동일 확인(재현성 검증 완료, §2 참조).

### Step 4 — RED 테스트 8파일 (`opal/tools/code-scan/tests/`)
`test-resolve-header.js` · `test-discover.js` · `test-scaffold.js` · `test-target.js` · `test-validate.js` · `test-feature.js` · `test-regression.js` · `test-hook.js`
— 전 파일 `header-standard.md` §3 JSON `@header`(`layer: test`, `task: "077"`, `scenarios: [...]`) + TC↔TS-ID↔S-ID 매핑 표 주석 + `[RED 기대]` 인라인 주석 보유.

---

## 7. 하네스 준수 확인

- [x] RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록 — 본 문서 §2.
- [x] RED 작성 주체(opal-test-agent)와 구현 주체(op-dev-execute 워커, 별도 디스패치) 분리 — `code-scan.js`/`code-map-hook.js`/`run.sh`를 일절 수정하지 않았다.
- [x] `test-regression.js`의 골든 대조는 기준선 유효성 확인을 위해 의도적으로 PASS 상태(§3).
- [x] 대역 객체·몽키패치 0건 — 전량 실 파일시스템 픽스처 + `spawnSync` CLI 블랙박스.
- [x] PLAN.md에 명시된 파일 외 생성/수정 없음 — `opal/tools/code-scan/tests/**`, 본 `RED-EVIDENCE.md`만 신규 생성.
