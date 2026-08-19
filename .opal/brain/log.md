# Project Brain Log

> append-only 연대기. brain-tool `log` 커맨드로만 기록한다. 직접 편집하지 않는다.
> 형식: `## [날짜] op | 요약` + 하위 목록(신규/갱신/출처)

## [2026-06-10] init | brain 부트스트랩 (task 015) — 핵심 엔티티 2 + 시스템 concept 1 시드
- 신규: [[state-tool]], [[brain-tool]], [[opal-brain-system]]

## [2026-06-11] ingest | 태스크 015 CLOSE — opal-brain 코어 신설
- 신규: [[opal-brain-system]], [[brain-tool]], [[state-tool]]
- 출처: task:015

## [2026-06-11] ingest | 016 dogfooding docs 5건
- 신규: [[opal-architecture]], [[opal-conventions]], [[opal-project-definition]], [[opal-security-model]], [[opal-brain-design-proposal]]
- 출처: doc:docs/ARCHITECTURE.md, doc:docs/CONVENTIONS.md, doc:docs/PROJECT.md, doc:docs/SECURITY.md, doc:docs/proposals/opal-brain-design.md

## [2026-06-11] ingest | 016 백필 — 선별 10건/후보 12건
- 신규: [[coding-principles-ssot]], [[wtm-agent-cmux-integration]], [[test-scenario-pipeline-redesign]], [[linux-install-script]], [[cmux-tool-dispatcher-expansion]], [[opwt-v4-output-system]], [[codex-platform-integration]], [[model-mapping-latest-tracking]], [[opal-principles-constitution]]
- 출처: task:001, task:002, task:004, task:006, task:007, task:008, task:009, task:011, task:012

## [2026-06-11] ingest | 016 dogfooding skills 전반 16건
- 신규: [[op-brain-ingest]], [[op-dev-analysis]], [[op-dev-execute]], [[op-dev-plan]], [[op-dev-qa]], [[op-dev-test-scenario]], [[op-dev-todo]], [[op-dev-wireframe]], [[op-sdd-action-plan]], [[op-sdd-plan]], [[op-sdd-spec]], [[op-sdd-verify]], [[op-spec-validator]], [[op-task]], [[op-task-execute]], [[op-task-plan]]
- 출처: skill:opal/skills/op-brain-ingest, skill:opal/skills/op-dev-analysis, skill:opal/skills/op-dev-execute, skill:opal/skills/op-dev-plan, skill:opal/skills/op-dev-qa, skill:opal/skills/op-dev-test-scenario, skill:opal/skills/op-dev-todo, skill:opal/skills/op-dev-wireframe, skill:opal/skills/op-sdd-action-plan, skill:opal/skills/op-sdd-plan, skill:opal/skills/op-sdd-spec, skill:opal/skills/op-sdd-verify, skill:opal/skills/op-spec-validator, skill:opal/skills/op-task, skill:opal/skills/op-task-execute, skill:opal/skills/op-task-plan

## [2026-06-11] ingest | 016 dogfooding skills 후반 16건
- 신규: [[skill-op-task-qa]], [[skill-opal-agent-creator]], [[skill-opal-brain]], [[skill-opal-onboarding]], [[skill-opal-pilot-dev]], [[skill-opal-pilot-dev-short]], [[skill-opal-pilot-dev-wireframe]], [[skill-opal-pilot-gc]], [[skill-opal-pilot-project]], [[skill-opal-pilot-project-dev]], [[skill-opal-pilot-sdd]], [[skill-opal-pilot-write-tech]], [[skill-opal-project-init]], [[skill-opal-skill-creator]], [[skill-opal-skill-manager]], [[skill-opal-start]]
- 출처: skill:opal/skills/op-task-qa, skill:opal/skills/opal-agent-creator, skill:opal/skills/opal-brain, skill:opal/skills/opal-onboarding, skill:opal/skills/opal-pilot-dev, skill:opal/skills/opal-pilot-dev-short, skill:opal/skills/opal-pilot-dev-wireframe, skill:opal/skills/opal-pilot-gc, skill:opal/skills/opal-pilot-project, skill:opal/skills/opal-pilot-project-dev, skill:opal/skills/opal-pilot-sdd, skill:opal/skills/opal-pilot-write-tech, skill:opal/skills/opal-project-init, skill:opal/skills/opal-skill-creator, skill:opal/skills/opal-skill-manager, skill:opal/skills/opal-start

