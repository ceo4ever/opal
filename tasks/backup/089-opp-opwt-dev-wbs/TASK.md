# TASK: opwt PMO 그룹 신설 + 개발 WBS 추가

> 작성일: 2026-04-06 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opwt(opal-pilot-write-tech) 스킬에 PMO 그룹을 신설하고, 개발 WBS 산출물 타입을 추가한다.
기획 산출물(IA, 기능 목록 등)을 기반으로 개발 항목을 누락·중복 없이 구조화하는 산출물을 opwt가 관리할 수 있도록 한다.

## 배경

현재 opwt 커버 범위는 필수 4종(PRD/TRD/서비스 정책서/IA) + 선택 4종(기능도/순서도/운영 정책서/서비스 매뉴얼) + 프로젝트 특화 선택(외부 API 명세서)으로 구성된다.
개발 WBS는 기획 산출물(IA 등)을 입력으로 받아 개발 관리 도구로 활용하는 산출물로, 기존 분류와 성격이 달라 별도 PMO 그룹이 필요하다.
향후 기획 WBS 추가를 고려하여 PMO 그룹을 미리 확보한다.

## 확정된 설계 방향 (대화에서 합의)

1. **PMO 그룹 신설**: 기존 필수/선택/프로젝트 특화와 별도로 "PMO" 그룹 추가
2. **개발 WBS 특성**:
   - 입력: IA, 기능 목록, 배치기능, 부가기능 등 기존 기획 산출물
   - 출력: 개발 WBS — 개발 항목을 MECE(누락·중복 없이) 원칙으로 구조화한 목록
   - 용도: 일정·완료여부 등 개발 관리 도구로 활용
   - 분해 원칙: Level 0(프로젝트 전체) → Level 1(BE/FE/인프라/공통) → Level 2(기능 모듈, IA 메뉴 구조 기준) → Level 3(작업 패키지, 8~80시간 단위)
   - 형식: Markdown 표 (일정·완료여부 컬럼 포함)
3. **핵심 연결**: IA → 개발 WBS (기능 정의 → 작업 분해), PRD 보조 참조, TRD 기술 컴포넌트 참조
4. **향후**: 기획 WBS도 PMO 그룹에 추가 예정 (이번 작업 범위 밖)

## 요구사항

- [ ] **SKILL.md 커버 범위 갱신** — PMO 그룹 신설 + 개발 WBS 추가
  - 무엇을: "PMO" 그룹 섹션 추가, 개발 WBS를 해당 그룹에 기재
  - 어디에: `opal/skills/opal-pilot-write-tech/SKILL.md` → "커버 범위" 섹션
  - 왜: 확정 방향 §1
  - AC: 커버 범위에 PMO 그룹이 별도 항목으로 존재하고, 개발 WBS가 포함되어 있다

- [ ] **SKILL.md TASK 확인 항목 갱신** — 개발 WBS가 대상 문서 유형으로 선택 가능하도록
  - 무엇을: "대상 문서 유형" 확인 항목에 개발 WBS 추가
  - 어디에: `opal/skills/opal-pilot-write-tech/SKILL.md` → "TASK 단계 > opwt 전용 확인 항목"
  - 왜: 개발 WBS를 opwt 파이프라인으로 작성하려면 TASK 단계에서 선택 가능해야 함
  - AC: TASK 확인 항목의 대상 문서 유형 목록에 "개발 WBS"가 포함되어 있다

- [ ] **network-guide.md 산출물 유형 정의 추가** — PMO 그룹 + 개발 WBS 항목 추가
  - 무엇을: PMO 그룹 섹션 신설, 개발 WBS 산출물 설명(입력/출력/형식/분해 구조) 추가
  - 어디에: `opal/skills/opal-pilot-write-tech/references/network-guide.md` → "§1 산출물 유형 정의"
  - 왜: 확정 방향 §2
  - AC: §1에 PMO 그룹이 존재하고, 개발 WBS의 설명·입력·출력 형식·Level 구조가 명시되어 있다

- [ ] **network-guide.md 연결 맵 추가** — 개발 WBS ↔ 기존 산출물 연결 관계
  - 무엇을: IA ↔ 개발 WBS, PRD ↔ 개발 WBS, TRD ↔ 개발 WBS 양방향 연결 추가
  - 어디에: `opal/skills/opal-pilot-write-tech/references/network-guide.md` → "§2 논리적 연결 맵"
  - 왜: 확정 방향 §3
  - AC: §2에 개발 WBS와 IA/PRD/TRD 각각의 양방향 연결이 기술되어 있다

- [ ] **network-guide.md diagnosis.json type 열거형 갱신** — 개발 WBS 타입 추가
  - 무엇을: `type` 필드 허용값에 `개발 WBS` 추가
  - 어디에: `opal/skills/opal-pilot-write-tech/references/network-guide.md` → "§5 diagnosis.json 스키마"
  - 왜: diagnosis.json으로 개발 WBS를 관리하려면 type 값이 정의되어 있어야 함
  - AC: `type` 필드 열거형에 `개발 WBS`가 포함되어 있다

## 제약 조건

- `~/.opal/` 경로 직접 수정 금지. 소스 경로(`opal/skills/opal-pilot-write-tech/`)만 수정
- 기존 산출물 유형(필수/선택/프로젝트 특화) 내용은 변경하지 않는다
- 기획 WBS는 이번 작업 범위 밖 (PMO 그룹 내 "향후 추가 예정" 주석만 남김)

## 기술 스택

- Markdown

## 관련 문서

- `opal/skills/opal-pilot-write-tech/SKILL.md`
- `opal/skills/opal-pilot-write-tech/references/network-guide.md`
