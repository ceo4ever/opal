# TASK: OPAL Console 브레인 질의 — fetch 타임아웃·ready 사각지대 견고화

> 작성일: 2026-06-22 | 작업 유형: 수정(결함) | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (라이브 화면 결함 보고 + 진단 대화)
> 출력: TASK.md

## 작업 목표

OPAL Console 브레인 질의(태스크 036 산출물)에서 "질문만 보이고 답이 안 보임" / "Load failed" 결함을 근본 해소한다. 수십 초 블로킹하는 동기 HTTP 질의가 브라우저 fetch 타임아웃을 초과하는 구조적 결함과, status 폴링이 ready에서 멈춰 BE 세션 소실을 감지 못 하는 사각지대를 제거한다.

## 배경

태스크 036은 BE/FE 자동 테스트(L1/L2)를 통과하고 PM Gate까지 마쳤으나(STATE row 13까지 ✅), 캡틴의 라이브 검증(대화 2: Q1 11:05 답 비어있음 / Q2 11:23 "Load failed")에서 런타임 결함이 드러났다. 결함은 036 설계가 다루지 않은 별도 근본 원인이라 신규 태스크로 분리한다.

## 배경 분석 (대화에서 도출)

진단 대화에서 어댑터와 동일한 명령을 직접 실측하여 근본 원인을 확정했다.

**실측 증거**
- 콜드 `claude --session-id … -p '//opbr query --read-only "…"' --output-format json` 호출: **69.0초** (`real 69.01`)
- 웜 `--resume` 호출: **19.8초** (`real 19.82`)
- 두 호출 모두 `is_error=false`, BE `extract_json_fence` 추출 정상(answer 730자/431자, citations 2건). **BE 어댑터·파서는 무결 — 범인 아님**.

**근본 원인 (확정)**
1. `dashboard/frontend/src/lib/api.ts` `apiClient`가 순수 `fetch`만 사용 — **AbortController·타임아웃 부재**. 브라우저(특히 Safari) 기본 응답 타임아웃(~60초)에 그대로 노출.
2. BE 콜드 타임아웃은 180초인데(`adapters/brain_session.py:COLD_TIMEOUT_S=180`) 콜드 실측이 69초로 이미 브라우저 한계 초과. 콜드 경로가 query 안에서 한 번이라도 돌면 브라우저가 60초에 끊고 `TypeError: Load failed`(Safari) 발생 → **Q2 증상과 일치**.
3. status 폴링이 `state==="ready"`에서 중단(`BrainPage.tsx` `refetchInterval`→false). 이후 데몬 재시작·30분 유휴 리셋(ⓒ)·웜 resume 크래시(ⓓ)로 BE 인메모리 세션이 사라져도 FE 배지는 "연동됨" 유지. 이 상태로 질의하면 BE가 query 안에서 **인라인 콜드 프라임(69초)**으로 폴백(`ConversationBrainSession.ask`→`_cold_and_ask`) → 60초 초과 → Load failed.
4. Q1(질문만·답 없음)은 동일 클래스의 다른 표면화로 추정 — fetch 중단 시점에 페이지 리로드/언마운트가 겹치면 낙관적 pending 턴이 localStorage에 잔존하여 빈 답으로 보임. **정확한 경위는 라이브 재현으로만 확정 가능**(요구사항 R-4).

## 확정된 설계 방향 (대화에서 합의)

캡틴이 권고안을 수락하고 `//opd --agentic`로 진입함. 권고 방향:

- 근본 처방은 **"수십 초 블로킹하는 동기 HTTP" 구조를 비동기 잡(job)+폴링으로 전환**. 이미 prime-on-intent가 백그라운드+폴링 패턴을 쓰므로 query도 같은 패턴으로 일관화한다.
- 단순 AbortController 추가만으로는 Safari 60초 하드 캡을 늘릴 수 없어 콜드 첫 질의를 살리지 못함 → 비동기 전환이 본질.
- 부가로 ready 사각지대(인라인 콜드 폴백)와 apiClient 타임아웃 가드도 함께 처리.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 브레인 질의가 콜드(≈69초)·웜(≈20초) 어느 경로든 브라우저 fetch 타임아웃에 끊기지 않고 답변/에러를 정확히 표시한다 | - | 콜드 69s·웜 20s 실측 (배경 분석) |
| 범위 | **포함**: ①POST /api/brain/query를 비동기 잡 제출+결과 폴링으로 전환(BE 라우터+brain_session 잡 관리, FE BrainPage 폴링) ②ready 사각지대 — query 인라인 콜드 폴백을 분리(세션 소실 시 재프라임 신호 반환, 60초 블로킹 금지) ③apiClient 타임아웃/AbortController 가드. **제외**: opbr/claude 자체 latency 단축, 브레인 질의 외 Console 화면, 인증 플로우 변경, 영속 저장(무상태 원칙 유지) | Q1 빈답의 정확한 경위(R-4는 라이브 재현으로 확인) | 036 산출물 구조 (brain.py/brain_session.py/opbr_adapter.py/BrainPage.tsx) |
| 제약 | 헌법 플랫폼 독립성·배포 경계(`~/.opal/` 직접편집 금지, 소스 수정 후 install 재배포) / BE 무상태 원칙(Q&A 내용 영속 금지, 잡 상태는 인메모리 휘발) / `--safe-mode`·anthropic SDK·API키 금지(구독 CLI 경유 유지) / shell=False 유지(H-13) / @header·변경이력·citation 규칙 / RED-first(동작검증 대상) | - | `.opal/AGENT.md` 금지사항, `console-brain-subscription-auth` 메모리, 036 @header 계약 |
| 완료기준 | ①콜드 경로(≥69초 소요)에서 FE가 fetch 타임아웃으로 끊기지 않고 최종 답변을 렌더한다(동작검증) ②BE 세션 소실(데몬 재시작/리셋 모사) 후 질의 시 60초+ 블로킹 없이 재프라임 신호→재질의로 복구한다 ③apiClient 호출에 타임아웃 가드가 적용되고 초과 시 명시적 에러 메시지를 표시한다 ④신규/변경 BE pytest·FE vitest 전부 PASS + 기존 회귀 0 ⑤TEST-SCENARIO 전 시나리오 PASS | - | opd 파이프라인 TEST 단계 |