## [2026-06-11] lint | 016 테스트 중 source_ref 형식 정정 — skills 32페이지 sources를 ingest-scan 표준(skill:<폴더명>)으로 통일, 멱등 skip 32건 복구

## [2026-06-11] query | 캡틴 질의: OPAL 첫 사용 순서·예시 — onboarding/start/project-init 3페이지 합성

## [2026-06-11] query | synthesis 파일링 — OPAL 첫 사용 가이드 (캡틴 승인)
- 신규: [[opal-first-use-guide]]

## [2026-06-11] ingest | CLOSE ingest — 태스크 016 opal-wiki-pilot 지능화 (concept 4건 신규, brain-tool entity 갱신)
- 신규: [[pages/concept/page-type-dynamic-schema.md]], [[pages/concept/three-layer-memory-architecture.md]], [[pages/concept/brain-search-on-demand.md]], [[pages/concept/wiki-intelligence-decisions-016.md]]
- 출처: task:016

## [2026-06-11] ingest | CLOSE ingest — 태스크 010 code-scan PM 우선 무조건화
- 신규: [[pages/concept/code-scan-mandatory-policy.md]], [[pages/concept/brain-code-scan-role-division.md]]
- 출처: task:010

## [2026-06-12] ingest | CLOSE ingest — 태스크 018 README 최신화
- 신규: [[pages/concept/readme-ssot-principle.md]], [[pages/concept/opsdd-pipeline-ssot.md]], [[pages/concept/uncommitted-component-readme-policy.md]]
- 출처: task:018

## [2026-06-12] ingest | CLOSE ingest — 태스크 019 opal-pilot-data-design (DB 설계 OPAL 내재화)
- 신규: [[pages/entity/skill-opal-pilot-data-design.md]], [[pages/entity/op-data-dictionary-skill.md]], [[pages/entity/op-data-model-skill.md]], [[pages/entity/op-data-ddl-skill.md]], [[pages/concept/dict-선행-model-ssot.md]], [[pages/concept/opdd-design-artifacts-path-pattern.md]], [[pages/concept/erd-modeler-deprecation.md]], [[pages/flow/opdd-pipeline-flow.md]]
- 출처: task:019

## [2026-06-14] ingest | CLOSE ingest — 태스크 020 opi 아키텍처 깊이 강화 (WHERE→HOW): concept 2건 누적
- 신규: [[pages/concept/opi-impl-injectable-depth-standard.md]], [[pages/concept/opi-v42-architecture-decisions.md]]
- 출처: task:020

## [2026-06-15] ingest | CLOSE ingest — 태스크 021 OPAL Console
- 신규: [[pages/entity/opal-console.md]], [[pages/concept/daemon-as-tool-orchestrator.md]], [[pages/concept/project-id-query-param-pattern.md]], [[pages/concept/deploy-artifact-verification-lesson.md]]
- 출처: task:021

## [2026-06-16] ingest | CLOSE ingest — 태스크 023 OPAL Console 칸반 stage pipeline UX 개선
- 신규: [[pages/concept/kanban-current-stage-derivation.md]], [[pages/concept/kanban-pipeline-stage-grouping.md]], [[pages/concept/test-real-data-validation-lesson.md]]
- 출처: task:023

## [2026-06-16] ingest | CLOSE ingest — 태스크 024 기획 산출물 비즈니스 용어 우선 원칙
- 신규: [[pages/concept/business-terminology-first-principle.md]]
- 출처: task:024

## [2026-06-16] ingest | CLOSE ingest — 태스크 005 명확화 게이트 TASK 4요소 잠금 기계 집행
- 신규: [[pages/concept/clarification-gate.md]], [[pages/concept/clarification-gate-backward-compat.md]]
- 출처: task:005

## [2026-06-16] ingest | CLOSE ingest — 태스크 025 brain-tool search 공백 무시 매칭
- 신규: [[pages/concept/brain-search-whitespace-insensitive.md]]
- 출처: task:025

## [2026-06-17] ingest | task:027 — Brain 업무 언어 번역 계층(term) 설계 등록
- 신규: [[brain-business-term-layer]]
- 출처: task:027

## [2026-06-17] ingest | CLOSE ingest — 태스크 028 Codex 워커 디스패치 어댑터 정합
- 신규: [[pages/concept/codex-dispatch-inline-injection.md]], [[pages/concept/opal-adapter-platform-isolation.md]]
- 출처: task:028

