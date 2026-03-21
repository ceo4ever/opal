# QA: PLAN -- OPAL 프레임워크 배포 구조 통합

> 검토일: 2026-03-21 | 판정: Pass

## 1. 요약

PLAN은 3개 플랫폼(Claude/Cursor/Antigravity)에 분산 배포되던 스킬과 에이전트를 `~/.opal/` 단일 경로로 통합하는 구현 계획이다. 소스 `agents/` 디렉토리 플랫화(Claude 포맷 기준), OPAL 전용 스킬에 opal- 접두사 적용, 9개 파일의 탐색 경로 2계층 단순화, install-mac.sh 메뉴 재설계(3항목)를 7단계 순서로 수행한다. 신규 파일 없이 기존 파일 이동/삭제/수정만으로 구성되며, RESEARCH에서 발견한 wtm-worker 누락, TASK.md 구조 오류 등이 모두 반영되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| P-1 | 즉시 구현 가능성 | Pass | 파일별 변경 내용, git mv 명령, 함수 수준 pseudo-code, 라인 번호까지 명시되어 바로 코딩 가능 |
| P-2 | 의존성 순서 정합 | Pass | (1) 소스 구조 변경 -> (2) 접두사 적용 -> (3) 참조 수정 -> (4) 코어 경로 -> (5) 스킬 탐색 경로 -> (6) install-mac.sh -> (7) 문서. 하위 레이어부터 올바른 순서 |
| P-3 | RESEARCH 반영 | Pass | RESEARCH의 5개 리스크(잔존 파일, 프로젝트 오버라이드, Gemini CLI, wtm-worker 누락, opal- 접두사 참조) 모두 PLAN 섹션 6에 대응 |
| P-4 | 파일 목록 일치 | Pass | RESEARCH 관련 파일 목록 20개 항목과 PLAN 수정/이동/삭제/영향확인 목록이 일치. RESEARCH에서 "수정 불필요"로 판단한 파일(opal-skill-creator, ui-designer 등)은 PLAN에서도 제외됨 |
| P-5 | 핵심 설계 구체성 | Warning | install-mac.sh 재설계(3.4)에서 함수 pseudo-code와 메뉴 구조는 명시되어 있으나, 삭제 대상 함수(install_claude, install_cursor, install_antigravity) 내의 로직 중 hooks 이관 외에 누락될 수 있는 세부 로직(예: Gemini CLI settings.json 머지, Cursor 부트스트래퍼 설치)에 대한 명시적 처리가 부족 |
| P-6 | 테스트 전략 커버리지 | Pass | 설치 스크립트 검증(배포 파일 수 확인), 탐색 경로 검증(grep), OPAL 전용 스킬 경로 검증 등 TASK 요구사항 4개 영역을 모두 커버 |

## 3. 지적 사항

### Warning 1개

**P-5: install-mac.sh 삭제 함수 내 세부 로직 이관 명세 부족**

심각도: Warning

PLAN 3.4절에서 `install_claude()`, `install_cursor()`, `install_antigravity()`를 삭제한다고 명시했으나, 이 함수들이 수행하던 모든 작업의 이관 처리가 명시적이지 않다.

- `install_claude()`의 hooks 머지는 `install_opal()` 라인 182에서 이관 명시됨 -- OK
- 부트스트래퍼 설치(install_opal_section)는 라인 177-179에서 이관 명시됨 -- OK
- 그러나 `install_antigravity()`의 Gemini CLI용 `settings.json` 머지(현재 `install_antigravity`에서 수행)가 `install_opal()`에 이관되는지 불분명

이 부분은 PLAN 3.4절의 MCP 설정이 별도 [2] 메뉴로 유지된다는 점에서 의도적 분리일 수 있으나, 명시적 언급이 없어 구현 시 혼란 가능성이 있다. EXECUTE 단계에서 `install_antigravity()` 함수 전체를 읽고 누락 로직이 없는지 확인하면 충분하다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 4개 영역(배포 구조/에이전트 포맷/소스 구조/경로 참조)이 PLAN에 모두 반영되었는가 | Pass |
| TASK.md | 제약 조건 4개(tasks/ 미수정, MCP 유지, 부트스트래퍼 유지, Claude 포맷 기준)가 준수되었는가 | Pass |
| TASK.md | 목표 배포 구조의 opal- 스킬 위치 오류를 PLAN이 수정했는가 | Pass -- RESEARCH 4-3에서 식별한 오류를 반영하여 skills/ 하위로 배치 |
| RESEARCH.md | 변경 필요 파일 9개가 PLAN에 모두 포함되었는가 | Pass -- 9개 파일 + 추가로 opal/core/AGENT.md, opal/bootstrapper/cursor-bootstrap.mdc 포함 |
| RESEARCH.md | 에이전트 3벌 통합 방향(Claude 포맷 기준)이 반영되었는가 | Pass |
| RESEARCH.md | wtm-worker 에이전트 누락 지적이 반영되었는가 | Pass -- PLAN 3.1에서 7개 에이전트에 wtm-worker 포함 |
| RESEARCH.md | install-mac.sh 메뉴 재설계 방향이 반영되었는가 | Pass -- RESEARCH 4-5의 3항목 메뉴 제안이 PLAN 3.4에 그대로 반영 |

## 5. 판정

**Pass**

6개 검증 항목 중 5개 Pass, 1개 Warning(install-mac.sh 삭제 함수 이관 세부 명세). Warning이 3개 미만이고 Critical 없음. EXECUTE 단계에서 기존 함수 코드를 읽으며 보완 가능한 수준이므로, 다음 단계 진행에 문제 없다.
