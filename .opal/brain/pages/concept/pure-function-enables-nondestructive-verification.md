---
type: concept
title: 판정부·실행부 분리가 파괴적 검증을 비파괴 검증으로 바꾼다
tags:
- verification
- architecture
- lesson
- pure-function
sources:
- task:087
related:
- fix-validity-requires-failure-mode-reproduction
created: '2026-08-10'
updated: '2026-08-10'
status: draft
---
## 개요

위험한 동작(재생성·삭제 등)을 결정하는 판정 로직을 로그·파일쓰기·전역참조가 없는 순수 함수로 분리하면, 그 판정부만 실제(운영) 환경에 안전하게 노출해 검증할 수 있다. 판정부와 실행부가 뒤섞여 있으면 검증 자체가 파괴적이 되어 실환경 대상 검증이 불가능해진다.

## 결정 배경 (WHY)

태스크 087은 `venv_meets_min()`을 포함한 6개 함수(`python_candidates`·`python_version_of`·`python_meets_min`·`find_python`·`venv_meets_min`·`python_autoinstall_enabled`)를 "로그를 출력하지 않고 파일을 쓰지 않으며 전역을 읽지 않는" 순수 함수로 강제했다(근거: task:087 PLAN.md §2.3, DONE.md §3).

이 순수성 덕분에, 실제 소유자 환경(`~/.opal/.venv`, 버전 3.14.3)을 대상으로 `venv_meets_min ~/.opal/.venv`를 그대로 실행해 판정 결과(rc 0)와 `pyvenv.cfg`의 mtime 불변(`1775181326` → `1775181326`)을 함께 확인할 수 있었다(근거: task:087 DONE.md §5 비파괴 보장 표). 만약 이 함수가 판정과 동시에 `rm -rf`나 재생성 같은 부수효과를 품고 있었다면, 실제로 값이 있는 환경을 대상으로 판정만 시험해 볼 방법이 없었을 것이다 — 검증하려면 매번 파괴를 감수해야 했을 것이다.

## 결정 내용

- 위험한 동작(삭제·재생성·덮어쓰기)을 트리거하는 조건 판정은 그 동작 자체와 별도의 함수로 분리한다. 판정 함수는 인자로만 입력을 받고, 로그·파일쓰기·전역 상태 참조를 하지 않는다.
- 실행부(`rm -rf` 등)는 판정부의 반환값(rc)만 보고 분기한다 — 판정 로직을 실행부 안에 인라인하지 않는다.
- 판정부가 순수하다는 사실을 검증 설계의 전제로 명시적으로 활용한다. 순수 함수는 실제 프로덕션 상태를 대상으로 "무슨 일이 일어날지"만 안전하게 미리 관측할 수 있게 해 준다(dry-run에 준하는 효과를 별도 dry-run 플래그 없이 얻는다).

## 영향 범위

삭제·재생성처럼 되돌리기 어려운 동작을 포함하는 모든 게이트·설치기·마이그레이션 코드에 적용된다. 판정부·실행부 분리는 [[fix-validity-requires-failure-mode-reproduction]]가 요구하는 "실패 모드를 실제로 재현해 검증"하는 일을 실환경에서도 안전하게 가능하게 만드는 구조적 전제조건이다.

## 관련 페이지

- [[fix-validity-requires-failure-mode-reproduction]]
