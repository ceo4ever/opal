# DONE: erd-modeler 스킬 범용화

> 완료일: 2026-03-31

## 작업 요약

erd-modeler 스킬에서 MAMS 프로젝트 특화 요소를 제거하고, 어떤 프로젝트에서든 범용적으로 사용 가능하도록 재구성했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `skills/erd-modeler/SKILL.md` | 경로 하드코딩 제거, 사전 3단계 폴백 도입, 체크리스트 업데이트, 스키마 예시 범용화 |
| `skills/erd-modeler/references/naming-convention.md` | 헤더에 MAMS 예시임을 명시, 약어표 섹션 제목 범용화, 테이블 예시의 `MAMS_` → `{SCHEMA}_` 치환 |
| `skills/erd-modeler/references/dbml-guide.md` | `stl_*` 테이블명 → `{schema}_*` 플레이스홀더로 교체, 작성자 하드코딩 제거 |
| `skills/erd-modeler/references/mermaid-guide.md` | 작성자 `알투(Altu)` → `{작성자}` 변수화 |

## 주요 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | 데이터 사전 3단계 폴백 | 사전 없으면 모델링 불가 → 내부 기본 규칙으로 진행 가능하도록 완화 |
| 2 | naming-convention.md 약어표 예시화 | MAMS 약어는 예시로, 규칙 자체(패턴/원칙)만 범용 유지 |
| 3 | 폴더 구조 유연화 | `{프로젝트}/{Phase}/DB설계/` 고정 경로 → 사용자에게 출력 경로 확인 |
| 4 | 작성자 변수화 | 알투 하드코딩 제거, 재사용 시 작성자 칸을 채우도록 유도 |

## 요구사항 충족 여부

- [x] SKILL.md 범용화
- [x] 데이터 사전 유연화 (3단계 폴백)
- [x] naming-convention.md 범용화
- [x] dbml-guide.md 범용화
- [x] mermaid-guide.md 범용화
- [x] 폴더 구조 유연화
- [x] 하드코딩 제거 (작성자명)
