# DONE: TDD RED-first 트랙 도입 — 독립 RED 작성 + 테스트코드 산출물 + state-tool red 게이트

> 완료일: 2026-06-10 | 스킬: opds (agentic) | 태스크: 016

## 요약

OPAL 하네스에 "실패하는 RED 테스트 → GREEN 구현" TDD 사이클을 도입했다. 자연어 시나리오에 머물던 테스트를 **실행 가능한 RED 테스트 코드 + 실패 증거 선확보 + state-tool deterministic 집행**으로 강화했다. R-5(state-tool 코드)는 **자기적용(dogfooding)** — RED 테스트 6 FAIL 확보 후 구현하여 GREEN 165 tests OK로 전환했다.

## 확정 설계 (캡틴 결정)

| # | 결정 | 내용 |
|---|------|------|
| C-1 | 독립 RED 작성 | RED 테스트 코드 작성 = `opal-test-agent(mode: red)`, 구현 = `op-dev-execute`. 작성자≠구현자 |
| C-2 | 스택·위치 탐지 | CONVENTIONS→스택문서→설정파일→기존관례 4단계. 러너 하드코딩 금지, 인프라 부재 시 에스컬레이션 |
| C-3 | 모듈 미러링 | 테스트는 대상 모듈에 배치. 케이스명 `[T{NNN}/L{계층}-{AC}]` + @header `task`/`scenarios` + §4 매핑표 열 |
| C-4 | state-tool 집행 | `verify --red-check`(RED 증거 게이트) + `--fix-mode`(테스트 불변성). 플랫폼 중립(훅 아님) |
| 정책 | 하이브리드 자동분기 | self-confirming 위험 작업(로직/DB/API/인증/버그)=RED-first 강제, 탐색/UI/리팩터=구현 후 검증. 모호 시 RED-first 기본 |

## 산출물 (변경 파일 12개)

**신규 (1)**
- `opal/core/references/harness/red-first.md` — RED-first 규칙 SSOT (§0 상속 ~ §6 STATE 정책 + 1.5 적용기준)

**수정 (11)**
- `opal/core/references/opal-harness.md` — §2 하네스 모듈 테이블에 red-first 등록
- `opal/tools/state-tool/state_tool.py` — ERROR_CODES 2종(`red_evidence_missing`/`test_modified_in_fix`) + 헬퍼 2종(`_check_red_evidence`/`_match_test_files`) + `cmd_verify` 분기(`--red-check`/`--fix-mode`) + argparse 4종 + `fnmatch` import
- `opal/tools/state-tool/tests/test_state_tool.py` — `TestRedFirst` 7케이스 + completeness 28→30
- `opal/skills/opal-pilot-dev-short/SKILL.md` — RED-first 참조 + EXECUTE 진입 전 `verify --red-check` 게이트·fix 불변성 절차
- `opal/skills/opal-pilot-dev/SKILL.md` — 동일 (opd)
- `opal/skills/op-dev-test-scenario/SKILL.md` — 역할 분배표 RED 작성주체 행 + §4 매핑표 "테스트 파일:케이스" 열
- `opal/skills/op-dev-test-scenario/references/test-scenario-guide.md` — 스택·위치 탐지 4단계 + 모듈 미러링 + 공개 인터페이스 규율
- `opal/agents/opal-test-agent/AGENT.md` — `mode: red` 추가
- `opal/skills/op-dev-execute/SKILL.md` — 가드레일 #6 RED 테스트 파일 수정 금지
- `opal/core/references/harness/header-rules.md` — 테스트 파일 `task`/`scenarios` 필드
- `opal/core/references/harness/coding-principles.md` — 공개 인터페이스 검증 1행

전 변경 문서에 016 변경이력 행 추가 완료.

## 동작검증 결과 (헌법 §4 — 실제 실행 증거)

| 시나리오 | 방식 | 결과 |
|---------|------|------|
| S-1~S-9 (RED 게이트·불변성·ERROR_CODES·skip·회귀) | `python -m unittest discover -s tests` | **Ran 165 tests OK, exit 0** (기존 158 + 신규 7, 회귀 0) |
| S-10 (SSOT 단일성) | grep | `red-first.md` 1개만 — 복제 0 |
| S-11 (STATE 행 불변) | grep | opds 10행 / opd 15행 유지 |

자기적용: RED 6 FAIL → GREEN 165 OK. 코드 품질(표준 라이브러리만)·보안(시크릿 없음) Pass.

## 후속 조치 (필수)

1. **install 재배포 필요** — 변경분이 `~/.opal/`로 배포돼야 실제 활성화된다. `scripts/install/*.sh`(mac) 재실행 또는 동기화 필요.
2. **후속 태스크 (017)** — `state-tool`에 "다중 Step EXECUTE 행은 마지막 Step(N=M)에서만 `--done` 허용" 가드 추가. 본 태스크에서 EXECUTE 행 조기 done 이슈로 식별됨(AGENTIC-LOG #8).
3. **커밋 분리 권고** — 워킹트리에 무관한 미커밋 변경(ppt-builder 등)이 있어, 016 변경분만 분리 커밋 권고.

## 특이사항 (AGENTIC-LOG 상세)

- 워커 소켓 끊김 2회(인프라). Step 3(GREEN 구현)은 캡틴 "계속" 지시로 PM 직접 구현(디스패치 의무 예외).
- EXECUTE 행 조기 done(PM 디스패치 지시 오류 + 단일행 구조 + 도구 가드 부재) → PM 행 통제로 보정. → 후속 017로 근본 개선.
- verify mock 오탐(체크 문장의 `MagicMock` 리터럴 자기검출) → 표현 수정.
