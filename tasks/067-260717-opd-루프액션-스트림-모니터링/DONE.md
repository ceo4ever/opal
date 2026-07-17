# DONE: 루프 액션 에이전트 투명 모니터링 — opal-agent stream-json 개조 + journal 규약 + opal-action-monitor 도구

> 완료일: 2026-07-17 23:20 (KST) | 스킬: opd | 모드: agentic (`//opd --agentic`)
> 판정: **All Pass** (TEST-SCENARIO S-1~S-15 전량 + 추가작업 1건, 에스컬레이션 0건)

## 요약

루프 액션 에이전트의 이중 블랙박스를 투명화했다: ① opal-agent에 `--stream`(stream-json) 실행 경로를 신설해 워커의 모든 도구 이벤트를 `events.jsonl`로 기계 방출하고, ② 결과 파일 규약 v2(events.jsonl 편입·prompt.txt 규약화·완료 마커 불변) + §운행 일지(journal.md — 루프 액션 에이전트 자신의 판단 기록)를 규약화했으며, ③ 신규 도구 **`opal-action-monitor`**(작성명 oppl-monitor → 캡틴 지시로 추가작업 리네임)로 단계×축 현황판을 한 명령으로 렌더한다(`--json`·`--watch`). RED-first 하이브리드 트랙 첫 실적용(opal_agent.py 개조분).

## 완료기준 대조 (TASK.md §명확화 결과)

| # | 완료기준 | 결과 | 증거 |
|---|---------|------|------|
| ① | stream E2E — events.jsonl 증분 + 5필드 + `--json` 회귀 무 | **PASS** | S-11 증분 성장 0→9,422바이트 실측 / pytest 21/21(RED 3건→GREEN + 기존 18) |
| ② | 재실증에서 events.jsonl·journal.md 실생성 | **PASS** | S-14 실 디스패치 완주(재개 0회) — 비동기 3축 events.jsonl + journal 4컬럼 12행(gate-verdict·retry 근거 포함), resume 동일 UUID(t1=t3) |
| ③ | monitor 렌더 + `--json` + `--watch` | **PASS** | S-8/S-10/S-12/S-15 — 실행 중 `running`→완료 `done` 전이 실관측(evidence/s15-*.txt) |
| ④ | 하드에러·blocked 구분 표시 | **PASS** | S-8/S-9 fixture 4종(done/running/error/blocked) 판정 전부 정확 + blocked 배너 |
| ⑤ | 문서 정합(규약 v2·레지스트리·SKILL·변경이력) | **PASS** | S-5~S-7 — 완료 마커 원문 불변 확인, 레지스트리 2곳, 변경이력 067 전부 |

## 변경 파일 (install 배포 완료)

| 파일 | 변경 요지 |
|------|----------|
| `opal/tools/opal-agent/opal_agent.py` (v2.6) | `--stream` 경로 — Popen 증분 passthrough·`--verbose` 자동·마지막 result 줄 5필드·비지원 provider 명시 에러. 기존 경로 무변경(opt-in) |
| `opal/tools/opal-agent/tests/test_opal_agent.py` | RED-first 신규 4케이스(`[T067/L1-R1]`) — 작성자(test-agent red)≠구현자 분리 |
| `opal/tools/opal-agent/README.md` (v2.6) | stream 모드 절·옵션 표 |
| `opal/agents/opal-loop-action-agent/AGENT.md` (v1.2) | §결과 파일 규약 v2(비동기 events.jsonl/동기 result.json·prompt 규약화·완료 마커 불변) + §운행 일지 신설 |
| `opal/tools/opal-action-monitor/` (신규) | `.oppl-run/` 파서 — 6상태 판정·R-NEST 방어 요약·journal tail·`--json`·`--watch`·에러계약. **리네임: oppl-monitor→opal-action-monitor(추가작업, 공용화 대비)** |
| `opal/core/references/tools.md`·`opal-harness.md` §9 | 도구 레지스트리 등록 |
| `opal/skills/opal-pilot-project-loop/SKILL.md` (v1.4) | 모니터링 안내 |
| `scripts/install-mac.sh` | chmod 블록 |
| `docs/PROJECT.md` | Project Loop 표 행 + 리네임 이력 |

## 핵심 설계 결정

- **R-ASYNC**: events.jsonl 기록 주체 = 호출측 stdout 리다이렉트(비동기 축의 stdout 슬롯 재포맷) — opal-agent에 파일 인자 미도입, 완료 마커=exitcode 불변.
- **R-EVSCHEMA**: claude 원본 이벤트 passthrough(정규화 미채택) — opal-agent는 마지막 result 줄 5필드만 의존(R-H), 파싱 부담은 monitor가 방어적으로.
- **관측 경계**: 실행 중 에이전트 직접 질의 배제 — 파일 SSOT 경유(journal/events를 PM이 읽고 답변). Observability 아이콘 룩업 비대상 유지.
- **RED-first 하이브리드**: 도구 계약 변경(opal_agent.py)만 RED 강제, 신규 읽기 전용 뷰어·문서는 구현-후 검증.

## 특이 관찰 (결함 아님 — 기록)

1. T4b 인라인 생략 축이 monitor에 `pending` 표시(journal에는 end) — 파일 기준 판정의 표시 한계, 후속 개선 후보(069 phase 동적 발견과 함께 검토).
2. 루프 액션 에이전트가 T2 시나리오 3→2 재시드를 자율 판단하고 journal에 근거 기록 — **투명화가 실전에서 이미 작동한 사례**.

## 프로세스 기록

- Gate 판단 11회(Pass 10 / Fail 1 — PLAN 1차: 실증 완화·배포 Step 부재 2건, 재지시 1회로 해소), 3회 초과 Gate 0건, 에스컬레이션 0건, 추가작업 1건(리네임, 캡틴 지시). 전체: `AGENTIC-LOG.md`.

## 후속 (백로그 — 메모리 등록됨)

1. **068 (캡틴 확정, 즉시 착수)**: `//opm` 범용 모니터 스킬 — 인자 없이 backlog.json/최근 태스크 자동 탐지 + opal-action-monitor `--json` 소비 + 해석 보고. opds.
2. **069·070**: oppd(opal-task-action-agent)·opsdd(opal-sdd-action-agent) 채널·규약 전환 → monitor phase 동적 발견 개선 → `//opm` 3/3 커버. 상세: `memory/후속_069_070_액션에이전트_관측_확장.md`.
3. 3/3 커버 확정 후 oppl 잔향 표현 정리 재판단.

## 산출물

- 태스크: TASK/ANALYSIS/PLAN(v1.1)/TEST-SCENARIO(실행 완료·RED 증거)/AGENTIC-LOG/STATE·state.json/DONE(본 문서)
- 실증: `samples/T01-정상슬라이스/`(.oppl-run 22파일·journal·DONE) / `samples/monitor-fixtures/` 4종 / `samples/evidence/` 렌더 캡처 2건
