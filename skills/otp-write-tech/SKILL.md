---
name: otp-write-tech
description: |
  **서비스 기획 산출물 네트워크 오케스트레이터**. 기술 산출물(PRD, TRD, 서비스 정책서, IA 등)을 논리적 네트워크로 관리한다.
  PM이 워커를 병렬 디스패치하여 문서를 분석/작성하고, 교차 논리 검토와 정합성 검증으로 문서 간 일관성을 보장한다.
  반드시 이 스킬: "otp-write-tech", "otpwt", "기획 문서 세트", "기술 산출물 작성", "기획 문서 검토", "기획 문서 최신화".
---

# otp-write-tech

서비스 기획 산출물 네트워크 오케스트레이터.

## 설계 원칙

- **문서가 인터페이스** — 프로젝트 문서(`docs/`)만 참조, 다른 스킬의 존재를 모른다
- **PM 중심 관리** — 교차 검토/진단/배치 편성/최종 판정/문서 등록
- **복수 문서 + 병렬 처리** — 정책서 N개 등, 독립 문서는 워커 병렬 디스패치

## 커버 범위

**필수 4종**: PRD, TRD, 서비스 정책서(복수), IA(기능 포함)
**선택 4종**: 기능도, 순서도, 운영 정책서, 서비스 매뉴얼
**순서 체인**: PRD → TRD → 서비스 정책서 → IA (역방향도 가능)

## 산출물 저장 구조

- `docs/` = 프로젝트 환경/기반 메타 문서 (`PROJECT.md`가 SSOT)
- 프로젝트 산출물은 `docs/` 밖 별도 폴더
- PM이 `docs/PROJECT.md` 읽어 기존 폴더 구조 파악 → 기존 구조 따름
- 구조 없으면 default 제안 (`outputs/01_기획/`, `outputs/02_설계/` 등) → `PROJECT.md`에 기록

## 3가지 모드

| 모드 | 동작 |
|------|------|
| 작성 | Phase 2(간략) → Phase 3(작성) → Phase 4(검증) |
| 수정 | Phase 1(분석) → Phase 2(영향 진단) → Phase 3(수정) → Phase 4(검증) |
| 분석 | Phase 1(분석) → Phase 2(진단 보고) → 승인 → Phase 3(보완) → Phase 4(검증) |

## 4 Phase 파이프라인

### Phase 1: 병렬 분석

- PM이 기존 문서 경로 스캔 (Glob)
- 문서별 워커 디스패치 (Agent, 병렬) — 각 워커가 문서 읽고 요약/이슈 반환
- 워커 프롬프트: `references/network-guide.md` "Phase 1 워커 프롬프트" 참조

### Phase 2: PM 진단

PM이 직접 수행:

1. 워커 결과 종합
2. 교차 논리 검토 (`references/network-guide.md` 연결 맵 참조)
3. 누락/불일치 진단
4. 문서별 조치 판단:
   - **보강**: 품질 OK, 누락/수정만 (버전 업)
   - **재작성**: 구조 불일치 (기존 내용 계승하여 표준 구조로)
   - **신규**: 해당 산출물 없음
5. `diagnosis.json` 생성 (스키마: `references/network-guide.md` 참조)
6. 배치 편성 (`depends_on` 기반: `references/network-guide.md` 참조)
7. 사용자에게 진단 보고 → 사용자가 조치 확인/조정

### Phase 3: 병렬 작성

- PM이 `diagnosis.json` 파싱
- 배치별 순회:
  - 독립 문서 → 워커 병렬 디스패치
  - 의존 문서 → 다음 배치 (이전 배치 완료 후)
- 워커 프롬프트: `references/network-guide.md` "Phase 3 워커 프롬프트" 참조
- 각 배치 완료 → PM 검토 → 사용자 확인 게이트
- 완료된 산출물은 `docs/PROJECT.md` 문서 테이블에 등록

### Phase 4: 정합성 검증

- QA 워커 디스패치 (`references/consistency-rules.md` 기반)
- 유형 간 검증 + 유형 내 검증
- `diagnosis.json`의 `connected_to`로 검증 범위 자동 결정
- PM 최종 판정:
  - **Pass** → `DONE.md` 생성, 사용자 보고
  - **Fail** → 수정 지시 (Phase 3로 부분 재진입)

## STATE.md 관리

기존 오케스트레이터 패턴에 네트워크 상태를 확장:

```markdown
# STATE: {제목}
> 최종 갱신: YYYY-MM-DD HH:mm

## 현재 상태
- 모드: {작성 / 수정 / 분석}
- Phase: {1 / 2 / 3 / 4}
- 상태: {진행 중 / 대기 중 / 완료}

## 네트워크 상태
| 산출물 | 유형 | 상태 | 버전 | 경로 |
|--------|------|------|------|------|

## 배치 계획
| Batch | 문서 | 의존 | 상태 |
|-------|------|------|------|

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
```

## 게이트 체크포인트

- **Phase 2 → 3**: 진단 보고서(`diagnosis.json`) 사용자 확인
- **Phase 3 배치별**: 배치 완료 시 PM 검토 → 사용자 확인
- **Phase 4**: 정합성 검증 결과 사용자 보고

## 프로젝트 메모리 동기화

프로젝트 `.opal/MEMORY.md` 존재 시 작업 히스토리 갱신.

## 문서 표준

opal-doc-standard 적용: `~/.opal/references/opal-doc-standard.md`

## 참조 가이드

- `references/network-guide.md` — 산출물 정의, 연결 맵, diagnosis.json 스키마, 워커 프롬프트, 배치 규칙, IA 형식
- `references/consistency-rules.md` — 유형 간/내 검증, QA 워커 프롬프트

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 |
