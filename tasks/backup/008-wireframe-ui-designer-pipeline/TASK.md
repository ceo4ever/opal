# TASK: wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 작성일: 2026-03-13 | 작업 유형: 🆕 신규 개발 + 🔧 기능 개선

## 작업 목표

wireframe-builder 스킬을 UI 분석·설계 도구로 전환하고, 그 산출물(wireframe.md)을 shadcn/ui 기반 UI로 구현하는 ui-designer 스킬을 신규 개발하여 **분석→설계→구현 파이프라인**을 구축한다.

## 배경

현재 wireframe-builder는 정책서를 입력받아 단일 HTML 와이어프레임을 직접 생성한다. 이 방식은:
- 분석/설계 과정이 암묵적이어서 중간 산출물이 없음
- 그레이스케일 HTML 프로토타입이라 실제 프로덕션 UI와 거리가 멀음
- shadcn/ui 같은 컴포넌트 라이브러리와 연계가 안 됨

캡틴의 비전:
1. **wireframe-builder**: 정책서/요구사항 → 분석·설계 → 구조화된 wireframe.md 생성
2. **ui-designer** (신규): wireframe.md → shadcn/ui + Next.js 기반 UI 구현 (단일 HTML 출력도 지원)

이 파이프라인이 완성되면 `정책서 → 설계 문서 → 실동작 UI`까지 체계적으로 진행할 수 있다.

## 요구사항

### wireframe-builder 개선
- [ ] 정책서, 서비스 요청사항 등을 입력받아 분석·설계 수행
- [ ] 화면 목록, 화면별 레이아웃·구조·기능을 도출
- [ ] 네비게이션 흐름, 화면 간 관계를 정의
- [ ] shadcn 컴포넌트 매핑을 포함
- [ ] 구조화된 wireframe.md 산출물 생성

### ui-designer 신규 개발
- [ ] wireframe.md를 입력으로 받아 정형 스키마 기반으로 파싱
- [ ] shadcn/ui 컴포넌트 기반 React 코드 생성 (프로토타입·프로덕션 공통 컴포넌트)
- [ ] 프로토타입 모드: web-artifacts-builder 파이프라인으로 단일 HTML 번들 생성 (Parcel + html-inline)
- [ ] 프로덕션 모드: Next.js App Router + shadcn 스킬 연계 프로젝트 생성
- [ ] 두 모드 간 React + shadcn 컴포넌트 코드 재활용 (공통 컴포넌트 → 출력 방식만 분기)
- [ ] shadcn 스킬의 Critical Rules 준수 (컴포넌트 구성, 스타일링, 폼 패턴 등)
- [ ] web-artifacts-builder의 번들링 파이프라인 참조/활용

### 레지스트리 업데이트
- [ ] skills.md에 wireframe-builder 설명 업데이트
- [ ] skills.md에 ui-designer 추가
- [ ] CLAUDE.md 소스 구조 설명에 ui-designer 반영

## 성공 기준

- [ ] wireframe-builder가 정책서/요구사항 입력 → wireframe.md 산출물을 생성할 수 있다
- [ ] wireframe.md가 ui-designer가 파싱 가능한 정형화된 스키마를 따른다
- [ ] ui-designer가 wireframe.md 입력 → shadcn 기반 단일 HTML 파일을 생성할 수 있다
- [ ] skills.md 레지스트리에 두 스킬이 정확히 등록되어 있다
- [ ] 파이프라인 E2E: 정책서 → wireframe-builder → wireframe.md → ui-designer → 동작하는 UI 산출물

## 제약 조건

- 기존 프레임워크 스킬 구조(`skills/{name}/SKILL.md`)를 따른다
- wireframe.md 산출물은 ui-designer가 기계적으로 파싱할 수 있도록 구조화한다
- shadcn 스킬의 Critical Rules를 ui-designer가 준수하도록 참조한다
- 설치 스크립트(install-mac.sh)와 호환되어야 한다 (skills/ 디렉토리 기준)

## 관련 문서

- `skills/wireframe-builder/SKILL.md` — 현재 wireframe-builder 스킬
- `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md` — shadcn 스킬
- `~/.opal/references/skills.md` — 스킬 레지스트리
- `CLAUDE.md` — 프레임워크 아키텍처 정의
