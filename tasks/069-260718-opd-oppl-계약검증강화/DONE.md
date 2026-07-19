# DONE: oppl 계약 접합면 검증 강화

> 완료일: 2026-07-19 | 스킬: //opd --agentic | 모드: agentic
> 승인: 캡틴 확인 (2026-07-19 12:40 — TEST All Pass 검토 후 CLOSE 승인)

## 요약

oppl 파이프라인의 완료 판정이 "테스트가 어떤 환경·어떤 상대로 실행됐는지"를 반영하지 않아 목(MSW)·비브라우저·서버 미기동 GREEN이 전부 "verified"로 집계되던 근본 갭을 봉쇄했다. **증거 충실도(Evidence Fidelity) 원칙**(mock < real-http < real-usage)과 **계약 표면(surface) 전수 커버리지**를 1급 규범으로 명문화하고, 도구 거부(exit code + 에러 필드)로 강제했다.

사고 사례(타 프로젝트 oppl 실전: auth 계약 구멍·목 self-confirming·표본 검증) 3원인의 재발 경로가 도구 수준에서 전부 차단됨을 라이브 실관찰로 확인:

| 사고 원인 | 봉쇄 게이트 | 실증 |
|----------|-----------|------|
| 계약 표면 미배정(budgets/decisions) | backlog-tool `coverage-check` | `surface_uncovered` exit 1 실관찰 |
| 목 단독 GREEN(FE 79건 MSW) | test-tool `scenario-fidelity-check` | `fidelity_unmet` exit 13 실관찰 |
| 표본 검증(3표면만) | test-tool `scenario-conformance` | 표면 전수 매트릭스 — `surface_unverified` exit 14 |
| auth 계약 구멍 | 표면 인벤토리(surfaces.json) auth 필드 의무 + D6 Evaluator 판정 ⑦⑧ | contract.md §2.2 [MUST] |
| CORS류 브라우저 결함 | conformance CORS preflight 규범 + L✓ 여정 스모크(실 브라우저) | verification.md §2.1.1 / journey-flow.md §6 |
| 검증 환경 부재(목 개발 사유) | D5 워킹 스켈레톤 최우선 태스크 의무(BE 스웨거+FE dev 서버+브라우저 관통) | SKILL.md D5 [MUST] + Evaluator ⑩ |

## 변경 파일 (소스 16개)

| 영역 | 파일 | 변경 |
|------|------|------|
| 도구 | `opal/tools/backlog-tool/backlog_tool.py` | `--covers` 필드(add/update-task, 렌더), `coverage-check` 서브명령, 에러 4종(covers_invalid_json·surface_uncovered·integration_task_missing·surfaces_file_not_found) |
| 도구 | `opal/tools/backlog-tool/schema/backlog.schema.json` · `README.md` · `tests/test_backlog_tool.py` | covers optional 스키마·문서·신규 TestCase 4클래스(RED-first) |
| 도구 | `opal/tools/test-tool/lib/scenario.py` | FIDELITY_ORDER, required_fidelity/fidelity/surface_ref 필드, `scenario-fidelity-check`(exit 13)·`scenario-conformance`(exit 14/15, surfaces 부재 시 applicable:false 스킵) |
| 도구 | `opal/tools/test-tool/schema/test-scenario.schema.json` · `README.md` · `tests/test_scenario.py` | 스키마 additive·문서·신규 TestCase 3클래스(RED-first) |
| 스킬 | `opal/skills/opal-pilot-project-loop/SKILL.md` | D4 surfaces 요구, D5 스켈레톤 4항 의무+covers 안내, D7 coverage-check 게이트, L✓ 3중 불리언 AND(done-check ∧ conformance ∧ 회귀 0)+여정 스모크, T4a fidelity-check, 병렬 통합 태스크 게이트 연결 |
| 스킬 | `references/contract.md` | §2.1 origin 선언 의무, §2.2 표면 인벤토리 [MUST], §2.2.1 surfaces.json 스펙(OpenAPI 파생 이원화) |
| 스킬 | `references/verification.md` | §1.5 증거 충실도 사다리·done 규범, §1.6 스켈레톤 메커니즘, §2.1 conformance 분모·실행방식·§2.1.1 원문(auth 토큰 체인·CORS preflight), E2E 실 브라우저 |
| 스킬 | `references/journey-flow.md` | §6 여정 스모크 게이트(실 브라우저, 스킵 조건, VERIFICATION.md 기록) |
| 스킬 | `references/loop-control.md` | §7 신규 게이트 에러 4종 복구가능 분류 |
| 에이전트 | `opal/agents/opal-evaluator-agent/AGENT.md` | Base 루브릭 ⑦표면 완전성 ⑧auth ⑨origin ⑩스켈레톤 + target_artifacts surfaces.json |
| 에이전트 | `opal/agents/opal-loop-action-agent/AGENT.md` | 요구 충실도·surfaces_path 주입(T1·T2), T4a fidelity/conformance 게이트 호출, blocked 트리거 편입 |
| 문서 | `docs/PROJECT.md` | Project Loop 표 도구 설명 정합 + 변경이력 (PM 직접) |

