# DONE: 샤드 분할 파이프라인 — 2축 판정 + 분할 집행 + 유도

> 완료일: 2026-08-04 22:36 (KST) | 스킬: opds | 모드: semi-agentic | code-scan v1.5.0 → **v1.6.0**

## 1. 무엇을 했나

082가 만든 "쪼개진 상태를 도구가 **이해**한다"에 이어, "쪼개는 행위를 도구가 **집행**한다"를 완성했다.

082는 과대 매니페스트를 탐지하고 한 줄 열거하는 데서 끝났다 — 누가 무엇을 어떻게 해야 하는지가 어디에도 없었고, 분할을 수행하는 서브명령이 0건이었다. 그래서 강제력을 차단으로 두든 비차단으로 두든 결말이 같았다(막혔는데 푸는 법이 없음 / 경고만 쌓임). 083은 **해결 경로를 먼저 만들었다.**

동시에 판정 자체를 정교화했다. 바이트 단독 기준은 "서술이 길어서 큰 것"과 "항목이 많아서 큰 것"을 구분하지 못해 나눌 의미 경계가 없는 매니페스트까지 열거했다. 파일 수 하한을 결합해 2축으로 만들었다.

## 2. 변경 내역

| # | 파일 | 변경 |
|---|------|------|
| 1 | `opal/tools/code-scan/code-scan.js` | v1.6.0. 신규: `resolveShardPolicy`(정책 3단 해석 봉인 1곳)·`loadGlobalSetting`/`resolveOpalHome`(전역 설정 로더)·`cmdSplit`(집행+제안)·`cmdInit`(설정 온보딩)·`loadWordDictionary`·`parseMdTable`. 폐기: `manifestMaxBytes(ctx)` 헬퍼 |
| 2 | `scripts/install-mac.sh` | `setting.json` 샤드 정책 시드 — `SEED_KEYS` 루프로 일반화(기존 `models` 조기 종료 구조가 기존 설치 환경에 정책 키를 영구 미시드하는 문제 해소) |
| 3 | `opal/core/setting.default.json` | `shardPolicy.maxBytes` 10240 / `minFiles` 40 |
| 4 | `opal/tools/code-scan/tests/test-shard-policy.js` | **신규** — 89 케이스 |
| 5 | `opal/tools/code-scan/tests/test-*.js` (11종) | `OPAL_HOME` 격리 주입 + 082 단언 이전 |
| 6 | `tests/fixtures/shard-policy/` | **신규** — 정책·가짜 홈 5종·분할 대상·사전 4종·`init` 3종 |
| 7 | `tests/fixtures/shard-{goal,violations}/` (8파일) | 구 위치 키 제거 + `code-scan.json` 정책 오버라이드로 흡수 |
| 8 | 참조 문서 6종 | `docs/PROJECT.md`·`docs/ARCHITECTURE.md`·`tools.md`·`harness/header-rules.md`·`opal-harness.md`·`pm/code-scan-management.md` |

서브명령 **13 → 15** (`split`·`init` 신설).

## 3. 설계 핵심

### 3.1 정책 3단 우선순위 — 판정 지점 1곳 봉인

```
{프로젝트}/.opal/code-scan.json  >  ~/.opal/setting.json  >  코드 상수(10240 / 40)
```

**셀 단위 머지** — 프로젝트에 `minFiles`만 적으면 `maxBytes`는 상위 단계 값이 유지된다. 이 3단 해석을 읽는 지점은 `resolveShardPolicy` **1곳**뿐이며, `DEFAULT_SHARD_POLICY`·`loadGlobalSetting`도 그 함수 본문 밖에서 참조하지 않는다(080 `resolveHeaderSource`·082 `resolveShards` 봉인 구조 계승).

전역 설정 부재·JSON 파손·키 부재·타입 위반 **4상태 전부 비차단 폴백**이다. `headerSource`의 미설정 전 명령 차단과 성질이 다르다 — 샤드 정책은 합리적 기본값이 존재하므로 추측 불가한 값이 아니다.

