# TEST 단계 소요시간 단축 — 요청과 AS-IS 근거

> 용도: TASK.md의 근거 보존. 2026-09-27 PM(대화) AS-IS 분석 결과(읽기 전용 수집 3건 + PM 판정)를 옮긴다.
> 사용자 결정: 개선 범위 C(프로세스 + 구조·기능 전체)를 한 태스크로, CLOSE까지 자율 진행.

## 1. 사용자 요청

"테스트 단계가 너무 오래 걸린다. 프로세스·기능·구조 문제를 냉철하게 검토하고 opal-studio·mams 최근 태스크에서 확인하라." → 검토 후 범위 C 승인.

## 2. 핵심 판정

테스트 **실행**은 느리지 않다. TEST 벽시계의 대부분은 (1) 사람 대기, (2) TEST 안에서 흡수되는 요구 변경, (3) 수정마다 전체 재검증·중복 검사·디스패치 고정비다.

## 3. 실측 근거 (F=파일 사실, E=추정)

### 3.1 사람 대기 (최대 비용)

- mams 174~184: TEST 구간 워커 실작업 합계 138분 vs TEST 벽시계 약 90시간(184 제외) (F: `state.json` worker_duration_minutes, state-tool show). 184는 사용자 확인만 9.6일 대기.
- opal-studio 004: AC-9 macOS 관찰 대기로 TEST 6일 (`opal-studio/tasks/004*/AGENTIC-LOG.md:44,48,49`). 009: 33시간 28분 유휴 + S-28 4계정 로그인. 010: S-12 Finder 확인 ~40분, verifier가 "확인" 단답을 `evidence_missing`으로 거부 (`010*/AGENTIC-LOG.md:55,62-63,76`).
- 사람 전용 시나리오(L3 `[SUPERVISOR]`, DDL 적용, 로그인, 관찰)는 자동 테스트 PASS 뒤에야 하나씩 요청된다 (opal-studio `004:44`, `010:63`; mams 177 L3 32건 언급, 178 21건).
- 측정 한계: opal-studio state.json 행 시점이 사후 일괄 기입됨(009 행 8~11 동일 초, 010 행 7~8이 후속 TEST 행보다 늦음). mams는 `run/` 로그가 없다.

### 3.2 TEST 중 요구 변경의 무제한 흡수

- opal-studio 009: TEST 중 UX 수정 약 15회(UX1~UX15), 테스트 297→449개 (`009*/AGENTIC-LOG.md:110-138`).
- opal-studio 010: 요구 변경 1회 + 사용자 지시 fix 3회, fix 상한(3) 초과 4·5·6차 (state-tool show 010 행 10~17).
- mams 176(R-9), 179(O-19~O-23), 177·180 범위 추가. 하네스가 요구 변경을 fix 카운트에 포함하지 않아 상한이 작동하지 않는다 (`mams/tasks/176*/AGENTIC-LOG.md:127`).

### 3.3 수정마다 전체 재검증·중복 검사

- 규칙: `guards.md:101` "자동 수정 후 이전 통과 테스트를 재실행", `opal-pilot-dev/SKILL.md:318` "이전 PASS 항목 재실행". test-agent는 매번 전 시나리오 + lint/type/format + 보안 + 전체 회귀를 수행 (`agents/opal-test-agent/AGENT.md:22-39`).
- `test-tool unit --changed-files`는 파서만 있고 미연결 (`opal/tools/test-tool/test_tool.py:437`) — 태스크 161(A1) 범위.
- 같은 검사가 EXECUTE 자가 점검(`op-dev-execute/references/execute-guide.md:60-70`)·PM 재확인·TEST에서 3회 반복.
- 디스패치 1회당 고정 절차: pilot.start receipt 재검증 + worker.dispatch load(4문서)·verify + Steps 1~7, 워커 측 verify 재수행 (`pm/dispatch-process.md:8-24,99-102`). fix 1회 ≈ 고정 30단계 + 시나리오 N회 mark (E).
- 실측 실행 시간은 작다: vitest 206건 5.3~5.6s, 병합 후 503+253건 10.6~11.3s, E2E S-10 10.3s (opal-studio 010 `run/*.log`). mams 실데이터 실행 19~397s.
- GC 컨벤션 검사: opal-studio 010에서 4회(21:08→22:37→22:54→06:40), 009에서 3라운드 5파일. 1회 1~9분.
- main 분기 차이를 CLOSE 직전에 발견: opal-studio 010 병합 충돌 9파일 56분 + E2E 단언 드리프트 2건 (`010*/AGENTIC-LOG.md:82-93`, 회고 `:96`).

### 3.4 도구 마찰

- `worker_duration_undeclared` 거부(mams 182·183, opal-studio 003·007), `surface_profile_mismatch`(005:67), verifier `evidence_missing`(010:63), auto-mode 분류기의 worker verify·DB 스크립트 차단(opal-studio 009:137-138, mams 178 LOG:65).
- `stage.test` 이벤트는 `scenario-gate.md`·`qa-standards.md`만 로드한다 (`opal/core/references/events.json:351`). 둘 다 테스트 실행 규칙이 아니다.

## 4. 인접 태스크와 범위 경계

- 태스크 161(A1, 진행 중 worktree): test-tool 실행기·resolver·스키마·템플릿, `--changed-files` 실행 연결을 소유한다. 이 태스크는 그 파일을 수정하지 않는다.
- `docs/proposals/gc-verification-task-drafts.md`의 B(GC 빠른 완화)·C(검증 증거)·D(GC 증분 재검사)는 GC 스킬·체커 내부를 소유한다. 이 태스크는 GC 호출 **시점·횟수** 정책만 다루고 GC 스킬 내부는 수정하지 않는다.
- 기존 제안 `docs/proposals/opal-oppl-fast-project-execution.md` Phase D(동일 검증 재사용·영향 범위 분리, AC #9·#10·#13)는 oppl 대상이며 opd/opds에 미구현이다. 참고 입력으로만 쓴다.