## 검증 결과

- **TEST 판정: All Pass** — S-1~S-12 전부 GREEN(실행 출력 증거, `TEST-SCENARIO.md` §7)
- RED-first: 신규 테스트 13건 RED 실관찰(§RED 증거) → 구현 후 GREEN 전환, 테스트 파일 무수정(불변성)
- 회귀 0: backlog-tool 29/29 · test-tool scenario 23/23 (discover 35 중 1건은 본 태스크 무관 기존 환경 의존 실패 — 판정 제외 명기)
- 통합 체인(S-12): 실 run.sh 호출로 init→covers→coverage-check→scenario-init→red/lock→mark(fidelity)→fidelity-check→conformance 전 단계 exit 0
- 축 분리(S-9): backlog-tool↔test-scenario.json 기능 결합 0건, yaml import 0건(surfaces=stdlib JSON)
- 컨벤션 자동 진단: Critical/High 0건 (`GC-CONVENTION-2026-07-19T12-24-18.md`)

## 의사결정 기록 (M-1~M-6 — PLAN §3.0)

1. 표면 인벤토리 = surfaces.json 단일 IR(JSON), 작성 SSOT는 API=OpenAPI 파생/비-API=직접 작성 이원화(D4 격리)
2. 교차 판정 축별 분리 — R-3=backlog-tool(surfaces만)/R-4=test-tool(surfaces만), L✓=PM 불리언 AND (3-SSOT 축 분리 유지)
3. required_fidelity/fidelity 분리 + 시나리오별 부분 게이트 (task:061 전부-게이트 재발 방지)
4. Evaluator·루프 액션 AGENT.md 모두 확장 (R-G 사각지대 봉쇄)
5. 하위 호환 기본값 = 미지정 mock, surfaces 부재 = conformance 스킵 (회귀 0)
6. 신규 게이트 에러 4종 = loop-control §7 복구가능

## 잔여·특이사항

- Minor 2건(보정 불요 판단): 도구 docstring 내 축 분리 설명 문자열(기능 결합 0), 테스트 파일 blank line 3연속 2곳
- 1차 TEST 워커 세션 한도 중단 → 재개 완주 (AGENTIC-LOG #11, 산출물 손실 없음)
- agentic 대행 전 과정: `AGENTIC-LOG.md` (게이트 6회 전부 Pass, 에스컬레이션 0)

## 다음 단계 (후속 후보)

1. **install 재배포** — `~/.opal/` 동기화 (별도 승인 필요, 미배포 시 신규 게이트는 프로젝트 소스 경로에서만 유효)
2. **커밋** — 캡틴 지시 시 수행
3. oppd/opsdd 파이프라인으로 충실도·커버리지 게이트 확산 (기존 후속 069·070 관측 확장과 병합 검토)
