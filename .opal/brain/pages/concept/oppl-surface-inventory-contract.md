---
type: concept
title: 계약 표면 인벤토리 — surfaces.json 단일 IR
tags:
- oppl
- contract
- surfaces-json
- schema
sources:
- task:069
related:
- oppl-evidence-fidelity-principle
- oppl-coverage-conformance-axis-split
- oppl-3-ssot-tool-gated-separation
created: '2026-07-19'
updated: '2026-07-19'
status: active
---
## 개념 요약

CONTRACT 단계 산출물에 기계가독 "표면 인벤토리"(`surfaces.json`)를 필수화한다. 계약에 정의된 API·엔드포인트·인증 표면을 구조화 JSON 하나로 수렴시켜, 이후 커버리지·conformance 게이트가 문서 파싱 없이 소비하게 한다.

## 결정 배경 (WHY)

실전 사고에서 CONTRACT §3.3 엔드포인트 표에 auth 행 자체가 없어 BE/FE가 로그인 응답 형태를 각자 발명했고, budgets/decisions 표면은 계약에 있었지만 백로그 분해에서 대응 태스크가 미배정됐다 — "계약 표면 ↔ 백로그 커버리지" 대조 자체가 아무도 하지 않는 구조였다. CONTRACT가 3파트+기계검증절만 요구하고 표면 전수 나열 의무가 없었던 것이 근본 원인이다.

## 결정 내용 (HOW)

- **작성 SSOT(조건부 이원화)**: API 프로젝트는 OpenAPI(YAML) spec을 1순위 작성 원천으로 삼는다. 비-API 프로젝트(CLI/라이브러리/배치)는 표면 목록을 직접 작성한다. 이 분기는 CONTRACT 작성 단계(D4, Planner)에 격리된다.
- **게이트 소비 인터페이스는 단일**: 커버리지·conformance 게이트 도구는 오직 `surfaces.json`(구조화 JSON 중간 표현)만 소비한다. OpenAPI→surfaces 변환(securitySchemes→auth 포함)이나 비-API 직접 작성은 모두 D4에서 완료되어 surfaces.json으로 수렴하며, 도구는 YAML·markdown을 직접 파싱하지 않는다.
- **JSON 채택 근거**: backlog-tool은 표준 라이브러리 전용이라 YAML 파서(PyYAML) 도입이 금지되고, 마크다운 표 파서는 결합도가 취약하다. JSON은 stdlib `json`으로 견고 파싱되며 신규 패키지 도입이 0이다.
- **구조**: `{schema_version, origins:{dev,prod}, surfaces:[{id,resource,auth:"required|none",request_shape,response_shape,kind}]}`. 인증 표면(로그인 자체)도 반드시 등재한다. `origins`는 웹 클라이언트 존재 시만 선언(nullable) — CORS 결정론 검사의 계약 근거.
- **소유 위치**: CONTRACT 도메인 산출물로 3-SSOT(backlog/state/test-scenario) 밖에 위치한다(`tasks/{NNN}-oppl-{프로젝트명}/surfaces.json`). 두 게이트 도구가 읽지만 3-SSOT 일원이 아니므로 [[oppl-3-ssot-tool-gated-separation]] 축 분리 위반이 아니다.
- **Evaluator 연동**: opal-evaluator-agent Base 루브릭에 ⑦표면 완전성(PRD/TRD/여정 대비 누락, Likert) ⑧auth 필드 완전성(binary) ⑨origin 선언(웹 클라이언트 프로젝트, binary) 항목이 추가되었다.

## 영향 범위

- `opal/skills/opal-pilot-project-loop/references/contract.md` §2.1 origin 선언 의무, §2.2 표면 인벤토리 [MUST], §2.2.1 surfaces.json 스펙
- `opal/skills/opal-pilot-project-loop/SKILL.md` D4 디스패치 프롬프트(surfaces.json 생성 요구)
- `opal/agents/opal-evaluator-agent/AGENT.md` target_artifacts에 surfaces.json 추가

## 관련 페이지

- [[oppl-evidence-fidelity-principle]]
- [[oppl-coverage-conformance-axis-split]]
- [[oppl-3-ssot-tool-gated-separation]]