## 요구사항

- [ ] **R-1 (BE)**: POST `/api/brain/query`를 동기 블로킹에서 **비동기 잡 제출+결과 조회** 패턴으로 전환한다. 제출 즉시 job_id(또는 즉시 응답 가능 시 결과) 반환, 백그라운드 스레드가 `brain_session_registry.ask` 수행, 별도 GET 엔드포인트로 결과 폴링. — 어디에: `dashboard/backend/routers/brain.py`, `adapters/brain_session.py`(잡 상태 관리, 무상태 휘발). 왜: 동기 HTTP가 60초 브라우저 캡에 끊김(배경분석 #1·#2). AC: 콜드 69초 질의가 FE에서 타임아웃 없이 완료되는 동작검증 PASS.
- [ ] **R-2 (BE)**: ready 사각지대 제거 — query 시 BE 세션이 cold(`_claude_session_id is None`)이면 **인라인 콜드 프라임(블로킹)을 수행하지 않고** 재프라임 필요 신호를 반환한다(FE가 prime 폴링 후 재질의). 단, R-1 비동기 전환으로 콜드도 잡으로 흡수되면 본 요구는 "콜드 잡이 status를 priming으로 정확히 반영"으로 충족될 수 있음(PLAN에서 R-1과 통합 설계). — 어디에: `adapters/brain_session.py` `ask`/`_cold_and_ask`, `routers/brain.py`. 왜: status 폴링이 ready에서 멈춰 세션 소실 미감지(배경분석 #3). AC: 세션 소실 모사 후 질의가 60초+ 블로킹 없이 복구되는 동작검증 PASS.
- [ ] **R-3 (FE)**: `apiClient`에 AbortController 기반 타임아웃 가드를 추가하고, 브레인 질의/폴링 호출이 이를 사용한다. 초과 시 `TypeError: Load failed`가 아닌 명시적 에러 메시지로 onError를 채운다. — 어디에: `dashboard/frontend/src/lib/api.ts`, `pages/brain/BrainPage.tsx`. 왜: fetch 타임아웃·에러 메시지 불명확(배경분석 #1·Q2). AC: 타임아웃 시 사용자에게 식별 가능한 에러 문구 표시.
- [ ] **R-4 (검증)**: 라이브 화면에서 Q1 빈답/pending 잔존 재현 여부를 1회 확인하고, R-1~R-3 적용 후 콜드 질의·세션소실 복구·타임아웃 표시를 동작검증한다(L3 [SUPERVISOR] 협업 시나리오). — 왜: Q1 경위는 정적 분석으로 미확정(배경분석 #4).

## 제약 조건

- 배포 경계: `~/.opal/` 배포본 직접 편집 금지. 소스(`dashboard/`) 수정 후 install 재배포로 발효(L3 배포는 캡틴 직접 수행).
- BE 무상태 원칙: Q&A 내용·잡 결과를 DB/파일에 영속 금지. 잡 상태는 인메모리 휘발(프로세스 재시작 시 소멸 허용).
- 플랫폼 독립성: Claude 전용 하드코딩 금지. `--safe-mode`·anthropic SDK·`ANTHROPIC_API_KEY` 금지, 구독 `claude -p` CLI 경유 유지, `shell=False` 유지.
- 추적성: 변경 코드 파일 @header 갱신, 문서 변경 시 변경이력 행 추가.
- RED-first: 동작검증 대상(자동 잡·타임아웃 분기)은 RED-first 트랙 적용 — 작성자≠구현자 분리.

## 기술 스택

- Console BE: Python, FastAPI, uvicorn (`dashboard/backend/`) — pytest
- Console FE: React, TypeScript, Vite, TanStack Query, Tailwind, shadcn/ui (`dashboard/frontend/`) — vitest
- 외부: Claude Code CLI(`claude -p`, 구독 인증) — subprocess

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | 036 산출물 (BE) | `dashboard/backend/routers/brain.py`, `adapters/brain_session.py`, `adapters/opbr_adapter.py` | 수정 대상 + @header 계약 |
| D-2 | 소스 | 036 산출물 (FE) | `dashboard/frontend/src/pages/brain/BrainPage.tsx`, `src/lib/api.ts` | 수정 대상 |
| D-3 | 설계 | OPAL Console 아키텍처 | `docs/ARCHITECTURE.md §OPAL Console` | 데몬 구조·읽기전용 계약 |
| D-4 | 설계 | 컨벤션 | `docs/CONVENTIONS.md` | 구현 규칙(@header/citation/배포 경계) |
| D-5 | 기획 | 036 태스크 산출물 | `tasks/036-260622-opd-브레인질의-콘솔연동/PLAN.md`, `ANALYSIS.md` | 기존 설계 의도·세션 상태기계 |