## [2026-06-18] ingest | CLOSE ingest — 태스크 029 스킬레지스트리-정합-분류정리
- 신규: [[pages/concept/opal-brain-not-pilot-decision.md]], [[pages/concept/skill-registry-validate-extension.md]], [[pages/concept/opal-skill-classification-system.md]]
- 출처: task:029

## [2026-06-21] ingest | CLOSE ingest — 태스크 030 opal-start→opal-next 개명
- 신규: [[pages/concept/skill-opal-next.md]], [[pages/concept/skill-rename-validate-pattern.md]]
- 출처: task:030

## [2026-06-21] ingest | CLOSE ingest — 태스크 031 oppd 개선·세분화·B7 완성도루프
- 신규: [[b7-action-completion-loop]], [[wbs-세분화-단일책임-수용시나리오]], [[oppd-prd-trd-task-folder-promote]], [[loop-upper-bound-ssot-pattern]], [[analysis-drift-pm-cross-verify-lesson]]
- 출처: task:031

## [2026-06-21] ingest | CLOSE ingest — 태스크 032 install 어댑터 본문 model 레벨 치환
- 신규: [[adapter-body-model-level-substitution]], [[active-platform-dir-install-target-lesson]]
- 갱신: [[analysis-drift-pm-cross-verify-lesson]]
- 출처: task:032

## [2026-06-21] ingest | CLOSE ingest — 태스크 033 검증명령-표준화-vitest
- 신규: [[pages/concept/verification-command-4-standard.md]], [[pages/concept/analysis-version-hallucination-npm-view.md]], [[pages/concept/state-tool-mock-guard-skill-false-positive.md]]
- 출처: task:033

## [2026-06-22] ingest | CLOSE ingest — 태스크 035 brain-validate-flatness-check
- 신규: [[pages/concept/brain-validate-flatness-enforcement.md]], [[pages/entity/brain-tool.md]]
- 출처: task:035

## [2026-06-23] ingest | CLOSE ingest — 태스크 037 브레인질의-타임아웃-견고화
- 신규: [[pages/concept/brain-query-async-job-polling.md]], [[pages/concept/red-test-determinism-abort-trap.md]], [[pages/concept/brain-query-latency-model.md]]
- 출처: task:037

## [2026-06-23] ingest | CLOSE ingest — 태스크 038 brain entity 작성 규율 표준화
- 신규: [[brain-entity-discipline]]
- 출처: task:038

## [2026-06-23] ingest | CLOSE ingest — 태스크 039 테스트도구 FE/BE 2단계 재정의 + 신규 test-tool
- 신규: [[pages/entity/test-tool.md]], [[pages/concept/test-two-tier-system.md]], [[pages/concept/e2e-cmux-first-playwright-fallback.md]], [[pages/concept/external-tool-boundary-stub-insufficient-lesson.md]]
- 출처: task:039

## [2026-06-24] ingest | CLOSE ingest — 태스크 040 OPAL 부트스트랩 스킵 옵션(OPAL_BOOTSTRAP=off)
- 신규: [[pages/concept/opal-bootstrap-skip-gate.md]], [[pages/concept/bootstrapper-marker-ssot-single-point.md]]
- 출처: task:040

## [2026-06-24] ingest | CLOSE ingest — 태스크 042 CLOSE 단계 관련 문서 업데이트 스텝 추가
- 신규: [[close-related-doc-update-before-ingest]]
- 출처: task:042

## [2026-06-24] ingest | CLOSE ingest — 태스크 043 부트스트랩 게이트 설정파일 전환: concept 1건 신규(read-based-gate-pattern), concept 1건 갱신(opal-bootstrap-skip-gate — 040 Bash echo 방식을 043 Read 기반으로 업데이트)
- 신규: [[pages/concept/read-based-gate-pattern.md]]
- 출처: task:043

## [2026-06-26] ingest | CLOSE ingest — 태스크 044 도구-검색-사용법-활용 (tool-scan)
- 신규: [[pages/entity/tool-scan.md]], [[pages/concept/usage-ssot-live-help-principle.md]], [[pages/concept/tool-scan-thin-manifest-federation.md]], [[pages/concept/tool-usage-precheck-error-diagnosis-rule.md]], [[pages/concept/agentic-output-direct-verification-lesson.md]]
- 출처: task:044

