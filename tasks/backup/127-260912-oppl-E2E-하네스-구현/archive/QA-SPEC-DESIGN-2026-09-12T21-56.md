# QA-SPEC-DESIGN — oppl Loop 1 D6 설계 검토

> 판정 주체: `opal-evaluator-agent` (phase: design-review) · 기록: PM
> 판정 대상: TASK.md · PRD.md · TRD.md · CONTRACT.md · surfaces.json · BACKLOG.md
> 기준: `CONTRACT.md` §E 루브릭절 6축 앵커, 통과선 전 축 ≥4
> 회전: 2회전 (1회전 2026-09-12 21:50 `fail` → 2회전 21:56 `pass`)

## 1회전 — verdict `fail`

| 축 | 점수 | 판정 |
|---|---:|---|
| E.1 계약 완전성 | 4 | PASS |
| E.2 계약 일관성 | 4 | PASS |
| E.3 설계 정합 | **3** | **FAIL** |
| E.4 drift 필요성 | drift=no | — |
| E.5 컨벤션 정신 | 4 | PASS |
| E.6 아키텍처 적합 | 5 | PASS |

**FAIL 근거**: 백로그 의존 그래프가 자기 완료 기준과 모순. T01(P0 의존 루트)의 완료 기준이 "FE가 임대 backend를 가리키고 실 호출 200"을 요구하는데, 이를 가능하게 하는 T03(FE 주소 주입)·T04(CORS env)가 거꾸로 T01에 의존했다. 선언된 순서로는 워킹 스켈레톤이 성립 불가.

미해결 이슈 10건: ① CONTRACT §A.1·§A.4 소스 인용 5건 오류 ② TRD §2.1 인용 3건 오류 ③ TD-19 "5건" 수치 모순 ④ **T01 의존 역전(FAIL 원인)** ⑤ `drivers/manifest.json` 스키마 부재 ⑥ capability probe 저장 경로 미정의 ⑦ 후보 제외 사유·version 필드 부재 ⑧ MV-19·MV-38 결정론 실행 불가 ⑨ 격리 `OPAL_HOME` 생성 주체 부재 ⑩ §C.8 표면 개수 서술 부정확.

## PM 반영 (1회전 → 2회전)

| # | 반영 |
|---|---|
| ① | §A.1 `profile`→`:38`, `actors`→`:41`, `status`→`:39`, `operational_status`→`:40`, §A.4 `executor`→`:41` |
| ② | TRD §2.1 `EXECUTOR_MATRIX`→`:57-66`, `HANDOFF_REQUIRED_FIELDS`→`:67-76`, `server_policy`→`:74` (본문 2곳 포함) |
| ③ | TD-19 "추가 소비자 7건"으로 정정 |
| ④ | **흡수** 선택 — T01이 FE 3파일 + CORS env를 흡수하고 T03·T04 제거. 의존 역전 대안은 oppl D5 [MUST]("실행 스켈레톤을 의존 루트 P0로 의무화")를 깨므로 탈락. `backlog-tool`에 삭제 서브명령이 없어 backlog.json·BACKLOG.md 삭제 후 `init` 재생성(실행 0건 상태) |
| ⑤ | CONTRACT §A.15 driver manifest 스키마 신설 + §F.1 TD-11 등재 |
| ⑥ | §A.8 서두에 `$OPAL_E2E_ARTIFACT_DIR/probe.json`(후보별 배열) 확정, TRD §7 구조 반영, MV-14 대상 명시 |
| ⑦ | §A.1.2 `candidates[]` 10필드 신설 + `outcome=selected` 0/1개 불변식 + §A.1 필드 행 |
| ⑧ | MV-19를 (a) 문자열 grep + (b) 종료 인자 `status_to_exit()` 호출 AST 검사로 분리, MV-38을 `candidates[].order` 검사로 치환 |
| ⑨ | 범위 경계 선언 — PRD §4.2 비목표, TRD RK-4, T03 완료 기준 3지점 일치 |
| ⑩ | "라우터 경로 선언 16건 + `main.py:102-105` health 1건 = 17건"으로 정정 |
| 추가 | R-14 부정 케이스 검증이 통합 단계에만 있던 지적을 받아 T06 「판정 부정 검증」을 P0·g2로 신설 |

