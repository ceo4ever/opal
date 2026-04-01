# TASK: opwt IA 산출물 JSON + Mermaid 이중 출력

> 작성일: 2026-04-01 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opwt의 IA 산출물 형식을 JSON + Mermaid 사이트맵 이중 출력으로 확정하여, IA 작성 시 구조 데이터(JSON)와 시각화(Mermaid)를 동시에 생성한다.

## 배경

현재 IA는 JSON 작성 후 검토 시 xlsx 변환을 권장하는 구조다. xlsx는 협업 도구에 의존하고 시각화 품질이 떨어진다. Mermaid `flowchart TD`로 계층 구조를 시각화하면 기획 검토 단계에서 별도 도구 없이 사이트맵을 확인할 수 있고, PRD/정책서 검토 시 논리적 흐름 파악이 쉬워진다.

## 요구사항

### A. network-guide.md §9 IA 형식 가이드 업데이트

- [ ] A1. IA 산출물 형식을 "JSON + Mermaid" 이중 출력으로 재정의
- [ ] A2. Mermaid 변환 스펙 추가:
  - JSON 필드 → Mermaid 매핑 규칙 (id, name, depth, parent_id, access → classDef)
  - `classDef` 스타일 기준 (depth별 색상, access별 색상)
  - 파일명 규칙 (`ia.json` → `ia.md` 또는 `ia-sitemap.md`)
  - 대규모 IA 분리 기준 (노드 50개 초과 시 도메인별 분리)
- [ ] A3. xlsx 변환 섹션 → "검토 도구 내보내기"로 대체 (xlsx는 선택, Mermaid가 기본)
- [ ] A4. .md 폴백 섹션 정리 (Mermaid .md와 혼동 방지)

### B. SKILL.md 커버 범위 업데이트

- [ ] B1. IA 산출물 설명에 "JSON + Mermaid 사이트맵" 명시
- [ ] B2. 변경이력 v1.5 기록

## 제약 조건

- JSON 스키마 구조는 변경하지 않는다 (필드 추가/제거 없음)
- Mermaid는 JSON과 동일 경로에 별도 파일로 저장 (`ia.json` + `ia-sitemap.md`)
- xlsx 변환은 제거하지 않고 "선택 사항"으로 유지

## 관련 문서

- `opal/skills/opal-pilot-write-tech/SKILL.md`
- `opal/skills/opal-pilot-write-tech/references/network-guide.md`
