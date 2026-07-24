# ADD_DONE-2: state.schema mode enum semi-agentic 정정

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-2 |
| 일시 | 2026-07-10 17:57 ~ 18:37 (KST) |
| 사유 | 056 PLAN Gate 부수 발견 — `state.schema.json` mode enum이 `["interactive","agentic"]`로 semi-agentic(기본 모드) 누락. CLI는 수용하나 스키마 기준 검증 시 위반 판정될 기존 드리프트 (AGENTIC-LOG #8) |
| 변경 내용 | mode enum에 `"semi-agentic"` 추가 + description "3-way" 정합. 회귀 방지 테스트 2건 신설(`TestSchemaModeEnumSemiAgentic` — 스키마↔CLI choices 일치·semi-agentic init→validate 통과) |
| 변경 파일 | opal/tools/state-tool/{schema/state.schema.json, README.md(v1.4), tests/test_state_tool.py(+2)} |
| 검증 결과 | `init --mode semi-agentic` → `validate` violations 0. state-tool 스위트 206 passed(+2, 기지 환경성 실패 1건 불변) |
