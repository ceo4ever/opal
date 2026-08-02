# AGENTIC-LOG: 워커 중단 복구 프로토콜 + 디스패치 산출량 상한 + 증분 저장 규율 SSOT화

> 모드: semi-agentic | 시작: 2026-08-02 16:01 | 스킬: //opds

## 모드 경계

- PLAN 사용자 확인 행(행 6) 통과 시점부터 EXECUTE·TEST는 PM 자율. CLOSE 진입은 캡틴 승인 필수.
- 캡틴 지시: 080 미커밋 변경 커밋은 **생략**하고 EXECUTE 진입 (PM 권고와 다른 선택 — 롤백 시 080 변경분 동반 손실 위험을 캡틴이 수용).

## PM 판단 기록

| # | 시점 | 판단 | 근거 |
|---|------|------|------|
| 1 | PLAN PM Gate | 워커 권고 M-8(TEST를 PM 직접 수행) **반려** | 하네스 §1 디스패치 의무 원칙 + self-confirming 방지(TEST-SCENARIO 작성자 = PM) |
| 2 | PLAN PM Gate | 워커 주장 7건 실측 대조 후 승인 | `memory_tool.py` promote 제약 / `install-mac.sh:208-212` strip / `test-regression.js:930` / 변경이력 최신 버전 4건 |
| 3 | 목표-커버 게이트 1회차 | 평가자 fail(1.33) 수용, 재작성 | 목표 시나리오가 정답 고지+저자 자가수행 구조 — 재현성이 아닌 탐색가능성만 검증 |
| 4 | 목표-커버 게이트 2회차 | pass(2.00) 후 잔여 결함 N-1~N-4 즉시 정정 | N-1은 PM 앵커 오기(`AGENT.md`에 `parallel-execution` 0건, 실제는 `opal-harness.md:102`) |

## EXECUTE 디스패치 기록

> S-17(규율의 프롬프트 도달) 검증 증거. 각 디스패치 프롬프트의 고정 2항목 포함 여부를 기록한다.
> Phase 1·2는 주입 템플릿 신설 이전이므로 `PLAN.md` §3.3.2 (A) 확정 문언과 동일 문구를 사용한다.

| Phase | Step | 워커 | 대상 파일 | 고정 2항목 주입 | 문구 출처 |
|-------|------|------|----------|---------------|----------|
| 1 | 1 | opal-task-agent | `opal-harness.md` | ✅ 증분 저장 + 입력 축소 | PLAN §3.3.2 (A) 확정 문언 |
| 1 | 2 | opal-task-agent | `pm-review-gate.md` | ✅ 증분 저장 + 입력 축소 | PLAN §3.3.2 (A) 확정 문언 |
| 2 | 3 | opal-task-agent | `dispatch-process.md` | ✅ 증분 저장 + 입력 축소 | PLAN §3.3.2 (A) 확정 문언 |
| 3 | 4 | opal-task-agent | `parallel-execution.md` | ✅ 증분 저장 + 입력 축소 | `dispatch-process.md` 주입 템플릿 인용 (Step 3에서 신설 완료) |
| 3 | 5 | opal-task-agent | `op-dev-execute/SKILL.md` | ✅ 증분 저장 + 입력 축소 | `dispatch-process.md` 주입 템플릿 인용 (Step 3에서 신설 완료) |

**주입 문구 원문** (Phase 1·2 공통 — PLAN §3.3.2 (A)와 자구 동일):

```
- [MUST] 증분 저장: 산출물 1개를 완결 저장한 뒤 다음 산출물로 이동한다. 말미 일괄 저장 금지.
- [MUST] 입력 축소: 대상 파일 전체 통독 금지. grep으로 위치를 특정한 뒤 해당 구간만 Read하고 부분 편집(Edit)한다.
```

## 배치 구성 실측 (S-18 증거)

| Phase | 계획 산출 파일 수 | 실제 산출 파일 수 | 일치 |
|-------|-----------------|-----------------|------|
| 1 | 2 | 2 (`opal-harness.md`, `pm-review-gate.md`) | ✅ 일치 |
| 2 | 1 | 1 (`dispatch-process.md`) | ✅ 일치 |
| 3 | 2 | 2 (`parallel-execution.md`, `op-dev-execute/SKILL.md`) | ✅ 일치 |

## Step 6 install 재배포 — 중단 사건 및 실측 판정 (본 태스크 프로토콜 자기적용)

**사건**: `./scripts/install-mac.sh` 실행이 10분 타임아웃으로 중단됨(exit 143 / SIGTERM). 워커 중단은 아니지만 "정상 종료 없이 끊긴 프로세스"라 본 태스크가 신설한 실측 판정 3단계를 그대로 적용했다.

| 단계 | 수행 | 결과 |
|------|------|------|
| ① 산출물 확정 | `~/.opal/` 배포본과 프로젝트 소스를 `## 변경이력` strip 기준으로 5파일 대조 | **5/5 OK** (diff 0줄) |
| ② 완료/잔여 판정 | `~/.opal/` 하위 디렉토리 mtime 확인 — references·skills·tools·agents·templates·bin·dashboard-server 전부 16:10 갱신 | 문서·스킬·도구 배포 **완료**. 잔여는 MCP 등록 단계 이후로 추정(본 태스크 범위 밖) |
| ③ 잔여만 재배치 | 본 태스크 완료기준(REQ-5 AC)은 5파일 배포 일치이므로 충족 — install 재실행 불요 | 재실행 **안 함** (완료분 덮어쓰기 회피) |

**중단 원인 추정**: `scripts/install-mac.sh`의 MCP 등록 단계(npx/playwright 캐시 등) 장시간 소요. 스크립트에 대화형 `read` 4개소가 있으나 비대화형 분기(`[[ ! -t 0 ]]`)가 존재한다. **본 태스크와 무관한 선행 이슈**이므로 후속 F-5로 분리 제안.

## Step 7 메모리 졸업 결과

- candidate 2건 → `promoted` 2건 (`update --kind memory --status promoted` — `promote` 서브명령은 실파일 부재로 사용 불가, PLAN M-6 확정대로)
- history에 081 행 append. **FIFO 상한(5)으로 최고령 075 행이 밀려남** — 도구 정상 동작(`history_count: 5` 유지)
- active 메모리 4건 무변경

## Step 8 정합성 검증 4종 결과

| # | 검증 | 결과 |
|---|------|------|
| ① | 앵커 존재 grep (6개소) | 6/6 OK |
| ② | 참조 무결성 (신규 상호 참조 6건) | 6/6 OK — dangling 0건, 대상 헤딩 실재 확인 |
| ③ | 수치 리터럴 유일성 | 재시도 `1회`=harness 1파일 / 산출 `3개`=dispatch-process 1파일 / 판정 3단계 본문=pm-review-gate 1파일 |
| ④ | 회귀 (`test-regression.js`) | 36 pass / 0 fail |
