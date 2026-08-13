# DONE: 작업 히스토리 오기재 정정 명령 신설 (`update --kind history`)

> 완료일시: 2026-07-30 12:53 (KST) | 시작일시: 2026-07-30 10:10 (KST)
> 적용 스킬: opds (Short Task) | 모드: agentic (TASK 단계에서 semi-agentic → agentic 전환)
> 태스크 번호: 079

## 1. 작업 결과 요약

`memory-tool update`에 `--kind history`를 신설해, 잘못 기재된 작업 히스토리 행을 **삭제 없이 정정**할 수 있게 했다.

**배경**: 078에서 메모리 SSOT를 `MEMORY.json`으로 전환하며 히스토리 관리가 전량 tool-gated가 됐고, 그 결과 오기재를 되돌릴 경로가 사라졌다. 남은 선택지는 ① 5건을 더 추가해 FIFO로 밀어내기 ② `MEMORY.json` 손편집뿐이었고, ②는 078이 없애려던 바로 그 행위다.

**설계 선택 — 삭제가 아니라 정정** (소유자 결정): `delete`의 무손실 가드는 `status`(`dead`/`superseded`)에 걸려 있는데 히스토리 행에는 그 필드가 없다. 가드 없는 삭제 명령을 노출하면 오히려 위험하다. 히스토리는 FIFO 5 회전 로그이므로 필요한 것은 삭제가 아니라 정정이다.

## 2. 요구사항 달성 (R-1 ~ R-5)

| R-ID | 요구사항 | 결과 | 근거 |
|------|---------|------|------|
| R-1 | `--kind {memory,history}` 신설, 기본 `memory` | ✅ | 하위호환 유지 — 기존 132건 무변경 통과. TS-001~004, 019, 020, 025, 026 |
| R-2 | 4필드 정정(`--stage`/`--result`/`--path`/`--new-title`) | ✅ | 미지정 필드·타 행 불변, 행 수 불변, 스키마 통과. TS-005~010, 018 |
| R-3 | 오용 조합 결정론 거부 | ✅ | 4거부 케이스 전량 + 경로 탈출. TS-011~015, 027, 028 |
| R-4 | 무손실·원자성 보존 | ✅ | 거부 경로 파일 바이트·mtime 불변, `.tmp`·`.lock` 잔여 0, 동시 정정 클로버 0. TS-016, 017 |
| R-5 | 문서·배포 반영 + 실사용 검증 | ✅ | 3문서 개정 + 배포 + **078 히스토리 실정정**. TS-021~024, 029, 030 |

## 3. 변경 파일 (5개)

| 파일 | 핵심 변경 |
|------|----------|
| `opal/tools/memory-tool/memory_tool.py` | `cmd_update` `kind` 2분기 + `_check_update_kind_args`(락 진입 전 게이트)·`_apply_history_correction`(in-place, FIFO 미호출) 신설, argparse 4인자 추가, @header v2.1 |
| `opal/tools/memory-tool/tests/test_memory_tool.py` | 신규 4클래스 31케이스 (`TestUpdateBackCompat`/`KindHistory`/`KindArgGuard`/`HistoryLossless`), @header v1.2 |
| `opal/tools/memory-tool/README.md` | `update` 절 개정 — 조합 규칙 표·대상 판별 정책·FIFO 미적용 명시 (절 30줄), v2.1 |
| `opal/core/references/tools.md` | memory-tool 절 순증 **+4줄** (`Edit` 전용·앵커 편집으로 077 변경 보존), v2.8 |
| `opal/core/references/harness/memory-learning.md` | 정정 경로 **1줄**만 추가 (83줄, ≤84 게이트 준수), v1.3 |

## 4. 검증 결과

