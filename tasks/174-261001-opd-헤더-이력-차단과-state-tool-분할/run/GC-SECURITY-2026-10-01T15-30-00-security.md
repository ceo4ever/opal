# GC-SECURITY 보고서 (2026-10-01T15-30-00, element=security)

- 대상: 명시 목록 40개 + state_tool_parts 신규 10개(중복 제거 후 checked_files는 JSON 참조). base_ref=dee405ca, baseline=none
- 기준: docs/SECURITY.md(T0), docs/CONVENTIONS.md, 공식 baseline(OWASP/CWE, T1). SECURITY.md 위협모델(install·MCP·skill fetch)은 이번 변경 표면과 무관.
- 판정: PASS (check status pass, blocking 0건). finding 2건(Low, advisory, 신규 1 / 영향 없음 pre_existing 성격 1)

## 검토 관점
- 경로 처리(CWE-22): 하위 모듈로 이동하며 `__file__` 기준 상대 경로가 한 단계 깊어졌으나 base.py(date.js, run-log-tool, ownership-tool), gates.py(test-tool, parents[3]=opal, event-loader), journal.py(memory-tool), commands_core.py(parent x4)가 모두 동일 대상으로 해소됨. 사용자 입력이 결합되지 않는 고정 경로.
- sys.path(CWE-427/829): state_tool.py가 자기 디렉토리(abspath(__file__) 기준)를 sys.path[0]에 삽입. 디렉토리에는 state_tool.py·state_tool_parts·todo_mirror_hook.py·tests 등 표준 라이브러리와 충돌하는 최상위 이름이 없고 외부 입력이 경로를 결정하지 않음. 중복 삽입 방지 조건 있음. 위험 낮음. 파트 내부 로더는 spec_from_file_location만 쓰고 sys.path 불변(GC-007 관례 유지).
- 재노출: importlib.import_module 대상은 고정 튜플 PART_MODULES(하드코딩)라 동적 입력 없음(CWE-94 해당 없음).
- subprocess(CWE-78): 이동된 호출 전부 리스트 인자, shell=True 없음, sys.executable 또는 node+고정 스크립트, 일부 timeout 있음. 신규 호출 없음.
- 해시 입력(skill_tester): sha256, 입력은 고정 경로+glob(state_tool_parts/*.py) 정렬. 파일 경계 구분자가 없는 단순 연결(F-002).
- 드리프트 확장(skill_tester): 설치본/소스 파일명 합집합 비교, 읽기 전용(read_bytes), 경로 이탈 입력 없음.
- code-scan.js: findHeaderCloseIndex는 선형 순회(ReDoS 없음), isHeaderOverflow는 statSync+고정 크기 head 읽기만 수행, 예외는 false로 흡수. header_overflow는 차단 방향이라 fail-open 아님(단 stat 실패 시 false=미차단, 의도된 안전측 아님이나 다른 단계가 같은 파일을 읽지 못해 별도 보고됨).
- 시크릿: 변경분에 자격증명 의심값 없음. 테스트의 tmp_path/subprocess git 사용은 리스트 인자.

## Findings
| ID | 심각도 | 구분 | 위치 | 내용 |
|---|---|---|---|---|
| GC-001 | Low | advisory, 이번 변경이 새로 만듦(T1 CWE-345 계열) | opal/skills/opal-skill-tester/scripts/skill_tester.py `_framework_fingerprint` | 파일 내용을 구분자·파일명 없이 연속 해시. 파일 수가 늘어(1→11개) 경계 이동(바이트가 인접 파일 사이로 이동)이 같은 해시를 낳을 수 있음. 위협 모델상 무결성 용도가 아닌 변경 감지 지문이라 실영향 미미. 권고: 파일 상대경로+길이를 해시에 포함. |
| GC-002 | Low | advisory, pre_existing(이동만 됨, 영향 없음) | opal/tools/state-tool/state_tool_parts/base.py `_run_date_js` 등 | subprocess에서 `node`를 PATH 탐색으로 실행. 기존 코드 원문 이동. 이번 변경이 노출을 늘리지 않음. |

## 요약
Critical 0 / High 0 / Medium 0 / Low 2. 신규 1(GC-001), 기존 이동분 1(GC-002). blocking 0건.
