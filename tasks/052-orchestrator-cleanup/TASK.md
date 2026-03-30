# TASK: 오케스트레이터 정비 — opw 삭제 + 리네이밍 + opdp→opwt 연동

> 작성일: 2026-03-30 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opw 삭제, opp/opdp 리네이밍(네이밍 컨벤션 통일), opdp가 opwt를 호출하는 구조로 전환하여 오케스트레이터 체계를 정리한다.

## 배경

오케스트레이터가 6개(opd, opds, opdw, opp, opw, opwt)로 늘어나면서 역할 경계가 모호해졌다. 비교 검토 결과:
- opw는 opwt와 커버 범위가 중복되고, 개선하면 opp와 중복됨 → 삭제 결정
- opp의 자기 정의가 실제 용도와 맞지 않음 → 정비 + 리네이밍
- opdp의 PRD/TRD 작성이 opwt와 이중 존재 → opdp가 opwt를 호출하는 구조로 통합
- 네이밍 컨벤션이 불일치 (opal-project-* vs opal-pilot-*) → opal-pilot-* 통일

## 요구사항

### R1. opw 삭제
- [ ] `opal/skills/opal-pilot-write/` 소스 삭제
- [ ] `~/.opal/skills/opal-pilot-write/` 배포본 삭제
- [ ] 스킬 레지스트리(`opal/core/skills.json`)에서 opw 항목 제거
- [ ] `opal/core/references/skills.md`에서 opw 항목 제거
- [ ] 다른 스킬에서 opw 참조 정리
- [ ] 하네스 용어표에서 `opw` 관련 행 정리

### R2. opp 리네이밍 + 정체성 정비
- [ ] opal-project-pilot → **opal-pilot-project** (약어 opp 유지)
- [ ] 폴더, SKILL.md name 필드, 레지스트리, references/skills.md 일괄 변경
- [ ] description 수정: 프로젝트 범용 오케스트레이터 (문서 작성, 간단한 코드 수정 포함)
- [ ] opw로 안내하던 문서 작성을 opp 또는 opwt로 안내하도록 수정

### R3. opdp 리네이밍 + opwt 연동
- [ ] opal-project-dev-pilot → **opal-pilot-project-dev** (약어 oppd)
- [ ] 폴더, SKILL.md name 필드, 레지스트리, references/skills.md 일괄 변경
- [ ] Phase 1~2(PRD/TRD)를 opwt 호출로 전환 (PM 직접 작성 → opwt 디스패치)
- [ ] Phase 4 태스크 실행에서 opd/opds 사용 명시 (기존과 동일, 명확화)
- [ ] 자체 references/prd-guide.md, trd-guide.md는 opwt로 위임 후 정리 검토

### R4. 전체 참조 정리
- [ ] 모든 스킬에서 변경된 이름 반영 (opw, opp, opdp 참조)
- [ ] 하네스 용어표 업데이트
- [ ] 배포본(~/.opal/)과 소스(opal/) 동기화

### R5. (별도 태스크) agentic 자율 루핑 장치
- opdp(→oppd)에 QA/TEST 루핑을 통한 자율 개선/보정 장치 설계 → 별도 태스크로 등록

## 제약 조건

- 하네스(opal-harness.md) 핵심 구조는 변경하지 않음 (용어표만 갱신)
- 배포본(~/.opal/)과 소스(opal/) 동기화 유지
- opwt 기존 기능은 변경하지 않음 (opdp에서 호출만 추가)

## 기술 스택

- Markdown (스킬/참조 문서)
- JSON (skills.json 레지스트리)
- Shell (install-mac.sh 동기화 확인)

## 관련 문서

- `~/.opal/references/opal-harness.md` — 하네스 용어표
- `~/.opal/references/skills.md` — 스킬 레지스트리 참조 문서
- `opal/core/skills.json` — 스킬 레지스트리 소스
- `~/.opal/skills/opal-pilot-write-tech/SKILL.md` — opwt (연동 대상)