| 항목 | 결과 |
|------|------|
| TEST-SCENARIO | **30/30 Pass**, Fail 0 |
| 회귀 | **163 tests OK** (기존 132 + 신규 31) |
| 컨벤션 자동 진단 | **Critical 0 / High 0** (Medium 1 즉시 수정, Low 1 이월) |
| RED-first | 강제 트랙 — RED 증거 exit 1(163건 중 24 fail) 확보 후 GREEN 진입, `verify --red-check` pass |
| 목표-커버 게이트 | coverage-check exit 0(R5/F4/H10/S30) + 평가자 rubric pass(2/2/2, gaps 0) — **1회차 수렴** |

### TS-024 — 목표달성 실증 (M3, PM 직접 수행)

배포본 CLI 응답:

```json
{"ok": true, "command": "update", "kind": "history",
 "title": "078 메모리 SSOT JSON 전환",
 "matched_index": 0, "match_count": 1,
 "changed": ["stage"], "history_count": 5,
 "review": {"history_status": {"fifo_trimmed": false, "count": 5}, "violations": []}}
```

`git diff .opal/MEMORY.json` (해당 hunk):

```diff
       "title": "078 메모리 SSOT JSON 전환",
       "date": "2026-07-29",
-      "stage": "완료·미커밋",
+      "stage": "완료·커밋(d7a8ce0, 447ff09)",
       "path": "tasks/078-260728-opd-메모리-json전환/",
```

> 같은 파일의 `last_task_number: 78→79`는 **079 채번(`task-number --bump`)** 에 의한 것으로 이번 정정과 무관하다. 정정 자체는 **1행 1필드**다.

**이 태스크는 자기 존재 이유를 스스로 증명했다** — 078의 히스토리가 `완료·미커밋`으로 stale했고(커밋 `d7a8ce0`·`447ff09` 이후에도), 그 최초 피해 사례를 신설 기능으로 해소했다. 손편집 0, 삭제 0, 행 수 불변.

## 5. 설계 결정 (P-1 ~ P-7)

| # | 결정 | 근거 |
|---|------|------|
| P-1 | `cmd_update` 내부 `kind` 분기 + 락 밖 사전 게이트 | `cmd_append`가 이미 동일 패턴. 함수 분리는 lock/load/validate/write 골격을 복제해 "새 쓰기 경로 금지" 제약 위반 |
| P-2 | `--summary`는 히스토리에서 **거부**(별칭 불허) | `memoryRow.summary`에는 `maxLength:80`이 있으나 `historyRow.result`에는 없다 — 별칭 허용 시 **같은 플래그가 kind에 따라 길이 검증을 켜고 끄는** 비결정적 표면이 된다 |
| P-3 | 에러코드 **신설 0** | `invalid_kind`가 이미 `ERROR_CODES:125`에 존재(`cmd_append` 사용 중). 조합 위반은 `invalid_args`+`detail`(`cmd_task_number` 선례). → 키 수 23 불변, 동기화 회귀 0 |
| P-4 | 복수 매치 시 **배열 선행 1건** + `match_count`/`matched_index` 노출 | `append`가 `insert(0,…)`만 하고 스키마가 "맨 앞=최신"을 규약화 — 임의 선택이 아니다. 거부 정책은 재작업으로 title이 중복되는 순간 주 유스케이스를 영구 봉쇄하는 반면, 오정정은 같은 명령으로 되정정 가능(비대칭) |
| P-5 | **FIFO 재적용 금지** [MUST] | `_enforce_history_fifo`는 `rows[:5]` 순수 절단이고 스키마에 `maxItems`가 없다 — 호출하면 6행 이상 문서의 행을 **조용히 삭제**해 "삭제 없는 정정" 전제를 깬다. 초과는 `review.fifo_trimmed`가 표면화하고 정리는 `prune` 전담 |
| P-6 | RED-first 강제 | `red-first.md` §1.5 "API 계약" + "버그 수정(회귀 방지)" 2중 해당 |
| P-7 | 문서 3층 분담 | README 상세(≤45줄) / `tools.md` 시그니처(순증 ≤8줄) / `memory-learning.md` **1줄**(≤84줄 게이트) — 078의 슬림화 성과 보존 |