## 2회전 — verdict `pass`

| 축 | 점수 | 판정 | 근거 요약 |
|---|---:|---|---|
| E.1 계약 완전성 | 4 | PASS | `coverage-check` all_covered, 표면 40건 유일·중복 0, Q-2/Q-3 "값 미확정·형태 확정" 유지 |
| E.2 계약 일관성 | 4 | PASS | `e2e_contract.py` 인용 20여 건 원본 전건 대조 오류 0, 판정 단일 관문 유지, 즉시 감점 0 |
| E.3 설계 정합 | 4 | PASS (1회전 3→4) | T01 `depends: []`·AC 자기완결, D5 [MUST] 4항 충족((d) auth는 §C.8 부재 선언으로 N/A), RK-1·RK-2·RK-6 완화책 개별 확인 |
| E.4 drift 필요성 | drift=`no` | PASS | 125 소유 계약 변경 요구 0건 |
| E.5 컨벤션 정신 | 5 | PASS | 표본 사실 주장 전건 정확, 플랫폼 분기 `process.py` 단일, 사용자 자원 판별이 `user_owned` 관측 근거 |
| E.6 아키텍처 적합 | 5 | PASS | 신규 CLI 도구 0, `test-tool`↔`opal-cli` 무의존 MV-22 집행, 증적 쓰기 `evidence.py` 단일 관문 |

1회전 10건 중 9건 해소 · ④ 부분 해소(핵심 역전 해소, 잔여 2건은 아래 A·D) · T06 신설 확인.

## 2회전 잔여 지적과 PM 반영

| # | 지적 | 반영 |
|---|---|---|
| A | T01이 `console-start`·`console-status`를 커버 선언하나 두 표면을 산출하는 완료 기준은 T02에만 있다(④와 같은 방향의 귀속 역전) | T01 `covers`를 `sut-health` 단독으로, T02를 `console-start`·`console-stop`·`console-status` 3건으로 이동 |
| B | §A.1.2 `excluded_by` enum의 `tested_range_probe_failed`가 4곳의 "`infra_error` 승격" 규정과 모순 | enum을 `minimum_version` \| `capability_missing` 2종으로 축소하고 `infra_error` 귀속을 명문화 |
| C | 백로그 재생성으로 CONTRACT의 백로그 완료 기준 인용 3건이 stale | §A.15 "T07 4번"→"T05 4번", §A.1.2 "T07 4번·T08 5번"→"T07 5번·T08 2번·4번" |
| D | T01의 "임대한 포트"와 T03의 lease record 소유 경계가 문구로 갈리지 않음 | T01 슬라이스에 「포트 경계」 명시 — T01은 가용 포트 bind + strict-port 기동까지, allocator lock·lease record·stale 회수·동시성은 T03 소유 |
| E | §A.1.2·§A.15의 신설 [MUST] 불변식에 검증 훅 부재 | MV-41(selected 0/1개 + 0개면 `executor_unavailable`), MV-42(manifest 4필드·semver 파싱) 신설 |
| F | T04의 병렬 그룹 귀속 비대칭 | g2 편입 대신 **제외 사유 명시** — T04와 T10이 모두 `test_tool.py` e2e 서브파서를 수정하므로 같은 그룹이면 동일 파일을 두 워커가 나눠 갖는다(`dispatch-process` Step 1 위반). `depends`를 `T03,T10`으로 바꿔 순차화 |

반영 후 `coverage-check` 재실행: `all_covered: true`, `surface_count: 40`.

## 판정

**D6 통과** — verdict `pass`, drift `no`, 미해결 이슈 0건. Loop 1 4요소(PRD/TRD/CONTRACT/BACKLOG) 잠김 준비 완료. D7 사용자 확정 게이트로 진행한다.