### 3.2 2축 판정

바이트 **초과(`>`)** AND 엔트리 수 **이상(`>=`)**. `size === maxBytes`는 초과가 아니다(082 off-by-one 계약 보존). 전면 비차단 — 초과만으로는 exit 0이다.

### 3.3 `split --plan` 5단계 제안 사다리

S1 첫 토큰 → S2 첫 2토큰 결합 → S3 전체 토큰 → S4 마지막 토큰 → S5 `depends` 공유. **각 단계는 직전 단계의 미분류분만 입력으로 받고, 앞 단계 배정은 후속 단계가 재배정하지 않는다** — 그래서 같은 입력에 같은 출력이 나온다.

잔여는 `unassigned`로 남긴다. **도구는 임의 배분하지 않고 "기타" 그룹도 만들지 않는다.** 의미 경계 확정은 사람의 몫이다(파일명 접두사 분류는 상위 18개 토큰이 198건만 덮고 90건이 기타로 남는다는 실측 근거).

표준단어사전은 **읽기 전용·옵셔널** 대조다 — 부재·파싱 실패·매칭 0건 3분기 전부 비차단. code-scan이 `.opal/` 밖 문서를 읽는 첫 사례이며, 호출은 `split --plan` 경로 **1곳뿐**이라 조회 8커맨드의 출력 바이트가 흔들리지 않는다.

### 3.4 `split` 집행 — 쓰는 유일한 명령

4단 파이프라인(사전 검증 → tmp 작성 → rename 커밋 → 사후 재검증). 실패 지점별 에러 코드 7종. 사후 재검증은 `resolveShards`를 비운 캐시로 다시 호출해 해석 로직을 복제하지 않는다. **엔트리 유실 0건이 절대 조건.**

### 3.5 `init` — 차단 게이트 **앞** 배치

080이 `headerSource` 미설정을 전 명령 차단으로 만들었는데 설정 파일이 생기는 정의된 경로가 없었다 — 구멍이 곧 막힘이 되는 게이트 순환이었다. `cmdInit`을 `main()` 차단 게이트 **앞** 분기에 배치해 순환을 끊었다. 비대화형(TTY 의존 0건), `headerSource`는 추론하지 않고 CLI 인자로 받는다.

## 4. 미확정 7건 결정 (TASK §미확정)

| # | 쟁점 | 결정 |
|---|------|------|
| U-1 | `split` 입력 형식 | 그룹 정의 파일(JSON) + stdin(`-`) 파이프. 292 엔트리를 CLI 인자로 넘기는 것은 비현실적 |
| U-2 | 제안 알고리즘 | **5단계 사다리**(단일 축 불채택 — 잔여 31%). 각 단계 잔여만 전달 |
| U-3 | 유도 진입점 | 위반 페이로드에 `recommendedShards` + `next` 명령 탑재. 전용 스킬·커맨드는 만들지 않음 |
| U-4 | 원자성·롤백 | tmp 작성 → rename 커밋. 실패 시 `*.tmp-split` 잔존 0건 |
| U-5 | 스키마·타입 위반 | `shardPolicy` 객체. 프로젝트 타입 위반은 exit 1 `code_scan_config_invalid`, 전역은 비차단 폴백 |
| U-6 | 구 위치 키 | **무시 + `deprecationOnce` 안내**(080 F-002 선례). 값을 읽지 않으며 자동 변환도 없음. `invalid_index` 승격 안 함 |
| U-7 | 테스트 격리 | `OPAL_HOME` 환경변수 주입 |

## 5. 검증 결과

### 5.1 전량 회귀 — PM 독립 실측

| 스크립트 | pass | 스크립트 | pass |
|---|---|---|---|
| test-discover | 12 | test-scope-filter | 24 |
| test-feature | 9 | test-shard-policy | **89** |
| test-header-source | 12 | test-shard | 57 |
| test-hook | 18 | test-target | 13 |
| test-regression | 36 | test-validate | 34 |
| test-resolve-header | 27 | | |
| test-scaffold | 9 | **합계** | **340 / fail 0** |