## [2026-06-26] ingest | CLOSE ingest — 태스크 045 메모리 관리 개선
- 신규: [[pages/entity/memory-tool.md]], [[pages/concept/memory-lifecycle-graduation-workflow.md]], [[pages/concept/fixture-vs-real-blind-spot-lesson.md]]
- 출처: task:045

## [2026-06-28] ingest | CLOSE ingest — 태스크 046 모델매핑-프로젝트유저-오버라이드: 2-레이어 오버라이드 아키텍처 + 미설정 오류 정책
- 신규: [[pages/concept/model-mapping-2layer-override.md]], [[pages/concept/model-mapping-missing-cell-error-policy.md]]
- 출처: task:046

## [2026-06-29] ingest | CLOSE ingest — 태스크 048 버전-아카이브-각인: concept 3건 누적 (버전결정모델전환/설치기우선순위모델/RED테스트커밋강요교훈)
- 신규: [[pages/concept/version-stamp-export-subst-decision.md]], [[pages/concept/installer-version-priority-model.md]], [[pages/concept/red-test-commit-coercion-guard-lesson.md]]
- 출처: task:048

## [2026-06-30] ingest | CLOSE ingest — 태스크 049 부트스트랩 2-tier 전환
- 신규: [[pages/concept/opal-bootstrap-2tier-model.md]], [[pages/concept/opal-pm-promotion-gate.md]]
- 출처: task:049

## [2026-06-30] ingest | CLOSE ingest — 태스크 050 에이전트 다이제스트: concept 3건 누적 (agent-md-digest-pattern, dedup-pointer-over-copy, strip-deploy-runtime-token-neutral)
- 신규: [[pages/concept/agent-md-digest-pattern.md]], [[pages/concept/dedup-pointer-over-copy.md]], [[pages/concept/strip-deploy-runtime-token-neutral.md]]
- 출처: task:050

## [2026-07-02] ingest | CLOSE ingest — 태스크 051 [ASSISTANT] 마커로 headless(claude -p) 호출을 비서 tier로 캡
- 신규: [[pages/concept/bootstrap-marker-skip-ladder.md]]
- 출처: task:051

## [2026-07-02] ingest | CLOSE ingest — 태스크 052 워크스페이스 Git 일괄 동기화 (git-sync-tool + opal-workspace-sync)
- 신규: [[pages/entity/git-sync-tool.md]], [[pages/entity/opal-workspace-sync.md]], [[pages/concept/skill-registry-index-registration-required-for-discovery.md]], [[pages/concept/fallback-approval-detached-head-precedence.md]]
- 출처: task:052

## [2026-07-10] ingest | CLOSE ingest — 태스크 054 산출물 소유자 호칭 identity 통일: concept 2건 신규 (오염 차단 원칙 + state-tool write-time 치환 메커니즘)
- 신규: [[owner-honorific-contamination-prevention]], [[state-tool-owner-name-write-time-substitution]]
- 출처: task:054

## [2026-07-10] ingest | CLOSE ingest — 태스크 053 brain related 링크필드 정비 + validate 강화
- 신규: [[pages/concept/enforce-rule-legacy-data-surfacing-lesson.md]]
- 출처: task:053

## [2026-07-10] ingest | CLOSE ingest — 태스크 055 opal-cli install 서브커맨드 완전 제거
- 신규: [[pages/concept/opal-cli-install-subcommand-removal.md]]
- 출처: task:055

## [2026-07-10] ingest | CLOSE ingest — 태스크 056 opal-pilot-project-loop(oppl) 루프 오케스트레이터 신설
- 신규: [[pages/concept/oppl-two-loop-orchestrator.md]], [[pages/entity/opal-evaluator-agent.md]], [[pages/concept/oppl-3-ssot-tool-gated-separation.md]], [[pages/concept/oppl-scenario-red-confirmed-gap.md]]
- 출처: task:056

## [2026-07-13] ingest | CLOSE ingest — 태스크 059 opal-agent 부트스트랩 마커 3-way + cold session 지원
- 신규: [[pages/concept/cold-warm-session-separation.md]]
- 출처: task:059

## [2026-07-14] ingest | CLOSE ingest — 태스크 060 브레인 프라임 연결 풀
- 신규: [[brain-prime-connection-pool-design]], [[pool-lock-idiom-contract]], [[warm-handle-single-entry-injection]]
- 출처: task:060

