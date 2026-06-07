# PLAN 013 — state-tool 동작 증거 강제 게이트

> 모드: agentic | 근거: 헌법(PRINCIPLES.md) §4 / 태스크 012 진단 P0

## 의사결정
- M-1: 강제 강도 = **a (자동 호출)** — verify 신설 + TEST stage mark 자동 강제 (캡틴 확정)
- M-2: mock 검출은 **코드 패턴**만 (오탐 방지) — 단순 "mock" 단어/설명 문구는 제외

## verify 서브커맨드 스펙

```
state-tool verify <task_path> [--scenario <path>]
```

대상: `<task_path>/TEST-SCENARIO.md` (없고 --scenario도 없으면 → skip ok, doc-only로 간주)

**검사 1 — mock 코드 패턴 (헌법 §4 "Don't fake it")**
- 정규식(코드 사용 패턴만): `MagicMock` / `unittest\.mock` / `@patch` / `mock\.patch` / `\bMock\(` / `@mock\.`
- 발견 → `mock_in_scenario` (exit 1), 위반 라인 번호 포함
- 단순 단어 "mock"(설명 문구)은 매칭 제외

**검사 2 — 증거 누락 (헌법 §4 "Completion requires evidence")**
- TEST-SCENARIO.md 시나리오 표에서 결과가 Pass/✅/PASS인 행에 "실행 명령" 또는 "결과/출력" 칸이 비어있으면 → `evidence_missing` (exit 1)
- 형식: `op-dev-test-scenario/references/test-scenario-guide.md` 시나리오 표 (워커가 tasks/004 산출물로 실제 형식 확인)

**정상** → ok (exit 0)

## mark 자동 훅
- `cmd_mark`에서 `row["stage"]`가 TEST(STAGE_ENUM 확인)이고 done 처리 시, 같은 task_path의 TEST-SCENARIO.md에 verify 로직 자동 실행
- 위반 시 mark 거부 (verify 에러 코드 전파)
- TEST-SCENARIO.md 부재 → skip (문서 태스크 무해)

## 변경 지점 (state_tool.py)
| 지점 | 변경 |
|------|------|
| `ERROR_CODES` (L59) | `mock_in_scenario`, `evidence_missing` 2종 추가 |
| 신규 `cmd_verify` | verify 로직 |
| `cmd_mark` (L803) | TEST stage done 시 verify 자동 호출 훅 |
| `main` sub.add_parser (L1201~) | `verify` 파서 등록 |
| `tests/test_state_tool.py` | TestVerify 클래스 — happy/mock검출/증거누락/mark자동훅/doc-only skip |

## 제약 (헌법 + 프로젝트)
- 표준 라이브러리만 (TASK T-11, pytest/hypothesis 금지)
- ~/.opal 직접 수정 금지, 임시 디렉토리 테스트 (AGENT.md 확정기준 #2)
- 헌법 §4: 구현 후 **실제 테스트 실행 + 통과 출력**을 동작 증거로 첨부 (선언 금지)

## 실행 구성
Phase 1: ERROR_CODES + cmd_verify + 파서 등록 → Phase 2: cmd_mark 자동 훅 → Phase 3: 테스트 작성 + 실행 검증