- `git diff --stat -- tests/fixtures/golden/` **빈 결과** — 골든 8파일 바이트 diff 0, 재캡처 없음
- 실 `~/.opal/setting.json` 키 `['bootstrap','models']` — 변조 0건 (배포 경계 준수)
- **EXECUTE 워커 자기보고(340/340)를 PM이 독립 재실행으로 대조 확인** — 수치 일치. N-1 문서 정정 후 재실행에서도 340/340 유지

### 5.2 시나리오 판정

16종 전부 **Pass**. 리스크 가설 22건·TASK AC 37행·PLAN TS-ID 122개 미매핑 0.

**P0 8종 전부 GREEN** — H-1(기본값 인하)·H-2(하한 도입)·H-4(홈 유입)·H-5(fail-safe)·H-6(엔트리 유실)·H-12(봉인)·H-13(골든)·H-22(게이트 순환).

### 5.3 완료기준 ④ 왕복 입증 (S-16)

`validate`(탐지, `manifest_oversize === 1` **사전 상태 단언**) → `split --plan --out`(제안) → `--groups --dry-run`(예행) → `--groups`(집행) → `validate`(재검증, **0건**). 엔트리 총합 실행 전후 동일. 중간 산출 groups 문서를 수정 없이 그대로 집행에 재사용.

사전 상태 단언이 핵심이다 — 이것 없이 "0건이 되었다"만 보면 픽스처 정책 오설정도 공허하게 참이 되어 false green이 된다.

### 5.4 PM Gate (TEST) — 6항목

| 항목 | 판정 | 근거 |
|---|---|---|
| 시나리오 전부 PASS | ✅ | 16/16 |
| 코드 품질 | ✅ | `node --check` 13/13, `bash -n` OK. 타입체크 N/A(순수 JS) |
| 보안 (시크릿/`.gitignore`) | ✅ | **§5에 보안 행이 부재하여 PM 직접 실측** — 시크릿 0건, 임시물 추적 0건 |
| 회귀 | ✅ | 340/340 + 골든 diff 0 (PM 독립 재실행) |
| 설계 피드백 빈틈 | ⬜ N/A | PLAN.md에 해당 섹션 부재. §9 리스크 및 대응이 담당 |
| 컨벤션 자동 진단 | ✅ | `GC-CONVENTION-2026-08-04T22-02-37.md` — Critical 0 / High 0 / Medium 0 / Low 1 / Info 1 |

## 6. 이번 태스크에서 잡아낸 결함

| # | 결함 | 발견 | 처리 |
|---|------|------|------|
| 1 | `install-mac.sh` 시드가 `if 'models' in existing: sys.exit(0)`로 조기 종료 — **기존 설치 환경에 정책 키가 영구히 시드되지 않는다** | PLAN 리스크 가설 H-11 | `SEED_KEYS` 루프로 일반화. 3형태 시드 무손실 + 멱등 실측 |
| 2 | `init` 게이트 순환 — 설정이 없어 `init`이 거부되고 `init`을 못 돌려 설정을 못 만듦 | TASK 범위 확장(F-9) | 차단 게이트 **앞** 배치. 설정 부재·파손 트리 양쪽에서 exit 0 실측 |
| 3 | 082 픽스처 다수가 엔트리 소량이라 하한 40 기본값 도입 시 기존 초과 판정이 전부 사라짐 | TASK 제약 ⑤ | 픽스처에 정책 오버라이드 명시로 흡수. **단언 완화·삭제·skip 0건** |
| 4 | `AGENTIC-LOG.md`가 EXECUTE 진입 시점에 생성되지 않음 (semi-agentic §7 위반) | TEST 재개 시 PM | 소급 생성. 행 7 기록은 `state.json` note 실측 근거로 채움(사후 창작 없음) |
| 5 | `opal-harness.md:330` v6.9 변경이력에 HH:mm 누락 (`CONVENTIONS.md §변경이력` 위반) | 컨벤션 자동 진단 Low | `2026-08-04 17:30`으로 정정. 시각은 파일 mtime 실측 |
| 6 | TEST-SCENARIO §4 매핑 표 라벨 8행이 테스트 소스 실제 라벨과 불일치 | TEST PM Gate (N-1) | 문서→소스 단방향 정정. **테스트 코드·단언 무수정**, 정정 후 340/340 유지 |