## [2026-07-14] ingest | CLOSE ingest — 태스크 062 브레인답변-레이아웃-워크플로우
- 신규: [[pages/concept/brain-answer-layout-content-driven.md]]
- 출처: task:062

## [2026-07-14] ingest | CLOSE ingest — 태스크 061 콘솔 설정 화면(프라임 풀 토글) — 쓰기 예외 격리 패턴 2호 적용·동시쓰기 방어 표준·설정화면 점진확장 방침 신규 + scenario-lock 혼합트랙 갭 재발 갱신
- 신규: [[pages/concept/console-write-exception-router-isolation.md]], [[pages/concept/config-file-concurrent-write-defense-standard.md]], [[pages/concept/console-settings-incremental-scope-policy.md]]
- 갱신: [[pages/concept/oppl-scenario-red-confirmed-gap.md]]
- 출처: task:061

## [2026-07-15] ingest | CLOSE ingest — 태스크 063 콘솔 브레인 세션 단순화
- 신규: [[console-brain-volatile-single-session]], [[brain-prime-pool-need-based-refill]], [[console-brain-exit-guard-pattern]]
- 출처: task:063

## [2026-07-17] ingest | CLOSE ingest — 태스크 064 커뮤니티 스킬 관리 워크플로우 통일
- 신규: [[community-skill-installation-architecture.md]], [[community-skill-basename-matching.md]], [[community-skill-user-registry.md]]
- 출처: task:064

## [2026-07-17] ingest | CLOSE ingest — 태스크 065 oppl 태스크 실행자(opal-loop-action-agent) 도입
- 신규: [[pages/entity/opal-loop-action-agent.md]], [[pages/concept/oppl-executor-delegation-architecture.md]]
- 출처: task:065

## [2026-07-17] ingest | CLOSE ingest — 태스크 066 루프 액션 에이전트 opal-agent 채널 전환
- 신규: [[oppl-internal-channel-opal-agent]]
- 출처: task:066

## [2026-07-17] ingest | CLOSE ingest — 태스크 067 루프 액션 에이전트 투명 모니터링
- 신규: [[pages/concept/opal-agent-stream-json-passthrough.md]], [[pages/concept/oppl-run-record-journal-dual-observability.md]], [[pages/entity/opal-action-monitor.md]], [[pages/concept/red-first-hybrid-verification-track.md]]
- 출처: task:067

## [2026-07-18] ingest | CLOSE ingest — 태스크 068 opal-action-status(opas) 발동층 스킬 신설
- 신규: [[pages/entity/opal-action-status.md]], [[pages/concept/observability-3layer-protocol-renderer-trigger-separation.md]]
- 출처: task:068

## [2026-07-19] ingest | CLOSE ingest — 태스크 069 oppl 계약 접합면 검증 강화
- 신규: [[pages/concept/oppl-evidence-fidelity-principle.md]], [[pages/concept/oppl-surface-inventory-contract.md]], [[pages/concept/oppl-coverage-conformance-axis-split.md]]
- 출처: task:069

## [2026-07-20] ingest | 태스크 058 CLOSE ingest — PM 개선 루프 tool-gated 재설계
- 신규: [[pages/entity/opal-improve.md]], [[pages/entity/improve-tool.md]], [[pages/entity/fw-inbox-collection.md]], [[pages/concept/pm-improvement-loop-two-tracks.md]], [[pages/concept/local-fw-improvement-classification.md]], [[pages/flow/close-retrospective-hardstep.md]]
- 출처: task:058

## [2026-07-23] ingest | CLOSE ingest — 태스크 070 state-tool task-step 키 주소 체계 도입 1차
- 신규: [[pages/concept/state-tool-task-step-key-address.md]], [[pages/entity/pipeline-json-spec.md]]
- 출처: task:070

## [2026-07-23] ingest | CLOSE ingest — 태스크 072 state-tool STATE.md 다음 액션 자동 파생
- 신규: [[pages/concept/state-tool-next-action-auto-derivation.md]]
- 출처: task:072

## [2026-07-23] ingest | CLOSE ingest — 태스크 074 state-tool import-existing key 유실 결함 수정
- 신규: [[pages/concept/state-tool-import-existing-key-reattachment.md]]
- 출처: task:074

