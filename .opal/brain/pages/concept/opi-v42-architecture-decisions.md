---
type: concept
title: opi v4.2 아키텍처 결정 — 심층 분석·멀티서비스·워커 디스패치
tags:
- opi
- opal-project-init
- architecture-decision
- multi-service
- worker-dispatch
sources:
- task:020
related: [skill-opal-project-init, opi-impl-injectable-depth-standard]
created: '2026-06-14'
updated: '2026-06-14'
status: active
---

## 개요

opi v4.2에서 채택된 4개의 비자명 아키텍처 결정: (1) code-analysis-guide 추출 패턴, (2) 멀티서비스 문서 세트 경로 표준, (3) 대형 코드베이스 전문 워커 디스패치 임계, (4) 성숙 레포 자체 docs 흡수 분기.

## 결정 1 — code-analysis-guide.md 추출 (헌법 §2 단순성 적용 패턴)

**배경**: 최신화 Step C/D에 이미 검증된 심층 탐색·재대조 방법론이 있는데, 초기화 Phase 3에 동일 내용을 복붙하면 SKILL.md 두 곳에 중복 발생.

**결정**: 방법론을 `references/code-analysis-guide.md`로 추출, 초기화와 최신화 양쪽이 이를 참조. SKILL.md 본문에는 "언제/어떤 산출물에" 적용하는지(분기·조건)만 남기고, "어떻게 탐색하는지"(방법론)는 가이드로 위임.

**패턴**: `docs-guide.md`가 docs 작성 방법을 위임받는 분리 패턴과 동일. 헌법 §2 "Remove a duplicated existing pattern before introducing a new one" 적용.

**code-analysis-guide.md 4개 블록**:
1. 블록 1 — 심층 탐색 패턴 표 (11행: 엔트리포인트·베이스클래스·미들웨어·설정로더·라우터·유틸·레이어 경계·트랜잭션·상태 전이·도메인 패턴·새 기능 추가 경로)
2. 블록 2 — BE/FE 스택별 탐색 체크리스트 (도구명 금지, 행위로 기술)
3. 블록 3 — 작성 후 코드 1:1 재대조 절차 (4분류: 일치/불일치/문서에없음/실제에없음)
4. 블록 4 — 레포 구조 판별 + 자체 docs 흡수 절차

파일 참조: `opal/skills/opal-project-init/references/code-analysis-guide.md`

## 결정 2 — 멀티서비스 문서 세트 경로 표준

**결정**: `docs/services/{서비스명}/` (OPAL 표준 일관성 우선)

**배경**: pointail/backend 정답지는 `docs/claude/services/{서비스}/`를 사용하나, 이는 특정 프로젝트 관례. OPAL 산출 표준은 `docs/` 직속 경로를 기준으로 한다.

**구조 분기**:

| 구조 | 판별 | 문서 세트 |
|------|------|----------|
| 단일레포·단일서비스 | 코드 디렉토리 1벌, 다중 빌드파일 없음 | ARCHITECTURE/BACKEND/FRONTEND 단일 세트 |
| 멀티레포(우산) | 하위 독립 `.git` N개 | 레포별 문서 세트 |
| 멀티서비스(단일레포) | 다중 빌드모듈 + 서비스 경계 (`settings.gradle.kts` 등) | 공통 ARCHITECTURE + `docs/services/{서비스}/` |

**[MUST] 하위호환**: 멀티 구조 아니면 기존 단일 문서 세트로 동작 — 기존 사용자 영향 0.

## 결정 3 — 대형 코드베이스 전문 워커 디스패치 임계

**결정**: 코드 디렉토리(영역) 수 **≥ 2** 또는 빌드 모듈 수 **≥ 10** 시 영역별 전문 워커 디스패치.

**근거**: pointail/backend living reference = 50개 Gradle 모듈 × 5개 서비스. 이 규모에서 PM 단독 표면 훑기는 HOW 섹션 품질 보장 불가.

**에이전트 매핑**: Backend → `opal-be-agent`, Frontend → `opal-fe-agent` (기존 SKILL.md `:298-305` 재사용)

**opgc 패턴 재사용**: "PROJECT.md 프로젝트 구성 기반 매트릭스 + fallback" 패턴을 디스패치 분기로 재사용. 신규 디스패치 메커니즘 발명 금지.

**폴백**: 임계 미만(소형) → PM 직접 수행 / 서브에이전트 미지원 플랫폼 → PM 직접.

## 결정 4 — 성숙 레포 자체 docs 흡수 vs 빈약 레포 직접 생성 분기

**분기 로직**:
```
코드 디렉토리 내 자체 docs 탐색
├─ 발견 (성숙 레포: ARCHITECTURE/ADR/docs/) → 정제·흡수 경로
│   1. 자체 docs Read → HOW 정보 추출
│   2. docs-guide.md 템플릿 슬롯 매핑·정제
│   3. [MUST] 출처 추적 보존: "원본: {레포}/docs/{파일} §{섹션}" 기재
│   4. 코드와 재대조 (블록 3) — stale 문서 맹신 금지
└─ 빈약/없음 → 직접 생성 경로 (블록 1~3 심층 분석으로 생성)
```

**[MUST]** 흡수 시 출처 추적: 흡수한 내용에 원본 docs 경로·섹션을 반드시 기재. 헌법 §4: 자체 docs도 코드 재대조로 검증.

## 영향 범위

- `opal/skills/opal-project-init/SKILL.md` (v4.0.0 → v4.2.0)
- `opal/skills/opal-project-init/references/code-analysis-guide.md` (신규)
- `opal/skills/opal-project-init/references/docs-guide.md` (템플릿 심화)

## 관련 페이지

- [[skill-opal-project-init]]
- [[opi-impl-injectable-depth-standard]]
- [[skill-opal-pilot-gc]] — 디스패치 패턴 선례
