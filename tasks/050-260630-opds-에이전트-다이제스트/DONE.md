# DONE: AGENT.md 다이제스트 — 비서 tier 코어 경량화

> 완료일: 2026-06-30 21:28 KST | 스킬: opds | 모드: agentic | 태스크: 050

## 결과 요약

049로 부트스트랩이 2-tier가 되면서 매 세션 로드되는 `opal/core/AGENT.md`를 **비서 코어만 남긴 lean core**로 다이제스트했다. PM/프로젝트 전용 섹션은 이미 Phase B로 로드되는 `opal-pm.md`로 이동(dedup 포함), 부트스트래퍼 자동관리는 신규 reference로 이관, 변경이력은 trim했다. **AGENT.md 소스 493줄 → 236줄, 런타임(변경이력 strip 후) ~455 → ~223줄(약 51% 경감)**. 동작(부트스트랩 절차·2-tier 게이트·보고형식·`//` 진입)은 불변.

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | PM 섹션을 opal-pm.md(이미 Phase B 로드)로 이동 → PM 세션 토큰 중립, 비서 세션만 경감 | 049 2-tier 구조 재활용 |
| 2 | **dedup**: 하네스 3-way(opal-harness.md §2)·모델매핑 우선순위(§6+model-mapping §5)는 기존 존재 → 표 복사 금지, 포인터 단일화 | PRINCIPLES §2 (신규 추상화 금지) |
| 3 | install 스크립트 무변경(검증만) — 마커/strip 메커니즘이 이미 충분 | PRINCIPLES §3 Surgical |
| 4 | 변경이력 trim은 소스 위생(런타임 strip되어 토큰 영향 0) — PLAN이 TASK 전제 493줄을 455줄로 자가정정 | strip_deploy_md 직접 검증 |
| 5 | **WORKER 직교 스킵 경로 명시 + 회귀 TS**(캡틴 지적) | 049/050이 부트스트랩 절을 크게 변경 → 보존 회귀 필요 |

## 변경 파일 (3)

| 파일 | 변경 |
|------|------|
| `opal/core/AGENT.md` | 이관 섹션 10개 제거 + 변경이력 trim + 교차참조 3건 갱신 + **WORKER 규칙 직교 스킵 명시 보강**. 493→236줄 |
| `opal/core/references/opal-pm.md` | §12~§17 신규 수신(역할전환 상세·L2·code-scan 활용·opal-brain 활용·메모리 브리핑·모델매핑 적용·프로젝트 컨텍스트) + dedup 포인터 + 변경이력 |
| `opal/core/references/bootstrapper-management.md` | **신규** — 부트스트래퍼 자동관리(4 플랫폼 + 수동 삽입 마커 블록 + 2-tier 서술) 이관 |

## 검증 결과

- **L1 정적 17/17 PASS, FAIL 0** (TS-001~015): 이관 제거·비서 코어 완결·dedup·dangling 0·install bash -n 불변·WORKER 보존.
- **049 회귀 4건(TS-014a~d) PASS**: Eager 2-phase·PM 게이트·`//` 불변식·step0 스킵게이트 다이제스트 후 보존.
- **L3 2건(TS-014e/f) pending(캡틴 직접)**: 비서/PM 실세션 동작 — install 재배포 후 확인.

## 후속 (캡틴)

1. **install 재배포** — 다이제스트된 AGENT.md·opal-pm.md·신규 bootstrapper-management.md를 `~/.opal/`에 반영(배포 경계).
2. **L3 실세션 검증** (재배포 후): 비서 세션 행동 완결(정보 손실 0) + PM 세션 이관 섹션 정상 발동.
3. **커밋** — 지시 시 수행(현재 미커밋).
4. **(후속 설계 후보, 051)** PRINCIPLES 로딩 역할별 재배치 — 역할 매트릭스 분석 결과: 비서엔 Core Stance 2줄 / PM엔 Lazy / 워커엔 주입. 대화에서 합의된 정제안.

## 산출물

- `TASK.md` / `PLAN.md` / `TEST-SCENARIO.md` / `AGENTIC-LOG.md`