## [2026-07-23] ingest | CLOSE ingest — 태스크 073 TEST-SCENARIO 목표-커버리지 루브릭 게이트 루프
- 신규: [[pages/concept/scenario-goal-coverage-gate-loop.md]], [[pages/concept/070-derivation-engine-perspective-bias-lesson.md]], [[pages/concept/scenario-normalized-contract-pilot-neutral.md]], [[pages/entity/op-scenario-gate-skill.md]]
- 출처: task:073

## [2026-07-23] ingest | CLOSE ingest — 태스크 075 시나리오게이트 확산 1차 (opds·opsdd)
- 신규: [[scenario-gate-pilot-fit-criteria]], [[opds-testscenario-producer-establishment]], [[legacy-row-address-gate-insertion-regression]]
- 출처: task:075

## [2026-07-23] ingest | CLOSE ingest — 태스크 076 파이프라인 todo 미러 hook 강제 자동화
- 신규: [[pipeline-todo-mirror-hook-enforcement]], [[install-hook-ownership-marker-idempotent-upsert]], [[native-todo-panel-llm-only-hook-boundary]]
- 출처: task:076

## [2026-07-29] ingest | CLOSE ingest — 태스크 078 프로젝트 메모리 SSOT MEMORY.md→MEMORY.json 전환
- 신규: [[pages/concept/json-not-token-saving-format.md]], [[pages/concept/silent-loss-prevention-row-accounting-invariant.md]], [[pages/concept/non-gated-write-path-audit-before-ssot-conversion.md]], [[pages/concept/parser-drift-silent-longevity-lesson.md]], [[pages/concept/long-running-worker-infra-failure-mitigation.md]], [[pages/concept/concurrent-task-shared-file-discipline.md]]
- 출처: task:078

## [2026-07-30] ingest | CLOSE ingest — 태스크 079 히스토리 정정명령 신설
- 신규: [[pages/concept/rotating-log-correction-over-deletion.md]], [[pages/concept/backward-compat-default-value-discipline.md]], [[pages/concept/argparse-choices-breaks-json-contract.md]], [[pages/concept/literal-version-test-expectation-fragility.md]], [[pages/concept/manual-scenario-verbatim-output-evidence.md]]
- 출처: task:079

## [2026-08-01] ingest | CLOSE ingest — 태스크 077 코드맵 헤더 작성층
- 신규: [[code-header-dual-source-inheritance]], [[code-map-write-location-decision]], [[exports-generation-tool-verification-division]], [[regression-only-coverage-gate]], [[code-scan-tool]]
- 출처: task:077

## [2026-08-02] ingest | CLOSE ingest — 태스크 081 opds 워커중단-복구프로토콜
- 신규: [[pages/concept/mitigation-recurs-without-ssot-registration.md]], [[pages/concept/governance-single-owner-rule-mapping.md]], [[pages/concept/anchor-load-condition-must-match-target.md]], [[pages/concept/blind-reproduction-verification-test.md]], [[pages/concept/self-edit-line-anchor-drift.md]]
- 출처: task:081

## [2026-08-03] ingest | CLOSE ingest — 태스크 082 opds 코드맵 매니페스트 샤딩
- 신규: [[code-scan-manifest-sharding-design]], [[code-scan-sealed-decision-point-pattern]], [[code-scan-nonblocking-limit-rollout]], [[code-scan-version-constant-freeze]], [[fixture-conflicting-requirements-lesson]]
- 출처: task:082

## [2026-08-04] ingest | CLOSE ingest — 태스크 083 샤드 분할 파이프라인(2축 판정+split 집행+init 온보딩)
- 신규: [[pages/concept/shard-policy-block-vs-nonblock-fallback-criterion.md]], [[pages/concept/code-scan-gate-deadlock-init-placement.md]], [[pages/concept/code-scan-split-execution-precedes-block.md]], [[pages/concept/code-scan-classification-ladder-design.md]], [[pages/concept/code-scan-two-axis-threshold-design.md]], [[pages/concept/code-scan-fixture-policy-override-absorption.md]], [[pages/concept/install-mac-seed-key-loop-generalization.md]], [[pages/concept/code-scan-opal-home-test-isolation.md]], [[pages/concept/round-trip-pre-state-assertion-false-green-guard.md]]
- 출처: task:083

## [2026-08-06] ingest | CLOSE ingest — 태스크 084 PM 대화형 AS-IS 분석 워크플로우
- 신규: [[asis-analysis-five-stage-workflow]], [[asis-workflow-order-over-new-skill]], [[inherit-new-boundary-fixed-before-writing]], [[pm-conversation-readonly-collection-exception]], [[degraded-execution-with-explicit-gap]], [[section-append-at-tail-preserves-backrefs]]
- 출처: task:084

