# TASK: CLOSE 단계 관련 문서 업데이트 스텝 추가

> 작성일: 2026-06-24 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic

## 작업 목표

모든 pilot SKILL.md의 CLOSE 단계에서 `op-brain-ingest` 디스패치 직전에 "관련 문서 업데이트" 스텝을 삽입한다. 태스크 완료 시 기획·설계·프로젝트 문서가 최신화된 상태로 brain ingest가 이루어지도록 보장한다.

## 배경

현재 CLOSE 단계: `DONE.md 생성 → op-brain-ingest → 완료 보고`  
문제: brain ingest 전에 PROJECT.md 레지스트리에 등재된 관련 문서(ARCHITECTURE.md, 기획서 등)가 태스크 결과를 반영하지 않은 상태일 수 있어, ingest 품질이 저하됨.

## 배경 분석 (대화에서 도출)

- **대상 파일 8개** 확인: opd / opp / op-data-design / op-dev-short / op-dev-wireframe / op-gc / op-sdd / op-write-tech
- **각 파일의 CLOSE 구조**: DONE.md 생성(단계 1) → op-brain-ingest(단계 2 또는 최종) → 완료 보고 패턴이 공통
- **op-gc, op-sdd**는 CLOSE 항목 수가 다름(op-sdd: 4항목, op-gc: DONE.md+brain 순서 상이) — PLAN에서 개별 확인 필요

## 확정된 설계 방향 (대화에서 합의)

- **삽입 위치**: DONE.md 생성 직후, `op-brain-ingest` 디스패치 직전
- **기준**: PROJECT.md 레지스트리 + 태스크 changed_files 양쪽을 종합
- **수행 방식**: PM이 판단 + 직접 수정 또는 워커 호출 (없으면 스킵)
- **신규 스텝 번호**: 기존 `op-brain-ingest` 번호를 +1 밀어내고 그 자리에 삽입

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 8개 pilot SKILL.md CLOSE에 관련 문서 업데이트 스텝 추가 | - | - |
| 범위 | opal/skills/opal-pilot-*/SKILL.md (CLOSE 섹션만 수정) | - | - |
| 제약 | 기존 CLOSE 흐름(DONE.md→brain ingest→완료 보고) 유지, 스텝 번호 일관성 | - | - |
| 완료기준 | 8개 파일 모두 CLOSE 내 brain ingest 직전에 "관련 문서 업데이트" 스텝이 존재하고, PROJECT.md 레지스트리 + changed_files 기반 설명이 포함되며, 스텝 번호가 정합적으로 재번호됨 | - | - |

## 요구사항

- [ ] F-1: 8개 pilot SKILL.md CLOSE 섹션에 "관련 문서 업데이트" 스텝 삽입  
  - **무엇을**: op-brain-ingest 직전에 관련 문서 업데이트 스텝(텍스트 블록) 추가  
  - **어디에**: 각 파일의 CLOSE 섹션 `op-brain-ingest 디스패치` 항목 바로 앞  
  - **왜**: brain ingest 전 관련 문서 최신화 보장 (확정 방향 §3)  
  - **AC**: 8개 파일 모두 CLOSE 내 `op-brain-ingest` 항목 바로 위에 관련 문서 업데이트 항목이 존재하고, "PROJECT.md 레지스트리" + "changed_files" 키워드가 해당 항목에 포함됨

- [ ] F-2: 스텝 번호 재정렬  
  - **무엇을**: 신규 스텝 삽입으로 인한 이후 항목 번호 +1 조정  
  - **어디에**: 각 파일의 CLOSE 섹션 내 번호가 있는 항목  
  - **왜**: 문서 내부 정합성 유지  
  - **AC**: CLOSE 내 모든 항목 번호가 1부터 연속적으로 정렬됨

- [ ] F-3: 변경이력 행 추가 (8개 파일)  
  - **무엇을**: 각 SKILL.md 변경이력 표에 신규 행 추가  
  - **어디에**: 각 파일의 변경이력 섹션  
  - **왜**: 프로젝트 AGENT.md 업무 수행 지침 §문서 변경이력 의무  
  - **AC**: 8개 파일 모두 변경이력에 `2026-06-24` + `042` 포함 행이 있음

## 제약 조건

- `~/.opal/` 직접 편집 금지 — `opal/skills/opal-pilot-*/SKILL.md` 소스만 수정
- 변경이력 표 행 추가 의무 (프로젝트 AGENT.md §업무 수행 지침)
- CLOSE 외 다른 섹션 수정 금지 (Surgical Changes 원칙)

## 기술 스택

- Markdown 문서 수정
- grep 기반 검증 (TEST)

## 관련 문서

| # | 유형 | 문서명 | 경로 | 참조 이유 |
|---|------|--------|------|----------|
| D-1 | 소스 | opal-pilot-dev SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | CLOSE STEP 6 수정 대상 |
| D-2 | 소스 | opal-pilot-project SKILL.md | `opal/skills/opal-pilot-project/SKILL.md` | CLOSE STEP 4 수정 대상 |
| D-3 | 소스 | opal-pilot-data-design SKILL.md | `opal/skills/opal-pilot-data-design/SKILL.md` | CLOSE STEP 6 수정 대상 |
| D-4 | 소스 | opal-pilot-dev-short SKILL.md | `opal/skills/opal-pilot-dev-short/SKILL.md` | CLOSE STEP 5 수정 대상 |
| D-5 | 소스 | opal-pilot-dev-wireframe SKILL.md | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | CLOSE STEP 4 수정 대상 |
| D-6 | 소스 | opal-pilot-gc SKILL.md | `opal/skills/opal-pilot-gc/SKILL.md` | CLOSE STEP 4 수정 대상 (구조 상이) |
| D-7 | 소스 | opal-pilot-sdd SKILL.md | `opal/skills/opal-pilot-sdd/SKILL.md` | CLOSE Phase 6 수정 대상 (4항목) |
| D-8 | 소스 | opal-pilot-write-tech SKILL.md | `opal/skills/opal-pilot-write-tech/SKILL.md` | CLOSE 단계 수정 대상 |
| D-9 | 설계 | 프로젝트 AGENT.md | `.opal/AGENT.md` | 변경이력 의무, 금지사항 |
