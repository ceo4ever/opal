# TASK: 하네스 모듈화 — 공통 + 모드별 분리

> 작성일: 2026-03-31 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opal-harness.md를 모듈화하여 **공통(필수) + 모드별 특화 하네스** 구조로 분리한다. 향후 새 모드 추가 시 공통은 공유하면서 특화 하네스만 추가하는 확장 모델.

## 배경

057에서 agentic mode를 §7로 추가하면서 하네스가 비대해지기 시작했다. 현재 §0~7이 한 파일에 있어 모드 추가마다 파일이 계속 커진다. 모듈화하면:
- 공통 규칙(Guards, State 등)은 한 곳에서 관리
- 모드별 규칙은 독립 파일로 분리
- 새 모드 추가 시 기존 파일 변경 없이 파일 추가만으로 확장

## 요구사항

- [ ] opal-harness.md → 공통 규칙만 유지 (§0 용어, §1 Guards, §3 State, §4 TASK, §5 Observability, §6 Model Mapping)
- [ ] opal-harness-interactive.md 신규 생성 — §2 Gates 내용 이동 (기본 모드)
- [ ] opal-harness-agentic.md 신규 생성 — §7 Agentic Mode 내용 이동
- [ ] opal-harness.md에 모듈 구조 설명 + 로딩 규칙 추가
- [ ] 4개 오케스트레이터(opd, opds, opp, oppd) SKILL.md의 하네스 참조 방식 갱신
- [ ] 공통 하네스에 QA 체크리스트 검증 규칙 추가 (EXECUTE 후 QA 체크리스트 갱신 의무)
- [ ] opd/opds: EXECUTE 후 PM Gate 추가 (TEST-SCENARIO 결과 검토 + QA 체크리스트 갱신)
- [ ] opp: EXECUTE 후 QA Gate + PM Gate 추가
- [ ] 배포본(~/.opal/) 동기화

## 제약 조건

- 기능적 변경 없음 — 구조 분리만 (리팩터링)
- 기존 오케스트레이터의 동작은 분리 전후 동일해야 함
- 공통 하네스는 모든 모드에서 필수 로드
- 모드별 하네스는 모드에 따라 1개만 로드

## 기술 스택

- Markdown

## 관련 문서

- `opal/core/references/opal-harness.md` — 현재 모놀리식 하네스
- `opal/skills/opal-pilot-dev/SKILL.md` — opd
- `opal/skills/opal-pilot-dev-short/SKILL.md` — opds
- `opal/skills/opal-pilot-project/SKILL.md` — opp
- `opal/skills/opal-pilot-project-dev/SKILL.md` — oppd