## [2026-08-07] ingest | CLOSE ingest — 태스크 085 릴리즈 체크섬 검증 경로 정합
- 신규: [[dl-contract-download-verify-target-identity]], [[release-asset-presence-single-signal]], [[silent-success-defect-class]], [[green-tests-do-not-imply-contract-conformance]], [[fix-validity-requires-failure-mode-reproduction]], [[installer-verification-path-stub-boundary-sealing]]
- 출처: task:085

## [2026-08-10] ingest | CLOSE ingest — 태스크 086 아키텍처 다이어그램 재작성 (지식 자산 1급 승격·환류 시각화·사실 정합)
- 신규: [[vertical-writing-rotation-glyph-flip]], [[silent-render-failure-deterministic-gate]], [[expected-total-as-reference-not-gate-criterion]], [[knowledge-assets-as-flow-entrypoint]], [[source-measured-figures-over-stale-docs]], [[nojs-flex-rail-over-inline-svg-overlay]]
- 출처: task:086

## [2026-08-10] ingest | CLOSE ingest — 태스크 087 설치 스크립트 Python 최소버전 게이트 + 3.14 설치 유도 (플랫폼 대칭화)
- 신규: [[pages/concept/platform-parity-mirror-before-design.md]], [[pages/concept/delegation-only-file-gate-bypass.md]], [[pages/concept/existence-check-not-version-check.md]], [[pages/concept/pure-function-enables-nondestructive-verification.md]], [[pages/concept/fail-fast-earliest-legible-point.md]]
- 출처: task:087

## [2026-08-11] ingest | CLOSE ingest — 태스크 088 클로즈 메모리히스토리 자동연결
- 신규: [[close-history-auto-link-enforce-conversion]]
- 출처: task:088

## [2026-08-13] ingest | CLOSE ingest — 태스크 090 미전환 6 pilot 파이프라인 스펙 마이그레이션
- 신규: [[pipeline-json-full-adoption-migration]], [[phase-name-stage-value-homonym-boundary]], [[na-status-contract-agentic-init-only]], [[mark-force-decision-log-scope]], [[replacement-goal-verification-scope-gap]]
- 출처: task:090

## [2026-08-14] ingest | CLOSE ingest — 태스크 091 파이프라인 스펙 중복정리(PM Gate SSOT 승격)
- 신규: [[pm-gate-artifact-tool-enforcement]], [[conditional-artifact-gate-ineligibility]], [[pre-edit-baseline-single-capture-invariant]]
- 갱신: [[replacement-goal-verification-scope-gap]]
- 출처: task:091

## [2026-08-15] ingest | CLOSE ingest — 태스크 092 워크트리 작업공간 분리
- 신규: [[pages/entity/worktree-tool.md]], [[pages/concept/worktree-workspace-isolation-axis.md]], [[pages/concept/worktree-slot-existence-to-occupancy-judgment.md]]
- 출처: task:092

## [2026-08-16] ingest | CLOSE ingest — 태스크 093 파이프라인 사용자 확인 행 자동 승인 경로 일원화
- 신규: [[pages/concept/pipeline-user-confirmation-single-status-axis.md]], [[pages/concept/auto-approve-user-confirmation-axis-separation.md]], [[pages/concept/self-modifying-tool-deploy-unit-coupling.md]]
- 출처: task:093

## [2026-08-16] ingest | CLOSE ingest — 태스크 094 STATE.md 파생 섹션 제거·저널화
- 신규: [[pages/concept/state-md-journal-redefinition.md]], [[pages/concept/mirror-gate-must-not-hostage-ssot-record.md]]
- 출처: task:094

## [2026-08-19] ingest | CLOSE ingest — 태스크 095 TEST-SCENARIO 목표계열 선작성 (PLAN 병렬 도출 트랙 신설)
- 신규: [[scenario-prewrite-goal-series-track]], [[prewrite-track-quality-not-efficiency-measurement]], [[prewrite-self-confirming-triple-defense]], [[subsection-number-insertion-preserves-citations]], [[marker-literal-check-meta-circular-false-positive]], [[global-deploy-after-verification-ordering]], [[worker-abort-artifact-measured-adjudication]]
- 출처: task:095

