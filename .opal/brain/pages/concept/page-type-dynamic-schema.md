---
type: concept
title: 페이지 타입 동적화 — SCHEMA SSOT
tags:
- architecture
- brain
- schema
- dynamic-type
sources:
- task:016
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: active
---
## 개념 요약

brain-tool의 페이지 타입 세트를 하드코딩에서 `schema-template.md §1.5` 동적 로드로 전환한 아키텍처 결정. 기본 4종(entity/concept/flow/synthesis)은 검토 후보일 뿐, init이 origin 분석 후 채택/제외/추가/교체하여 SCHEMA가 타입 SSOT가 된다.

## 배경·문제 (WHY)

015에서 `brain_tool.py:29-38`이 `PAGE_TYPES`·`TYPE_TO_CATEGORY`·`CATEGORY_ORDER`·`BRAIN_DIRS`를 하드코딩했다. 프로젝트 특성에 맞는 커스텀 타입 추가가 불가능하고, init이 구조를 제안해도 반영 경로가 없었다. "enforce, don't advise" 원칙과 "결정론적 작업 = brain-tool" 원칙을 함께 충족하려면 타입 세트 자체가 마크다운 선언으로 이동해야 했다.

## 결정 내용 (HOW)

- **2계층 타입 모델**: `DEFAULT_PAGE_TYPES`(기본 후보 상수, 기존 테스트 호환) + `load_page_types(brain_root)` 함수(SCHEMA §1.5 파싱, 부재 시 폴백).
- **SCHEMA §1.5 파싱 규약**: `## 1.5 페이지 타입 정의` 절의 마크다운 테이블에서 `type`·`category` 컬럼을 읽어 `TYPE_TO_CATEGORY`·`CATEGORY_ORDER`·`BRAIN_DIRS`(`pages/{type}`)를 동적 파생.
- **argparse choices 제거**: 파서 빌드 시점에 brain_path 미확정이므로 `--type` 검증을 `cmd_add_page` 내부로 이동. 위반 시 `invalid_page_type` 에러 코드 재사용.
- **graceful degradation**: SCHEMA 부재/파싱 실패 시 `DEFAULT_PAGE_TYPES` 폴백.
- **`init --types <csv>` 옵션**: SKILL이 사용자 확정 타입 세트를 init에 전달하는 경로.

## 영향·관계

- `opal/tools/brain-tool/brain_tool.py` — `load_page_types`, `DEFAULT_PAGE_TYPES`, 동적 파생 상수 3종
- `opal/tools/brain-tool/templates/schema-template.md` — §1.5 "페이지 타입 정의" 테이블
- `opal/tools/brain-tool/tests/test_brain_tool.py` — TestDynamicPageTypes 6케이스 (83 passed)
- `opal/skills/opal-brain/SKILL.md` — init STEP 0

## 근거 출처

`task:016` PLAN §0 M-1, §2 U-1/U-2 — `opal/tools/brain-tool/brain_tool.py:29-60`(상수 동적화), `opal/tools/brain-tool/templates/schema-template.md:§1.5`(타입 선언 블록).
</content>
</invoke>
## 관련

- [[opal-brain-system]] — 이 타입 동적화가 적용된 brain 시스템 본체
- [[wiki-intelligence-decisions-016]] — 타입 완전 동적화를 확정한 016 의사결정 묶음
