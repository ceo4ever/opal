# TASK: 멀티 플랫폼 모델 매핑 참조 문서 + 스킬 적용

> 작성일: 2026-03-29 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

플랫폼(Claude, Gemini, OpenAI 등)별 LLM 모델을 레벨 기반으로 매핑하는 참조 문서를 작성하고, 오케스트레이터 스킬의 model override를 이 참조 기반으로 전환한다.

## 배경

현재 모든 오케스트레이터(opd/opds/opdw/opp)의 워커 디스패치 model override가 Claude 전용(haiku/opus/sonnet)으로 하드코딩되어 있다. OPAL은 멀티 플랫폼 프레임워크(Claude Code, Cursor, Gemini, OpenAI)인데, 모델 정의가 Claude만 커버하는 상태.

## 요구사항

- [ ] 모델 매핑 참조 문서 신규 작성 (`opal-model-mapping.md`)
  - 레벨 기반 모델 추상화 정의 (예: light/standard/advanced)
  - 플랫폼별 모델 매핑 테이블 (Claude, Gemini, OpenAI 등)
  - 스킬에서 참조하는 방법/형식 가이드
- [ ] 오케스트레이터 스킬의 model override를 참조 문서 기반으로 수정

## 제약 조건

- 참조 문서는 `~/.opal/references/`에 배치
- 소스는 `opal/core/references/`에 작성, install-mac.sh로 배포

## 관련 문서

- `.opal/memory/project_multi_platform_model_mapping.md` (기존 메모리)
- `~/.opal/skills/opal-pilot-dev/SKILL.md` (현재 model override 예시)
- `~/.opal/references/opal-harness.md`