## 7. 잔여 미해결 / 후속 후보

| # | 항목 | 성격 | 판단 |
|---|------|------|------|
| K-1 | **`split_rollback` 에러 코드(`code-scan.js:2894`) 트리거 케이스 부재** — rename 커밋 단계 실패 주입 경로가 테스트에 없다. 나머지 3코드(`split_groups_invalid`·`split_write_failed`·`split_verify_failed`)는 실측 확인됨 | Known Issue (테스트 커버리지 갭) | **후속 태스크 이관.** 신규 테스트 작성 = 동작검증 필요 → CLOSE 시점 우회 처리 금지(헌법 §4 self-confirming) |
| K-2 | 실제 자산의 의미 분할 미수행 — 대상 9개가 여전히 미분할 상태 | 범위 외(TASK §범위 제외) | 적용 프로젝트 측 작업. 도구는 준비 완료 |
| K-3 | **악화 차단(ratchet) 미도입** — 크기는 단조 증가하므로 기존 초과 면제는 영구 면죄부가 된다 | 의도적 유보 | 순서는 **분할 → 차단**. K-2 완료로 초과 0건이 된 뒤 별도 판단 |
| K-4 | `HOME_ABSENT` 상수+주석이 테스트 11파일에 준-동일 중복 | 개선 제안 (Info) | `CONVENTIONS.md` 근거 없음 — 위반 아님. 규칙화 여부는 별도 판단 |
| K-5 | `resolveHeaderSource`는 완전 무수정이 아니다 — 에러 `fix` 문자열에 `INIT_CREATE_FIX` 안내가 추가됨. 분기 조건·에러 코드 등 판정 로직은 무변경 | 표현 정정 | F-012 AC의 의도된 변경. 080 계약 훼손 아님 |
| K-6 | 4~9 산출파일 구간의 디스패치 상한 미검증 (`pm/dispatch-process.md` Step 6 임계값 3은 관측 기반 잠정치) | 프레임워크 관측 | 083은 상한 내 배치로 완주. 수치 갱신은 관측 누적 시 |

## 8. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 요구사항 F-1~F-9 + 미확정 U-1~U-7 + 제약 11항 + 완료기준 4항 |
| `PLAN.md` | §1~§9 + 리스크 가설 22건 + 기능 설계 F-001~F-012 + TS-ID 122 |
| `TEST-SCENARIO.md` | 시나리오 16종(S-1~S-16) + AC 37행 매핑 + §5 코드품질. 전 항목 Pass |
| `SCENARIO-GATE-1.md` | 목표-커버 게이트 1회차 — coverage-check exit 0 + evaluator verdict pass |
| `AGENTIC-LOG.md` | semi-agentic 게이트 판정 기록 + PM Gate 검증 6항목 + 관측 N-1~N-4 |
| `GC-CONVENTION-2026-08-04T22-02-37.md` | 컨벤션 자동 진단 — verdict PASS |
| `DONE.md` | 이 문서 |

**미커밋 상태다.** 커밋은 소유자 명시 요청 시에만 수행한다(하네스 §1 커밋 규칙).

---

## 변경이력

| 일시 (KST) | 변경 내용 |
|---|---|
| 2026-08-04 22:36 | DONE.md 최초 작성 — 2축 판정·`split` 집행·`--plan` 5단 사다리·`init` 온보딩·전역 설정 3단 해석 완료. 340/340 GREEN(PM 독립 실측)·골든 diff 0·P0 8종 GREEN·완료기준 ④ 왕복 입증. 잡아낸 결함 6건 / 잔여 6건(K-1 `split_rollback` 커버리지 갭은 후속 태스크 이관) (Task 083) |
