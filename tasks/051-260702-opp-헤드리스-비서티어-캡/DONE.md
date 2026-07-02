# DONE: `[ASSISTANT]` 마커로 headless(claude -p) 호출을 비서 tier로 캡

> 완료일: 2026-07-02 | 스킬: opp | 모드: agentic | 태스크: 051

## 목표 달성

049 2-tier 부트스트랩(비서=Phase A / PM=Phase B)의 이득을 `claude -p` headless 호출에도 적용했다. 프롬프트 첫 줄 `[ASSISTANT]` 마커를 신설하여, cwd에 `.opal/AGENT.md`가 있어도 Phase B(PM tier)로 승격하지 않고 비서 tier(Phase A)까지만 로드한다. 3단 마커 사다리 완성: `[WORKER]`(전부 스킵) / `[ASSISTANT]`(Phase A만) / 무마커(A+B).

**본질**: 지연 단축이 아니라 **올바른 tier 격리(정합성)** — 읽기전용 브레인 워커가 PM tier(구현금지 가드·디스패치 의무·CLOSE 게이트)를 불필요 로드하는 오염 제거.

## 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/core/AGENT.md` | 3단 마커 사다리(:9) + `[ASSISTANT 규칙]` 박스(:13) + Phase B 승격 게이트 억제 절(:32) + 완료보고 캡 세션 표기(:84) + 변경이력 v4.2(:241) |
| `dashboard/backend/adapters/opbr_adapter.py` | `-p` 프롬프트 첫 줄 `[ASSISTANT]\n` 프리픽스(:130) + @header/docstring 캡 의도(:6,:102) — cmd/shell=False/allowedTools/read-only 계약 불변 |
| `docs/ARCHITECTURE.md` | 부트스트랩 진입 모델에 첫 줄 마커 3단 스킵 사다리 추가 + 변경이력 (CLOSE 관련 문서 업데이트) |
| `~/.opal/AGENT.md` | dev-artifact 배포(검증용 임시, 소스와 IDENTICAL) |

## 요구사항 충족 (R1~R5)

| R | 내용 | 검증 |
|---|------|------|
| R1 | Phase B 억제 게이트 + 3단 사다리 + 마커 이후 라인 실제 요청/`//` 인식 유지 | AGENT.md :9/:13/:32 직접 Read 확인 |
| R2 | 완료보고 `[ASSISTANT]` 캡 세션 `⬜ harness ⬜ PM ⬜ PM모드` 표기 | AGENT.md :84 확인 |
| R3 | 변경이력 v4.2 (KST 실측 `2026-07-02 10:46`) | AGENT.md :241 확인 |
| R4 | 어댑터 프롬프트 프리픽스 + docstring + 보안 계약 불변 | opbr_adapter :130 + :136-139 불변 확인 |
| R5 | `[ASSISTANT]` 프로브 실측 — Phase B 미로드 | 아래 실측 결과 |

## 동작 검증 실측 (Step 6, PM 직접 — self-confirming 방지)

| 프로브 | 완료 보고 | Read 파일 |
|--------|----------|-----------|
| `[ASSISTANT]` 캡 | `✅ principles ✅ identity ⬜ harness ⬜ PM ⬜ PM모드` | setting.json, ~/.opal/AGENT.md, identity.md, PRINCIPLES.md — **harness·opal-pm·프로젝트 .opal/AGENT.md 부재** |
| 무마커 대조군(초반 실측) | `✅ harness ✅ PM ✅ PM모드` | 6파일(harness·opal-pm·프로젝트 AGENT.md 포함) |

→ Phase B 억제 확인 + **회귀 0**. 헌법 §4(done=검증된 동작) 충족.

## 후속 액션 (필수)

1. **[캡틴] canonical install** — 현재 `~/.opal/AGENT.md`는 검증용 dev-artifact. `install-mac.sh`로 정식 재배포해야 하며, 미수행 시 다음 install이 임시본을 덮어쓴다.
2. **[선택] 커밋** — 지시 시 수행 (현재 미커밋).
3. **[선택] 후속 태스크** — opbr_adapter 외 다른 headless `claude -p` 소비자 인벤토리 스캔 (현재 opbr_adapter 단일 적용).

## 참고

- 지연 병목 정정 근거: `.opal/memory/follow-up-brain-query-lite.md` — 부트스트랩 로딩은 콜드 지연 병목이 아님. 콜드 지연 레버는 별건(`opbr --lite`).
- 전 과정 추적: `AGENTIC-LOG.md` (게이트 3회 Pass, PM 의사결정 2건, 에스컬레이션 0).
