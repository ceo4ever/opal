# TASK: oppd ROADMAP → WBS 전환

> 작성일: 2026-04-02 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 (대화 맥락)
> 출력: TASK.md

## 작업 목표

oppd Phase 2의 ROADMAP.md를 WBS(Work Breakdown Structure)로 전환하여, 작업 분해 구조의 명칭과 실체를 일치시키고, 액션별 완료 추적 기능을 추가한다.

## 배경

현재 oppd Phase 2에서 `docs/ROADMAP.md`를 작성하지만, 실제 내용은 타임라인/마일스톤이 아닌 **작업 분해 + 의존관계 + 스킬 배정**이다. 이는 ROADMAP보다 WBS에 해당한다. 또한 액션별 완료 상태와 완료일시를 WBS에서 직접 관리하면 STATE.md와의 중복을 줄일 수 있다.

## 요구사항

- [ ] `ROADMAP.md` → `WBS.md`로 리네이밍 (파일명, 문서 제목, 구조)
- [ ] WBS 액션 테이블에 `상태`, `완료일시` 컬럼 추가
- [ ] WBS 구조에 Work Package 계층 도입 (Work Package → Action 2단계)
- [ ] oppd SKILL.md 내 ROADMAP 참조를 WBS로 전환
- [ ] `references/roadmap-guide.md` → `references/wbs-guide.md`로 전환 (내용 포함)
- [ ] STATE.md에서 액션 진행 추적 중복 정리 (WBS가 액션 상태 담당, STATE.md는 Phase 레벨 + 로그에 집중)
- [ ] opal-harness.md 내 ROADMAP 참조가 있으면 WBS로 갱신
- [ ] Phase 3 실행 루프에서 WBS 기반으로 액션을 읽도록 반영
- [ ] `--wbs` 플래그 지원: Phase 1~2(PRD/TRD + WBS)까지만 실행 후 종료

## 제약 조건

- Phase 3 실행 메커니즘(opal-task-action-agent 디스패치)은 변경하지 않음
- 기존 oppd의 3-Phase 파이프라인 구조 유지
- 배포 행위 금지 (개발 범위만)

## 기술 스택

- Markdown 문서 (스킬/가이드/하네스)

## 관련 문서

- `opal/skills/opal-pilot-project-dev/SKILL.md` — oppd 본체
- `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` — 현재 로드맵 가이드
- `~/.opal/references/opal-harness.md` — 하네스 공통
- `docs/PROJECT.md` — 프로젝트 정의
