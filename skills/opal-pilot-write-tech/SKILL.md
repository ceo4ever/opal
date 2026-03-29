---
name: opal-pilot-write-tech
description: |
  **서비스 기획 산출물 네트워크 오케스트레이터**. 기술 산출물(PRD, TRD, 서비스 정책서, IA 등)을 논리적 네트워크로 관리한다.
  PM이 워커를 병렬 디스패치하여 문서를 분석/작성하고, 교차 논리 검토와 정합성 검증으로 문서 간 일관성을 보장한다.
  반드시 이 스킬: "opal-pilot-write-tech", "opwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토", "기획 문서 최신화".
---

# opal-pilot-write-tech

서비스 기획 산출물 네트워크 오케스트레이터.

## Harness
> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**모드**: {작성 / 수정 / 분석}

## 설계 원칙

- **문서가 인터페이스** — 프로젝트 문서(`docs/`)만 참조, 다른 스킬의 존재를 모른다
- **PM 중심 관리** — 교차 검토/진단/배치 편성/최종 판정/문서 등록
- **복수 문서 + 병렬 처리** — 정책서 N개 등, 독립 문서는 워커 병렬 디스패치

## 커버 범위

**필수 4종**: PRD, TRD, 서비스 정책서(복수), IA(기능 포함)
**선택 4종**: 기능도, 순서도, 운영 정책서, 서비스 매뉴얼
**순서 체인**: PRD → TRD → 서비스 정책서 → IA (역방향도 가능)

## 산출물 저장 구조

- `docs/` = 메타 문서 (`PROJECT.md`가 SSOT), 산출물은 별도 폴더
- PM이 `docs/PROJECT.md`로 기존 구조 파악 → 없으면 default 제안 → `PROJECT.md`에 기록

## 3가지 모드

| 모드 | 동작 |
|------|------|
| 작성 | Phase 2(간략) → Phase 3(작성) → Phase 4(검증) |
| 수정 | Phase 1(분석) → Phase 2(영향 진단) → Phase 3(수정) → Phase 4(검증) |
| 분석 | Phase 1(분석) → Phase 2(진단 보고) → 승인 → Phase 3(보완) → Phase 4(검증) |

## 4 Phase 파이프라인

### Phase 1: 병렬 분석
- PM이 기존 문서 경로 스캔 → 문서별 워커 병렬 디스패치 (요약/이슈 반환)
- 워커 프롬프트: `references/network-guide.md` "Phase 1 워커 프롬프트"

### Phase 2: PM 진단
PM 직접 수행: 워커 결과 종합 → 교차 논리 검토 → 누락/불일치 진단 → 문서별 조치(보강/재작성/신규) → `diagnosis.json` 생성 → 배치 편성(`depends_on` 기반) → 사용자 진단 보고

### Phase 3: 병렬 작성
- `diagnosis.json` 파싱 → 배치별 순회 (독립=병렬, 의존=순차)
- 워커 프롬프트: `references/network-guide.md` "Phase 3 워커 프롬프트"
- 배치 완료 → PM 검토 → 사용자 확인 → `docs/PROJECT.md` 등록

### Phase 4: 정합성 검증
- QA 워커 디스패치 (`references/consistency-rules.md` 기반, 유형 간+내 검증)
- PM 최종 판정: Pass → DONE.md, Fail → Phase 3 부분 재진입

## STATE.md 네트워크 확장

Harness STATE.md 기본 구조에 도메인 고유 섹션 추가:
- `{모드}`: 작성/수정/분석, `{단계 목록}`: Phase 1~4
- **네트워크 상태**: 산출물 | 유형 | 상태 | 버전 | 경로
- **배치 계획**: Batch | 문서 | 의존 | 상태

## 게이트 체크포인트

Harness 기본 게이트 + Phase별 추가:
- **Phase 2→3**: `diagnosis.json` 사용자 확인
- **Phase 3 배치별**: PM 검토 → 사용자 확인
- **Phase 4**: 정합성 검증 결과 보고

## 문서 표준

opal-doc-standard 적용: `~/.opal/references/opal-doc-standard.md`

## 참조 가이드

- `references/network-guide.md` — 산출물 정의, 연결 맵, diagnosis.json 스키마, 워커 프롬프트, 배치 규칙, IA 형식
- `references/consistency-rules.md` — 유형 간/내 검증, QA 워커 프롬프트

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
| v1.1 | 2026-03-28 | Harness 참조 전환으로 슬림화 |
| v1.2 | 2026-03-29 | 컴포넌트 리네이밍 (042) |
