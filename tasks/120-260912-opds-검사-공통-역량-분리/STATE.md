# STATE: GC 검사 역량의 공통 스킬 분리

> 최종 갱신: 2026-09-12 15:06:33
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-12 14:49 | 제안서 마이그레이션 8단계 중 6(self-pm 연결)·7(reference registry)을 범위 제외 | `opal-self-pm`은 미채택 동반 제안에만 존재해 검증 불가. registry는 외부 공급망 축으로 독립 태스크가 적합 |
| 2 | 2026-09-12 14:49 | 스킬명을 `op-gc-security`/`op-gc-convention`/`op-gc-report`로 확정 | `docs/PROJECT.md` §네이밍 규칙의 `op-{그룹}-{역할}` 체계. 제안서 원안(`op-security-check` 등)은 규칙 이탈 |
| 3 | 2026-09-12 15:07 | W-1 워커가 `execute.implement` 행을 조기 mark한 상태를 되돌리지 않고 진행 | 도구에 done→in_progress 되감기 경로 없음. 품질 보증은 TEST PM Gate와 W-9 회귀가 담당 |
| 4 | 2026-09-12 15:19 | `opal-skills-registry.json` changelog를 말미가 아니라 맨 앞에 삽입 | 기존 배열이 최신 우선 정렬. PLAN 문구보다 파일의 실제 정렬 규약 우선 |
| 5 | 2026-09-12 15:27 | W-9 ②③④의 `unittest discover -t .`를 `-t <tests dir>`로 정정 실행 | Python 3.14에서 하이픈 경로가 importable하지 않아 `ImportError`. 명령 표기 오류이며 범위 변경 아님 |
| 6 | 2026-09-12 15:30 | 이동한 컨벤션 파일 3종의 stale 헤더(`module`/`domain`/`description`/템플릿 참조)를 PM이 직접 정정 | W-3이 H-1 문안 보존을 우선하며 헤더를 남겨 AC-3 grep 잔존 3건 발생. W-2 보안 파일과 동일 처리로 정합 |

## 검증 결과 (W-9)

| # | 검증 | 명령 | 결과 |
|---|------|------|------|
| ① | 파이프라인 행 불변 | `git diff --exit-code -- opal/skills/opal-pilot-gc/references/pipeline.json` | PASS (exit 0) |
| ② | state-tool 회귀 | `python3 -m unittest discover -s opal/tools/state-tool/tests -t opal/tools/state-tool/tests` | PASS (OK, skipped 3) |
| ③ | memory-tool 회귀 (채번 문구 보존) | 동일 형식 | PASS (202 tests OK, TS-041 4건 포함) |
| ④ | tool-scan 회귀 | 동일 형식 | 기존 실패 4건 — 클린 baseline(`git stash`)에서도 동일 재현. 이번 변경과 무관 |
| ⑤ | 스킬 레지스트리 | `node opal/tools/skill-registry/skill-registry.js validate` | unregistered 0건. dangling 3건은 배포 미실행 상태(H-3) — install 후 해소 |
| ⑥ | 문서 표준 감사 | `python3 scripts/tests/task113_bootstrap_audit.py --mode source` | PASS (exit 0) — H-1 경로 갱신 확인 |
| ⑦ | 구형 잔존 0 | 구 체크리스트·템플릿 경로 grep (제안서 제외) | PASS (0건, 헤더 정정 후) |
| ⑦-2 | checker 기준 잔존 0 | `OWASP`/`CWE-`/`SANS`/`fingerprint`/`auto_fixable`/트리거 grep | PASS (0건) |
| ⑧ | Gate 문안 보존 | `close.done_md`/`--owner user`/`CLOSE로 진행할까요` grep | PASS (7건 매칭) |
| ⑨ | 범위 해석 4종 + 대상 고정 | `opal-pilot-gc/SKILL.md` §1.1 문서 대조 | PASS — staged/all/untracked/commit/explicit 5경로 표 + `[MUST] 대상 고정`(하위 재선별 금지, 분할 합집합 = 확정 목록) |

> 미실행 1건: S-17(설치 후 `//opgc --scope staged` E2E)은 `scripts/install-mac.sh` 배포가 선행되어야 하며 소유자 승인 대기다.

## 블로커
없음