### 부가 결정 — `--kind`에 argparse `choices=` 금지 [MUST]

붙이면 위반 시 argparse가 **exit 2 + stderr usage(비 JSON)** 를 내어 R-1 AC(c)와 "응답은 단일라인 JSON" 계약을 동시에 위반한다. `append`는 `choices=`를 쓰므로 **무비판 복사 위험**이 실재했다. `metavar`로 `--help`에 노출하고 검증은 코드에서 수행한다(TS-004가 exit code와 stdout을 동시 단정).

## 6. 비범위

| 대상 | 제외 근거 |
|------|----------|
| `delete --kind history` | 무손실 가드 근거(`status` 필드)가 히스토리 행에 없다. 히스토리는 FIFO 5 회전 로그이므로 지목 삭제가 불필요 |
| 히스토리 스키마 변경 | `$defs.historyRow` 무변경 — `additionalProperties:false` 유지 |
| 타 서브명령 `--kind` 확장 | 이번 요구에 없음 |

## 7. 잔여 미해결 · 후속 후보

| # | 항목 | 성격 |
|---|------|------|
| 1 | `append --kind history`의 `--summary`→`result` 매핑과 신규 `update --result` 간 **용어 불일치** | 후속 — 계약 파괴 위험이 있어 이번에 통일하지 않음(PLAN 권고) |
| 2 | `tools.md` 변경이력 `HH:mm` 누락 (Low) | 해당 파일 이력 전체의 기존 패턴 — 079 단독 결함 아님 |
| 3 | `~/.claude_platform_mkt/settings.json` todo hook 미등록 | 078에서 이월 — 캡틴 수동 조치 |

## 8. 특이사항 (agentic 운영)

- **PM Gate에서 워커 판단 2건을 실측 대조** — ① PLAN의 핵심 주장 3건(`invalid_kind` 기존 존재 / FIFO 순수 절단 / `maxItems` 부재)을 코드로 재확인해 "FIFO 호출 금지"가 설계상 필수임을 검증 ② TEST의 TS-030 Fail이 **기대값 오류였음**을 밝혀 Pass로 정정
- **TS-030 사례** — 워커가 `tools.md` v2.7 대신 v2.8을 쓴 것은 077의 v2.7 선점을 회피한 정상 동작이었고, 틀린 쪽은 PLAN 작성 시점의 예측값을 리터럴로 굳힌 **시나리오 문서**였다. 워커가 산출물을 억지로 맞추지 않고 보고만 한 판단이 정확했다(맞췄다면 077 행과 충돌)
- **동시 태스크 077 공존** — `tools.md` 공유. `Write` 금지·`Edit` 전용·헤딩 앵커 규율(078 §8 승계)로 충돌 0건, code-scan 절 diff 0줄 확인
- **078 운영 교훈 적용** — 워커 프롬프트에 "전체 파일 통독 금지·grep으로 위치·함수 단위 저장"을 명시. 이번 태스크는 워커 인프라 실패 **0건**
- **평가자 권고 수용** — M3 시나리오(TS-024)는 자동 게이트가 없으므로 결과란에 실제 출력 원문을 첨부했다("확인함"류 산문 금지)
- 판단 이력: `AGENTIC-LOG.md`

## 9. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 요구사항 R-1~R-5 · 확정 방향 4 · 비범위 3 · 명확화 4요소 |
| `PLAN.md` | F-001~F-004 · 5 Step / 4 Phase · H-1~H-10 · P-1~P-7 (820줄) |
| `TEST-SCENARIO.md` | 30 시나리오 (L1 26 / L2 4) · 결과 기재 완료 |
| `SCENARIO-GATE-1.md` | 목표-커버 루브릭 채점 (1회차 수렴, 2/2/2) |
| `GC-CONVENTION-20260730.md` | 컨벤션 진단 (Critical 0 / High 0) |
| `AGENTIC-LOG.md` | PM 대행 일지 |
| `STATE.md` / `state.json` | 파이프라인 현황판 (11행) |
