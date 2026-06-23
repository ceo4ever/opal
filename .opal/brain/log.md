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

